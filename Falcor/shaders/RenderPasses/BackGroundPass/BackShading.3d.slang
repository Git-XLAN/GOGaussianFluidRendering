import Scene.Scene;
import Scene.Shading;
#include "Scene/VertexAttrib.slangh"
import Scene.ShadingData;
import Scene.Raster;
import Utils.Sampling.SampleGenerator;
import Rendering.Lights.LightHelpers;
import Utils.Math.MathHelpers;
import Utils.Sampling.UniformSampleGenerator;


struct BParamerter {
    EnvMap SceneEnvMap;
    int mipCount;
}
ParameterBlock<BParamerter> gData;

/*
struct MyMaterail {
    Texture2D baseColorTex;
    Texture1D normalTex;
    Texture2D roughnessTex;
    Sampler2D sampler;
}

struct MyParameter {
    MyMaterail mat;
}
ParameterBlock<MyParameter> gData;

*/
cbuffer CameraData {
    float3 cameraPos;
    float4x4 VPmat;
}

VSOut VSMain(VSIn vsIn)
{
    return defaultVS(vsIn);
}

struct PSOut {
    float4 color : SV_Target0;
    float depth : SV_Target1;
}

PSOut PSMain(VSOut pIn, uint triangleIndex: SV_PrimitiveID)
{
    PSOut psout;
    float3 viewDir = normalize(gScene.camera.getPosition() - pIn.posW);
    float2 uv = pIn.texC;

    float3 faceNormal = gScene.getFaceNormalW(pIn.instanceID, triangleIndex);
    VertexData v = prepareVertexData(pIn, faceNormal);

    ShadingData sd = gScene.materials.prepareShadingData(v, pIn.materialID, viewDir);
    let lod = ImplicitLodTextureSampler();

    let mi = gScene.materials.getMaterialInstance(sd, lod);
    let props = mi.getProperties(sd);

    float3 albedo = props.diffuseReflectionAlbedo;
    float3 worldNormal = props.guideNormal;

    if (dot(worldNormal, viewDir) < 0) {
        worldNormal = -1.0 * worldNormal;
    }
    float roughness = props.roughness;

    UniformSampleGenerator sg = UniformSampleGenerator(pIn.posH.xy, 0);
    float3 directLighting = 0;

    // 假设场景里有灯光
    for (uint i = 0; i < gScene.getLightCount(); i++) {
        LightData lightData = gScene.getLight(i);
        float3 lightVec = lightData.posW - sd.posW;
        float distSq = max(dot(lightVec, lightVec), 0.0001);
        float dist = sqrt(distSq);

        float3 L = lightVec / dist;

        float3 Li = lightData.intensity / distSq;

        directLighting += mi.eval(sd, L, sg) * Li;
    }


    float3 R = reflect(-viewDir, worldNormal);

    float LOD = roughness * gData.mipCount;
    float3 envColor = gData.SceneEnvMap.eval(R, LOD).rgb;

    float3 ambient = 10*envColor * albedo;

    float dis = length(gScene.camera.getPosition() - pIn.posW);

    // psout.color = float4(N, 1.0f);
    psout.color = float4(directLighting+ambient, 1.0f);
    psout.depth = dis;

    return psout;
}
