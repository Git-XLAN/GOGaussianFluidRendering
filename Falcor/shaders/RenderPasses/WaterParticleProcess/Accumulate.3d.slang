struct VSIn
{
    float4 pos : POSITIONUV;
};

struct VSOut
{
    float4 posR : SV_POSITION;
    float2 uv : POSUV;
};
cbuffer Uniform {
    float Radius;
    float sigma;
}

VSOut VSMain(VSIn vIn)
{
    VSOut vOut;
    vOut.posR = float4(vIn.pos.xy, 1.0f, 1.f);
    vOut.uv = float2(vIn.pos.zw);
    return vOut;
}

float PSMain(VSOut vsOut) : SV_TARGET
{
    float2 centeredUV = vsOut.uv * 2 - 1;
    float r = length(centeredUV);
    float g = exp(-r * r / (2 * sigma * sigma));
    return 2.0*g*Radius;
}
