# SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

###########################################################################
# Example Smoothed Particle Hydrodynamics
#
# Shows how to implement a SPH fluid simulation.
#
# Neighbors are found using the wp.HashGrid class, and
# wp.hash_grid_query(), wp.hash_grid_query_next() kernel methods.
#
# Reference Publication
# Matthias Müller, David Charypar, and Markus H. Gross.
# "Particle-based fluid simulation for interactive applications."
# Symposium on Computer animation. Vol. 2. 2003.
#
###########################################################################

import numpy as np

import warp as wp
import warp.render


@wp.func
def square(x: float):
    return x * x


@wp.func
def cube(x: float):
    return x * x * x


@wp.func
def fifth(x: float):
    return x * x * x * x * x


@wp.func
def density_kernel(xyz: wp.vec3, smoothing_length: float):
    # calculate distance
    distance = wp.dot(xyz, xyz)

    return wp.max(cube(square(smoothing_length) - distance), 0.0)


@wp.func
def diff_pressure_kernel(
    xyz: wp.vec3, pressure: float, neighbor_pressure: float, neighbor_rho: float, smoothing_length: float
):
    # calculate distance
    distance = wp.sqrt(wp.dot(xyz, xyz))
    distance = wp.max(distance, 1.0e-4 * smoothing_length)

    if distance < smoothing_length:
        # calculate terms of kernel
        term_1 = -xyz / distance
        nr = wp.max(neighbor_rho, 1.0e-5)
        term_2 = (neighbor_pressure + pressure) / (2.0 * nr)
        term_3 = square(smoothing_length - distance)
        return term_1 * term_2 * term_3
    else:
        return wp.vec3()


@wp.func
def diff_viscous_kernel(xyz: wp.vec3, v: wp.vec3, neighbor_v: wp.vec3, neighbor_rho: float, smoothing_length: float):
    # calculate distance
    distance = wp.sqrt(wp.dot(xyz, xyz))
    distance = wp.max(distance, 1.0e-4 * smoothing_length)

    # calculate terms of kernel
    if distance < smoothing_length:
        nr = wp.max(neighbor_rho, 1.0e-5)
        term_1 = (neighbor_v - v) / nr
        term_2 = smoothing_length - distance
        return term_1 * term_2
    else:
        return wp.vec3()


@wp.kernel
def compute_density(
    grid: wp.uint64,
    particle_x: wp.array[wp.vec3],
    particle_rho: wp.array[float],
    density_normalization: float,
    smoothing_length: float,
):
    tid = wp.tid()

    # order threads by cell
    i = wp.hash_grid_point_id(grid, tid)

    # get local particle variables
    x = particle_x[i]

    # store density
    rho = float(0.0)

    # particle contact
    neighbors = wp.hash_grid_query(grid, x, smoothing_length)

    # loop through neighbors to compute density
    for index in neighbors:
        # compute distance
        distance = x - particle_x[index]

        # compute kernel derivative
        rho += density_kernel(distance, smoothing_length)

    # add external potential
    particle_rho[i] = density_normalization * rho


@wp.kernel
def get_acceleration(
    grid: wp.uint64,
    particle_x: wp.array[wp.vec3],
    particle_v: wp.array[wp.vec3],
    particle_rho: wp.array[float],
    particle_a: wp.array[wp.vec3],
    isotropic_exp: float,
    base_density: float,
    gravity: float,
    pressure_normalization: float,
    viscous_normalization: float,
    smoothing_length: float,
):
    tid = wp.tid()

    # order threads by cell
    i = wp.hash_grid_point_id(grid, tid)

    # get local particle variables
    x = particle_x[i]
    v = particle_v[i]
    rho = particle_rho[i]
    rho_eff = wp.max(rho, 0.09 * base_density)
    pressure = isotropic_exp * (rho_eff - base_density)

    # store forces
    pressure_force = wp.vec3()
    viscous_force = wp.vec3()

    # particle contact
    neighbors = wp.hash_grid_query(grid, x, smoothing_length)

    # loop through neighbors to compute acceleration
    for index in neighbors:
        if index != i:
            # get neighbor velocity
            neighbor_v = particle_v[index]

            # get neighbor density and pressures
            neighbor_rho = particle_rho[index]
            neighbor_rho_eff = wp.max(neighbor_rho, 0.09 * base_density)
            neighbor_pressure = isotropic_exp * (neighbor_rho_eff - base_density)

            # compute relative position
            relative_position = particle_x[index] - x

            # calculate pressure force
            pressure_force += diff_pressure_kernel(
                relative_position, pressure, neighbor_pressure, neighbor_rho_eff, smoothing_length
            )

            # compute kernel derivative
            viscous_force += diff_viscous_kernel(relative_position, v, neighbor_v, neighbor_rho_eff, smoothing_length)

    # sum all forces
    force = pressure_normalization * pressure_force + viscous_normalization * viscous_force

    # add external potential (floor rho so free-surface / few-neighbor particles do not explode)
    particle_a[i] = force / rho_eff + wp.vec3(0.0, gravity, 0.0)


