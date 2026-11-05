                                                                          
static int descriptionTypes14[16],jointTypes14[256];
static int mathId14,mathCount14,mathResultCount14;
static uint32_t mathInput14[6],mathResult14[2];
static int descriptionCount14(int type){return type==5?20:type==4?21:18;}
static int payloadCount14(int type){return type==5?30:type==4?34:26;}
static int viewCount14(int type){return type==4?51:50;}
static bool angle14(float x){return -B2_PI<=x&&x<=B2_PI;}
static bool axis14(float x,float y){return b2IsNormalized((b2Vec2){x,y});}
static bool limitsR14(float x,float y){return -.99f*B2_PI<=x&&y<=.99f*B2_PI&&x<=y;}
static bool descriptionValidB14(int type,const uint32_t* u,bool raw)
{
    for(int i=0;i<4;++i)if(!isfinite(from_bits(u[i])))return false;
    int ref=type==5?4:6,target=ref+1,hz=type==5?7:9,max=type==5?13:15,lower=type==5?10:12;
    if(!isfinite(from_bits(u[ref]))||!isfinite(from_bits(u[target])))return false;
    if(!raw&&(!angle14(from_bits(u[ref]))||(type==5&&!angle14(from_bits(u[target])))))return false;
    if(type==4){float x=from_bits(u[4]),y=from_bits(u[5]);
        if(raw){float norm=x*x+y*y;if(!isfinite(norm)||!(norm>0))return false;}
        else if(!axis14(x,y)){reason14=9;return false;}}
    for(int i=0;i<2;++i)if(!isfinite(from_bits(u[hz+i]))||(!raw&&from_bits(u[hz+i])<0))return false;
    if(!isfinite(from_bits(u[max]))||(!raw&&from_bits(u[max])<0)||!isfinite(from_bits(u[max+1])))return false;
    float lo=from_bits(u[lower]),hi=from_bits(u[lower+1]);
    if(type==5){if(!limitsR14(lo,hi)||!isfinite(from_bits(u[15])))return false;}
    else if(!isfinite(lo)||!isfinite(hi)||lo>hi)return false;
    return true;
}
static bool descriptionBoolB14(int type,int index)
{return type==5?(index==6||index==9||index==12||index==16||index==17):(index==8||index==11||index==14||index==17||index==18);}
static bool mutationBoolB14(int k){return k==32||k==36||k==38||k==48||k==52||k==54;}
static int mutationTypeB14(int k)
{return k==3||k>=48&&k<=56?4:k>=32&&k<=40?5:k>=16&&k<=24?0:-1;}
static bool mutationValidB14(int type,int k,float x,float y)
{
    if(k==2)return angle14(x);
    if(k==3){if(!axis14(x,y)){reason14=9;return false;}return true;}
    if(k==35)return angle14(x);
    if(k==37)return limitsR14(x,y);
    if(k==53)return isfinite(x)&&isfinite(y)&&x<=y;
    if(k==33||k==34||k==40||k==49||k==50||k==56)return isfinite(x)&&x>=0;
    if(k==39||k==51||k==55)return isfinite(x);
    return true;
}
static b2JointId createB14(int type,b2WorldId w,b2BodyId a,b2BodyId b,const uint32_t* u)
{
    if(type==5){b2RevoluteJointDef d=b2DefaultRevoluteJointDef();d.bodyIdA=a;d.bodyIdB=b;
        d.localAnchorA=(b2Vec2){from_bits(u[0]),from_bits(u[1])};d.localAnchorB=(b2Vec2){from_bits(u[2]),from_bits(u[3])};
        d.referenceAngle=from_bits(u[4]);d.targetAngle=from_bits(u[5]);d.enableSpring=u[6];d.hertz=from_bits(u[7]);d.dampingRatio=from_bits(u[8]);
        d.enableLimit=u[9];d.lowerAngle=from_bits(u[10]);d.upperAngle=from_bits(u[11]);d.enableMotor=u[12];
        d.maxMotorTorque=from_bits(u[13]);d.motorSpeed=from_bits(u[14]);d.drawSize=from_bits(u[15]);d.collideConnected=u[16];return b2CreateRevoluteJoint(w,&d);}
    b2PrismaticJointDef d=b2DefaultPrismaticJointDef();d.bodyIdA=a;d.bodyIdB=b;
    d.localAnchorA=(b2Vec2){from_bits(u[0]),from_bits(u[1])};d.localAnchorB=(b2Vec2){from_bits(u[2]),from_bits(u[3])};
    d.localAxisA=(b2Vec2){from_bits(u[4]),from_bits(u[5])};d.referenceAngle=from_bits(u[6]);d.targetTranslation=from_bits(u[7]);
    d.enableSpring=u[8];d.hertz=from_bits(u[9]);d.dampingRatio=from_bits(u[10]);d.enableLimit=u[11];
    d.lowerTranslation=from_bits(u[12]);d.upperTranslation=from_bits(u[13]);d.enableMotor=u[14];d.maxMotorForce=from_bits(u[15]);d.motorSpeed=from_bits(u[16]);d.collideConnected=u[17];return b2CreatePrismaticJoint(w,&d);
}
static void mutateB14(b2JointId id,int k,const Operation* o)
{
    float x=o->f[4],y=o->f[5];bool enabled=o->u[4];
    switch(k){
    case 32:b2RevoluteJoint_EnableSpring(id,enabled);break;
    case 33:b2RevoluteJoint_SetSpringHertz(id,x);break;
    case 34:b2RevoluteJoint_SetSpringDampingRatio(id,x);break;
    case 35:b2RevoluteJoint_SetTargetAngle(id,x);break;
    case 36:b2RevoluteJoint_EnableLimit(id,enabled);break;
    case 37:b2RevoluteJoint_SetLimits(id,x,y);break;
    case 38:b2RevoluteJoint_EnableMotor(id,enabled);break;
    case 39:b2RevoluteJoint_SetMotorSpeed(id,x);break;
    case 40:b2RevoluteJoint_SetMaxMotorTorque(id,x);break;
    case 48:b2PrismaticJoint_EnableSpring(id,enabled);break;
    case 49:b2PrismaticJoint_SetSpringHertz(id,x);break;
    case 50:b2PrismaticJoint_SetSpringDampingRatio(id,x);break;
    case 51:b2PrismaticJoint_SetTargetTranslation(id,x);break;
    case 52:b2PrismaticJoint_EnableLimit(id,enabled);break;
    case 53:b2PrismaticJoint_SetLimits(id,x,y);break;
    case 54:b2PrismaticJoint_EnableMotor(id,enabled);break;
    case 55:b2PrismaticJoint_SetMotorSpeed(id,x);break;
    case 56:b2PrismaticJoint_SetMaxMotorForce(id,x);break;
    default:fail("INPUT_ENUM");}
}
static void tailB14(b2JointId id,int type,uint32_t* u)
{
    if(type==5){uint32_t a[]={b2RevoluteJoint_IsSpringEnabled(id),to_bits(b2RevoluteJoint_GetSpringHertz(id)),to_bits(b2RevoluteJoint_GetSpringDampingRatio(id)),to_bits(b2RevoluteJoint_GetTargetAngle(id)),
        b2RevoluteJoint_IsLimitEnabled(id),to_bits(b2RevoluteJoint_GetLowerLimit(id)),to_bits(b2RevoluteJoint_GetUpperLimit(id)),to_bits(b2RevoluteJoint_GetAngle(id)),b2RevoluteJoint_IsMotorEnabled(id),
        to_bits(b2RevoluteJoint_GetMotorSpeed(id)),to_bits(b2RevoluteJoint_GetMaxMotorTorque(id)),to_bits(b2RevoluteJoint_GetMotorTorque(id))};memcpy(u,a,sizeof a);}
    else{uint32_t a[]={b2PrismaticJoint_IsSpringEnabled(id),to_bits(b2PrismaticJoint_GetSpringHertz(id)),to_bits(b2PrismaticJoint_GetSpringDampingRatio(id)),to_bits(b2PrismaticJoint_GetTargetTranslation(id)),
        b2PrismaticJoint_IsLimitEnabled(id),to_bits(b2PrismaticJoint_GetLowerLimit(id)),to_bits(b2PrismaticJoint_GetUpperLimit(id)),to_bits(b2PrismaticJoint_GetTranslation(id)),to_bits(b2PrismaticJoint_GetSpeed(id)),
        b2PrismaticJoint_IsMotorEnabled(id),to_bits(b2PrismaticJoint_GetMotorSpeed(id)),to_bits(b2PrismaticJoint_GetMaxMotorForce(id)),to_bits(b2PrismaticJoint_GetMotorForce(id))};memcpy(u,a,sizeof a);}
}

