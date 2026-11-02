Texture2D<float4> OriginDepth;
SamplerState Sampler;

#define PI_OVER_8 0.392699082f

cbuffer GlobalVar {
    uint selectFilter;
    int filterSize;
    uint filterCount;
    float particleRadius;
    int filterDirection;
    int filterDim;
}

cbuffer CameraData {
    float4x4 projMat;
}

static const int fixedFilterRadius = 4;
static const float thresholdRatio = 10.5;
static const float clampRatio = 1;

float compute_weight1D(float r, float two_sigma2)
{
    return exp(-r * r / two_sigma2);
}
float compute_weight2D(float2 r, float two_sigma2)
{
    return exp(-dot(r, r) / two_sigma2);
}


void ModifiedGaussianFilter1D(inout float sampleDepth, inout float weight, inout float weight_other, inout float upper, inout float lower, float lower_clamp, float threshold)
{
    if (sampleDepth > upper||sampleDepth ==0) {
        weight = 0;
        weight_other = 0;
    } else {
        if (sampleDepth < lower) {
            sampleDepth = lower_clamp;
        }
        else {
            upper = max(upper, sampleDepth + threshold);
            lower = min(lower, sampleDepth - threshold);
        }
    }
}

void ModifiedGaussianFilter2D(inout float sampleDepth, inout float weight, inout float weight_other, inout float upper, inout float lower, float lower_clamp, float threshold)
{
    if (sampleDepth > upper || sampleDepth == 0) {
        weight = 0;
        weight_other = 0;
    } else {
        if (sampleDepth < lower) {
            sampleDepth = lower_clamp;
        }
        else {
            upper = max(upper, sampleDepth + threshold);
            lower = min(lower, sampleDepth - threshold);
        }
    }
}




float filter1D(float depth,float2 TexC) {
    float2 blurRadius = float2(1.0f / Width, 1.0f / Height);
    float threshold = particleRadius * thresholdRatio;
    float ratio = Height / 2.0f / tan(PI_OVER_8);
    float K = filterSize * ratio * particleRadius * 0.1f;

    int filterSizeInt = min(100, int(ceil(K / depth)));

    float upper = depth + threshold;
    float lower = depth - threshold;
    float lower_clamp = depth - particleRadius * clampRatio;

    float sigma = filterSizeInt / 3.0f;
    float two_sigma2 = 2.0f * sigma * sigma;

    float2 sum2 = float2(depth, 0);
    float2 wsum2 = float2(1, 0);

    float4 dtc = (filterDirection == 0) ? float4(blurRadius.x, 0, -blurRadius.x, 0) : float4(0, blurRadius.y, 0, -blurRadius.y);
    float4 f_tex = float4(TexC, TexC);
    float r = 0;
    float dr = dtc.x + dtc.y;

    float upper1 = upper;
    float upper2 = upper;
    float lower1 = lower;
    float lower2 = lower;

    float2 sampleDepth;
    float2 w2;

    for (int x = 1; x <= filterSizeInt; x++) {
        f_tex += dtc;
        r += dr;

        sampleDepth.x = OriginDepth.Sample(Sampler, f_tex.xy).x;
        sampleDepth.y = OriginDepth.Sample(Sampler, f_tex.zw).x;

        w2 = float2(compute_weight1D(r, two_sigma2));
        ModifiedGaussianFilter1D(sampleDepth.x, w2.x, w2.y, upper1, lower1, lower_clamp, threshold);
        ModifiedGaussianFilter1D(sampleDepth.y, w2.y, w2.x, upper2, lower2, lower_clamp, threshold);

        sum2 += sampleDepth * w2;
        wsum2 += w2;
    }

    float2 filterVal = float2(sum2.x, wsum2.x) + float2(sum2.y, wsum2.y);

    return filterVal.x / filterVal.y;
}

float filter2D(float depth,float2 TexC) {

    float2 blurRadius = float2(1.0f / Width, 1.0f / Height);
    float threshold = particleRadius * thresholdRatio;
    float ratio = Height / 2.0f / tan(PI_OVER_8);
    float K = filterSize * ratio * particleRadius * 0.1f;

    int filterSizeInt = fixedFilterRadius;

    float upper = depth + threshold;
    float lower = depth - threshold;
    float lower_clamp = depth - particleRadius * clampRatio;

    float sigma = filterSizeInt / 3.0f;
    float two_sigma2 = 2.0f * sigma * sigma;

    float4 f_tex = float4(TexC, TexC);

    float2 r = float2(0.0f);
    float4 sum4 = float4(depth, 0, 0, 0);
    float4 wsum4 = float4(1, 0, 0, 0);
    float4 sampleDepth;
    float4 w4;

    for (int x = 1; x <= filterSizeInt; ++x) {
        r.x += blurRadius.x;
        f_tex.x += blurRadius.x;
        f_tex.z -= blurRadius.x;
        float4 f_tex1 = f_tex.xyxy;
        float4 f_tex2 = f_tex.zwzw;

        for (int y = 1; y <= filterSizeInt; ++y) {
            f_tex1.y += blurRadius.y;
            f_tex1.w -= blurRadius.y;
            f_tex2.y += blurRadius.y;
            f_tex2.w -= blurRadius.y;

            sampleDepth.x = OriginDepth.Sample(Sampler, f_tex1.xy).x;
            sampleDepth.y = OriginDepth.Sample(Sampler, f_tex1.zw).x;
            sampleDepth.z = OriginDepth.Sample(Sampler, f_tex2.xy).x;
            sampleDepth.w = OriginDepth.Sample(Sampler, f_tex2.zw).x;

            r.y += blurRadius.y;
            w4 = float4(compute_weight2D(blurRadius * r, two_sigma2));

            ModifiedGaussianFilter2D(sampleDepth.x, w4.x, w4.w, upper, lower, lower_clamp, threshold);
            ModifiedGaussianFilter2D(sampleDepth.y, w4.y, w4.z, upper, lower, lower_clamp, threshold);
            ModifiedGaussianFilter2D(sampleDepth.z, w4.z, w4.y, upper, lower, lower_clamp, threshold);
            ModifiedGaussianFilter2D(sampleDepth.w, w4.w, w4.x, upper, lower, lower_clamp, threshold);

            sum4 += sampleDepth * w4;
            wsum4 += w4;
        }
    }

    float2 filterVal;
    filterVal.x = dot(sum4, float4(1, 1, 1, 1));
    filterVal.y = dot(wsum4, float4(1, 1, 1, 1));
    return filterVal.x / filterVal.y;

}

