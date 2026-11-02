RWStructuredBuffer<half4>NormalDepthTex;

float4 SampleBuffer(int2 coord) {
    uint id = coord.y * Width + coord.x;
    return float4(NormalDepthTex[id]);
}
cbuffer CameraData {
    float3 CamPos;
    float3 U;
    float3 V;
    float3 W;
}

float3 getWorldPos(int2 coord) {
    if (coord.x < 0) coord.x = 0;
    if (coord.y < 0) coord.y = 0;
    if (coord.x >= Width) coord.x = Width - 1;
    if (coord.y >= Height) coord.y = Height - 1;

    float depth = SampleBuffer(coord).w;

    if (depth == 0) return float3(1000, 1000, 1000);
    float2 uv = coord / (float2(Width, Height));
    float2 ndc = float2(uv.x, 1.0 - uv.y) * 2 - 1.0;
    float3 dir = normalize(ndc.x * U + ndc.y * V + W);

    return CamPos + dir * depth;
}

[numthreads(32, 32, 1)]
void Recover(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
             uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex)
{
    int2 coord = dispatchThreadID.xy;

    if (coord.x >= Width || coord.y >= Height) { return;}

    float3 posW = getWorldPos(coord);

    float3 posWxp = getWorldPos(coord + int2(1, 0));
    float3 posWxn = getWorldPos(coord - int2(1, 0));
    float3 posWyp = getWorldPos(coord + int2(0, 1));
    float3 posWyn = getWorldPos(coord - int2(0, 1));

    float3 dxl = posW - posWxn;
    float3 dxr = posWxp - posW;

    if (all(dxl == 0)) dxl.z = 1000;
    if (all(dxr == 0)) dxr.z = 1000;

    float3 dx = (abs(dxr.z) < abs(dxl.z)) ? dxr : dxl;

    float3 dyb = posW - posWyn;
    float3 dyt = posWyp - posW;

    if (all(dyb == 0)) dyb.z = 1000;
    if (all(dyt == 0)) dyt.z = 1000;

    float3 dy = (abs(dyt.z) < abs(dyb.z)) ? dyt : dyb;

    float3 N = normalize(cross(dy, dx));

    uint id = coord.y * Width + coord.x;
    float3 nor = NormalDepthTex[id].xyz;
    float depth = NormalDepthTex[id].w;

    NormalDepthTex[id] = half4(N, depth);

}
