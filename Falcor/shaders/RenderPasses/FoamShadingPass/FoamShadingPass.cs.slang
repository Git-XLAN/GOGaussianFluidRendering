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
    uint ParticleNum;
    float BigFoamMinRadius;
    float RadiusFactor;
}

cbuffer CameraData {
    float4x4 VPMat;
    float3 CamPos;
    float3 U;
    float3 V;
    float3 W;
}
RWByteAddressBuffer GlobalCount;
StructuredBuffer<half4> FoamParticles;
RWTexture2D<float4> NormalTex;
RWTexture2D<float> DepthTex;
RWStructuredBuffer<uint> ResortedFoamList;
RWStructuredBuffer<uint> ResortedFoamNextList;
RWTexture2D<uint> TileHead;


uint2 ScreenToTile(uint2 ScreenCoord) {
    return ScreenCoord / TileSize;
}

bool check(float2 ndc) {
    if (ndc.x > 1.0f || ndc.x < -1.0f) return true;
    if (ndc.y > 1.0f || ndc.y < -1.0f) return true;
    return false;
}

[numthreads(32, 32, 1)]
void Resort(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,                    
            uint groupIndex: SV_GroupIndex) {

    uint pid = groupID.x * 32 * 32 + groupIndex;
    if (pid >= ParticleNum) {
        return;
    }

    float4 particle = FoamParticles[pid];
    float3 pos = particle.xyz;
    float r = particle.w;

    float4 homPos = float4(pos, 1.0f);
    float4 clipPos = mul(VPMat, homPos);

    // Near Plane 保护
    if (clipPos.w < 0.1f) { return;}

    float3 ndc = clipPos.xyz / clipPos.w;

    ndc.y *= -1.0f;


    float projectedRadius = (r / clipPos.w) * max(Width, Height);


    float2 screenPos = (ndc.xy * 0.5 + 0.5) * float2(Width, Height);


    int2 minPosScreenI = int2(floor(screenPos - float2(projectedRadius, projectedRadius)));
    int2 maxPosScreenI = int2(ceil(screenPos + float2(projectedRadius, projectedRadius)));


    if (maxPosScreenI.x < 0 || minPosScreenI.x >= Width || 
        maxPosScreenI.y < 0 || minPosScreenI.y >= Height) {
        return;
    }

    minPosScreenI = max(minPosScreenI, int2(0, 0));
    maxPosScreenI = min(maxPosScreenI, int2(Width - 1, Height - 1));

    // 现在转回 uint 是安全的
    uint2 minPos = uint2(minPosScreenI);
    uint2 maxPos = uint2(maxPosScreenI);



    uint2 tileMin = ScreenToTile(minPos);
    uint2 tileMax = ScreenToTile(maxPos);

    for (uint x = tileMin.x; x <= tileMax.x; x++) {
        for (int y = tileMin.y; y <= tileMax.y; y++) {

            uint id;
            GlobalCount.InterlockedAdd(0, 1, id);

            uint oldHead;
            InterlockedExchange(TileHead[uint2(x, y)], id, oldHead);

            ResortedFoamList[id] = pid;
            ResortedFoamNextList[id] = oldHead;
            
        }
    }
}

float4 distancePtoL(float3 pos, float3 sta, float3 dir, float r) {
    float3 ap = pos - sta;
    float3 proj = dot(ap, dir) * dir;

    float dis = length(ap - proj);
    float sp = length(pos - sta);
    float k = sqrt(sp * sp - dis * dis);
    float delta = sqrt(r * r - dis * dis);

    float t = k - delta;

    float3 hitpos = sta + t * dir;
    return float4(dis, hitpos);
}

[numthreads(TileSize, TileSize, 1)]
void Gbuffer(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {

    uint2 coord = dispatchThreadID.xy;

    uint2 tileCoord = ScreenToTile(coord);

    float2 ndc = ((coord + 0.5f) / float2(Width, Height)) * 2.0f - 1.0f;
    ndc.y *= -1;

    float3 dir = normalize(U * ndc.x + V * ndc.y + W);

    uint id = TileHead[tileCoord];

    float dMin = 1e20;
    float4 normalF;
    bool hit = false;
    while (id != 0xFFFFFFFF) {
        uint curID = ResortedFoamList[id];
        float4 particle = FoamParticles[curID];
        float3 pos = particle.xyz;
        float radius = particle.w * RadiusFactor;
        float4 disHit = distancePtoL(pos, CamPos, dir, radius);
        float dis = disHit.x;
        float3 hitpos = float3(disHit.y, disHit.z, disHit.w);
        float d = length(CamPos - hitpos);

        if (dis < radius && d < dMin) {
            float3 normal = normalize(hitpos - pos);
            float flag = radius > BigFoamMinRadius ? 3.0f : 2.0f;
            normalF = float4(normal, flag);
            dMin = d;
            hit = true;
        }
        id = ResortedFoamNextList[id];
    }
    if (hit) {
        NormalTex[coord] = normalF;
        DepthTex[coord] = dMin;
    }

}
