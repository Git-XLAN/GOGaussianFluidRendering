
RWTexture2D<float4> NormalDepth;
Texture2D<half> Thickness;
RWStructuredBuffer<float4> GTBuffer;


[numthreads(32, 32, 1)]
void test(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {

    uint2 ScreenCoord = uint2(dispatchThreadID.x, dispatchThreadID.y);

    if (any(ScreenCoord >= uint2(Width, Height))) {
        return;
    }
    uint id = ScreenCoord.y * Width + ScreenCoord.x;

    GTBuffer[id] = NormalDepth[ScreenCoord];
}
