// Uniform-grid neighbor structure and the paper's conservative binary density mask.
// A cell edge equals the SPH support radius, so all density contributors are in 3x3x3 cells.

static const float kPi = 3.14159265359;

cbuffer Params
{
    uint particleNum;
    float3 gridMin;
    uint3 gridDim;
    float smoothingRadius;
    float particleMass;
    float isoDensity;
    float aggregationDensity;
    float anisotropyRegularization;
    float densityQuantization;
}

struct AnisotropyData
{
    // Rows of G. row*.w stores abs(det(G)).
    float4 row0;
    float4 row1;
    float4 row2;
};

StructuredBuffer<float3> Particles;
RWStructuredBuffer<uint> CellCounts;
RWStructuredBuffer<uint> CellOffsets;
RWStructuredBuffer<uint> CellWriteCursor;
RWStructuredBuffer<uint> CellParticles;
RWStructuredBuffer<uint> DensityMask;
RWStructuredBuffer<uint> AggregationFlags;
RWStructuredBuffer<AnisotropyData> Anisotropy;

uint Flatten(uint3 c)
{
    return c.x + gridDim.x * (c.y + gridDim.y * c.z);
}

bool IsInside(int3 c)
{
    return all(c >= int3(0)) && all(c < int3(gridDim));
}

bool IsPositionInside(float3 p)
{
    return all(p >= gridMin) && all(p < gridMin + float3(gridDim) * smoothingRadius);
}

uint3 PositionToCell(float3 p)
{
    float3 cell = floor((p - gridMin) / smoothingRadius);
    return uint3(clamp(int3(cell), int3(0), int3(gridDim) - 1));
}

float Poly6AtZero()
{
    return 315.0 / (64.0 * kPi * pow(smoothingRadius, 9.0));
}

float Poly6(float r2)
{
    const float h2 = smoothingRadius * smoothingRadius;
    if (r2 >= h2) return 0.0;
    const float d = h2 - r2;
    return Poly6AtZero() * d * d * d;
}

float DensityAt(float3 p)
{
    const uint3 center = PositionToCell(p);
    float density = 0.0;

    for (int z = -1; z <= 1; ++z)
    for (int y = -1; y <= 1; ++y)
    for (int x = -1; x <= 1; ++x)
    {
        const int3 cell = int3(center) + int3(x, y, z);
        if (!IsInside(cell)) continue;

        const uint linearCell = Flatten(uint3(cell));
        for (uint index = CellOffsets[linearCell]; index < CellOffsets[linearCell + 1u]; ++index)
        {
            const uint particle = CellParticles[index];
            const float3 d = p - Particles[particle];
            density += particleMass * Poly6(dot(d, d));
        }
    }
    return density;
}

[numthreads(256, 1, 1)]
void ClearGrid(uint3 id : SV_DispatchThreadID)
{
    const uint cell = id.x;
    const uint cellCount = gridDim.x * gridDim.y * gridDim.z;
    if (cell >= cellCount) return;
    CellCounts[cell] = 0;
    CellWriteCursor[cell] = 0;
    DensityMask[cell] = 0;
}

[numthreads(256, 1, 1)]
void CountGrid(uint3 id : SV_DispatchThreadID)
{
    const uint particle = id.x;
    if (particle >= particleNum) return;
    if (!IsPositionInside(Particles[particle])) return;

    const uint cell = Flatten(PositionToCell(Particles[particle]));
    InterlockedAdd(CellCounts[cell], 1);
}

[numthreads(256, 1, 1)]
void FillGrid(uint3 id : SV_DispatchThreadID)
{
    const uint particle = id.x;
    if (particle >= particleNum || !IsPositionInside(Particles[particle])) return;

    const uint cell = Flatten(PositionToCell(Particles[particle]));
    uint slot;
    InterlockedAdd(CellWriteCursor[cell], 1u, slot);
    CellParticles[CellOffsets[cell] + slot] = particle;
}

