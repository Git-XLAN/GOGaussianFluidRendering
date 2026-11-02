
RWStructuredBuffer<uint> surfaceIdx;
Texture2D<float4> DepthMap;
StructuredBuffer<float3> allParticles;
SamplerState sampler;
RWByteAddressBuffer CountBuffer;
import Utils.Sampling.SampleGenerator;
import Utils.Sampling.UniformSampleGenerator;
RWStructuredBuffer<uint> IsChosed;


cbuffer GlobalVar {
    uint particleNum;
    float depthBias;
    float radius;
    uint surfaceNum;

    uint minPixel;
    uint maxPixel;
    float minP;
}

cbuffer CameraData {
    float4x4 VPmat;
    float3 camPos;
    float FrameHeight;
    float FocalLenth;
    float3 Front;
}

bool check(float2 ndc) {
    if (ndc.x > 1.0f || ndc.x < -1.0f) return true;
    if (ndc.y > 1.0f || ndc.y < -1.0f) return true;
    return false;
}

[numthreads(32, 32, 1)]
void Filter(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {

    uint id = groupID.x * 32 * 32 + groupIndex;

    if (id >= particleNum) return;

    float3 pos = allParticles[id];

    float4 clipPos = mul(VPmat, float4(pos, 1.0f));
    if (clipPos.w < 0) return;
    float3 ndc = clipPos.xyz / (clipPos.w + 1e-5);

    if (check(ndc.xy)) return;
    float2 uv = float2(ndc.x * 0.5 + 0.5, (1.0 - ndc.y) * 0.5);

    float depth = DepthMap.SampleLevel(sampler, uv, 0).x;

    float curDepth = length(camPos - pos);

    if (curDepth < (depth + 2*radius + depthBias)) {
        int oldid;
        CountBuffer.InterlockedAdd(0, 1, oldid);
        surfaceIdx[oldid] = id;

        IsChosed[id] = IsChosed[id] + 1;
    }

}

[numthreads(32, 32, 1)]
void IdChose(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
             uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint2 coord = dispatchThreadID.xy;

    if (coord.x >= Width) return;
    if (coord.y >= Height) return;

    float id = DepthMap[coord].y;

    if (id == 0) return;

    uint pId = uint(id - 1.0f);
    uint oldid;
    InterlockedAdd(IsChosed[pId], 1, oldid);
    if (oldid == 0) {
        uint count;
        CountBuffer.InterlockedAdd(0, 1, count);
        surfaceIdx[count] = pId;
    }
}
RWStructuredBuffer<uint> tempSrufaceIdx;

[numthreads(32, 32, 1)]
void Sample(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint id = groupID.x * 32 * 32 + groupIndex;

    if (id >= surfaceNum) return;

    uint idx = tempSrufaceIdx[id];

    float3 pos = allParticles[idx];
    float depth = length(pos - camPos) * (dot(normalize(Front), normalize(pos - camPos)));
    depth = max(0.1f, depth);
    float x = radius * FocalLenth / depth;
    float pixel = x / FrameHeight * Height;

    if (pixel < minPixel) pixel = float(minPixel);
    if (pixel > maxPixel) pixel = float(maxPixel);

    float p = (pixel - minPixel) / (maxPixel - minPixel);
    p = minP +  (1.0 - minP) * p;

    UniformSampleGenerator sg = UniformSampleGenerator(id,1);
    float rand1 = sampleNext1D(sg);

    if (rand1 < p) {
        uint count;
        CountBuffer.InterlockedAdd(0, 1, count);
        surfaceIdx[count] = idx;
    }

}