static const float kMeanCurvatureEpsilon = 1e-20f;

// 0 = infinity / background (no valid surface). Valid fluid uses view-z > 0.
bool IsInvalidDepth(float d)
{
    return d <= 0.0f;
}

float3 meanCurvature(float2 pos)
{
    float w = (float)Width;
    float h = (float)Height;
    float2 dx = float2(1.0f / w, 0.0f);
    float2 dy = float2(0.0f, 1.0f / h);

    // Stencil: center + axis + corners. Skip if any tap is infinity (0) so we do not
    // difference across fluid / background (matches idea of filter-curvature-flow early-out).
    float d0 = OriginDepth.Sample(Sampler, pos).x;
    float dpx = OriginDepth.Sample(Sampler, pos + dx).x;
    float dnx = OriginDepth.Sample(Sampler, pos - dx).x;
    float dpy = OriginDepth.Sample(Sampler, pos + dy).x;
    float dny = OriginDepth.Sample(Sampler, pos - dy).x;
    float dpp = OriginDepth.Sample(Sampler, pos + dx + dy).x;
    float dnn = OriginDepth.Sample(Sampler, pos - dx - dy).x;
    float dpn = OriginDepth.Sample(Sampler, pos + dx - dy).x;
    float dnp = OriginDepth.Sample(Sampler, pos - dx + dy).x;

    if (IsInvalidDepth(d0) || IsInvalidDepth(dpx) || IsInvalidDepth(dnx) || IsInvalidDepth(dpy) || IsInvalidDepth(dny) ||
        IsInvalidDepth(dpp) || IsInvalidDepth(dnn) || IsInvalidDepth(dpn) || IsInvalidDepth(dnp))
        return float3(0.0f, 0.0f, 0.0f);

    // Positive view-z -> negate to match original shader's z convention
    float zc = -d0 - 1.0f;
    float zdxp = -dpx - 1.0f;
    float zdxn = -dnx - 1.0f;

    float zdx = 0.5f * (zdxp - zdxn);

    float zdyp = -dpy - 1.0f;
    float zdyn = -dny - 1.0f;

    float zdy = 0.5f * (zdyp - zdyn);

    float zdx2 = zdxp + zdxn - 2.0f * zc;
    float zdy2 = zdyp + zdyn - 2.0f * zc;

    float zdxpyp = -dpp - 1.0f;
    float zdxnyn = -dnn - 1.0f;
    float zdxpyn = -dpn - 1.0f;
    float zdxnyp = -dnp - 1.0f;

    float zdxy = (zdxpyp + zdxnyn - zdxpyn - zdxnyp) / 4.0f;

    if (abs(zdx) > particleRadius * thresholdRatio) {
        zdx = 0.0f;
        zdx2 = 0.0f;
    }
    if (abs(zdy) > particleRadius * thresholdRatio) {
        zdy = 0.0f;
        zdy2 = 0.0f;
    }
    if (abs(zdxy) > particleRadius * thresholdRatio) {
        zdxy = 0.0f;
    }

    // GLSL: 2 / (W * -P[0][0])
    float cx = 2.0f / (w * -projMat[0][0]);
    float cy = 2.0f / (h * -projMat[1][1]);

    float d = cy * cy * zdx * zdx + cx * cx * zdy * zdy + cx * cx * cy * cy * zc * zc;

    float ddx = cy * cy * 2.0f * zdx * zdx2 + cx * cx * 2.0f * zdy * zdxy + cx * cx * cy * cy * 2.0f * zc * zdx;
    float ddy = cy * cy * 2.0f * zdx * zdxy + cx * cx * 2.0f * zdy * zdy2 + cx * cx * cy * cy * 2.0f * zc * zdy;

    float ex = 0.5f * zdx * ddx - zdx2 * d;
    float ey = 0.5f * zdy * ddy - zdy2 * d;

    d = max(d, kMeanCurvatureEpsilon);
    float hc = 0.5f * ((cy * ex + cx * ey) / pow(d, 1.5f));

    return float3(zdx, zdy, hc);
}

float4 main(float2 TexC: TEXCOORD) : SV_Target {

    if (filterSize == 0) return OriginDepth.Sample(Sampler, TexC);

    float depth = OriginDepth.Sample(Sampler, TexC).x;
    float y = OriginDepth.Sample(Sampler, TexC).y;
    float z = OriginDepth.Sample(Sampler, TexC).z;
    if (depth == 0) return float4(0.0f);

    if(selectFilter==0){
        // Curvature
        const float dt = 0.0003f;
        const float dzt = 1000.0f;
        float3 dxyz = meanCurvature(TexC);

        return float4(depth - dxyz.z * dt * (1.0f + (abs(dxyz.x) + abs(dxyz.y)) * dzt), y, z, 1);
    }
    else {
        return (filterDim == 1) ? float4(filter1D(depth, TexC), y, z, 1.0f) : float4(filter2D(depth, TexC), y, z, 1.0f);
    }
}
