                                                                          
                                                                            
                                                                           
   
#define _GNU_SOURCE
#ifndef PORT14_PART_B
#define PORT14_PART_B 0
#endif
static int port14Attached(int owner,int reg);
static unsigned echoCount14;
#include "polaczenia-base13.inc"
#include "joint.h"
#include "solver.h"

typedef struct Joint14 {bool saved;b2JointId raw;uint64_t birth,owner;World captured;int slot;} Joint14;
typedef struct Meta14 {uint64_t birth,owner,object;bool hasObject;} Meta14;
typedef struct Copy14 {int kind,count,parent;uint32_t identity[128][8],raw[128][3],view[51];int viewCount;} Copy14;
static Joint14 joints14[256];
static Meta14 metadata14[16][128];
static bool descriptions14[16];
static uint32_t definition14[16][21];
static Copy14 copies14[4];
static uint32_t jcount14[20];
static int reason14,status14,query14,listBody14,listCount14,validReg14;
static b2JointId list14[128];
static bool fixture14,direct14,helperOnly14,compact14;
static int directPrepared14;
static b2StepContext directContext14;
static b2BodyState directStates14[2];
static int phaseVisits14[128][4],phaseOrdinals14[8][4][13];
static bool guardMode14;
static uint32_t guardArgs14[64];
static int pendingKind14=-1;
static uint32_t pendingLow14;
static void fixtureSeed14(const Operation* o);
static int callbackCount14,callbackStatus14,callbackReason14;
static int create14(const Operation*);
static void array14(const uint32_t*,int);
#include "kontrola-14b.h"
static void loadFixtureB14(FILE*,unsigned);
static int mutationArity14(uint32_t k);
static Body physicalBody14[2],operandBody14[2];static bool physicalBodySaved14[2];
static bool port14CanonicalBody(b2BodyId raw,Body* value)
{
    if(!guardMode14)return false;
    for(int i=0;i<2;++i)if(physicalBodySaved14[i]&&b2StoreBodyId(physicalBody14[i].raw)==b2StoreBodyId(raw)){*value=physicalBody14[i];return true;}
    return false;
}

static int port14Attached(int owner,int reg)
{if(b2Body_GetJointCount(bodies[reg].raw)>0){reason14=8;return 1;}return 0;}
static bool worldLive14(World owner)
{
    if(!world_live(&owner)||!b2GetWorldFromId(owner.raw)->inUse)return false;
    for(int i=0;i<WORLDS;++i)if(worlds[i].live&&worlds[i].raw.index1==owner.raw.index1&&hooks12[i].birth==owner.birth)return true;
    return false;
}
static bool port14CanonicalWorld(World* owner)
{
    if(!guardMode14||!b2World_IsValid(owner->raw))return false;
    for(int i=0;i<WORLDS;++i)if(worlds[i].live&&worlds[i].raw.index1==owner->raw.index1&&hooks12[i].birth){owner->birth=hooks12[i].birth;return true;}
    return false;
}

static void echo(int id,uint32_t seq,const Operation* o)
{
    int n=o->code<200?64:o->code==200?2:o->code==201?6:o->code==202?3:o->code==203?
        4+mutationArity14(o->u[3]):
        o->code==206?5:o->code==208?1:o->code==209?4:3;
    ++echoCount14;
    printf("E14 %d %"PRIu32" %"PRIu32" %d",id,seq,o->code,n);
    for(int i=0;i<n;++i)word(o->u[i]);putchar('\n');
}
static void jp14(int source,int w,int slot,int group,int n)
{printf("J14 %d %"PRIu32" %d %d %d %d %d",case9,seq9,source,w,slot,group,n);if(group<8)++jcount14[group];}
static void lp14(int source,int w,int container,int parent,int n)
{printf("L14 %d %"PRIu32" %d %d %d %d %d",case9,seq9,source,w,container,parent,n);++jcount14[8+container];}
static void array14(const uint32_t* u,int n){for(int i=0;i<n;++i)word(u[i]);putchar('\n');}
static int owner14(uint64_t ticket)
{for(int i=0;i<WORLDS;++i)if(worlds[i].saved&&worlds[i].birth==ticket)return i;return -1;}
static int jointStatus14(World owner,Joint14 j)
{
    if(!worldLive14(owner))return STALE;
    if(owner.birth!=j.owner)return FOREIGN;
    b2World* w=b2GetWorldFromId(owner.raw);uint32_t slot=(uint32_t)j.slot;
    if(slot>=(uint32_t)w->jointIdPool.nextIndex)return STALE;
    b2Joint* physical=w->joints.data+slot;
    if(physical->setIndex==B2_NULL_INDEX)return STALE;
    Meta14* m=&metadata14[j.raw.world0][slot];
    if(m->birth!=j.birth)return STALE;
    return OK;
}
static bool live14(Joint14 j){return j.saved&&jointStatus14(j.captured,j)==OK;}
static Joint14 number14(b2JointId raw)
{
    for(int i=0;i<256;++i)if(live14(joints14[i])&&b2StoreJointId(joints14[i].raw)==b2StoreJointId(raw))return joints14[i];
    fail("INPUT_DOMAIN");return (Joint14){0};
}
static void identity14(Joint14 j,uint32_t* u)
{uint32_t a[]={j.raw.index1,j.raw.world0,j.raw.generation,(uint32_t)j.slot,j.birth,j.birth>>32,j.owner,j.owner>>32};memcpy(u,a,sizeof a);}
static void bodyNumber14(b2BodyId raw,uint32_t* u)
{Body b=public_body_number(raw);u[0]=raw.index1-1;u[1]=b.birth;u[2]=b.birth>>32;u[3]=b.owner;u[4]=b.owner>>32;}
static void publicView14(Joint14 j,uint32_t* u)
{
    b2JointId id=j.raw;b2BodyId a=b2Joint_GetBodyA(id),b=b2Joint_GetBodyB(id);b2WorldId w=b2Joint_GetWorld(id);
    u[0]=b2Joint_GetType(id);u[1]=a.index1;u[2]=a.world0;u[3]=a.generation;u[4]=b.index1;u[5]=b.world0;u[6]=b.generation;
    u[7]=w.index1;u[8]=0;u[9]=w.generation;bodyNumber14(a,u+10);bodyNumber14(b,u+15);
    b2Vec2 aa=b2Joint_GetLocalAnchorA(id),bb=b2Joint_GetLocalAnchorB(id),force=b2Joint_GetConstraintForce(id);
    u[20]=to_bits(aa.x);u[21]=to_bits(aa.y);u[22]=to_bits(bb.x);u[23]=to_bits(bb.y);u[24]=u[25]=u[26]=0;
    if(PORT14_PART_B&&u[0]){u[24]=to_bits(b2Joint_GetReferenceAngle(id));if(u[0]==4){b2Vec2 axis=b2Joint_GetLocalAxisA(id);u[25]=to_bits(axis.x);u[26]=to_bits(axis.y);}}
    u[27]=b2Joint_GetCollideConnected(id);Meta14 m=metadata14[id.world0][id.index1-1];u[28]=m.hasObject;u[29]=m.object;u[30]=m.object>>32;
    u[31]=to_bits(force.x);u[32]=to_bits(force.y);u[33]=to_bits(b2Joint_GetConstraintTorque(id));
    u[34]=to_bits(b2Joint_GetLinearSeparation(id));u[35]=to_bits(b2Joint_GetAngularSeparation(id));
    float hz,damping;b2Joint_GetConstraintTuning(id,&hz,&damping);u[36]=to_bits(hz);u[37]=to_bits(damping);
    if(PORT14_PART_B&&u[0]){tailB14(id,u[0],u+38);return;}
    u[38]=to_bits(b2DistanceJoint_GetLength(id));u[39]=b2DistanceJoint_IsSpringEnabled(id);u[40]=to_bits(b2DistanceJoint_GetSpringHertz(id));
    u[41]=to_bits(b2DistanceJoint_GetSpringDampingRatio(id));u[42]=b2DistanceJoint_IsLimitEnabled(id);u[43]=to_bits(b2DistanceJoint_GetMinLength(id));
    u[44]=to_bits(b2DistanceJoint_GetMaxLength(id));u[45]=to_bits(b2DistanceJoint_GetCurrentLength(id));u[46]=b2DistanceJoint_IsMotorEnabled(id);
    u[47]=to_bits(b2DistanceJoint_GetMotorSpeed(id));u[48]=to_bits(b2DistanceJoint_GetMaxMotorForce(id));u[49]=to_bits(b2DistanceJoint_GetMotorForce(id));
}
static bool descriptionValid14(const uint32_t* u)
{
    for(int i=0;i<5;++i)if(!isfinite(from_bits(u[i])))return false;
    if(!(from_bits(u[4])>0))return false;
    for(int i=6;i<=12;++i)if(i!=8&&i!=11&&(!isfinite(from_bits(u[i]))||from_bits(u[i])<0))return false;
    return isfinite(from_bits(u[13]))&&from_bits(u[9])<=from_bits(u[10]);
}
                                                                             
