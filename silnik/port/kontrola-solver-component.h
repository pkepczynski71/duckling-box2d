                                                                               
                                                                           
   
static void fields10(FILE* input,const char* tag,int np,int nw,int* prefix,uint32_t* words)
{
    char* p=row(input);size_t len=strlen(tag);
    if(!strcmp(tag,"FP")&&!strncmp(p,"F ",2))fail("INPUT_CAPTURE_UNCLOSED");
    if(strncmp(p,tag,len)||p[len]!=' ')fail("INPUT_TAG");arity10(p,1+np+nw);p+=len;
    for(int j=0;j<np;++j){space(&p);prefix[j]=(int)decimal(&p);}
    for(int j=0;j<nw;++j){space(&p);words[j]=hex_word(&p);}if(*p)fail("INPUT_ARITY");
}
static void seed_echo10(const char* tag,int np,const int* prefix,int nw,const uint32_t* words)
{
    printf("%s",tag);for(int j=0;j<np;++j)printf(" %d",prefix[j]);for(int j=0;j<nw;++j)word(words[j]);putchar('\n');
}
static void context10(b2StepContext* c,b2World* w,const uint32_t* fw,int n,int warm)
{
    memset(c,0,sizeof(*c));w->gravity=(b2Vec2){from_bits(fw[0]),from_bits(fw[1])};w->maxLinearSpeed=from_bits(fw[2]);
    w->contactHertz=from_bits(fw[3]);w->contactDampingRatio=from_bits(fw[4]);w->maxContactPushSpeed=from_bits(fw[5]);
    w->restitutionThreshold=from_bits(fw[6]);w->hitEventThreshold=from_bits(fw[7]);w->enableWarmStarting=warm!=0;
    c->dt=from_bits(fw[8]);c->subStepCount=n;c->inv_dt=1.0f/c->dt;c->h=c->dt/(float)n;c->inv_h=(float)n*c->inv_dt;
    if(c->h<=0||!isfinite(c->h)||!isfinite(c->inv_dt)||!isfinite(c->inv_h))fail("INPUT_DOMAIN");
    float hz=b2MinFloat(w->contactHertz,0.125f*c->inv_h);
    c->contactSoftness=b2MakeSoft(hz,w->contactDampingRatio,c->h);c->staticSoftness=b2MakeSoft(2.0f*hz,w->contactDampingRatio,c->h);
    w->contactSpeed=w->maxContactPushSpeed/c->staticSoftness.massScale;
    c->restitutionThreshold=w->restitutionThreshold;c->maxLinearVelocity=w->maxLinearSpeed;c->enableWarmStarting=w->enableWarmStarting;
    c->world=w;c->graph=&w->constraintGraph;c->workerCount=1;
    b2SolverSet* set=w->solverSets.data+b2_awakeSet;c->states=set->bodyStates.data;c->sims=set->bodySims.data;
}
static void seed_body10(b2World* w,int j,const uint32_t* u)
{
    b2SolverSet* set=w->solverSets.data+b2_awakeSet;b2BodySim* sim=set->bodySims.data+j;
    b2BodyState* state=set->bodyStates.data+j;memset(sim,0,sizeof(*sim));memset(state,0,sizeof(*state));
    sim->bodyId=(int)u[0];sim->invMass=from_bits(u[1]);sim->invInertia=from_bits(u[2]);
    sim->force=(b2Vec2){from_bits(u[3]),from_bits(u[4])};sim->torque=from_bits(u[5]);
    sim->linearDamping=from_bits(u[6]);sim->angularDamping=from_bits(u[7]);sim->gravityScale=from_bits(u[8]);sim->allowFastRotation=u[9]!=0;
    state->linearVelocity=(b2Vec2){from_bits(u[10]),from_bits(u[11])};state->angularVelocity=from_bits(u[12]);
    state->deltaPosition=(b2Vec2){from_bits(u[13]),from_bits(u[14])};state->deltaRotation=(b2Rot){from_bits(u[15]),from_bits(u[16])};
    for(int k=0;k<17;++k)if(k!=0&&k!=9&&!isfinite(from_bits(u[k])))fail("INPUT_DOMAIN");
    if(u[0]>7||u[9]>1||sim->invMass<0||sim->invInertia<0||sim->linearDamping<0||sim->angularDamping<0||!b2IsNormalizedRot(state->deltaRotation))fail("INPUT_DOMAIN");
    for(int k=0;k<j;++k)if(set->bodySims.data[k].bodyId==sim->bodyId)fail("INPUT_REGISTER_COLLISION");
    while(w->bodyIdPool.nextIndex<=sim->bodyId)b2AllocId(&w->bodyIdPool);
}
static void seed_contact10(b2World* w,int color,int local,const uint32_t* u)
{
    if(color<0||color>11||local!=w->constraintGraph.colors[color].contactSims.count)fail("INPUT_REGISTER_RANGE");
    b2ContactSim* s=b2ContactSimArray_Add(&w->constraintGraph.colors[color].contactSims);memset(s,0,sizeof(*s));
    s->contactId=(int)u[0];memcpy(&s->bodySimIndexA,u+1,4);memcpy(&s->bodySimIndexB,u+2,4);
    s->shapeIdA=(int)u[3];s->shapeIdB=(int)u[4];s->invMassA=from_bits(u[5]);s->invIA=from_bits(u[6]);
    s->invMassB=from_bits(u[7]);s->invIB=from_bits(u[8]);s->friction=from_bits(u[9]);s->restitution=from_bits(u[10]);
    s->rollingResistance=from_bits(u[11]);s->tangentSpeed=from_bits(u[12]);s->simFlags=u[13];
    if(u[14]>3)fail("INPUT_FIXTURE_CACHE");s->cache.count=(uint16_t)u[14];
    for(int j=0;j<3;++j){if(u[15+j]>255||u[18+j]>255)fail("INPUT_FIXTURE_CACHE");s->cache.indexA[j]=(uint8_t)u[15+j];s->cache.indexB[j]=(uint8_t)u[18+j];}
    s->manifold=decode_manifold9(u+21);if(s->manifold.pointCount<1||s->manifold.pointCount>2)fail("INPUT_FIXTURE_MANIFOLD");
    for(int k=0;k<30;++k){uint32_t value=u[21+k];bool integer=k==3||k==15||k==16||k==28||k==29;
        if((!integer&&!isfinite(from_bits(value)))||((k==15||k==28)&&value>65535)||((k==16||k==29)&&value>1))fail("INPUT_FIXTURE_MANIFOLD");}
    if(!(s->simFlags&b2_simTouchingFlag))fail("INPUT_DOMAIN");
    if(u[0]>7||u[3]>15||u[4]>15)fail("INPUT_REGISTER_RANGE");
    for(int k=5;k<=12;++k)if(!isfinite(from_bits(u[k]))||(k<12&&from_bits(u[k])<0))fail("INPUT_DOMAIN");
    b2SolverSet* set=w->solverSets.data+b2_awakeSet;int indices[]={s->bodySimIndexA,s->bodySimIndexB};
    for(int side=0;side<2;++side){int i=indices[side];float mass=side?s->invMassB:s->invMassA,inertia=side?s->invIB:s->invIA;
        if(i<-1||i>=set->bodySims.count)fail("INPUT_REGISTER_RANGE");
        if(i==-1){if(mass!=0||inertia!=0)fail("INPUT_DOMAIN");}
        else if(to_bits(mass)!=to_bits(set->bodySims.data[i].invMass)||to_bits(inertia)!=to_bits(set->bodySims.data[i].invInertia))fail("INPUT_DOMAIN");}
    if(indices[0]!=-1&&indices[0]==indices[1])fail("INPUT_DOMAIN");
    for(int c=0;c<=color;++c){b2ContactSimArray* array=&w->constraintGraph.colors[c].contactSims;
        for(int j=0;j<array->count;++j){b2ContactSim* previous=array->data+j;if(previous==s)continue;
            if(previous->contactId==s->contactId)fail("INPUT_REGISTER_COLLISION");
            if(c==color&&color!=11)for(int side=0;side<2;++side)if(indices[side]!=-1&&(indices[side]==previous->bodySimIndexA||indices[side]==previous->bodySimIndexB))fail("INPUT_DOMAIN");}}
}
static int blocks10(b2SolverBlock* blocks,int count,int body,int type)
{
    int base=body?32:4,n=count?(count-1)/base+1:0;if(count>4*base){base=count/4;n=4;}
    for(int j=0;j<n;++j){blocks[j]=(b2SolverBlock){0};blocks[j].startIndex=j*base;
        int width=j==n-1?count-j*base:base;if(width>INT16_MAX)fail("INPUT_POPULATION");
        blocks[j].count=(int16_t)width;blocks[j].blockType=(int16_t)type;}
    return n;
}
static void component_layout10(b2StepContext* c,b2SolverStage* stages,b2SolverBlock blocks[64][4])
{
    int total=0;
    for(int color=0;color<11;++color)total+=(c->graph->colors[color].contactSims.count+B2_SIMD_WIDTH-1)/B2_SIMD_WIDTH;
    c->contacts=malloc((size_t)(B2_SIMD_WIDTH*total+1)*sizeof(*c->contacts));
    size_t simdBytes=(size_t)(total+1)*(size_t)b2GetContactConstraintSIMDByteCount();
                                                                                                  
    c->simdContactConstraints=aligned_alloc(32,(simdBytes+31)&~(size_t)31);
    c->graph->colors[11].overflowConstraints=malloc((size_t)(c->graph->colors[11].contactSims.count+1)*sizeof(b2ContactConstraint));
    if(!c->contacts||!c->simdContactConstraints||!c->graph->colors[11].overflowConstraints)fail("INPUT_DOMAIN");
    int base=0;for(int color=0;color<11;++color){b2GraphColor* g=c->graph->colors+color;int packets=(g->contactSims.count+B2_SIMD_WIDTH-1)/B2_SIMD_WIDTH;
        g->simdConstraints=(b2ContactConstraintSIMD*)((unsigned char*)c->simdContactConstraints+(size_t)base*(size_t)b2GetContactConstraintSIMDByteCount());
        for(int j=0;j<B2_SIMD_WIDTH*packets;++j)c->contacts[B2_SIMD_WIDTH*base+j]=j<g->contactSims.count?g->contactSims.data+j:NULL;base+=packets;}
    int num=0;
    for(int phase=0;phase<8;++phase){
        if(phase==0||phase==1||phase==4||phase==7){int body=phase==1||phase==4,count=body?c->world->solverSets.data[b2_awakeSet].bodySims.count:total;
            b2SolverStage* s=stages+num;memset(s,0,sizeof(*s));s->type=phase==0?b2_stagePrepareContacts:phase==1?b2_stageIntegrateVelocities:phase==4?b2_stageIntegratePositions:b2_stageStoreImpulses;
            s->colorIndex=-1;s->blocks=blocks[num];s->blockCount=blocks10(s->blocks,count,body,body?b2_bodyBlock:b2_contactBlock);++num;
        }else for(int color=0;color<11;++color){int packets=(c->graph->colors[color].contactSims.count+B2_SIMD_WIDTH-1)/B2_SIMD_WIDTH;if(!packets)continue;
            b2SolverStage* s=stages+num;memset(s,0,sizeof(*s));s->type=phase==2?b2_stageWarmStart:phase==3?b2_stageSolve:phase==5?b2_stageRelax:b2_stageRestitution;
            s->colorIndex=color;s->blocks=blocks[num];s->blockCount=blocks10(s->blocks,packets,0,b2_graphContactBlock);++num;}}
    c->stages=stages;c->stageCount=num;
}
static int component_main10(FILE* input,int count)
{
    componentMode10=1;printf("COMPONENT10 %d\n",count);
    for(int id=1;id<=count;++id){case9=id;observedWorld10=0;memset(componentCounts10,0,sizeof(componentCounts10));
        int f[8];uint32_t unused[1];fields10(input,"F",8,0,f,unused);
        int fixture=f[1],n=f[2],warm=f[3],nb=f[4],nc=f[5],nh=f[6],phases=f[7];
        if(f[0]!=id||fixture<1||fixture>16||(n!=1&&n!=4&&n!=8)||warm<0||warm>1||nb<0||nb>8||nc<0||nc>8||nh<0||nh>32||phases!=5*n+3)fail("INPUT_DOMAIN");
        seed_echo10("F",8,f,0,unused);int prefix[4];uint32_t fw[9];fields10(input,"FW",1,9,prefix,fw);
        if(prefix[0]!=id)fail("INPUT_ID");for(int j=0;j<9;++j)if(!isfinite(from_bits(fw[j]))||(j>=2&&from_bits(fw[j])<0))fail("INPUT_DOMAIN");
        if(from_bits(fw[2])<=0||from_bits(fw[8])<=0)fail("INPUT_DOMAIN");seed_echo10("FW",1,prefix,9,fw);
        b2WorldDef d=b2DefaultWorldDef();d.enableSleep=false;d.enableContinuous=false;
        b2WorldId raw=b2CreateWorld(&d);b2World* w=b2GetWorldFromId(raw);b2SolverSet* set=w->solverSets.data+b2_awakeSet;
        b2BodySimArray_Resize(&set->bodySims,nb);b2BodyStateArray_Resize(&set->bodyStates,nb);
        for(int j=0;j<nb;++j){uint32_t u[17];fields10(input,"FB",2,17,prefix,u);if(prefix[0]!=id||prefix[1]!=j)fail("INPUT_ID");seed_body10(w,j,u);seed_echo10("FB",2,prefix,17,u);}
        int previousColor=-1;
        for(int j=0;j<nc;++j){uint32_t u[51];fields10(input,"FC",4,51,prefix,u);if(prefix[0]!=id||prefix[1]!=j)fail("INPUT_ID");
            if(prefix[2]<previousColor)fail("INPUT_DOMAIN");previousColor=prefix[2];seed_contact10(w,prefix[2],prefix[3],u);seed_echo10("FC",4,prefix,51,u);}
        uint32_t helpers[32][16];int kinds[32];
        for(int j=0;j<nh;++j){fields10(input,"FX",3,16,prefix,helpers[j]);if(prefix[0]!=id||prefix[1]!=j||prefix[2]<0||prefix[2]>2)fail("INPUT_ID");kinds[j]=prefix[2];
            if(kinds[j]!=2)for(int k=0;k<16;++k)if(!isfinite(from_bits(helpers[j][k])))fail("INPUT_DOMAIN");
            if(kinds[j]==0)for(int k=4;k<8;++k)if(from_bits(helpers[j][k])<0)fail("INPUT_DOMAIN");
            if(kinds[j]==1)for(int lane=0;lane<4;++lane)if(!b2IsNormalizedRot((b2Rot){from_bits(helpers[j][lane]),from_bits(helpers[j][4+lane])}))fail("INPUT_ROTATION");
            if(kinds[j]==2){if(helpers[j][1]>INT32_MAX||helpers[j][2]>2)fail("INPUT_DOMAIN");for(int k=3;k<16;++k)if(helpers[j][k])fail("INPUT_UNUSED");}
            seed_echo10("FX",3,prefix,16,helpers[j]);}
        for(int j=0;j<nh;++j)port10Helpers(j,kinds[j],helpers[j]);
        b2StepContext context;context10(&context,w,fw,n,warm);b2SolverStage stages[64];b2SolverBlock blocks[64][4];component_layout10(&context,stages,blocks);
        for(int ordinal=0;ordinal<phases;++ordinal){int next=fgetc(input);if(next==EOF)fail("INPUT_CAPTURE_UNCLOSED");ungetc(next,input);fields10(input,"FP",4,0,prefix,unused);
            int sub=ordinal==0||ordinal>=phases-2?0:(ordinal-1)/5+1;
            int phase=ordinal==0?0:ordinal==phases-2?6:ordinal==phases-1?7:(ordinal-1)%5+1;
            if(prefix[0]!=id||prefix[1]!=ordinal||prefix[2]!=sub||prefix[3]!=phase)fail("INPUT_PHASE");
            seed_echo10("FP",4,prefix,0,unused);seq9=(uint32_t)ordinal+1;begin_output9();
            if(phase==1||phase==4)port10Integrate(&context,phase==4,nb);else port10ComponentContacts(&context,phase);
            port10Trace(&context,sub,phase,phase==0);commit10();++componentCounts10[0];}
        for(int j=0;j<nc;++j){                                                  
            int at=0;for(int color=0;color<12;++color){b2ContactSimArray* a=&w->constraintGraph.colors[color].contactSims;
                for(int local=0;local<a->count;++local,++at)if(at==j){printf("FM10 %d %d",id,j);manifold9(a->data[local].manifold);putchar('\n');++componentCounts10[6];}}}
        printf("FI10 %d",id);for(int j=0;j<7;++j)word(componentCounts10[j]);putchar('\n');printf("ENDCASE %d\n",id);
        free(context.contacts);free(context.simdContactConstraints);free(w->constraintGraph.colors[11].overflowConstraints);
        b2DestroyWorld(raw);
    }
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input)||fclose(input))fail("INPUT_DOMAIN");
    printf("END %d\n",count);return (ferror(stdout)||fflush(stdout))?2:0;
}
