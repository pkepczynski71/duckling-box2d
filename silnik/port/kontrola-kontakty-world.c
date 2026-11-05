                                                                                
#include "box2d/box2d.h"
#include "world.h"
#include "solver.h"
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-value"
#include "world.c"
#pragma GCC diagnostic pop

extern bool port9IsPairTask(b2TaskCallback* task);
extern void port9CapturePairs(b2World* world);
extern void port9CaptureTask(b2StepContext* context, int start, int end);

void* port9Enqueue(b2TaskCallback* task, int count, int minimum, void* context, void* user)
{
    (void)minimum; (void)user;
    task(0,count,0,context);
    if(port9IsPairTask(task))port9CapturePairs(context);
    if(task==b2CollideTask)port9CaptureTask(context,0,count);
    return NULL;
}
void port9Finish(void* task,void* user){(void)task;(void)user;}
void port9Collide(b2World* world)
{
    b2StepContext context={0};context.world=world;
    b2Collide(&context);
}
