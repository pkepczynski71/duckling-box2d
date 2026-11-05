                                                                        
#include "box2d/box2d.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
static uint64_t object = UINT64_C(456) << 32 | 123;
static uint32_t bits(float value) { uint32_t result; memcpy(&result,&value,4); return result; }
int main(void)
{
    b2WorldDef wd=b2DefaultWorldDef();wd.enableContinuous=false;
    b2WorldId w=b2CreateWorld(&wd);
    b2BodyDef a=b2DefaultBodyDef();b2BodyId first=b2CreateBody(w,&a);
    a.type=b2_dynamicBody;a.position=(b2Vec2){2,0};b2BodyId second=b2CreateBody(w,&a);
    b2DistanceJointDef d=b2DefaultDistanceJointDef();d.bodyIdA=first;d.bodyIdB=second;
    b2JointId j=b2CreateDistanceJoint(w,&d);
    for(int i=0;i<3;i++) {
        if(i==1){b2Joint_SetUserData(j,&object);b2Joint_SetReferenceAngle(j,.5f);b2Joint_SetLocalAxisA(j,(b2Vec2){1,0});}
        if(i==2){b2Joint_SetUserData(j,NULL);b2Joint_SetReferenceAngle(j,-.5f);b2Joint_SetLocalAxisA(j,(b2Vec2){0,1});}
        void* value=b2Joint_GetUserData(j);if(value!=NULL&&value!=&object)return 3;
        b2Vec2 axis=b2Joint_GetLocalAxisA(j);float angle=b2Joint_GetReferenceAngle(j);
        printf("GET14 %d %u %u %u %u %u %u\n",i+1,value!=NULL,value?123u:0u,value?456u:0u,bits(angle),bits(axis.x),bits(axis.y));
    }
    b2DestroyWorld(w);return 0;
}
