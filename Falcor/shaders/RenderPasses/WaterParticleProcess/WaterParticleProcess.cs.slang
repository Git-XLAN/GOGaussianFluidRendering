/***************************************************************************
 # Copyright (c) 2015-23, NVIDIA CORPORATION. All rights reserved.
 #
 # Redistribution and use in source and binary forms, with or without
 # modification, are permitted provided that the following conditions
 # are met:
 #  * Redistributions of source code must retain the above copyright
 #    notice, this list of conditions and the following disclaimer.
 #  * Redistributions in binary form must reproduce the above copyright
 #    notice, this list of conditions and the following disclaimer in the
 #    documentation and/or other materials provided with the distribution.
 #  * Neither the name of NVIDIA CORPORATION nor the names of its
 #    contributors may be used to endorse or promote products derived
 #    from this software without specific prior written permission.
 #
 # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS "AS IS" AND ANY
 # EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 # PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 # CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 # EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 # PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 # PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 # OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 **************************************************************************/

    cbuffer Var {
        float KernelRadius;
        uint MaxNeighborNum;
        uint MaxParticleNum;
        float EnlargeFactor;
        float Radius;
        bool Train;
    }

    cbuffer Camera {
        float4x4 VPMat;
        float3 U;
    }

    RWStructuredBuffer<half4> OriginalParticles;
    RWStructuredBuffer<half3> ValidParticles;
    RWStructuredBuffer<half3> OriginalVelBuffer;
    RWStructuredBuffer<half3> ValidVelBuffer;

    RWStructuredBuffer<uint> CountBuffer;
    RWStructuredBuffer<uint> AssistBuffer;
    RWStructuredBuffer<uint> EdgeSrc;
    RWStructuredBuffer<uint> EdgeDst;
    RWStructuredBuffer<uint> RasterIndirectArgs;
    RWTexture2D<half> ThicknessTex;//Dont Delete
    RWStructuredBuffer<half> ThicknessTexBuffer; // Write this
    RWStructuredBuffer<float4> TriangleBuffer;

    RWStructuredBuffer<uint> GridEdge;

    bool check(float3 ndc) {
        return true;
    if (Train) {
        return true;
    }
    if (ndc.x > 1.1f || ndc.x < -1.1f) return false;
    if (ndc.y > 1.1f || ndc.y < -1.1f) return false;
    if (ndc.z > 1 || ndc.z < 0) return false;
    return true;
    }

groupshared uint validSize;

