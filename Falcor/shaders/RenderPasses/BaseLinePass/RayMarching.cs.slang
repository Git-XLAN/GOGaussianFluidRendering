static const uint kInvalid = 0xffffffff;
static const float kPi = 3.14159265359;

cbuffer CameraData
{
    float3 camPos;
    float3 U;
    float3 V;
    float3 W;
}

cbuffer Params
{
    uint particleNum;
    float3 gridMin;
    float3 gridMax;
    uint3 gridDim;
    float smoothingRadius;
    float particleMass;
    float isoDensity;
    float traceStep;
    float searchBand;
    uint maxSteps;
    uint maxSkipSteps;
    float normalBlendDistance;
    float normalBlendRadius;
    float radius;
    float flatVarianceLow;
    float flatVarianceHigh;
    float densityQuantization;
    uint normalMode;
    uint enableAdaptiveResolution;
    uint enableAggregationSkip;
    uint enableDensityMaskSkip;
}

Texture2D<float4> InputDepth;
RWTexture2D<float> OutputDepth;

Texture2D<float> FilteredDepth;
Texture2D<float> AggregationDepth;
RWTexture2D<uint> TileRate;
StructuredBuffer<float3> Particles;
StructuredBuffer<uint> CellOffsets;
StructuredBuffer<uint> CellParticles;
StructuredBuffer<uint> DensityMask;
RWTexture2D<float4> Result;
Texture2D<float4> SparseResult;

float2 PixelToNdc(uint2 pixel)
{
    float2 ndc = ((float2(pixel) + 0.5) / float2(Width, Height)) * 2.0 - 1.0;
    ndc.y *= -1.0;
    return ndc;
}

float3 GetRay(uint2 pixel)
{
    const float2 ndc = PixelToNdc(pixel);
    return normalize(U * ndc.x + V * ndc.y + W);
}

float ViewDepthToRayDistance(float viewDepth, float3 ray)
{
    // ParticleDepth stores abs(view-space z), whereas all ray-marching values use world ray distance.
    return viewDepth / max(abs(dot(ray, normalize(W))), 1e-5);
}

float Gaussian(float x, float sigma)
{
    return exp(-(x * x) / max(2.0 * sigma * sigma, 1e-6));
}

[numthreads(16, 16, 1)]
void BilateralDepth(uint3 id : SV_DispatchThreadID)
{
    const uint2 pixel = id.xy;
    if (any(pixel >= uint2(Width, Height))) return;

    const float centerViewDepth = InputDepth[pixel].x;
    if (centerViewDepth <= 0.0)
    {
        OutputDepth[pixel] = 0.0;
        return;
    }

    const float centerDepth = ViewDepthToRayDistance(centerViewDepth, GetRay(pixel));
    const int filterRadius = clamp(int(ceil(radius * Height / max(centerViewDepth, 1e-3))), 1, 6);
    const float spatialSigma = max(float(filterRadius) / 2.0, 0.5);
    const float depthSigma = max(smoothingRadius * 0.5, 1e-4);

    float weightSum = 0.0;
    float depthSum = 0.0;
    for (int y = -filterRadius; y <= filterRadius; ++y)
    for (int x = -filterRadius; x <= filterRadius; ++x)
    {
        const int2 samplePixel = clamp(int2(pixel) + int2(x, y), int2(0), int2(Width - 1, Height - 1));
        const float sampleViewDepth = InputDepth[uint2(samplePixel)].x;
        if (sampleViewDepth <= 0.0) continue;

        const float sampleDepth = ViewDepthToRayDistance(sampleViewDepth, GetRay(uint2(samplePixel)));
        const float w = Gaussian(length(float2(x, y)), spatialSigma) * Gaussian(sampleDepth - centerDepth, depthSigma);
        depthSum += w * sampleDepth;
        weightSum += w;
    }
    OutputDepth[pixel] = depthSum / max(weightSum, 1e-6);
}

