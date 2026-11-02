struct VSIn
{
    float3 pos    : POSITION;
    float3 normal : NORMAL;
};

struct VSOut {
    float4 pos : SV_Position;
    float2 uv : TEXCOORD0;
    float radius : TEXCOORD1;
    float inShadow : TEXCOORD2;
};

cbuffer CameraData {
    float4x4 gViewMat;
    float4x4 gProjMat;
    float4x4 gVPMat;
    float3 camRight;
    float3 camUp;
    float3 camPos;
}

cbuffer GlobalVar {
    float ParticleRadius;
    uint ParticleNum;
}

StructuredBuffer<half3> gParticleBuffer;

Texture2D<float> BGDepth;

VSOut VSmain(uint vID: SV_VertexID, uint instID: SV_InstanceID) {

    VSOut out;
    
    float3 pPos = gParticleBuffer[instID];
    float4 clipPos = mul(gVPMat, float4(pPos, 1.0f));

    float3 ndc = clipPos.xyz / clipPos.w;
    ndc.y *= -1.0f;

    uint2 screenCoord = uint2((ndc.xy * 0.5 + 0.5) * float2(Width, Height));
    screenCoord = clamp(screenCoord, uint2(0, 0), uint2(Width - 1, Height - 1));

    float2 corners[4] = {
        float2(-1, -1), float2(1, -1),
        float2(-1, 1), float2(1, 1)
    };
    float2 cornerPos = corners[vID];

    float3 posWS = pPos + (normalize(camRight) * cornerPos.x + normalize(camUp) * cornerPos.y) * ParticleRadius;

    out.pos = mul(gVPMat, float4(posWS, 1.0f));

    out.uv = cornerPos;
    out.radius = ParticleRadius;
    out.inShadow = 0.0f;

    float depth = distance(pPos, camPos);
    if (depth > BGDepth[screenCoord]) {
        out.inShadow = 1.0f;
    }
    return out;
}

float PSmain(VSOut input) : SV_Target {
    float d2 = dot(input.uv, input.uv);

    if (d2 > 1.0f) discard;
    float thickness = 2.0 * input.radius * sqrt(1.0 - d2);

    return thickness * (1.0 - input.inShadow);
}