static void payloadR14(b2RevoluteJoint* d,uint32_t* u,bool load)
{
    if(load){d->linearImpulse.x=from_bits(u[0]);d->linearImpulse.y=from_bits(u[1]);d->springImpulse=from_bits(u[2]);d->motorImpulse=from_bits(u[3]);d->lowerImpulse=from_bits(u[4]);d->upperImpulse=from_bits(u[5]);d->hertz=from_bits(u[6]);d->dampingRatio=from_bits(u[7]);d->targetAngle=from_bits(u[8]);d->maxMotorTorque=from_bits(u[9]);d->motorSpeed=from_bits(u[10]);d->referenceAngle=from_bits(u[11]);d->lowerAngle=from_bits(u[12]);d->upperAngle=from_bits(u[13]);d->indexA=(int32_t)u[14];d->indexB=(int32_t)u[15];d->anchorA.x=from_bits(u[16]);d->anchorA.y=from_bits(u[17]);d->anchorB.x=from_bits(u[18]);d->anchorB.y=from_bits(u[19]);d->deltaCenter.x=from_bits(u[20]);d->deltaCenter.y=from_bits(u[21]);d->deltaAngle=from_bits(u[22]);d->axialMass=from_bits(u[23]);d->springSoftness.biasRate=from_bits(u[24]);d->springSoftness.massScale=from_bits(u[25]);d->springSoftness.impulseScale=from_bits(u[26]);d->enableSpring=u[27];d->enableMotor=u[28];d->enableLimit=u[29];}
    else{uint32_t a[]={to_bits(d->linearImpulse.x),to_bits(d->linearImpulse.y),to_bits(d->springImpulse),to_bits(d->motorImpulse),to_bits(d->lowerImpulse),to_bits(d->upperImpulse),to_bits(d->hertz),to_bits(d->dampingRatio),to_bits(d->targetAngle),to_bits(d->maxMotorTorque),to_bits(d->motorSpeed),to_bits(d->referenceAngle),to_bits(d->lowerAngle),to_bits(d->upperAngle),d->indexA,d->indexB,to_bits(d->anchorA.x),to_bits(d->anchorA.y),to_bits(d->anchorB.x),to_bits(d->anchorB.y),to_bits(d->deltaCenter.x),to_bits(d->deltaCenter.y),to_bits(d->deltaAngle),to_bits(d->axialMass),to_bits(d->springSoftness.biasRate),to_bits(d->springSoftness.massScale),to_bits(d->springSoftness.impulseScale),d->enableSpring,d->enableMotor,d->enableLimit};memcpy(u,a,sizeof a);}
}

