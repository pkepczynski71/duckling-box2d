                                                                                  
#include "kontrola-sen11.h"
#include "world.h"
#include "solver_set.h"
#include "island.h"
static int profile11=5,fixture11;
static uint64_t port11BodyUpper(b2World*);
static bool body_upper_fit11(uint64_t count);
#include "sen-solver10.inc"
static b2BodyDef body11(const Operation* o);
static bool threshold11(float value){return isfinite(value)&&value>=0;}
static bool valid_body11(const b2BodyDef* d){return valid_body8(d)&&threshold11(d->sleepThreshold);}

typedef struct Trace11 { b2World* world; uint32_t value[7]; } Trace11;
typedef struct Final11 { bool present;uint32_t words[4];int count,capacity;uint64_t bits[32]; } Final11;
static Trace11 traces11[4096];static int traceCount11;
static Final11 finals11[WORLDS];static uint32_t count11[11],public11[2],positive11;
                                                                               
static uint64_t finalizedBirth11[WORLDS];
extern void port11OriginalWakeSolverSet(b2World*,int);
extern void port11OriginalTrySleepIsland(b2World*,int);
extern void port11OriginalSplitIsland(b2World*,int);
extern void port11OriginalSplitIslandTask(int,int,uint32_t,void*);

static uint64_t port11BodyUpper(b2World* w)
{
    uint64_t count=0;for(int i=2;i<w->solverSetIdPool.nextIndex;++i)
        if(w->solverSets.data[i].setIndex==i)count+=(uint64_t)w->solverSets.data[i].bodySims.count;
    return count;
}
static int trace11(b2World* w,int kind,int object,int source,int bodies_,int contacts_)
{
    if(traceCount11==4096)fail("INPUT_POPULATION");int id=traceCount11++;
    traces11[id]=(Trace11){w,{kind,object,source,source,bodies_,contacts_,0}};return id;
}
void b2WakeSolverSet(b2World* w,int set)
{
    b2SolverSet* s=w->solverSets.data+set;int n=trace11(w,1,set,set,s->bodySims.count,s->contactSims.count);
    port11OriginalWakeSolverSet(w,set);
    traces11[n].value[3]=2;traces11[n].value[6]=1;
}
void b2TrySleepIsland(b2World* w,int island)
{
    b2Island before=w->islands.data[island];int n=trace11(w,2,island,before.setIndex,before.bodyCount,before.contactCount);
    port11OriginalTrySleepIsland(w,island);
    int after=w->islands.data[island].setIndex;traces11[n].value[3]=after;
    traces11[n].value[6]=after!=before.setIndex;
}
void b2SplitIsland(b2World* w,int island)
{
    b2Island before=w->islands.data[island];int n=trace11(w,3,island,before.setIndex,before.bodyCount,before.contactCount);
                                                                                
    bool work=before.setIndex==b2_awakeSet&&before.constraintRemoveCount>0;
    port11OriginalSplitIsland(w,island);traces11[n].value[6]=work;
}
void b2SplitIslandTask(int start,int end,uint32_t thread,void* context)
{
    b2World* w=context;b2Island before=w->islands.data[w->splitIslandId];
    int n=trace11(w,3,w->splitIslandId,before.setIndex,before.bodyCount,before.contactCount);
    bool work=before.setIndex==b2_awakeSet&&before.constraintRemoveCount>0;
                                                                                      
    port11OriginalSplitIslandTask(start,end,thread,context);traces11[n].value[6]=work;
}
void port11AfterFinalize(b2World* w)
{
    if(!OBS)return;int owner=owner9(w);if(owner<0)fail("INPUT_DOMAIN");
    Final11* f=finals11+owner;if(f->present)fail("INPUT_DOMAIN");f->present=true;
    finalizedBirth11[owner]=worlds[owner].birth;
    b2TaskContext* task=w->taskContexts.data;
    f->words[0]=w->enableSleep;f->words[1]=w->splitIslandId;
    f->words[2]=task->splitIslandId;f->words[3]=to_bits(task->splitSleepTime);
    b2BitSet* bits=&task->awakeIslandBitSet;f->count=bits->blockCount;f->capacity=bits->blockCapacity;
    if(f->count>32)fail("INPUT_POPULATION");for(int j=0;j<f->count;++j)f->bits[j]=bits->bits[j];
}
static void record11(const char* tag,int owner,int extra_,int np,const uint32_t* words,int nw,int counter)
{
    printf("%s %d %"PRIu32" %d",tag,case9,seq9,owner);if(np)printf(" %d",extra_);
    for(int j=0;j<nw;++j)word(words[j]);putchar('\n');
    if(counter>=0)++count11[counter];
}
static void state11(int owner,int reg,int mode)
{
    Body* b=bodies+reg;int status=guard(worlds+owner,b);uint32_t value[10]={status,(uint32_t)(b->raw.index1-1),b->birth,b->birth>>32,b->owner,b->owner>>32,0,0,0,0};
    if(!status){b2BodyId id=b->raw;value[6]=b2Body_IsAwake(id);value[7]=b2Body_IsEnabled(id)&&b2Body_GetType(id)!=b2_staticBody&&!value[6];value[8]=b2Body_IsSleepEnabled(id);value[9]=to_bits(b2Body_GetSleepThreshold(id));}
    (void)mode;record11("GS11",reg,0,0,value,10,-1);++public11[1];
}
static void public_sleep11(const Operation* o)
{
    for(int j=0;j<WORLDS;++j)if(worlds[j].saved){uint32_t v[]={world_live(worlds+j)?OK:STALE,world_live(worlds+j)?b2World_IsSleepingEnabled(worlds[j].raw):0};record11("SW11",j,0,0,v,2,-1);++public11[0];}
    for(int j=0;j<BODIES;++j)if(bodies[j].saved){int owner=-1;for(int k=0;k<WORLDS;++k)if(worlds[k].saved&&worlds[k].birth==bodies[j].owner){owner=k;break;}
        if(o->code==62&&(int)o->u[1]==j)owner=(int)o->u[0];
        if(owner<0){uint32_t v[]={STALE,(uint32_t)(bodies[j].raw.index1-1),bodies[j].birth,bodies[j].birth>>32,bodies[j].owner,bodies[j].owner>>32,0,0,0,0};record11("GS11",j,0,0,v,10,-1);++public11[1];}
        else state11(owner,j,1);}
}
static void bitset11(int owner,int phase,int count,int capacity,const uint64_t* bits)
{
    printf("AB11 %d %"PRIu32" %d %d",case9,seq9,owner,phase);word(count);word(capacity);
    for(int j=0;j<count;++j)wide(bits[j]);putchar('\n');++count11[5];
}
static void sim11(b2BodySim* s)
{
    transform_words(s->transform);vec(s->center);vec(s->localCenter);real(s->rotation0.c);real(s->rotation0.s);vec(s->center0);
    vec(s->force);real(s->torque);real(s->invMass);real(s->invInertia);real(s->minExtent);real(s->maxExtent);
    real(s->linearDamping);real(s->angularDamping);real(s->gravityScale);word(s->bodyId);
    word(s->isFast);word(s->isBullet);word(s->isSpeedCapped);word(s->allowFastRotation);word(s->enlargeAABB);
}
static void private_sleep11(void)
{
    if(!OBS)return;
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2World* w=b2GetWorldFromId(worlds[owner].raw);Final11* f=finals11+owner;
        if(f->present)record11("WS11",owner,0,1,f->words,4,0);
        b2TaskContext* task=w->taskContexts.data;bool initialized=finalizedBirth11[owner]==worlds[owner].birth;
        uint32_t v[]={w->enableSleep,w->splitIslandId,initialized?(uint32_t)task->splitIslandId:0,initialized?to_bits(task->splitSleepTime):0};record11("WS11",owner,1,1,v,4,0);
        for(int j=0;j<w->bodyIdPool.nextIndex;++j){b2Body* b=w->bodies.data+j;if(b->id!=j)continue;uint32_t value[]={to_bits(b->sleepThreshold),to_bits(b->sleepTime),b->enableSleep,b->isMarked,b->bodyMoveIndex,b->setIndex==2};record11("BS11",owner,j,1,value,6,1);}
        for(int j=0;j<w->solverSetIdPool.nextIndex;++j){b2SolverSet* s=w->solverSets.data+j;bool live=s->setIndex==j;uint32_t v[]={live,live?j:UINT32_MAX,live?s->bodySims.count:0,live?s->bodyStates.count:0,live?s->contactSims.count:0,live?s->islandSims.count:0};record11("SS11",owner,j,1,v,6,2);}
        for(int j=0;j<w->solverSetIdPool.nextIndex;++j){b2SolverSet* s=w->solverSets.data+j;if(s->setIndex!=j)continue;for(int k=0;k<s->bodySims.count;++k){printf("SD11 %d %"PRIu32" %d %d %d",case9,seq9,owner,j,k);word(s->bodySims.data[k].bodyId);putchar('\n');++count11[3];}}
        for(int j=0;j<w->solverSetIdPool.nextIndex;++j){b2SolverSet* s=w->solverSets.data+j;if(s->setIndex!=j)continue;for(int k=0;k<s->bodySims.count;++k){printf("SM11 %d %"PRIu32" %d %d %d",case9,seq9,owner,j,k);sim11(s->bodySims.data+k);putchar('\n');++count11[4];}}
        if(f->present)bitset11(owner,0,f->count,f->capacity,f->bits);
        b2BitSet* bits=&task->awakeIslandBitSet;bitset11(owner,1,bits->blockCount,bits->blockCapacity,bits->bits);
        int ordinal=0;for(int j=0;j<traceCount11;++j)if(traces11[j].world==w)record11("TR11",owner,ordinal++,1,traces11[j].value,7,6);
        if(ordinal>4*(bound10(0)+bound10(2)+1))fail("INPUT_POPULATION");
        b2IdPool* pools[]={&w->solverSetIdPool,&w->bodyIdPool};
        for(int group=0;group<2;++group){b2IdPool* pool=pools[group];uint32_t v[]={pool->nextIndex,pool->freeArray.count,b2GetIdCount(pool)};record11(group?"BP11":"SP11",owner,0,0,v,3,group?9:7);
            for(int k=0;k<pool->freeArray.count;++k){uint32_t value=pool->freeArray.data[k];record11(group?"BF11":"SF11",owner,k,1,&value,1,group?10:8);}}
    }
}
static Operation read11(FILE* input,uint32_t seq)
{
    char* text=row(input);char saved[2050];snprintf(saved,sizeof(saved),"%s\n",text);char* p=text;
    if(strncmp(p,"O ",2))fail("INPUT_TAG");arity10(p,67);p+=2;uint32_t actual=decimal(&p);space(&p);uint32_t code=decimal(&p);if(actual!=seq)fail("INPUT_SEQ");
    if(!(code<=5||code>=10&&code<=19||code==21||code>=30&&code<=62||code==64))fail("INPUT_OPCODE");
    Operation o={0};o.code=code;
    for(int j=0;j<64;++j){space(&p);o.u[j]=hex_word(&p);o.f[j]=from_bits(o.u[j]);}if(*p)fail("INPUT_ARITY");
    if(code>=41&&code<=45||code>=51&&code<=53){FILE* stream=fmemopen(saved,strlen(saved),"r");if(!stream)fail("INPUT_DOMAIN");Operation result_=read_operation(stream,seq);fclose(stream);if(profile11!=7)fail("INPUT_PHASE");return result_;}
    if(code<56){FILE* stream=fmemopen(saved,strlen(saved),"r");if(!stream)fail("INPUT_DOMAIN");Operation result_=read10(stream,seq);fclose(stream);return result_;}
    if(o.u[0]>=WORLDS||(code!=56&&code!=61&&code!=64&&o.u[1]>=BODIES))fail("INPUT_REGISTER_RANGE");
    if(code==64){if(o.u[1]<1||o.u[1]>3)fail("INPUT_ENUM");for(int j=4;j<64;++j)if(o.u[j])fail("INPUT_UNUSED");
        if(!worlds[o.u[0]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(!world_live(worlds+o.u[0]))fail("INPUT_DOMAIN");b2World* w=b2GetWorldFromId(worlds[o.u[0]].raw);uint32_t object=o.u[2];
        if(o.u[1]==1){if(object<3||object>=(uint32_t)w->solverSetIdPool.nextIndex||w->solverSets.data[object].setIndex!=(int)object)fail("INPUT_DOMAIN");}
        else if(object>=(uint32_t)w->islandIdPool.nextIndex||w->islands.data[object].islandId!=(int)object||o.u[1]==2&&w->islands.data[object].setIndex!=2)fail("INPUT_DOMAIN");if(profile11!=7||phase9)fail("INPUT_PHASE");if(o.u[3])fail("INPUT_PROFILE");return o;}
    if(code==56){if(o.u[1]>1)fail("INPUT_MODE");if(o.u[10]>1||o.u[11]>1)fail("INPUT_BOOL");}
    else if(code==61){if(o.u[1]>1)fail("INPUT_MODE");if(o.u[2]>1)fail("INPUT_BOOL");}
    else {if(o.u[2]>1)fail("INPUT_MODE");if(code==57){if(o.u[3]>2)fail("INPUT_ENUM");for(int j=14;j<=17;++j)if(o.u[j]>1)fail("INPUT_BOOL");}
        else if((code==58||code==59)&&o.u[3]>1)fail("INPUT_BOOL");}
    const int used[]={12,19,4,4,4,3,3};for(int j=used[code-56];j<64;++j)if(o.u[j])fail("INPUT_UNUSED");
    if(code==56&&!o.u[1]&&!valid_solver_world10(&o))fail("INPUT_DOMAIN");
    if(code==57&&!o.u[2]){b2BodyDef d=body11(&o);if(!valid_body11(&d))fail("INPUT_DOMAIN");}
    if(code==60&&!o.u[2]&&!threshold11(o.f[3]))fail("INPUT_DOMAIN");
    if(code!=56&&!worlds[o.u[0]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    if(code!=56&&code!=57&&code!=61&&!bodies[o.u[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    if(code==56&&worlds[o.u[0]].live||code==57&&bodies[o.u[1]].live)fail("INPUT_REGISTER_COLLISION");
    return o;
}
static b2BodyDef body11(const Operation* o)
{
    b2BodyDef d=b2DefaultBodyDef();d.type=o->u[3];d.position=(b2Vec2){o->f[4],o->f[5]};d.rotation=(b2Rot){o->f[6],o->f[7]};d.linearVelocity=(b2Vec2){o->f[8],o->f[9]};d.angularVelocity=o->f[10];d.linearDamping=o->f[11];d.angularDamping=o->f[12];d.gravityScale=o->f[13];d.fixedRotation=o->u[14];d.allowFastRotation=o->u[15];d.enableSleep=o->u[16];d.isAwake=o->u[17];d.sleepThreshold=o->f[18];return d;
}
static void execute11(const Operation* o)
{
    int c=o->code;if(c<56){execute10(o);if((c==31||c==32)&&extra.status==0&&o->f[1]>0)++positive11;return;}
    reset_extra10();int owner=o->u[0],slot=owner,status=0,kind=1;
    if(c==64){b2World* w=b2GetWorldFromId(worlds[owner].raw);if(o->u[1]==1)b2WakeSolverSet(w,o->u[2]);else if(o->u[1]==2)b2TrySleepIsland(w,o->u[2]);else b2SplitIsland(w,o->u[2]);population_after9();echo(case9,seq9,o);result(case9,seq9,0,0,0,0);dump(case9,seq9,1,0,0,-1);return;}
    if(c==56){status=solver_world10(o);kind=status?0:1;if(!status)b2World_EnableSleeping(worlds[owner].raw,o->u[11]);}
    else if(c==57){kind=2;slot=o->u[1];b2BodyDef d=body11(o);if(!o->u[2]&&!valid_body11(&d))fail("INPUT_DOMAIN");
        status=world_live(worlds+owner)?OK:STALE;if(!status&&o->u[2]&&!valid_body11(&d))status=PARAM;
        if(!status)status=create_body(slot,owner,d);if(status)kind=0;
    }else if(c==61){status=world_live(worlds+owner)?OK:STALE;if(!status)b2World_EnableSleeping(worlds[owner].raw,o->u[2]);}
    else{slot=o->u[1];kind=2;status=guard(worlds+owner,bodies+slot);
        if(!status&&c==60&&!threshold11(o->f[3]))status=PARAM;
        if(!status){b2BodyId id=bodies[slot].raw;if(c==58)b2Body_SetAwake(id,o->u[3]);else if(c==59)b2Body_EnableSleep(id,o->u[3]);else if(c==60)b2Body_SetSleepThreshold(id,o->f[3]);}}
    population_after9();echo(case9,seq9,o);result(case9,seq9,0,status,kind,slot);dump(case9,seq9,1,0,0,-1);
}
static void run_row11(FILE* input,uint32_t seq)
{
    int id=case9;reset_operation9(id,seq,0);traceCount11=0;memset(finals11,0,sizeof(finals11));memset(count11,0,sizeof(count11));memset(public11,0,sizeof(public11));memset(counts10,0,sizeof(counts10));memset(hitsCount10,0,sizeof(hitsCount10));
    begin_output9();Operation o=read11(input,seq);opcode9=o.code;fixture11=profile11==6?guardSeedApplied10:profile11==7&&(o.code==51||o.code==52||o.code==64);population9(&o);execute11(&o);hits10(&o);public_sleep11(&o);world10_dump();private_sleep11();
    if(OBS){printf("I10 %d %"PRIu32,id,seq);for(int j=0;j<6;++j)word(counts10[j]);putchar('\n');printf("I11 %d %"PRIu32,id,seq);for(int j=0;j<11;++j)word(count11[j]);putchar('\n');}
    printf("Z10 %d %"PRIu32,id,seq);for(int j=0;j<4;++j)word(hitsCount10[j]);word(completed10);putchar('\n');printf("Z11 %d %"PRIu32,id,seq);word(public11[0]);word(public11[1]);word(positive11);putchar('\n');commit10();
}
#include "kontrola-sen-guard.h"
int main(int argc,char** argv)
{
    if(argc!=2)fail("INPUT_DOMAIN");FILE* input=fopen(argv[1],"rb");if(!input)fail("INPUT_DOMAIN");char* p=row(input);
    if(!strncmp(p,"GUARD11 ",8)){arity10(p,2);p+=8;uint32_t n=decimal(&p);if(*p)fail("INPUT_ARITY");if(n!=1)fail("INPUT_N");profile11=6;return guard_main11(input);}
    bool component=!strncmp(p,"COMPONENT11 ",12);if(!component&&strncmp(p,"PORT11 ",7))fail("INPUT_TAG");profile11=component?7:5;arity10(p,2);p+=component?12:7;uint32_t n=decimal(&p);if(*p)fail("INPUT_ARITY");if(n<1||n>(component?16:(int)(sizeof(limits10)/sizeof(limits10[0]))))fail("INPUT_N");printf("%s %"PRIu32"\n",component?"COMPONENT11":"PORT11",n);
    for(int id=1;id<=(int)n;++id){reset_case10();positive11=0;case9=id;p=row(input);if(strncmp(p,"C ",2))fail("INPUT_TAG");arity10(p,3);p+=2;uint32_t actual=decimal(&p);space(&p);uint32_t count=decimal(&p);if(*p)fail("INPUT_ARITY");if(actual!=(uint32_t)id)fail("INPUT_ID");if(!count||count>(uint32_t)(component?64:limits10[id-1][3]))fail("INPUT_OPCOUNT");printf("CASE %d %"PRIu32"\n",id,count);
        for(uint32_t seq=1;seq<=count;++seq)run_row11(input,seq);
        if(phase9)fail("INPUT_PHASE");printf("ENDCASE %d\n",id);for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);
    }if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input)||fclose(input))fail("INPUT_DOMAIN");printf("END %"PRIu32"\n",n);free_tokens();return ferror(stdout)||fflush(stdout)?2:0;
}
