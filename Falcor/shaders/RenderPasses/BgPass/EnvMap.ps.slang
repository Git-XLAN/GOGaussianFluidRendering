import Scene.Scene;
import Scene.Shading;
#include "Scene/VertexAttrib.slangh"
import Scene.ShadingData;
import Scene.Raster;
import Utils.Sampling.SampleGenerator;
import Rendering.Lights.LightHelpers;
import Utils.Math.MathHelpers;
import Utils.Sampling.UniformSampleGenerator;

Texture2D<float4> BgColor;
cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
}
struct EnvParamerter {
    EnvMap SceneEnvMap;
    int mipCount;
}
SamplerState sampler;
ParameterBlock<EnvParamerter> gData;


float4 main(float2 TexC: TEXCOORD) : SV_Target {
    float2 ndc = float2(TexC.x,1.0-TexC.y) * 2 - 1.0;

    float4 bg = BgColor.Sample(sampler, TexC);

    if (all(bg == 0)) {
        float3 dir = normalize(ndc.x * U + ndc.y * V + W);
        float3 color = gData.SceneEnvMap.eval(dir, 0);
        return float4(color,1.0f);
    }
    return bg;
}
