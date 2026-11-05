                                                                        
                                                                                
#include "contact.c"
int port13ContactKind(int a,int b,bool* primary)
{
    if(a<0||a>=b2_shapeTypeCount||b<0||b>=b2_shapeTypeCount)return -2;
    const struct b2ContactRegister* entry=&s_registers[a][b];*primary=entry->primary;
    b2ManifoldFcn* const functions[]={b2CircleManifold,b2CapsuleAndCircleManifold,
        b2SegmentAndCircleManifold,b2PolygonAndCircleManifold,b2CapsuleManifold,
        b2SegmentAndCapsuleManifold,b2PolygonAndCapsuleManifold,b2SegmentAndPolygonManifold,
        b2PolygonManifold,b2ChainSegmentAndCircleManifold,b2ChainSegmentAndCapsuleManifold,b2ChainSegmentAndPolygonManifold};
    if(!entry->fcn)return -1;
    for(int i=0;i<12;i++)if(entry->fcn==functions[i])return i;
    return -2;
}
