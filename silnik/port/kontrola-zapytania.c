                                                                              
#include <box2d/collision.h>
#include <box2d/math_functions.h>
#include <float.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef OBSERVE18
#define OBSERVE18 1
#endif
_Static_assert(sizeof(float)==4 && sizeof(uint32_t)==4, "word ABI");
_Static_assert(sizeof(b2Vec2)==8 && sizeof(b2ShapeProxy)==72, "proxy ABI");
_Static_assert(sizeof(b2Polygon)==144 && sizeof(b2RayCastInput)==20, "geometry ABI");
_Static_assert(sizeof(b2ShapeCastInput)==88 && sizeof(b2ShapeCastPairInput)==192, "cast ABI");
_Static_assert(sizeof(b2CastOutput)==28, "output ABI");

static float fl(uint32_t w) { float f; memcpy(&f,&w,4); return f; }
static uint32_t bits(float f) { uint32_t w; memcpy(&w,&f,4); return w; }
static void fail(const char *s) { fprintf(stderr,"PORT18A: INPUT_%s\n",s); exit(2); }
static char line[2050];
static char *tok[1025];                                                         
static int nt;
static int read_line(void) {
    size_t n=0; int c;
    while ((c=getchar())!=EOF && c!='\n') {
        if(n>=2049) fail("LINE_LENGTH");
        line[n++]=(char)c;
    }
    if(c==EOF && n==0) return 0;
    if(n && line[n-1]=='\r') { if(c!='\n') fail("ASCII"); --n; }
    if(n>2048) fail("LINE_LENGTH");
    for(size_t i=0;i<n;i++) if((unsigned char)line[i]<32 || (unsigned char)line[i]>126) fail("ASCII");
    if(!n) fail("ASCII");
    line[n]=0; nt=0; tok[nt++]=line;
    for(size_t i=0;i<n;i++) if(line[i]==' ') {
        if(i==0 || i+1==n || line[i+1]==' ') fail("ASCII");
        line[i]=0; if(nt==1025) fail("ARITY"); tok[nt++]=line+i+1;
    }
    return 1;
}
static void required(void) { if(!read_line()) fail("EOF"); }
static uint32_t dec(const char *s) {
    uint64_t v=0; if(!*s || (s[0]=='0' && s[1])) fail("NUMBER");
    for(;*s;s++) { if(*s<'0'||*s>'9') fail("NUMBER"); v=v*10+(unsigned)(*s-'0'); if(v>UINT32_MAX) fail("NUMBER"); }
    return (uint32_t)v;
}
static uint32_t hex(const char *s) {
    if(strlen(s)!=8) fail("WORD");
    uint32_t v=0;
    for(int i=0;i<8;i++) { unsigned c=(unsigned char)s[i]; if(c>='0'&&c<='9') c-='0'; else if(c>='a'&&c<='f') c=c-'a'+10; else fail("WORD"); v=(v<<4)|c; }
    return v;
}
static void words(const uint32_t *w,int n) { for(int i=0;i<n;i++) printf(" %08" PRIx32,w[i]); putchar('\n'); }
static int arity(int k) { return k==0?7:k<=3?22:k<=7?26:k<=11?42:50; }

                                                                              
typedef struct {
    int kind; b2Vec2 point; b2RayCastInput ray; b2ShapeCastInput shape;
    b2ShapeCastPairInput pair; b2ShapeProxy target; bool oneSided;
    b2Polygon polygon; b2Circle circle; b2Capsule capsule; b2Segment segment;
} Args;
typedef struct { int status,reason,kind,n; bool boolean; b2CastOutput cast; } Result;
static void result_words(const Result *r,uint32_t w[7]) {
    if(r->kind==1) w[0]=r->boolean;
    if(r->kind==2) {
        w[0]=r->cast.hit;w[1]=bits(r->cast.point.x);w[2]=bits(r->cast.point.y);
        w[3]=bits(r->cast.normal.x);w[4]=bits(r->cast.normal.y);
        w[5]=bits(r->cast.fraction);w[6]=(uint32_t)r->cast.iterations;
    }
}
static void print_result(const Result *r) { uint32_t w[7]={0};result_words(r,w);words(w,r->n); }
static void change_result(Result *r,uint32_t field,uint32_t value) {
    if(r->kind==1) r->boolean=value!=0;
    else switch(field) {
        case 0:r->cast.hit=value!=0;break;
        case 1:r->cast.point.x=fl(value);break;
        case 2:r->cast.point.y=fl(value);break;
        case 3:r->cast.normal.x=fl(value);break;
        case 4:r->cast.normal.y=fl(value);break;
        case 5:r->cast.fraction=fl(value);break;
        case 6:r->cast.iterations=(int32_t)value;break;
    }
}
static b2Vec2 vec(const uint32_t *w) { return (b2Vec2){fl(w[0]),fl(w[1])}; }
static b2ShapeProxy proxy(const uint32_t *w) {
    b2ShapeProxy p={0}; p.count=(int32_t)w[0]; p.radius=fl(w[1]);
    for(int i=0;i<8;i++) p.points[i]=vec(w+2+2*i);
    return p;
}
static b2Transform transform(const uint32_t *w) { return (b2Transform){vec(w),{fl(w[2]),fl(w[3])}}; }
static Args decode(const uint32_t *w) {
    Args a={0}; a.kind=(int)w[1]; int k=a.kind;
    if(k==0 || (k>=4&&k<=7)) a.ray=(b2RayCastInput){vec(w+2),vec(w+4),fl(w[6])};
    if(k>=1&&k<=3) { a.point=vec(w+2); a.target=proxy(w+4); }
    if(k>=4&&k<=7) { a.target=proxy(w+7); a.oneSided=w[25]!=0; }
    if(k>=8&&k<=11) { a.shape.proxy=proxy(w+2); a.shape.translation=vec(w+20); a.shape.maxFraction=fl(w[22]); a.shape.canEncroach=w[23]!=0; a.target=proxy(w+24); }
    if(k==12) { a.pair.proxyA=proxy(w+2); a.pair.proxyB=proxy(w+20); a.pair.transformA=transform(w+38); a.pair.transformB=transform(w+42); a.pair.translationB=vec(w+46); a.pair.maxFraction=fl(w[48]); a.pair.canEncroach=w[49]!=0; }
    return a;
}
static bool finite_vec(b2Vec2 v) { return isfinite(v.x)&&isfinite(v.y); }
static bool valid_transform(b2Transform t) {
    if(!finite_vec(t.p)||!isfinite(t.q.c)||!isfinite(t.q.s)) return false;
    float qq=t.q.s*t.q.s+t.q.c*t.q.c;
    return 1.0f-0.0006f<qq && qq<1.0f+0.0006f;
}
static int target_type(int k) { return k<=3?k-1:k<=7?k-4:k-8; }                                     
static bool count_ok(b2ShapeProxy p,int type) {
    if(type==-1) return p.count>=1&&p.count<=8;
    if(type==0) return p.count==1;
    if(type==1||type==2) return p.count==2;
    return p.count>=3&&p.count<=8;
}
static bool points_ok(b2ShapeProxy p) {
    for(int i=0;i<8;i++) if(i<p.count&&!finite_vec(p.points[i])) return false;
    return true;
}
static int prepare(Args *a) {
    b2ShapeProxy t=a->target; int type=target_type(a->kind);
                                                                               
    if(a->kind==3) type=3;
    if(type==0) a->circle=(b2Circle){t.points[0],t.radius};
    if(type==1) a->capsule=(b2Capsule){t.points[0],t.points[1],t.radius};
    if(type==2) a->segment=(b2Segment){t.points[0],t.points[1]};
    if(type==3) {
        b2Hull h={0}; h.count=t.count;
        for(int i=0;i<8;i++) if(i<t.count) h.points[i]=t.points[i];
        for(int i=0;i<t.count;i++) {
            float e=b2LengthSquared(b2Sub(t.points[(i+1)%t.count],t.points[i]));
            if(!isfinite(e)||e<=FLT_EPSILON*FLT_EPSILON) return 4;
        }
        if(!b2ValidateHull(&h)) return 4;
        float area=0;
        for(int i=1;i<t.count-1;i++) area=area+0.5f*b2Cross(b2Sub(t.points[i],t.points[0]),b2Sub(t.points[i+1],t.points[0]));
        if(!isfinite(area)||area<=FLT_EPSILON) return 4;
        a->polygon=b2MakePolygon(&h,t.radius);
        if(!finite_vec(a->polygon.centroid)) return 4;
        for(int i=0;i<t.count;i++) if(!finite_vec(a->polygon.normals[i])) return 4;
    }
    return 0;
}
                                                                             
