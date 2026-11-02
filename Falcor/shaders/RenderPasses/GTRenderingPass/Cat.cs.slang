

RWTexture2D<float4> NormalDepth;
Texture2D<float> Depth;

[numthreads(32, 32, 1)]
void Main(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint2 coord = dispatchThreadID.xy;
    float4 normalDepth = NormalDepth[coord];
    normalDepth.w = Depth[coord];
    NormalDepth[coord] = normalDepth;
}
