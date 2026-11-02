
cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
    bool useGT;
    float bias;
}
import Scene.Shading;
struct SSRParamerter {
    EnvMap SceneEnvMap;
}
ParameterBlock<SSRParamerter> gData;

Texture2D<float4> NormalTex;
Texture2D<float4> EnvTex;
Texture2D<float> BackDepth;

Texture2D<float> Depth;
Texture2D<float4> Water;
Texture2D<float4> WaterDepth;
SamplerState Sampler;

cbuffer FoamMaterial {
    float bigIOR, smallIOR;
    float3 bigEmissive, smallEmissive;
    float bigF0, smallF0;
    float bigStrenth, smallStrenth;
    float bigRoughness, smallRoughness;
    float bigPower, smallPower;
    float3 Tr;
    float TrStrenth;
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

    float d = Depth.Sample(Sampler, TexC);
    float waterD = WaterDepth.Sample(Sampler, TexC).w;
    float backD = BackDepth.Sample(Sampler,TexC);

    float3 ColorUnder;

    if (d < waterD && d < backD) {
        ColorUnder = float3(1.0f, 1.0f, 1.0f);
    }
    else {
        if (d > waterD && d < waterD + bias && d < backD) {
            ColorUnder = exp(-Tr * (d - waterD));
        }
        else {
            return Water.SampleLevel(Sampler, TexC, 0);
        }
    }

    
    

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
        //uv = directionToLatLong(reflDir);
        //reflecColor = fresnel * EnvTex.SampleLevel(Sampler, uv, smallRoughness * 13.0f).xyz;
        reflecColor = fresnel * gData.SceneEnvMap.eval(reflDir, smallRoughness * 13.0f);
        emissionColor = smallEmissive * smallStrenth;
        Color = refracColor + reflecColor + emissionColor;
    }
    else if (flag == 3.0f) {
        //Big
        fresnel = GetFresnel(IdotN, bigF0, bigPower);
        refracDir = refract(dir, normal, 1.0 / bigIOR);
        refracColor = (1.0 - fresnel) * Water.SampleLevel(Sampler, TexC, 0).xyz;
        // uv = directionToLatLong(reflDir);
        // reflecColor = fresnel * EnvTex.SampleLevel(Sampler, uv, bigRoughness * 13.0f).xyz;
        reflecColor = fresnel * gData.SceneEnvMap.eval(reflDir, bigRoughness * 13.0f);
        emissionColor = bigEmissive * bigStrenth;
        Color = refracColor + reflecColor + emissionColor;
    }
    else {
        return Water.SampleLevel(Sampler, TexC, 0);
    }
    return float4(ColorUnder*Color, 1.0f);

}