static bool reservation14(uint64_t last,uint64_t required,uint32_t slotNext)
{return required<=UINT64_MAX-last&&slotNext<(uint32_t)INT_MAX;}
static int create14(const Operation* o)
{
    const uint32_t* a=o->u;int wreg=a[1],ar=a[2],br=a[3],dest=a[4],dreg=a[5];bool game=a[0];
    if(!worldLive14(worlds[wreg]))return STALE;
    Body operandA=ar<2&&physicalBodySaved14[ar]?operandBody14[ar]:bodies[ar];
    Body operandB=br<2&&physicalBodySaved14[br]?operandBody14[br]:bodies[br];
    int status=guard(worlds+wreg,&operandA);if(status)return status;status=guard(worlds+wreg,&operandB);if(status)return status;
    b2World* w=b2GetWorldFromId(worlds[wreg].raw);
    if(game&&w->locked){reason14=1;return 7;}
    if(b2StoreBodyId(operandA.raw)==b2StoreBodyId(operandB.raw)){reason14=7;return PARAM;}
    const uint32_t* u=definition14[dreg];
    int type=descriptionTypes14[dreg];
    if(game&&!(PORT14_PART_B&&type?descriptionValidB14(type,u,false):descriptionValid14(u))){if(!reason14)reason14=10;return PARAM;}
    if(!reservation14(lastIssued,1,(uint32_t)w->jointIdPool.nextIndex))return LIMIT;
    if(helperOnly14)return OK;
    int total=0;for(int i=0;i<WORLDS;++i)if(worlds[i].live)total+=b2World_GetCounters(worlds[i].raw).jointCount;
    if(total>=128)fail("INPUT_POPULATION");
    b2DistanceJointDef d=b2DefaultDistanceJointDef();d.bodyIdA=bodies[ar].raw;d.bodyIdB=bodies[br].raw;
    d.localAnchorA=(b2Vec2){from_bits(u[0]),from_bits(u[1])};d.localAnchorB=(b2Vec2){from_bits(u[2]),from_bits(u[3])};
    d.length=from_bits(u[4]);d.enableSpring=u[5];d.hertz=from_bits(u[6]);d.dampingRatio=from_bits(u[7]);d.enableLimit=u[8];
    d.minLength=from_bits(u[9]);d.maxLength=from_bits(u[10]);d.enableMotor=u[11];d.maxMotorForce=from_bits(u[12]);d.motorSpeed=from_bits(u[13]);d.collideConnected=u[14];
    uint64_t birth=++lastIssued;b2JointId raw=PORT14_PART_B&&type?createB14(type,worlds[wreg].raw,bodies[ar].raw,bodies[br].raw,u):b2CreateDistanceJoint(worlds[wreg].raw,&d);
    jointTypes14[dest]=type;
    if(!b2Joint_IsValid(raw)||raw.index1<1||raw.index1>128)fail("INPUT_POPULATION");
    joints14[dest]=(Joint14){true,raw,birth,worlds[wreg].birth,worlds[wreg],raw.index1-1};
    int objectAt=PORT14_PART_B&&type?descriptionCount14(type)-3:15;
    metadata14[raw.world0][raw.index1-1]=(Meta14){birth,worlds[wreg].birth,(uint64_t)u[objectAt+1]|(uint64_t)u[objectAt+2]<<32,u[objectAt]};
    if(u[objectAt])b2Joint_SetUserData(raw,&metadata14[raw.world0][raw.index1-1]);
    return OK;
}
static int mutate14(const Operation* o)
{
    const uint32_t* a=o->u;int k=a[3];bool game=a[0];Joint14 j=joints14[a[2]];
    int status=jointStatus14(worlds[a[1]],j);if(status)return status;b2World* w=b2GetWorldFromId(worlds[a[1]].raw);
    if(game&&w->locked){reason14=1;return 7;}
    int type=w->joints.data[j.slot].type,expected=mutationTypeB14(k);
    if(PORT14_PART_B&&((k==2&&type==0)||(expected>=0&&type!=expected))){if(game){reason14=6;return PARAM;}fail("INPUT_DOMAIN");}
    if(game&&(k==2||k==3)&&w->joints.data[j.slot].type==b2_distanceJoint){reason14=6;return PARAM;}
    if(game){bool good=true;float x=o->f[4],y=o->f[5];
        if(k==0||k==1)good=isfinite(x)&&isfinite(y);
        else if(k==7||k==17)good=isfinite(x)&&isfinite(y)&&x>=0&&y>=0&&(k!=17||x<=y);
        else if(k==16)good=isfinite(x)&&x>0;
        else if(k==19||k==20||k==24)good=isfinite(x)&&x>=0;
        else if(k==23)good=isfinite(x);
        if(PORT14_PART_B&&type&&good)good=mutationValidB14(type,k,x,y);
        if(!good){if(!reason14)reason14=10;return PARAM;}}
    if(helperOnly14)return OK;
    b2JointId id=j.raw;
    if(PORT14_PART_B&&k>=32){mutateB14(id,k,o);return OK;}
    switch(k){
      case 0:b2Joint_SetLocalAnchorA(id,(b2Vec2){o->f[4],o->f[5]});break;
      case 1:b2Joint_SetLocalAnchorB(id,(b2Vec2){o->f[4],o->f[5]});break;
      case 2:b2Joint_SetReferenceAngle(id,o->f[4]);break;
      case 3:b2Joint_SetLocalAxisA(id,(b2Vec2){o->f[4],o->f[5]});break;
      case 4:b2Joint_SetCollideConnected(id,a[4]);break;
      case 5:{Meta14* m=&metadata14[id.world0][id.index1-1];m->hasObject=a[4];m->object=(uint64_t)a[5]|(uint64_t)a[6]<<32;b2Joint_SetUserData(id,a[4]?m:NULL);break;}
      case 6:b2Joint_WakeBodies(id);break;
      case 7:b2Joint_SetConstraintTuning(id,o->f[4],o->f[5]);break;
      case 16:b2DistanceJoint_SetLength(id,o->f[4]);break;
      case 17:b2DistanceJoint_SetLengthRange(id,o->f[4],o->f[5]);break;
      case 18:b2DistanceJoint_EnableSpring(id,a[4]);break;
      case 19:b2DistanceJoint_SetSpringHertz(id,o->f[4]);break;
      case 20:b2DistanceJoint_SetSpringDampingRatio(id,o->f[4]);break;
      case 21:b2DistanceJoint_EnableLimit(id,a[4]);break;
      case 22:b2DistanceJoint_EnableMotor(id,a[4]);break;
      case 23:b2DistanceJoint_SetMotorSpeed(id,o->f[4]);break;
      case 24:b2DistanceJoint_SetMaxMotorForce(id,o->f[4]);break;
    }return OK;
}
void port14JointEvent(b2JointSim* joint,b2StepContext* context,int phase)
{
    if(!OBS||!output9)return;
    int slot=joint->jointId;if(slot<0||slot>=128)fail("INPUT_POPULATION");
    int sub=phase?phaseVisits14[slot][phase]++:0;
    b2Joint* raw=context->world->joints.data+slot;int color=phase?raw->colorIndex:raw->colorIndex==11?11:-1;
    if(direct14&&phase==0)color=-1;
    if(sub>=8||color< -1||color>11)fail("INPUT_POPULATION");
    int ordinal=phaseOrdinals14[sub][phase][color+1]++;
    printf("T14 %d %"PRIu32" %d %d %d %d %d %d %d\n",case9,seq9,sub,phase,color,ordinal,slot,joint->type,phase==2);
    ++jcount14[13];
}
static void commonWords14(b2JointSim* s,uint32_t* u)
{
    uint32_t a[]={s->jointId,s->bodyIdA,s->bodyIdB,s->type,to_bits(s->localOriginAnchorA.x),to_bits(s->localOriginAnchorA.y),
      to_bits(s->localOriginAnchorB.x),to_bits(s->localOriginAnchorB.y),to_bits(s->invMassA),to_bits(s->invMassB),to_bits(s->invIA),to_bits(s->invIB),
      to_bits(s->constraintHertz),to_bits(s->constraintDampingRatio),to_bits(s->constraintSoftness.biasRate),to_bits(s->constraintSoftness.massScale),to_bits(s->constraintSoftness.impulseScale)};
    memcpy(u,a,sizeof a);
}
static void distanceWords14(b2DistanceJoint* d,uint32_t* u)
{
    uint32_t a[]={to_bits(d->length),to_bits(d->hertz),to_bits(d->dampingRatio),to_bits(d->minLength),to_bits(d->maxLength),to_bits(d->maxMotorForce),
      to_bits(d->motorSpeed),to_bits(d->impulse),to_bits(d->lowerImpulse),to_bits(d->upperImpulse),to_bits(d->motorImpulse),d->indexA,d->indexB,
      to_bits(d->anchorA.x),to_bits(d->anchorA.y),to_bits(d->anchorB.x),to_bits(d->anchorB.y),to_bits(d->deltaCenter.x),to_bits(d->deltaCenter.y),
      to_bits(d->distanceSoftness.biasRate),to_bits(d->distanceSoftness.massScale),to_bits(d->distanceSoftness.impulseScale),to_bits(d->axialMass),d->enableSpring,d->enableLimit,d->enableMotor};
    memcpy(u,a,sizeof a);
}
static void stateWords14(b2BodyState* s,uint32_t* u)
{uint32_t a[]={to_bits(s->linearVelocity.x),to_bits(s->linearVelocity.y),to_bits(s->angularVelocity),s->flags,to_bits(s->deltaPosition.x),to_bits(s->deltaPosition.y),to_bits(s->deltaRotation.c),to_bits(s->deltaRotation.s)};memcpy(u,a,sizeof a);}
static void observe14(const Operation* o)
{
    if(compact14){
        int total=0;
        for(int r=0;r<WORLDS;++r)if(worlds[r].live){b2World* w=b2GetWorldFromId(worlds[r].raw);
            total+=b2World_GetCounters(worlds[r].raw).jointCount;
            if(OBS){lp14(0,w->worldId,4,0,4+w->jointIdPool.freeArray.count);
                word(w->jointIdPool.nextIndex);word(w->jointIdPool.freeArray.count);wide(lastIssued);
                for(int i=0;i<w->jointIdPool.freeArray.count;++i)word(w->jointIdPool.freeArray.data[i]);putchar('\n');}}
        jcount14[14]=positive11;jcount14[15]=seq9;jcount14[16]=total;jcount14[19]=fixture14;
        jp14(0,16,0,8,20);array14(jcount14,20);return;
    }
    uint32_t u[51];
    for(int i=0;i<256;++i)if(joints14[i].saved){identity14(joints14[i],u);jp14(0,joints14[i].raw.world0,i,0,8);array14(u,8);}
    if(query14>=0){memset(u,0,sizeof u);if(!status14)publicView14(joints14[query14],u);int n=viewCount14(jointTypes14[query14]);jp14(0,joints14[query14].raw.world0,query14,4,n);array14(u,n);}
    if(validReg14>=0){Joint14 j=joints14[validReg14];jp14(0,j.raw.world0,validReg14,9,2);word(b2Joint_IsValid(j.raw));word(live14(j));putchar('\n');}
    if(listBody14>=0){Body b=bodies[listBody14];lp14(0,b.raw.world0,0,b.raw.index1-1,3*listCount14);for(int i=0;i<listCount14;++i){word(list14[i].index1);word(list14[i].world0);word(list14[i].generation);}putchar('\n');}
    for(int c=0;c<4;++c)if(copies14[c].kind){Copy14* copy=copies14+c;++jcount14[18];
        for(int i=0;i<copy->count;++i){jp14(c+1,16,i,0,8);array14(copy->identity[i],8);}
        if(copy->kind==1){int n=copy->viewCount?copy->viewCount:50;jp14(c+1,16,0,4,n);array14(copy->view,n);}
        else{lp14(c+1,16,0,copy->parent,3*copy->count);for(int i=0;i<copy->count;++i)for(int j=0;j<3;++j)word(copy->raw[i][j]);putchar('\n');}}
    for(int i=0;i<16;++i)if(descriptions14[i]){int type=descriptionTypes14[i],n=descriptionCount14(type);jp14(5,16,i,6,n+1);word(type);array14(definition14[i],n);++jcount14[17];}
    int total=0;for(int r=0;r<WORLDS;++r)if(worlds[r].live)total+=b2World_GetCounters(worlds[r].raw).jointCount;
    jcount14[16]=total;
    if(OBS){
        for(int group=1;group<=3;++group)for(int r=0;r<WORLDS;++r)if(worlds[r].live){b2World* w=b2GetWorldFromId(worlds[r].raw);
            for(int i=0;i<w->jointIdPool.nextIndex;++i){b2Joint* j=w->joints.data+i;if(j->setIndex<0)continue;b2JointSim* s=b2GetJointSim(w,j);
                jp14(0,w->worldId,i,group,group==1?21:group==2?17:payloadCount14(s->type));
                if(group==1){Meta14 m=metadata14[w->worldId][i];word(m.hasObject);wide(m.object);int a[]={j->setIndex,j->colorIndex,j->localIndex,j->edges[0].bodyId,j->edges[0].prevKey,j->edges[0].nextKey,j->edges[1].bodyId,j->edges[1].prevKey,j->edges[1].nextKey,j->jointId,j->islandId,j->islandPrev,j->islandNext};for(int k=0;k<13;++k)word(a[k]);real(j->drawSize);word(j->type);word(j->generation);word(j->isMarked);word(j->collideConnected);putchar('\n');}
                else{if(group==2)commonWords14(s,u);else if(s->type==5)payloadR14(&s->revoluteJoint,u,false);else if(s->type==4)payloadP14(&s->prismaticJoint,u,false);else distanceWords14(&s->distanceJoint,u);array14(u,group==2?17:payloadCount14(s->type));}}}
        for(int r=0;r<WORLDS;++r)if(worlds[r].live){b2World* w=b2GetWorldFromId(worlds[r].raw);
            for(int i=0;i<w->jointIdPool.nextIndex;++i){b2Joint* j=w->joints.data+i;Meta14 m=metadata14[w->worldId][i];jp14(0,w->worldId,i,5,6);word(j->setIndex>=0);word(j->generation);wide(m.birth);wide(m.owner);putchar('\n');}
            for(int i=0;i<w->bodyIdPool.nextIndex;++i){b2Body* b=w->bodies.data+i;if(b->id!=i)continue;jp14(0,w->worldId,i,7,2);word(b->headJointKey);word(b->jointCount);putchar('\n');}
            for(int i=0;i<w->islandIdPool.nextIndex;++i){b2Island* island=w->islands.data+i;if(island->islandId!=i)continue;lp14(0,w->worldId,1,i,island->jointCount);int k=island->headJoint,seen=0;while(k!=-1){if(++seen>128)fail("INPUT_POPULATION");word(k);k=w->joints.data[k].islandNext;}if(seen!=island->jointCount)fail("INPUT_DOMAIN");putchar('\n');}
            for(int i=0;i<w->solverSetIdPool.nextIndex;++i){b2SolverSet* s=w->solverSets.data+i;if(s->setIndex!=i)continue;lp14(0,w->worldId,2,i,s->jointSims.count);for(int k=0;k<s->jointSims.count;++k)word(s->jointSims.data[k].jointId);putchar('\n');}
            for(int i=0;i<12;++i){b2GraphColor* c=w->constraintGraph.colors+i;lp14(0,w->worldId,3,i,c->jointSims.count);for(int k=0;k<c->jointSims.count;++k)word(c->jointSims.data[k].jointId);putchar('\n');}
            lp14(0,w->worldId,4,0,4+w->jointIdPool.freeArray.count);word(w->jointIdPool.nextIndex);word(w->jointIdPool.freeArray.count);wide(lastIssued);for(int i=0;i<w->jointIdPool.freeArray.count;++i)word(w->jointIdPool.freeArray.data[i]);putchar('\n');}
        if(o->code==210&&(!PORT14_PART_B||o->u[0]==0)){jp14(0,0,0,10,16);b2World* w=directContext14.world;
            for(int i=0;i<2;++i){b2BodyState* state=b2GetBodyState(w,w->bodies.data+i);stateWords14(state?state:directStates14,u+8*i);}array14(u,16);}
    }
    if(PORT14_PART_B&&OBS&&mathResultCount14){jp14(0,16,0,12,mathResultCount14);array14(mathResult14,mathResultCount14);}
    jcount14[14]=positive11;jcount14[15]=seq9;jcount14[19]=fixture14;jp14(0,16,0,8,20);array14(jcount14,20);
}
static void execute14(const Operation* o)
{
    const uint32_t* a=o->u;int code=o->code;
    if(code==200){descriptions14[a[1]]=true;memset(definition14[a[1]],0,sizeof definition14[0]);definition14[a[1]][4]=to_bits(1);definition14[a[1]][10]=to_bits(100000);
        if(PORT14_PART_B){descriptionTypes14[a[1]]=a[0];if(a[0]){memset(definition14[a[1]],0,sizeof definition14[0]);if(a[0]==5)definition14[a[1]][15]=to_bits(b2DefaultRevoluteJointDef().drawSize);else definition14[a[1]][4]=to_bits(b2DefaultPrismaticJointDef().localAxisA.x);}}}
    else if(code==202)definition14[a[0]][a[1]]=a[2];
    else if(code==201)status14=create14(o);
    else if(code==203)status14=mutate14(o);
    else if(code==204||code==205||code==207||code==212){int reg=code==207?a[1]:a[2],owner=code==207?a[0]:a[1];Joint14 j=joints14[reg];
        status14=jointStatus14(worlds[owner],j);bool game=code==207||a[0];
        if(code==212){if(!game)status14=OK;validReg14=reg;}
        else{if(!status14&&game&&b2GetWorldFromId(worlds[owner].raw)->locked){status14=7;reason14=1;}
            if(code==204)query14=reg;
            if(!status14&&code==205&&!helperOnly14)b2DestroyJoint(j.raw);
            if(!status14&&code==207&&!helperOnly14){Copy14* c=copies14+a[2];memset(c,0,sizeof *c);c->kind=c->count=1;identity14(j,c->identity[0]);c->viewCount=viewCount14(jointTypes14[reg]);publicView14(j,c->view);}}}
    else if(code==206){status14=guard(worlds+a[1],bodies+a[2]);listBody14=a[2];listCount14=0;
        if(!status14){int cap=a[0]?128:a[3];listCount14=b2Body_GetJoints(bodies[a[2]].raw,list14,cap);
            if(a[0]){Copy14* c=copies14+a[4];memset(c,0,sizeof *c);c->kind=2;c->parent=bodies[a[2]].raw.index1-1;c->count=listCount14;for(int i=0;i<listCount14;++i){identity14(number14(list14[i]),c->identity[i]);memcpy(c->raw[i],c->identity[i],sizeof c->raw[i]);}}}}
    else if(code==209){Copy14* c=copies14+a[0];uint32_t* target=a[1]==4?c->view+a[2]:&c->identity[a[2]/8][a[2]%8];if(*target==a[3])fail("INPUT_DOMAIN");*target=a[3];}
    else if(code==210&&PORT14_PART_B&&a[0]){fixture14=true;mathResultCount14=a[0]==1?1:2;
        if(a[0]==1)mathResult14[0]=to_bits(b2UnwindAngle(from_bits(mathInput14[0])));
        else{b2Mat22 m={{from_bits(mathInput14[0]),from_bits(mathInput14[1])},{from_bits(mathInput14[2]),from_bits(mathInput14[3])}};b2Vec2 v=b2Solve22(m,(b2Vec2){from_bits(mathInput14[4]),from_bits(mathInput14[5])});mathResult14[0]=to_bits(v.x);mathResult14[1]=to_bits(v.y);}}
    else if(code==210){fixture14=true;b2World* w=b2GetWorldFromId(worlds[0].raw);b2JointSim* s=b2GetJointSim(w,w->joints.data);
        if(a[1]==0){b2PrepareJoint(s,&directContext14);directPrepared14=1;}
        else if(a[1]==1)b2WarmStartJoint(s,&directContext14);else b2SolveJoint(s,&directContext14,a[2]);}
    else if(code==211){fixture14=true;int f=a[0];Joint14* j=joints14;b2World* w=worlds[0].live?b2GetWorldFromId(worlds[0].raw):NULL;
        if(f==0)lastIssued=(uint64_t)a[1]|(uint64_t)a[2]<<32;
        else if(f==8){for(int i=0;i<w->jointIdPool.nextIndex;++i)if(w->joints.data[i].setIndex>=0){b2JointSim* s=b2GetJointSim(w,w->joints.data+i);if(PORT14_PART_B&&s->type){uint32_t u[34];if(s->type==5){payloadR14(&s->revoluteJoint,u,false);for(int k=0;k<6;++k)u[k]=to_bits(k+1);payloadR14(&s->revoluteJoint,u,true);}else{payloadP14(&s->prismaticJoint,u,false);for(int k=0;k<6;++k)u[k+2]=to_bits(k+1);payloadP14(&s->prismaticJoint,u,true);}}else{b2DistanceJoint* d=&s->distanceJoint;d->impulse=1;d->lowerImpulse=2;d->upperImpulse=3;d->motorImpulse=4;}}}
        else if(f==17){b2JointId raw={(int32_t)a[2],(uint16_t)(a[1]>>16),(uint16_t)a[1]},back=b2LoadJointId(b2StoreJointId(raw));jp14(0,16,17,11,4);word(0);word(raw.index1==back.index1&&raw.world0==back.world0&&raw.generation==back.generation);wide(b2StoreJointId(raw));putchar('\n');}
        else if(f==18){b2WorldId got=b2Joint_GetWorld(j->raw);jp14(0,16,18,11,4);word(0);word(1);word(got.index1);word(got.generation);putchar('\n');}
        else if(guardMode14)fixtureSeed14(o);else fail("INPUT_PROFILE");}
    echo(case9,seq9,o);
}
static void port14PreSolveRoute(void)
{
    if(!guardMode14)fail("INPUT_PROFILE");
    uint32_t* a=guardArgs14;Operation o={.code=a[2]};int previousReason=reason14;reason14=0;helperOnly14=true;
    if(o.code==201){uint32_t args[]={1,a[0],a[4],a[5],1,a[6]};memcpy(o.u,args,sizeof args);callbackStatus14=create14(&o);}
    else if(o.code==203){o.u[0]=1;o.u[1]=a[0];o.u[2]=a[1];o.u[3]=a[3];int n=mutationArity14(a[3]);if(n<0)fail("INPUT_ENUM");
        for(int i=0;i<n;++i){o.u[4+i]=a[4+i];o.f[4+i]=from_bits(a[4+i]);}
        b2World* w=b2GetWorldFromId(worlds[a[0]].raw);b2Joint* joint=w->joints.data+joints14[a[1]].slot;int oldType=joint->type;
        if(a[3]==2)joint->type=b2_revoluteJoint;else if(a[3]==3)joint->type=b2_prismaticJoint;
        callbackStatus14=mutate14(&o);joint->type=oldType;
    }else if(o.code==204||o.code==205||o.code==207){callbackStatus14=jointStatus14(worlds[a[0]],joints14[a[1]]);
        if(!callbackStatus14&&b2GetWorldFromId(worlds[a[0]].raw)->locked){callbackStatus14=7;reason14=1;}}
    else fail("INPUT_OPCODE");
    helperOnly14=false;callbackReason14=reason14;reason14=previousReason;++callbackCount14;
    printf("A14 %d %"PRIu32" %d %d\n",case9,seq9,callbackStatus14,callbackReason14);
}
static int mutationArity14(uint32_t k)
{if(PORT14_PART_B&&(k==37||k==53))return 2;if(PORT14_PART_B&&(k>=32&&k<=40||k>=48&&k<=56))return 1;if(k==0||k==1||k==3||k==7||k==17)return 2;if(k==5)return 3;if(k==6)return 0;if(k==2||k==4||k>=16&&k<=24)return 1;return -1;}
typedef struct Input14 {const char* prefix;size_t offset,size;FILE* tail;} Input14;
static ssize_t input14Read(void* cookie,char* buffer,size_t size)
{
    Input14* input=cookie;if(!size)return 0;
    if(input->offset<input->size){*buffer=input->prefix[input->offset++];return 1;}
    int c=fgetc(input->tail);if(c==EOF)return ferror(input->tail)?-1:0;*buffer=(char)c;return 1;
}
static Operation read14(FILE* input,uint32_t seq)
{
    char* line=row(input);char saved[2052];snprintf(saved,sizeof saved,"%s\n",line);char* p=line;
    if(strncmp(p,"O ",2))fail("INPUT_TAG");p+=2;uint32_t actual=decimal13(&p);space(&p);uint32_t code=decimal13(&p);
    if(actual!=seq)fail("INPUT_SEQ");
    if(code<200){if(!(code<=64&&used_legacy12[code]||code>=80&&code<=92||code>=100&&code<=109||code==120))fail("INPUT_OPCODE");
        if(PORT14_PART_B&&direct14)fail("INPUT_PROFILE");
        if(code>=41&&code<=45||code>=51&&code<=53)fail("INPUT_PHASE");
        Input14 replay={saved,0,strlen(saved),input};cookie_io_functions_t io={.read=input14Read};
        FILE* f=fopencookie(&replay,"r",io);if(!f)fail("INPUT_DOMAIN");setvbuf(f,NULL,_IONBF,0);
        int profile=profile12;if(code==64){if(!direct14)fail("INPUT_PROFILE");profile12=15;}
        Operation o=read13(f,seq);profile12=profile;fclose(f);return o;}
    if(code>212)fail("INPUT_OPCODE");space(&p);uint32_t n=decimal13(&p);Operation o={.code=code};
    if(n>64)fail("INPUT_ARITY");arity13(line,4+n,"INPUT_ARITY");for(uint32_t i=0;i<n;++i){space(&p);o.u[i]=hex_word(&p);o.f[i]=from_bits(o.u[i]);}if(*p)fail("INPUT_ARITY");
    if(code==203&&n>=4&&mutationArity14(o.u[3])<0)fail("INPUT_ENUM");
    uint32_t* a=o.u;int needed=code==200?2:code==201?6:code==202?3:code==203?4+mutationArity14(a[3]):code==206?5:code==208?1:code==209?4:3;
    if(n!=(uint32_t)needed)fail("INPUT_ARITY");if(code==203&&mutationArity14(a[3])<0)fail("INPUT_ENUM");
    if((code==201||code>=203&&code<=206||code==212)&&a[0]>1)fail("INPUT_MODE");
    if(code==200){if(a[0]&&(!PORT14_PART_B||a[0]!=4&&a[0]!=5))fail("INPUT_ENUM");if(a[1]>=16)fail("INPUT_REGISTER_RANGE");}
    else if(code==202){if(a[0]>=16)fail("INPUT_REGISTER_RANGE");if(!descriptions14[a[0]])fail("INPUT_REGISTER_UNINITIALIZED");int type=descriptionTypes14[a[0]];if(a[1]>=(uint32_t)descriptionCount14(type))fail("INPUT_ENUM");if((type?descriptionBoolB14(type,a[1]):a[1]==5||a[1]==8||a[1]==11||a[1]==14||a[1]==15)&&a[2]>1)fail("INPUT_BOOL");}
    else if(code==208||code==209){if(a[0]>=4)fail("INPUT_REGISTER_RANGE");Copy14* c=copies14+a[0];if(!c->kind)fail("INPUT_COPY");
        if(code==209){if(a[1]!=0&&a[1]!=4||a[1]==4&&c->kind!=1||a[2]>=(uint32_t)(a[1]==4?(c->viewCount?c->viewCount:50):8*c->count))fail("INPUT_COPY");}}
    else if(code==210){if(!direct14||!joints14[0].saved)fail("INPUT_PROFILE");if(a[0]&&(!PORT14_PART_B||a[0]!=(uint32_t)mathId14)||a[1]>2)fail("INPUT_ENUM");if(PORT14_PART_B&&a[0]&&(a[1]||a[2]))fail("INPUT_PHASE");if(PORT14_PART_B&&a[0]&&!directPrepared14)fail("INPUT_PHASE");if(a[2]>1)fail("INPUT_BOOL");if(a[1]<2&&a[2])fail("INPUT_UNUSED");if(!directPrepared14&&a[1])fail("INPUT_PHASE");}
    else if(code==211){if(a[0]>18)fail("INPUT_ENUM");if(!guardMode14&&(!direct14||a[0]!=8&&a[0]!=17&&a[0]!=18))fail("INPUT_PROFILE");}
    else{int wr=code==207?a[0]:a[1];if(wr>=16)fail("INPUT_REGISTER_RANGE");if(!worlds[wr].saved)fail("INPUT_REGISTER_UNINITIALIZED");
        if(code==201){if(a[2]>=256||a[3]>=256||a[4]>=256||a[5]>=16)fail("INPUT_REGISTER_RANGE");if(direct14&&case9>=65)fail("INPUT_PROFILE");if(!bodies[a[2]].saved||!bodies[a[3]].saved||!descriptions14[a[5]])fail("INPUT_REGISTER_UNINITIALIZED");if(live14(joints14[a[4]]))fail("INPUT_REGISTER_COLLISION");
            const uint32_t* u=definition14[a[5]];
            int type=descriptionTypes14[a[5]],objectAt=type?descriptionCount14(type)-3:15;
            if(!u[objectAt]&&(u[objectAt+1]||u[objectAt+2]))fail("INPUT_UNUSED");
            if(PORT14_PART_B&&type&&!a[0]&&!descriptionValidB14(type,u,true))fail("INPUT_DOMAIN");
            if(!a[0]){if(guard(worlds+wr,bodies+a[2])||guard(worlds+wr,bodies+a[3])||b2StoreBodyId(bodies[a[2]].raw)==b2StoreBodyId(bodies[a[3]].raw))fail("INPUT_DOMAIN");
                if(!type){for(int i=0;i<14;++i)if(i!=5&&i!=8&&i!=11&&!isfinite(from_bits(u[i])))fail("INPUT_DOMAIN");if(!(from_bits(u[4])>0))fail("INPUT_DOMAIN");}}}
        else if(code==206){if(a[2]>=256||a[4]>=4)fail("INPUT_REGISTER_RANGE");if(!bodies[a[2]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(a[3]>128)fail("INPUT_DOMAIN");if(a[0]&&a[3]||!a[0]&&a[4])fail("INPUT_UNUSED");}
        else{int jr=code==207?a[1]:a[2];if(jr>=256||code==207&&a[2]>=4)fail("INPUT_REGISTER_RANGE");if(!joints14[jr].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(code!=207&&!a[0]&&code!=212&&jointStatus14(worlds[wr],joints14[jr]))fail("INPUT_DOMAIN");}
        if(code==203){int k=a[3];if((k==4||k==18||k==21||k==22)&&a[4]>1||k==5&&a[4]>1||PORT14_PART_B&&mutationBoolB14(k)&&a[4]>1)fail("INPUT_BOOL");if(k==5&&!a[4]&&(a[5]||a[6]))fail("INPUT_UNUSED");}}
    if(code==203&&PORT14_PART_B&&!a[0]){int type=jointTypes14[a[2]],k=a[3],expected=mutationTypeB14(k);if((k==2&&type==0)||(expected>=0&&expected!=type))fail("INPUT_DOMAIN");if(k==37&&!limitsR14(o.f[4],o.f[5])||k==53&&o.f[4]>o.f[5]||k==3&&!axis14(o.f[4],o.f[5]))fail("INPUT_DOMAIN");}
    if(code==203&&!a[0]&&!(PORT14_PART_B&&mutationBoolB14(a[3]))&&a[3]!=4&&a[3]!=5&&a[3]!=6&&a[3]!=18&&a[3]!=21&&a[3]!=22)
        for(int i=4;i<needed;++i)if(!isfinite(o.f[i]))fail("INPUT_DOMAIN");
    if(direct14&&(PORT14_PART_B||case9>=65)&&code!=210)fail("INPUT_PROFILE");
    return o;
}
typedef struct Output14 {char* text;int rank,ordinal;} Output14;
static int order14(const void* av,const void* bv)
{const Output14* a=av;const Output14* b=bv;return a->rank!=b->rank?a->rank-b->rank:a->ordinal-b->ordinal;}
static void commit14(void)
{
    if(fclose(output9))fail("INPUT_DOMAIN");output9=NULL;if(outputSize9>13833216u)fail("INPUT_POPULATION");
    int n=0,cap=256;Output14* rows=malloc(cap*sizeof *rows);if(!rows)fail("INPUT_DOMAIN");
    for(char* p=outputBytes9;p&&*p;){char* e=strchr(p,'\n');if(!e)fail("INPUT_DOMAIN");*e=0;char tag[32];sscanf(p,"%31s",tag);int rank;
        if(!strcmp(tag,"TASK")){p=e+1;continue;}
        if(!strcmp(tag,"E14"))rank=0;
        else if(!strcmp(tag,"A14"))rank=200;
        else if(!strcmp(tag,"T14"))rank=800;
        else if(!strcmp(tag,"J14")||!strcmp(tag,"L14")){int id,seq,source,w,slot,group,count;if(sscanf(p,"%*s %d %d %d %d %d %d %d",&id,&seq,&source,&w,&slot,&group,&count)!=7)fail("INPUT_DOMAIN");
            if(tag[0]=='L')rank=source?700:slot==0?600:1100+slot;
            else rank=group==8?1200:source?700:group==0?400:group==4||group==9||group==11||group==12?500:1000+group;
        }else{int old=rank10(tag);if(old<0)fail("INPUT_DOMAIN");
            bool counter=!strcmp(tag,"I8")||!strcmp(tag,"I9")||!strcmp(tag,"I10")||!strcmp(tag,"I11")||!strcmp(tag,"I12")||!strcmp(tag,"IP12")||!strcmp(tag,"I13")||tag[0]=='Z';
            rank=counter?1300+old:old<rank10("X")?300+old:900+old;
            if(!strcmp(tag,"R")||!strcmp(tag,"AP12")||!strcmp(tag,"HT12")||!strcmp(tag,"HR12")||!strcmp(tag,"A13")||!strcmp(tag,"EP13B")||!strcmp(tag,"EU13B"))rank=100+old;}
        if(n==cap){cap*=2;rows=realloc(rows,cap*sizeof *rows);if(!rows)fail("INPUT_DOMAIN");}rows[n]=(Output14){p,rank,n};++n;p=e+1;}
    qsort(rows,n,sizeof *rows,order14);for(int i=0;i<n;++i)output_line10(rows[i].text);
    free(rows);free(outputBytes9);outputBytes9=NULL;outputSize9=0;
}
static void resetOperation14(int id,uint32_t seq)
{
    mathResultCount14=0;echoCount14=0;reset_operation9(id,seq,0);traceCount11=0;status12=reason12=reason13=status13=reason14=status14=0;vectorKind12=-1;vector12=b2Vec2_zero;private12=0;hasPreparedGeometry12=false;
    traceCount12=callbackAPCount12=0;readShape12=copyMutation12=-1;query13=parent13=mutation13=-1;query14=listBody14=validReg14=-1;listCount14=0;
    memset(finals11,0,sizeof finals11);memset(count11,0,sizeof count11);memset(public11,0,sizeof public11);memset(counts10,0,sizeof counts10);memset(hitsCount10,0,sizeof hitsCount10);
    memset(counts12,0,sizeof counts12);memset(count13,0,sizeof count13);memset(privateCount13,0,sizeof privateCount13);memset(jcount14,0,sizeof jcount14);memset(phaseVisits14,0,sizeof phaseVisits14);memset(phaseOrdinals14,0,sizeof phaseOrdinals14);
    begin_output9();reset_extra10();
}
static void finishOperation14(const Operation* o)
{
    printf("A14 %d %"PRIu32" %d %d\n",case9,seq9,status14,reason14);
    if(o->code<200){++count13[0];prefix13("A13",0,0,0,0);word(status13);word(reason13);putchar('\n');}
    hits10(o);public_sleep11(o);observe12();world10_dump();private_sleep11();observe13(o);observe14(o);
    if(OBS){prefix12("I10",0,0,0);for(int j=0;j<6;++j)word(counts10[j]);putchar('\n');prefix12("I11",0,0,0);for(int j=0;j<11;++j)word(count11[j]);putchar('\n');}
    prefix12("Z10",0,0,0);for(int j=0;j<4;++j)word(hitsCount10[j]);word(completed10);putchar('\n');prefix12("Z11",0,0,0);word(public11[0]);word(public11[1]);word(positive11);putchar('\n');
    prefix12("I12",0,0,0);for(int j=0;j<11;++j)word(counts12[j]);putchar('\n');if(OBS){prefix12("IP12",0,0,0);word(private12);putchar('\n');}prefix12("Z12",0,0,0);word(positive11);word(seq9);putchar('\n');commit14();
}
static void run14(FILE* input,int id,uint32_t seq)
{
    resetOperation14(id,seq);Operation o=read14(input,seq);opcode9=o.code;fixture11=fixture14;population9(&o);
    if(o.code<200){execute13(&o);aggregate13();status14=status13;if(reason14!=8)reason14=reason13;}
    else{execute14(&o);population_after9();dump(case9,seq9,0,0,0,-1);}
    fixture11=fixture14;finishOperation14(&o);
}
static void loadFixture14(FILE* input,unsigned id)
{
    if(PORT14_PART_B){loadFixtureB14(input,id);return;}
    uint32_t f[5][26]={{0}};const int arities[]={5,17,26,20,16};
    for(int group=0;group<5;++group){char* p=row(input);if(strncmp(p,"F14 ",4))fail("INPUT_TAG");arity13(p,5+arities[group],"INPUT_ARITY");p+=4;
        uint32_t actual=decimal13(&p);space(&p);uint32_t fixture=decimal13(&p);space(&p);uint32_t gotgroup=decimal13(&p);space(&p);uint32_t n=decimal13(&p);
        if(actual!=id)fail("INPUT_ID");if(fixture||gotgroup!=(uint32_t)group)fail("INPUT_PHASE");if(n!=(uint32_t)arities[group])fail("INPUT_ARITY");
        for(unsigned i=0;i<n;++i){space(&p);f[group][i]=hex_word(&p);}if(*p)fail("INPUT_ARITY");}
    if(f[0][2]>1)fail("INPUT_BOOL");if((f[0][3]!=0&&f[0][3]!=2)||(f[0][4]!=0&&f[0][4]!=2)||f[0][3]+f[0][4]==0)fail("INPUT_ENUM");
    if(!isfinite(from_bits(f[0][0]))||!isfinite(from_bits(f[0][1]))||from_bits(f[0][0])<=0||from_bits(f[0][1])<=0)fail("INPUT_DOMAIN");
    if(f[1][0]||f[1][1]||f[1][2]!=1||f[1][3])fail("INPUT_DOMAIN");
    for(int g=1;g<=4;++g)for(int i=0;i<arities[g];++i){bool integer=g==1&&i<4||g==2&&(i==11||i==12||i>=23)||g==4&&(i==3||i==11);if(!integer&&!isfinite(from_bits(f[g][i])))fail("INPUT_DOMAIN");}
    for(int i=23;i<26;++i)if(f[2][i]>1)fail("INPUT_BOOL");
    for(int b=0;b<2;++b){int at=b*10;float c=from_bits(f[3][at+2]),s=from_bits(f[3][at+3]);if(!b2IsNormalizedRot((b2Rot){c,s}))fail("INPUT_ROTATION");}
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;wd.workerCount=1;wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
    if(create_world(0,wd))fail("INPUT_DOMAIN");sync_hooks12();
    for(int i=0;i<2;++i){b2BodyDef bd=b2DefaultBodyDef();bd.type=f[0][3+i]==0?b2_staticBody:b2_dynamicBody;if(create_body(i,0,bd))fail("INPUT_DOMAIN");}
    descriptions14[0]=true;memset(definition14[0],0,sizeof definition14[0]);definition14[0][4]=to_bits(1);definition14[0][10]=to_bits(100000);
    Operation create={.code=201,.u={0,0,0,1,0,0}};if(create14(&create))fail("INPUT_DOMAIN");descriptions14[0]=false;
    b2World* w=b2GetWorldFromId(worlds[0].raw);b2JointSim* s=b2GetJointSim(w,w->joints.data);uint32_t* a=f[1];
    s->localOriginAnchorA=(b2Vec2){from_bits(a[4]),from_bits(a[5])};s->localOriginAnchorB=(b2Vec2){from_bits(a[6]),from_bits(a[7])};
    s->invMassA=from_bits(a[8]);s->invMassB=from_bits(a[9]);s->invIA=from_bits(a[10]);s->invIB=from_bits(a[11]);s->constraintHertz=from_bits(a[12]);s->constraintDampingRatio=from_bits(a[13]);
    s->constraintSoftness=(b2Softness){from_bits(a[14]),from_bits(a[15]),from_bits(a[16])};a=f[2];b2DistanceJoint* d=&s->distanceJoint;
    d->length=from_bits(a[0]);d->hertz=from_bits(a[1]);d->dampingRatio=from_bits(a[2]);d->minLength=from_bits(a[3]);d->maxLength=from_bits(a[4]);d->maxMotorForce=from_bits(a[5]);d->motorSpeed=from_bits(a[6]);
    d->impulse=from_bits(a[7]);d->lowerImpulse=from_bits(a[8]);d->upperImpulse=from_bits(a[9]);d->motorImpulse=from_bits(a[10]);d->indexA=(int32_t)a[11];d->indexB=(int32_t)a[12];
    d->anchorA=(b2Vec2){from_bits(a[13]),from_bits(a[14])};d->anchorB=(b2Vec2){from_bits(a[15]),from_bits(a[16])};d->deltaCenter=(b2Vec2){from_bits(a[17]),from_bits(a[18])};
    d->distanceSoftness=(b2Softness){from_bits(a[19]),from_bits(a[20]),from_bits(a[21])};d->axialMass=from_bits(a[22]);d->enableSpring=a[23];d->enableLimit=a[24];d->enableMotor=a[25];
    memset(&directContext14,0,sizeof directContext14);directContext14.world=w;directContext14.graph=&w->constraintGraph;directContext14.h=from_bits(f[0][0]);directContext14.inv_h=from_bits(f[0][1]);directContext14.enableWarmStarting=f[0][2];
    directContext14.states=w->solverSets.data[2].bodyStates.data;directContext14.sims=w->solverSets.data[2].bodySims.data;
    directStates14[0]=(b2BodyState){.deltaRotation=b2Rot_identity};
    for(int i=0;i<2;++i){a=f[3]+10*i;b2BodySim* sim=b2GetBodySim(w,w->bodies.data+i);
        sim->transform=(b2Transform){{from_bits(a[0]),from_bits(a[1])},{from_bits(a[2]),from_bits(a[3])}};sim->localCenter=(b2Vec2){from_bits(a[4]),from_bits(a[5])};sim->center=(b2Vec2){from_bits(a[6]),from_bits(a[7])};sim->invMass=from_bits(a[8]);sim->invInertia=from_bits(a[9]);
        a=f[4]+8*i;b2BodyState state={{from_bits(a[0]),from_bits(a[1])},from_bits(a[2]),a[3],{from_bits(a[4]),from_bits(a[5])},{from_bits(a[6]),from_bits(a[7])}};
        if(f[0][3+i]==2)*b2GetBodyState(w,w->bodies.data+i)=state;}
    for(int group=0;group<5;++group){printf("EF14 %u 0 %d %d",id,group,arities[group]);array14(f[group],arities[group]);}
}
static void resetCase14(int id)
{
    reset13(id);memset(joints14,0,sizeof joints14);memset(metadata14,0,sizeof metadata14);memset(copies14,0,sizeof copies14);memset(descriptions14,0,sizeof descriptions14);
    memset(descriptionTypes14,0,sizeof descriptionTypes14);memset(jointTypes14,0,sizeof jointTypes14);mathId14=mathCount14=mathResultCount14=0;
    fixture14=false;fixture11=false;compact14=false;directPrepared14=0;pendingKind14=-1;
    callbackCount14=0;callbackStatus14=-1;callbackReason14=0;
    memset(physicalBodySaved14,0,sizeof physicalBodySaved14);
}
#include "kontrola-polaczenia-guard.h"
int main(int argc,char** argv)
{
    if(argc>2)fail("INPUT_DOMAIN");FILE* input=argc==2?fopen(argv[1],"rb"):stdin;if(!input)fail("INPUT_DOMAIN");
    char* p=row(input);char profile[16];unsigned n;int consumed=0;
    if(strncmp(p,"PORT14 ",7))fail("INPUT_TAG");arity13(p,4,"INPUT_ARITY");
    if(strncmp(p,PORT14_PART_B?"PORT14 B ":"PORT14 A ",9))fail("INPUT_PROFILE");p+=9;char* end=strchr(p,' ');if(!end)fail("INPUT_ARITY");size_t len=end-p;if(len>=sizeof profile)fail("INPUT_PROFILE");memcpy(profile,p,len);profile[len]=0;p=end+1;n=decimal13(&p);if(*p)fail("INPUT_ARITY");
    bool public=!strcmp(profile,"PUBLIC");direct14=!strcmp(profile,"DIRECT");if(!public&&!direct14&&strcmp(profile,"GUARD"))fail("INPUT_PROFILE");
    if(!n||n>(public?96:direct14?128:PORT14_PART_B?221:156))fail("INPUT_N");
    if(!public&&!direct14){int code=guardMain14(input,n);if(input!=stdin)fclose(input);free_tokens();free(trace12);free(callbackAP12);return code;}
    profile11=profile12=14;printf("PORT14 %c %s %u\n",PORT14_PART_B?'B':'A',profile,n);
    for(unsigned id=1;id<=n;++id){p=row(input);if(strncmp(p,"C ",2))fail("INPUT_TAG");arity13(p,3,"INPUT_ARITY");p+=2;uint32_t got=decimal13(&p);space(&p);uint32_t count=decimal13(&p);if(*p)fail("INPUT_ARITY");if(got!=id)fail("INPUT_ID");if(!count||count>(public?id<=(PORT14_PART_B?24:48)?128:PORT14_PART_B&&id>=49&&id<=54?2048:1328:32))fail("INPUT_OPCOUNT");
        resetCase14(id);
        printf("CASE %u %"PRIu32"\n",id,count);
        if(direct14&&(PORT14_PART_B||id>=65))loadFixture14(input,id);
        for(uint32_t seq=1;seq<=count;++seq)run14(input,id,seq);
        printf("ENDCASE %u\n",id);for(int r=0;r<WORLDS;++r)if(worlds[r].live)destroy_world(r);
    }
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input))fail("INPUT_DOMAIN");printf("END %u\n",n);if(input!=stdin)fclose(input);free_tokens();free(trace12);free(callbackAP12);return ferror(stdout)||fflush(stdout)?2:0;
}
