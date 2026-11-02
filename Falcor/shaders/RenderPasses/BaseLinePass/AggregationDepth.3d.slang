StructuredBuffer<float3> gParticleBuffer;
StructuredBuffer<uint> AggregationFlags;

cbuffer GlobalVar
{
    float radius;
}

cbuffer CameraData
{
    float4x4 gVPMat;
    float4x4 gViewMat;
    float4x4 gProjMat;
    float4x4 inViewMat;
    float3 camRight;
    float3 camUp;
    float3 camPos;
    float3 camFront;
}

struct VsOut
{
    float4 posH : SV_Position;
    float3 centerV : TEXCOORD0;
    float2 uv : TEXCOORD1;
    uint id : TEXCOORD2;
};

struct PsOut
{
    float depth : SV_Depth;
    float color : SV_Target;
};

VsOut Vs_Main(uint vtxId : SV_VertexID, uint instanceId : SV_InstanceID)
{
    VsOut out;
    const float3 p = gParticleBuffer[instanceId];
    const float2 offset = float2(vtxId & 1, (vtxId >> 1) & 1) * 2.0 - 1.0;
    const float3 posW = p + (normalize(camRight) * offset.x + normalize(camUp) * offset.y) * radius;
    out.posH = mul(gVPMat, float4(posW, 1.0));
    out.centerV = mul(gViewMat, float4(p, 1.0)).xyz;
    out.uv = float2(offset.y, offset.x);
    out.id = instanceId;
    return out;
}

PsOut Ps_Main(VsOut input)
{
    if (AggregationFlags[input.id] == 0) discard;

    const float d2 = dot(input.uv, input.uv);
    if (d2 > 1.0) discard;

    const float3 posV = input.centerV + float3(input.uv, sqrt(1.0 - d2)) * radius;
    const float4 clip = mul(gProjMat, float4(posV, 1.0));

    PsOut out;
    out.depth = clip.z / clip.w;
    // Dagg is an approximate stopping distance, in the same ray-distance convention as RayMarching.
    const float3 posW = mul(inViewMat, float4(posV, 1.0)).xyz;
    out.color = length(posW - camPos);
    return out;
}
