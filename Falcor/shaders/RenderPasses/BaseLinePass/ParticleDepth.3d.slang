// 与 ParticleFilterPass/ParticleDepth3d.slang 完全一致；BaseLinePass 仅使用此深度阶段。

struct mVsOut {
    float4 posH : SV_Position;
    float3 centerV : CENTERW;
    float2 uv : TEXCOORD;
    float radius : RADIUS;
    uint id : ID;
}

cbuffer GlobalVar {
    float radius;
}
cbuffer CameraData {
    float4x4 gVPMat;
    float4x4 gViewMat;
    float4x4 gProjMat;
    float3 camRight;
    float3 camUp;
    float3 camFront;
    float3 camPos;
    float4x4 inViewMat;
}

StructuredBuffer<float3> gParticleBuffer;

struct PS_OUT {
    float4 color : SV_Target;
    float depth : SV_Depth;
};

mVsOut Vs_Main(uint vtxId : SV_VertexID, uint instanceId : SV_InstanceID) {
    mVsOut out;

    float3 pPos = gParticleBuffer[instanceId];
    float2 offset = float2(vtxId & 1, (vtxId >> 1) & 1) * 2.0 - 1.0;

    float3 posW = pPos + (normalize(camRight) * offset.x + normalize(camUp) * offset.y) * radius;

    float4 clipPosW = mul(gVPMat, float4(posW, 1.0f));

    out.posH = clipPosW;
    out.centerV = mul(gViewMat, float4(pPos, 1.0f)).xyz;
    out.uv = float2(offset.y,offset.x);
    out.radius = radius;
    out.id = instanceId;
    return out;
}

PS_OUT Ps_Main(mVsOut input){

    PS_OUT out;

    float d2 = dot(input.uv, input.uv);
    if (d2 > 1.0) discard;

    float normalZ = sqrt(1.0 - d2);
    float3 localNormal = float3(input.uv, normalZ);
    float3 fragPos = input.centerV + localNormal * radius;
    float4 clipSpacePos = mul(gProjMat,float4(fragPos, 1.0f));

    out.depth = clipSpacePos.z / clipSpacePos.w;

    out.color = float4(abs(fragPos.z), fragPos.x, fragPos.y,1.0);
    return out;
    /*
    float3 pixelPosV = input.centerV;
    pixelPosV.xy += input.uv * input.radius;

    float3 rayDir = normalize(pixelPosV);
    float3 sphereCenterV = input.centerV;

    float3 L = -sphereCenterV;
    float b = dot(rayDir, L);
    float c = dot(L, L) - input.radius * input.radius;
    float h = b * b - c;

    if (h < 0.0) discard;

    float t = -b - sqrt(h); // 这里的 t 是从相机出发的距离

    float3 hitPosV = rayDir * t;
    float3 normalV = normalize(hitPosV - sphereCenterV);
    float3 normalW = mul(inViewMat, float4(normalV, 0.0f)).xyz;

    float4 clipPos = mul(gProjMat, float4(hitPosV, 1.0));

    out.depth = clipPos.z / clipPos.w;

    out.color = float4(abs(hitPosV.z),0.0f,0.0f, 1.0);
    //out.color = float4(normalW, 1.0f);
    return out;
    */
}
