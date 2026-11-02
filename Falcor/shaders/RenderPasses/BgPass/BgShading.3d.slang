import Scene.Scene;
import Scene.Shading;
#include "Scene/VertexAttrib.slangh"
import Scene.ShadingData;
import Scene.Raster;
import Utils.Sampling.SampleGenerator;
import Rendering.Lights.LightHelpers;
import Utils.Math.MathHelpers;
import Utils.Sampling.UniformSampleGenerator;


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
cbuffer HardCode {
    int Dynamic;
    float4x4 WorldMat;
}

VSOut VSMain(VSIn vsIn)
{
    
    if (Dynamic>0) {
        VSOut out = defaultVS(vsIn);
        float4 posW = mul(WorldMat, float4(vsIn.pos, 1.0f));
        out.posW = posW.xyz;
        out.posH = mul(VPmat, posW);

        return out;
    }
    
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

    float3 albedo = props.diffuseReflectionAlbedo;//Using LightingMap

    float dis = length(gScene.camera.getPosition() - pIn.posW);

    // psout.color = float4(N, 1.0f);
    psout.color = float4(albedo, 1.0f);
    psout.depth = dis;

    return psout;
}
