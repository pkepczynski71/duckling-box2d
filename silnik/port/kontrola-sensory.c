                                                                                      
#define _GNU_SOURCE
#include "sensory-base14.inc"
#include "sensor.h"
#include "ctz.h"
#include "sensory-counts17.inc"

typedef struct Touch17 {uint32_t u[16];} Touch17;
typedef struct Rows17 {bool saved;int count[2];Touch17* list[2];} Rows17;
typedef struct History17 {b2ShapeId raw;uint64_t birth,owner;struct History17* next;} History17;
typedef struct RefHistory17 {int n,oldn;uint32_t current[128][8],old[128][8];uint64_t birth;} RefHistory17;
static History17* history17;
static RefHistory17 refs17[16][512];
static Rows17 eventCopies17[4],overlapCopies17[4],begin17[16];
static int reason17,resultStatus17,listCount17,resultWorld17=-1,resultShape17=-1;
static Touch17 resultList17[128];
static uint32_t trace17[16384][5];static int traceCount17;
static bool freshBegin17[16];static bool changed17[16];static int fullProfile17;static bool diagnostic17;
static int n16;
static uint32_t typedDescription17[16][21];static unsigned typedKind17[16],typedSize17[16];static bool typedSaved17[16];
static int port17LockGate(int wr){if(b2GetWorldFromId(worlds[wr].raw)->locked){reason17=1;reason12=1;return 7;}return 0;}
static int port17PairGate(int wr,int trigger){b2World* w=b2GetWorldFromId(worlds[wr].raw);if(trigger&&w->sensors.count&&w->customFilterFcn){reason17=20;reason12=2;return PARAM;}return 0;}
static int port17InstallGate(int wr,int flag){if(flag&&b2GetWorldFromId(worlds[wr].raw)->sensors.count){reason17=20;reason12=2;return PARAM;}return 0;}

