
RWTexture2D<float4> NormalDepth;
Texture2D<half> Thickness;
RWStructuredBuffer<float4> GTBuffer;

RWStructuredBuffer<half> FoamGTBuffer;

[numthreads(32, 32, 1)]
void test(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {

    uint2 ScreenCoord = uint2(dispatchThreadID.x, dispatchThreadID.y);
    uint id = ScreenCoord.y * Width + ScreenCoord.x;

    GTBuffer[id] = NormalDepth[ScreenCoord];
}

cbuffer Var {
    uint ParticleNum;
    float BigFoamMinRadius;
    uint flag;
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
Texture2D<float4> WaterNormalDepth;
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

    uint index1D = coord.y * Width + coord.x;


    uint2 tileCoord = ScreenToTile(coord);

    float2 ndc = ((coord + 0.5f) / float2(Width, Height)) * 2.0f - 1.0f;
    ndc.y *= -1;

    float3 dir = normalize(U * ndc.x + V * ndc.y + W);

    uint id = TileHead[tileCoord];

    float dWater = WaterNormalDepth[coord].w;
    bool hit = false;
    while (id != 0xFFFFFFFF) {
        uint curID = ResortedFoamList[id];
        float4 particle = FoamParticles[curID];
        float3 pos = particle.xyz;
        float radius = particle.w*2.5;
        float4 disHit = distancePtoL(pos, CamPos, dir, radius);
        float dis = disHit.x;
        float3 hitpos = float3(disHit.y, disHit.z, disHit.w);
        float d = length(CamPos - hitpos);

        if (dis < radius && d < dWater) {
            hit = true;
            break;
        }
        id = ResortedFoamNextList[id];
    }
    if (hit) {
        FoamGTBuffer[index1D * 2 + flag] = 1;
    }
    else {
        FoamGTBuffer[index1D * 2 + flag] = 0;
    }
}

RWStructuredBuffer<uint> SurfaceId;
[numthreads(32, 32, 1)]
void Surface(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
             uint3 groupID: SV_GroupID,                    
            uint groupIndex: SV_GroupIndex) {

    uint id = groupID.x * 32 * 32 + groupIndex;

    if (id >= ParticleNum) { return;}

    float4 posR = FoamParticles[id];
    float r = posR.w;

    float4 hPos = float4(float3(posR.xyz), 1.0f);

    float4 clipPos = mul(VPMat, hPos);
    clipPos.w = clipPos.w + 1e-6;
    float3 ndc = float3(clipPos.x, clipPos.y, clipPos.z) / clipPos.w;
    ndc.y *= -1.0;

    if (check(ndc.xy)) {
        return;
    }

    uint x = uint((ndc.x * 0.5 + 0.5) * Width);
    uint y = uint((ndc.y * 0.5 + 0.5) * Height);

    float depth = length(CamPos - posR.xyz);

    float waterDepth = WaterNormalDepth[uint2(x,y)].w;

    if (depth - r < waterDepth) {
        //能被看见
        uint globalid;
        GlobalCount.InterlockedAdd(0, 1, globalid);
        SurfaceId[globalid] = id;
    }

}