static int preflight(Args *a) {
    int k=a->kind; if(k==0) return 0;
    if(k<=3) { if(!finite_vec(a->point)) return 5; }
    else if(k<=7) { if(!b2IsValidRay(&a->ray)) return 5; }
    else if(k<=11) { if(!finite_vec(a->shape.translation)||!isfinite(a->shape.maxFraction)||a->shape.maxFraction<0) return 5; }
    else { if(!finite_vec(a->pair.translationB)||!isfinite(a->pair.maxFraction)||a->pair.maxFraction<0) return 5; }
    b2ShapeProxy p[2]; int types[2]; int n=1;
    if(k==12) { p[0]=a->pair.proxyA; p[1]=a->pair.proxyB; types[0]=types[1]=-1; n=2; }
    else if(k>=8) { p[0]=a->shape.proxy; p[1]=a->target; types[0]=-1; types[1]=target_type(k); n=2; }
    else { p[0]=a->target; types[0]=k==3?3:target_type(k); }
    for(int i=0;i<n;i++) if(types[i]!=2&&(!isfinite(p[i].radius)||p[i].radius<0)) return 5;
    if(k==12 && (!valid_transform(a->pair.transformA)||!valid_transform(a->pair.transformB))) return 5;
    for(int i=0;i<n;i++) if(!count_ok(p[i],types[i])) return 4;
    for(int i=0;i<n;i++) if(!points_ok(p[i])) return 4;
    return k==12?0:prepare(a);
}
static Result calculate(Args *a,int checked) {
    Result r={0}; int k=a->kind; r.kind=k<=3?1:2; r.n=k<=3?1:7;
    if(checked) { r.status=preflight(a); if(r.status) { r.reason=r.status==5?22:0; return r; } }
    else if(k!=0) { if(prepare(a)) fail("DOMAIN"); }
    Args before=*a; b2CastOutput o={0}; bool v=false;
    switch(k) {
        case 0:v=b2IsValidRay(&a->ray);break;
        case 1:v=b2PointInCircle(a->point,&a->circle);break;
        case 2:v=b2PointInCapsule(a->point,&a->capsule);break;
        case 3:v=b2PointInPolygon(a->point,&a->polygon);break;
        case 4:o=b2RayCastCircle(&a->ray,&a->circle);break;
        case 5:o=b2RayCastCapsule(&a->ray,&a->capsule);break;
        case 6:o=b2RayCastSegment(&a->ray,&a->segment,a->oneSided);break;
        case 7:o=b2RayCastPolygon(&a->ray,&a->polygon);break;
        case 8:o=b2ShapeCastCircle(&a->shape,&a->circle);break;
        case 9:o=b2ShapeCastCapsule(&a->shape,&a->capsule);break;
        case 10:o=b2ShapeCastSegment(&a->shape,&a->segment);break;
        case 11:o=b2ShapeCastPolygon(&a->shape,&a->polygon);break;
        case 12:o=b2ShapeCast(&a->pair);break;
    }
    if(OBSERVE18 && memcmp(&before,a,sizeof before)) { fputs("PORT18A: ARGUMENT_MUTATION\n",stderr); exit(3); }
    if(k<=3) r.boolean=v;
    else { r.cast=o;
        if(checked && (!finite_vec(o.point)||!finite_vec(o.normal)||!isfinite(o.fraction))) { r.cast=(b2CastOutput){0};r.status=5;r.reason=22; }
    }
    return r;
}
static void push_vec(uint32_t *w,int *n,b2Vec2 v) { w[(*n)++]=bits(v.x);w[(*n)++]=bits(v.y); }
static void push_proxy(uint32_t *w,int *n,b2ShapeProxy p) { w[(*n)++]=(uint32_t)p.count;w[(*n)++]=bits(p.radius);for(int i=0;i<8;i++) push_vec(w,n,p.points[i]); }
static void push_transform(uint32_t *w,int *n,b2Transform t) {push_vec(w,n,t.p); w[(*n)++]=bits(t.q.c);w[(*n)++]=bits(t.q.s);}
static void observe(int id,int seq,const Args *a) {
    if(!OBSERVE18) return;
    uint32_t w[48];int n=0,k=a->kind;
    if(k==0||(k>=4&&k<=7)) { push_vec(w,&n,a->ray.origin);push_vec(w,&n,a->ray.translation);w[n++]=bits(a->ray.maxFraction); }
    if(k>=1&&k<=3) {push_vec(w,&n,a->point);push_proxy(w,&n,a->target);}
    if(k>=4&&k<=7) {push_proxy(w,&n,a->target);w[n++]=a->oneSided;}
    if(k>=8&&k<=11) {push_proxy(w,&n,a->shape.proxy);push_vec(w,&n,a->shape.translation);w[n++]=bits(a->shape.maxFraction);w[n++]=a->shape.canEncroach;push_proxy(w,&n,a->target);}
    if(k==12) {push_proxy(w,&n,a->pair.proxyA);push_proxy(w,&n,a->pair.proxyB);push_transform(w,&n,a->pair.transformA);push_transform(w,&n,a->pair.transformB);push_vec(w,&n,a->pair.translationB);w[n++]=bits(a->pair.maxFraction);w[n++]=a->pair.canEncroach;}
    printf("I18 %d %d %d",id,seq,n);words(w,n);
}
static void structure(uint32_t *w,int n,int profile,int guard) {
    if(n<2) fail("ARITY");
    if(w[0]>1 || w[0]!=(profile!=0)) fail("MODE");
    if(w[1]>12) fail("KIND");
    int k=(int)w[1]; if(n!=arity(k)) fail("ARITY");
    if(guard&&k==0) fail("KIND");
    if(k>=4&&k<=7) {if(w[25]>1)fail("VALUE");if(k!=6&&w[25])fail("UNUSED");}
    if(k>=8&&k<=11&&w[23]>1)fail("VALUE");
    if(k==12&&w[49]>1)fail("VALUE");
    int offsets[2],types[2],np=0;
    if(k>=1&&k<=3){offsets[np]=4;types[np++]=k==3?3:target_type(k);}
    if(k>=4&&k<=7){offsets[np]=7;types[np++]=target_type(k);}
    if(k>=8&&k<=11){offsets[np]=2;types[np++]=-1;offsets[np]=24;types[np++]=target_type(k);}
    if(k==12){offsets[np]=2;types[np++]=-1;offsets[np]=20;types[np++]=-1;}
    for(int j=0;j<np;j++) {
        int off=offsets[j]; if(types[j]==2&&w[off+1]!=0)fail("UNUSED");
        if(w[0]==0) for(int i=0;i<8;i++) if((int32_t)w[off]<=i&&(w[off+2+2*i]||w[off+3+2*i]))fail("UNUSED");
    }
    if(w[0]==0 && k!=0) { Args a=decode(w);if(preflight(&a))fail("DOMAIN"); }
}
int main(int argc,char **argv) {
    int diagnostic=0;for(int i=1;i<argc;i++){if(!strcmp(argv[i],"--diagnostic"))diagnostic=1;else fail("HEADER");}
    required();if(nt!=4||strcmp(tok[0],"PORT18"))fail("HEADER");if(strcmp(tok[1],"A"))fail("PART");
    int profile=!strcmp(tok[2],"DIRECT")?0:!strcmp(tok[2],"PUBLIC")?1:!strcmp(tok[2],"GUARD")?2:-1;
    if(profile<0)fail("PROFILE");
    uint32_t N=dec(tok[3]),full=profile==2?821:96;
    if(!N||N>full||(!diagnostic&&N!=full))fail("N");
    int previous=0;
    for(uint32_t c=0;c<N;c++) {
        required();if(nt!=3||strcmp(tok[0],"C"))fail("CASE");uint32_t id=dec(tok[1]),M=dec(tok[2]);
        if(id<1||id>full||id<=(uint32_t)previous||(!diagnostic&&id!=c+1))fail("ID");
        previous=(int)id;
        if((profile==2&&M!=0)||(profile==0&&M!=1)||(profile==1&&(M<1||M>32||(!diagnostic&&M!=8))))fail("COUNT");
        printf("CASE %u %u\n",id,M); Result current={0},banks[4]={{0}};int has=0,used[4]={0};
        for(uint32_t s=0;s<(profile==2?2:M);s++) {
            required();int guard=profile==2; if(strcmp(tok[0],guard?"G":"O"))fail(guard?"GUARD":"CASE");
            int base=guard?5:4; if(nt<base)fail("ARITY");
            uint32_t seq,op,n;
            if(guard){if(dec(tok[1])!=id||dec(tok[2])!=s)fail("GUARD");seq=s;op=dec(tok[3]);}
            else {seq=dec(tok[1]);if(seq!=s+1)fail("SEQ");op=dec(tok[2]);}
            if(op!=500&&(guard||profile==0||(op!=516&&op!=517&&op!=518)))fail("OPCODE");
            n=dec(tok[guard?4:3]);
            if(n>50||nt!=base+(int)n)fail("ARITY");
            uint32_t w[50]={0};for(uint32_t i=0;i<n;i++)w[i]=hex(tok[base+i]);
            if(op==500)structure(w,(int)n,profile,guard);
            else {
                if(n!=(op==518?3u:1u))fail("ARITY");
                if(w[0]>3)fail("BANK");
                if(op==518){if(w[1]>6)fail("FIELD");if((w[1]==0&&w[2]>1)||(w[1]==6&&w[2]>INT32_MAX))fail("VALUE");}
                if((op==516&&!has)||(op!=516&&!used[w[0]]))fail("BANK");
                if(op==518){if(w[1]>=(uint32_t)banks[w[0]].n)fail("FIELD");uint32_t old[7]={0};result_words(&banks[w[0]],old);if(w[2]==old[w[1]])fail("VALUE");}
            }
            if(guard){printf("G18 %u %u %u %u",id,seq,op,n);words(w,(int)n);Args a=decode(w);int status=preflight(&a);printf("GA18 %u %u %d %d %d\n",id,seq,status==0,status,status==5?22:0);}
            else {
                printf("E18 %u %u %u %u",id,seq,op,n);words(w,(int)n);Args a={0};Result r={0};
                if(op==500){a=decode(w);r=calculate(&a,w[0]!=0);current=r;has=1;}
                if(op==516){banks[w[0]]=current;used[w[0]]=1;}
                                                                                
                if(op==518)change_result(&banks[w[0]],w[1],w[2]);
                printf("R18 %u %u %u %d %d %d %d",id,seq,op,r.status,r.reason,r.kind,r.n);print_result(&r);
                if(op==500)observe((int)id,(int)seq,&a);
                if(profile==1)for(int b=0;b<4;b++)if(used[b]){printf("V18 %u %u %d %d %d",id,seq,b,banks[b].kind,banks[b].n);print_result(&banks[b]);}
            }
        }
        printf("ENDCASE %u\n",id);
    }
    if(getchar()!=EOF)fail("TRAILING_DATA");
    printf("END %u\n",N);return 0;
}
