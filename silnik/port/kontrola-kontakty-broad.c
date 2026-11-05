                                                                              
#include "box2d/box2d.h"
#include "world.h"
#include "body.h"
#include "shape.h"
#include "atomic.h"
#include <stdlib.h>
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-value"
#include "broad_phase.c"
#pragma GCC diagnostic pop

extern void port9Request(b2World* world,int move,int shapeA,int shapeB);
bool port9IsPairTask(b2TaskCallback* task){return task==b2FindPairsTask;}
void port9CapturePairs(b2World* world)
{
    b2BroadPhase* bp=&world->broadPhase;
    for(int i=0;i<bp->moveArray.count;++i)
        for(b2MovePair* pair=bp->moveResults[i].pairList;pair;pair=pair->next)
            port9Request(world,i,pair->shapeIndexA,pair->shapeIndexB);
}
                                                                            
                                                                            
int port9Prepare(b2World* world,b2ShapeId* first,b2ShapeId* second,bool capture)
{
    b2BroadPhase* bp=&world->broadPhase;int count=bp->moveArray.count;
    if(!count)return 0;
    b2MoveResult* oldResults=bp->moveResults;b2MovePair* oldPairs=bp->movePairs;
    int oldCapacity=bp->movePairCapacity,oldIndex=b2AtomicLoadInt(&bp->movePairIndex);
    bp->moveResults=calloc((size_t)count,sizeof(b2MoveResult));bp->movePairCapacity=16*count;
    bp->movePairs=calloc((size_t)bp->movePairCapacity,sizeof(b2MovePair));
    if(!bp->moveResults||!bp->movePairs)abort();
    b2AtomicStoreInt(&bp->movePairIndex,0);b2FindPairsTask(0,count,0,world);
    if(capture)port9CapturePairs(world);
    int requests=0;
    for(int i=0;i<count;++i){
        b2MovePair* pair=bp->moveResults[i].pairList;
        while(pair){b2MovePair* next=pair->next;
            if(requests++==0){
                b2Shape* a=world->shapes.data+pair->shapeIndexA; b2Shape* b=world->shapes.data+pair->shapeIndexB;
                *first=(b2ShapeId){a->id+1,world->worldId,a->generation};
                *second=(b2ShapeId){b->id+1,world->worldId,b->generation};
            }
            if(pair->heap)b2Free(pair,sizeof(b2MovePair));pair=next;
        }
    }
    free(bp->movePairs);free(bp->moveResults);bp->moveResults=oldResults;bp->movePairs=oldPairs;
    bp->movePairCapacity=oldCapacity;b2AtomicStoreInt(&bp->movePairIndex,oldIndex);
    return requests;
}
