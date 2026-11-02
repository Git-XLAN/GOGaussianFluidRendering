"""
Hold the right mouse button and drag over the fluid to push water.

Picking uses the same framebuffer convention as rendering: particles are selected
when their projected position (MiniGL.project_world) is near the cursor.

By default only the *visible* surface sheet is affected: among particles whose
screen projection falls in the brush, we keep those whose NDC depth (pw[2] from
project_world) lies within a small band of the shallowest (camera-closest)
candidate, so a vertical stack under the cursor is not all pushed at once.

Optional: set SPH_MOUSE_SURFACE_RHO_MAX=0.995 to also require rho/rho0 below
that value (approx. free-surface particles in SPH).

Uses MiniGL.prepend_mouse_press_func (before ImGui). Right/middle avoids the
built-in left-drag selection tool.

Force is applied in SimulatorBase.setTimeStepCB (every simulation step) by
polling the cursor. When the cursor has not moved to a new **integer pixel**
since the last step, the near-plane delta is zero: we skip the O(n) particle
scan so slow drags do not stall the solver (simulation time keeps up with real
time). Sub-pixel motion still accumulates through float cursor state.

  python mouse_fluid_interaction.py
  $env:SPH_MOUSE_SURFACE_NDC="0.03"   # wider NDC-z band (include more of the front layer)
  $env:SPH_MOUSE_SURFACE_RHO_MAX="0.995"
  $env:SPH_MOUSE_IMPULSE="2.5"        # strength of push (default lower; raise if too weak)

``SimulatorBase.setTimeStepCB`` runs **once per simulation substep** (each inner integration step), **after**
the fluid advance for that step. This script refreshes ``PARTICLE_BUFFERS`` at the **end** of that callback
(so values include any mouse brush applied in the same callback). That matches **each Step**, not each OpenGL
frame (one display frame may run ``NUM_STEPS_PER_RENDER`` substeps → multiple refreshes per frame).

``PARTICLE_BUFFERS['pos']`` / ``['vel']`` use **views** into solver memory when possible (fast); shape
``(numActiveParticles, 3)``, ``float64`` — do **not** write through them. Fallback: per-particle copy (slow).

**在 Python 里取用 pos / vel / 粒子半径**

1. **本脚本内**（例如在 ``setTimeStepCB`` 里、且已调用 ``_update_particle_buffers`` 之后）：读模块级变量
   ``PARTICLE_BUFFERS["pos"]``、``PARTICLE_BUFFERS["vel"]``（``numpy.ndarray``），以及
   ``float(sim.getParticleRadius())`` 或 ``PARTICLE_BUFFER_INFO["particle_radius"]``（每次 ``_update_particle_buffers`` 后写入）。
2. **其它 .py**：``from mouse_fluid_interaction import PARTICLE_BUFFERS, PARTICLE_BUFFER_INFO``，在仿真运行、且本脚本的回调每步更新了缓冲区后读取；若需**独立拷贝**再传给别的线程/进程，用
   ``np.array(PARTICLE_BUFFERS["pos"], copy=True)``（``vel`` 同理）。
3. **不依赖本模块全局**：在回调里对 ``fluid = sim.getFluidModel(0)`` 使用 ``fluid.getFieldBuffer("position")`` / ``"velocity"`` 得到内存视图，半径用 ``sim.getParticleRadius()``。

  $env:SPH_PARTICLE_NPY=0              # disable export
  $env:SPH_PARTICLE_SHAPE_LOG=1        # stderr: shape when n_active / pool size changes
  $env:SPH_MOUSE_STEP_LOG=0            # stderr: each sim substep — one line: shapes + particle radius (default off)
  $env:SPH_MOUSE_STEP_LOG=1            # enable that line
  $env:SPH_MOUSE_FAKE_RENDERER=1        # stderr: ``FakeParticleRenderer`` summary of pos/vel/radius (default on)
  $env:SPH_MOUSE_FAKE_RENDERER=0        # disable fake renderer
"""
from __future__ import annotations

