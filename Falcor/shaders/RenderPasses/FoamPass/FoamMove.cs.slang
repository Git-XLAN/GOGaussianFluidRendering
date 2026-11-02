import Utils.Sampling.UniformSampleGenerator;

struct FoamParticle {
    half3 position;
    half radius;
    half lifeTime;
    half3 vel;
}

cbuffer GlobalVar {
    uint newFoamNum;
    uint foamNum;
    float timeStep;
    float radiusMu;
    float radiusSigma;
    uint frameCount;
    float enlargeFactor;

    float3 boundMax;
}

cbuffer PhysicalVar {
    float bubbleG;
    float dragFactor;
    float surfaceRange;
}

cbuffer CameraData {
    float4x4 VPMat;
    float3 camPos;
    float3 U;
    float3 V;
    float3 W;
}

RWStructuredBuffer<FoamParticle> FoamNextBuffer;
RWStructuredBuffer<float> FoamDepth;

RWStructuredBuffer<FoamParticle> FoamBuffer;

struct NewFoamData {
    half3 pos;
    half3 vel;
}
StructuredBuffer<NewFoamData> NewFoamBuffer;

StructuredBuffer<half4> SurfaceVelDepth;
RWTexture2D<float4> VelDepthTex;

RWByteAddressBuffer GlobalCount;
bool check(float3 ndc) {
    if (ndc.x > 1.0f || ndc.x < -1.0f) return false;
    if (ndc.y > 1.0f || ndc.y < -1.0f) return false;
    if (ndc.z > 1 || ndc.z < 0) return false;
    return true;
}
float3 getVelFactor(half3 pos) {
    if (abs(pos.x) > boundMax.x) return float3(-0.5f, 1.0f, 1.0f);
    if (abs(pos.y) > boundMax.y) return float3(1.0f, -0.5f, 1.0f);
    if (abs(pos.z) > boundMax.z) return float3(1.0f, 1.0f, -0.5f);

    return float3(1.0f,1.0f,1.0f);
}

bool inBox(half3 pos) {
    if (abs(pos.x) > boundMax.x) return false;
    if (pos.y < -boundMax.y) return false;
    if (abs(pos.z) > boundMax.z) return false;

    return true;
}

[numthreads(32, 32, 1)]
void Move(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,
          uint groupIndex: SV_GroupIndex) {
    uint pid = groupID.x * 32 * 32 + groupIndex;
    if (pid >= foamNum) {
        return;
    }
    FoamParticle par = FoamBuffer[pid];
    float life = par.lifeTime;
    uint oldid;

    life -= timeStep;
    if (life <= 0) { return;}

    par.lifeTime = half(life);

    float3 pos = par.position;
    float depth = length(pos - camPos);

    float3 dir = normalize(pos - camPos);

    float4 clipPos = mul(VPMat, float4(pos, 1.0f));
    float3 ndc = clipPos.xyz /(clipPos.w + 1e-5);

    ndc.y *= -1.0f;

    par.position = par.position + par.vel * timeStep;

    if (check(ndc)) {
        uint x = (ndc.x * 0.5f + 0.5f) * Width;
        uint y = (ndc.y * 0.5f + 0.5f) * Height;

        float4 velDepth = VelDepthTex[uint2(x,y)];
        float d = velDepth.w;

        if (d == 0) {
            par.vel = par.vel - float3(0.0f, 9.8, 0.0f) * dragFactor * timeStep;
        }
        else {
            if (depth > (d + surfaceRange)&&depth<(d+surfaceRange*2.0f)) {
                /*UnderWater*/
                par.vel = par.vel + float3(0.0f, 0.1f*bubbleG,0.0f) * timeStep;
            }
            else if (depth < (d - surfaceRange)) {
                par.vel = par.vel - float3(0.0f, 9.8, 0.0f) * dragFactor * timeStep;
            }
            
            else {

                float3 pos = camPos + d * dir;
                // par.lifeTime = 0;
                par.vel = velDepth.xyz;
                //par.position = pos;
            }
            
        }
        

        
    }

    else {
        par.vel = par.vel;// - float3(0.0f, 9.8, 0.0f) * dragFactor * timeStep;
        //采用原来的速度继续运动
    }

    
    if (!inBox(par.position)) {
        par.lifeTime = 0;
    }
    
    

    /*
    float3 boundFactor = getVelFactor(par.position);
    par.vel = boundFactor * par.vel;
    */
    GlobalCount.InterlockedAdd(0, 1, oldid);

    FoamNextBuffer[oldid] = par;
}

float sampleLogNormal(float mu, float sigma,float u1,float u2,float maxData) {

    u1 = max(1e-6, u1); 
    float muInternal = log(mu) + sigma * sigma;

    float pi = 3.14159265359;
    float z = sqrt(-2.0 * log(u1)) * cos(2.0 * pi * u2);

    float radius = exp(muInternal + sigma * z);
    return min(radius,maxData);
}

StructuredBuffer<half3> GTFoamBuffer;

[numthreads(32, 32, 1)]
void GTAdd(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
           uint3 groupID: SV_GroupID,
         uint groupIndex: SV_GroupIndex) {
    uint pid = groupID.x * 32 * 32 + groupIndex;
    if (pid >= newFoamNum) {
        return;
    }

    uint oldpos;

    GlobalCount.InterlockedAdd(0, 1, oldpos);

    FoamParticle par;

    par.position = GTFoamBuffer[pid];
    // To DO : Sample Radi
    UniformSampleGenerator sg = UniformSampleGenerator(pid, frameCount);
    float rand1 = sampleNext1D(sg);
    float rand2 = sampleNext1D(sg);

    // par.radius = sampleLogNormal(radiusMu, radiusSigma, rand1, rand2, 0.005f);
    par.radius = enlargeFactor*radiusMu;
    par.lifeTime = 0.0001h;
    par.vel = half3(0.0h);

    FoamBuffer[oldpos] = par;
}



[numthreads(32, 32, 1)]
void Add(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
            uint3 groupID: SV_GroupID,
         uint groupIndex: SV_GroupIndex) {
    uint pid = groupID.x * 32 * 32 + groupIndex;

    if (pid >= newFoamNum) {
        return;
    }

    uint oldpos;

    GlobalCount.InterlockedAdd(0, 1, oldpos);

    FoamParticle par;

    par.position = NewFoamBuffer[pid].pos;
    // To DO : Sample Radi
    UniformSampleGenerator sg = UniformSampleGenerator(pid,frameCount);
    float rand1 = sampleNext1D(sg);
    float rand2 = sampleNext1D(sg);

    par.radius = enlargeFactor*sampleLogNormal(radiusMu, radiusSigma, rand1, rand2,0.005f);
    // par.radius = enlargeFactor * radiusMu;
    par.lifeTime = sampleLogNormal(5.0f,0.5f, rand1, rand2,6.0f);
    par.vel = NewFoamBuffer[pid].vel;

    par.vel += float3(sampleNext1D(sg), sampleNext1D(sg), sampleNext1D(sg));

    FoamBuffer[oldpos] = par;
}

[numthreads(32, 32, 1)]
void ShowTexture(uint3 dispatchThreadID: SV_DispatchThreadID, 
            uint3 groupThreadID: SV_GroupThreadID,
                 uint3 groupID: SV_GroupID,
         uint groupIndex: SV_GroupIndex) {
    uint2 coord = dispatchThreadID.xy;

    uint id = coord.y * Width + coord.x;
    float4 velDepth = SurfaceVelDepth[id];
    VelDepthTex[coord] = velDepth;
}
