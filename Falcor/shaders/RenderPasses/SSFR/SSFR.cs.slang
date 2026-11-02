cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
    float FocalLenX;
    float FocalLenY;
    float3 CamPos;
}

cbuffer Var {
    float DepthThreshold;
    float Step;
    int Radius;
    int2 Direction;
    float GaussianSigmaSpatial;
    float GaussianSigmaDepth;
}

RWTexture2D<float> ViewDepth;
RWTexture2D<float> WorldDepth;
RWTexture2D<float> OutDepth;

[numthreads(32, 32, 1)]
void toViewSpace(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                 uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint2 coord = dispatchThreadID.xy;
    float2 ndc = ((coord + 0.5f) / float2(Width, Height)) * 2.0f - 1.0f;
    ndc.y *= -1;

    float3 dir = normalize(U * ndc.x + V * ndc.y + W);

    float cosTheta = dot(dir, W)/length(W);

    ViewDepth[coord] = WorldDepth[coord]* cosTheta;
}

float getDepth(int2 coord, uint2 dim)
{
    coord = clamp(coord, int2(0), int2(dim) - 1);
    return ViewDepth[coord];
}

[numthreads(32, 32, 1)]
void Filter(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint2 coord = dispatchThreadID.xy;
    uint2 dim = uint2(Width, Height);

    float z = getDepth(coord, dim);

    if(z < (1e-5)) {
        OutDepth[coord] = z;
        return;
    }

    float z_u = getDepth(coord + int2(0, 1), dim);
    float z_d = getDepth(coord + int2(0, -1), dim);
    float z_r = getDepth(coord + int2(1, 0), dim);
    float z_l = getDepth(coord + int2(-1, 0), dim);

    
    if (abs(z_l - z) >DepthThreshold) z_l = z;
    if (abs(z_r - z) >DepthThreshold) z_r = z;
    if (abs(z_d - z) >DepthThreshold) z_d = z;
    if (abs(z_u - z) >DepthThreshold) z_u = z;
    

    float cx = 2.0 / (Width * FocalLenX);
    float cy = 2.0 / (Height * FocalLenY);

    float dx = (z_r - z_l) * 0.5f;
    float dy = (z_d - z_u) * 0.5f;

    float dxx = (z_r - 2.0f * z + z_l);
    float dyy = (z_d - 2.0f * z + z_u);

    float Cy = (1.0f + dy * dy);
    float Cx = (1.0f + dx * dx);
    float num = Cy * dxx + Cx * dyy; // 这里忽略了交叉项 dxy，通常没问题
    float den = 2.0f * pow(max(1e-5f, 1.0f + dx * dx + dy * dy), 1.5f);

    float H = num / den;

    float z_new = z + H * Step;
    OutDepth[coord] = z_new;
}



float3 getWorldPos(int2 coord) {
    float d = getDepth(coord, uint2(Width, Height));

    float2 ndc = ((coord + 0.5f) / float2(Width, Height)) * 2.0f - 1.0f;
    ndc.y *= -1;

    float3 dir = normalize(U * ndc.x + V * ndc.y + W);
    float cosTheta = dot(dir, W) / length(W);
    float worldD = d / cosTheta;

    return CamPos + worldD * dir;
}

RWTexture2D<float4> OutNormal;

[numthreads(32, 32, 1)]
void ReBuildNormal(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                   uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    int2 coord = dispatchThreadID.xy;

    float d = getDepth(coord, uint2(Width, Height));
    float2 ndc = ((coord + 0.5f) / float2(Width, Height)) * 2.0f - 1.0f;
    ndc.y *= -1;

    float3 dir = normalize(U * ndc.x + V * ndc.y + W);

    if (d < 1e-5) {
        OutNormal[coord] = float4(0.0f, 0.0f, 0.0f, 0.0f);
        return;
    }
    float3 P_c = getWorldPos(coord);
    float3 P_l = getWorldPos(coord+int2(-1, 0));
    float3 P_r = getWorldPos(coord+int2(1, 0));
    float3 P_u = getWorldPos(coord+int2(0, -1));
    float3 P_d = getWorldPos(coord+int2(0, 1));


    if (length(P_l - P_c) > DepthThreshold) P_l = P_c;
    if (length(P_r - P_c) > DepthThreshold) P_r = P_c;
    if (length(P_u - P_c) > DepthThreshold) P_u = P_c;
    if (length(P_d - P_c) > DepthThreshold) P_d = P_c;
    

    float3 ddx = P_r - P_l;
    float3 ddy = P_d - P_u;

    if(all(ddx==0)||all(ddy==0)){
        OutNormal[coord] = float4(0.0f, 0.0f, 0.0f, 0.0f);
        return;
    }


    float3 N = cross(ddx, ddy);
    if(dot(N,dir)>0){
        N = -1.0f * N;
    }
    N = normalize(N);

    OutNormal[coord] = float4(N, d);
} 
float gaussian(float x, float sigma)
{
    return exp(-(x * x) / (2.0f * sigma * sigma));
}
float gaussian2D(float2 x, float sigma)
{
    return exp(-(dot(x,x)) / (2.0f * sigma * sigma));
}

    [numthreads(32, 32, 1)]
void BilateralFilter(uint3 dispatchThreadID: SV_DispatchThreadID,
                    uint3 groupThreadID: SV_GroupThreadID,
                   uint3 groupID: SV_GroupID,
                    uint groupIndex: SV_GroupIndex) {
    int2 coord = dispatchThreadID.xy;

    float depth = getDepth(coord, uint2(Width, Height));

    if (depth < 1e-5) {
        OutDepth[coord] = 0.0f;
        return;
    }

    float sumWeight = 0.0f;
    float sumDepth = 0.0f;

    
    float ratio = (float)Height / 2.0 / tan(radians(45.0) / 2.0);
    float K = float(Radius) * ratio * 0.025 * 0.1f;
    int filterSize = min(8,(int)ceil(K / depth));

    float sigma = filterSize / 3.0f;

    float thresholdRatio = 10.0f;
    float threshold = 0.025 * thresholdRatio;
    float sigmaDepth = threshold / 3.0f;

    for (int i = -filterSize; i <= filterSize; i++) {
        for (int j = -filterSize; j <= filterSize; j++) {
            float curD = getDepth(coord + int2(i, j), uint2(Width, Height));
            float deltaD = abs(curD - depth);
            if (deltaD > DepthThreshold) continue;

            float spatialWeight = gaussian2D(float2(i,j), sigma);
            float depthWeight = gaussian(deltaD, sigmaDepth);

            float weight = spatialWeight * depthWeight;

            sumDepth += weight * curD;
            sumWeight += weight;
        }
    }

    OutDepth[coord] = sumDepth / (sumWeight + 1e-5);
}