[numthreads(1, 1, 1)]
void EvaluateTiles(uint3 id : SV_DispatchThreadID)
{
    const uint2 tile = id.xy;
    const uint2 start = tile * TileSize;
    if (any(start >= uint2(Width, Height))) return;

    if (enableAdaptiveResolution == 0)
    {
        TileRate[tile] = 1;
        return;
    }

    float sum = 0.0;
    float sumSq = 0.0;
    uint count = 0;
    for (uint y = 0; y < TileSize && start.y + y < Height; ++y)
    for (uint x = 0; x < TileSize && start.x + x < Width; ++x)
    {
        const float d = InputDepth[start + uint2(x, y)].x;
        if (d <= 0.0) continue;
        sum += d;
        sumSq += d * d;
        ++count;
    }

    const float variance = count > 0 ? max(0.0, sumSq / count - pow(sum / count, 2.0)) : 1e20;
    const bool sparseOrDiscontinuous = count < (TileSize * TileSize) / 2;
    TileRate[tile] = sparseOrDiscontinuous ? 1 : (variance <= flatVarianceLow ? 4 : (variance <= flatVarianceHigh ? 2 : 1));
}

uint Flatten(uint3 c)
{
    return c.x + gridDim.x * (c.y + gridDim.y * c.z);
}

bool IsInside(int3 c)
{
    return all(c >= int3(0)) && all(c < int3(gridDim));
}

int3 PositionToCellUnclamped(float3 p)
{
    return int3(floor((p - gridMin) / smoothingRadius));
}