import os
import sys

# 保证 ``import src_v3...`` 可用：仓库根须在 sys.path 中（直接运行本脚本时 cwd 可能不在根目录）
_this_dir = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_this_dir, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np
import pysplishsplash as sph
import pysplishsplash.Utilities.SceneLoaderStructs as Scenes

from src_v3.demo.RealTimeWaterMinimal import Render

# -----------------------------------------------------------------------------

# Updated at the end of **every** ``setTimeStepCB`` when export is on (one refresh per sim substep).
# Entries are **views** (fast) or owned copies (fallback); do not mutate if views point into the solver.
PARTICLE_BUFFERS: dict[str, np.ndarray] = {
    "pos": np.zeros((0, 3), dtype=np.float64),
    "vel": np.zeros((0, 3), dtype=np.float64),
}
# Last reported shapes / pool sizes (for logging); same as ``PARTICLE_BUFFERS`` rows when using views.
PARTICLE_BUFFER_INFO: dict[str, int | float | tuple[int, ...]] = {
    "num_active": 0,
    "num_particles": 0,
    "pos_shape": (0, 3),
    "vel_shape": (0, 3),
    "sim_time": 0.0,
    "time_step_size": 0.0,
    "particle_radius": 0.0,
}


class FakeParticleRenderer:
    """占位渲染器：接口为 ``(pos, vel, radius)``，当前实现只把收到的数据摘要打到 stderr。"""

    def render(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        radius: float,
        *,
        sim_time: float | None = None,
        dt: float | None = None,
        file=sys.stderr,
    ) -> None:
        """输出本帧拿到的 ``pos`` / ``vel`` / ``radius`` 信息（形状、类型、数量、简单统计）。"""
        lines = [
            "[fake_renderer] inputs:",
            f"  particle_radius (h) = {float(radius):.6g}",
        ]
        if sim_time is not None:
            lines.append(f"  sim_time = {sim_time:.6g}")
        if dt is not None:
            lines.append(f"  dt = {dt:.6g}")

        def _block(name: str, arr: np.ndarray) -> None:
            lines.append(f"  {name}:")
            lines.append(f"    shape = {tuple(arr.shape)}, dtype = {arr.dtype}")
            if arr.size == 0:
                lines.append("    (empty)")
                return
            a = np.asarray(arr, dtype=np.float64)
            lines.append(f"    min = {np.min(a, axis=0)}, max = {np.max(a, axis=0)}, mean = {np.mean(a, axis=0)}")

        _block("pos", pos)
        _block("vel", vel)

        print("\n".join(lines), file=file, flush=True)


def _mesh(name: str) -> str:
    return os.path.join(_REPO_ROOT, "data", "models", name)


def cursor_framebuffer(mgl, win_x: float, win_y: float):
    """GLFW window coords (top-left origin) -> MiniGL framebuffer x,y (bottom-left origin)."""
    dpr = float(mgl.get_device_pixel_ratio())
    h = float(mgl.get_height())
    return (win_x * dpr, h - win_y * dpr)


def _surface_ndc_band():
    v = os.environ.get("SPH_MOUSE_SURFACE_NDC", "").strip()
    if not v:
        return 0.018
    try:
        return max(1e-6, float(v))
    except ValueError:
        return 0.018


