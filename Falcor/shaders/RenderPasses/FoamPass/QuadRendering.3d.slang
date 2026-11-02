import Scene.Scene;
import Scene.Shading;
#include "Scene/VertexAttrib.slangh"
import Scene.ShadingData;
import Scene.Raster;
import Utils.Sampling.SampleGenerator;
import Rendering.Lights.LightHelpers;
import Utils.Math.MathHelpers;
import Utils.Sampling.UniformSampleGenerator;

struct VS_Out {
    float4 pos : SV_Position;
    float2 uv : TEXCOORD0;
};
cbuffer CameraData {
    float4x4 inViewMat;
    float3 U;
    float3 V;
    float3 W;
}

cbuffer FoamMat {
    float roughness;
    float F0;
    float intensity;
    float ior;
    float edgeSoftness;
}

cbuffer GlobalVar {
    float gBulge;
    int mode;
}

struct EnvParamerter {
    EnvMap SceneEnvMap;
    int mipCount;
}
ParameterBlock<EnvParamerter> gData;

VS_Out VSmain(uint vID: SV_VertexID) {

    VS_Out output;

    output.uv = float2((vID << 1) & 2, vID & 2);
    output.pos = float4(output.uv * 2.0f - 1.0f, 0.0f, 1.0f);
    //output.uv.y = 1.0f - output.uv.y;
    return output;
}

float GetFresnel(float cost, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cost, 5.0);
}

float4 PSmain(VS_Out input): SV_Target {

    float2 localXY = input.uv * 2.0f - 1.0f;

    float3 dir = normalize(localXY.x * U + localXY.y * V + W);

    float rSq = dot(localXY, localXY);
    float dist = sqrt(rSq);
    float alpha = 1.0f - smoothstep(1.0f - edgeSoftness, 1.0f, dist);

    if (rSq > 1.0f) {
        discard;
    }

    float localZ = sqrt(1.0f - rSq);

    float3 N_view = normalize(float3(localXY, localZ * gBulge));

    float3 N_world = mul(inViewMat, float4(N_view, 0.0f)).xyz;

    if (mode == 1) {
        return float4(N_world, 1.0f);
    }

    float3 refleDir = reflect(dir, N_world);
    float3 refraDir = refract(dir, N_world, 1.0 / ior);
    float3 refColor = gData.SceneEnvMap.eval(refleDir, int(gData.mipCount * roughness));
    float3 refrColor = gData.SceneEnvMap.eval(refraDir, int(gData.mipCount * roughness));

    float IdotN = abs(dot(dir, N_world));
    float fresnel = GetFresnel(IdotN, F0);

    float3 Color = fresnel * refColor + (1.0 - fresnel) * refrColor;

    return float4(intensity * Color, alpha);
}