static void payloadP14(b2PrismaticJoint* d,uint32_t* u,bool load)
{
    if(load){d->localAxisA.x=from_bits(u[0]);d->localAxisA.y=from_bits(u[1]);d->impulse.x=from_bits(u[2]);d->impulse.y=from_bits(u[3]);d->springImpulse=from_bits(u[4]);d->motorImpulse=from_bits(u[5]);d->lowerImpulse=from_bits(u[6]);d->upperImpulse=from_bits(u[7]);d->hertz=from_bits(u[8]);d->dampingRatio=from_bits(u[9]);d->targetTranslation=from_bits(u[10]);d->maxMotorForce=from_bits(u[11]);d->motorSpeed=from_bits(u[12]);d->referenceAngle=from_bits(u[13]);d->lowerTranslation=from_bits(u[14]);d->upperTranslation=from_bits(u[15]);d->indexA=(int32_t)u[16];d->indexB=(int32_t)u[17];d->anchorA.x=from_bits(u[18]);d->anchorA.y=from_bits(u[19]);d->anchorB.x=from_bits(u[20]);d->anchorB.y=from_bits(u[21]);d->axisA.x=from_bits(u[22]);d->axisA.y=from_bits(u[23]);d->deltaCenter.x=from_bits(u[24]);d->deltaCenter.y=from_bits(u[25]);d->deltaAngle=from_bits(u[26]);d->axialMass=from_bits(u[27]);d->springSoftness.biasRate=from_bits(u[28]);d->springSoftness.massScale=from_bits(u[29]);d->springSoftness.impulseScale=from_bits(u[30]);d->enableSpring=u[31];d->enableLimit=u[32];d->enableMotor=u[33];}
    else{uint32_t a[]={to_bits(d->localAxisA.x),to_bits(d->localAxisA.y),to_bits(d->impulse.x),to_bits(d->impulse.y),to_bits(d->springImpulse),to_bits(d->motorImpulse),to_bits(d->lowerImpulse),to_bits(d->upperImpulse),to_bits(d->hertz),to_bits(d->dampingRatio),to_bits(d->targetTranslation),to_bits(d->maxMotorForce),to_bits(d->motorSpeed),to_bits(d->referenceAngle),to_bits(d->lowerTranslation),to_bits(d->upperTranslation),d->indexA,d->indexB,to_bits(d->anchorA.x),to_bits(d->anchorA.y),to_bits(d->anchorB.x),to_bits(d->anchorB.y),to_bits(d->axisA.x),to_bits(d->axisA.y),to_bits(d->deltaCenter.x),to_bits(d->deltaCenter.y),to_bits(d->deltaAngle),to_bits(d->axialMass),to_bits(d->springSoftness.biasRate),to_bits(d->springSoftness.massScale),to_bits(d->springSoftness.impulseScale),d->enableSpring,d->enableLimit,d->enableMotor};memcpy(u,a,sizeof a);}
}

