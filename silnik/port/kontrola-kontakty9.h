                                                                                 
#include "contact.h"
#include "island.h"
#ifndef GUARD9
#define GUARD9 0
#endif
enum { CONTACTS9=256, EVENTS9=516 };
typedef struct Number9 { int slot;uint64_t birth,owner; } Number9;
typedef struct Saved9 { bool saved;Number9 number; } Saved9;
typedef struct Begin9 { Number9 a,b;b2Manifold manifold; } Begin9;
typedef struct End9 { Number9 a,b; } End9;
typedef struct Copy9 { bool saved;int nb,ne;Begin9 begin[EVENTS9];End9 end[EVENTS9]; } Copy9;
typedef struct Meta9 {
    uint64_t birth[CONTACTS9];bool rolling[CONTACTS9];
    int nb,ne[2];Begin9 begin[EVENTS9];End9 end[2][EVENTS9];
} Meta9;
typedef struct Request9 { int move,a,b,kind,primary,created,id,ca,cb; } Request9;
static Saved9 saved9[CONTACTS9];static Copy9 copies9[4];static Meta9 meta9[WORLDS];
static uint64_t metadataOwner9[WORLDS];
static Request9 requests9[1024];static int nr9,phase9,active9=-1,case9;static uint32_t seq9,opcode9;
static int result9,has9,query9=-1,list9=-1,read9=-1,change9,deadEvents9=-1,phaseOwner9=-1;
static Number9 return9;static uint32_t pub9[7],priv9[19];
static int history9[3],beforePools9[WORLDS][3];static bool populationDone9;
static void population_after9(void);
static const int bounds9[16][3]={{0,0,0},{2,2,1},{2,2,1},{3,3,3},{3,3,3},{2,2,1},{8,8,12},{8,8,12},{8,8,12},{14,14,13},{14,14,13},{4,4,4},{65,130,129},{6,12,16},{8,16,16},{8,16,16}};
static const int kind9[4][4]={{0,1,2,3},{1,4,5,6},{2,5,-1,7},{3,6,7,8}};
static const bool primary9[4][4]={{true,false,false,false},{true,true,false,false},{true,true,false,true},{true,true,false,true}};
extern void* port9Enqueue(b2TaskCallback*,int,int,void*,void*);
extern void port9Finish(void*,void*);
extern void port9Collide(b2World*);
extern int port9Prepare(b2World*,b2ShapeId*,b2ShapeId*,bool);

