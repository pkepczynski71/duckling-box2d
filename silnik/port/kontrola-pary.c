                                          
                               
                                                                            
                                                                             
                                                                               
   
#include <box2d/box2d.h>
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if !defined(NDEBUG) || defined(B2_ENABLE_ASSERT)
#error PORT9A requires Release / NDEBUG without B2_ENABLE_ASSERT
#endif
_Static_assert(sizeof(float)==4 && FLT_RADIX==2 && FLT_MANT_DIG==24 && FLT_MAX_EXP==128,
               "IEEE binary32 required");
_Static_assert(CHAR_BIT==8 && sizeof(int)==4,"32-bit int required");

typedef struct Shape {
    uint32_t tag,words[44];
    b2Transform xf;
    b2Circle circle;
    b2Capsule capsule;
    b2Segment segment;
    b2Polygon polygon;
} Shape;

static void fail(const char* message)
{
    fprintf(stderr,"PORT9A: %s\n",message);
    exit(2);
}
static float from_bits(uint32_t u) { float f;memcpy(&f,&u,4);return f; }
static uint32_t to_bits(float f) { uint32_t u;memcpy(&u,&f,4);return u; }
static void word(uint32_t u) { printf(" %08" PRIx32,u); }
static void real(float f) { word(to_bits(f)); }
static void vec(b2Vec2 v) { real(v.x);real(v.y); }

static void prepare(Shape* s, bool constructor)
{
    if(s->tag>4) fail("tag");
    float f[44];
    for(int i=0;i<44;++i) {
        f[i]=from_bits(s->words[i]);
        if(!(s->tag==3 && i==4) && !isfinite(f[i])) fail("NaN / Inf");
    }
    s->xf=(b2Transform){{f[0],f[1]},{f[2],f[3]}};
    if(!b2IsNormalizedRot(s->xf.q)) fail("rotation");
    const float* g=f+4;
    const uint32_t* u=s->words+4;
    unsigned used;
    if(s->tag==0) {
        used=3;
        if(g[2]<0) fail("geometry");
        s->circle=(b2Circle){{g[0],g[1]},g[2]};
    } else if(s->tag==1 || s->tag==2) {
        used=s->tag==1 ? 5:4;
        b2Vec2 p={g[0],g[1]},q={g[2],g[3]};
        float dd=b2DistanceSquared(p,q);
        float threshold=constructor ? FLT_EPSILON:FLT_EPSILON*FLT_EPSILON;
        if(!isfinite(dd) || !(dd>threshold)) fail("geometry");
        if(s->tag==1) {
            if(g[4]<0) fail("geometry");
            s->capsule=(b2Capsule){p,q,g[4]};
        } else s->segment=(b2Segment){p,q};
    } else if(s->tag==4) {
        used=7;
        if(!(g[0]>0 && g[1]>0 && g[6]>=0)) fail("geometry");
        b2Rot q={g[4],g[5]};
        if(!b2IsNormalizedRot(q)) fail("rotation");
        s->polygon=b2MakeOffsetRoundedBox(g[0],g[1],(b2Vec2){g[2],g[3]},q,g[6]);
    } else {
        unsigned count=u[0];
        if(count<3 || count>8 || g[1]<0) fail("geometry");
        used=2+2*count;
        b2Hull hull={0};hull.count=(int)count;
        for(unsigned i=0;i<count;++i) hull.points[i]=(b2Vec2){g[2+2*i],g[3+2*i]};
        if(!b2ValidateHull(&hull)) fail("geometry");
        s->polygon=b2MakePolygon(&hull,g[1]);
    }
    for(unsigned i=used;i<40;++i) if(u[i]!=0) fail("unused geometry");
}

static b2Manifold collide(unsigned kind, const Shape* a, const Shape* b)
{
    switch(kind) {
        case 0:return b2CollideCapsuleAndCircle(&a->capsule,a->xf,&b->circle,b->xf);
        case 1:return b2CollidePolygonAndCircle(&a->polygon,a->xf,&b->circle,b->xf);
        case 2:return b2CollideCapsules(&a->capsule,a->xf,&b->capsule,b->xf);
        case 3:return b2CollideSegmentAndCircle(&a->segment,a->xf,&b->circle,b->xf);
        case 4:return b2CollideSegmentAndCapsule(&a->segment,a->xf,&b->capsule,b->xf);
        case 5:return b2CollidePolygonAndCapsule(&a->polygon,a->xf,&b->capsule,b->xf);
        case 6:return b2CollideSegmentAndPolygon(&a->segment,a->xf,&b->polygon,b->xf);
        default:fail("kind");
    }
    return (b2Manifold){0};
}

