struct VSIn
{
    float3 pos    : POSITION; 
    float3 normal : NORMAL;   
};

struct VSOut
{
    float4 posH     : SV_Position; 
    float3 normalW  : NORMAL;     
    float3 posW     : TEXCOORD0;   
};

cbuffer CameraData {

    float3 pos;
    float4x4 VPmat;
    float4x4 Viewmat;
}

cbuffer GlobalVar {
    float ParticleRadius;
    uint ParticleNum;
}

VSOut VSMain(VSIn vIn)
{
    VSOut vOut;

    float4 posWorld = float4(vIn.pos, 1.0);
    vOut.posW = posWorld.xyz;
    vOut.posH = mul(VPmat, posWorld);

    vOut.normalW = vIn.normal;

    return vOut;
}

float4 PSMain(VSOut pIn) : SV_Target
{
    float3 N = normalize(pIn.normalW);

    //float4 N_View = mul(Viewmat, float4(N, 0.0f));

    float dist = distance(pIn.posW, pos);

    return float4(N, dist);
}