[numthreads(32, 32, 1)]
    void CMain(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {

        uint index = groupID.x * 32 * 32 * 1 + groupIndex;

        if (groupIndex == 0) {
            validSize = 0;
        }

        GroupMemoryBarrierWithGroupSync();

        
        if (index >= MaxParticleNum) return;

        float4 posR = OriginalParticles[index];
        float3 vel = OriginalVelBuffer[index];

        float radius = float(posR.w);
        float4 hPos = float4(float3(posR.xyz), 1.0f);

        float4 clipPos = mul(VPMat,hPos);
        clipPos.w = clipPos.w + 1e-6;
        float3 ndc = float3(clipPos.x, clipPos.y, clipPos.z) / clipPos.w;
        ndc.y *= -1.0;

        if (check(ndc)) {
            uint x = uint((ndc.x * 0.5 + 0.5) * Width);
            uint y = uint((ndc.y * 0.5 + 0.5) * Height);
            // just For Deug
            InterlockedAdd(validSize, uint(1));
        }
        else {
            OriginalParticles[index] = half4(0.0h, 0.0h, 0.0h, 0.0h);
            OriginalVelBuffer[index] = half3(0.0h, 0.0h, 0.0h);
        }
        
        GroupMemoryBarrierWithGroupSync();

        if (groupIndex == 0) {
            uint origin;
            InterlockedAdd(CountBuffer[0], validSize, origin);
            AssistBuffer[groupID.x] = origin;
        }
}


[numthreads(32, 32, 1)]
void Resort(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {

    uint index = groupID.x * 32 * 32 * 1 + groupIndex;
    if (groupIndex == 0) {
        validSize = 0;
    }

    GroupMemoryBarrierWithGroupSync();
    if (index >= MaxParticleNum) return;

    float4 posR = OriginalParticles[index];
    if (posR.w < 1e-6) return;

    uint globalId = AssistBuffer[groupID.x];
    uint localId;
    if (posR.w > 0.0f) {
        InterlockedAdd(validSize, 1u, localId);
    }
    GroupMemoryBarrierWithGroupSync();

    if (posR.w > 0) {
        ValidParticles[globalId + localId] = half3(posR.xyz);
        ValidVelBuffer[globalId + localId] = OriginalVelBuffer[index];

        //Just For Debug
        float4 hpos = float4(posR.xyz, 1.0f);
        float4 clipP = mul(VPMat, hpos);
        clipP.w = clipP.w + 1e-6;
        float3 ndc = clipP.xyz / clipP.w;

        ndc.y *= -1;
        uint x = uint((ndc.x * 0.5 + 0.5) * Width);
        uint y = uint((ndc.y * 0.5 + 0.5) * Height);
    }

}


    [numthreads(2, 1, 1)]
    void Clear(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
        uint index = groupID.x * 2 + groupIndex;
        if(groupID.x==0)
            CountBuffer[groupIndex] = 0;

        AssistBuffer[index] = 0;
    }

[numthreads(32, 32, 1)]
void Quad(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint index = groupID.x * 32 * 32 + groupIndex;

    if (index >= CountBuffer[0]) return;

    if (index == 0) {
        RasterIndirectArgs[0] = CountBuffer[0]*6;
        RasterIndirectArgs[1] = 1;
        RasterIndirectArgs[2] = 0;
        RasterIndirectArgs[3] = 0;
    }

    float3 pos = ValidParticles[index];

    GroupMemoryBarrierWithGroupSync();


    float4 homPos = float4(pos, 1.0f);
    float4 areaHomPos = homPos + EnlargeFactor * Radius * float4(normalize(U), 0.0f);
    float4 clipPos = mul(VPMat, homPos);
    float4 areaClipPos = mul(VPMat, areaHomPos);
    clipPos.w += 0.00001;
    areaClipPos.w += 0.00001;
    float3 ndc = clipPos.xyz / clipPos.w;
    float3 areaNdc = areaClipPos.xyz / areaClipPos.w;
    float ndcR = length(ndc.xy - areaNdc.xy);
    ndcR = max(1.0 / Width, ndcR);
    ndc.y *= -1.0;

    uint x = uint((ndc.x * 0.5 + 0.5) * Width);
    uint y = uint((ndc.y * 0.5 + 0.5) * Height);

    ndc.y *= -1.0f;
    float2 v0 = ndc.xy + float2(ndcR, ndcR);
    float2 v1 = ndc.xy + float2(ndcR, -ndcR);
    float2 v2 = ndc.xy - float2(ndcR, ndcR);
    float2 v3 = ndc.xy + float2(-ndcR, ndcR);

    TriangleBuffer[index * 6 + 0] = float4(v0, float2(1.0f, 1.0f));
    TriangleBuffer[index * 6 + 1] = float4(v1, float2(1.0f, 0.0f));
    TriangleBuffer[index * 6 + 2] = float4(v2, float2(0.0f, 0.0f));

    TriangleBuffer[index * 6 + 3] = float4(v2, float2(0.0f, 0.0f));
    TriangleBuffer[index * 6 + 4] = float4(v3, float2(0.0f, 1.0f));
    TriangleBuffer[index * 6 + 5] = float4(v0, float2(1.0f, 1.0f));

}

[numthreads(32, 32, 1)]
void TexToBuffer(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                 uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {

    uint2 ScreenCoord = uint2(dispatchThreadID.x, dispatchThreadID.y);
    uint id = ScreenCoord.y * Width + ScreenCoord.x;

    ThicknessTexBuffer[id] = ThicknessTex[ScreenCoord];
}