static int wr17(b2World* w){for(int i=0;i<16;i++)if(worlds[i].live&&worlds[i].raw.index1==w->worldId+1)return i;fail("INPUT_DOMAIN");return -1;}
static void clearRows17(Rows17* r){for(int i=0;i<2;i++){free(r->list[i]);r->list[i]=NULL;r->count[i]=0;}r->saved=false;}
static void saveRows17(Rows17* r,const Rows17* in){Rows17 x={.saved=true};for(int i=0;i<2;i++){x.count[i]=in->count[i];if(x.count[i]){x.list[i]=malloc(x.count[i]*sizeof(Touch17));if(!x.list[i])fail("INPUT_DOMAIN");memcpy(x.list[i],in->list[i],x.count[i]*sizeof(Touch17));}}clearRows17(r);*r=x;}
static History17* find17(b2ShapeId raw){for(History17* h=history17;h;h=h->next)if(h->raw.index1==raw.index1&&h->raw.world0==raw.world0&&h->raw.generation==raw.generation)return h;fail("INPUT_DOMAIN");return NULL;}
static void identity17(b2ShapeId raw,uint64_t birth,uint64_t owner,uint32_t* u){u[0]=raw.index1;u[1]=raw.world0;u[2]=raw.generation;u[3]=raw.index1-1;u[4]=birth;u[5]=birth>>32;u[6]=owner;u[7]=owner>>32;}
static void register17(void){for(int r=0;r<512;r++)if(shapes[r].live){Shape s=shapes[r];History17* h=history17;while(h&&h->birth!=s.birth)h=h->next;if(h)continue;h=malloc(sizeof *h);if(!h)fail("INPUT_DOMAIN");*h=(History17){s.raw,s.birth,s.owner,history17};history17=h;int wr=-1;for(int w=0;w<16;w++)if(worlds[w].live&&worlds[w].birth==s.owner)wr=w;if(wr>=0&&s.raw.index1<=512&&b2Shape_IsSensor(s.raw)){RefHistory17* p=&refs17[wr][s.raw.index1-1];p->birth=s.birth;p->n=p->oldn=0;}}}
static void rawIdentity17(b2ShapeId raw,uint32_t* u){History17* h=find17(raw);identity17(raw,h->birth,h->owner,u);}
static void visitor17(int wr,int sid,b2ShapeId raw,bool old,uint32_t* u){RefHistory17* r=&refs17[wr][sid];int n=old?r->oldn:r->n;uint32_t (*a)[8]=old?r->old:r->current;for(int i=0;i<n;i++)if(a[i][0]==(uint32_t)raw.index1&&a[i][2]==raw.generation){memcpy(u,a[i],32);return;}rawIdentity17(raw,u);}
static Touch17 touch17(int wr,b2ShapeId s,b2ShapeId v,bool old){Touch17 t={0};uint32_t a[8],b[8];rawIdentity17(s,a);visitor17(wr,s.index1-1,v,old,b);memcpy(t.u,a,12);memcpy(t.u+3,b,12);memcpy(t.u+6,a+3,20);memcpy(t.u+11,b+3,20);return t;}
extern void port17OriginalOverlapSensors(b2World*);
void b2OverlapSensors(b2World* w){int wr=wr17(w);for(int s=0;s<512;s++){RefHistory17* p=&refs17[wr][s];p->oldn=p->n;memcpy(p->old,p->current,p->n*32);p->n=0;}changed17[wr]=true;port17OriginalOverlapSensors(w);}
void port17Query(b2World* w,int s,int v,int tree,float distance){if(OBS){if(traceCount17>=16384)fail("INPUT_POPULATION");uint32_t* q=trace17[traceCount17++];q[0]=wr17(w);q[1]=s;q[2]=v;q[3]=tree;q[4]=to_bits(distance);}}
static void refresh17(void){register17();for(int wr=0;wr<16;wr++)if(worlds[wr].live&&changed17[wr]){for(int s=0;s<512;s++)if(shapes[s].live&&shapes[s].owner==worlds[wr].birth&&b2Shape_IsSensor(shapes[s].raw)){b2ShapeId raw=shapes[s].raw,list[128];int n=b2Shape_GetSensorOverlaps(raw,list,128);RefHistory17* h=&refs17[wr][raw.index1-1];h->n=n;for(int j=0;j<n;j++)rawIdentity17(list[j],h->current[j]);}changed17[wr]=false;}}
static Rows17 currentEvents17(int wr){b2SensorEvents e=b2World_GetSensorEvents(worlds[wr].raw);Rows17 r={.saved=true,.count={e.beginCount,e.endCount}};for(int l=0;l<2;l++){int n=r.count[l];if(n){r.list[l]=malloc(n*sizeof(Touch17));if(!r.list[l])fail("INPUT_DOMAIN");}for(int j=0;j<n;j++){b2ShapeId s=l?e.endEvents[j].sensorShapeId:e.beginEvents[j].sensorShapeId,v=l?e.endEvents[j].visitorShapeId:e.beginEvents[j].visitorShapeId;r.list[l][j]=(l==0&&begin17[wr].saved&&!freshBegin17[wr]&&j<begin17[wr].count[0])?begin17[wr].list[0][j]:touch17(wr,s,v,l!=0);}}if(!begin17[wr].saved||freshBegin17[wr]){Rows17 cache={.saved=true,.count={r.count[0],0},.list={r.list[0],NULL}};saveRows17(begin17+wr,&cache);freshBegin17[wr]=false;}return r;}
static int access17(int wr,int sr,bool game,bool lock,bool sensor,bool b18){int st=shape_guard(worlds+wr,shapes+sr);if(st)return st;b2World* w=b2GetWorldFromId(worlds[wr].raw);if(game&&lock&&w->locked){reason17=1;return 7;}if(game&&sensor&&!b2Shape_IsSensor(shapes[sr].raw)){reason17=21;return PARAM;}if(game&&b18&&w->sensors.count&&w->customFilterFcn){reason17=20;return PARAM;}return 0;}
static void result17(int code,int status,int reason,int n,const uint32_t* u){printf("R17 %d %"PRIu32" %d %d %d %d",case9,seq9,code,status,reason,n);for(int i=0;i<n;i++)word(status?0:u[i]);putchar('\n');}
static void echo17(const char* tag,const Operation* o,int n){printf("%s %d %"PRIu32" %"PRIu32" %d",tag,case9,seq9,o->code,n);for(int i=0;i<n;i++)word(o->u[i]);putchar('\n');}
static b2ShapeDef shapeDef17(const uint32_t* a){b2ShapeDef d=b2DefaultShapeDef();d.density=from_bits(a[44]);d.material.friction=from_bits(a[45]);d.material.restitution=from_bits(a[46]);d.material.rollingResistance=from_bits(a[47]);d.material.tangentSpeed=from_bits(a[48]);d.material.userMaterialId=a[49];d.filter=(b2Filter){(uint64_t)a[50]|((uint64_t)a[51]<<32),(uint64_t)a[52]|((uint64_t)a[53]<<32),(int32_t)a[54]};d.invokeContactCreation=a[55];d.enableContactEvents=a[56];d.enableHitEvents=a[57];d.isSensor=a[59];d.enableSensorEvents=a[60];d.updateBodyMass=a[61];d.enablePreSolveEvents=a[62];return d;}
static int create17(const Operation* o){const uint32_t* a=o->u;int dst=a[0],wr=a[1],br=a[2];bool game=a[58];int st=guard(worlds+wr,bodies+br);if(st)return st;b2World* w=b2GetWorldFromId(worlds[wr].raw);if(game&&w->locked){reason17=1;return 7;}b2ShapeDef d=shapeDef17(a);if(game&&!valid_material_definition9(d))return PARAM;if(game&&(!isfinite(d.density)||d.density<0||a[3]==4&&!b2IsNormalizedRot((b2Rot){from_bits(a[8]),from_bits(a[9])})))return GEOMETRY;Geometry g;bool valid=game?geometry12(a[3],a+4,&g):raw_geometry12(a[3],a+4,&g);if(!valid)return GEOMETRY;if(game&&!preflight(bodies[br].raw,NULL,&g,d.density,b2_nullShapeId,false,0))return GEOMETRY;if(game&&d.isSensor&&w->customFilterFcn){reason17=20;return PARAM;}uint64_t ticket;if(!ticket_next(lastIssued,&ticket))return LIMIT;b2ShapeId raw=g.type==0?b2CreateCircleShape(bodies[br].raw,&d,&g.circle):g.type==1?b2CreateCapsuleShape(bodies[br].raw,&d,&g.capsule):g.type==2?b2CreateSegmentShape(bodies[br].raw,&d,&g.segment):b2CreatePolygonShape(bodies[br].raw,&d,&g.polygon);if(B2_IS_NULL(raw))return GEOMETRY;shapes[dst]=(Shape){true,true,raw,worlds[wr].birth,ticket};lastIssued=ticket;register17();return 0;}
static void outputRows17(int source,int bank,int list,int sid,int count,const Touch17* data,int n,int* total){printf("L17 %d %"PRIu32" %d %d %d %d %d\n",case9,seq9,source,bank,list,sid,count);for(int j=0;j<count;j++){printf("T17 %d %"PRIu32" %d %d %d %d %d %d",case9,seq9,source,bank,list,sid,j,n);for(int k=0;k<n;k++)word(data[j].u[k]);putchar('\n');++*total;}}
static void observe17(const Operation* op){int total=0;for(int wr=0;wr<16;wr++)if(worlds[wr].live){int sensors=0;b2World* w=OBS?b2GetWorldFromId(worlds[wr].raw):NULL;for(int r=0;r<512;r++)if(shapes[r].live&&shapes[r].owner==worlds[wr].birth){b2ShapeId s=shapes[r].raw;printf("V17 %d %"PRIu32" %d %d 2",case9,seq9,wr,s.index1-1);word(b2Shape_IsSensor(s));word(b2Shape_AreSensorEventsEnabled(s));putchar('\n');sensors+=b2Shape_IsSensor(s);}
 Rows17 e=currentEvents17(wr);outputRows17(0,wr,0,0,e.count[0],e.list[0],16,&total);outputRows17(0,wr,1,0,e.count[1],e.list[1],16,&total);clearRows17(&e);
 Shape* bySlot17[512]={0};for(int r=0;r<512;r++)if(shapes[r].live&&shapes[r].owner==worlds[wr].birth&&b2Shape_IsSensor(shapes[r].raw))bySlot17[shapes[r].raw.index1-1]=shapes+r;for(int sid=0;sid<512;sid++){Shape* s=bySlot17[sid];if(!s)continue;b2ShapeId ids[128];Touch17 items[128];int n=b2Shape_GetSensorOverlaps(s->raw,ids,128);for(int j=0;j<n;j++)visitor17(wr,sid,ids[j],false,items[j].u);outputRows17(0,wr,2,sid,n,items,8,&total);}
 if(OBS){for(int i=0;i<w->sensors.count;i++){b2Sensor* s=w->sensors.data+i;printf("U17 %d %"PRIu32" %d %d 0 0 3",case9,seq9,wr,i);word(s->shapeId);word(s->overlaps1.count);word(s->overlaps2.count);putchar('\n');for(int g=1;g<=2;g++){b2ShapeRefArray* a=g==1?&s->overlaps1:&s->overlaps2;for(int j=0;j<a->count;j++){b2ShapeRef r=a->data[j];uint32_t u[8];b2ShapeId raw={r.shapeId+1,w->worldId,r.generation};visitor17(wr,s->shapeId,raw,g==1,u);printf("U17 %d %"PRIu32" %d %d %d %d 4",case9,seq9,wr,i,g,j);word(r.shapeId);word(r.generation);word(u[4]);word(u[5]);putchar('\n');}}}
 b2BitSet* bits=&w->sensorTaskContexts.data[0].eventBits;for(int j=0;j<bits->blockCount;j++){printf("U17 %d %"PRIu32" %d 0 3 %d 2",case9,seq9,wr,j);wide(bits->bits[j]);putchar('\n');}
 for(int side=0;side<2;side++)for(int j=0;j<w->sensorEndEvents[side].count;j++){b2SensorEndTouchEvent r=w->sensorEndEvents[side].data[j];Touch17 t=touch17(wr,r.sensorShapeId,r.visitorShapeId,true);printf("U17 %d %"PRIu32" %d 0 %d %d 16",case9,seq9,wr,4+side,j);for(int k=0;k<16;k++)word(t.u[k]);putchar('\n');}}
 printf("W16 %d %"PRIu32" %d 1",case9,seq9,wr);word(b2World_IsContinuousEnabled(worlds[wr].raw));putchar('\n');
 }
 if(resultWorld17>=0)outputRows17(1,0,2,resultShape17,listCount17,resultList17,8,&total);
 for(int k=0;k<4;k++){if(eventCopies17[k].saved){for(int l=0;l<2;l++)outputRows17(2,k,l,0,eventCopies17[k].count[l],eventCopies17[k].list[l],16,&total);}if(overlapCopies17[k].saved)outputRows17(2,k,2,0,overlapCopies17[k].count[0],overlapCopies17[k].list[0],8,&total);}
 for(int wr=0;wr<16;wr++)if(worlds[wr].live){int count=0;for(int r=0;r<512;r++)if(shapes[r].live&&shapes[r].owner==worlds[wr].birth)count+=b2Shape_IsSensor(shapes[r].raw);printf("W17 %d %"PRIu32" %d 8",case9,seq9,wr);word(count);word(b2World_GetSensorEvents(worlds[wr].raw).beginCount);if(OBS){b2World* w=b2GetWorldFromId(worlds[wr].raw);word(w->sensorEndEvents[0].count);word(w->sensorEndEvents[1].count);word(w->endEventArrayIndex);word(w->sensorTaskContexts.data[0].eventBits.blockCount);int nq=0;for(int i=0;i<traceCount17;i++)nq+=trace17[i][0]==wr;word(nq);word(total);}else for(int j=0;j<6;j++)word(0);putchar('\n');}
 printf("I16 %d %"PRIu32" 8",case9,seq9);word(op->code>=302&&op->code<=305||op->code==308||op->code==309||op->code==312);int worlds16=0;for(int w=0;w<16;w++)worlds16+=worlds[w].live;word(worlds16);for(int k=0;k<5;k++)word(0);word(seq9);putchar(10);
}
static void commit17(void){commit14();}
static void churnTrace17(unsigned j,int phase,int reg,int old,int parent,int wr)
{
    printf("J %d %"PRIu32" %u %d",case9,seq9,j,phase);shape_handle(shapes[reg]);
    word(b2Shape_IsValid(shapes[old].raw));word(shape_live(shapes+old));
    word(b2World_GetCounters(worlds[wr].raw).shapeCount);word(b2Body_GetShapeCount(bodies[parent].raw));
    mass(b2Body_GetMassData(bodies[parent].raw));putchar('\n');
}
static void churnWork17(const Operation* o,bool transport)
{
    const uint32_t* a=o->u;int wr=a[0],parent=a[1],reg=a[2],old=a[4];
    if(guard(worlds+wr,bodies+parent)||shapes[reg].live||!shapes[old].saved||shape_live(shapes+old)||shapes[old].owner!=worlds[wr].birth)fail("INPUT_FIXTURE");
    if(transport){echo17("E14",o,64);echoCount14++;}uint32_t n=0,sa[64]={0};sa[0]=reg;sa[1]=wr;sa[2]=parent;
    sa[4]=to_bits(1);sa[5]=sa[6]=sa[7]=1;sa[9]=sa[10]=UINT32_MAX;sa[17]=to_bits(.5f);
    for(unsigned j=1;j<=a[3];j++){
        if(j>1){b2DestroyShape(shapes[reg].raw,true);shapes[reg].live=false;churnTrace17(j,0,reg,old,parent,wr);n++;}
        if(create_shape(reg,wr,parent,sa,false))fail("INPUT_FIXTURE");churnTrace17(j,1,reg,old,parent,wr);n++;
    }
    register17();if(transport){result(case9,seq9,0,0,3,reg);dump(case9,seq9,1,n,0,-1);}
}
static void churn17(const Operation* o){churnWork17(o,true);
}
static void execute17(const Operation* o,int n){const uint32_t* a=o->u;uint32_t value[8]={0};int status=0,size=0;reason17=0;
 if(o->code==308){Operation q={.code=56};memcpy(q.u,a,13*4);q.u[0]=a[1];q.u[1]=a[0];for(int j=0;j<64;j++)q.f[j]=from_bits(q.u[j]);status=solver_world10(&q);if(!status){b2World_EnableSleeping(worlds[a[1]].raw,a[11]);b2World_EnableContinuous(worlds[a[1]].raw,a[12]);sync_hooks12();value[0]=worlds[a[1]].raw.index1-1;value[1]=worlds[a[1]].birth;value[2]=worlds[a[1]].birth>>32;}size=3;}
 else if(o->code==309){b2BodyDef d=body11(o);d.isEnabled=a[19];d.isBullet=a[56];if(!world_live(worlds+a[0]))status=STALE;else if(a[2]&&b2GetWorldFromId(worlds[a[0]].raw)->locked)status=7;else if(!valid_body11(&d))status=PARAM;else {char name[33]={0};for(int j=0;j<a[20];j++)name[j]=a[21+j];d.name=name;d.userData=token(a[53],a[54],a[55]);status=create_body(a[1],a[0],d);}if(!status){Body b=bodies[a[1]];value[0]=b.raw.index1-1;value[1]=b.birth;value[2]=b.birth>>32;value[3]=b.owner;value[4]=b.owner>>32;}size=5;}
 else if(o->code==312){int r=a[0];typedSaved17[r]=true;typedKind17[r]=a[1];typedSize17[r]=n-2;memcpy(typedDescription17[r],a+2,(n-2)*4);if(!a[1]){descriptions14[r]=true;memcpy(definition14[r],a+2,18*4);}size=0;}
 else if(o->code>=302&&o->code<=305){int wr=a[1];if(!world_live(worlds+wr))status=STALE;else if(o->code<=303)status=guard(worlds+wr,bodies+a[2]);if(!status){if(o->code==302)b2Body_SetBullet(bodies[a[2]].raw,a[3]);if(o->code==303)value[0]=b2Body_IsBullet(bodies[a[2]].raw);if(o->code==304)b2World_EnableContinuous(worlds[wr].raw,a[2]);if(o->code==305)value[0]=b2World_IsContinuousEnabled(worlds[wr].raw);}size=o->code==303||o->code==305;}
 else if(o->code==400){status=create17(o);size=8;if(!status)rawIdentity17(shapes[a[0]].raw,value);}
 else if(o->code==401){status=access17(a[1],a[2],a[0],true,false,false);if(!status)b2Shape_EnableSensorEvents(shapes[a[2]].raw,a[3]);}
 else if(o->code==402){size=1;status=access17(a[1],a[2],a[0],a[3]==2,a[3]==2,a[3]==2);if(!status)value[0]=a[3]==0?b2Shape_IsSensor(shapes[a[2]].raw):a[3]==1?b2Shape_AreSensorEventsEnabled(shapes[a[2]].raw):b2Shape_GetSensorCapacity(shapes[a[2]].raw);}
 else if(o->code==403||o->code==405){int wr=o->code==405?a[0]:a[1],sr=o->code==405?a[1]:a[2];bool game=o->code==405||a[0];status=access17(wr,sr,game,true,true,true);if(!status){b2ShapeId ids[128];int cap=game?128:(int)a[3];if(cap>128)cap=128;listCount17=b2Shape_GetSensorOverlaps(shapes[sr].raw,ids,cap);for(int j=0;j<listCount17;j++)visitor17(wr,shapes[sr].raw.index1-1,ids[j],false,resultList17[j].u);if(o->code==403){resultWorld17=wr;resultShape17=shapes[sr].raw.index1-1;value[0]=listCount17;}else{Rows17 r={.saved=true,.count={listCount17,0},.list={resultList17,NULL}};saveRows17(overlapCopies17+a[2],&r);}}size=o->code==403?1:0;}
 else if(o->code==404){if(!world_live(worlds+a[1]))status=STALE;else {b2World* w=b2GetWorldFromId(worlds[a[1]].raw);if(a[0]&&w->locked){status=7;reason17=1;}else if(a[0]&&w->sensors.count&&w->customFilterFcn){status=PARAM;reason17=20;}else{Rows17 r=currentEvents17(a[1]);saveRows17(eventCopies17+a[2],&r);clearRows17(&r);}}}
 else if(o->code==406){}
 else if(o->code==407){Rows17* r=a[0]?overlapCopies17+a[1]:eventCopies17+a[1];int list=a[0]?0:a[2];r->list[list][a[3]].u[a[4]]=a[5];}
 else if(o->code==408){b2ShapeRef x={(int)a[1],(uint16_t)a[2]},y={(int)a[3],(uint16_t)a[4]};extern int port17Compare(const void*,const void*);value[0]=port17Compare(&x,&y);size=1;}
 else if(o->code==409){b2ShapeDef d=b2DefaultShapeDef();if(a[0]){d.density=0;d.isSensor=true;d.enableSensorEvents=true;}value[0]=to_bits(d.density);value[1]=d.isSensor;value[2]=d.enableSensorEvents;value[3]=d.enableContactEvents;value[4]=d.enableHitEvents;value[5]=d.enablePreSolveEvents;size=6;}
 else fail("INPUT_OPCODE");
 echo17(o->code>=400?"E17":"E16",o,n);if(o->code>=400)result17(o->code,status,reason17,size,value);else{printf("R16 %d %"PRIu32" %"PRIu32" %d 0 %d",case9,seq9,o->code,status,size);for(int j=0;j<size;j++)word(status?0:value[j]);putchar('\n');}
 status14=status;population_after9();dump(case9,seq9,0,0,0,-1);
}
static Operation read17(FILE* in,unsigned seq,int* n){char* text=row(in);char saved[2052];snprintf(saved,sizeof saved,"%s\n",text);char* p=text;if(strncmp(p,"O ",2))fail("INPUT_TAG");p+=2;unsigned actual=decimal13(&p);space(&p);unsigned code=decimal13(&p);if(actual!=seq)fail("INPUT_SEQ");
 if((code<200&&code!=20)||(code>=200&&code<=212)){Input14 replay={saved,0,strlen(saved),in};cookie_io_functions_t io={.read=input14Read};FILE* f=fopencookie(&replay,"r",io);setvbuf(f,NULL,_IONBF,0);Operation o=read14(f,seq);fclose(f);*n=64;return o;}
 Operation o={.code=code};unsigned count=64;if(code>=200){space(&p);count=decimal13(&p);}if(count>64)fail("INPUT_ARITY");arity13(text,(code>=200?4:3)+count,"INPUT_ARITY");for(unsigned j=0;j<count;j++){space(&p);o.u[j]=hex_word(&p);o.f[j]=from_bits(o.u[j]);}if(*p)fail("INPUT_ARITY");*n=count;
 int needs[]={63,4,4,4,3,3,2,6,5,1};if(code>=400&&code<=409){if(count!=needs[code-400])fail("INPUT_ARITY");}
 else if(code==308){if(count!=13)fail("INPUT_ARITY");}
 else if(code==309){if(count!=57)fail("INPUT_ARITY");}
 else if(code==312){if(count<2)fail("INPUT_ARITY");if(o.u[1]>7)fail("INPUT_ENUM");static const unsigned size[8]={18,3,10,9,21,20,13,19};if(count!=2+size[o.u[1]])fail("INPUT_ARITY");if(o.u[0]>=16)fail("INPUT_REGISTER_RANGE");}
 else if(code>=302&&code<=305){static const unsigned size[4]={4,3,3,2};if(count!=size[code-302])fail("INPUT_ARITY");if(o.u[0]>1)fail("INPUT_MODE");if(o.u[1]>=16)fail("INPUT_REGISTER_RANGE");if(!worlds[o.u[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(code<=303){if(o.u[2]>=256)fail("INPUT_REGISTER_RANGE");if(!bodies[o.u[2]].saved)fail("INPUT_REGISTER_UNINITIALIZED");}if((code==302&&o.u[3]>1)||(code==304&&o.u[2]>1))fail("INPUT_BOOL");}
 else if(code!=20)fail("INPUT_OPCODE");
 uint32_t* a=o.u;
 if(code==308){if(a[0]>1)fail("INPUT_MODE");if(a[1]>=16)fail("INPUT_REGISTER_RANGE");if(worlds[a[1]].live)fail("INPUT_REGISTER_COLLISION");int live=0;for(int w=0;w<16;w++)live+=worlds[w].live;if(live>=2)fail("INPUT_POPULATION");for(int j=10;j<=12;j++)if(a[j]>1)fail("INPUT_BOOL");if(!a[0]){for(int j=2;j<10;j++)if(!isfinite(o.f[j]))fail("INPUT_DOMAIN");if(!(o.f[4]>0))fail("INPUT_DOMAIN");}}
 if(code==309){Operation q=o;q.code=90;q.u[56]=0;validate_new12(&q,true);if(a[56]>1)fail("INPUT_BOOL");if(!a[2]&&!valid_body11(&(b2BodyDef){.type=a[3],.position={o.f[4],o.f[5]},.rotation={o.f[6],o.f[7]},.linearVelocity={o.f[8],o.f[9]},.angularVelocity=o.f[10],.linearDamping=o.f[11],.angularDamping=o.f[12],.gravityScale=o.f[13],.sleepThreshold=o.f[18]}))fail("INPUT_DOMAIN");}
 if(code==400){if(a[0]>=512||a[1]>=16||a[2]>=256)fail("INPUT_REGISTER_RANGE");if(!worlds[a[1]].saved||!bodies[a[2]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(shape_live(shapes+a[0]))fail("INPUT_REGISTER_COLLISION");if(a[3]>4)fail("INPUT_ENUM");for(int j=55;j<=62;j++)if(a[j]>1)fail(j==58?"INPUT_MODE":"INPUT_BOOL");if(a[58]&&!a[61])fail("INPUT_PROFILE");int used=a[3]==0?3:a[3]==1?5:a[3]==2?4:a[3]==4?7:a[4]<=8?2+2*a[4]:40;for(int j=used;j<40;j++)if(a[4+j])fail("INPUT_UNUSED");if(!a[58]){Geometry g;if(!raw_geometry12(a[3],a+4,&g)||!valid_material_definition9(shapeDef17(a))||!isfinite(o.f[44])||o.f[44]<0||guard(worlds+a[1],bodies+a[2]))fail("INPUT_DOMAIN");}}
 if(code>=401&&code<=403){if(a[0]>1)fail("INPUT_MODE");if(a[1]>=16||a[2]>=512)fail("INPUT_REGISTER_RANGE");if(!worlds[a[1]].saved||!shapes[a[2]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(code==401&&a[3]>1)fail("INPUT_BOOL");if(code==402&&a[3]>2)fail("INPUT_ENUM");if(code==403&&((int32_t)a[3]<0||a[0]&&a[3]))fail("INPUT_DOMAIN");}
 if(code>=401&&code<=403&&!a[0]&&shape_guard(worlds+a[1],shapes+a[2]))fail("INPUT_DOMAIN");
 if(code==404){if(a[0]>1)fail("INPUT_MODE");if(a[1]>=16||a[2]>=4)fail("INPUT_REGISTER_RANGE");if(!worlds[a[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(!a[0]&&!world_live(worlds+a[1]))fail("INPUT_DOMAIN");}
 if(code==405){if(a[0]>=16||a[1]>=512||a[2]>=4)fail("INPUT_REGISTER_RANGE");if(!worlds[a[0]].saved||!shapes[a[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");}
 if(code==406||code==407){if(a[0]>1)fail("INPUT_ENUM");if(a[1]>=4)fail("INPUT_REGISTER_RANGE");Rows17* r=a[0]?overlapCopies17+a[1]:eventCopies17+a[1];if(!r->saved)fail("INPUT_COPY");if(code==407){if(a[2]!=(a[0]?2:0)&&(!(!a[0]&&a[2]==1)))fail("INPUT_ENUM");int l=a[0]?0:a[2];if(a[3]>=(uint32_t)r->count[l]||a[4]>=(a[0]?8u:16u))fail("INPUT_COPY");if(r->list[l][a[3]].u[a[4]]==a[5])fail("INPUT_DOMAIN");}}
 if(code==408){if(fullProfile17!=1)fail("INPUT_PROFILE");if(a[0])fail("INPUT_FIXTURE");if((int32_t)a[1]<0||(int32_t)a[3]<0||a[2]>65535||a[4]>65535)fail("INPUT_DOMAIN");}
 if(code==20){if(fullProfile17==0)fail("INPUT_PROFILE");if(a[0]>=16||a[1]>=256||a[2]>=512||a[4]>=512)fail("INPUT_REGISTER_RANGE");if(a[2]==a[4]||!a[3]||a[3]>65536)fail("INPUT_DOMAIN");for(int j=5;j<64;j++)if(a[j])fail("INPUT_UNUSED");}
 if(code==409&&a[0]>1)fail("INPUT_ENUM");
 return o;}
static void reset17(int id){resetCase14(id);memset(typedSaved17,0,sizeof typedSaved17);memset(refs17,0,sizeof refs17);for(int k=0;k<4;k++){clearRows17(eventCopies17+k);clearRows17(overlapCopies17+k);}while(history17){History17* p=history17;history17=p->next;free(p);}memset(changed17,0,sizeof changed17);memset(freshBegin17,0,sizeof freshBegin17);for(int w=0;w<16;w++)clearRows17(begin17+w);}
#include "kontrola-sensory-guard.h"
int main(int argc,char** argv){FILE* in=stdin;for(int i=1;i<argc;i++){if(!strcmp(argv[i],"--diagnostic"))diagnostic17=true;else if(in==stdin){in=fopen(argv[i],"rb");if(!in)fail("INPUT_DOMAIN");}else fail("INPUT_DOMAIN");}
 char* p=row(in);arity13(p,3,"INPUT_HEADER");if(strncmp(p,"PORT17 ",7))fail("INPUT_TAG");p+=7;char* end=strchr(p,' ');if(!end)fail("INPUT_HEADER");*end=0;fullProfile17=!strcmp(p,"PUBLIC")?0:!strcmp(p,"DIRECT")?1:!strcmp(p,"GUARD")?2:-1;if(fullProfile17<0)fail("INPUT_PROFILE");p=end+1;unsigned n=decimal13(&p);if(*p)fail("INPUT_HEADER");unsigned bound=fullProfile17==0?96:fullProfile17==1?64:697;if(!n||n>bound||!diagnostic17&&n!=bound)fail("INPUT_N");profile11=profile12=14;if(fullProfile17==2){guard17(in,n);return fflush(stdout)?2:0;}direct14=fullProfile17==1;
 printf("PORT17 %s %u\n",fullProfile17==0?"PUBLIC":"DIRECT",n);unsigned prior=0;
 for(unsigned ci=0;ci<n;ci++){p=row(in);arity13(p,3,"INPUT_ARITY");if(strncmp(p,"C ",2))fail("INPUT_TAG");p+=2;unsigned id=decimal13(&p);space(&p);unsigned count=decimal13(&p);if(id<=prior||id>bound||!diagnostic17&&id!=ci+1)fail("INPUT_ID");prior=id;if(!count||count>(fullProfile17==0?(id<=24?128:2048):160))fail("INPUT_OPCOUNT");if(!diagnostic17&&count!=frozenCounts17[fullProfile17][id-1])fail("INPUT_OPCOUNT");reset17(id);printf("CASE %u %u\n",id,count);
 for(unsigned seq=1;seq<=count;seq++){int payload=0;resetOperation14(id,seq);Operation o=read17(in,seq,&payload);traceCount17=0;reason17=0;resultWorld17=resultShape17=-1;listCount17=0;opcode9=o.code;if(o.code==20)churn17(&o);else if(o.code>=302)execute17(&o,payload);else{if(o.code<200){execute13(&o);aggregate13();status14=status13;if(reason14!=8)reason14=reason13;}else execute14(&o);}if((o.code==31||o.code==32)&&status14==0&&o.u[0]<16)freshBegin17[o.u[0]]=true;refresh17();int ordinal17[16]={0};if(OBS)for(int q=0;q<traceCount17;q++){printf("Q17 %d %"PRIu32" %u %d 4",case9,seq9,trace17[q][0],ordinal17[trace17[q][0]]++);for(int k=1;k<5;k++)word(trace17[q][k]);putchar('\n');}if(o.code==32||o.code==86&&o.u[1]&&o.u[2]==0)result17(o.code,status14,status14==7?1:reason17,0,NULL);finishOperation14(&o);}
 printf("ENDCASE %u\n",id);for(int r=0;r<16;r++)if(worlds[r].live)destroy_world(r);}
 if(fgetc(in)!=EOF)fail("INPUT_TRAILING_DATA");printf("END %u\n",n);return fflush(stdout)?2:0;}