@wp.kernel
def apply_bounds(
    particle_x: wp.array[wp.vec3],
    particle_v: wp.array[wp.vec3],
    damping_coef: float,
    bmin: wp.vec3,
    bmax: wp.vec3,
):
    tid = wp.tid()

    x = particle_x[tid]
    v = particle_v[tid]

    if x[0] < bmin[0]:
        x = wp.vec3(bmin[0], x[1], x[2])
        v = wp.vec3(v[0] * damping_coef, v[1], v[2])
    if x[0] > bmax[0]:
        x = wp.vec3(bmax[0], x[1], x[2])
        v = wp.vec3(v[0] * damping_coef, v[1], v[2])
    if x[1] < bmin[1]:
        x = wp.vec3(x[0], bmin[1], x[2])
        v = wp.vec3(v[0], v[1] * damping_coef, v[2])
    if x[1] > bmax[1]:
        x = wp.vec3(x[0], bmax[1], x[2])
        v = wp.vec3(v[0], v[1] * damping_coef, v[2])
    if x[2] < bmin[2]:
        x = wp.vec3(x[0], x[1], bmin[2])
        v = wp.vec3(v[0], v[1], v[2] * damping_coef)
    if x[2] > bmax[2]:
        x = wp.vec3(x[0], x[1], bmax[2])
        v = wp.vec3(v[0], v[1], v[2] * damping_coef)

    particle_x[tid] = x
    particle_v[tid] = v


@wp.kernel
def apply_solid_box(
    particle_x: wp.array[wp.vec3],
    particle_v: wp.array[wp.vec3],
    solid_min: wp.vec3,
    solid_max: wp.vec3,
    damping: float,
):
    tid = wp.tid()
    x = particle_x[tid]
    v = particle_v[tid]

    outside = (
        x[0] < solid_min[0]
        or x[0] > solid_max[0]
        or x[1] < solid_min[1]
        or x[1] > solid_max[1]
        or x[2] < solid_min[2]
        or x[2] > solid_max[2]
    )
    if outside:
        return

    d_left = x[0] - solid_min[0]
    d_right = solid_max[0] - x[0]
    d_bot = x[1] - solid_min[1]
    d_top = solid_max[1] - x[1]
    d_back = x[2] - solid_min[2]
    d_front = solid_max[2] - x[2]

    m = d_left
    face = 0
    if d_right < m:
        m = d_right
        face = 1
    if d_bot < m:
        m = d_bot
        face = 2
    if d_top < m:
        m = d_top
        face = 3
    if d_back < m:
        m = d_back
        face = 4
    if d_front < m:
        m = d_front
        face = 5

    new_x = x
    new_v = v
    if face == 0:
        new_x = wp.vec3(solid_min[0], x[1], x[2])
        new_v = wp.vec3(v[0] * damping, v[1], v[2])
    if face == 1:
        new_x = wp.vec3(solid_max[0], x[1], x[2])
        new_v = wp.vec3(v[0] * damping, v[1], v[2])
    if face == 2:
        new_x = wp.vec3(x[0], solid_min[1], x[2])
        new_v = wp.vec3(v[0], v[1] * damping, v[2])
    if face == 3:
        new_x = wp.vec3(x[0], solid_max[1], x[2])
        new_v = wp.vec3(v[0], v[1] * damping, v[2])
    if face == 4:
        new_x = wp.vec3(x[0], x[1], solid_min[2])
        new_v = wp.vec3(v[0], v[1], v[2] * damping)
    if face == 5:
        new_x = wp.vec3(x[0], x[1], solid_max[2])
        new_v = wp.vec3(v[0], v[1], v[2] * damping)

    particle_x[tid] = new_x
    particle_v[tid] = new_v


@wp.kernel
def kick(particle_v: wp.array[wp.vec3], particle_a: wp.array[wp.vec3], dt: float):
    tid = wp.tid()
    v = particle_v[tid]
    particle_v[tid] = v + particle_a[tid] * dt


