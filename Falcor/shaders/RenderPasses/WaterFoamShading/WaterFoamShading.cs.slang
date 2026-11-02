
RWTexture2D<half4> aimTex;

RWTexture2D<half> aimTexDim1;
RWStructuredBuffer<half> srcBuffer;

[numthreads(32, 32, 1)]
void BufferToTexDim4(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                 uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint id = groupID.x * 32 * 32 + groupIndex;

    uint y = id / Width;
    uint x = id % Width;

    aimTex[uint2(x, y)] = half4(srcBuffer[id * 4], srcBuffer[id * 4 + 1], srcBuffer[id * 4 + 2], srcBuffer[id * 4 + 3]);

}

[numthreads(32, 32, 1)]
void BufferToTexDim1(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                     uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint id = groupID.x * 32 * 32 + groupIndex;

    uint y = id / Width;
    uint x = id % Width;

    aimTexDim1[uint2(x, y)]= srcBuffer[id];
}
