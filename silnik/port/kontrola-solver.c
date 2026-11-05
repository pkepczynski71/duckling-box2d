                                                                           
                                                                              
                                                                                
#include "kontrola-solver10.h"
#include "solver-limity10.inc"
static int bound10(int field);
#define main port9_main
#define GUARD8 0
#include "solver-base10.inc"
#undef main
#include "contact_solver.h"
static bool guardMode10,guardSeedApplied10;
static int bound10(int field){static const int guardBounds[]={8,16,8};return guardMode10?guardBounds[field]:limits10[case9-1][field];}
static bool body_blocks_fit10(uint64_t count);
static bool contact_blocks_fit10(uint64_t count);
static bool checked_sum10(uint64_t count,uint64_t added,uint64_t* value);
typedef struct Hit10 {Number9 a,b;b2Vec2 point,normal;float speed;} Hit10;
typedef struct Hits10 {int count;Hit10 values[CONTACTS9+1];} Hits10;
static Hits10 hitCopies10[4],stepHits10[WORLDS];
static uint64_t stepHitOwner10[WORLDS];
static Hits10 capture_hits10(int owner);
static uint32_t counts10[6],hitsCount10[4],completed10;
static uint32_t componentCounts10[7];
static int observedWorld10,componentMode10;
uint32_t port10Bits(float value){return to_bits(value);}
bool port10Observe(void){return OBS||componentMode10;}
void port10Record(const char* tag,const int* prefix,int np,const uint32_t* words,int nw)
{
    if(!port10Observe())return;
    printf("%s %d",tag,case9);
    if(strcmp(tag,"FH10")&&strcmp(tag,"FM10"))printf(" %"PRIu32" %d",seq9,observedWorld10);
    for(int j=0;j<np;++j)printf(" %d",prefix[j]);
    for(int j=0;j<nw;++j)word(words[j]);putchar('\n');
    const char* tags[]={"W10","CX10","SB10","PK10","SC10","BV10"};
    for(int j=0;j<6;++j)if(!strcmp(tag,tags[j]))++counts10[j];
    const char* ctags[]={"", "SC10", "BV10", "SB10", "PK10", "FH10", "FM10"};
    for(int j=1;j<7;++j)if(!strcmp(tag,ctags[j]))++componentCounts10[j];
}
extern void port10OriginalCreateContact(b2World*,b2Shape*,b2Shape*);
void b2CreateContact(b2World* w,b2Shape* a,b2Shape* b)
{
    port10OriginalCreateContact(w,a,b);                                                      
    port10Created(w,a->id,b->id);
}
void port10Created(b2World* w,int a,int b)
{
    int contact=find_contact9(w,a,b);if(contact<0)return;
    b2Contact* c=w->contacts.data+contact;int owner=owner9(w);
    uint64_t ticket;if(!ticket_next(lastIssued,&ticket))fail("INPUT_DOMAIN");
    lastIssued=ticket;meta9[owner].birth[contact]=ticket;meta9[owner].rolling[contact]=false;
    for(int j=0;j<nr9;++j){Request9* r=requests9+j;
        if((r->a==a&&r->b==b)||(r->a==b&&r->b==a)){
            r->created=1;r->id=contact;r->ca=c->shapeIdA;r->cb=c->shapeIdB;break;}}
}
static void reset_extra10(void)
{
    memset(&extra,0,sizeof(extra));extra.copy=extra.listBody=extra.parentShape=-1;
}
static int step10(const Operation* o)
{
    const uint32_t* a=o->u;int owner=(int)a[0],n;memcpy(&n,a+2,4);float dt=o->f[1];
    extra.k=1;extra.world=owner;extra.dt=a[1];extra.requested=a[2];active9=owner;
    if(!worlds[owner].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    if(!world_live(worlds+owner))return STALE;
    if(o->code==32&&!valid_step(dt,n))return PARAM;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);
    if(o->code==31&&!isfinite(dt)&&dt>0&&w->solverSets.data[b2_awakeSet].bodySims.count)fail("INPUT_DOMAIN");
    if(o->code==32&&dt>0&&!body_blocks_fit10((uint64_t)w->solverSets.data[b2_awakeSet].bodySims.count))return LIMIT;
    if(dt!=0){
        int capacity=w->broadPhase.movePairCapacity,index=b2AtomicLoadInt(&w->broadPhase.movePairIndex);
        b2ShapeId x=b2_nullShapeId,y=b2_nullShapeId;
        port9Prepare(w,&x,&y,true);uint64_t needed=0,upper=0;
        for(int j=0;j<nr9;++j)needed+=requests9[j].kind>=0;
        bool fits=checked_sum10((uint64_t)b2GetIdCount(&w->contactIdPool),needed,&upper);
        if(!fits||UINT64_MAX-lastIssued<needed||(o->code==32&&dt>0&&!contact_blocks_fit10(upper))){
            w->broadPhase.movePairCapacity=capacity;b2AtomicStoreInt(&w->broadPhase.movePairIndex,index);return LIMIT;
        }
        nr9=0;
    }
    meta9[owner].nb=0;observedWorld10=owner;
    b2World_Step(worlds[owner].raw,dt,n);++completed10;
    meta9[owner].ne[w->endEventArrayIndex]=0;
    stamp9();
                                                                                
                                                                      
    stepHits10[owner]=capture_hits10(owner);stepHitOwner10[owner]=worlds[owner].birth;
    extra.effective=dt==0?0:n>0?n:1;extra.didSolve=dt>0;
    b2BodyEvents events=b2World_GetBodyEvents(worlds[owner].raw);
    if(events.moveCount<0||events.moveCount>BODIES)fail("INPUT_POPULATION");
    extra.moves=events.moveCount;
    for(int j=0;j<events.moveCount;++j)extra.events[j]=events.moveEvents[j];
    if(o->code==32){int dest=(int)a[3];MoveCopy* copy=copies+dest;
        copy->saved=true;copy->count=events.moveCount;
        for(int j=0;j<events.moveCount;++j){b2BodyMoveEvent e=events.moveEvents[j];
            copy->moves[j].body=public_body_number(e.bodyId);copy->moves[j].transform=e.transform;
            copy->moves[j].fellAsleep=e.fellAsleep;copy_object(copy->moves[j].object,e.userData);}
        extra.copy=dest;}
    return OK;
}
static Hits10 capture_hits10(int owner)
{
    Hits10 result={0};b2ContactEvents e=b2World_GetContactEvents(worlds[owner].raw);
    if(e.hitCount<0||e.hitCount>CONTACTS9)fail("INPUT_POPULATION");result.count=e.hitCount;
    for(int j=0;j<e.hitCount;++j){b2ContactHitEvent h=e.hitEvents[j];
        result.values[j]=(Hit10){shape_number9(h.shapeIdA),shape_number9(h.shapeIdB),h.point,h.normal,h.approachSpeed};}
    return result;
}
static Hits10 get_hits10(int owner)
{
    Hits10 empty={0};
    if(stepHitOwner10[owner]!=worlds[owner].birth)return empty;
    if(stepHits10[owner].count!=b2World_GetContactEvents(worlds[owner].raw).hitCount)fail("INPUT_DOMAIN");
    return stepHits10[owner];
}
static bool valid_solver_world10(const Operation* o)
{
    for(int j=2;j<=9;++j)if(!isfinite(o->f[j])||(j>=5&&o->f[j]<0))return false;
    return o->f[4]>0;
}
static int solver_world10(const Operation* o)
{
    const uint32_t* a=o->u;int slot=(int)a[0];
    if(worlds[slot].live)fail("INPUT_REGISTER_COLLISION");
    if(a[1]&&!valid_solver_world10(o))return PARAM;
    b2WorldDef d=b2DefaultWorldDef();d.gravity=(b2Vec2){o->f[2],o->f[3]};d.maximumLinearSpeed=o->f[4];
    d.contactHertz=o->f[5];d.contactDampingRatio=o->f[6];d.maxContactPushSpeed=o->f[7];
    d.restitutionThreshold=o->f[8];d.hitEventThreshold=o->f[9];d.enableSleep=false;d.enableContinuous=false;
    d.workerCount=1;d.enqueueTask=port9Enqueue;d.finishTask=port9Finish;
    int status=create_world(slot,d);
    if(!status){b2World_EnableWarmStarting(worlds[slot].raw,a[10]!=0);metadataOwner9[slot]=worlds[slot].birth;memset(meta9+slot,0,sizeof(Meta9));}
    return status;
}
static void execute10(const Operation* o)
{
    int code=(int)o->code,status=0,kind=0,slot=(int)o->u[0];reset_extra10();
    if(code==31||code==32){kind=1;status=step10(o);extra.status=status;}
    else if(code==54){status=solver_world10(o);kind=status?0:1;}
    else if(code==55){kind=1;status=world_live(worlds+slot)?OK:STALE;if(!status)b2World_EnableWarmStarting(worlds[slot].raw,o->u[1]!=0);}
    else{
        if(code==49&&world_live(worlds+slot))hitCopies10[o->u[1]]=get_hits10(slot);
        if(code>=40)execute9(case9,seq9,o);else execute(case9,seq9,o);
        return;
    }
    population_after9();echo(case9,seq9,o);result(case9,seq9,0,status,kind,slot);dump(case9,seq9,1,0,0,-1);
}
static void hit_number10(Hit10 h)
{
    number9(h.a);number9(h.b);vec(h.point);vec(h.normal);real(h.speed);
}
static void hits10(const Operation* o)
{
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2ContactEvents e=b2World_GetContactEvents(worlds[owner].raw);
        if(stepHitOwner10[owner]!=worlds[owner].birth){stepHits10[owner]=(Hits10){0};stepHitOwner10[owner]=worlds[owner].birth;}
        printf("HN10 %d %"PRIu32" %d",case9,seq9,owner);word((uint32_t)e.hitCount);putchar('\n');++hitsCount10[0];
        for(int j=0;j<e.hitCount;++j){b2ContactHitEvent h=e.hitEvents[j];
            printf("HR10 %d %"PRIu32" %d %d",case9,seq9,owner,j);
            word((uint32_t)h.shapeIdA.index1);word(h.shapeIdA.world0);word(h.shapeIdA.generation);
            word((uint32_t)h.shapeIdB.index1);word(h.shapeIdB.world0);word(h.shapeIdB.generation);
            vec(h.point);vec(h.normal);real(h.approachSpeed);putchar('\n');++hitsCount10[1];}}
    for(int k=0;k<4;++k){bool refusal=o->code==49&&(int)o->u[1]==k&&deadEvents9>=0;
        if(!copies9[k].saved&&!refusal)continue;
        int phases=k==read9&&change9?3:1;
        for(int phase=0;phase<phases;++phase){Hits10 h=hitCopies10[k];if(refusal)h.count=0;
            if(phase==1&&h.count){int count=h.count;h.values[count]=h.values[0];
                if(count>=2){Hit10 swap=h.values[0];h.values[0]=h.values[1];h.values[1]=swap;}
                h.values[0].a.birth^=UINT64_C(1);h.values[0].point.x=from_bits(to_bits(h.values[0].point.x)^UINT32_C(0x80000000));++h.count;}
            printf("HC10 %d %"PRIu32" %d %d",case9,seq9,k,phase);word(refusal?STALE:OK);word((uint32_t)h.count);putchar('\n');++hitsCount10[2];
            for(int j=0;j<h.count;++j){printf("HG10 %d %"PRIu32" %d %d %d",case9,seq9,k,phase,j);hit_number10(h.values[j]);putchar('\n');++hitsCount10[3];}}}
}
static void world10_dump(void)
{
    if(!OBS)return;
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2World* w=b2GetWorldFromId(worlds[owner].raw);observedWorld10=owner;
        uint32_t words[]={to_bits(w->contactHertz),to_bits(w->contactDampingRatio),to_bits(w->maxContactPushSpeed),
            to_bits(w->restitutionThreshold),to_bits(w->hitEventThreshold),to_bits(w->contactSpeed),w->enableWarmStarting,w->enableSpeculative};
        port10Record("W10",NULL,0,words,8);}
}
static const char* groups10[]={"E","R","V","W","B","S/G","L/A","Q","QGN/QG","SB","K/M/MCN/MC","CD",
    "NC9","RC9","GV","GL","GE","GC","HN10/HR10","HC10/HG10","X","P","T","F","U","H","Y","DN","RT","JW",
    "RQ","CP","CF","CT","CA","CS","GB","CB","BL9","IP","IF","IS","IL","EB","EE0","EE1","EN9",
    "W10","CX10","SB10","PK10","SC10","BV10","I8","I9","I10","Z8","Z9","Z10"};
