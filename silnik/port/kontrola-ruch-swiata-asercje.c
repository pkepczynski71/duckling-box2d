                                          
                               
                                                                       
                                                                          
   
#include <box2d/box2d.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef NDEBUG
#error ASSERT8 requires assertions in the original library
#endif
static int record_assert(const char* condition,const char* file,int line)
{
    (void)file;(void)line;
    fprintf(stderr,"ASSERT8: %s\n",condition);
    if(strcmp(condition,"b2IsValidFloat( timeStep )")==0)exit(86);
    if(strcmp(condition,"0 < subStepCount")==0)exit(87);
    exit(88);
}
int main(int argc,char** argv)
{
    if(argc!=3)return 2;
    uint32_t word=(uint32_t)strtoul(argv[1],NULL,16);float dt;memcpy(&dt,&word,4);
    int count=atoi(argv[2]);b2SetAssertFcn(record_assert);
    b2WorldDef def=b2DefaultWorldDef();def.enableSleep=false;def.enableContinuous=false;
    b2WorldId world=b2CreateWorld(&def);
    b2World_Step(world,dt,count);
    b2DestroyWorld(world);
    return 0;
}
