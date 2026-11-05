                                                                           
#include "kontrola-solver10.h"
#include "world.h"
#include "contact.h"
#include "constraint_graph.h"
#include "contact_solver.h"
#include <string.h>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-value"
#include "contact_solver.c"
#pragma GCC diagnostic pop
_Static_assert(B2_SIMD_WIDTH==4 || B2_SIMD_WIDTH==8,"supported original C lane widths");
static float lane10(b2FloatW value,int lane)
{
    float words[B2_SIMD_WIDTH];memcpy(words,&value,sizeof(words));return words[lane];
}
void port10Constraints(b2StepContext* c,int sub,int phase,bool packets)
{
    for(int color=0;color<B2_GRAPH_COLOR_COUNT;++color){b2GraphColor* g=c->graph->colors+color;
        int count=g->contactSims.count, wide=color!=B2_OVERFLOW_INDEX;
        int packetCount=wide?(count+B2_SIMD_WIDTH-1)/B2_SIMD_WIDTH:count;
        for(int packet=0;packet<packetCount;++packet)for(int lane=0;lane<(wide?B2_SIMD_WIDTH:1);++lane){
            int local=wide?B2_SIMD_WIDTH*packet+lane:packet;b2ContactSim* s=local<count?g->contactSims.data+local:NULL;
            uint32_t f[41]={0};f[0]=s?(uint32_t)s->contactId:UINT32_MAX;
            f[1]=f[2]=UINT32_MAX;f[3]=s?(uint32_t)s->manifold.pointCount:0;
            if(wide){b2ContactConstraintSIMD* q=g->simdConstraints+packet;
                f[1]=(uint32_t)q->indexA[lane];f[2]=(uint32_t)q->indexB[lane];
#define W10(i,field) f[i]=port10Bits(lane10(q->field,lane))
                W10(4,normal.X);W10(5,normal.Y);W10(6,invMassA);W10(7,invIA);W10(8,invMassB);W10(9,invIB);
                W10(10,friction);W10(11,restitution);W10(12,tangentSpeed);W10(13,rollingResistance);
                W10(14,rollingMass);W10(15,rollingImpulse);W10(16,biasRate);W10(17,massScale);W10(18,impulseScale);
                W10(19,anchorA1.X);W10(20,anchorA1.Y);W10(21,anchorB1.X);W10(22,anchorB1.Y);
                W10(23,baseSeparation1);W10(24,relativeVelocity1);W10(25,normalImpulse1);W10(26,tangentImpulse1);
                W10(27,totalNormalImpulse1);W10(28,normalMass1);W10(29,tangentMass1);
                W10(30,anchorA2.X);W10(31,anchorA2.Y);W10(32,anchorB2.X);W10(33,anchorB2.Y);
                W10(34,baseSeparation2);W10(35,relativeVelocity2);W10(36,normalImpulse2);W10(37,tangentImpulse2);
                W10(38,totalNormalImpulse2);W10(39,normalMass2);W10(40,tangentMass2);
#undef W10
            }else{b2ContactConstraint* q=g->overflowConstraints+packet;
                f[1]=(uint32_t)q->indexA;f[2]=(uint32_t)q->indexB;
                float values[]={q->normal.x,q->normal.y,q->invMassA,q->invIA,q->invMassB,q->invIB,
                    q->friction,q->restitution,q->tangentSpeed,q->rollingResistance,q->rollingMass,q->rollingImpulse,
                    q->softness.biasRate,q->softness.massScale,q->softness.impulseScale};
                for(int k=0;k<15;++k)f[4+k]=port10Bits(values[k]);
                for(int point=0;point<q->pointCount;++point){b2ContactConstraintPoint* p=q->points+point;
                    float v[]={p->anchorA.x,p->anchorA.y,p->anchorB.x,p->anchorB.y,p->baseSeparation,p->relativeVelocity,
                        p->normalImpulse,p->tangentImpulse,p->totalNormalImpulse,p->normalMass,p->tangentMass};
                    for(int k=0;k<11;++k)f[19+11*point+k]=port10Bits(v[k]);}}
            if(packets){int prefix[]={color,packet,lane};port10Record("PK10",prefix,3,f,3);}
            uint32_t words[43];words[0]=wide||f[3]==2?UINT32_MAX:UINT32_C(0x3fffffff);
            words[1]=wide||f[3]==2?UINT32_C(0x1ff):0;memcpy(words+2,f,sizeof(f));
            int prefix[]={sub,phase,color,packet,lane};port10Record("SC10",prefix,5,words,43);
        }}
}
void port10ComponentContacts(b2StepContext* c,int phase)
{
    int packets=0;
    for(int color=0;color<11;++color)packets+=(c->graph->colors[color].contactSims.count+B2_SIMD_WIDTH-1)/B2_SIMD_WIDTH;
    if(phase==0){b2PrepareContactsTask(0,packets,c);b2PrepareOverflowContacts(c);return;}
    if(phase==7){b2StoreOverflowImpulses(c);b2StoreImpulsesTask(0,packets,c);return;}
    if(phase==2)b2WarmStartOverflowContacts(c);
    if(phase==3||phase==5)b2SolveOverflowContacts(c,phase==3);
    if(phase==6)b2ApplyOverflowRestitution(c);
    for(int color=0;color<11;++color){int count=(c->graph->colors[color].contactSims.count+B2_SIMD_WIDTH-1)/B2_SIMD_WIDTH;
        if(phase==2)b2WarmStartContactsTask(0,count,c,color);
        if(phase==3||phase==5)b2SolveContactsTask(0,count,c,color,phase==3);
        if(phase==6)b2ApplyRestitutionTask(0,count,c,color);}
}
void port10Helpers(int helper,int kind,const uint32_t* words)
{
    if(kind==2){uint64_t count=(uint64_t)words[0]|((uint64_t)words[1]<<32);uint32_t base=words[2]==0?32:4;
        uint32_t blocks=count?((uint32_t)count-1)/base+1:0;
        if(count>4*base){base=(uint32_t)(count/4);blocks=4;}
        uint32_t result[]={blocks,base};
        for(int k=0;k<2;++k){int p[]={helper,k,0};port10Record("FH10",p,3,result+k,1);}
        for(uint32_t j=0;j<blocks;++j){uint32_t values[]={j*base,j==blocks-1?(uint32_t)count-j*base:base};
            for(int k=0;k<2;++k){int p[]={helper,2+2*(int)j+k,0};port10Record("FH10",p,3,values+k,1);}}
        return;}
                                                                                     
    uint32_t loaded[4][B2_SIMD_WIDTH];
    for(int group=0;group<4;++group)for(int lane=0;lane<B2_SIMD_WIDTH;++lane)loaded[group][lane]=words[4*group+lane%4];
    b2FloatW a,b,d,mask;memcpy(&a,loaded[0],sizeof(a));memcpy(&b,loaded[1],sizeof(b));
    memcpy(&d,loaded[2],sizeof(d));memcpy(&mask,loaded[3],sizeof(mask));
    if(kind==1){b2RotW q={a,b};b2Vec2W v={d,mask};b2Vec2W rotated=b2RotateVectorW(q,v);
        b2FloatW values[]={rotated.X,rotated.Y,b2DotW(v,v),b2CrossW(v,v)};
        for(int op=0;op<4;++op)for(int lane=0;lane<B2_SIMD_WIDTH;++lane){uint32_t w=port10Bits(lane10(values[op],lane));int p[]={helper,op,lane};port10Record("FH10",p,3,&w,1);}return;}
                                                                             
                                                                                
    mask=b2EqualsW(b2EqualsW(mask,b2ZeroW()),b2ZeroW());
    b2FloatW values[]={b2ZeroW(),b2SplatW(lane10(a,0)),b2AddW(a,b),b2SubW(a,b),b2MulW(a,b),
        b2MulAddW(a,b,d),b2MulSubW(a,b,d),b2MinW(a,b),b2MaxW(a,b),b2SymClampW(a,b),b2OrW(a,b),
        b2GreaterThanW(a,b),b2EqualsW(a,b),b2BlendW(a,b,mask)};
    for(int op=0;op<14;++op)for(int lane=0;lane<B2_SIMD_WIDTH;++lane){uint32_t w=port10Bits(lane10(values[op],lane));int p[]={helper,op,lane};port10Record("FH10",p,3,&w,1);}
    uint32_t w=b2AllZeroW(a);int p[]={helper,14,0};port10Record("FH10",p,3,&w,1);
}
