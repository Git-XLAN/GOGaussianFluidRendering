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
}

struct PSOut {
    float4 color : SV_Target0;
    float depth : SV_Target1;
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

PSOut PSMain(VSOut pIn)
{
    float3 N = normalize(pIn.normalW);

    float dist = distance(pIn.posW, pos);

    PSOut out;
    out.color = float4(N,1.0f);
    out.depth = dist;

    return out;
}
