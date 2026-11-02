struct mVsOut {
    float4 posH : SV_Position;
    float3 centerW : CENTERW;
    float2 uv : TEXCOORD;
    float radius : RADIUS;
}

cbuffer GlobalVar {
    float radius;
}
cbuffer CameraData {
    float4x4 gVPMat;
    float3 camRight;
    float3 camUp;
    float3 camFront;
    float3 camPos;
    float4x4 inViewMat;
}

StructuredBuffer<float3> gParticleBuffer;
StructuredBuffer<uint> gSurfaceIdX;
struct PS_OUT {
    float4 color : SV_Target; // 输出到 RenderTarget 的颜色
    float depth : SV_Depth;   // 显式写入深度缓冲 (用于伪球体)
};

mVsOut Vs_Main(uint vtxId : SV_VertexID, uint instanceId : SV_InstanceID) {
    mVsOut out;

    uint id = gSurfaceIdX[instanceId];
    float3 pPos = gParticleBuffer[id];
    float2 offset = float2(vtxId & 1, (vtxId >> 1) & 1) * 2.0 - 1.0;

    float3 posW = pPos + (normalize(camRight) * offset.x + normalize(camUp) * offset.y) * radius;

    float4 clipPosW = mul(gVPMat, float4(posW, 1.0f));

    out.posH = clipPosW;
    out.centerW = pPos;
    out.uv = offset;
    out.radius = radius;
    return out;
}

PS_OUT Ps_Main(mVsOut input){

    PS_OUT out;

    float d2 = dot(input.uv, input.uv);
    if (d2 > 1.0) discard;

    float normalZ = sqrt(1.0 - d2);
    float3 localNormal = float3(input.uv, normalZ); 

    float3 viewDir = normalize(camPos - input.centerW);
    float3 sphereSurfaceW = input.centerW + viewDir * (normalZ * input.radius);

    float4 clipPos = mul(gVPMat,float4(sphereSurfaceW, 1.0));

    out.depth = clipPos.z / (clipPos.w + 1e-4); // 输出精确的球面深度
    out.color = float4(length(sphereSurfaceW - camPos), 0.0f, 0.0f, 1.0f);

    return out;
}
