// Port of normal-pass.fs.glsl; RGB = view-space normal, A = filtered view Z

Texture2D<float> gDepthTex;
SamplerState gPointSampler;

cbuffer NormalData {
    float nearZ;
    float farZ;
    int screenWidth;
    int screenHeight;
};

cbuffer CameraData {
    float4x4 invProj;
};

float3 uvToEye(float2 texCoord, float depth) {
    float x = texCoord.x * 2.0 - 1.0;
    float y = texCoord.y * 2.0 - 1.0;
    float farV = farZ;
    float nearV = nearZ;
    float zn = ((farV + nearV) / (farV - nearV) * depth + 2.0 * farV * nearV / (farV - nearV)) / depth;
    float4 clipPos = float4(x, y, zn, 1.0f);
    float4 viewPos = mul(invProj, clipPos);
    return viewPos.xyz / viewPos.w;
}

float4 main(float2 texC : TEXCOORD) : SV_Target {
    float pixelWidth = 1.0f / (float)screenWidth;
    float pixelHeight = 1.0f / (float)screenHeight;
    float x = texC.x;
    float xp = texC.x + pixelWidth;
    float xn = texC.x - pixelWidth;
    float y = texC.y;
    float yp = texC.y + pixelHeight;
    float yn = texC.y - pixelHeight;

    float depth = gDepthTex.SampleLevel(gPointSampler, float2(x, y), 0);
    float depthxp = gDepthTex.SampleLevel(gPointSampler, float2(xp, y), 0);
    float depthxn = gDepthTex.SampleLevel(gPointSampler, float2(xn, y), 0);
    float depthyp = gDepthTex.SampleLevel(gPointSampler, float2(x, yp), 0);
    float depthyn = gDepthTex.SampleLevel(gPointSampler, float2(x, yn), 0);

    if (depth < -999.0f)
        return float4(0, 1, 0, depth);

    float3 position = uvToEye(float2(x, y), depth);
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

    float3 N = normalize(cross(dx, dy));
    // Avoid isnan/isinf on targets where Slang lowers poorly (see SVGFReproject.ps.slang note).
    bool badN = (N.x != N.x) || (N.y != N.y) || (N.z != N.z);
    badN = badN || (abs(N.x) > 1e8) || (abs(N.y) > 1e8) || (abs(N.z) > 1e8);
    if (badN)
        N = float3(0, 0, 1);

    return float4(N, depth);
}
