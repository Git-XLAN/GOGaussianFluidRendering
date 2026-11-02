
cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
}
Texture2D<float4> NormalTex;
Texture2D<float4> EnvTex;
Texture2D<float> ThicknessTex;
SamplerState Sampler;

cbuffer WaterMaterial {
    float IOR;
    float3 Tr;
    float F0;
    float TrStrenth;
    float minThickness;
    float maxThickness;
    float Roughness;
    bool useBlur;
}

#define PI 3.1415926
float2 directionToLatLong(float3 dir)
{
    float2 uv;
    uv.x = atan2(dir.z, dir.x) * (0.5f / PI) + 0.5f;
    uv.y = acos(clamp(dir.y, -1.0, 1.0)) * (1.0f / PI);
    return uv;
}

float GetFresnel(float cost, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cost, 5.0);
}

float4 main(float2 TexC: TEXCOORD) : SV_Target {
    float2 ndc = float2(TexC.x,1.0-TexC.y) * 2 - 1.0;
    float3 dir = normalize(ndc.x * U + ndc.y * V + W);
    float3 normal = NormalTex.Sample(Sampler, TexC).xyz;

    float IdotN = abs(dot(dir, normal));
    float thickness = ThicknessTex.Sample(Sampler, TexC);
    thickness = thickness * IdotN;

    thickness = min(maxThickness, thickness);
    thickness = max(minThickness, thickness);

    float lod = (thickness - minThickness)/(maxThickness-minThickness) * 13.0f;

    if (all(normal == 0)) {
        float2 uv = directionToLatLong(dir);
        float3 Color = EnvTex.Sample(Sampler, uv).xyz;
        return float4(Color, 1.0f);
    }

    float fresnel = GetFresnel(IdotN, F0);

    float3 refrDir = refract(dir, normal, 1.0/IOR);
    float3 reflDir = reflect(dir, normal);
    float2 uv = directionToLatLong(refrDir);

    float3 refrColor = useBlur ? (1.0 - fresnel) * EnvTex.SampleLevel(Sampler, uv, lod).xyz : (1.0 - fresnel) * EnvTex.Sample(Sampler, uv).xyz;

    refrColor = refrColor * exp(-Tr * TrStrenth*thickness);

    uv = directionToLatLong(reflDir);
    float3 reflColor = fresnel*EnvTex.SampleLevel(Sampler, uv,13.0f*Roughness).xyz;
    float3 Color = reflColor + refrColor;

    return float4(Color, 1.0f);
}
