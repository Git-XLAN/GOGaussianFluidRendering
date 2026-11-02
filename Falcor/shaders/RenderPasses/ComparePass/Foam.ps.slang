
cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
}
Texture2D<float4> NormalTex;
Texture2D<float4> EnvTex;

Texture2D<float> Depth;
Texture2D<float4> Water;
SamplerState Sampler;

cbuffer FoamMaterial {
    float bigIOR, smallIOR;
    float3 bigEmissive, smallEmissive;
    float bigF0, smallF0;
    float bigStrenth, smallStrenth;
    float bigRoughness, smallRoughness;
    float bigPower, smallPower;
}

#define PI 3.1415926
float2 directionToLatLong(float3 dir)
{
    float2 uv;
    uv.x = atan2(dir.z, dir.x) * (0.5f / PI) + 0.5f;
    uv.y = acos(clamp(dir.y, -1.0, 1.0)) * (1.0f / PI);
    return uv;
}

float GetFresnel(float cost, float F0,float ex) {
    return F0 + (1.0 - F0) * pow(1.0 - cost, ex);
}

float4 main(float2 TexC: TEXCOORD) : SV_Target {
    float2 ndc = float2(TexC.x,1.0-TexC.y) * 2 - 1.0;
    float3 dir = normalize(ndc.x * U + ndc.y * V + W);

    float4 normalFlag = NormalTex.Sample(Sampler, TexC);
    float3 normal = normalFlag.xyz;
    float flag = normalFlag.w;

    float IdotN = abs(dot(dir, normal));
    float3 reflDir = reflect(dir, normal);
    float2 uv;
    float fresnel;
    float3 refracDir;
    float3 reflecColor, refracColor;
    float3 emissionColor, Color;
    if (flag == 2.0f) {
        // Small
        fresnel = GetFresnel(IdotN, smallF0, smallPower);
        refracDir = refract(dir, normal, 1.0 / smallIOR);
        refracColor = (1.0 - fresnel) * Water.SampleLevel(Sampler, TexC, 0).xyz;
        uv = directionToLatLong(reflDir);
        reflecColor = fresnel * EnvTex.SampleLevel(Sampler, uv, smallRoughness * 13.0f).xyz;
        emissionColor = smallEmissive * smallStrenth;
        Color = refracColor + reflecColor + emissionColor;
    }
    else if (flag == 3.0f) {
        //Big
        fresnel = GetFresnel(IdotN, bigF0, bigPower);
        refracDir = refract(dir, normal, 1.0 / bigIOR);
        refracColor = (1.0 - fresnel) * Water.SampleLevel(Sampler, TexC, 0).xyz;
        uv = directionToLatLong(reflDir);
        reflecColor = fresnel * EnvTex.SampleLevel(Sampler, uv, bigRoughness * 13.0f).xyz;
        emissionColor = bigEmissive * bigStrenth;
        Color = refracColor + reflecColor + emissionColor;
    }
    else {
        return Water.SampleLevel(Sampler, TexC, 0);
    }
    return float4(Color, 1.0f);

}
