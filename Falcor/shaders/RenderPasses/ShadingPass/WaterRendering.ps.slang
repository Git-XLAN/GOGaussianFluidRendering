import Scene.Scene;
import Scene.Shading;
#include "Scene/VertexAttrib.slangh"
import Scene.ShadingData;
import Scene.Raster;
import Utils.Sampling.SampleGenerator;
import Rendering.Lights.LightHelpers;
import Utils.Math.MathHelpers;
import Utils.Sampling.UniformSampleGenerator;

StructuredBuffer<half4> NormalDepthTex;
Texture2D<float> BgDepthTex;
Texture2D<float4> BgColorTex;
Texture2D<float> ThicknessTex;
Texture2D<float4> FoamColorTex;
SamplerState Sampler;

cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
    float3 CamPos;
}

cbuffer WaterMat {
    float IOR;
    float3 TrColor;
    float F0;
    float TrStrenth;
    float roughness;
    float refractStrenth;
}
cbuffer GlobalVar {
    uint Mode;

    float3 LightPos;
    float3 ambientColor;
    float3 lightColor;
    float3 diffColor;
    float diffuseStrength;
    float shininess;
    float specularStrength;
    float attenuationIntensity;
    uint SelectBuffer;
}

struct EnvParamerter {
    EnvMap SceneEnvMap;
    int mipCount;
}
ParameterBlock<EnvParamerter> gData;

float GetFresnel(float cost, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cost, 5.0);
}

float3 computeAttennuation(float thickness)
{
    return exp(-TrColor * TrStrenth * thickness);
}

float4 computeFoamLight(float2 TexC) {
    return FoamColorTex.Sample(Sampler, TexC);
}

float4 main(float2 TexC: TEXCOORD) : SV_Target {
    uint2 coord = uint2(TexC * uint2(Width, Height));
    uint id = coord.y * Width + coord.x;
    float4 normalDepth = NormalDepthTex[id];

    float3 N = normalDepth.xyz;

    float2 ndc = float2(TexC.x, 1.0 - TexC.y) * 2 - 1.0;
    float3 dir = normalize(ndc.x * U + ndc.y * V + W);
    float thickness = ThicknessTex.Sample(Sampler, TexC);
    float4 foamColor = computeFoamLight(TexC);

    if (dot(N, dir) > 0) N = -1.0 * N;

    if (Mode == 4) {
        if (SelectBuffer == 0) {
            return float4(thickness, thickness, thickness, 1.0f);
        }
        else if (SelectBuffer == 1) {
            return float4(normalDepth.w, 0.0f, 0.0f, 1.0f);
        }
        else if (SelectBuffer == 2) {
            return float4(foamColor.xyz, 1.0f);
        }
    }

    if (Mode == 5) {
        if (all(N == 0)) return float4(0.0f,0.0f,0.0f,1.0f);
        float3 pos = CamPos + dir * normalDepth.w;
        float3 viewDir = -dir;
        float3 L = normalize(LightPos - pos);
        float3 H = normalize(viewDir + L);

        float3 ambient = ambientColor;
        float diffuseFactor = max(dot(N, L), 0.1);
        float3 diff = diffColor*lightColor * diffuseStrength * diffuseFactor;
        float specularFactor = pow(max(dot(N, H), 0.1), shininess);
        float3 specular = lightColor * specularStrength * specularFactor;

        float distance = length(LightPos - pos);
        float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);

        float3 lighting = (diff + specular);// * attenuationIntensity * attenuation;
        float3 finalColor = ambient + lighting;
        return float4(finalColor, 1.0f);

    }

    
    if (Mode == 1) {
        //if (all(N == 0)) return foamColor;
        return float4(N, 1.0f);
    }

    if (Mode == 2) {
        if (all(foamColor == 0)) return float4(0.0f, 0.0f, 0.0f, 1.0f);
        return foamColor;
    }

    float Depth = normalDepth.w;

    
    float bgDepth = BgDepthTex.Sample(Sampler, TexC);
    float4 bgColor = BgColorTex.Sample(Sampler, TexC);

    if (Mode == 3) {
        return bgColor;
    }

    if (bgDepth < Depth || Depth == 0) {
        return float4(bgColor.xyz + foamColor.xyz, 1.0f);
    }

    

    

    float IdotN = abs(dot(dir, N));
    IdotN = clamp(IdotN, 0.0f, 0.99f);
    float fresnel = GetFresnel(IdotN, F0);

    float3 refrDir = refract(dir, N, 1.0 / IOR);
    float3 reflDir = reflect(dir, N);

    float3 refractColor = BgColorTex.Sample(Sampler, TexC + refrDir.xy * thickness * refractStrenth * 0.1f).xyz;

    float3 colorAttnnuation = computeAttennuation(thickness * 5.0f);
    float3 reflectColor = fresnel * gData.SceneEnvMap.eval(reflDir,int(gData.mipCount*roughness));

    refractColor = (1.0 - fresnel) * colorAttnnuation * refractColor;

    return float4(((refractColor + reflectColor)*(1.0f-foamColor.w) + foamColor.xyz*foamColor.w), 1.0f);
    //return normalDepth;
}
