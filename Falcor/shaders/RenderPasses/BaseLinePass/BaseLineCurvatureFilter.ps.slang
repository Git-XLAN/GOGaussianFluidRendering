// Port of filter-curvature-flow.fs.glsl

Texture2D<float> gDepthTex;
SamplerState gPointSampler;

cbuffer FilterData {
    float particleRadius;
    int screenWidth;
    int screenHeight;
};

cbuffer CameraData {
    float4x4 proj;
};

static const float thresholdRatio = 5.0;

float3 meanCurvature(float2 pos) {
    float2 dx = float2(1.0f / (float)screenWidth, 0.0f);
    float2 dy = float2(0.0f, 1.0f / (float)screenHeight);

    float zc = gDepthTex.SampleLevel(gPointSampler, pos, 0) - 1.0f;

    float zdxp = gDepthTex.SampleLevel(gPointSampler, pos + dx, 0) - 1.0f;
    float zdxn = gDepthTex.SampleLevel(gPointSampler, pos - dx, 0) - 1.0f;
    float zdx = 0.5f * (zdxp - zdxn);

    float zdyp = gDepthTex.SampleLevel(gPointSampler, pos + dy, 0) - 1.0f;
    float zdyn = gDepthTex.SampleLevel(gPointSampler, pos - dy, 0) - 1.0f;
    float zdy = 0.5f * (zdyp - zdyn);

    float zdx2 = zdxp + zdxn - 2.0f * zc;
    float zdy2 = zdyp + zdyn - 2.0f * zc;

    float zdxpyp = gDepthTex.SampleLevel(gPointSampler, pos + dx + dy, 0) - 1.0f;
    float zdxnyn = gDepthTex.SampleLevel(gPointSampler, pos - dx - dy, 0) - 1.0f;
    float zdxpyn = gDepthTex.SampleLevel(gPointSampler, pos + dx - dy, 0) - 1.0f;
    float zdxnyp = gDepthTex.SampleLevel(gPointSampler, pos - dx + dy, 0) - 1.0f;
    float zdxy = (zdxpyp + zdxnyn - zdxpyn - zdxnyp) / 4.0f;

    if (abs(zdx) > particleRadius * thresholdRatio) {
        zdx = 0.0f;
        zdx2 = 0.0f;
    }
    if (abs(zdy) > particleRadius * thresholdRatio) {
        zdy = 0.0f;
        zdy2 = 0.0f;
    }
    if (abs(zdxy) > particleRadius * thresholdRatio)
        zdxy = 0.0f;

    float cx = 2.0f / ((float)screenWidth * -proj[0][0]);
    float cy = 2.0f / ((float)screenHeight * -proj[1][1]);

    float d = cy * cy * zdx * zdx + cx * cx * zdy * zdy + cx * cx * cy * cy * zc * zc;
    float ddx = cy * cy * 2.0f * zdx * zdx2 + cx * cx * 2.0f * zdy * zdxy + cx * cx * cy * cy * 2.0f * zc * zdx;
    float ddy = cy * cy * 2.0f * zdx * zdxy + cx * cx * 2.0f * zdy * zdy2 + cx * cx * cy * cy * 2.0f * zc * zdy;

    float ex = 0.5f * zdx * ddx - zdx2 * d;
    float ey = 0.5f * zdy * ddy - zdy2 * d;
    float h = 0.5f * ((cy * ex + cx * ey) / pow(d, 1.5f));

    return float3(zdx, zdy, h);
}

float main(float2 texC : TEXCOORD) : SV_Target {
    float particleDepth = gDepthTex.SampleLevel(gPointSampler, texC, 0);
    if (particleDepth < -1000.0f || particleDepth > 0) {
        return particleDepth;
    }
    const float dt = 0.0003f;
    const float dzt = 1000.0f;
    float3 dxyz = meanCurvature(texC);
    return particleDepth + dxyz.z * dt * (1.0f + (abs(dxyz.x) + abs(dxyz.y)) * dzt);
}