uint3 PositionToCell(float3 p)
{
    return uint3(clamp(PositionToCellUnclamped(p), int3(0), int3(gridDim) - 1));
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

uint QuantizeDensity(float density)
{
    const float q = round(max(0.0, density) * densityQuantization);
    return q >= 4294967040.0 ? 0xffffffffu : uint(q);
}

float DensityAt(float3 p)
{
    const int3 center = PositionToCellUnclamped(p);
    uint densityQ = 0u;
    for (int z = -1; z <= 1; ++z)
    for (int y = -1; y <= 1; ++y)
    for (int x = -1; x <= 1; ++x)
    {
        const int3 cell = center + int3(x, y, z);
        if (!IsInside(cell)) continue;
        const uint linearCell = Flatten(uint3(cell));
        for (uint index = CellOffsets[linearCell]; index < CellOffsets[linearCell + 1u]; ++index)
        {
            const uint particle = CellParticles[index];
            const float3 d = p - Particles[particle];
            // Saturating non-negative integer addition is associative and
            // avoids modulo-2^32 density wrap when h is small.
            const uint contributionQ = QuantizeDensity(particleMass * Poly6(dot(d, d)));
            if (densityQ > 0xffffffffu - contributionQ)
            {
                densityQ = 0xffffffffu;
            }
            else
            {
                densityQ += contributionQ;
            }
        }
    }
    return float(densityQ) / densityQuantization;
}

float3 ObjectNormal(float3 p)
{
    // DensityAt() uses quantized integer accumulation. Central differences
    // therefore produce a stable normal even though linked-list insertion
    // order is not deterministic from frame to frame.
    const float e = max(smoothingRadius * 0.02, 1e-4);
    const float3 ex = float3(e, 0.0, 0.0);
    const float3 ey = float3(0.0, e, 0.0);
    const float3 ez = float3(0.0, 0.0, e);
    const float3 gradient = float3(
        DensityAt(p + ex) - DensityAt(p - ex),
        DensityAt(p + ey) - DensityAt(p - ey),
        DensityAt(p + ez) - DensityAt(p - ez)
    );
    return length(gradient) > 1e-6 ? normalize(-gradient) : float3(0.0);
}

float3 ScreenNormal(uint2 pixel)
{
    const float centerDepth = FilteredDepth[pixel];
    if (centerDepth <= 0.0) return float3(0.0);

    const int2 p = int2(pixel);
    const int2 left = clamp(p + int2(-1, 0), int2(0), int2(Width - 1, Height - 1));
    const int2 right = clamp(p + int2(1, 0), int2(0), int2(Width - 1, Height - 1));
    const int2 up = clamp(p + int2(0, -1), int2(0), int2(Width - 1, Height - 1));
    const int2 down = clamp(p + int2(0, 1), int2(0), int2(Width - 1, Height - 1));

    const float3 pc = camPos + centerDepth * GetRay(pixel);
    float3 pl = camPos + FilteredDepth[uint2(left)] * GetRay(uint2(left));
    float3 pr = camPos + FilteredDepth[uint2(right)] * GetRay(uint2(right));
    float3 pu = camPos + FilteredDepth[uint2(up)] * GetRay(uint2(up));
    float3 pd = camPos + FilteredDepth[uint2(down)] * GetRay(uint2(down));
    if (FilteredDepth[uint2(left)] <= 0.0) pl = pc;
    if (FilteredDepth[uint2(right)] <= 0.0) pr = pc;
    if (FilteredDepth[uint2(up)] <= 0.0) pu = pc;
    if (FilteredDepth[uint2(down)] <= 0.0) pd = pc;

    const float3 n = cross(pr - pl, pd - pu);
    return length(n) > 1e-6 ? normalize(n) : float3(0.0);
}

float DistanceToCellExit(float3 p, float3 dir)
{
    const uint3 cell = PositionToCell(p);
    const float3 cellMin = gridMin + float3(cell) * smoothingRadius;
    const float3 cellMax = cellMin + smoothingRadius;
    const float3 boundary = float3(dir.x >= 0.0 ? cellMax.x : cellMin.x, dir.y >= 0.0 ? cellMax.y : cellMin.y,
                                   dir.z >= 0.0 ? cellMax.z : cellMin.z);
    const float3 dt = (boundary - p) / dir;
    float stepLength = 1e20;
    if (dt.x > 1e-5) stepLength = min(stepLength, dt.x);
    if (dt.y > 1e-5) stepLength = min(stepLength, dt.y);
    if (dt.z > 1e-5) stepLength = min(stepLength, dt.z);
    return stepLength < 1e19 ? stepLength + 1e-4 : smoothingRadius;
}

bool IntersectDomain(float3 ray, out float tNear, out float tFar)
{
    const float3 safeRay = float3(
        abs(ray.x) < 1e-8 ? (ray.x >= 0.0 ? 1e-8 : -1e-8) : ray.x,
        abs(ray.y) < 1e-8 ? (ray.y >= 0.0 ? 1e-8 : -1e-8) : ray.y,
        abs(ray.z) < 1e-8 ? (ray.z >= 0.0 ? 1e-8 : -1e-8) : ray.z
    );
    const float3 invDir = 1.0 / safeRay;
    const float3 t0 = (gridMin - camPos) * invDir;
    const float3 t1 = (gridMax - camPos) * invDir;
    const float3 lo = min(t0, t1);
    const float3 hi = max(t0, t1);
    tNear = max(max(lo.x, lo.y), lo.z);
    tFar = min(min(hi.x, hi.y), hi.z);
    return tFar >= max(tNear, 0.0);
}

float RefineHit(float3 ray, float tOutside, float tInside)
{
    float a = tOutside;
    float b = tInside;
    [unroll]
    for (uint refine = 0; refine < 8; ++refine)
    {
        const float mid = 0.5 * (a + b);
        if (DensityAt(camPos + mid * ray) >= isoDensity) b = mid;
        else a = mid;
    }
    return b;
}

[numthreads(16, 16, 1)]
void RayMarch(uint3 id : SV_DispatchThreadID)
{
    const uint2 pixel = id.xy;
    if (any(pixel >= uint2(Width, Height))) return;

    const uint rate = (enableAdaptiveResolution != 0) ? max(TileRate[pixel / TileSize], 1u) : 1u;
    if (normalMode != 1 && ((pixel.x % rate) != 0 || (pixel.y % rate) != 0))
    {
        Result[pixel] = float4(0.0);
        return;
    }

    const float entry = FilteredDepth[pixel];
    if (entry <= 0.0)
    {
        Result[pixel] = float4(0.0);
        return;
    }

    const float3 ray = GetRay(pixel);
    const float3 screenN = ScreenNormal(pixel);
    if (normalMode == 1)
    {
        float3 n = screenN;
        if (dot(n, ray) > 0.0) n = -n;
        Result[pixel] = float4(n, entry);
        return;
    }

    float domainNear, domainFar;
    if (!IntersectDomain(ray, domainNear, domainFar))
    {
        Result[pixel] = float4(0.0);
        return;
    }

    const float stepSize = max(traceStep, 1e-5);
    const float domainStart = max(0.0, domainNear);
    const float tMax = min(domainFar, entry + max(searchBand, stepSize));
    float t = max(domainStart, entry - searchBand);

    float density = DensityAt(camPos + t * ray);
    for (uint backtrack = 0; density >= isoDensity && t > domainStart && backtrack < maxSteps; ++backtrack)
    {
        t = max(domainStart, t - stepSize);
        density = DensityAt(camPos + t * ray);
    }

    float previousT = t;
    float previousDensity = density;
    bool skippedToAggregation = false;
    bool hit = false;
    float hitT = 0.0;

    for (uint step = 0; step < maxSteps; ++step)
    {
        if (enableAggregationSkip != 0 && step >= maxSkipSteps && !skippedToAggregation)
        {
            const float aggregationT = AggregationDepth[pixel];
            if (aggregationT > t && aggregationT <= tMax)
            {
                const float jumpDensity = DensityAt(camPos + aggregationT * ray);
                if (jumpDensity < isoDensity)
                {
                    t = aggregationT;
                    previousT = t;
                    previousDensity = jumpDensity;
                }
            }
            skippedToAggregation = true;
        }

        const float3 p = camPos + t * ray;
        if (any(p < gridMin) || any(p >= gridMax) || t > tMax) break;

        if (enableDensityMaskSkip != 0)
        {
            const int3 cell = PositionToCellUnclamped(p);
            if (IsInside(cell) && DensityMask[Flatten(uint3(cell))] == 0)
            {
                previousT = t;
                previousDensity = 0.0;
                t += DistanceToCellExit(p, ray);
                continue;
            }
        }

        const float currentDensity = DensityAt(p);
        if (previousDensity < isoDensity && currentDensity >= isoDensity)
        {
            hitT = RefineHit(ray, previousT, t);
            hit = true;
            break;
        }

        previousT = t;
        previousDensity = currentDensity;
        t += stepSize;
    }

    if (!hit)
    {
        Result[pixel] = float4(0.0);
        return;
    }

    const float3 hitPos = camPos + hitT * ray;
    float3 objectN = ObjectNormal(hitPos);
    float3 finalN = screenN;
    if (length(objectN) > 1e-6)
    {
        if (normalMode == 2)
        {
            finalN = objectN;
        }
        else if (normalMode == 0)
        {
            const float distanceWeight = saturate(normalBlendDistance * length(hitPos - (camPos + entry * ray)));
            const float screenParticleRadius = Height * radius / max(entry, 1e-4);
            const float radiusWeight = saturate(exp(normalBlendRadius * screenParticleRadius));
            const float objectWeight = min(distanceWeight * radiusWeight, 1.0);
            finalN = length(screenN) > 1e-6 ? normalize(lerp(screenN, objectN, objectWeight)) : objectN;
        }
    }
    if (dot(finalN, ray) > 0.0) finalN = -finalN;
    Result[pixel] = float4(finalN, hitT);
}

[numthreads(16, 16, 1)]
void ResolveAdaptiveRays(uint3 id : SV_DispatchThreadID)
{
    const uint2 pixel = id.xy;
    if (any(pixel >= uint2(Width, Height))) return;

    // Full-resolution copy unless adaptive resolution is explicitly enabled.
    if (normalMode == 1 || enableAdaptiveResolution == 0)
    {
        Result[pixel] = SparseResult[pixel];
        return;
    }

    const uint rate = max(TileRate[pixel / TileSize], 1u);
    if (rate == 1)
    {
        Result[pixel] = SparseResult[pixel];
        return;
    }

    const uint2 maxSample = ((uint2(Width, Height) - 1) / rate) * rate;
    const uint2 p00 = min((pixel / rate) * rate, maxSample);
    const uint2 p10 = min(p00 + uint2(rate, 0), maxSample);
    const uint2 p01 = min(p00 + uint2(0, rate), maxSample);
    const uint2 p11 = min(p00 + uint2(rate, rate), maxSample);
    const float2 f = float2(pixel - p00) / rate;

    const float4 a = lerp(SparseResult[p00], SparseResult[p10], f.x);
    const float4 b = lerp(SparseResult[p01], SparseResult[p11], f.x);
    float4 value = lerp(a, b, f.y);
    if (value.w > 0.0) value.xyz = normalize(value.xyz);
    Result[pixel] = value;
}
