#define _GNU_SOURCE
#include "box2d/box2d.h"
#include "box2d/collision.h"
#include "world.h"
#include "sensor.h"
#include "body.h"
#include "shape.h"
#include "contact.h"
#include "joint.h"
#include "ctz.h"
#include "array.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <fenv.h>
#include <time.h>
#ifndef OBS
#define OBS 0
#endif
static unsigned cov[400][2];
static unsigned mcov[4][3000][2];
int probe_pred(int module,const char* file,int line,int value){const char* p=strrchr(file,'/');p=p?p+1:file;const char* names[4]={"sensor.c","shape.c","body.c","world.c"};if(module>=0&&module<4&&strcmp(p,names[module])==0&&line<3000)mcov[module][line][!!value]++;return value;}
static int pred(int l,int x){if(l<400)cov[l][!!x]++;
#ifdef MUTATE
if(l==MUTATE)return 0;
#endif
return x;}
static int qcount, qmax, invalid, checks, maxSensors,maxRefs,maxBegin,maxEnd,maxBits;
static float lastDistance;
static int customCalls, preCalls, lockSeen;
static int maxBodies,maxShapes,maxContacts,maxJoints,maxChains;
static b2ShapeId lockTarget;
static int lockMeta,lockFlag,lockCapacity,lockOverlaps,lockBegin,lockCreatedShape,lockCreatedBody,lockSwapUnchanged;
static FILE* stream;
static int ops;
static uint32_t H(float f){uint32_t u;memcpy(&u,&f,4);return u;}
static float F(uint32_t u){float f;memcpy(&f,&u,4);return f;}
static void word(uint32_t u){if(stream)fwrite(&u,4,1,stream);}
static void fl(float f){checks++;if(!isfinite(f))invalid++;word(H(f));}
static b2DistanceOutput distanceObs(const b2DistanceInput* in,b2SimplexCache* c,b2Simplex* s,int n){
  b2DistanceOutput r=b2ShapeDistance(in,c,s,n);qcount++;lastDistance=r.distance;if(!isfinite(r.distance))invalid++;return r;
}
#if OBS
#define if(...) if(pred(__LINE__,(__VA_ARGS__)))
#define b2ShapeDistance distanceObs
#endif
#include "sensor.c"
#if OBS
#undef if
#undef b2ShapeDistance
#endif
#define b2Shape_EnableSensorEvents(...) (ops++,b2Shape_EnableSensorEvents(__VA_ARGS__))
#define b2Body_SetTransform(...) (ops++,b2Body_SetTransform(__VA_ARGS__))
#define b2Body_SetLinearVelocity(...) (ops++,b2Body_SetLinearVelocity(__VA_ARGS__))
#define b2Body_Enable(...) (ops++,b2Body_Enable(__VA_ARGS__))
#define b2Body_Disable(...) (ops++,b2Body_Disable(__VA_ARGS__))
#define b2Body_SetAwake(...) (ops++,b2Body_SetAwake(__VA_ARGS__))
#define b2Shape_SetFilter(...) (ops++,b2Shape_SetFilter(__VA_ARGS__))
#define b2Shape_SetCircle(...) (ops++,b2Shape_SetCircle(__VA_ARGS__))
#define b2Shape_SetDensity(...) (ops++,b2Shape_SetDensity(__VA_ARGS__))
#define b2DestroyShape(...) (ops++,b2DestroyShape(__VA_ARGS__))
#define b2DestroyBody(...) (ops++,b2DestroyBody(__VA_ARGS__))
#define b2World_SetCustomFilterCallback(...) (ops++,b2World_SetCustomFilterCallback(__VA_ARGS__))
#define b2World_SetPreSolveCallback(...) (ops++,b2World_SetPreSolveCallback(__VA_ARGS__))
#define b2Shape_EnablePreSolveEvents(...) (ops++,b2Shape_EnablePreSolveEvents(__VA_ARGS__))
#define b2Shape_EnableContactEvents(...) (ops++,b2Shape_EnableContactEvents(__VA_ARGS__))
#define b2Shape_EnableHitEvents(...) (ops++,b2Shape_EnableHitEvents(__VA_ARGS__))
#define b2CreateChain(...) (ops++,b2CreateChain(__VA_ARGS__))
#define b2CreateDistanceJoint(...) (ops++,b2CreateDistanceJoint(__VA_ARGS__))
static int beginTotal,endTotal,everOverlap;
static b2WorldId world(int continuous,int warm){ops++;b2WorldDef d=b2DefaultWorldDef();d.gravity=(b2Vec2){0,0};d.enableContinuous=continuous;d.enableSleep=true;b2WorldId w=b2CreateWorld(&d);b2World_EnableWarmStarting(w,warm);return w;}
static b2BodyId body(b2WorldId w,int t,float x,float y,int awake,int enabled,int bullet){ops++;b2BodyDef d=b2DefaultBodyDef();d.type=t;d.position=(b2Vec2){x,y};d.isAwake=awake;d.isEnabled=enabled;d.isBullet=bullet;return b2CreateBody(w,&d);}
static b2ShapeId shape(b2BodyId b,int sensor,int events,int geom,float radius){
 ops++;
 b2ShapeDef d=b2DefaultShapeDef();d.isSensor=sensor;d.enableSensorEvents=events;d.invokeContactCreation=false;
 if(geom==0){b2Circle c={{0,0},radius};return b2CreateCircleShape(b,&d,&c);}
 if(geom==1){b2Capsule c={{-.5f,0},{.5f,0},radius};return b2CreateCapsuleShape(b,&d,&c);}
 if(geom==2){b2Polygon p=b2MakeRoundedBox(.6f,.4f,radius);return b2CreatePolygonShape(b,&d,&p);}
 if(geom>=10){int n=geom-7;b2Vec2 points[8];for(int i=0;i<n;i++){float a=2*3.14159265358979323846f*i/n;points[i]=(b2Vec2){.6f*cosf(a),.6f*sinf(a)};}b2Hull h=b2ComputeHull(points,n);b2Polygon p=b2MakePolygon(&h,radius);printf("POLY %d",n);for(int i=0;i<p.count;i++)printf(" %08x %08x",H(p.vertices[i].x),H(p.vertices[i].y));printf("\nPOLYMETA %d %08x %08x",n,H(p.centroid.x),H(p.centroid.y));for(int i=0;i<p.count;i++)printf(" %08x %08x",H(p.normals[i].x),H(p.normals[i].y));printf("\n");return b2CreatePolygonShape(b,&d,&p);}
 b2Segment s={{-.5f,0},{.5f,0}};return b2CreateSegmentShape(b,&d,&s);
}
static bool custom(b2ShapeId a,b2ShapeId b,void* p){(void)a;(void)b;(void)p;customCalls++;return false;}
static bool pre(b2ShapeId a,b2ShapeId b,b2Manifold* m,void* p){(void)a;(void)b;(void)m;b2WorldId w=*(b2WorldId*)p;b2World* v=b2GetWorldFromId(w);preCalls++;lockSeen|=v->locked;lockMeta=b2Shape_IsSensor(lockTarget);lockFlag=b2Shape_AreSensorEventsEnabled(lockTarget);lockCapacity=b2Shape_GetSensorCapacity(lockTarget);b2ShapeId out[1];lockOverlaps=b2Shape_GetSensorOverlaps(lockTarget,out,1);lockBegin=b2World_GetSensorEvents(w).beginCount;b2Shape_EnableSensorEvents(lockTarget,false);int oldIndex=v->endEventArrayIndex;b2World_Step(w,1.f/60,1);lockSwapUnchanged=oldIndex==v->endEventArrayIndex;b2ShapeDef sd=b2DefaultShapeDef();sd.isSensor=true;b2Circle circle={{0,0},1};lockCreatedShape=b2CreateCircleShape(b2Shape_GetBody(lockTarget),&sd,&circle).index1;b2BodyDef bd=b2DefaultBodyDef();lockCreatedBody=b2CreateBody(w,&bd).index1;return true;}
static void snapshot(b2WorldId id){
 b2World* w=b2GetWorldFromId(id);b2SensorEvents e=b2World_GetSensorEvents(id);word(e.beginCount);word(e.endCount);
 word(id.index1);word(id.generation);
 b2Counters co=b2World_GetCounters(id);if(co.bodyCount>maxBodies)maxBodies=co.bodyCount;if(co.shapeCount>maxShapes)maxShapes=co.shapeCount;if(co.contactCount>maxContacts)maxContacts=co.contactCount;if(co.jointCount>maxJoints)maxJoints=co.jointCount;int ch=b2GetIdCount(&w->chainIdPool);if(ch>maxChains)maxChains=ch;
 beginTotal+=e.beginCount;endTotal+=e.endCount;if(e.beginCount>maxBegin)maxBegin=e.beginCount;
 for(int j=0;j<e.beginCount;j++){b2SensorBeginTouchEvent a=e.beginEvents[j];word(a.sensorShapeId.index1);word(a.sensorShapeId.generation);word(a.visitorShapeId.index1);word(a.visitorShapeId.generation);}
 for(int j=0;j<e.endCount;j++){b2SensorEndTouchEvent a=e.endEvents[j];word(a.sensorShapeId.index1);word(a.sensorShapeId.generation);word(a.visitorShapeId.index1);word(a.visitorShapeId.generation);}
 if(w->sensors.count>maxSensors)maxSensors=w->sensors.count;
 int refs=0;
 for(int i=0;i<w->sensors.count;i++){
  b2Sensor* s=w->sensors.data+i;refs+=s->overlaps1.count+s->overlaps2.count;word(s->shapeId);word(s->overlaps1.count);word(s->overlaps2.count);
  everOverlap+=s->overlaps2.count;
  for(int k=0;k<2;k++){b2ShapeRefArray* r=k?&s->overlaps2:&s->overlaps1;for(int j=0;j<r->count;j++){word(r->data[j].shapeId);word(r->data[j].generation);}}
 }
 if(refs>maxRefs)maxRefs=refs;
 for(int i=0;i<2;i++)if(w->sensorEndEvents[i].count>maxEnd)maxEnd=w->sensorEndEvents[i].count;
 int blocks=w->sensorTaskContexts.data[0].eventBits.blockCount;if(blocks>maxBits)maxBits=blocks;
 word(w->sensors.count);word(w->endEventArrayIndex);word(blocks);for(int i=0;i<blocks;i++){uint64_t z=w->sensorTaskContexts.data[0].eventBits.bits[i];word((uint32_t)z);word(z>>32);}
 for(int i=0;i<2;i++){word(w->sensorEndEvents[i].count);for(int j=0;j<w->sensorEndEvents[i].count;j++){b2SensorEndTouchEvent a=w->sensorEndEvents[i].data[j];word(a.sensorShapeId.index1);word(a.sensorShapeId.generation);word(a.visitorShapeId.index1);word(a.visitorShapeId.generation);}}
 for(int i=0;i<w->bodies.count;i++){b2Body* b=w->bodies.data+i;if(b->id<0)continue;b2BodyId bi={i+1,w->worldId,b->generation};b2Transform t=b2Body_GetTransform(bi);fl(t.p.x);fl(t.p.y);fl(t.q.c);fl(t.q.s);b2Vec2 v=b2Body_GetLinearVelocity(bi);fl(v.x);fl(v.y);fl(b2Body_GetAngularVelocity(bi));fl(b2Body_GetMass(bi));fl(b->inertia);fl(b->sleepThreshold);fl(b->sleepTime);
 b2BodySim* z=b2GetBodySim(w,b);fl(z->center.x);fl(z->center.y);fl(z->center0.x);fl(z->center0.y);fl(z->rotation0.c);fl(z->rotation0.s);fl(z->localCenter.x);fl(z->localCenter.y);fl(z->force.x);fl(z->force.y);fl(z->torque);fl(z->invMass);fl(z->invInertia);fl(z->minExtent);fl(z->maxExtent);fl(z->linearDamping);fl(z->angularDamping);fl(z->gravityScale);
 b2BodyState* st=b2GetBodyState(w,b);if(st){fl(st->linearVelocity.x);fl(st->linearVelocity.y);fl(st->angularVelocity);fl(st->deltaPosition.x);fl(st->deltaPosition.y);fl(st->deltaRotation.c);fl(st->deltaRotation.s);}}
 for(int i=0;i<w->shapes.count;i++){b2Shape* s=w->shapes.data+i;if(s->id<0)continue;word(s->id);word(s->generation);word(s->sensorIndex);word(s->enableSensorEvents);word(s->enableContactEvents);word(s->enableHitEvents);word(s->enablePreSolveEvents);fl(s->density);fl(s->friction);fl(s->restitution);fl(s->rollingResistance);fl(s->tangentSpeed);fl(s->aabb.lowerBound.x);fl(s->aabb.lowerBound.y);fl(s->aabb.upperBound.x);fl(s->aabb.upperBound.y);fl(s->fatAABB.lowerBound.x);fl(s->fatAABB.lowerBound.y);fl(s->fatAABB.upperBound.x);fl(s->fatAABB.upperBound.y);fl(s->localCentroid.x);fl(s->localCentroid.y);b2ShapeProxy p=b2MakeShapeDistanceProxy(s);fl(p.radius);for(int j=0;j<p.count;j++){fl(p.points[j].x);fl(p.points[j].y);}}
 for(int i=0;i<w->contacts.count;i++){b2Contact* c=w->contacts.data+i;if(c->contactId<0)continue;b2ContactSim* z=b2GetContactSim(w,c);fl(z->invMassA);fl(z->invMassB);fl(z->invIA);fl(z->invIB);fl(z->friction);fl(z->restitution);fl(z->tangentSpeed);fl(z->manifold.normal.x);fl(z->manifold.normal.y);fl(z->manifold.rollingImpulse);if(z->manifold.pointCount)fl(z->rollingResistance);else word(0);for(int j=0;j<z->manifold.pointCount;j++){b2ManifoldPoint* p=z->manifold.points+j;fl(p->point.x);fl(p->point.y);fl(p->anchorA.x);fl(p->anchorA.y);fl(p->anchorB.x);fl(p->anchorB.y);fl(p->separation);fl(p->normalImpulse);fl(p->tangentImpulse);fl(p->totalNormalImpulse);fl(p->normalVelocity);}}
 for(int i=0;i<w->joints.count;i++){b2Joint* j=w->joints.data+i;if(j->jointId<0)continue;b2JointSim* z=b2GetJointSim(w,j);fl(z->localOriginAnchorA.x);fl(z->localOriginAnchorA.y);fl(z->localOriginAnchorB.x);fl(z->localOriginAnchorB.y);fl(z->invMassA);fl(z->invMassB);fl(z->invIA);fl(z->invIB);fl(z->constraintHertz);fl(z->constraintDampingRatio);fl(z->constraintSoftness.biasRate);fl(z->constraintSoftness.massScale);fl(z->constraintSoftness.impulseScale);if(z->type==b2_distanceJoint){b2DistanceJoint* d=&z->distanceJoint;fl(d->length);fl(d->hertz);fl(d->dampingRatio);fl(d->minLength);fl(d->maxLength);fl(d->maxMotorForce);fl(d->motorSpeed);fl(d->impulse);fl(d->lowerImpulse);fl(d->upperImpulse);fl(d->motorImpulse);fl(d->anchorA.x);fl(d->anchorA.y);fl(d->anchorB.x);fl(d->anchorB.y);fl(d->deltaCenter.x);fl(d->deltaCenter.y);fl(d->distanceSoftness.biasRate);fl(d->distanceSoftness.massScale);fl(d->distanceSoftness.impulseScale);fl(d->axialMass);}}
 if(qcount>qmax)qmax=qcount;qcount=0;
}
static void step(b2WorldId w,float dt,int sub){ops++;b2World_Step(w,dt,sub);snapshot(w);}
static void reset(void){memset(cov,0,sizeof(cov));ops=qcount=qmax=invalid=checks=maxSensors=maxRefs=maxBegin=maxEnd=maxBits=0;maxBodies=maxShapes=maxContacts=maxJoints=maxChains=0;customCalls=preCalls=lockSeen=beginTotal=endTotal=everOverlap=0;}
static void metric(int id){printf("CASE %d ops%d begin%d end%d overlaps%d sensors%d refs%d maxBegin%d maxEnd%d bits%d queryMax%d checks%d invalid%d custom%d pre%d lock%d B%d S%d C%d J%d Chain%d\n",id,ops,beginTotal,endTotal,everOverlap,maxSensors,maxRefs,maxBegin,maxEnd,maxBits,qmax,checks,invalid,customCalls,preCalls,lockSeen,maxBodies,maxShapes,maxContacts,maxJoints,maxChains);for(int l=0;l<400;l++)if(cov[l][0]||cov[l][1])printf("BR %d 0 %d %u %u\n",id,l,cov[l][0],cov[l][1]);for(int m=1;m<4;m++)for(int l=0;l<3000;l++)if(mcov[m][l][0]||mcov[m][l][1])printf("BR %d %d %d %u %u\n",id,m,l,mcov[m][l][0],mcov[m][l][1]);}
static void longcase(int id){
 int f=(id-25)/6+1,v=(id-25)%6;int subs[6]={1,4,8,1,4,8};int n=(f==8||f==11)?1200:600;
 b2WorldId w=world(f==10,v>=3);b2BodyId bs=body(w,(f==1)?v%3:0,0,0,1,1,0);
 b2ShapeId s=shape(bs,1,1,(f==5)?10+v:0,1);
 b2BodyId bv=body(w,(f==1)?(v/3+1)%3:2,0,0,(f==4)?0:1,1,f==10);b2ShapeId a=shape(bv,f==1&&v>=3,1,(f==5)?(v+1)%4:0,.2f);
 b2BodyId extras[127];b2ShapeId ex[127];int ec=0;
 b2SensorBeginTouchEvent saved={0};
 if(f==1){b2BodyId bstatic=body(w,0,0,0,1,1,0);shape(bstatic,0,1,0,.2f);shape(bs,0,1,0,.2f);}
 if(f==6){b2BodyId ground=body(w,0,0,-.5f,1,1,0);b2Vec2 pts[5]={{-3,0},{-2,0},{0,0},{2,0},{3,0}};b2SurfaceMaterial m=b2DefaultSurfaceMaterial();b2ChainDef cd=b2DefaultChainDef();cd.points=pts;cd.count=5;cd.materials=&m;cd.materialCount=1;cd.enableSensorEvents=true;b2CreateChain(ground,&cd);}
 if(f==10){b2DistanceJointDef jd=b2DefaultDistanceJointDef();jd.bodyIdA=bs;jd.bodyIdB=bv;jd.length=.5f;jd.collideConnected=false;b2CreateDistanceJoint(w,&jd);}
 if(f==12){for(int i=1;i<65;i++){extras[ec]=bs;ex[ec++]=shape(bs,1,1,0,1);} }
 for(int k=0;k<n;k++){
  if(f==2&&k%50==0){b2Shape_EnableSensorEvents((k/50)%2?s:a,(k/100)%2==0);}
  if(f==3&&k%50==0){b2Filter z=b2DefaultFilter();int phase=(k/50)%6;if(phase==1)z.maskBits=0;if(phase==2)z.categoryBits=UINT64_C(1)<<63;if(phase==3)z.groupIndex=-1;if(phase==4){z.groupIndex=1;z.maskBits=0;}b2Shape_SetFilter((k/50)%2?s:a,z);}
  if(f==4&&k%100==0){b2BodyId target=v<3?bs:bv;if((k/100)%2)b2Body_Enable(target);else b2Body_Disable(target);}
  if(f==4&&k%100==50)b2Body_SetAwake(bv,false);
  if(f==5&&k>0&&k%60==0){b2Circle c={{0,0},.1f+.01f*(k%3)};if(v%4==0)b2Shape_SetCircle(s,&c);}
  if(f==7&&k==200){b2DestroyShape(s,true);s=shape(bs,1,1,0,1);}
  if(f==7&&k==400){b2DestroyBody(bv);bv=body(w,2,0,0,1,1,0);a=shape(bv,0,1,0,.2f);}
  if(f==8&&k%100==50){b2DestroyShape(a,true);a=shape(bv,0,1,0,.2f);}
  if(f==8&&k==800){b2DestroyWorld(w);w=world(0,v>=3);bs=body(w,0,0,0,1,1,0);s=shape(bs,1,1,0,1);bv=body(w,2,0,0,1,1,0);a=shape(bv,0,1,0,.2f);word(saved.sensorShapeId.index1);word(saved.sensorShapeId.generation);word(saved.visitorShapeId.index1);word(saved.visitorShapeId.generation);printf("LONG_WORLD_COPY sensor%d visitor%d oldgen%u worldgen%u\n",saved.sensorShapeId.index1,saved.visitorShapeId.index1,saved.visitorShapeId.generation,w.generation);}
  if(f==9&&k%20==0){if(ec){b2DestroyBody(extras[0]);ec=0;}extras[0]=body(w,2,0,0,1,1,0);ex[0]=shape(extras[0],0,1,0,.1f);ec=1;}
  if(f==11&&k%100==50){b2DestroyShape(a,true);a=shape(bv,0,1,0,.2f);step(w,0,subs[v]);step(w,0,subs[v]);}
  if(f==12&&k==200){b2DestroyShape(ex[0],true);ex[0]=shape(bs,1,1,0,1);}
  if(f==12&&k==400){for(int i=0;i<ec;i++)b2DestroyShape(ex[i],true);ec=0;}
  if(f==12&&k==450){for(int i=0;i<126;i++){extras[ec]=bs;ex[ec++]=shape(bs,1,1,0,1);}}
  if(f==10){b2Body_SetTransform(bv,(b2Vec2){-2,0},b2Rot_identity);b2Body_SetLinearVelocity(bv,(b2Vec2){240,0});}
  else if(f!=4&&k%60==0){float x=(k%120<60)?.3f:2.5f;float y=(f==6&&k%240>=120)?-1:0;b2Body_SetTransform(bv,(b2Vec2){x,y},b2Rot_identity);if(f==6)b2Body_SetTransform(bs,(b2Vec2){x,y},b2Rot_identity);}
  step(w,1.0f/60.0f,subs[v]);
  if(f==6&&(k==0||k==120))printf("CHAIN_SIDE k%d sensorY%08x visitorY%08x capacity%d\n",k,H(b2Body_GetPosition(bs).y),H(b2Body_GetPosition(bv).y),b2Shape_GetSensorCapacity(s));
  if(f==8&&k==0){b2SensorEvents e=b2World_GetSensorEvents(w);if(e.beginCount)saved=e.beginEvents[0];}
  if(f==11&&k%100==0){b2ShapeId one[1]={{0}},two[1]={{0}},fresh[1]={{0}};int n1=b2Shape_GetSensorOverlaps(s,one,1);memcpy(two,one,sizeof(one));if(n1)one[0].index1++;int nn=b2Shape_GetSensorOverlaps(s,fresh,1);ops+=7;word(n1);word(nn);word(one[0].index1);word(two[0].index1);word(fresh[0].index1);}
 }
 b2DestroyWorld(w);
}
static void shortcase(int id){
 b2WorldId w=world(0,1);b2BodyId bs=body(w,0,0,0,1,1,0),bv=body(w,2,0,0,1,1,0);
 b2ShapeId s=shape(bs,1,(id<=4)?(id-1)/2:1,0,1),a=shape(bv,0,(id<=4)?(id-1)%2:1,0,.2f);
 if(id==5){printf("BEFORE sensor%d events%d capacity%d begin%d\n",b2Shape_IsSensor(s),b2Shape_AreSensorEventsEnabled(s),b2Shape_GetSensorCapacity(s),b2World_GetSensorEvents(w).beginCount);}
 if(id==24){b2World* p=b2GetWorldFromId(w);int before=p->broadPhase.moveArray.count;shape(bs,0,1,0,.2f);printf("PROXY_BEFORE afterSensorAndDynamic%d afterStaticSolid%d sensors%d\n",before,p->broadPhase.moveArray.count,p->sensors.count);}
 step(w,1.f/60,4);
 if(id==6){step(w,1.f/60,4);}
 if(id==7){b2Body_SetTransform(bv,(b2Vec2){4,0},b2Rot_identity);step(w,1.f/60,4);}
 if(id==8){b2Shape_EnableSensorEvents(s,false);step(w,1.f/60,4);}
 if(id==9){printf("SOLID capacity%d\n",b2Shape_GetSensorCapacity(a));}
 if(id==10){b2ShapeId out[2];printf("TRUNC %d %d\n",b2Shape_GetSensorOverlaps(s,out,0),b2Shape_GetSensorOverlaps(s,out,1));}
 if(id>=11&&id<=14){if(id==11)b2DestroyShape(a,true);if(id==12)b2DestroyShape(s,true);if(id==13)b2DestroyBody(bv);if(id==14)b2DestroyBody(bs);b2World* z=b2GetWorldFromId(w);printf("DESTROY_NOW %d publicEnd%d privateEnd0_%d privateEnd1_%d writeIndex%d\n",id,b2World_GetSensorEvents(w).endCount,z->sensorEndEvents[0].count,z->sensorEndEvents[1].count,z->endEventArrayIndex);if(id==11||id==13){b2ShapeId out[1];printf("HISTORY count%d returned%d visitorValid%d\n",b2Shape_GetSensorCapacity(s),b2Shape_GetSensorOverlaps(s,out,1),b2Shape_IsValid(a));}snapshot(w);step(w,0,4);printf("AFTER_ZERO %d publicEnd%d\n",id,b2World_GetSensorEvents(w).endCount);step(w,0,4);printf("AFTER_TWO_ZERO %d publicEnd%d\n",id,b2World_GetSensorEvents(w).endCount);if(id==11||id==13){step(w,1.f/60,4);printf("AFTER_POSITIVE %d publicEnd%d capacity%d\n",id,b2World_GetSensorEvents(w).endCount,b2Shape_GetSensorCapacity(s));}}
 if(id==15){b2Filter z=b2DefaultFilter();z.maskBits=0;b2Shape_SetFilter(s,z);snapshot(w);step(w,1.f/60,4);}
 if(id==16){b2Circle c={{0,0},.01f};b2Shape_SetCircle(s,&c);b2Body_SetTransform(bv,(b2Vec2){.5f,0},b2Rot_identity);snapshot(w);step(w,1.f/60,4);}
 if(id==17){b2Body_SetTransform(bv,(b2Vec2){4,0},b2Rot_identity);snapshot(w);step(w,1.f/60,4);}
 if(id==18){step(w,0,4);step(w,0,4);}
 if(id==19){b2SensorEvents e=b2World_GetSensorEvents(w);b2SensorBeginTouchEvent copy=e.beginEvents[0];step(w,1.f/60,4);printf("COPY %d %u %d %u\n",copy.sensorShapeId.index1,copy.sensorShapeId.generation,copy.visitorShapeId.index1,copy.visitorShapeId.generation);}
 if(id==20){b2World_SetCustomFilterCallback(w,custom,NULL);step(w,1.f/60,4);}
 if(id==21){b2Body_SetAwake(bv,false);step(w,1.f/60,4);printf("SLEEP awake%d\n",b2Body_IsAwake(bv));}
 if(id==22){b2Body_Disable(bs);step(w,1.f/60,4);}
 if(id==23){b2BodyId b=body(w,2,10,0,1,1,0);b2ShapeId x=shape(b,1,1,0,1);float m=b2Body_GetMass(b);b2Shape_SetDensity(x,0,true);printf("SENSOR_MASS positive%08x zeroDensity%08x\n",H(m),H(b2Body_GetMass(b)));snapshot(w);}
 if(id==24){b2World* p=b2GetWorldFromId(w);printf("PROXY moves%d sensors%d\n",p->broadPhase.moveArray.count,p->sensors.count);}
 b2DestroyWorld(w);
}
static void directcase(int id){
 if(id<=8){ops++;static int v[8][4]={{0,0,0,0},{0,0,1,0},{1,0,0,0},{0,0,0,1},{0,1,0,0},{0,65535,0,65535},{1,65535,2,0},{2,0,1,65535}};b2ShapeRef a={v[id-1][0],v[id-1][1]},b={v[id-1][2],v[id-1][3]};int r=b2CompareShapeRefs(&a,&b);word(r);printf("CMP %d %d\n",id,r);return;}
 if(id==64){ops++;b2ShapeDef d=b2DefaultShapeDef();b2WorldDef w=b2DefaultWorldDef();word(H(d.density));word(d.isSensor);word(d.enableSensorEvents);word(d.enableContactEvents);word(d.enableHitEvents);word(d.enablePreSolveEvents);printf("DEFAULT %08x %d %d continuous%d\n",H(d.density),d.isSensor,d.enableSensorEvents,w.enableContinuous);ops++;d.density=0;d.isSensor=true;d.enableSensorEvents=true;word(H(d.density));word(d.isSensor);word(d.enableSensorEvents);word(d.enableContactEvents);word(d.enableHitEvents);word(d.enablePreSolveEvents);printf("CONVENIENT_POLICY %08x %d %d\n",H(d.density),d.isSensor,d.enableSensorEvents);return;}
 if(id==62){for(int route=0;route<6;route++){b2WorldId w=world(0,1);if(route%2==0)b2World_SetCustomFilterCallback(w,custom,NULL);b2BodyId bs=body(w,0,0,0,1,route<4,0),bv=body(w,2,0,0,1,1,0);b2ShapeId s=shape(bs,1,route<2,0,1);shape(bv,0,1,0,.2f);if(route%2)b2World_SetCustomFilterCallback(w,custom,NULL);int before=customCalls;step(w,1.f/60,4);printf("B18_RAW route%d sensorCount%d enabled%d events%d hook%d queryCustom%d capacity%d\n",route,b2GetWorldFromId(w)->sensors.count,b2Body_IsEnabled(bs),b2Shape_AreSensorEventsEnabled(s),b2GetWorldFromId(w)->customFilterFcn!=NULL,customCalls-before,b2Shape_GetSensorCapacity(s));b2BodyId b=body(w,0,10,0,1,1,0),c=body(w,2,10.1f,0,1,1,0);shape(b,0,1,0,1);shape(c,0,1,0,1);before=customCalls;step(w,1.f/60,4);printf("B18_CONTROL route%d solidCustomCalls%d\n",route,customCalls-before);b2DestroyWorld(w);}return;}
 b2WorldId w=world(id==60,1);b2BodyId bs=body(w,0,0,0,1,1,0),bv=body(w,2,0,0,1,1,id==60);
 b2ShapeId s=shape(bs,1,1,0,id==39?.1f:1),a=shape(bv,0,1,0,id==39?.1f:.2f);
 b2ShapeId originalVisitor=a; b2BodyId other={0};if(id==13||id==14){other=body(w,2,id==13?0:4,0,1,1,0);shape(other,0,1,0,.2f);if(id==13)b2Body_SetTransform(bv,(b2Vec2){4,0},b2Rot_identity);}
 if(id>=33&&id<=35){b2Circle point={{0,0},0};b2Shape_SetCircle(s,&point);b2Shape_SetCircle(a,&point);float threshold=10*FLT_EPSILON;uint32_t u=H(threshold)+(id-34);b2Body_SetTransform(bv,(b2Vec2){F(u),0},b2Rot_identity);printf("THRESH %d input%08x threshold%08x\n",id,u,H(threshold));}
 if(id==39){b2Body_SetTransform(bv,(b2Vec2){.00001f,0},b2Rot_identity);b2DistanceInput in={0};b2Circle c={{0,0},.1f};in.proxyA=b2MakeProxy(&c.center,1,c.radius);in.proxyB=in.proxyA;in.transformA=b2Transform_identity;in.transformB=b2Body_GetTransform(bv);in.useRadii=true;b2SimplexCache cache={0};b2DistanceOutput out=b2ShapeDistance(&in,&cache,NULL,0);printf("B14 x%08x radii%08x distance%08x threshold%08x\n",H(.00001f),H(.1f),H(out.distance),H(10*FLT_EPSILON));}
 if(id==17){shape(bs,0,1,0,.2f);}
 if(id==18)b2Shape_EnableSensorEvents(a,false);
 if(id==19){b2Filter f=b2DefaultFilter();f.maskBits=0;b2Shape_SetFilter(a,f);}
 if(id==20){b2Filter f=b2DefaultFilter();f.maskBits=0;f.groupIndex=1;b2Shape_SetFilter(a,f);b2Shape_SetFilter(s,f);}
 if(id==21){b2Filter f=b2DefaultFilter();f.groupIndex=-1;b2Shape_SetFilter(a,f);b2Shape_SetFilter(s,f);}
 if(id==22)b2Body_SetTransform(bv,(b2Vec2){1,1},b2Rot_identity);
 if(id>=23&&id<=26){b2DestroyShape(s,true);s=shape(bs,1,1,id-23,1);b2DestroyShape(a,true);a=shape(bv,0,1,id-23,.2f);printf("SENSOR_FACTORY geom%d isSensor%d events%d\n",id-23,b2Shape_IsSensor(s),b2Shape_AreSensorEventsEnabled(s));}
 if(id==27||id==28){b2DestroyShape(a,true);a=shape(bv,1,id==27,0,.2f);}
 if(id==27){lockTarget=s;b2Shape_EnableContactEvents(s,true);b2Shape_EnableContactEvents(a,true);b2Shape_EnableHitEvents(s,true);b2Shape_EnableHitEvents(a,true);b2Shape_EnablePreSolveEvents(s,true);b2Shape_EnablePreSolveEvents(a,true);b2World_SetPreSolveCallback(w,pre,&w);}
 if(id==29)b2Body_SetAwake(bv,false);
 if(id==30)b2Body_Disable(bv);
 if(id==31)b2Shape_EnableSensorEvents(s,false);
 if(id==32){b2World_SetCustomFilterCallback(w,custom,NULL);}
 if(id==36){b2Filter z=b2DefaultFilter();z.categoryBits=UINT64_C(1)<<63;b2Shape_SetFilter(a,z);z=b2DefaultFilter();z.maskBits=UINT64_C(1)<<63;b2Shape_SetFilter(s,z);}
 if(id==37){b2Filter z=b2DefaultFilter();z.groupIndex=1;b2Shape_SetFilter(s,z);z.maskBits=0;b2Shape_SetFilter(a,z);}
 if(id==38){b2Filter z=b2DefaultFilter();z.maskBits=0;b2Shape_SetFilter(s,z);}
 if(id==40){shape(bv,0,1,1,.1f);shape(bv,0,1,2,.1f);}
 if(id==16){for(int i=0;i<65534;i++){b2DestroyShape(a,true);a=shape(bv,0,1,0,.5f);}printf("GEN_BEFORE %u\n",a.generation);}
 if(id==60){b2Body_SetTransform(bv,(b2Vec2){-2,0},b2Rot_identity);b2Body_SetLinearVelocity(bv,(b2Vec2){240,0});}
 step(w,1.f/60,4);
 if(id>=33&&id<=35)printf("THRESH_RESULT %d distance%08x overlap%d\n",id,H(lastDistance),b2Shape_GetSensorCapacity(s));
 if(id>=9&&id<=16){
  if(id==9)b2Body_SetTransform(bv,(b2Vec2){4,0},b2Rot_identity);
  if(id==10)shape(bv,0,1,0,.2f);
  if(id==11){b2DestroyShape(a,true);a=shape(bv,0,1,0,.2f);}
  if(id==12){for(int i=0;i<65536;i++){b2DestroyShape(a,true);a=shape(bv,0,1,0,.5f);}printf("WRAP creates65536 destroys65536 rawgen%u oldRawValid%d\n",a.generation,b2Shape_IsValid(originalVisitor));}
  if(id==13){b2Body_SetTransform(bv,(b2Vec2){0,0},b2Rot_identity);b2Body_SetTransform(other,(b2Vec2){4,0},b2Rot_identity);}
  if(id==14){b2Body_SetTransform(bv,(b2Vec2){4,0},b2Rot_identity);b2Body_SetTransform(other,(b2Vec2){0,0},b2Rot_identity);}
  if(id==15)step(w,1.f/60,4);
  if(id==16){b2DestroyShape(a,true);a=shape(bv,0,1,0,.2f);printf("GEN_AFTER %u\n",a.generation);}
  step(w,1.f/60,4);
 }
 if(id>=41&&id<=48){b2BodyId bx=(id==42||id==44)?body(w,0,0,0,1,1,0):bs;b2ShapeId x=shape(bx,1,1,0,1);step(w,1.f/60,4);if(id==45)b2DestroyShape(a,true);if(id==46)b2DestroyBody(bv);if(id==48){b2SensorEvents e=b2World_GetSensorEvents(w);b2SensorBeginTouchEvent saved=e.beginEvents[0];b2DestroyWorld(w);word(saved.sensorShapeId.index1);word(saved.visitorShapeId.index1);printf("WORLD_DESTROY_COPY sensor%d visitor%d\n",saved.sensorShapeId.index1,saved.visitorShapeId.index1);return;}if(id==43)b2DestroyShape(x,true);else if(id==44)b2DestroyBody(bx);else if(id==47){b2DestroyShape(x,true);b2DestroyShape(s,true);}else if(id%2)b2DestroyShape(s,true);else b2DestroyBody(bs);snapshot(w);step(w,0,4);if(id==41||id==42){b2Shape_EnableSensorEvents(x,true);step(w,1.f/60,4);}}
 if(id>=49&&id<=56){if(id==49||id==50){step(w,0,4);if(id==50)step(w,0,4);}if(id==51)b2Shape_EnableSensorEvents(s,false);if(id==52)b2Body_Disable(bs);if(id==53||id==54){if(id==54)b2DestroyBody(bv);for(int i=1;i<(id==53?65:128);i++)shape(bs,1,1,0,1);}if(id==55)b2DestroyShape(s,true);if(id==56){b2DestroyShape(s,true);b2DestroyBody(bv);}step(w,1.f/60,4);}
 if(id==57){b2ShapeId z[3];printf("CAP %d %d %d %d solidOverlaps%d\n",b2Shape_GetSensorCapacity(s),b2Shape_GetSensorOverlaps(s,z,0),b2Shape_GetSensorOverlaps(s,z,1),b2Shape_GetSensorCapacity(a),b2Shape_GetSensorOverlaps(a,z,1));}
 if(id==58){b2Shape_EnableSensorEvents(s,true);step(w,1.f/60,4);}
 if(id==59){printf("FLAGS %d %d %d %d\n",b2Shape_IsSensor(s),b2Shape_AreSensorEventsEnabled(s),b2Shape_IsSensor(a),b2Shape_AreSensorEventsEnabled(a));b2BodyId extra=body(w,2,10,0,1,1,0);b2ShapeDef d=b2DefaultShapeDef();d.isSensor=true;d.enableSensorEvents=true;d.updateBodyMass=false;b2Circle c={{0,0},1};ops++;b2CreateCircleShape(extra,&d,&c);float before=b2Body_GetMass(extra);ops++;b2Body_ApplyMassFromShapes(extra);printf("RAW_UPDATE_MASS before%08x after%08x\n",H(before),H(b2Body_GetMass(extra)));snapshot(w);}
 if(id==61){b2Body_SetAwake(bv,false);b2Shape_EnableSensorEvents(a,false);printf("SOLID_FLAG isSensor%d events%d awake%d\n",b2Shape_IsSensor(a),b2Shape_AreSensorEventsEnabled(a),b2Body_IsAwake(bv));step(w,1.f/60,4);}
 if(id==60){printf("CCD_FAST begin%d overlaps%d x%08x\n",b2World_GetSensorEvents(w).beginCount,b2Shape_GetSensorCapacity(s),H(b2Body_GetPosition(bv).x));b2Body_SetTransform(bv,(b2Vec2){-2,0},b2Rot_identity);b2Body_SetLinearVelocity(bv,(b2Vec2){60,0});step(w,1.f/60,4);printf("CCD_ENDPOINT begin%d overlaps%d x%08x\n",b2World_GetSensorEvents(w).beginCount,b2Shape_GetSensorCapacity(s),H(b2Body_GetPosition(bv).x));}
 if(id==63){b2SensorEvents e=b2World_GetSensorEvents(w);b2SensorBeginTouchEvent c1=e.beginEvents[0],c2=c1;c1.visitorShapeId.index1+=1;word(c1.visitorShapeId.index1);word(c2.visitorShapeId.index1);b2DestroyWorld(w);b2WorldId nw=world(0,1);printf("COPY_WORLD old%d oldgen%u new%d newgen%u copyVisitor%d changedVisitor%d\n",w.index1,w.generation,nw.index1,nw.generation,c2.visitorShapeId.index1,c1.visitorShapeId.index1);word(c2.visitorShapeId.index1);word(c2.visitorShapeId.generation);b2DestroyWorld(nw);return;}
 b2DestroyWorld(w);
}
static void extraLock(void){b2WorldId w=world(0,1);b2BodyId bs=body(w,0,0,0,1,1,0),bv=body(w,2,0,0,1,1,0);b2ShapeId s=shape(bs,1,1,0,1);shape(bv,0,1,0,.2f);lockTarget=s;b2World_SetPreSolveCallback(w,pre,&w);b2BodyId bb=body(w,0,10,0,1,1,0),bc=body(w,2,10.1f,0,1,1,0);b2ShapeId x=shape(bb,0,1,0,1),y=shape(bc,0,1,0,1);b2Shape_EnablePreSolveEvents(x,true);b2Shape_EnablePreSolveEvents(y,true);step(w,1.f/60,4);printf("LOCK_META sensor%d flag%d capacity%d overlaps%d begin%d flagAfterSetter%d rawCreateShape%d rawCreateBody%d reentrantSwapUnchanged%d\n",lockMeta,lockFlag,lockCapacity,lockOverlaps,lockBegin,b2Shape_AreSensorEventsEnabled(s),lockCreatedShape,lockCreatedBody,lockSwapUnchanged);b2DestroyWorld(w);}
int main(int argc,char** argv){if(argc<3)return 2;feenableexcept(FE_INVALID|FE_DIVBYZERO);int kind=atoi(argv[1]),id=atoi(argv[2]);if(argc>3){stream=fopen(argv[3],"wb");if(!stream)return 3;}reset();if(kind==0){if(id<=24)shortcase(id);else longcase(id);}else if(kind==1)directcase(id);else extraLock();if(stream)fclose(stream);metric(id);return invalid?1:0;}
