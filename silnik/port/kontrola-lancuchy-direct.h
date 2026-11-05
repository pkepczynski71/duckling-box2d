                                                                                     
#include <float.h>
static bool rigid13c(const uint32_t* a)
{float c=from_bits(a[2]),s=from_bits(a[3]),ss=s*s,cc=c*c,q=ss+cc;return isfinite(from_bits(a[0]))&&isfinite(from_bits(a[1]))&&isfinite(c)&&isfinite(s)&&q>1.0f-.0006f&&q<1.0f+.0006f;}
static b2Transform transform13c(const uint32_t* a)
{return (b2Transform){{from_bits(a[0]),from_bits(a[1])},{from_bits(a[2]),from_bits(a[3])}};}
static void cache13c(const char* tag,int id,int seq,const b2SimplexCache* c)
{printf("%s %d %d",tag,id,seq);word(c->count);for(int j=0;j<3;j++)word(c->indexA[j]);for(int j=0;j<3;j++)word(c->indexB[j]);putchar('\n');}
static void syntax13c(const uint32_t* a,bool laterWarm)
{
    if(a[0]>2)fail("INPUT_ENUM");if(a[1]>1)fail("INPUT_MODE");
    for(int j=43;j<64;j++)if(a[j])fail("INPUT_UNUSED");
    for(uint32_t j=a[18]<8?a[18]:8;j<8;j++)if(a[20+2*j]||a[21+2*j])fail("INPUT_UNUSED");
    if(laterWarm)for(int j=36;j<=42;j++)if(a[j])fail("INPUT_UNUSED");
    if(a[18]>10)fail("INPUT_DOMAIN");
    if(a[36]>65535)fail("INPUT_CACHE");for(int j=37;j<=42;j++)if(a[j]>255)fail("INPUT_CACHE");
}
static b2SimplexCache decode13c(const uint32_t* a)
{
    b2SimplexCache k={0};k.count=a[36];for(int j=0;j<3;j++){k.indexA[j]=a[37+j];k.indexB[j]=a[40+j];}
    return k;
}
static int validate13c(const uint32_t* a,b2SimplexCache k,int* resultReason,b2Vec2* chainPoints,b2Vec2* points,b2Hull* hull)
{
    int status=OK,reason=0;bool game=a[1];uint32_t n=a[18];
    bool countOK=(a[0]==0?n==1:a[0]==1?n==2:n>=3&&n<=8);
    if(!isfinite(from_bits(a[19]))||from_bits(a[19])<0||!rigid13c(a+10)||!rigid13c(a+14))status=PARAM;
    if(!status&&(k.count>3)){status=PARAM;reason=82;}
    if(!status&&a[0]!=0&&countOK)for(int j=0;j<k.count;j++)if(k.indexA[j]>=2||k.indexB[j]>=n){status=PARAM;reason=82;break;}
    if(!countOK&&!status){status=GEOMETRY;reason=84;}
    for(int j=0;j<4;j++)chainPoints[j]=(b2Vec2){from_bits(a[2+2*j]),from_bits(a[3+2*j])};
    if(!status){
        if(game){reason13=0;status=geometry13(chainPoints,4,false);reason=reason13;}
        else for(int j=0;j<4;j++)if(!finite_vec(chainPoints[j]))status=GEOMETRY;
        for(uint32_t j=0;j<n;j++){points[j]=(b2Vec2){from_bits(a[20+2*j]),from_bits(a[21+2*j])};if(!finite_vec(points[j])){status=GEOMETRY;reason=84;}}
        if(!status&&a[0]==1){float dx=points[1].x-points[0].x,dy=points[1].y-points[0].y,xx=dx*dx,yy=dy*dy,d=xx+yy;if(!isfinite(dx)||!isfinite(dy)||!isfinite(xx)||!isfinite(yy)||!isfinite(d)||!(d>FLT_EPSILON)){status=GEOMETRY;reason=84;}}
        if(!status&&a[0]==2){hull->count=n;memcpy(hull->points,points,n*sizeof(b2Vec2));if(!b2ValidateHull(hull)){status=GEOMETRY;reason=84;}}
    }
    *resultReason=reason;return status;
}
static int guardPair13c(const uint32_t* a)
{
    syntax13c(a,false);if(a[1]!=1)fail("INPUT_MODE");
    b2Vec2 chain[4],points[8];b2Hull hull={0};int reason;
    return validate13c(a,decode13c(a),&reason,chain,points,&hull);                             
}
static void direct13c(FILE* file,int id,int seq,b2SimplexCache* previous)
{
    char* p=row(file);if(strncmp(p,"O ",2))fail("INPUT_TAG");arity13(p,67,"INPUT_ARITY");p+=2;
    uint32_t actual=decimal13(&p);space(&p);uint32_t code=decimal13(&p);if(actual!=(uint32_t)seq)fail("INPUT_SEQ");if(code!=120)fail("INPUT_OPCODE");
    uint32_t a[64];for(int j=0;j<64;j++){space(&p);a[j]=hex_word(&p);}if(*p)fail("INPUT_ARITY");
    bool warm=(id<=128?id>64:id<=256?id>192:id>320);syntax13c(a,warm&&seq>1);
    b2SimplexCache k=warm&&seq>1?*previous:decode13c(a);bool game=a[1];
    if(!game&&(!rigid13c(a+10)||!rigid13c(a+14)))fail("INPUT_ROTATION");
    b2Vec2 chainPoints[4],points[8];b2Hull hull={0};int reason=0;
    int status=validate13c(a,k,&reason,chainPoints,points,&hull);
    if(status&&!game)fail(reason==82?"INPUT_CACHE":"INPUT_DOMAIN");
    printf("E13C %d %d 120",id,seq);for(int j=0;j<64;j++)word(a[j]);putchar('\n');
    printf("A13 %d %d",id,seq);word(status);word(reason);putchar('\n');
    if(!status){
        cache13c("KI13",id,seq,&k);b2ChainSegment chain={chainPoints[0],{chainPoints[1],chainPoints[2]},chainPoints[3],0};
        b2Transform xfA=transform13c(a+10),xfB=transform13c(a+14);b2Manifold m;
        if(a[0]==0){b2Circle circle={points[0],from_bits(a[19])};m=b2CollideChainSegmentAndCircle(&chain,xfA,&circle,xfB);}
        else if(a[0]==1){b2Capsule capsule={points[0],points[1],from_bits(a[19])};m=b2CollideChainSegmentAndCapsule(&chain,xfA,&capsule,xfB,&k);}
        else {b2Polygon polygon=b2MakePolygon(&hull,from_bits(a[19]));m=b2CollideChainSegmentAndPolygon(&chain,xfA,&polygon,xfB,&k);}
        printf("M13C %d %d",id,seq);vec(m.normal);real(m.rollingImpulse);word(m.pointCount);
        for(int j=0;j<2;j++){b2ManifoldPoint t=m.points[j];vec(t.point);vec(t.anchorA);vec(t.anchorB);real(t.separation);real(t.normalImpulse);real(t.tangentImpulse);real(t.totalNormalImpulse);real(t.normalVelocity);word(t.id);word(t.persisted);}putchar('\n');
        cache13c("K13C",id,seq,&k);*previous=k;
    }
    printf("DC13 %d %d",id,seq);word(1);word(1);for(int j=0;j<3;j++)word(!status);putchar('\n');
}
