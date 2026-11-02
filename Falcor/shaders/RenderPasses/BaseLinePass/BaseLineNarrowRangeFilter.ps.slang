// Port of filter-narrow-range.fs.glsl (FIX_OTHER_WEIGHT + RANGE_EXTENSION)

Texture2D<float> gDepthTex;
SamplerState gPointSampler;

#define PI_OVER_8 0.392699082f

static const int fixedFilterRadius = 4;
static const float thresholdRatio = 10.5f;
static const float clampRatio = 1.0f;

cbuffer FilterData {
    float particleRadius;
    int filterDim;
    int maxFilterSize;
    int screenWidth;
    int screenHeight;
    int separable1D;     // 1 = separable 1D, 0 = adaptive 2D, -1 = fixed-radius 2D
    int filterDirection; // 0 = horizontal, 1 = vertical (1D only)
};

float compute_weight1D(float r, float two_sigma2) {
    return exp(-r * r / two_sigma2);
}

float compute_weight2D(float2 r, float two_sigma2) {
    return exp(-dot(r, r) / two_sigma2);
}

void ModifiedGaussianFilter1D(inout float sampleDepth, inout float weight, inout float weight_other, inout float upper, inout float lower, float lower_clamp, float threshold) {
    if (sampleDepth > upper) {
        weight = 0;
        weight_other = 0;
    } else {
        if (sampleDepth < lower) {
            sampleDepth = lower_clamp;
        } else {
            upper = max(upper, sampleDepth + threshold);
            lower = min(lower, sampleDepth - threshold);
        }
    }
}

void ModifiedGaussianFilter2D(inout float sampleDepth, inout float weight, inout float weight_other, inout float upper, inout float lower, float lower_clamp, float threshold) {
    if (sampleDepth > upper) {
        weight = 0;
        weight_other = 0;
    } else {
        if (sampleDepth < lower) {
            sampleDepth = lower_clamp;
        } else {
            upper = max(upper, sampleDepth + threshold);
            lower = min(lower, sampleDepth - threshold);
        }
    }
}

float filter1D(float2 f_TexCoord, float pixelDepth) {
    if (filterDim == 0)
        return pixelDepth;

    float2 blurRadius = float2(1.0f / (float)screenWidth, 1.0f / (float)screenHeight);
    float threshold = particleRadius * thresholdRatio;
    float ratio = (float)screenHeight / 2.0f / tan(PI_OVER_8);
    float K = -(float)filterDim * ratio * particleRadius * 0.1f;
    int filterSize = min(maxFilterSize, (int)ceil(K / pixelDepth));

    float upper = pixelDepth + threshold;
    float lower = pixelDepth - threshold;
    float lower_clamp = pixelDepth - particleRadius * clampRatio;

    float sigma = (float)filterSize / 3.0f;
    float two_sigma2 = 2.0f * sigma * sigma;

    float2 sum2 = float2(pixelDepth, 0);
    float2 wsum2 = float2(1, 0);
    float4 dtc = (filterDirection == 0) ? float4(blurRadius.x, 0, -blurRadius.x, 0) : float4(0, blurRadius.y, 0, -blurRadius.y);

    float4 f_tex = f_TexCoord.xyxy;
    float r = 0;
    float dr = dtc.x + dtc.y;

    float upper1 = upper;
    float upper2 = upper;
    float lower1 = lower;
    float lower2 = lower;

    for (int x = 1; x <= filterSize; ++x) {
        f_tex += dtc;
        r += dr;

        float sampleDepthA = gDepthTex.SampleLevel(gPointSampler, f_tex.xy, 0);
        float sampleDepthB = gDepthTex.SampleLevel(gPointSampler, f_tex.zw, 0);
        float2 w2 = float2(compute_weight1D(r, two_sigma2));

        ModifiedGaussianFilter1D(sampleDepthA, w2.x, w2.y, upper1, lower1, lower_clamp, threshold);
        ModifiedGaussianFilter1D(sampleDepthB, w2.y, w2.x, upper2, lower2, lower_clamp, threshold);

        sum2 += float2(sampleDepthA, sampleDepthB) * w2;
        wsum2 += w2;
    }

    float2 filterVal = float2(sum2.x, wsum2.x) + float2(sum2.y, wsum2.y);
    return filterVal.x / filterVal.y;
}

float filter2D(float2 f_TexCoord, float pixelDepth) {
    if (filterDim == 0)
        return pixelDepth;

    float2 blurRadius = float2(1.0f / (float)screenWidth, 1.0f / (float)screenHeight);
    float threshold = particleRadius * thresholdRatio;
    float ratio = (float)screenHeight / 2.0f / tan(PI_OVER_8);
    float K = -(float)filterDim * ratio * particleRadius * 0.1f;
    int filterSize = (separable1D < 0) ? fixedFilterRadius : min(maxFilterSize, (int)ceil(K / pixelDepth));

    float upper = pixelDepth + threshold;
    float lower = pixelDepth - threshold;
    float lower_clamp = pixelDepth - particleRadius * clampRatio;

    float sigma = (float)filterSize / 3.0f;
    float two_sigma2 = 2.0f * sigma * sigma;

    float4 f_tex = f_TexCoord.xyxy;
    float4 sum4 = float4(pixelDepth, 0, 0, 0);
    float4 wsum4 = float4(1, 0, 0, 0);

    for (int x = 1; x <= filterSize; ++x) {
        float rx = (float)x * blurRadius.x;
        f_tex.x += blurRadius.x;
        f_tex.z -= blurRadius.x;
        float4 f_tex1 = f_tex.xyxy;
        float4 f_tex2 = f_tex.zwzw;

        for (int y = 1; y <= filterSize; ++y) {
            float ry = (float)y * blurRadius.y;
            float2 r_ij = float2(rx, ry);
            f_tex1.y += blurRadius.y;
            f_tex1.w -= blurRadius.y;
            f_tex2.y += blurRadius.y;
            f_tex2.w -= blurRadius.y;

            float sd0 = gDepthTex.SampleLevel(gPointSampler, f_tex1.xy, 0);
            float sd1 = gDepthTex.SampleLevel(gPointSampler, f_tex1.zw, 0);
            float sd2 = gDepthTex.SampleLevel(gPointSampler, f_tex2.xy, 0);
            float sd3 = gDepthTex.SampleLevel(gPointSampler, f_tex2.zw, 0);

            float wv = compute_weight2D(blurRadius * r_ij, two_sigma2);
            float4 w4 = float4(wv, wv, wv, wv);

            ModifiedGaussianFilter2D(sd0, w4.x, w4.w, upper, lower, lower_clamp, threshold);
            ModifiedGaussianFilter2D(sd1, w4.y, w4.z, upper, lower, lower_clamp, threshold);
            ModifiedGaussianFilter2D(sd2, w4.z, w4.y, upper, lower, lower_clamp, threshold);
            ModifiedGaussianFilter2D(sd3, w4.w, w4.x, upper, lower, lower_clamp, threshold);

            sum4 += float4(sd0, sd1, sd2, sd3) * w4;
            wsum4 += w4;
        }
    }

    float filtX = dot(sum4, float4(1, 1, 1, 1));
    float filtY = dot(wsum4, float4(1, 1, 1, 1));
    return filtX / filtY;
}

float main(float2 texC : TEXCOORD) : SV_Target {
    float pixelDepth = gDepthTex.SampleLevel(gPointSampler, texC, 0);
    if (pixelDepth > 0.0 || pixelDepth < -1000.0f)
        return pixelDepth;
    if (separable1D == 1)
        return filter1D(texC, pixelDepth);
    return filter2D(texC, pixelDepth);
}
