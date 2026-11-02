


cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
    float4x4 VPMat;
    float4x4 ViewMat;
    bool FocuseFoam;
}

cbuffer SSRParameter {
    float Step;
    float ThicknessT;
}
import Scene.Scene;
import Scene.Shading;
#include "Scene/VertexAttrib.slangh"
import Scene.ShadingData;
import Scene.Raster;

struct SSRParamerter {
    EnvMap SceneEnvMap;
}
ParameterBlock<SSRParamerter> gData;

Texture2D<float4> NormalTex;
Texture2D<float4> EnvTex;
Texture2D<float> ThicknessTex;
Texture2D<float4> BackColor;
Texture2D<float> BackDepth;
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

float3 SampleBackGround(float3 dirW, float3 posW)
{
    // 参数调整
    //const uint kMaxSteps = 100;     // 线性步进次数
    //const float kStepSize = 0.1f;   // 步长，根据场景尺度调整
    //const float kThickness = 0.5f; // 厚度容差

    // 获取相机世界坐标
    float3 cameraPosW = gScene.camera.getPosition();

    // 稍微偏移起点，防止自遮挡
    float3 currentPosW = posW + dirW * 0.01f;

    [loop]
    for (uint i = 0; i < 100; i++)
    {
        // 1. 步进
        currentPosW += dirW * Step;

        // 2. 投影到屏幕空间以获取 UV
        float4 clipPos = mul(VPMat,float4(currentPosW, 1.0f));

        
        if (clipPos.w <= 0) {
            continue;
        }
        

        float3 ndc = clipPos.xyz / clipPos.w;
        float2 uv = ndc.xy * float2(0.5f, -0.5f) + 0.5f;

        if (any(uv < 0) || any(uv > 1)) {
            break;
        }

        float sceneEuclideanDist = BackDepth.SampleLevel(Sampler,uv, 0);


        float rayEuclideanDist = distance(currentPosW, cameraPosW);

        if (rayEuclideanDist > sceneEuclideanDist)
        {
            if (rayEuclideanDist - sceneEuclideanDist < ThicknessT)
            {
                float3 hitColor = BackColor.SampleLevel(Sampler, uv, 0).rgb;

                float2 dUV = abs(uv - 0.5f) * 2.0f;
                float edgeFade = saturate(1.0f - max(dUV.x, dUV.y));

                return hitColor;
            }
        }
    }

    /*

    float4 screenPos = mul(VPMat, float4(posW, 1.0f));
    float2 screenUV = (screenPos.xy / screenPos.w) * float2(0.5f, -0.5f) + 0.5f;

    float3 viewDirW = mul(ViewMat, float4(dirW,0.0f)).xyz;

    // 偏移量受 ThicknessT 或自定义强度控制
    float2 refractOffset = viewDirW.xy * ThicknessT * 0.1f;
    float2 finalUV = screenUV + refractOffset;

    // 3. 边界检查
    finalUV = saturate(finalUV);

    // 4. 深度保护：确保折射采样的背景深度大于当前位置深度
    float bgDepth = BackDepth.SampleLevel(Sampler, finalUV, 0).r;
    float selfDepth = distance(posW, cameraPosW);

    if (bgDepth < selfDepth) {
        finalUV = screenUV; // 深度冲突时回退到原始 UV
    }

    return BackColor.SampleLevel(Sampler, finalUV, 0).rgb;
    */
    return gData.SceneEnvMap.eval(dirW);
}


float4 main(float2 TexC: TEXCOORD) : SV_Target {

    // return float4(BackDepth.Sample(Sampler, TexC),0.0f,0.0f,1.0f);
    //return float4(0.0f,0.0f,0.0f,1.0f);

    float2 ndc = float2(TexC.x,1.0-TexC.y) * 2 - 1.0;
    float3 dir = normalize(ndc.x * U + ndc.y * V + W);
    float4 normalD = NormalTex.Sample(Sampler, TexC);
    float3 normal = normalD.xyz;

    float4 backColor = BackColor.Sample(Sampler, TexC);
    float backd = BackDepth.Sample(Sampler, TexC);

    float d = normalD.w;

    if (dot(dir, normal) > 0) {
        normal = -1.0 * normal;
    }

    float IdotN = abs(dot(dir, normal));
    float thickness = ThicknessTex.Sample(Sampler, TexC);
    thickness = thickness * IdotN;

    thickness = min(maxThickness, thickness);
    thickness = max(minThickness, thickness);

    float lod = (thickness - minThickness)/(maxThickness-minThickness) * 13.0f;

    if (all(normal == 0)) {
        // float2 uv = directionToLatLong(dir);
        // float3 Color = EnvTex.Sample(Sampler, uv).xyz;
        float3 Color;
        if (all(backColor == 0)) {
            float3 Color = gData.SceneEnvMap.eval(dir);
            return float4(Color, 1.0f);
        }
        else
            return backColor;
    }
    else {
        if (d > backd) {
            return backColor;
        }
    }

    float fresnel = GetFresnel(IdotN, F0);

    float3 refrDir = refract(dir, normal, 1.0/IOR);
    float3 reflDir = reflect(dir, normal);
    // float2 uv = directionToLatLong(refrDir);
    float3 xyz = gScene.camera.getPosition() + d * dir;
    float3 refrColor = (1.0 - fresnel) *SampleBackGround(refrDir,xyz);
    //float3 refrColor = useBlur ? (1.0 - fresnel) * gData.SceneEnvMap.eval(refrDir, lod) : (1.0 - fresnel) * gData.SceneEnvMap.eval(refrDir);
    //float3 refrColor = useBlur ? (1.0 - fresnel) * EnvTex.SampleLevel(Sampler, uv, lod).xyz : (1.0 - fresnel) * EnvTex.Sample(Sampler, uv).xyz;

    refrColor = refrColor * exp(-Tr * TrStrenth*thickness);

    // uv = directionToLatLong(reflDir);
    // float3 reflColor = fresnel * gData.SceneEnvMap.eval(reflDir, 13.0f * Roughness);
    float3 reflColor = fresnel * SampleBackGround(reflDir, xyz);
    //float3 reflColor = fresnel*EnvTex.SampleLevel(Sampler, uv,13.0f*Roughness).xyz;
    float3 Color = reflColor + refrColor;
    return float4(Color, 1.0f);
}
