                                          
                               
                                                                            
                                                                        
   
#include <box2d/box2d.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef NDEBUG
#error ASSERT9A requires assertions in the original library
#endif
static int record_assert(const char* condition,const char* file,int line)
{
    (void)file;(void)line;
    fprintf(stderr,"ASSERT9A: %s\n",condition);
    if(strcmp(condition,"dd1 > epsSqr && dd2 > epsSqr")==0)exit(86);
    if(strcmp(condition,"b2LengthSquared( d ) > FLT_EPSILON")==0)exit(87);
    exit(88);
}
int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    b2SetAssertFcn(record_assert);
    b2Transform xf={{0,0},{1,0}};
    b2Capsule good={{-1,0},{1,0},.25f};
    b2Capsule zero={{0,0},{0,0},.25f};
    b2Polygon polygon=b2MakeBox(1,1);
    if(strcmp(argv[1],"capsules-A")==0) {
        b2Manifold m=b2CollideCapsules(&zero,xf,&good,xf);return m.pointCount==3;
    }
    if(strcmp(argv[1],"capsules-B")==0) {
        b2Manifold m=b2CollideCapsules(&good,xf,&zero,xf);return m.pointCount==3;
    }
    if(strcmp(argv[1],"polygon-capsule")==0) {
        b2Manifold m=b2CollidePolygonAndCapsule(&polygon,xf,&zero,xf);return m.pointCount==3;
    }
    if(strcmp(argv[1],"segment-polygon")==0) {
        b2Segment segment={{0,0},{0,0}};
        b2Manifold m=b2CollideSegmentAndPolygon(&segment,xf,&polygon,xf);return m.pointCount==3;
    }
    return 2;
}
