// SphereRendering.cs.slang

cbuffer CB {
    uint gParticleCount;
    uint gMaxNodeCount;
};

cbuffer CameraData {
    float3 U;
    float3 V;
    float3 W;
    float3 CamPos;
    float4x4 gViewProjMat;
}


struct ListNode {
    uint particleId;
    uint next;
};

// 资源
StructuredBuffer<half4> Particles;

RWTexture2D<uint> TileHeads; 
RWStructuredBuffer<ListNode> LinkedListNodes;
RWByteAddressBuffer NodeCounter; // 原子计数器


RWTexture2D<float4> OutNormal; // RGB = Normal, A = small Or Big
RWTexture2D<float>  OutDepth;  // Depth

bool check(float2 ndc) {
    if (ndc.x > Width || ndc.x < 0) return false;
    if (ndc.y > Height || ndc.y < 0) return false;
    return true;
}

float2 intersectSphere(float3 ro, float3 rd, float3 center, float radius) {
    float3 oc = ro - center;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - radius * radius;
    float h = b * b - c;
    
    if (h < 0.0) return float2(-1.0, 0.0); 
    
    float t = -b - sqrt(h);
    return float2(t, 1.0);
}

[numthreads(32, 32, 1)]
void binParticles(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                  uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint pId = groupID.x * 32 * 32 + groupIndex;
    if (pId >= gParticleCount) return;

    float3 pos = Particles[pId].xyz;
    float r = Particles[pId].w;

    float4 clipPos = mul(gViewProjMat, float4(pos, 1.0));
    clipPos.w += 0.00001;
    if (clipPos.w < 0.1f) return;

    float projectedRadius = (r / clipPos.w) * max(Width, Height);

    float2 gScreenSize = float2(Width, Height);
    float2 ndcPos = clipPos.xy / clipPos.w;

    ndcPos.y *= -1;
    float2 screenPos = (ndcPos * 0.5 + 0.5) * gScreenSize;

    float2 maxPos = screenPos + float2(projectedRadius, projectedRadius);
    float2 minPos = screenPos - float2(projectedRadius, projectedRadius);

    /*
    if (!(check(maxPos)&&check(minPos))) {
        return;
    }
    */

    int2 minTile = int2(floor((screenPos - projectedRadius) / float(TileSize)));
    int2 maxTile = int2(floor((screenPos + projectedRadius) / float(TileSize)));

    int2 gridDim = int2(ceil(gScreenSize / float(TileSize)));
    minTile = max(minTile, int2(0, 0));
    maxTile = min(maxTile, gridDim - 1);


    for (int y = minTile.y; y <= maxTile.y; y++) {
        for (int x = minTile.x; x <= maxTile.x; x++) {
            
            uint nodeIdx;
            NodeCounter.InterlockedAdd(0, 1, nodeIdx);
            
            if (nodeIdx < gMaxNodeCount) {
                uint oldHead;
                InterlockedExchange(TileHeads[int2(x, y)], nodeIdx, oldHead);
                
                ListNode node;
                node.particleId = pId;
                node.next = oldHead;
                LinkedListNodes[nodeIdx] = node;
            }
        }
    }
}


[numthreads(TileSize,TileSize, 1)] // 刚好对应 TileSize
void renderSpheres(uint3 id : SV_DispatchThreadID) {
    if (id.x >= Width|| id.y >= Height) return;

    int2 tileCoord = id.xy / TileSize;
    float2 gScreenSize = float2(Width, Height);

    float2 uv = (float2(id.xy) + 0.5) / gScreenSize;
    float2 ndc = uv * 2.0 - 1.0;
    //ndc.y = -ndc.y;

    float3 rayDir = normalize(ndc.x * U + ndc.y * V + W);
    float3 rayOrigin = CamPos;

    uint currNode = TileHeads[tileCoord];

    /*
    if (currNode != 0xFFFFFFFF) {
        OutNormal[id.xy] = float4(1, 0, 0, 1); // 红色
        OutDepth[id.xy] = 0.5;                 // 随便写个深度
        return;                                // 强制返回，不跑后面的光线求交
    }*/

    float minT = 1e20;
    float3 bestNormal = float3(0, 0, 0);
    float bestR;
    bool hitAny = false;

    int safeLoop = 0;
    while (currNode != 0xFFFFFFFF && safeLoop < 256) {
        safeLoop++;
        
        ListNode node = LinkedListNodes[currNode];
        uint pId = node.particleId;
        
        float4 p = Particles[pId];

        float2 res = intersectSphere(rayOrigin, rayDir, p.xyz, p.w);
        
        if (res.y > 0.5) {
            float t = res.x;
            if (t > 0 && t < minT) {
                minT = t;
                hitAny = true;
                float3 hitPos = rayOrigin + t * rayDir;
                bestNormal = normalize(hitPos - p.xyz);
                bestR = p.w > 0.1 ? 3.0f : 2.0f;//大小粒子标记
            }
        }

        currNode = node.next;
    }

    if (safeLoop == 256) {
        if (currNode != 0xFFFFFFFF) {
            OutNormal[id.xy] = float4(1, 0, 0, 1); // 红色
            OutDepth[id.xy] = 0.5;                 // 随便写个深度
            return;                                // 强制返回，不跑后面的光线求交
        }
    }

    if (hitAny) {

        float3 finalHitPos = rayOrigin + minT * rayDir;
        float4 clipPos = mul(gViewProjMat, float4(finalHitPos, 1.0));
        float depth = clipPos.z / clipPos.w;

        OutNormal[id.xy] = float4(bestNormal * 0.5 + 0.5,bestR); // Pack normal
        OutDepth[id.xy] = depth;
    } else {
        // Clear value or keep background
        OutDepth[id.xy] = 1.0; 
        OutNormal[id.xy] = float4(0.0f, 0, 0,1.0f);
    }
}