static int rank10(const char* tag)
{
    for(int j=0;j<(int)(sizeof(groups10)/sizeof(*groups10));++j){const char* p=groups10[j];size_t n=strlen(tag);
        while(*p){const char* e=strchr(p,'/');size_t size=e?(size_t)(e-p):strlen(p);if(size==n&&!strncmp(tag,p,n))return j;if(!e)break;p=e+1;}}
    return -1;
}
typedef struct Row10 {char* text;int rank,ordinal;} Row10;
static int row_order10(const void* a,const void* b)
{
    const Row10* x=a;const Row10* y=b;return x->rank!=y->rank?x->rank-y->rank:x->ordinal-y->ordinal;
}
static void output_line10(char* text)
{
    char* tokens[4096];int count=0;char* next=NULL;
    for(char* p=strtok_r(text," ",&next);p;p=strtok_r(NULL," ",&next)){if(count==4096)fail("INPUT_DOMAIN");tokens[count++]=p;}
    if(!count)return;
    for(int i=0;i<count;++i){if(i)fputc(' ',stdout);
        bool replacement=false;uint32_t value=0;
        if(!strcmp(tokens[0],"Z9")&&i==15){replacement=true;value=guardMode10?4:3;}
        if(!strcmp(tokens[0],"Z9")&&i==16){replacement=true;value=guardMode10&&guardSeedApplied10;}
        if(!strcmp(tokens[0],"I9")&&(i==20||i==21)){replacement=true;value=0;}
        if((!strcmp(tokens[0],"GE")||!strcmp(tokens[0],"GC"))&&count==11&&i==10){
            int owner=atoi(tokens[3]),phase=atoi(tokens[4]);replacement=true;
            if(tokens[0][1]=='E')value=owner==deadEvents9?0:(uint32_t)b2World_GetContactEvents(worlds[owner].raw).hitCount;
            else value=(uint32_t)(hitCopies10[owner].count+(phase==1&&hitCopies10[owner].count>0));}
        if(replacement)fprintf(stdout,"%08"PRIx32,value);else fputs(tokens[i],stdout);}
    fputc('\n',stdout);
}
static void commit10(void)
{
    bool bad=ferror(output9)!=0;if(fclose(output9))bad=true;output9=NULL;if(bad)fail("INPUT_DOMAIN");
    size_t capacity=128,count=0;Row10* rows=malloc(capacity*sizeof(*rows));if(!rows)fail("INPUT_DOMAIN");
    char* p=outputBytes9;
    while(p&&*p){char* end=strchr(p,'\n');if(!end)fail("INPUT_DOMAIN");*end=0;
        char tag[32];if(sscanf(p,"%31s",tag)!=1)fail("INPUT_DOMAIN");int rank=rank10(tag);
        if(!strcmp(tag,"TASK")){p=end+1;continue;}if(rank<0)fail("INPUT_DOMAIN");
        if(count==capacity){capacity*=2;Row10* grown=realloc(rows,capacity*sizeof(*rows));if(!grown)fail("INPUT_DOMAIN");rows=grown;}
        rows[count]=(Row10){p,rank,(int)count};++count;p=end+1;}
    qsort(rows,count,sizeof(*rows),row_order10);
    for(size_t j=0;j<count;++j)output_line10(rows[j].text);
    free(rows);free(outputBytes9);outputBytes9=NULL;outputSize9=0;
    if(ferror(stdout))fail("INPUT_DOMAIN");
}
static void arity10(const char* text,int expected)
{
    int count=1;for(const char* p=text;*p;++p)count+=*p==' ';
    if(count!=expected)fail("INPUT_ARITY");
}
static Operation read10(FILE* input,uint32_t seq)
{
    char* text=row(input);char saved[2050];snprintf(saved,sizeof(saved),"%s\n",text);
    char* p=text;if(strncmp(p,"O ",2))fail("INPUT_TAG");arity10(p,67);p+=2;uint32_t actual=decimal(&p);space(&p);uint32_t code=decimal(&p);
    if(actual!=seq)fail("INPUT_SEQ");
    if(code==41||code==42||code==43||code==44||code==45||(code>=51&&code<=53)||code>55)fail("INPUT_OPCODE");
    if(code<54){FILE* stream=fmemopen(saved,strlen(saved),"r");if(!stream)fail("INPUT_DOMAIN");Operation o=read_operation(stream,seq);fclose(stream);return o;}
    Operation o={0};o.code=code;for(int j=0;j<64;++j){space(&p);o.u[j]=hex_word(&p);o.f[j]=from_bits(o.u[j]);}if(*p)fail("INPUT_ARITY");
    int used=code==54?11:2;for(int j=used;j<64;++j)if(o.u[j])fail("INPUT_UNUSED");
    if(o.u[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");if(o.u[1]>1||(code==54&&o.u[10]>1))fail("INPUT_BOOL");
    if(code==55&&!worlds[o.u[0]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    if(code==54&&!o.u[1])for(int j=2;j<=9;++j)if(!isfinite(o.f[j])||(j>=5&&o.f[j]<0)||(j==4&&o.f[j]<=0))fail("INPUT_DOMAIN");
    return o;
}
static void reset_case10(void)
{
    guardSeedApplied10=false;
    memset(worlds,0,sizeof(worlds));memset(bodies,0,sizeof(bodies));memset(shapes,0,sizeof(shapes));memset(copies,0,sizeof(copies));
    memset(saved9,0,sizeof(saved9));memset(copies9,0,sizeof(copies9));memset(meta9,0,sizeof(meta9));memset(metadataOwner9,0,sizeof(metadataOwner9));
    memset(hitCopies10,0,sizeof(hitCopies10));memset(stepHits10,0,sizeof(stepHits10));memset(stepHitOwner10,0,sizeof(stepHitOwner10));memset(history9,0,sizeof(history9));phase9=0;phaseOwner9=-1;completed10=0;
}
static void run_row10(FILE* input,uint32_t seq)
{
    int id=case9;reset_operation9(id,seq,0);memset(counts10,0,sizeof(counts10));memset(hitsCount10,0,sizeof(hitsCount10));
    begin_output9();Operation o=read10(input,seq);opcode9=o.code;population9(&o);execute10(&o);hits10(&o);world10_dump();
    if(OBS){printf("I10 %d %"PRIu32,id,seq);for(int j=0;j<6;++j)word(counts10[j]);putchar('\n');}
    printf("Z10 %d %"PRIu32,id,seq);for(int j=0;j<4;++j)word(hitsCount10[j]);word(completed10);putchar('\n');commit10();
}
static int guard_main10(FILE* input);
static int component_main10(FILE* input,int count);
int main(int argc,char** argv)
{
    if(argc!=2)fail("INPUT_DOMAIN");FILE* input=fopen(argv[1],"rb");if(!input)fail("INPUT_DOMAIN");
    char* p=row(input);
#ifdef COMPONENT10_MAIN
    if(!strncmp(p,"COMPONENT10 ",12)){arity10(p,2);p+=12;int count=(int)decimal(&p);if(*p)fail("INPUT_ARITY");if(count<1||count>96)fail("INPUT_N");return component_main10(input,count);}
    fail("INPUT_TAG");
#endif
    if(!strncmp(p,"GUARD10 ",8)){arity10(p,2);p+=8;uint32_t n=decimal(&p);if(*p)fail("INPUT_ARITY");if(n!=1)fail("INPUT_N");return guard_main10(input);}
    if(strncmp(p,"PORT10 ",7))fail("INPUT_TAG");arity10(p,2);p+=7;uint32_t count=decimal(&p);if(*p)fail("INPUT_ARITY");if(count<1||count>124)fail("INPUT_N");
    printf("PORT10 %"PRIu32"\n",count);
    for(int id=1;id<=(int)count;++id){reset_case10();case9=id;
        p=row(input);if(strncmp(p,"C ",2))fail("INPUT_TAG");arity10(p,3);p+=2;uint32_t actual=decimal(&p);space(&p);uint32_t ops=decimal(&p);
        if(*p)fail("INPUT_ARITY");if(actual!=(uint32_t)id)fail("INPUT_ID");if(!ops||ops>(uint32_t)limits10[id-1][3])fail("INPUT_OPCOUNT");
        printf("CASE %d %"PRIu32"\n",id,ops);
        for(uint32_t seq=1;seq<=ops;++seq)run_row10(input,seq);
        printf("ENDCASE %d\n",id);for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);}
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input)||fclose(input))fail("INPUT_DOMAIN");
    printf("END %"PRIu32"\n",count);free_tokens();return (ferror(stdout)||fflush(stdout))?2:0;
}
#include "kontrola-solver-component.h"

#include "kontrola-solver-guard.h"