[numthreads(256, 1, 1)]
void BuildAnisotropy(uint3 id : SV_DispatchThreadID)
{
    const uint particle = id.x;
    if (particle >= particleNum) return;

    const float3 p = Particles[particle];
    if (!IsPositionInside(p))
    {
        Anisotropy[particle].row0 = float4(1.0 / smoothingRadius, 0.0, 0.0, 1.0 / pow(smoothingRadius, 3.0));
        Anisotropy[particle].row1 = float4(0.0, 1.0 / smoothingRadius, 0.0, 0.0);
        Anisotropy[particle].row2 = float4(0.0, 0.0, 1.0 / smoothingRadius, 0.0);
        return;
    }

    float3 mean = 0.0;
    float weightSum = 0.0;
    const uint3 center = PositionToCell(p);
    for (int z = -1; z <= 1; ++z)
    for (int y = -1; y <= 1; ++y)
    for (int x = -1; x <= 1; ++x)
    {
        const int3 cell = int3(center) + int3(x, y, z);
        if (!IsInside(cell)) continue;
        const uint linearCell = Flatten(uint3(cell));
        for (uint index = CellOffsets[linearCell]; index < CellOffsets[linearCell + 1u]; ++index)
        {
            const uint neighbor = CellParticles[index];
            const float3 q = Particles[neighbor];
            const float w = Poly6(dot(q - p, q - p));
            mean += w * q;
            weightSum += w;
        }
    }
    mean /= max(weightSum, 1e-8);

    float c00 = 0.0, c01 = 0.0, c02 = 0.0, c11 = 0.0, c12 = 0.0, c22 = 0.0;
    for (int z = -1; z <= 1; ++z)
    for (int y = -1; y <= 1; ++y)
    for (int x = -1; x <= 1; ++x)
    {
        const int3 cell = int3(center) + int3(x, y, z);
        if (!IsInside(cell)) continue;
        const uint linearCell = Flatten(uint3(cell));
        for (uint index = CellOffsets[linearCell]; index < CellOffsets[linearCell + 1u]; ++index)
        {
            const uint neighbor = CellParticles[index];
            const float3 d = Particles[neighbor] - mean;
            const float w = Poly6(dot(Particles[neighbor] - p, Particles[neighbor] - p));
            c00 += w * d.x * d.x; c01 += w * d.x * d.y; c02 += w * d.x * d.z;
            c11 += w * d.y * d.y; c12 += w * d.y * d.z; c22 += w * d.z * d.z;
        }
    }
    const float regularization = max(anisotropyRegularization, 1e-4) * smoothingRadius * smoothingRadius;
    c00 = c00 / max(weightSum, 1e-8) + regularization;
    c01 /= max(weightSum, 1e-8); c02 /= max(weightSum, 1e-8);
    c11 = c11 / max(weightSum, 1e-8) + regularization;
    c12 /= max(weightSum, 1e-8); c22 = c22 / max(weightSum, 1e-8) + regularization;

    const float detC = c00 * (c11 * c22 - c12 * c12) - c01 * (c01 * c22 - c02 * c12) + c02 * (c01 * c12 - c02 * c11);
    const float invDet = 1.0 / max(abs(detC), 1e-12);
    float3 r0 = float3(c11 * c22 - c12 * c12, c02 * c12 - c01 * c22, c01 * c12 - c02 * c11) * invDet;
    float3 r1 = float3(c02 * c12 - c01 * c22, c00 * c22 - c02 * c02, c01 * c02 - c00 * c12) * invDet;
    float3 r2 = float3(c01 * c12 - c02 * c11, c01 * c02 - c00 * c12, c00 * c11 - c01 * c01) * invDet;

    // Normalize the inverse covariance so its geometric mean scale is 1/h.
    const float detInvC = abs(detC) > 1e-12 ? 1.0 / abs(detC) : 1.0;
    const float scale = 1.0 / (smoothingRadius * pow(detInvC, 1.0 / 3.0));
    r0 *= scale; r1 *= scale; r2 *= scale;
    const float detG = abs(dot(r0, cross(r1, r2)));
    Anisotropy[particle].row0 = float4(r0, detG);
    Anisotropy[particle].row1 = float4(r1, 0.0);
    Anisotropy[particle].row2 = float4(r2, 0.0);
}

[numthreads(256, 1, 1)]
void BuildDensityMask(uint3 id : SV_DispatchThreadID)
{
    const uint linearCell = id.x;
    const uint cellCount = gridDim.x * gridDim.y * gridDim.z;
    if (linearCell >= cellCount) return;

    const uint z = linearCell / (gridDim.x * gridDim.y);
    const uint rem = linearCell - z * gridDim.x * gridDim.y;
    const uint y = rem / gridDim.x;
    const uint x = rem - y * gridDim.x;

    uint surroundingCount = 0;
    for (int dz = -1; dz <= 1; ++dz)
    for (int dy = -1; dy <= 1; ++dy)
    for (int dx = -1; dx <= 1; ++dx)
    {
        const int3 neighbor = int3(x, y, z) + int3(dx, dy, dz);
        if (IsInside(neighbor)) surroundingCount += CellCounts[Flatten(uint3(neighbor))];
    }

    // Must use the exact quantization used by RayMarching::DensityAt().
    // Otherwise rounding can make an apparently empty cell contain an
    // iso-surface, producing discontinuities at binary-grid boundaries.
    const float q = max(densityQuantization, 1.0);
    const uint contributionQ = uint(round(max(0.0, particleMass * Poly6AtZero()) * q));
    const uint isoQ = uint(ceil(max(0.0, isoDensity) * q));
    DensityMask[linearCell] = float(surroundingCount) * float(contributionQ) >= float(isoQ) ? 1 : 0;
}

[numthreads(256, 1, 1)]
void ClassifyParticles(uint3 id : SV_DispatchThreadID)
{
    const uint particle = id.x;
    if (particle >= particleNum) return;
    const float3 p = Particles[particle];
    if (!IsPositionInside(p)) { AggregationFlags[particle] = 0; return; }

    float density = 0.0;
    const uint3 center = PositionToCell(p);
    for (int z = -1; z <= 1; ++z)
    for (int y = -1; y <= 1; ++y)
    for (int x = -1; x <= 1; ++x)
    {
        const int3 cell = int3(center) + int3(x, y, z);
        if (!IsInside(cell)) continue;
        const uint linearCell = Flatten(uint3(cell));
        for (uint index = CellOffsets[linearCell]; index < CellOffsets[linearCell + 1u]; ++index)
        {
            const uint neighbor = CellParticles[index];
            const AnisotropyData g = Anisotropy[neighbor];
            const float3 d = p - Particles[neighbor];
            const float3 gd = float3(dot(g.row0.xyz, d), dot(g.row1.xyz, d), dot(g.row2.xyz, d));
            const float q2 = dot(gd, gd);
            if (q2 < 1.0)
            {
                const float q = 1.0 - q2;
                density += particleMass * g.row0.w * (315.0 / (64.0 * kPi)) * q * q * q;
            }
        }
    }
    AggregationFlags[particle] = density >= aggregationDensity ? 1 : 0;
}
