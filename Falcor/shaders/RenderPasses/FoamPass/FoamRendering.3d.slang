struct VSOut {
    float4 pos : SV_Position;
    float2 uv : TEXCOORD0;
    float radius : TEXCOORD1;
    float inShadow : TEXCOORD2;
    float4 underWater : TEXCOORD3;
};
struct FoamParticle {
    half3 position;
    half radius;
    half lifeTime;
    half3 vel;
}

cbuffer CameraData {
    float4x4 gVPMat;
    float3 camRight;
    float3 camUp;
    float3 camPos;
}

cbuffer waterMat {
    float3 TrColor;
    float TrStrenth;
}

cbuffer GlobalVar {
    float radiusMu;
    float emissiveSmallStrenth;
    float emissiveBigStrenth;
    float enlargeFactor;
}

Texture2D<float4> QuadTex;
Texture2D<float> BGDepth;

StructuredBuffer<half4> SurfaceVelDepth;
StructuredBuffer<FoamParticle> FoamParticleBuffer;
SamplerState sampler;

float3 computeAttennuation(float thickness)
{
    return exp(-TrColor * TrStrenth * thickness*0.1f);
}

VSOut VSmain(uint vID: SV_VertexID, uint instID: SV_InstanceID) {

    VSOut out;
    FoamParticle foamP = FoamParticleBuffer[instID];
    float3 pPos = foamP.position;
    float radius = foamP.radius;

    float4 clipPos = mul(gVPMat, float4(pPos, 1.0f));

    float3 ndc = clipPos.xyz / clipPos.w;
    ndc.y *= -1.0f;

    uint2 screenCoord = uint2((ndc.xy * 0.5 + 0.5) * float2(Width, Height));
    screenCoord = clamp(screenCoord, uint2(0, 0), uint2(Width - 1, Height - 1));

    uint id = screenCoord.y * Width + screenCoord.x;

    float waterD = SurfaceVelDepth[id].w;

    float2 corners[4] = {
        float2(-1, -1), float2(1, -1),
        float2(-1, 1), float2(1, 1)
    };
    float2 cornerPos = corners[vID];

    float3 posWS = pPos + (normalize(camRight) * cornerPos.x + normalize(camUp) * cornerPos.y) * radius;

    out.pos = mul(gVPMat, float4(posWS, 1.0f));

    out.uv = cornerPos;
    out.radius = radius;
    out.inShadow = 0.0f;

    float depth = distance(pPos, camPos);
    if (depth > BGDepth[screenCoord]) {
        out.inShadow = 1.0f;
    }
    out.underWater = float4(1.0f);
    //To Do：0.1 参数化
    if (waterD!=0 && depth > (waterD + 0.1f)) {
        out.underWater = float4(computeAttennuation(depth - waterD), 1.0f);
    }

    return out;
}

float4 PSmain(VSOut input) : SV_Target {

    float d2 = dot(input.uv, input.uv);

    if (d2 > 1.0f) discard;

    float4 emissive = float4(1.0f, 1.0f, 1.0f, 0.0f);

    emissive = (input.radius <= 2.65*radiusMu*enlargeFactor) ? emissive *emissiveSmallStrenth : emissive * emissiveBigStrenth;

    float2 texUV = input.uv / 2.0f + 0.5f;

    float4 result = (1.0-input.inShadow)*QuadTex.Sample(sampler, texUV);

    return result + emissive;
}
