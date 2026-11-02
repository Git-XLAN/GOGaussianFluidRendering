

Texture2D<float> ThicknessInput;
cbuffer GlobalVar {
    int FilterSize;
}
SamplerState Sampler;

float main(float2 TexC: TEXCOORD) : SV_Target {
    float2 blurRadius = float2(1.0f / float(Width), 1.0f / float(Height));
    float sum = 0;
    float wsum = 0;
    float sigma = float(FilterSize) / 3.0f;
    float sigma2 = 2.0 * sigma * sigma;

    for (int x = -FilterSize; x <= FilterSize; x++) {
        for (int y = -FilterSize; y <= FilterSize; y++) {
            float2 sampleCoord = float2(x, y) * blurRadius + TexC;
            float sampleThickness = ThicknessInput.Sample(Sampler, sampleCoord);
            float r = length(float2(x, y));
            float w = exp(-r * r / sigma2);

            sum += w*sampleThickness;
            wsum += w;
        }
    }
    return sum / wsum;
}