static const unsigned char mathFixtureIDs14[129]={0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
static void loadFixtureB14(FILE* input,unsigned id)
{
    uint32_t f[5][34]={{0}};int arities[]={5,17,30,20,16};
    for(int group=0;group<5;++group){char* p=row(input);if(strncmp(p,"F14 ",4))fail("INPUT_TAG");arity13(p,5+arities[group],"INPUT_ARITY");p+=4;
        uint32_t actual=decimal13(&p);space(&p);uint32_t fixture=decimal13(&p);space(&p);uint32_t gotgroup=decimal13(&p);space(&p);uint32_t n=decimal13(&p);
        if(actual!=id)fail("INPUT_ID");if(fixture||gotgroup!=(uint32_t)group)fail("INPUT_PHASE");if(n!=(uint32_t)arities[group])fail("INPUT_ARITY");
        for(unsigned i=0;i<n;++i){space(&p);f[group][i]=hex_word(&p);}if(*p)fail("INPUT_ARITY");if(group==1){if(f[1][3]!=4&&f[1][3]!=5)fail("INPUT_ENUM");arities[2]=payloadCount14(f[1][3]);}}
    if(f[0][2]>1)fail("INPUT_BOOL");if((f[0][3]!=0&&f[0][3]!=2)||(f[0][4]!=0&&f[0][4]!=2)||f[0][3]+f[0][4]==0)fail("INPUT_ENUM");
    if(!isfinite(from_bits(f[0][0]))||!isfinite(from_bits(f[0][1]))||from_bits(f[0][0])<=0||from_bits(f[0][1])<=0)fail("INPUT_DOMAIN");
    if(f[1][0]||f[1][1]||f[1][2]!=1)fail("INPUT_DOMAIN");
    int type=f[1][3];
    for(int g=1;g<=4;++g)for(int i=0;i<arities[g];++i){bool integer=g==1&&i<4||g==2&&(type==5?(i==14||i==15||i>=27):(i==16||i==17||i>=31))||g==4&&(i==3||i==11);if(!integer&&!isfinite(from_bits(f[g][i])))fail("INPUT_DOMAIN");}
    for(int i=type==5?27:31;i<arities[2];++i)if(f[2][i]>1)fail("INPUT_BOOL");
    mathId14=mathFixtureIDs14[id];mathCount14=mathId14==1?1:mathId14==2?6:0;
    if(mathId14){char* p=row(input);if(strncmp(p,"F14 ",4))fail("INPUT_TAG");arity13(p,5+mathCount14,"INPUT_ARITY");p+=4;
        uint32_t actual=decimal13(&p);space(&p);uint32_t fixture=decimal13(&p);space(&p);uint32_t group=decimal13(&p);space(&p);uint32_t n=decimal13(&p);
        if(actual!=id)fail("INPUT_ID");if(fixture!=(uint32_t)mathId14||group!=5)fail("INPUT_PHASE");if(n!=(uint32_t)mathCount14)fail("INPUT_ARITY");
        for(unsigned i=0;i<n;++i){space(&p);mathInput14[i]=hex_word(&p);if(!isfinite(from_bits(mathInput14[i])))fail("INPUT_DOMAIN");}if(*p)fail("INPUT_ARITY");}
    for(int b=0;b<2;++b){int at=b*10;float c=from_bits(f[3][at+2]),s=from_bits(f[3][at+3]);if(!b2IsNormalizedRot((b2Rot){c,s}))fail("INPUT_ROTATION");}
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;wd.workerCount=1;wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
    if(create_world(0,wd))fail("INPUT_DOMAIN");sync_hooks12();
    for(int i=0;i<2;++i){b2BodyDef bd=b2DefaultBodyDef();bd.type=f[0][3+i]==0?b2_staticBody:b2_dynamicBody;if(create_body(i,0,bd))fail("INPUT_DOMAIN");}
    descriptions14[0]=true;memset(definition14[0],0,sizeof definition14[0]);descriptionTypes14[0]=type;if(type==4)definition14[0][4]=to_bits(1);else definition14[0][15]=to_bits(.25f);
    Operation create={.code=201,.u={0,0,0,1,0,0}};if(create14(&create))fail("INPUT_DOMAIN");descriptions14[0]=false;
    b2World* w=b2GetWorldFromId(worlds[0].raw);b2JointSim* s=b2GetJointSim(w,w->joints.data);uint32_t* a=f[1];
    s->localOriginAnchorA=(b2Vec2){from_bits(a[4]),from_bits(a[5])};s->localOriginAnchorB=(b2Vec2){from_bits(a[6]),from_bits(a[7])};
    s->invMassA=from_bits(a[8]);s->invMassB=from_bits(a[9]);s->invIA=from_bits(a[10]);s->invIB=from_bits(a[11]);s->constraintHertz=from_bits(a[12]);s->constraintDampingRatio=from_bits(a[13]);
    s->constraintSoftness=(b2Softness){from_bits(a[14]),from_bits(a[15]),from_bits(a[16])};a=f[2];if(type==5)payloadR14(&s->revoluteJoint,a,true);else payloadP14(&s->prismaticJoint,a,true);
    memset(&directContext14,0,sizeof directContext14);directContext14.world=w;directContext14.graph=&w->constraintGraph;directContext14.h=from_bits(f[0][0]);directContext14.inv_h=from_bits(f[0][1]);directContext14.enableWarmStarting=f[0][2];
    directContext14.states=w->solverSets.data[2].bodyStates.data;directContext14.sims=w->solverSets.data[2].bodySims.data;
    directStates14[0]=(b2BodyState){.deltaRotation=b2Rot_identity};
    for(int i=0;i<2;++i){a=f[3]+10*i;b2BodySim* sim=b2GetBodySim(w,w->bodies.data+i);
        sim->transform=(b2Transform){{from_bits(a[0]),from_bits(a[1])},{from_bits(a[2]),from_bits(a[3])}};sim->localCenter=(b2Vec2){from_bits(a[4]),from_bits(a[5])};sim->center=(b2Vec2){from_bits(a[6]),from_bits(a[7])};sim->invMass=from_bits(a[8]);sim->invInertia=from_bits(a[9]);
        a=f[4]+8*i;b2BodyState state={{from_bits(a[0]),from_bits(a[1])},from_bits(a[2]),a[3],{from_bits(a[4]),from_bits(a[5])},{from_bits(a[6]),from_bits(a[7])}};
        if(f[0][3+i]==2)*b2GetBodyState(w,w->bodies.data+i)=state;}
    for(int group=0;group<5;++group){printf("EF14 %u 0 %d %d",id,group,arities[group]);array14(f[group],arities[group]);}
    if(mathId14){printf("EF14 %u %d 5 %d",id,mathId14,mathCount14);array14(mathInput14,mathCount14);}
}