def _optional_rho_max():
    """If set, only particles with rho/rho0 < this value (lower => stricter surface)."""
    v = os.environ.get("SPH_MOUSE_SURFACE_RHO_MAX", "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _impulse_scale():
    """Multiplier for dv from near-plane mouse motion; higher = stronger push."""
    v = os.environ.get("SPH_MOUSE_IMPULSE", "").strip()
    if not v:
        return 2.5
    try:
        return max(0.0, float(v))
    except ValueError:
        return 2.5


def _particle_numpy_enabled() -> bool:
    return os.environ.get("SPH_PARTICLE_NPY", "1").strip().lower() not in ("0", "false", "no", "off")


def _particle_shape_log() -> bool:
    return os.environ.get("SPH_PARTICLE_SHAPE_LOG", "1").strip().lower() not in ("0", "false", "no", "off")


def _step_log_enabled() -> bool:
    return os.environ.get("SPH_MOUSE_STEP_LOG", "0").strip().lower() not in ("0", "false", "no", "off")


def _fake_renderer_enabled() -> bool:
    return os.environ.get("SPH_MOUSE_FAKE_RENDERER", "1").strip().lower() not in ("0", "false", "no", "off")


def _print_step_particle_state(sim) -> None:
    """stderr: ``pos``/``vel`` shapes and ``Simulation.getParticleRadius`` (per sim substep)."""
    rp = float(sim.getParticleRadius())
    PARTICLE_BUFFER_INFO["particle_radius"] = rp
    pos = PARTICLE_BUFFERS["pos"]
    vel = PARTICLE_BUFFERS["vel"]
    PARTICLE_BUFFER_INFO["pos_shape"] = tuple(int(x) for x in pos.shape)
    PARTICLE_BUFFER_INFO["vel_shape"] = tuple(int(x) for x in vel.shape)
    print(
        f"[mouse_fluid] step t={PARTICLE_BUFFER_INFO['sim_time']:.6g} "
        f"dt={PARTICLE_BUFFER_INFO['time_step_size']:.6g} "
        f"pos.shape={PARTICLE_BUFFER_INFO['pos_shape']} vel.shape={PARTICLE_BUFFER_INFO['vel_shape']} "
        f"particle_radius={rp:.6g}",
        file=sys.stderr,
        flush=True,
    )


def _log_particle_shapes(n_alloc: int, n_act: int) -> None:
    pos = PARTICLE_BUFFERS["pos"]
    vel = PARTICLE_BUFFERS["vel"]
    PARTICLE_BUFFER_INFO["num_particles"] = n_alloc
    PARTICLE_BUFFER_INFO["num_active"] = n_act
    PARTICLE_BUFFER_INFO["pos_shape"] = tuple(int(x) for x in pos.shape)
    PARTICLE_BUFFER_INFO["vel_shape"] = tuple(int(x) for x in vel.shape)
    print(
        "[mouse_fluid] PARTICLE_BUFFERS: "
        f"pos.shape={PARTICLE_BUFFER_INFO['pos_shape']} vel.shape={PARTICLE_BUFFER_INFO['vel_shape']} "
        f"(numActiveParticles={n_act}, numParticles={n_alloc}) "
        f"sim_time={PARTICLE_BUFFER_INFO['sim_time']} dt={PARTICLE_BUFFER_INFO['time_step_size']}",
        file=sys.stderr,
        flush=True,
    )


def _update_particle_buffers(fluid, *, shape_log: bool, shape_sig: list[tuple[int, int]]) -> None:
    """Prefer zero-copy views via ``getFieldBuffer``; fallback to element-wise copy."""
    tm = sph.TimeManager.getCurrent()
    t = float(tm.getTime())
    h = float(tm.getTimeStepSize())
    PARTICLE_BUFFER_INFO["sim_time"] = t
    PARTICLE_BUFFER_INFO["time_step_size"] = h
    PARTICLE_BUFFER_INFO["particle_radius"] = float(sph.Simulation.getCurrent().getParticleRadius())

    n_act = int(fluid.numActiveParticles())
    n_alloc = int(fluid.numParticles())
    try:
        mv_p = fluid.getFieldBuffer("position")
        mv_v = fluid.getFieldBuffer("velocity")
        pos_full = np.asarray(mv_p, dtype=np.float64)
        vel_full = np.asarray(mv_v, dtype=np.float64)
        if pos_full.size != n_alloc * 3:
            raise ValueError("position buffer size mismatch")
        pos_full = pos_full.reshape(n_alloc, 3)
        vel_full = vel_full.reshape(n_alloc, 3)
        PARTICLE_BUFFERS["pos"] = pos_full[:n_act]
        PARTICLE_BUFFERS["vel"] = vel_full[:n_act]
    except Exception:
        pos = np.empty((n_act, 3), dtype=np.float64)
        vel = np.empty((n_act, 3), dtype=np.float64)
        for i in range(n_act):
            p = fluid.getPosition(i)
            v = fluid.getVelocity(i)
            pos[i, 0] = float(p[0])
            pos[i, 1] = float(p[1])
            pos[i, 2] = float(p[2])
            vel[i, 0] = float(v[0])
            vel[i, 1] = float(v[1])
            vel[i, 2] = float(v[2])
        PARTICLE_BUFFERS["pos"] = pos
        PARTICLE_BUFFERS["vel"] = vel

    sig = (n_alloc, n_act)
    if shape_log and (not shape_sig or shape_sig[0] != sig):
        shape_sig.clear()
        shape_sig.append(sig)
        _log_particle_shapes(n_alloc, n_act)


def main():
    mgl = sph.MiniGL

    base = sph.Exec.SimulatorBase()
    base.init(useGui=True, sceneFile=sph.Extras.Scenes.Empty, initialPause=False)
    gui = sph.GUI.Simulator_GUI_imgui(base)
    base.setGui(gui)

    scene = sph.Exec.SceneConfiguration.getCurrent().getScene()
    # Fewer particles: larger spacing + smaller fluid block than default demos.
    scene.particleRadius = 0.03
    scene.boundaryModels.append(
        Scenes.BoundaryData(
            meshFile=_mesh("UnitBox.obj"),
            translation=[0.0, 0.0, 0.0],
            scale=[4.0, 4.0, 4.0],
            color=[0.1, 0.4, 0.5, 1.0],
            isWall=True,
            mapInvert=True,
            mapResolution=[20, 20, 20],
        )
    )
    scene.fluidBlocks.append(
        Scenes.FluidBlock(
            id="Fluid",
            boxMin=[-1.95, -2.0, -1.95],
            boxMax=[1.95, -1.5, 1.95],
            mode=0,
            initialVelocity=[0.0, 0.0, 0.0],
        )
    )

    base.initSimulation()

    sim = sph.Simulation.getCurrent()
    sim.setValueInt(sim.BOUNDARY_HANDLING_METHOD, 2)

    fluid = sim.getFluidModel(0)
    rho0 = float(fluid.getDensity0())
    surface_ndc_band = _surface_ndc_band()
    rho_max_ratio = _optional_rho_max()
    # Brush radius in framebuffer pixels (scales with resolution)
    brush_px = float(mgl.get_height()) * 0.03
    impulse_scale = _impulse_scale()*0.5
    export_particle_numpy = _particle_numpy_enabled()
    particle_shape_log = _particle_shape_log()
    step_log = _step_log_enabled()
    use_fake_renderer = _fake_renderer_enabled()
    fake_renderer = FakeParticleRenderer()
    _particle_shape_sig: list[tuple[int, int]] = []

    

    debug = os.environ.get("SPH_MOUSE_DEBUG", "").strip() in ("1", "true", "yes", "on")
    state = {"rmb": False, "prev_mx": None, "prev_my": None}

    def on_press(button, action, _mods):
        if debug:
            print(f"[sph-mouse] press cb: button={button} action={action} RIGHT={mgl.MOUSE_BUTTON_RIGHT}", flush=True)
        use_rmb = button == mgl.MOUSE_BUTTON_RIGHT or button == mgl.MOUSE_BUTTON_MIDDLE
        if not use_rmb:
            return False
        if action == mgl.PRESS:
            state["rmb"] = True
            cx, cy = mgl.get_cursor_pos()
            state["prev_mx"] = float(cx)
            state["prev_my"] = float(cy)
            return True
        state["rmb"] = False
        state["prev_mx"] = None
        state["prev_my"] = None
        return True

    def apply_brush_from_cursor(mx: float, my: float, px: float, py: float) -> None:
        """Apply impulse for cursor (mx,my) vs previous (px,py); brush centered at (mx,my)."""
        imx, imy = int(mx), int(my)
        ipx, ipy = int(px), int(py)
        # unproject() uses integer window coords: no visible motion => no dv — skip O(n) scan.
        # Slow drags often sit on one pixel for many substeps; without this, Python work per
        # step blocks the host and simulation time lags wall clock.
        if imx == ipx and imy == ipy:
            return

        tm = sph.TimeManager.getCurrent()
        h_step = float(tm.getTimeStepSize())
        if h_step < 1e-12:
            h_step = 1e-4

        p0 = mgl.unproject(ipx, ipy)
        p1 = mgl.unproject(imx, imy)
        dvx = impulse_scale * (float(p1[0]) - float(p0[0])) / h_step
        dvy = impulse_scale * (float(p1[1]) - float(p0[1])) / h_step
        dvz = impulse_scale * (float(p1[2]) - float(p0[2])) / h_step
        if abs(dvx) + abs(dvy) + abs(dvz) < 1e-14:
            return

        fbx, fby = cursor_framebuffer(mgl, mx, my)
        n_touch = 0
        n_act = fluid.numActiveParticles()
        cand = []
        for i in range(n_act):
            ppx = float(fluid.getPosition(i)[0])
            ppy = float(fluid.getPosition(i)[1])
            ppz = float(fluid.getPosition(i)[2])
            pw = mgl.project_world([ppx, ppy, ppz])
            if float(pw[0]) == 0.0 and float(pw[1]) == 0.0:
                continue
            ddx = float(pw[0]) - fbx
            ddy = float(pw[1]) - fby
            if ddx * ddx + ddy * ddy > brush_px * brush_px:
                continue
            cand.append((i, float(pw[2])))

        if not cand:
            return

        z_min = min(z for _, z in cand)
        z_lim = z_min + surface_ndc_band

        for i, ndc_z in cand:
            if ndc_z > z_lim:
                continue
            if rho_max_ratio is not None and rho0 > 1e-20:
                r = float(fluid.getDensity(i)) / rho0
                if r >= rho_max_ratio:
                    continue
            v = fluid.getVelocity(i)
            fluid.setVelocity(i, [float(v[0]) + dvx, float(v[1]) + dvy, float(v[2]) + dvz])
            n_touch += 1

        if debug:
            print(
                f"[sph-mouse] sim_step fb=({fbx:.1f},{fby:.1f}) brush_px={brush_px:.0f} "
                f"z_min={z_min:.4f} dv=({dvx:.5f},{dvy:.5f},{dvz:.5f}) touched={n_touch}/{n_act}",
                flush=True,
            )

    def on_sim_step():
        if state["rmb"] and state["prev_mx"] is not None:
            cx, cy = mgl.get_cursor_pos()
            mx = float(cx)
            my = float(cy)
            apply_brush_from_cursor(mx, my, state["prev_mx"], state["prev_my"])
            state["prev_mx"] = mx
            state["prev_my"] = my
        # One export per **simulation substep** (after brush above): same cadence as the integrator Step.
        if export_particle_numpy or step_log or use_fake_renderer:
            _update_particle_buffers(
                fluid,
                shape_log=particle_shape_log,
                shape_sig=_particle_shape_sig,
            )
        if use_fake_renderer:
            Render(
                pos=PARTICLE_BUFFERS["pos"],
                vel=PARTICLE_BUFFERS["vel"],
                radius=float(PARTICLE_BUFFER_INFO["particle_radius"]),
                dt = float(PARTICLE_BUFFER_INFO["time_step_size"]),
                simTime = float(PARTICLE_BUFFER_INFO["sim_time"])
            )
        if step_log:
            _print_step_particle_state(sim)

    mgl.prepend_mouse_press_func(on_press)
    base.setTimeStepCB(on_sim_step)

    base.runSimulation()
    base.cleanup()


if __name__ == "__main__":
    sys.exit(main() or 0)
