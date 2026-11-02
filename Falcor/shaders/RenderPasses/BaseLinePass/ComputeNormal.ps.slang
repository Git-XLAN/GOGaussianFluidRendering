Texture2D<float4> Depth;
SamplerState Sampler;

const static float far = 1000.0f;
const static float near = 0.1f;

cbuffer CameraData {
    float4x4 invProjectMatrix;
    float4x4 inViewMatrix;
    float4x4 projectMatrix;
}

float3 uvToEye(float2 texCoord, float depth) {
    float x = texCoord.x * 2.0f - 1.0f;
    float y = texCoord.y * 2.0f - 1.0f;
    float zn = ((far + near) / (far - near) * depth + 2 * far * near / (far - near)) / depth;

    float4 clipPos = float4(x, -y, zn, 1.0f);
    float4 viewPos = mul(invProjectMatrix, clipPos);

    return viewPos.xyz / viewPos.w;
}

float4 main(float2 TexC: TEXCOORD) : SV_Target {
    float4 depthOri = Depth.Sample(Sampler, TexC);

    if (all(depthOri == 0)) return float4(0.0f);

    float depth = depthOri.x;

    float pixelWidth = 1.0f / Width;
    float pixelHeight = 1.0f / Height;
    float x = TexC.x;
    float xp = TexC.x + pixelWidth;
    float xn = TexC.x - pixelWidth;

    float y = TexC.y;
    float yp = TexC.y + pixelHeight;
    float yn = TexC.y - pixelHeight;

    float depthxp = Depth.Sample(Sampler, float2(xp, y)).x;
    float depthxn = Depth.Sample(Sampler, float2(xn, y)).x;
    float depthyp = Depth.Sample(Sampler, float2(x, yp)).x;
    float depthyn = Depth.Sample(Sampler, float2(x, yn)).x;

    if (depthxp == 0) depthxp = 1000;
    if (depthxn == 0) depthxn = 1000;
    if (depthyp == 0) depthyp = 1000;
    if (depthyn == 0) depthyn = 1000;

    float3 position = uvToEye(TexC, depth);
    float3 positionxp = uvToEye(float2(xp, y), depthxp);
    float3 positionxn = uvToEye(float2(xn, y), depthxn);
    float3 dxl = position - positionxn;
    float3 dxr = positionxp - position;

    float3 dx = (abs(dxr.z) < abs(dxl.z)) ? dxr : dxl;

    float3 positionyp = uvToEye(float2(x, yp), depthyp);
    float3 positionyn = uvToEye(float2(x, yn), depthyn);
    float3 dyb = position - positionyn;
    float3 dyt = positionyp - position;

    float3 dy = (abs(dyt.z) < abs(dyb.z)) ? dyt : dyb;

    float3 N = normalize(cross(dy, dx));

    if (isnan(N.x) || isnan(N.y) || isnan(N.y) ||
       isinf(N.x) || isinf(N.y) || isinf(N.z)) {
        N = float3(0.0f, 0.0f, 1.0f);
       }

       float3 WorldN = mul(inViewMatrix, float4(N, 0.0f)).xyz;
       return float4(WorldN, length(depthOri.xyz));


}
