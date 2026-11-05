                                                                                   
#include "kontrola-solver10.h"
#include "body.h"
#include "world.h"
#include "constraint_graph.h"
#include <string.h>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-value"
#include "solver.c"
#pragma GCC diagnostic pop
void port10Integrate(b2StepContext* context,bool positions,int count)
{
    if(positions)b2IntegratePositionsTask(0,count,context);
    else b2IntegrateVelocitiesTask(0,count,context);
}
static int phase10(b2SolverStageType type)
{
    switch(type){
        case b2_stagePrepareJoints:case b2_stagePrepareContacts:return 0;
        case b2_stageIntegrateVelocities:return 1;
        case b2_stageWarmStart:return 2;
        case b2_stageSolve:return 3;
        case b2_stageIntegratePositions:return 4;
        case b2_stageRelax:return 5;
        case b2_stageRestitution:return 6;
        case b2_stageStoreImpulses:return 7;
    }
    return -1;
}
void port10Trace(b2StepContext* c,int sub,int phase,bool packets)
{
    uint32_t x[]={port10Bits(c->dt),port10Bits(c->inv_dt),port10Bits(c->h),port10Bits(c->inv_h),
        (uint32_t)c->subStepCount,port10Bits(c->contactSoftness.biasRate),port10Bits(c->contactSoftness.massScale),
        port10Bits(c->contactSoftness.impulseScale),port10Bits(c->staticSoftness.biasRate),
        port10Bits(c->staticSoftness.massScale),port10Bits(c->staticSoftness.impulseScale),
        port10Bits(c->restitutionThreshold),port10Bits(c->maxLinearVelocity),(uint32_t)c->enableWarmStarting};
    port10Record("CX10",NULL,0,x,14);
    int ordinal=0;
    for(int stage=0;stage<c->stageCount;++stage){b2SolverStage* s=c->stages+stage;
        if(sub>=0&&phase10(s->type)!=phase)continue;
        for(int j=0;j<s->blockCount;++j){b2SolverBlock* b=s->blocks+j;
            int p[]={sub<0?0:sub,phase,ordinal++};
            uint32_t w[]={(uint32_t)b->blockType,(uint32_t)s->colorIndex,(uint32_t)b->startIndex,(uint32_t)b->count};
            port10Record("SB10",p,3,w,4);}}
    port10Constraints(c,sub<0?0:sub,phase,packets);
    b2SolverSet* set=c->world->solverSets.data+b2_awakeSet;
    for(int id=0;id<c->world->bodyIdPool.nextIndex;++id){
        for(int j=0;j<set->bodySims.count;++j){b2BodySim* sim=set->bodySims.data+j;if(sim->bodyId!=id)continue;
            b2BodyState* s=c->states+j;int p[]={sub<0?0:sub,phase,id};
            uint32_t w[]={port10Bits(s->linearVelocity.x),port10Bits(s->linearVelocity.y),port10Bits(s->angularVelocity),
                port10Bits(s->deltaPosition.x),port10Bits(s->deltaPosition.y),port10Bits(s->deltaRotation.c),port10Bits(s->deltaRotation.s)};
            port10Record("BV10",p,3,w,7);}}
}
void port10CaptureSolver(b2TaskCallback* task,void* context)
{
    if(!port10Observe()||task!=b2SolverTask)return;
    b2WorkerContext* worker=context;
    port10Trace(worker->context,-1,7,true);
}
