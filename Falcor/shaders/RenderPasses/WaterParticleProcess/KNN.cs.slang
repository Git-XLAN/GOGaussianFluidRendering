
cbuffer Var {
    bool useUniformHashGrid;
    uint hashTableSize; // valid if useUniformHashGrid==false
    float particleRadius;
    float kernelRadius;
    float3 gridMin;
    uint3 gridDim; // valid if useUniformHashGrid==true
    uint maxNeighborNum;
    float threshold1;//直接有效的阈值
    float threshold2;//第一轮传递有效的阈值
    float threshold3;
    uint propStage;//第几轮传播
}

#define MAX_T 64
Texture2D<uint> Input;
RWTexture2D<uint> output;

RWStructuredBuffer<half3> Particles;//最终的结果写入这里
StructuredBuffer<uint> ParticleNums;
RWStructuredBuffer<uint> GridHeads;
RWStructuredBuffer<uint> ParticleNext;
RWStructuredBuffer<uint> IndirectArgs;
RWStructuredBuffer<half4> OriginalParticles; // 存放Culling后的结果,前三维表示Pos

RWStructuredBuffer<half3> OriginalVelBuffer;
RWStructuredBuffer<half3> VelBuffer;


RWStructuredBuffer<uint> ParticlesState;
RWStructuredBuffer<uint> ValidCount;

RWStructuredBuffer<uint> NeighborList;
RWStructuredBuffer<uint> NeighborCounts;
StructuredBuffer<uint> PrefixSum;

RWStructuredBuffer<uint> LinkSrcOut;
RWStructuredBuffer<uint> LinkDstOut;
RWByteAddressBuffer LinkCounter;


uint getGridHash(int3 gridPos) {
    if (useUniformHashGrid) {
        return gridPos.z * (gridDim.x * gridDim.y) + gridPos.y * gridDim.x + gridPos.x;
    }
    else {
        const uint p1 = 73856093;
        const uint p2 = 19349663;
        const uint p3 = 83492791;
        uint n = p1 * uint(gridPos.x) ^ p2 * uint(gridPos.y) ^ p3 * uint(gridPos.z);
        return n % hashTableSize;
    }
}