static int owner9(b2World* w){for(int i=0;i<WORLDS;++i)if(worlds[i].live&&worlds[i].raw.index1==w->worldId+1)return i;fail("INPUT_DOMAIN");return -1;}
static Number9 empty9(void){return (Number9){-1,0,0};}
static void number9(Number9 n){word((uint32_t)n.slot);wide(n.birth);wide(n.owner);}
static Number9 shape_number9(b2ShapeId raw)
{
                                                                                  
    uint64_t owner=0;for(int j=0;j<WORLDS;++j)if(worlds[j].live&&worlds[j].raw.index1==raw.world0+1)owner=worlds[j].birth;
    for(int i=0;i<SHAPES;++i)if(shapes[i].saved&&shapes[i].owner==owner&&b2StoreShapeId(shapes[i].raw)==b2StoreShapeId(raw))
        return (Number9){raw.index1-1,shapes[i].birth,shapes[i].owner};
    fail("INPUT_DOMAIN");return empty9();
}
static Number9 shape_slot9(b2World* w,int slot)
{b2Shape* s=w->shapes.data+slot;return shape_number9((b2ShapeId){slot+1,w->worldId,s->generation});}
static void manifold9(b2Manifold m)
{
    vec(m.normal);real(m.rollingImpulse);word((uint32_t)m.pointCount);
    for(int j=0;j<2;++j){b2ManifoldPoint p=m.points[j];vec(p.point);vec(p.anchorA);vec(p.anchorB);
        real(p.separation);real(p.normalImpulse);real(p.tangentImpulse);real(p.totalNormalImpulse);real(p.normalVelocity);word(p.id);word(p.persisted);}
}
static b2Manifold decode_manifold9(const uint32_t* a)
{
    b2Manifold m={0};m.normal=(b2Vec2){from_bits(a[0]),from_bits(a[1])};m.rollingImpulse=from_bits(a[2]);m.pointCount=(int)a[3];
    for(int j=0;j<2;++j){const uint32_t* p=a+4+13*j;b2ManifoldPoint* q=m.points+j;
        q->point=(b2Vec2){from_bits(p[0]),from_bits(p[1])};q->anchorA=(b2Vec2){from_bits(p[2]),from_bits(p[3])};
        q->anchorB=(b2Vec2){from_bits(p[4]),from_bits(p[5])};q->separation=from_bits(p[6]);q->normalImpulse=from_bits(p[7]);
        q->tangentImpulse=from_bits(p[8]);q->totalNormalImpulse=from_bits(p[9]);q->normalVelocity=from_bits(p[10]);q->id=(uint16_t)p[11];q->persisted=p[12]!=0;}
    return m;
}
static int find_contact9(b2World* w,int a,int b)
{
    for(int i=0;i<w->contacts.count;++i){b2Contact* c=w->contacts.data+i;
        if(c->contactId==i&&((c->shapeIdA==a&&c->shapeIdB==b)||(c->shapeIdA==b&&c->shapeIdB==a)))return i;}
    return -1;
}
static int contact_status9(int owner,Number9 n)
{
    if(!world_live(worlds+owner))return STALE;
    if(n.owner!=worlds[owner].birth)return FOREIGN;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);
    if(n.slot<0||n.slot>=w->contactIdPool.nextIndex)return STALE;
    b2Contact* c=w->contacts.data+n.slot;
    if(c->setIndex==B2_NULL_INDEX)return STALE;
    if(n.birth!=meta9[owner].birth[n.slot])return STALE;
    if(c->contactId!=n.slot)return STALE;
    return OK;
}
#ifdef HELPER9
static void helper9(const Operation* o)
{
    int owner=(int)o->u[0];Number9 n=saved9[o->u[1]].number;b2World* w=b2GetWorldFromId(worlds[owner].raw);
    if(HELPER9==1)w->contactIdPool.nextIndex=n.slot;
    if(HELPER9==2)w->contacts.data[n.slot].setIndex=-1;
    if(HELPER9==3)n.birth^=UINT64_C(1);
    if(HELPER9==4)n.birth^=UINT64_C(1)<<32;
    if(HELPER9==5)w->contacts.data[n.slot].contactId=n.slot+1;
    if(HELPER9==6)n.owner^=UINT64_C(1);
    if(HELPER9==7){worlds[15]=worlds[owner];worlds[15].live=false;worlds[15].birth^=UINT64_C(1);owner=15;}
    printf("GUARD9 %d\n",contact_status9(owner,n));
}
#endif
static void stamp9(void)
{
    for(int i=0;i<WORLDS;++i)if(worlds[i].live){
        b2World* w=b2GetWorldFromId(worlds[i].raw);Meta9* m=meta9+i;
        if(w->contactBeginEvents.count>EVENTS9)fail("INPUT_POPULATION");
        for(int j=m->nb;j<w->contactBeginEvents.count;++j){b2ContactBeginTouchEvent e=w->contactBeginEvents.data[j];m->begin[j]=(Begin9){shape_number9(e.shapeIdA),shape_number9(e.shapeIdB),e.manifold};}
        m->nb=w->contactBeginEvents.count;
        for(int side=0;side<2;++side){int count=w->contactEndEvents[side].count;
            if(count>EVENTS9)fail("INPUT_POPULATION");
            for(int j=m->ne[side];j<count;++j){b2ContactEndTouchEvent e=w->contactEndEvents[side].data[j];m->end[side][j]=(End9){shape_number9(e.shapeIdA),shape_number9(e.shapeIdB)};}
            m->ne[side]=count;
        }
    }
}
void port9Request(b2World* w,int move,int a,int b)
{
    if(nr9>=1024)fail("INPUT_POPULATION");
    int t=w->shapes.data[a].type,u=w->shapes.data[b].type;
    if(t>3||u>3)fail("INPUT_DOMAIN");int k=kind9[t][u];bool p=primary9[t][u];
    requests9[nr9++]=(Request9){move,a,b,k,p,0,-1,k<0?-1:p?a:b,k<0?-1:p?b:a};
}
static void finish_requests9(b2World* w)
{
    population_after9();
    int owner=owner9(w);
    for(int j=0;j<nr9;++j){Request9* r=requests9+j;
        if(r->kind<0)continue;int id=find_contact9(w,r->ca,r->cb);
        if(id<0||id>=CONTACTS9)fail("INPUT_DOMAIN");
        r->created=1;r->id=id;uint64_t next;if(!ticket_next(lastIssued,&next))fail("INPUT_DOMAIN");
        meta9[owner].birth[id]=next;meta9[owner].rolling[id]=false;lastIssued=next;
    }
}
void sim9(b2World* w,const b2ContactSim* s)
{
    word((uint32_t)s->contactId);word((uint32_t)s->bodySimIndexA);word((uint32_t)s->bodySimIndexB);
    word((uint32_t)s->shapeIdA);word((uint32_t)s->shapeIdB);real(s->invMassA);real(s->invIA);real(s->invMassB);real(s->invIB);
    real(s->friction);real(s->restitution);bool defined=meta9[owner9(w)].rolling[s->contactId];
    if(defined)real(s->rollingResistance);else word(0);real(s->tangentSpeed);word(s->simFlags);
    word(s->cache.count);for(int j=0;j<3;++j)word(s->cache.indexA[j]);for(int j=0;j<3;++j)word(s->cache.indexB[j]);
    manifold9(s->manifold);word(defined);
}
void bitset9(const b2BitSet* b){word(b->blockCount);word(b->blockCapacity);for(uint32_t j=0;j<b->blockCount;++j)wide(b->bits[j]);}
void port9CaptureTask(b2StepContext* context,int start,int end)
{
    b2World* w=context->world;
    for(int j=start;j<end;++j){b2ContactSim* s=context->contacts[j];
        if(!(s->simFlags&b2_simDisjoint))meta9[owner9(w)].rolling[s->contactId]=true;}
#if OBS
    int owner=owner9(w);b2BitSet* b=&w->taskContexts.data[0].contactStateBitSet;
    printf("TASK %d %"PRIu32" %d 0 0",case9,seq9,owner);word(0);word((uint32_t)start);word((uint32_t)end);word((uint32_t)(end-start));bitset9(b);putchar('\n');++priv9[17];++priv9[18];
    for(int j=start;j<end;++j){b2ContactSim* s=context->contacts[j];b2Contact* c=w->contacts.data+s->contactId;
        printf("TASK %d %"PRIu32" %d 1 %d",case9,seq9,owner,j-start);
        word(c->colorIndex<0?0:1);word((uint32_t)(c->colorIndex<0?c->setIndex:c->colorIndex));word((uint32_t)c->localIndex);sim9(w,s);putchar('\n');++priv9[17];}
#endif
}
static void value9(const char* tag,int id,uint32_t seq,int phase,b2World* w,b2Contact* c,Number9 n)
{
    printf("%s %d %"PRIu32" %d",tag,id,seq,phase);word(0);number9(n);number9(shape_slot9(w,c->shapeIdA));number9(shape_slot9(w,c->shapeIdB));word((c->flags&b2_contactTouchingFlag)!=0);
    b2Manifold m=b2GetContactSim(w,c)->manifold;if(phase==1){uint32_t x=to_bits(m.normal.x)^UINT32_C(0x80000000);m.normal.x=from_bits(x);}manifold9(m);putchar('\n');
}
static Copy9 copy_events9(int owner)
{
    b2World* w=b2GetWorldFromId(worlds[owner].raw);b2ContactEvents e=b2World_GetContactEvents(worlds[owner].raw);
    if(e.hitCount)fail("INPUT_DOMAIN");int side=1-w->endEventArrayIndex;Copy9 c={0};c.saved=true;c.nb=e.beginCount;c.ne=e.endCount;
    if(c.nb!=meta9[owner].nb||c.ne!=meta9[owner].ne[side])fail("INPUT_DOMAIN");
    for(int j=0;j<c.nb;++j)c.begin[j]=meta9[owner].begin[j];for(int j=0;j<c.ne;++j)c.end[j]=meta9[owner].end[side][j];
    return c;
}
static void events9(const char* tag,int id,uint32_t seq,int owner,int phase,int status,Copy9 c)
{
    int counter=tag[1]=='E'?5:6;
    printf("%s %d %"PRIu32" %d %d 0 0",tag,id,seq,owner,phase);word((uint32_t)status);word((uint32_t)c.nb);word((uint32_t)c.ne);word(0);putchar('\n');++pub9[counter];
    for(int j=0;j<c.nb;++j){printf("%s %d %"PRIu32" %d %d 1 %d",tag,id,seq,owner,phase,j);number9(c.begin[j].a);number9(c.begin[j].b);manifold9(c.begin[j].manifold);putchar('\n');++pub9[counter];}
    for(int j=0;j<c.ne;++j){printf("%s %d %"PRIu32" %d %d 2 %d",tag,id,seq,owner,phase,j);number9(c.end[j].a);number9(c.end[j].b);putchar('\n');++pub9[counter];}
}
static void public9_dump(int id,uint32_t seq)
{
    for(int i=0;i<WORLDS;++i)if(worlds[i].live&&metadataOwner9[i]!=worlds[i].birth){memset(meta9+i,0,sizeof(Meta9));metadataOwner9[i]=worlds[i].birth;}
    stamp9();
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2World* w=b2GetWorldFromId(worlds[owner].raw);
        for(int bid=0;bid<w->bodies.count;++bid){b2Body* b=w->bodies.data+bid;if(b->id!=bid)continue;
            b2BodyId raw={bid+1,w->worldId,b->generation};int capacity=b2Body_GetContactCapacity(raw);b2ContactData data[CONTACTS9];
            if(capacity>CONTACTS9)fail("INPUT_POPULATION");int count=b2Body_GetContactData(raw,data,capacity);
            printf("CD %d %"PRIu32" %d %d 0 0",id,seq,owner,bid);word((uint32_t)capacity);word((uint32_t)count);putchar('\n');++pub9[2];
            for(int j=0;j<count;++j){printf("CD %d %"PRIu32" %d %d 1 %d",id,seq,owner,bid,j);
                b2ShapeId a=data[j].shapeIdA,b_=data[j].shapeIdB;word((uint32_t)a.index1);word(a.world0);word(a.generation);word((uint32_t)b_.index1);word(b_.world0);word(b_.generation);manifold9(data[j].manifold);putchar('\n');++pub9[2];}
        }
    }
    for(int j=0;j<CONTACTS9;++j)if(saved9[j].saved){printf("NC9 %d %"PRIu32" %d",id,seq,j);number9(saved9[j].number);putchar('\n');++pub9[0];}
    if(opcode9==46||opcode9==47){printf("RC9 %d %"PRIu32,id,seq);word((uint32_t)result9);word((uint32_t)has9);number9(return9);putchar('\n');++pub9[1];}
    if(query9>=0&&!result9){Number9 n=saved9[query9].number;b2World* w=b2GetWorldFromId(worlds[active9].raw);b2Contact* c=w->contacts.data+n.slot;
        for(int phase=0;phase<(change9?3:1);++phase){value9("GV",id,seq,phase,w,c,n);++pub9[3];}}
    if(list9>=0){int phases=!result9&&change9?3:1;
        for(int phase=0;phase<phases;++phase){int count=0;b2ContactData data[CONTACTS9+1];b2World* w=NULL;
            if(!result9){w=b2GetWorldFromId(worlds[active9].raw);count=b2Body_GetContactData(bodies[list9].raw,data,CONTACTS9);
                if(phase==1&&count){data[count]=data[0];if(count>=2){b2ContactData t=data[0];data[0]=data[1];data[1]=t;}data[0].manifold.normal.x=from_bits(to_bits(data[0].manifold.normal.x)^UINT32_C(0x80000000));++count;}}
            printf("GL %d %"PRIu32" %d 0 0",id,seq,phase);word((uint32_t)result9);word((uint32_t)count);putchar('\n');++pub9[4];
            for(int j=0;j<count;++j){b2ShapeId a=data[j].shapeIdA,b=data[j].shapeIdB;int cid=find_contact9(w,a.index1-1,b.index1-1);
                printf("GL %d %"PRIu32" %d 1 %d",id,seq,phase,j);number9((Number9){cid,meta9[active9].birth[cid],worlds[active9].birth});number9(shape_number9(a));number9(shape_number9(b));word(1);manifold9(data[j].manifold);putchar('\n');++pub9[4];}
        }
    }
    for(int i=0;i<WORLDS;++i)if(worlds[i].live||i==deadEvents9)events9("GE",id,seq,i,0,i==deadEvents9?STALE:OK,i==deadEvents9?(Copy9){0}:copy_events9(i));
    for(int i=0;i<4;++i)if(copies9[i].saved){int phases=i==read9&&change9?3:1;
        for(int phase=0;phase<phases;++phase){Copy9 c=copies9[i];
            if(phase==1){if(c.nb){c.begin[0].a.birth^=UINT64_C(1);c.begin[0].manifold.normal.x=from_bits(to_bits(c.begin[0].manifold.normal.x)^UINT32_C(0x80000000));}else if(c.ne)c.end[0].a.birth^=UINT64_C(1);}
            events9("GC",id,seq,i,phase,0,c);}}
}
#if OBS
static void private9_dump(int id,uint32_t seq)
{
    for(int j=0;j<nr9;++j){Request9 r=requests9[j];printf("RQ %d %"PRIu32" %d %d",id,seq,active9,j);int a[]={r.move,r.a,r.b,r.kind,r.primary,r.created,r.id,r.ca,r.cb};for(int k=0;k<9;++k)word((uint32_t)a[k]);putchar('\n');++priv9[0];}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);printf("CP %d %"PRIu32" %d",id,seq,o);word((uint32_t)w->contactIdPool.nextIndex);word((uint32_t)w->contactIdPool.freeArray.count);word((uint32_t)b2GetIdCount(&w->contactIdPool));putchar('\n');++priv9[1];}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);for(int j=0;j<w->contactIdPool.freeArray.count;++j){printf("CF %d %"PRIu32" %d %d",id,seq,o,j);word((uint32_t)w->contactIdPool.freeArray.data[j]);putchar('\n');++priv9[2];}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);for(int j=0;j<w->contactIdPool.nextIndex;++j){b2Contact* c=w->contacts.data+j;bool live=c->contactId==j;
        printf("CT %d %"PRIu32" %d %d",id,seq,o,j);word(live);
        if(!live){for(int k=0;k<4;++k)word(UINT32_MAX);for(int k=0;k<15;++k)word(0);}
        else{int a[]={c->contactId,c->setIndex,c->colorIndex,c->localIndex,c->shapeIdA,c->shapeIdB,c->edges[0].bodyId,c->edges[0].prevKey,c->edges[0].nextKey,c->edges[1].bodyId,c->edges[1].prevKey,c->edges[1].nextKey,c->islandId,c->islandPrev,c->islandNext};for(int k=0;k<15;++k)word((uint32_t)a[k]);word(c->flags);word(c->isMarked);wide(meta9[o].birth[j]);}
        putchar('\n');++priv9[3];}}
    for(int group=0;group<2;++group)for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);
        for(int domain=0;domain<2;++domain)for(int index=0;index<(domain?12:3);++index){b2ContactSimArray* a=domain?&w->constraintGraph.colors[index].contactSims:&w->solverSets.data[index].contactSims;
            if(group==0){printf("CA %d %"PRIu32" %d %d %d",id,seq,o,domain,index);word((uint32_t)a->count);putchar('\n');++priv9[4];}
            else for(int j=0;j<a->count;++j){printf("CS %d %"PRIu32" %d %d %d %d",id,seq,o,domain,index,j);sim9(w,a->data+j);putchar('\n');++priv9[5];}}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);for(int color=0;color<12;++color){printf("GB %d %"PRIu32" %d %d",id,seq,o,color);word(color!=11);if(color==11){word(0);word(0);}else bitset9(&w->constraintGraph.colors[color].bodySet);putchar('\n');++priv9[6];}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);printf("CB %d %"PRIu32" %d 0",id,seq,o);bitset9(&w->taskContexts.data[0].contactStateBitSet);putchar('\n');++priv9[7];}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);for(int j=0;j<w->bodies.count;++j){b2Body* b=w->bodies.data+j;if(b->id!=j)continue;
        printf("BL9 %d %"PRIu32" %d %d",id,seq,o,j);word((uint32_t)b->headContactKey);word((uint32_t)b->contactCount);word((uint32_t)b->islandId);word((uint32_t)b->islandPrev);word((uint32_t)b->islandNext);
        int key=b->headContactKey,n=0;while(key!=-1){if(++n>CONTACTS9)fail("INPUT_DOMAIN");word((uint32_t)(key>>1));word((uint32_t)(key&1));key=w->contacts.data[key>>1].edges[key&1].nextKey;}putchar('\n');++priv9[8];}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);printf("IP %d %"PRIu32" %d",id,seq,o);word((uint32_t)w->islandIdPool.nextIndex);word((uint32_t)w->islandIdPool.freeArray.count);word((uint32_t)b2GetIdCount(&w->islandIdPool));putchar('\n');++priv9[9];}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);for(int j=0;j<w->islandIdPool.freeArray.count;++j){printf("IF %d %"PRIu32" %d %d",id,seq,o,j);word((uint32_t)w->islandIdPool.freeArray.data[j]);putchar('\n');++priv9[10];}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);for(int j=0;j<w->islandIdPool.nextIndex;++j){b2Island* a=w->islands.data+j;bool live=a->islandId==j;printf("IS %d %"PRIu32" %d %d",id,seq,o,j);word(live);
        if(!live){for(int k=0;k<3;++k)word(UINT32_MAX);for(int k=0;k<11;++k)word(0);}else{int v[]={a->setIndex,a->localIndex,a->islandId,a->headBody,a->tailBody,a->bodyCount,a->headContact,a->tailContact,a->contactCount,a->headJoint,a->tailJoint,a->jointCount,a->parentIsland,a->constraintRemoveCount};for(int k=0;k<14;++k)word((uint32_t)v[k]);}putchar('\n');++priv9[11];}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);
        for(int s=0;s<3;++s)for(int j=0;j<w->solverSets.data[s].islandSims.count;++j){printf("IL %d %"PRIu32" %d 0 %d %d",id,seq,o,s,j);word((uint32_t)w->solverSets.data[s].islandSims.data[j].islandId);putchar('\n');++priv9[12];}
        for(int kind=1;kind<=2;++kind)for(int k=0;k<w->islands.count;++k){b2Island* a=w->islands.data+k;if(a->islandId!=k)continue;int n=kind==1?a->headBody:a->headContact,j=0;
            while(n!=-1){if(j>CONTACTS9)fail("INPUT_DOMAIN");printf("IL %d %"PRIu32" %d %d %d %d",id,seq,o,kind,k,j++);word((uint32_t)n);putchar('\n');++priv9[12];n=kind==1?w->bodies.data[n].islandNext:w->contacts.data[n].islandNext;}}}
    for(int group=0;group<3;++group)for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);int count=group==0?w->contactBeginEvents.count:w->contactEndEvents[group-1].count;
        for(int j=0;j<count;++j){b2ShapeId a,b;b2Manifold m={0};if(!group){b2ContactBeginTouchEvent e=w->contactBeginEvents.data[j];a=e.shapeIdA;b=e.shapeIdB;m=e.manifold;}else{b2ContactEndTouchEvent e=w->contactEndEvents[group-1].data[j];a=e.shapeIdA;b=e.shapeIdB;}
            printf("%s %d %"PRIu32" %d %d",group==0?"EB":group==1?"EE0":"EE1",id,seq,o,j);word((uint32_t)a.index1);word(a.world0);word(a.generation);word((uint32_t)b.index1);word(b.world0);word(b.generation);if(!group)manifold9(m);putchar('\n');++priv9[13+group];}}
    for(int o=0;o<WORLDS;++o)if(worlds[o].live){b2World* w=b2GetWorldFromId(worlds[o].raw);printf("EN9 %d %"PRIu32" %d",id,seq,o);word((uint32_t)w->contactBeginEvents.count);word((uint32_t)w->contactEndEvents[0].count);word((uint32_t)w->contactEndEvents[1].count);word((uint32_t)w->endEventArrayIndex);word((uint32_t)w->contactHitEvents.count);putchar('\n');++priv9[16];}
}
#endif
static void counts9_dump(int id,uint32_t seq)
{
    uint32_t contacts=0,saved=0,copies_=0;
    for(int i=0;i<WORLDS;++i)if(worlds[i].live)contacts+=(uint32_t)b2GetIdCount(&b2GetWorldFromId(worlds[i].raw)->contactIdPool);
    for(int i=0;i<CONTACTS9;++i)saved+=saved9[i].saved;for(int i=0;i<4;++i)copies_+=copies9[i].saved;
    printf("Z9 %d %"PRIu32,id,seq);word(saved);word(contacts);word(copies_);for(int k=0;k<7;++k)word(pub9[k]);word(seq);word(seq);word(GUARD9?2:1);word(GUARD9||opcode9==51||opcode9==52||opcode9==53);wide(lastIssued);putchar('\n');
}
static void reset_operation9(int id,uint32_t seq,uint32_t code)
{
    case9=id;seq9=seq;opcode9=code;nr9=0;result9=0;has9=0;query9=list9=read9=deadEvents9=-1;change9=0;return9=empty9();
    memset(pub9,0,sizeof(pub9));memset(priv9,0,sizeof(priv9));
}
static void population9(const Operation* o)
{
    (void)o;populationDone9=false;memset(beforePools9,0,sizeof(beforePools9));
    for(int i=0;i<WORLDS;++i)if(worlds[i].live){b2World* w=b2GetWorldFromId(worlds[i].raw);
        beforePools9[i][0]=w->bodyIdPool.nextIndex;beforePools9[i][1]=w->shapeIdPool.nextIndex;beforePools9[i][2]=w->contactIdPool.nextIndex;}
}
static void population_after9(void)
{
    if(populationDone9)return;populationDone9=true;int nw=0,nb=0,ns=0;
    for(int i=0;i<WORLDS;++i)if(worlds[i].live){++nw;b2World* w=b2GetWorldFromId(worlds[i].raw);
        int pools[]={w->bodyIdPool.nextIndex,w->shapeIdPool.nextIndex,w->contactIdPool.nextIndex};
        for(int j=0;j<3;++j)if(pools[j]>beforePools9[i][j])history9[j]+=pools[j]-beforePools9[i][j];}
    for(int i=0;i<BODIES;++i)nb+=bodies[i].saved;for(int i=0;i<SHAPES;++i)ns+=shapes[i].saved;
    int b=GUARD9?4:bounds9[(case9-1)/4][0],s=GUARD9?4:bounds9[(case9-1)/4][1],c=GUARD9?4:bounds9[(case9-1)/4][2];
    if(nw>2||history9[0]>b||history9[1]>s||history9[2]>c||nb>2*b||ns>2*s)fail("INPUT_POPULATION");
}
static bool material9(const uint32_t* a)
{
    for(int i=45;i<=48;++i)if(!isfinite(from_bits(a[i]))||(i<48&&from_bits(a[i])<0))return false;
    return true;
}
static int create_shape9(const Operation* o)
{
    const uint32_t* a=o->u;int status=guard(worlds+a[1],bodies+a[2]);if(status)return status;
    if(a[58]&&!material9(a))return PARAM;
    Geometry geo;bool valid=prepare(a[3],a+4,&geo);
    if(!isfinite(o->f[44])||o->f[44]<0||!valid){
        if(!a[58]&&a[3]==2&&!valid){
            b2Segment segment={{o->f[4],o->f[5]},{o->f[6],o->f[7]}};
            b2ShapeDef def=b2DefaultShapeDef();def.density=o->f[44];
            if(B2_IS_NON_NULL(b2CreateSegmentShape(bodies[a[2]].raw,&def,&segment)))fail("INPUT_DOMAIN");
        }
        return GEOMETRY;
    }
    if(a[58]&&!preflight(bodies[a[2]].raw,NULL,&geo,o->f[44],b2_nullShapeId,false,0))return GEOMETRY;
    uint64_t next;if(!ticket_next(lastIssued,&next))return LIMIT;
    b2ShapeDef d=b2DefaultShapeDef();d.density=o->f[44];d.material=(b2SurfaceMaterial){0};
    d.material.friction=o->f[45];d.material.restitution=o->f[46];d.material.rollingResistance=o->f[47];d.material.tangentSpeed=o->f[48];memcpy(&d.material.userMaterialId,a+49,4);
    d.filter.categoryBits=(uint64_t)a[50]|(uint64_t)a[51]<<32;d.filter.maskBits=(uint64_t)a[52]|(uint64_t)a[53]<<32;memcpy(&d.filter.groupIndex,a+54,4);
    d.updateBodyMass=true;d.invokeContactCreation=a[55]!=0;d.enableContactEvents=a[56]!=0;d.enableHitEvents=a[57]!=0;d.enablePreSolveEvents=false;d.isSensor=false;
    b2ShapeId raw=b2_nullShapeId;
    if(a[3]==1){b2Capsule c={{o->f[4],o->f[5]},{o->f[6],o->f[7]},o->f[8]};raw=b2CreateCapsuleShape(bodies[a[2]].raw,&d,&c);}
    else if(geo.type==0)raw=b2CreateCircleShape(bodies[a[2]].raw,&d,&geo.circle);
    else if(geo.type==2)raw=b2CreateSegmentShape(bodies[a[2]].raw,&d,&geo.segment);
    else raw=b2CreatePolygonShape(bodies[a[2]].raw,&d,&geo.polygon);
    if(B2_IS_NULL(raw))return GEOMETRY;shapes[a[0]]=(Shape){true,true,raw,worlds[a[1]].birth,next};lastIssued=next;return OK;
}
static void validate9(const Operation* o)
{
    const uint32_t* a=o->u;int code=(int)o->code;
    if(code==40){
        if(a[0]>=SHAPES||a[1]>=WORLDS||a[2]>=BODIES)fail("INPUT_REGISTER_RANGE");
        for(int j=55;j<=58;++j)if(a[j]>1)fail("INPUT_BOOL");
        if(a[3]>4)fail("INPUT_ENUM");if(a[58]&&a[57])fail("INPUT_GAME_HIT");
        for(int j=0;j<40;++j)if(!geometry_float(a[3],a+4,j)&&!(a[3]==3&&j==0)&&a[4+j])fail("INPUT_UNUSED");
        if(a[3]==4&&isfinite(o->f[8])&&isfinite(o->f[9])&&!b2IsNormalizedRot((b2Rot){o->f[8],o->f[9]}))fail("INPUT_ROTATION");
        if(!a[58]){if(!material9(a)||!isfinite(o->f[44])||o->f[44]<0)fail("INPUT_DOMAIN");for(int j=0;j<40;++j)if(geometry_float(a[3],a+4,j)&&!isfinite(o->f[4+j]))fail("INPUT_DOMAIN");Geometry g;if(!prepare(a[3],a+4,&g)&&a[3]!=2)fail("INPUT_DOMAIN");}
    }else if(code==50){if(a[0]>3)fail("INPUT_REGISTER_RANGE");if(a[1]>1)fail("INPUT_BOOL");}
    else{
        if(a[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");
        if(code==46&&(a[1]>=SHAPES||a[2]>=SHAPES||a[3]>=CONTACTS9))fail("INPUT_REGISTER_RANGE");
        if((code==47||code==51||code==53)&&a[1]>=CONTACTS9)fail("INPUT_REGISTER_RANGE");
        if(code==48&&a[1]>=BODIES)fail("INPUT_REGISTER_RANGE");
        if(code==49&&a[1]>3)fail("INPUT_REGISTER_RANGE");if(code==52&&a[1]>=SHAPES)fail("INPUT_REGISTER_RANGE");
        if((code==47||code==48||code==53)&&a[2]>1)fail("INPUT_BOOL");
        if(code==51){
            if(a[5]>2)fail("INPUT_FIXTURE_MANIFOLD");
            for(int j=0;j<30;++j){bool integer=j==3||j==15||j==16||j==28||j==29;
                if((!integer&&!isfinite(o->f[2+j]))||((j==15||j==28)&&a[2+j]>65535)||((j==16||j==29)&&a[2+j]>1))fail("INPUT_FIXTURE_MANIFOLD");}
            if(a[32]>3)fail("INPUT_FIXTURE_CACHE");for(int j=33;j<=38;++j)if(a[j]>255)fail("INPUT_FIXTURE_CACHE");
        }
        if(code==52)for(int j=2;j<=5;++j)if(!isfinite(o->f[j])||(j<5&&o->f[j]<0))fail("INPUT_DOMAIN");
    }
                                                                                               
    if(code==40){if(!worlds[a[1]].saved||!bodies[a[2]].saved)fail("INPUT_REGISTER_UNINITIALIZED");if(shapes[a[0]].live)fail("INPUT_REGISTER_COLLISION");}
    else if(code==50){if(!copies9[a[0]].saved)fail("INPUT_REGISTER_UNINITIALIZED");}
    else{
        if(!worlds[a[0]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
        if(code==46&&(!shapes[a[1]].saved||!shapes[a[2]].saved))fail("INPUT_REGISTER_UNINITIALIZED");
        if((code==47||code==51||code==53)&&!saved9[a[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
        if(code==48&&!bodies[a[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
        if(code==52&&!shapes[a[1]].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    }
    if(code>=51&&code<=53){int status=code==52?shape_guard(worlds+a[0],shapes+a[1]):contact_status9((int)a[0],saved9[a[1]].number);if(status)fail("INPUT_DOMAIN");
        if(code==51){b2World* w=b2GetWorldFromId(worlds[a[0]].raw);b2Contact* c=w->contacts.data+saved9[a[1]].number.slot;bool touching=(c->flags&b2_contactTouchingFlag)!=0;if((a[5]>0)!=touching)fail("INPUT_FIXTURE_MANIFOLD");}}
}
static void phase_check9(const Operation* o)
{
    int code=(int)o->code;
    if(code>=46&&code<=50)return;
    if(!phase9){if(code>=42&&code<=45)fail("INPUT_PHASE");return;}
    if(code!=phase9+41||o->u[0]!=(uint32_t)phaseOwner9)fail("INPUT_PHASE");
}
static void execute9(int id,uint32_t seq,const Operation* o)
{
    const uint32_t* a=o->u;int code=(int)o->code;int status=0,kind=0,slot=0;
    if(code==40){status=create_shape9(o);kind=status?0:3;slot=(int)a[0];}
    else if(code==50){read9=(int)a[0];change9=(int)a[1];}
    else{
        int owner=(int)a[0];active9=owner;status=world_live(worlds+owner)?OK:STALE;
        b2World* w=status?NULL:b2GetWorldFromId(worlds[owner].raw);
        if(code==46){if(!status)status=shape_guard(worlds+owner,shapes+a[1]);if(!status)status=shape_guard(worlds+owner,shapes+a[2]);
            if(!status){int cid=find_contact9(w,shapes[a[1]].raw.index1-1,shapes[a[2]].raw.index1-1);has9=cid>=0;return9=has9?(Number9){cid,meta9[owner].birth[cid],worlds[owner].birth}:empty9();
                Number9 old=saved9[a[3]].number;
                if(saved9[a[3]].saved&&contact_status9(owner,old)==OK&&(old.slot!=return9.slot||old.birth!=return9.birth||old.owner!=return9.owner))fail("INPUT_REGISTER_COLLISION");
                saved9[a[3]]=(Saved9){true,return9};}}
        else if(code==47){return9=saved9[a[1]].number;status=contact_status9(owner,return9);has9=!status;query9=(int)a[1];change9=(int)a[2];}
        else if(code==48){status=guard(worlds+owner,bodies+a[1]);list9=(int)a[1];change9=(int)a[2];}
        else if(code==49){if(status)deadEvents9=owner;else{stamp9();copies9[a[1]]=copy_events9(owner);}}
        else if(!status){
            if(code==41){phase9=1;phaseOwner9=owner;b2ContactBeginTouchEventArray_Clear(&w->contactBeginEvents);meta9[owner].nb=0;b2ContactHitEventArray_Clear(&w->contactHitEvents);b2BodyMoveEventArray_Clear(&w->bodyMoveEvents);}
            if(code==42){
#if GUARD9
                b2ShapeId first=b2_nullShapeId,second=b2_nullShapeId;port9Prepare(w,&first,&second,true);uint64_t needed=0;
                for(int j=0;j<nr9;++j)needed+=requests9[j].kind>=0;
                if(UINT64_MAX-lastIssued<needed){status=LIMIT;phase9=0;}
                else{nr9=0;b2UpdateBroadPhasePairs(w);finish_requests9(w);phase9=2;}
#else
                b2UpdateBroadPhasePairs(w);finish_requests9(w);phase9=2;
#endif
            }
            if(code==43){port9Collide(w);phase9=3;}
            if(code==44){b2MergeAwakeIslands(w);phase9=4;}
            if(code==45){w->endEventArrayIndex=1-w->endEventArrayIndex;b2ContactEndTouchEventArray_Clear(w->contactEndEvents+w->endEventArrayIndex);meta9[owner].ne[w->endEventArrayIndex]=0;phase9=0;}
            if(code==51){b2Contact* c=w->contacts.data+saved9[a[1]].number.slot;b2ContactSim* s=b2GetContactSim(w,c);s->manifold=decode_manifold9(a+2);s->cache.count=(uint16_t)a[32];for(int j=0;j<3;++j){s->cache.indexA[j]=(uint8_t)a[33+j];s->cache.indexB[j]=(uint8_t)a[36+j];}}
            if(code==52){b2Shape* s=w->shapes.data+shapes[a[1]].raw.index1-1;s->friction=o->f[2];s->restitution=o->f[3];s->rollingResistance=o->f[4];s->tangentSpeed=o->f[5];memcpy(&s->userMaterialId,a+6,4);}
            if(code==53)b2DestroyContact(w,w->contacts.data+saved9[a[1]].number.slot,a[2]!=0);
        }
    }
    population_after9();result9=status;echo(id,seq,o);result(id,seq,0,status,kind,slot);dump(id,seq,1,0,0,-1);
}
#ifdef BITSET9_HELPER
static int bitset_helper9(void)
{
    b2BitSet a=b2CreateBitSet(16),b=b2CreateBitSet(16);
    printf("BIT9 0");bitset9(&a);putchar('\n');
    b2SetBitCountAndClear(&a,129);b2SetBitCountAndClear(&b,129);
    int x[]={31,32,63},y[]={64,127,128},all[]={31,32,63,64,127,128,255};
    for(int i=0;i<3;++i){b2SetBit(&a,x[i]);b2SetBit(&b,y[i]);}
    b2InPlaceUnion(&a,&b);printf("BIT9 1");bitset9(&a);putchar('\n');
    printf("BIT9 2");for(int i=0;i<7;++i)word(b2GetBit(&a,all[i]));putchar('\n');
    for(int i=0;i<7;++i)b2ClearBit(&a,all[i]);printf("BIT9 3");bitset9(&a);putchar('\n');
    b2SetBitGrow(&a,255);b2SetBitGrow(&a,256);b2SetBit(&a,0);printf("BIT9 4");bitset9(&a);putchar('\n');
    b2SetBitCountAndClear(&a,65);printf("BIT9 5");bitset9(&a);word(b2GetBit(&a,255));putchar('\n');
    b2ClearBit(&a,255);b2GrowBitSet(&a,4);printf("BIT9 6");bitset9(&a);putchar('\n');
    b2SetBitCountAndClear(&a,0);printf("BIT9 7");bitset9(&a);putchar('\n');
    b2DestroyBitSet(&a);b2DestroyBitSet(&b);printf("BIT9 8");bitset9(&a);putchar('\n');return 0;
}
#endif