static void manifold(unsigned id, b2Manifold m)
{
    printf("M %u",id);vec(m.normal);real(m.rollingImpulse);word((uint32_t)m.pointCount);
    for(int i=0;i<2;++i) {
        const b2ManifoldPoint* p=m.points+i;
        vec(p->point);vec(p->anchorA);vec(p->anchorB);real(p->separation);
        real(p->normalImpulse);real(p->tangentImpulse);real(p->totalNormalImpulse);
        real(p->normalVelocity);word(p->id);word(p->persisted);
    }
    putchar('\n');
}

static char line[2048];
static char* row(FILE* file)
{
    size_t n=0;int c;
    while((c=fgetc(file))!=EOF && c!='\n') {
        if(c==0 || c>127 || n==sizeof(line)-1) fail("ASCII / line length");
        line[n++]=(char)c;
    }
    if(ferror(file) || (c==EOF && n==0)) fail("truncated input / read error");
    if(n && line[n-1]=='\r' && c=='\n') --n;
    line[n]=0;
    if(strchr(line,'\r') || !n) fail("line ending / length");
    return line;
}
static void space(char** p)
{
    if(**p!=' ') fail("single space required");
    ++*p;
}
static uint32_t decimal(char** p)
{
    if(**p<'0' || **p>'9' || (**p=='0' && (*p)[1]>='0' && (*p)[1]<='9')) fail("canonical decimal");
    uint64_t value=0;
    do {
        value=10*value+(uint32_t)(**p-'0');++*p;
        if(value>UINT32_MAX) fail("decimal overflow");
    } while(**p>='0' && **p<='9');
    return (uint32_t)value;
}
static uint32_t hex_word(char** p)
{
    uint32_t value=0;
    for(int i=0;i<8;++i) {
        unsigned char c=(unsigned char)**p;
        if(!((c>='0' && c<='9') || (c>='a' && c<='f'))) fail("canonical hex");
        value=(value<<4)|(uint32_t)(c<='9' ? c-'0':c-'a'+10);++*p;
    }
    return value;
}
static Shape read_shape(FILE* file,char marker)
{
    Shape s={0};char* p=row(file);
    if(*p++!=marker) fail("marker");
    space(&p);s.tag=decimal(&p);
    if(s.tag>4) fail("tag");
    for(int i=0;i<44;++i) {space(&p);s.words[i]=hex_word(&p);}
    if(*p) fail("extra data");
    return s;
}
static void echo_side(const Shape* s)
{
    word(s->tag);vec(s->xf.p);real(s->xf.q.c);real(s->xf.q.s);
    for(int i=4;i<44;++i) word(s->words[i]);
}
int main(int argc,char** argv)
{
    if(argc!=2) fail("usage");
    FILE* input=fopen(argv[1],"rb");
    if(!input) fail("input file");
    char* p=row(input);
    if(strncmp(p,"PORT9A",6)!=0) fail("header");
    p+=6;space(&p);unsigned n=decimal(&p);
    if(*p || n<1 || n>448) fail("N");
    printf("PORT9A %u\n",n);
    static const unsigned types[7][2]={{1,0},{3,0},{1,1},{2,0},{2,1},{3,1},{2,3}};
    for(unsigned index=1;index<=n;++index) {
        p=row(input);if(*p++!='P') fail("marker");
        space(&p);unsigned id=decimal(&p);space(&p);unsigned kind=decimal(&p);
        if(*p) fail("extra data");
        if(id!=index) fail("id");
        if(kind>6) fail("kind");
        Shape a=read_shape(input,'A');
        Shape b=read_shape(input,'B');
        unsigned typeA=a.tag==4 ? 3:a.tag,typeB=b.tag==4 ? 3:b.tag;
        if(typeA!=types[kind][0] || typeB!=types[kind][1]) fail("pair types");
        prepare(&a,kind==6);prepare(&b,kind==5);
        printf("E %u %u",id,kind);echo_side(&a);echo_side(&b);putchar('\n');
        manifold(id,collide(kind,&a,&b));
        printf("ENDCASE %u\n",id);
    }
    if(fgetc(input)!=EOF) fail("trailing data");
    if(ferror(input)) fail("read error");
    fclose(input);printf("END %u\n",n);
    if(fflush(stdout)!=0 || ferror(stdout)) fail("write error");
    return 0;
}