@wp.kernel
def drift(particle_x: wp.array[wp.vec3], particle_v: wp.array[wp.vec3], dt: float):
    tid = wp.tid()
    x = particle_x[tid]
    particle_x[tid] = x + particle_v[tid] * dt


@wp.kernel
def clamp_velocity(particle_v: wp.array[wp.vec3], v_max: float):
    tid = wp.tid()
    v = particle_v[tid]
    s = wp.sqrt(wp.dot(v, v))
    if s > v_max:
        particle_v[tid] = v * (v_max / s)


@wp.kernel
def initialize_particles(
    particle_x: wp.array[wp.vec3],
    smoothing_length: float,
    origin_x: float,
    origin_y: float,
    origin_z: float,
    span_x: float,
    span_y: float,
    span_z: float,
    nr_x: int,
    nr_y: int,
    nr_z: int,
):
    tid = wp.tid()

    iz = tid % nr_z
    iy = (tid // nr_z) % nr_y
    ix = tid // (nr_z * nr_y)

    fx = (float(ix) + 0.5) / float(nr_x)
    fy = (float(iy) + 0.5) / float(nr_y)
    fz = (float(iz) + 0.5) / float(nr_z)

    pos = wp.vec3(origin_x + fx * span_x, origin_y + fy * span_y, origin_z + fz * span_z)

    state = wp.rand_init(123, tid)
    pos = pos + 0.0001 * smoothing_length * wp.vec3(wp.randn(state), wp.randn(state), wp.randn(state))

    particle_x[tid] = pos


class Example:
    def __init__(self, stage_path=None, verbose=False):
        self.verbose = verbose
        self._is_usd = bool(stage_path)

        # render params
        fps = 60
        self.frame_dt = 1.0 / fps
        self.sim_time = 0.0

        # simulation domain: fixed axis-aligned cube [-3, 3]^3 (world units)
        self.box_min = (-3.0, -3.0, -3.0)
        self.box_max = (3.0, 3.0, 3.0)
        # Initial fluid: x,y ∈ [-3,3] filled; z spans 1.5 from bottom (z ∈ [-3, -1.5])
        self.fluid_z_thickness = 1.5
        self._fluid_origin = (-3.0, -3.0, -3.0)
        self._fluid_span_x = 6.0
        self._fluid_span_y = 6.0
        self._fluid_span_z = self.fluid_z_thickness

        # h scaled for ~6-unit domain (was 0.8 on ~96-unit tank)
        self.smoothing_length = 0.12
        self.isotropic_exp = 20.0
        self.base_density = 1.0
        self.particle_mass = 0.01 * self.smoothing_length**3
        self.dt = 0.0032 * self.smoothing_length
        self.dynamic_visc = 0.022
        self.damping_coef = -0.85
        self.gravity = -0.085
        self.point_draw_radius_scale = 0.48

        h = self.smoothing_length
        self._init_nr_x = max(2, int(self._fluid_span_x / h))
        self._init_nr_y = max(2, int(self._fluid_span_y / h))
        self._init_nr_z = max(2, int(self._fluid_span_z / h))
        self.n = self._init_nr_x * self._init_nr_y * self._init_nr_z
        # Match ~original physical time per frame vs reference dt = 0.01*h, base steps 32/h
        ref_dt = 0.01 * self.smoothing_length
        base_substeps = 32.0 / self.smoothing_length
        self.sim_step_to_frame_ratio = max(24, int(round(base_substeps * (ref_dt / self.dt))))

        # Obstacle inside the thin z slab (around z = -2)
        self.solid_min = (-0.4, -0.4, -2.35)
        self.solid_max = (0.4, 0.4, -1.95)
        # Fixed half-extents for drawing: avoids float jitter changing render_box hash and re-adding instances (Warp GL bug)
        _sx = float(self.solid_max[0]) - float(self.solid_min[0])
        _sy = float(self.solid_max[1]) - float(self.solid_min[1])
        _sz = float(self.solid_max[2]) - float(self.solid_min[2])
        self._solid_half = (0.5 * _sx, 0.5 * _sy, 0.5 * _sz)
        self._solid_gl_registered = False
        self._solid_render_color = (0.32, 0.34, 0.38)
        # Arrow keys move solid on XZ; speed is in world units per input tick (see OpenGLRenderer._process_inputs)
        self.solid_keyboard_speed = 0.035

        # constants
        self.density_normalization = (315.0 * self.particle_mass) / (
            64.0 * np.pi * self.smoothing_length**9
        )  # integrate density kernel
        self.pressure_normalization = -(45.0 * self.particle_mass) / (np.pi * self.smoothing_length**6)
        self.viscous_normalization = (45.0 * self.dynamic_visc * self.particle_mass) / (
            np.pi * self.smoothing_length**6
        )

        # allocate arrays
        self.x = wp.empty(self.n, dtype=wp.vec3)
        self.v = wp.zeros(self.n, dtype=wp.vec3)
        self.rho = wp.zeros(self.n, dtype=float)
        self.a = wp.zeros(self.n, dtype=wp.vec3)

        # set random positions
        wp.launch(
            kernel=initialize_particles,
            dim=self.n,
            inputs=[
                self.x,
                self.smoothing_length,
                float(self._fluid_origin[0]),
                float(self._fluid_origin[1]),
                float(self._fluid_origin[2]),
                float(self._fluid_span_x),
                float(self._fluid_span_y),
                float(self._fluid_span_z),
                self._init_nr_x,
                self._init_nr_y,
                self._init_nr_z,
            ],
        )

        grid_size = int(
            np.ceil(
                max(
                    self.box_max[0] - self.box_min[0],
                    self.box_max[1] - self.box_min[1],
                    self.box_max[2] - self.box_min[2],
                )
                / (4.0 * self.smoothing_length)
            )
        )
        self.grid = wp.HashGrid(grid_size, grid_size, grid_size)

        # renderer: OpenGL window by default; USD when stage_path is set
        self.renderer = None
        if self._is_usd:
            self.renderer = wp.render.UsdRenderer(stage_path)
        else:
            target = np.array([0.0, 0.0, -2.2], dtype=np.float32)
            cam = np.array([8.0, 8.0, 6.0], dtype=np.float32)
            front = target - cam
            front = front / float(np.linalg.norm(front))
            self.renderer = wp.render.OpenGLRenderer(
                title="Warp SPH (arrows: move solid | WASD: camera)",
                device=wp.get_device(),
                fps=fps,
                screen_width=1280,
                screen_height=720,
                near_plane=0.1,
                far_plane=80.0,
                camera_fov=55.0,
                camera_pos=tuple(float(x) for x in cam),
                camera_front=tuple(float(x) for x in front),
                camera_up=(0.0, 1.0, 0.0),
                draw_grid=True,
            )
            self.renderer.register_input_processor(self._solid_arrow_block_camera)

    def _move_solid(self, dx: float, dy: float, dz: float):
        mn = [float(self.solid_min[0]) + dx, float(self.solid_min[1]) + dy, float(self.solid_min[2]) + dz]
        mx = [float(self.solid_max[0]) + dx, float(self.solid_max[1]) + dy, float(self.solid_max[2]) + dz]
        sx = mx[0] - mn[0]
        sy = mx[1] - mn[1]
        sz = mx[2] - mn[2]
        bmin = self.box_min
        bmax = self.box_max
        for i in range(3):
            if mn[i] < bmin[i]:
                mn[i] = bmin[i]
                mx[i] = mn[i] + (sx, sy, sz)[i]
            if mx[i] > bmax[i]:
                mx[i] = bmax[i]
                mn[i] = mx[i] - (sx, sy, sz)[i]
        self.solid_min = (mn[0], mn[1], mn[2])
        self.solid_max = (mx[0], mx[1], mx[2])

    def _solid_keyboard_update(self):
        """Apply arrow-key motion before drawing so render_box matches physics this frame."""
        if self._is_usd or self.renderer is None:
            return
        import pyglet

        kh = self.renderer._key_handler
        speed = self.solid_keyboard_speed * max(0.15, min(4.0, float(getattr(self.renderer, "_frame_speed", 1.0))))
        dx = dz = 0.0
        if kh[pyglet.window.key.LEFT]:
            dx -= speed
        if kh[pyglet.window.key.RIGHT]:
            dx += speed
        if kh[pyglet.window.key.UP]:
            dz += speed
        if kh[pyglet.window.key.DOWN]:
            dz -= speed
        if dx != 0.0 or dz != 0.0:
            self._move_solid(dx, 0.0, dz)

    def _solid_arrow_block_camera(self, key_handler):
        """Prevent OpenGLRenderer from using arrow keys for camera (solid uses them)."""
        if self._is_usd:
            return None
        import pyglet

        if (
            key_handler[pyglet.window.key.LEFT]
            or key_handler[pyglet.window.key.RIGHT]
            or key_handler[pyglet.window.key.UP]
            or key_handler[pyglet.window.key.DOWN]
        ):
            return pyglet.event.EVENT_HANDLED
        return None

    def step(self):
        with wp.ScopedTimer("step"):
            for _ in range(self.sim_step_to_frame_ratio):
                with wp.ScopedTimer("grid build", active=self.verbose):
                    # build grid
                    self.grid.build(self.x, self.smoothing_length)

                with wp.ScopedTimer("forces", active=self.verbose):
                    # compute density of points
                    wp.launch(
                        kernel=compute_density,
                        dim=self.n,
                        inputs=[self.grid.id, self.x, self.rho, self.density_normalization, self.smoothing_length],
                    )

                    # get new acceleration
                    wp.launch(
                        kernel=get_acceleration,
                        dim=self.n,
                        inputs=[
                            self.grid.id,
                            self.x,
                            self.v,
                            self.rho,
                            self.a,
                            self.isotropic_exp,
                            self.base_density,
                            self.gravity,
                            self.pressure_normalization,
                            self.viscous_normalization,
                            self.smoothing_length,
                        ],
                    )

                    # apply bounds
                    wp.launch(
                        kernel=apply_bounds,
                        dim=self.n,
                        inputs=[
                            self.x,
                            self.v,
                            self.damping_coef,
                            wp.vec3(*self.box_min),
                            wp.vec3(*self.box_max),
                        ],
                    )

                    wp.launch(
                        kernel=apply_solid_box,
                        dim=self.n,
                        inputs=[
                            self.x,
                            self.v,
                            wp.vec3(*self.solid_min),
                            wp.vec3(*self.solid_max),
                            self.damping_coef,
                        ],
                    )

                    # kick
                    wp.launch(kernel=kick, dim=self.n, inputs=[self.v, self.a, self.dt])

                    # drift
                    wp.launch(kernel=drift, dim=self.n, inputs=[self.x, self.v, self.dt])

                    wp.launch(
                        kernel=clamp_velocity,
                        dim=self.n,
                        inputs=[self.v, 5.0],
                    )

            self.sim_time += self.frame_dt

    def render(self):
        if self.renderer is None:
            return

        with wp.ScopedTimer("render"):
            self._solid_keyboard_update()
            self.renderer.begin_frame(self.sim_time)
            mn, mx = self.solid_min, self.solid_max
            center = (0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), 0.5 * (mn[2] + mx[2]))
            rot = (0.0, 0.0, 0.0, 1.0)
            col = self._solid_render_color
            if self._is_usd:
                self.renderer.render_box("solid_obstacle", center, rot, self._solid_half, color=col)
            else:
                r = self.renderer
                if self._solid_gl_registered:
                    r.update_shape_instance(
                        "solid_obstacle",
                        center,
                        rot,
                        color1=col,
                        color2=col,
                    )
                else:
                    r.render_box("solid_obstacle", center, rot, self._solid_half, color=col)
                    self._solid_gl_registered = True
            water_color = (0.12, 0.52, 0.88)
            r_draw = float(self.smoothing_length * self.point_draw_radius_scale)
            if self._is_usd:
                self.renderer.render_points(
                    points=self.x.numpy(),
                    radius=r_draw,
                    name="points",
                    colors=water_color,
                )
            else:
                self.renderer.render_points(
                    "points",
                    self.x,
                    r_draw,
                    colors=water_color,
                )
            self.renderer.end_frame()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--device", type=str, default=None, help="Override the default Warp device.")
    parser.add_argument(
        "--stage-path",
        type=lambda x: None if x in ("None", "") else str(x),
        default=None,
        help="If set, record USD to this path. If omitted, opens an interactive OpenGL window (requires pyglet >= 2).",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=None,
        help="Frame count. Default: 480 for USD, unlimited (until window close) for OpenGL. Use 0 for unlimited in both modes.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print out additional status messages during execution.")

    args = parser.parse_known_args()[0]

    with wp.ScopedDevice(args.device):
        example = Example(stage_path=args.stage_path, verbose=args.verbose)

        num_frames = args.num_frames
        if num_frames is None:
            num_frames = 480 if example._is_usd else 0

        frame = 0
        unlimited = num_frames <= 0
        while example.renderer is not None and (example._is_usd or example.renderer.is_running()):
            if not unlimited and frame >= num_frames:
                break
            example.render()
            example.step()
            frame += 1

        if example.renderer:
            if example._is_usd:
                example.renderer.save()
            else:
                example.renderer.close()
