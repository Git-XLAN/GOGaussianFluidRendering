// RealTimeFluidRendering depth-pass (isotropic), from Shaders/depth-pass-equiv-falcor.hlsl.
// Draw: TriangleList, 6 vertices / instance. RT: RGBA32F — RGB = view-space Z, A = 1.

static const float kClearDepthValue = -1000000.0f;

cbuffer GlobalVar {
    float g_PointRadius;
    int g_ScreenWidth;
    int g_ScreenHeight;
    int g_NdcYScaleSign;
};

cbuffer CameraData {
    float4x4 gView;
    float4x4 gProj;
};

StructuredBuffer<float3> gParticleBuffer;

static const float2 kQuadUV[6] = {
    float2(0, 0), float2(1, 0), float2(1, 1),
    float2(0, 0), float2(1, 1), float2(0, 1)
};

struct VsOut {
    float4 posH : SV_Position;
    float3 f_ViewCenter : VIEWCENTER;
    float2 f_PointCoord : SPRCOORD;
};

struct PsOut {
    float4 color : SV_Target;
    float depth : SV_Depth;
};

float4 MulD(float4 v) {
    return float4(v.x, v.y, v.z, -v.w);
}

float4 PVT_RowForQuadric(float4x4 P, float4x4 V, float4x4 T, int rowIndex) {
    float4x4 PVT = mul(mul(P, V), T);
    return float4(PVT[rowIndex][0], PVT[rowIndex][1], PVT[rowIndex][2], PVT[rowIndex][3]);
}

float ComputePointSizePixels(float4x4 P, float4x4 V, float4x4 T) {
    float4 c0 = PVT_RowForQuadric(P, V, T, 0);
    float4 c1 = PVT_RowForQuadric(P, V, T, 1);
    float4 c3 = PVT_RowForQuadric(P, V, T, 3);

    float A  = dot(c3, MulD(c3));
    float B  = -2.0 * dot(c0, MulD(c3));
    float C0 = dot(c0, MulD(c0));
    float disc = B * B - 4.0 * A * C0;
    float sx = 0;
    if (disc > 0 && abs(A) > 1e-20) {
        float s = sqrt(disc);
        float x0 = (-B - s) / (2.0 * A);
        float x1 = (-B + s) / (2.0 * A);
        sx = abs(x0 - x1) * 0.5 * (float)g_ScreenWidth;
    }

    A  = dot(c3, MulD(c3));
    B  = -2.0 * dot(c1, MulD(c3));
    C0 = dot(c1, MulD(c1));
    disc = B * B - 4.0 * A * C0;
    float sy = 0;
    if (disc > 0 && abs(A) > 1e-20) {
        float s = sqrt(disc);
        float y0 = (-B - s) / (2.0 * A);
        float y1 = (-B + s) / (2.0 * A);
        sy = abs(y0 - y1) * 0.5 * (float)g_ScreenHeight;
    }

    return ceil(max(sx, sy));
}

VsOut Vs_Main(uint vtxId : SV_VertexID, uint instanceId : SV_InstanceID) {
    VsOut o = (VsOut)0;

    float3 posW = gParticleBuffer[instanceId];
    float2 sprUv = kQuadUV[vtxId % 6];

    float4 eyeCoord = mul(gView, float4(posW, 1.0));
    float r = g_PointRadius;

    float4x4 T = float4x4(
        float4(r, 0, 0, posW.x),
        float4(0, r, 0, posW.y),
        float4(0, 0, r, posW.z),
        float4(0, 0, 0, 1));

    float pointSize = ComputePointSizePixels(gProj, gView, T);
    float4 clipCenter = mul(gProj, eyeCoord);

    float2 ndcCorner = (sprUv - 0.5) * 2.0;
    float ySign = (g_NdcYScaleSign >= 0) ? 1.0 : -1.0;
    float2 pixelToNdc = float2(2.0 / (float)g_ScreenWidth, ySign * (2.0 / (float)g_ScreenHeight));

    clipCenter.xy += ndcCorner * (0.5 * pointSize) * clipCenter.w * pixelToNdc;

    o.posH = clipCenter;
    o.f_ViewCenter = eyeCoord.xyz;
    o.f_PointCoord = sprUv;
    return o;
}

PsOut Ps_Main(VsOut input) {
    PsOut ps = (PsOut)0;

    // Isotropic splat (depth-pass.fs.glsl u_UseAnisotropyKernel == 0); buffer is float3 only.
    float3 normalT;
    normalT.xy = input.f_PointCoord.xy * float2(2.0, -2.0) + float2(-1.0, 1.0);
    float mag = dot(normalT.xy, normalT.xy);
    if (mag > 1.0)
        discard;
    normalT.z = sqrt(1.0 - mag);
    float3 fragPos = input.f_ViewCenter + normalT * g_PointRadius;

    float4 clipSpacePos = mul(gProj, float4(fragPos, 1.0));
    float vz = fragPos.z;
    ps.color = float4(vz, vz, vz, 1.0);
    ps.depth = clipSpacePos.z / (clipSpacePos.w + 1e-4f);
    (void)kClearDepthValue;
    return ps;
}
