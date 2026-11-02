
 Texture2D<float4> SrcTex;
 RWStructuredBuffer<float4> DstBuffer;
 [numthreads(32, 32, 1)]
 void Tex2Buffer(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                 uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {

     uint2 coord = dispatchThreadID.xy;

     if (coord.x >= Width) return;
     if (coord.y >= Height) return;
     uint id = coord.y * Width + coord.x;
     DstBuffer[id] = SrcTex[coord];
 }
