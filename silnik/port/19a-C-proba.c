                                                                              
                                                                             
#include "box2d/box2d.h"
#include "body.h"
#include "shape.h"
#include "world.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct ProbeTrace { int stage,phase,shape,body; float distance; b2Vec2 point,direction; float perimeter,scale,magnitude; b2Vec2 impulse; } ProbeTrace;
static ProbeTrace traces[64];static int traceCount,traceStage;
void probe_trace(int phase,int shape,int body,float distance,b2Vec2 point,b2Vec2 direction,float perimeter,float scale,float magnitude,b2Vec2 impulse)
{
    if(traceCount<64)traces[traceCount++]=(ProbeTrace){traceStage,phase,shape,body,distance,point,direction,perimeter,scale,magnitude,impulse};
    else {fprintf(stderr,"PROBE_TRACE_OVERFLOW\n");}
}

static float f(uint32_t v) { float x; memcpy(&x,&v,4); return x; }
static uint32_t u(float x) { uint32_t v; memcpy(&v,&x,4); return v; }
static b2Shape geometry(const uint32_t* p)
{
    b2Shape s={0}; s.type=(b2ShapeType)p[0];
    float r=f(p[1]),hx=f(p[2]),hy=f(p[3]),x=f(p[4]),y=f(p[5]);
                                                                             
    switch(s.type) {
    case b2_circleShape: s.circle=(b2Circle){{x,y},r}; break;
    case b2_capsuleShape: s.capsule=(b2Capsule){{x-hx,y-hy},{x+hx,y+hy},r}; break;
    case b2_polygonShape: s.polygon=b2MakeOffsetRoundedBox(hx,hy,(b2Vec2){x,y},b2Rot_identity,r); break;
    case b2_segmentShape: s.segment=(b2Segment){{x-hx,y-hy},{x+hx,y+hy}}; break;
    case b2_chainSegmentShape: s.chainSegment.segment=(b2Segment){{x-hx,y-hy},{x+hx,y+hy}}; break;
    default: break;
    }
    return s;
}
static void shapeInput(const b2Shape* s,b2Vec2 line,uint32_t* o)
{
    memset(o,0,39*sizeof(uint32_t));o[0]=s->type;int count=2;float radius=0;b2Vec2 points[8]={0};
    switch(s->type) {
    case b2_circleShape:count=1;radius=s->circle.radius;points[0]=s->circle.center;break;
    case b2_capsuleShape:radius=s->capsule.radius;points[0]=s->capsule.center1;points[1]=s->capsule.center2;break;
    case b2_segmentShape:points[0]=s->segment.point1;points[1]=s->segment.point2;break;
    case b2_chainSegmentShape:points[0]=s->chainSegment.segment.point1;points[1]=s->chainSegment.segment.point2;break;
    case b2_polygonShape:count=s->polygon.count;radius=s->polygon.radius;
        for(int j=0;j<count;++j){points[j]=s->polygon.vertices[j];o[19+2*j]=u(s->polygon.normals[j].x);o[20+2*j]=u(s->polygon.normals[j].y);}
        o[35]=u(s->polygon.centroid.x);o[36]=u(s->polygon.centroid.y);break;
    default:count=0;break;
    }
    o[1]=count;o[2]=u(radius);for(int j=0;j<count;++j){o[3+2*j]=u(points[j].x);o[4+2*j]=u(points[j].y);}
    o[37]=u(line.x);o[38]=u(line.y);
}
static void state(b2BodyId b,uint32_t* o)
{
    b2Vec2 v=b2Body_GetLinearVelocity(b),p=b2Body_GetPosition(b),c=b2Body_GetWorldCenterOfMass(b);
    b2Rot q=b2Body_GetRotation(b);
    o[0]=u(v.x);o[1]=u(v.y);o[2]=u(b2Body_GetAngularVelocity(b));o[3]=b2Body_IsAwake(b);
    o[4]=u(p.x);o[5]=u(p.y);o[6]=u(q.c);o[7]=u(q.s);o[8]=u(c.x);o[9]=u(c.y);
    o[10]=u(b2Body_GetMass(b));o[11]=u(b2Body_GetRotationalInertia(b));
    o[12]=b2Body_IsEnabled(b);o[13]=b2Body_GetType(b);
}
typedef struct LockProbe { b2WorldId w; b2BodyId body; uint32_t count,locked,before[14],after[14]; } LockProbe;
static bool lockedCallback(b2ShapeId a,b2ShapeId b,b2Manifold* manifold,void* context)
{
    (void)a;(void)b;(void)manifold;LockProbe* p=context;++p->count;
    p->locked=b2GetWorldFromId(p->w)->locked;state(p->body,p->before);
    b2ExplosionDef e=b2DefaultExplosionDef();e.radius=4;e.falloff=2;e.impulsePerLength=100;
    b2World_Explode(p->w,&e);state(p->body,p->after);return true;
}
static int nativeProbe(uint32_t kind,uint32_t* o)
{
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;
    b2WorldId w=b2CreateWorld(&wd);b2BodyDef bd=b2DefaultBodyDef();bd.type=b2_dynamicBody;
    b2BodyId b=b2CreateBody(w,&bd);b2ShapeDef sd=b2DefaultShapeDef();sd.enablePreSolveEvents=true;
    b2Circle circle={{0,0},.5f};b2CreateCircleShape(b,&sd,&circle);
    if(kind==3) {
        bd.position.x=.5f;b2BodyId other=b2CreateBody(w,&bd);b2CreateCircleShape(other,&sd,&circle);
        LockProbe p={.w=w,.body=b};b2World_SetPreSolveCallback(w,lockedCallback,&p);
        b2World_Step(w,1.0f/60.0f,1);o[0]=p.count;o[1]=p.locked;
        memcpy(o+2,p.before,sizeof p.before);memcpy(o+16,p.after,sizeof p.after);
        b2DestroyWorld(w);return 30;
    }
    state(b,o);uint32_t saved[14];memcpy(saved,o,sizeof saved);
    b2DestroyBody(b);o[14]=b2Body_IsValid(b);
    b2BodyId newer=b2CreateBody(w,&bd);b2CreateCircleShape(newer,&sd,&circle);o[15]=b2Body_IsValid(b);
    b2DestroyWorld(w);o[16]=b2World_IsValid(w);o[17]=b2Body_IsValid(newer);
    b2WorldId next=b2CreateWorld(&wd);o[18]=b2World_IsValid(w);b2DestroyWorld(next);
    if(memcmp(saved,o,sizeof saved)!=0)return 0;return 19;
}
static int probe(uint32_t kind,const uint32_t* p,uint32_t* o)
{
    if(kind==3 || kind==4)return nativeProbe(kind,o);
    if(kind==0) {
        b2ExplosionDef e=b2DefaultExplosionDef();
        o[0]=(uint32_t)e.maskBits;o[1]=(uint32_t)(e.maskBits>>32);
        o[2]=u(e.position.x);o[3]=u(e.position.y);o[4]=u(e.radius);o[5]=u(e.falloff);o[6]=u(e.impulsePerLength);
        return 7;
    }
    if(kind==5) {
        if(p[0]<3 || p[0]>8)return 0;
        b2Hull hull={0};hull.count=(int)p[0];
        for(int j=0;j<hull.count;++j)hull.points[j]=(b2Vec2){f(p[2+2*j]),f(p[3+2*j])};
        b2Shape s={0};s.type=b2_polygonShape;s.polygon=b2MakePolygon(&hull,f(p[1]));
        b2Vec2 c=b2GetShapeCentroid(&s);o[0]=u(b2GetShapePerimeter(&s));
        o[1]=u(b2GetShapeProjectedPerimeter(&s,(b2Vec2){f(p[18]),f(p[19])}));o[2]=u(c.x);o[3]=u(c.y);
        shapeInput(&s,(b2Vec2){f(p[18]),f(p[19])},o+4);return 43;
    }
    if(kind==1) {
        b2Shape s=geometry(p);b2Vec2 c=b2GetShapeCentroid(&s);
        o[0]=u(b2GetShapePerimeter(&s));o[1]=u(b2GetShapeProjectedPerimeter(&s,(b2Vec2){f(p[6]),f(p[7])}));
        o[2]=u(c.x);o[3]=u(c.y);shapeInput(&s,(b2Vec2){f(p[6]),f(p[7])},o+4);return 43;
    }
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=(b2Vec2){0,f(p[25])};wd.workerCount=1;wd.enableContinuous=false;
    b2WorldId w=b2CreateWorld(&wd);
    b2BodyDef bd=b2DefaultBodyDef();bd.type=(b2BodyType)p[0];bd.isEnabled=(p[1]&1)!=0;
    bd.isAwake=(p[1]&2)!=0;bd.fixedRotation=(p[1]&4)!=0;bd.position=(b2Vec2){f(p[6]),f(p[7])};
    bd.rotation=(b2Rot){f(p[8]),f(p[9])};bd.linearVelocity=(b2Vec2){f(p[15]),f(p[16])};bd.angularVelocity=f(p[17]);
    b2BodyId b=b2CreateBody(w,&bd);
    b2ShapeDef sd=b2DefaultShapeDef();sd.density=f(p[18]);sd.isSensor=(p[1]&8)!=0;
    sd.filter.categoryBits=(uint64_t)p[4]|((uint64_t)p[5]<<32);sd.filter.maskBits=UINT64_MAX;
    for(uint32_t j=0;j<p[3];++j) {
        uint32_t g[8]={p[2],p[10],p[11],p[12],u(f(p[13])+2.0f*(float)j*f(p[11])),p[14],0,0};
        b2Shape s=geometry(g);
        switch(s.type) {
        case b2_circleShape:b2CreateCircleShape(b,&sd,&s.circle);break;
        case b2_capsuleShape:b2CreateCapsuleShape(b,&sd,&s.capsule);break;
        case b2_polygonShape:b2CreatePolygonShape(b,&sd,&s.polygon);break;
        case b2_segmentShape:b2CreateSegmentShape(b,&sd,&s.segment);break;
        default:break;
        }
    }
    b2BodyId b2=b2_nullBodyId;
    if(p[1]&16) {
        bd.type=b2_dynamicBody;bd.position.x+=4.0f;bd.isAwake=true;bd.isEnabled=true;
        b2=b2CreateBody(w,&bd);b2Circle c={{0,0},0.5f};b2CreateCircleShape(b2,&sd,&c);
        b2DistanceJointDef jd=b2DefaultDistanceJointDef();jd.bodyIdA=b;jd.bodyIdB=b2;jd.length=4.0f;
        b2CreateDistanceJoint(w,&jd);
        if(!(p[1]&2)) b2Body_SetAwake(b,false);
    }
    for(uint32_t j=0;j<p[20];++j)b2World_Step(w,f(p[23]),(int)p[22]);
    state(b,o);
    b2ExplosionDef e={(uint64_t)p[26]|((uint64_t)p[27]<<32),{f(p[28]),f(p[29])},f(p[30]),f(p[31]),f(p[32])};
    traceStage=1;b2World_Explode(w,&e);state(b,o+14);
    if(p[33]) { b2ExplosionDef z=b2DefaultExplosionDef();z.radius=4.0f;z.falloff=2.0f;traceStage=2;b2World_Explode(w,&z); }
    for(uint32_t j=0;j<p[21];++j)b2World_Step(w,f(p[23]),(int)p[22]);
    state(b,o+28);
    o[42]=B2_IS_NULL(b2)?0:b2Body_IsAwake(b2);
    b2DestroyWorld(w);return 43;
}
int main(void)
{
    unsigned id,kind;uint32_t p[40],o[64];
    while(scanf("%u %u",&id,&kind)==2) {
        traceCount=0;
        for(int j=0;j<40;++j)if(scanf("%x",p+j)!=1)return 2;
        uint32_t before[40];memcpy(before,p,sizeof p);
        int n=probe(kind,p,o);printf("MEASURE %u %u %d",id,kind,n);
        for(int j=0;j<n;++j)printf(" %08x",o[j]);
        printf(" %u\n",memcmp(before,p,sizeof p)==0);
        for(int j=0;j<traceCount;++j) {
            ProbeTrace* t=traces+j;printf("TRACE %u %d %d %d %d %d %08x",id,t->stage,j,t->phase,t->shape,t->body,u(t->distance));
            if(t->phase==2) printf(" %08x %08x %08x %08x %08x %08x %08x %08x %08x",u(t->point.x),u(t->point.y),u(t->direction.x),u(t->direction.y),u(t->perimeter),u(t->scale),u(t->magnitude),u(t->impulse.x),u(t->impulse.y));
            printf("\n");
        }
    }
    return 0;
}