[numthreads(32, 32, 1)]
void ClearGrid(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {

    uint cellIndex = groupID.x * 32 * 32 + groupIndex;

    if (cellIndex < 3) {
        uint temp = (cellIndex == 0 ? ParticleNums[0] : 1);
        IndirectArgs[cellIndex] = temp;
    }

    uint hashSize = useUniformHashGrid ? (gridDim.x * gridDim.y * gridDim.z) : hashTableSize;
    if (cellIndex < hashSize) {
        // 0xFFFFFFFF 代表空指针 (-1)
        GridHeads[cellIndex] = 0xFFFFFFFF;
    }
}

[numthreads(32, 32, 1)]
void BuildGrid(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {

    uint pId = groupID.x * 32 * 32 + groupIndex;
    if (pId >= ParticleNums[0]) return;
    float3 pos = Particles[pId];
    ParticleNext[pId] = 0xFFFFFFFF;
    OriginalParticles[pId] = half4(half3(pos), 0.h);

    OriginalVelBuffer[pId] = VelBuffer[pId];

    int3 gridPos;
    float cellSize = (particleRadius * kernelRadius);
    if (!useUniformHashGrid)
        gridPos = (int3)floor(pos / cellSize);

    else {
        float3 relativePos = pos - gridMin;
        gridPos = (int3)floor(relativePos / cellSize);
    }

    uint cellHash = getGridHash(gridPos);

    uint oldHead;
    InterlockedExchange(GridHeads[cellHash], pId, oldHead);

    ParticleNext[pId] = oldHead;
}

bool Check(int3 grid) {


    if (!useUniformHashGrid) return true;
    if (any(grid) < 0) return false;
    if (any(grid >= gridDim)) return false;

    return true;
}

[numthreads(32, 32, 1)]
void SearchAndSort(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                   uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint pId = groupID.x * 32 * 32 + groupIndex;
    if (pId >= ParticleNums[0]) return;

    ParticlesState[pId] = 0;
    ValidCount[pId] = 0;

    float4 par = OriginalParticles[pId];
    float3 myPos = par.xyz;
    float searchRadius = kernelRadius * particleRadius;
    float searchRadiusSq = searchRadius * searchRadius;
    float radiusSq = 3*particleRadius * particleRadius;
    float cellSize = searchRadius;

    int3 centerGrid;
    if (useUniformHashGrid) {
        float3 relativePos = myPos - gridMin;
        centerGrid = (int3)floor(relativePos / cellSize);
    }
    else {
        centerGrid = (int3)floor(myPos / cellSize);
    }
    

    // 局部数组：维护最近的 T 个邻居
    // keys: 距离平方 (用于比较)
    // values: 粒子ID
    float cacheDist[MAX_T];
    uint cacheIdx[MAX_T];
    uint count = 0;

    // 初始化为最大距离
    [unroll]
    for (int i = 0; i < MAX_T; i++) cacheDist[i] = 3.402823466e+38F; // FLT_MAX

    // 1. 遍历 3x3x3 网格
    // 假设 cellSize >= searchRadius。如果 cellSize 较小，需要遍历更多格子
    int range = 1;

    for (int z = -range; z <= range; z++) {
        for (int y = -range; y <= range; y++) {
            for (int x = -range; x <= range; x++) {

                if (!Check(centerGrid + int3(x, y, z))) continue;
                uint h = getGridHash(centerGrid + int3(x, y, z));
                uint currNode = GridHeads[h];

                // 遍历链表
                while (currNode != 0xFFFFFFFF) {
                    uint otherId = currNode;
                    // 提前读取 Next 以防后续逻辑复杂
                    currNode = ParticleNext[currNode];

                    if (otherId == pId) continue;

                    float3 otherPos = OriginalParticles[otherId].xyz;
                    float3 diff = otherPos - myPos;
                    float d2 = dot(diff, diff);

                    if (d2 < searchRadiusSq && d2>radiusSq) {
                        // 【核心逻辑】插入排序 / 维护 Top-T

                        // 1. 如果还没满，直接加
                        if (count < maxNeighborNum) {
                            cacheDist[count] = d2;
                            cacheIdx[count] = otherId;
                            count++;
                        }
                        // 2. 如果满了，看能不能替换掉最远的那个
                        else {
                            // 找当前最远的
                            float maxD = -1.0;
                            int maxPtr = -1;
                            for (int k = 0; k < maxNeighborNum; k++) {
                                if (cacheDist[k] > maxD) {
                                    maxD = cacheDist[k];
                                    maxPtr = k;
                                }
                            }

                            // 如果新粒子更近，替换掉最远的
                            if (d2 < maxD) {
                                cacheDist[maxPtr] = d2;
                                cacheIdx[maxPtr] = otherId;
                            }
                        }
                    }
                }
            }
        }
    }

    // 2. 写入 Global Memory
    NeighborCounts[pId] = count;

    if (count <= floor(maxNeighborNum * threshold1)) {
        ParticlesState[pId] = 1;
        ValidCount[pId] = 1;
    }

    uint baseOffset = pId * maxNeighborNum; // 注意这里 stride 是 T (不是 MAX_T，取决于 C++ 设置)
    for (uint i = 0; i < count; i++) {
        NeighborList[baseOffset + i] = cacheIdx[i];
    }
}


[numthreads(32, 32, 1)]
void Propagate(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
               uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint pId = groupID.x * 32 * 32 + groupIndex;
    if (pId >= ParticleNums[0]) return;

    uint state = ParticlesState[pId];

    if (state > 0) return;

    // 扩散
    uint targetPrevState = propStage;
    uint count = NeighborCounts[pId];
    
    if (targetPrevState == 1 && count > floor(maxNeighborNum * threshold2)) {
        return;//第一轮扩散要求邻居数量小于一定阈值
    }

    if (targetPrevState == 2 && count > floor(maxNeighborNum * threshold3)) {
        return;
    }
    
    uint baseOffset = pId * maxNeighborNum;

    // 目标状态：如果是 Stage 1，找 State 1 的邻居，标记自身为Stage 2
    // 如果是 Stage 2，我们要找 State 2 的邻居，标记为Stage 3
    //Run 两轮 一轮找 propStage = 1 一轮找propStage = 2
    

    for (uint i = 0; i < count; i++) {
        uint neighborId = NeighborList[baseOffset + i];
        
        if (ParticlesState[neighborId] == targetPrevState) {
            ParticlesState[pId] = targetPrevState + 1; // 标记为下一级
            ValidCount[pId] = 1;
            break;                             
        }
    }
}

[numthreads(32, 32, 1)]
void CompactAndOutput(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
                      uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint oldId = groupID.x * 32 * 32 + groupIndex;
    if (oldId >= ParticleNums[0]) return;

    uint state = ParticlesState[oldId];
    if (state == 0) return; // 无效粒子直接跳过

    // 获取新索引 (利用前缀和)
    // PrefixSum[oldId] 存的是 outputBuffer 中的 index
    uint newIdx = PrefixSum[oldId];

    // 3. 输出位置
    Particles[newIdx] = OriginalParticles[oldId].xyz;
    VelBuffer[newIdx] = OriginalVelBuffer[oldId];

    // 4. 输出连接关系
    uint count = NeighborCounts[oldId];
    uint baseOffset = oldId * maxNeighborNum;

    for (uint i = 0; i < count; i++) {
        uint neighborOldId = NeighborList[baseOffset + i];

        // 只有当邻居也是有效粒子时，才建立连接
        if (ParticlesState[neighborOldId] > 0) {
            uint neighborNewIdx = PrefixSum[neighborOldId];


            // 原子申请写入位置
            uint edgeWriteIdx;
            LinkCounter.InterlockedAdd(0, 1, edgeWriteIdx);

            LinkSrcOut[edgeWriteIdx] = newIdx;         // 新索引
            LinkDstOut[edgeWriteIdx] = neighborNewIdx; // 新索引
        }
    }
}




[numthreads(32, 32, 1)]
void TestMain(uint3 dispatchThreadID: SV_DispatchThreadID, 
              uint3 groupThreadID: SV_GroupThreadID,
              uint3 groupID: SV_GroupID,                   
              uint groupIndex: SV_GroupIndex) {
    uint2 coord = dispatchThreadID.xy;
    output[coord] = Input[coord];
    
}
