#if !defined(PORT13B)
                                                                    
                                                                           
                                                                        
   
#include "box2d/collision.h"
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lancuchy-meta.inc"
#ifndef PORT13_PROFILE
#define PORT13_PROFILE 'R'
#endif
static FILE *input;
static char row[2052],*tokens[80];
static int nt;
static bool row_eof;
static bool guard;
static unsigned current_id,current_seq,guard_kind;
static bool observing,defined_a[3],trace_defined[23][3],oracle_invalid;
static int initialized,trace_count;
static void fatal(const char *reason){fprintf(stderr,"PORT13A: %s\n",reason);exit(2);}
static uint32_t word(float f){uint32_t u;memcpy(&u,&f,4);return u;}
static float number(uint32_t u){float f;memcpy(&f,&u,4);return f;}
static void h(uint32_t u){printf(" %08"PRIx32,u);}
static void cache_out(const char *tag,const b2SimplexCache *k){
 printf("%s %u %u",tag,current_id,current_seq);h(k->count);
 for(int j=0;j<3;++j)h(k->indexA[j]);for(int j=0;j<3;++j)h(k->indexB[j]);puts("");
}
                                                                                   
void __sanitizer_cov_trace_pc(void){
 if(!observing)return;
 intptr_t pc=(intptr_t)__builtin_return_address(0)-(intptr_t)b2ShapeDistance;
 unsigned action=0;
 for(unsigned i=0;i<sizeof(meta13)/sizeof(meta13[0]);++i)if(meta13[i].offset==pc){action=meta13[i].action;break;}
 switch(action){
 case 1:if(initialized<3)defined_a[initialized++]=true;else oracle_invalid=true;break;
 case 2:defined_a[0]=true;break;
 case 3:defined_a[0]=true;break;
 case 4:defined_a[1]=true;defined_a[0]=defined_a[1];break;
 case 5:defined_a[0]=defined_a[1]=true;break;
 case 6:defined_a[0]=true;break;
 case 7:defined_a[0]=defined_a[1]=true;break;
 case 8:defined_a[0]=defined_a[2]=true;defined_a[1]=defined_a[2];break;
 case 9:defined_a[1]=true;defined_a[0]=defined_a[1];break;
 case 10:defined_a[2]=true;defined_a[0]=defined_a[2];break;
 case 11:defined_a[1]=defined_a[2]=true;defined_a[0]=defined_a[2];break;
 case 12:defined_a[0]=defined_a[1]=defined_a[2]=true;break;
 case 13:if(trace_count<23){for(int j=0;j<3;++j)trace_defined[trace_count][j]=defined_a[j];++trace_count;}else oracle_invalid=true;break;
 case 15:if(!defined_a[0]||!defined_a[1])oracle_invalid=true;break;
 case 16:if(!defined_a[0]||!defined_a[1]||!defined_a[2])oracle_invalid=true;break;
 }
                                                                                  
 if(oracle_invalid)abort();
}
static void begin_observation(int count){
 memset(defined_a,0,sizeof defined_a);memset(trace_defined,0,sizeof trace_defined);
 (void)count;initialized=trace_count=0;oracle_invalid=false;observing=true;
}
static bool line(void){
 int c,n=0;bool cr=false;
 while((c=fgetc(input))!=EOF){
  if(c==0||c<0||c>127)fatal("INPUT_ASCII");
  if(c=='\n')break;
  if(cr)fatal("INPUT_CR");
  if(c=='\r'){cr=true;continue;}
  if(n>=2048)fatal("INPUT_ARITY");row[n++]=(char)c;
 }
 if(cr&&c!='\n')fatal("INPUT_CR");
 row_eof=c==EOF;
 if(c==EOF&&n==0)return false;
 if(!n)fatal("INPUT_EMPTY_LINE");row[n]=0;
 if(row[0]==' '||row[n-1]==' ')fatal("INPUT_SPACING");
 nt=0;tokens[nt++]=row;
 for(int i=0;i<n;++i){
  if(row[i]=='\t'||(unsigned char)row[i]<32)fatal("INPUT_SPACING");
  if(row[i]==' '){if(row[i+1]==' ')fatal("INPUT_SPACING");row[i]=0;if(nt>=80)fatal("INPUT_ARITY");tokens[nt++]=row+i+1;}
 }
 return true;
}
static void need_line(void){if(!line())fatal("INPUT_EOF");}
static void arity(int n){if(nt!=n)fatal(row_eof&&nt<n?"INPUT_EOF":"INPUT_ARITY");}
static uint32_t decimal(const char *s){
 if(!*s||(s[0]=='0'&&s[1]))fatal("INPUT_DECIMAL");uint64_t u=0;
 for(;*s;++s){if(*s<'0'||*s>'9')fatal("INPUT_DECIMAL");u=u*10+(unsigned)(*s-'0');if(u>UINT32_MAX)fatal("INPUT_DECIMAL");}return(uint32_t)u;
}
static uint32_t hexadecimal(const char *s){
 if(strlen(s)!=8)fatal("INPUT_WORD");uint32_t u=0;
 for(int i=0;i<8;++i){unsigned c=(unsigned char)s[i];if(c>='0'&&c<='9')c-='0';else if(c>='a'&&c<='f')c=c-'a'+10;else fatal("INPUT_WORD");u=(u<<4)|c;}return u;
}
static void used(bool u[64],int first,int last){for(int i=first;i<=last;++i)u[i]=true;}
static bool rigid(const uint32_t *a){
 float x=number(a[0]),y=number(a[1]),c=number(a[2]),s=number(a[3]);
 float ss=s*s,cc=c*c,qq=ss+cc;
 return isfinite(x)&&isfinite(y)&&isfinite(c)&&isfinite(s)&&qq>1.0f-0.0006f&&qq<1.0f+0.0006f;
}
static bool finite_points(const uint32_t *a,unsigned count){for(unsigned i=0;i<2*count;++i)if(!isfinite(number(a[i])))return false;return true;}
static void validate_syntax(unsigned kind,const uint32_t *a,bool is_trace,bool later_warm){
 if(kind>2)fatal("INPUT_OPCODE");if(a[0]>1)fatal("INPUT_MODE");
 bool u[64]={0};used(u,0,2);
 if(a[1]>10)fatal("INPUT_DOMAIN");
 if(kind==0){
  if(a[23]>10)fatal("INPUT_DOMAIN");
  if(a[45]>1||a[54]>1)fatal("INPUT_BOOL");if(a[53]>23)fatal("INPUT_DOMAIN");
  used(u,19,24);used(u,41,54);
  for(unsigned j=0;j<(a[1]<8?a[1]:8);++j)used(u,3+2*j,4+2*j);
  for(unsigned j=0;j<(a[23]<8?a[23]:8);++j)used(u,25+2*j,26+2*j);
  if(!a[54]&&a[53])fatal("INPUT_UNUSED");
  for(int i=55;i<64;++i)if(a[i])fatal("INPUT_UNUSED");
  if(later_warm)for(int i=46;i<=52;++i)if(a[i])fatal("INPUT_UNUSED");
  if(a[46]>65535)fatal("INPUT_CACHE");for(int i=47;i<=52;++i)if(a[i]>255)fatal("INPUT_CACHE");
  if(a[54]&&!is_trace)fatal("INPUT_PROFILE");
 }else{
  for(unsigned j=0;j<a[1];++j)used(u,3+2*j,4+2*j);
  if(kind==2)used(u,23,26);
 }
 for(int i=0;i<64;++i)if(!u[i]&&a[i])fatal("INPUT_UNUSED");
 if(a[0]==0){
  if(!isfinite(number(a[2]))||!finite_points(a+3,kind==0?(a[1]<8?a[1]:8):a[1]))fatal("INPUT_DOMAIN");
  if(kind==0){
   if(a[1]<1||a[1]>8||a[23]<1||a[23]>8||number(a[2])<0||!isfinite(number(a[24]))||number(a[24])<0||!finite_points(a+25,a[23]))fatal("INPUT_DOMAIN");
   if(!rigid(a+19)||!rigid(a+41))fatal("INPUT_ROTATION");
   if(a[46]>3)fatal("INPUT_CACHE");
   for(unsigned i=0;i<a[46];++i)if(a[47+i]>=a[1]||a[50+i]>=a[23])fatal("INPUT_CACHE");
  }else if(kind==2){for(int j=23;j<=26;++j)if(!isfinite(number(a[j])))fatal("INPUT_DOMAIN");}
 }
}
                                                                                  
static unsigned checked(unsigned kind,const uint32_t *a,const b2SimplexCache *cache,unsigned *reason){
 *reason=0;if(!isfinite(number(a[2]))||number(a[2])<0)return 5;
 if(kind==0){
  if(!isfinite(number(a[24]))||number(a[24])<0||!rigid(a+19)||!rigid(a+41))return 5;
  if(cache->count>3){*reason=82;return 5;}
  if(a[1]>=1&&a[1]<=8&&a[23]>=1&&a[23]<=8)
   for(unsigned i=0;i<3;++i)if(i<cache->count&&(cache->indexA[i]>=a[1]||cache->indexB[i]>=a[23])){*reason=82;return 5;}
 }else if(kind==2&&!rigid(a+23))return 5;
 if(a[1]<1||a[1]>8)return 4;
 if(kind==0&&(a[23]<1||a[23]>8))return 4;
 if(!finite_points(a+3,a[1]))return 4;
 if(kind==0&&!finite_points(a+25,a[23]))return 4;
 return 0;
}
static b2SimplexCache decode_cache(const uint32_t *a){
 b2SimplexCache k={0};k.count=(uint16_t)a[46];for(int j=0;j<3;++j){k.indexA[j]=(uint8_t)a[47+j];k.indexB[j]=(uint8_t)a[50+j];}return k;
}
static b2ShapeProxy decode_proxy(const uint32_t *a,unsigned count,unsigned radius){
 b2ShapeProxy p={0};p.count=(int)count;p.radius=number(radius);
 for(unsigned j=0;j<count&&j<8;++j)p.points[j]=(b2Vec2){number(a[2*j]),number(a[2*j+1])};return p;
}
static b2Transform decode_transform(const uint32_t *a){return(b2Transform){{number(a[0]),number(a[1])},{number(a[2]),number(a[3])}};}
static void echo(unsigned kind,const uint32_t *a){printf("E13A %u %u %u",current_id,current_seq,kind);for(int j=0;j<64;++j)h(a[j]);puts("");}
static void operation(unsigned kind,const uint32_t *a,b2SimplexCache *history,bool warm,bool first){
 b2SimplexCache k=kind==0&&warm&&!first?*history:decode_cache(a),ki=k;
 if(kind==0&&warm&&first)*history=k;
 if(kind==0&&!a[0]){
  if(k.count>3)fatal("INPUT_CACHE");
  for(unsigned i=0;i<k.count;++i)if(k.indexA[i]>=a[1]||k.indexB[i]>=a[23])fatal("INPUT_CACHE");
 }
 unsigned reason=0,status=a[0]?checked(kind,a,&k,&reason):0;
 b2DistanceOutput out={0};b2ShapeProxy proxy={0};b2Simplex trace[23];int ntrace=0,nvertices=0;
 if(!status&&kind==0){
  b2DistanceInput in={0};in.proxyA=decode_proxy(a+3,a[1],a[2]);in.proxyB=decode_proxy(a+25,a[23],a[24]);
  in.transformA=decode_transform(a+19);in.transformB=decode_transform(a+41);in.useRadii=a[45]!=0;
  for(int i=0;i<23;++i)trace[i].count=-1;
  begin_observation(k.count);out=b2ShapeDistance(&in,&k,a[54]?trace:NULL,(int)a[53]);observing=false;
  for(unsigned i=0;i<a[53];++i)if(trace[i].count!=-1){++ntrace;nvertices+=trace[i].count;}
  if(ntrace!=trace_count)abort();if(warm)*history=k;
 }else if(!status){
  b2Vec2 points[10];for(unsigned j=0;j<a[1];++j)points[j]=(b2Vec2){number(a[3+2*j]),number(a[4+2*j])};
  proxy=kind==1?b2MakeProxy(points,(int)a[1],number(a[2])):b2MakeOffsetProxy(points,(int)a[1],number(a[2]),(b2Vec2){number(a[23]),number(a[24])},(b2Rot){number(a[25]),number(a[26])});
 }
 echo(kind,a);printf("A13 %u %u",current_id,current_seq);h(status);h(reason);puts("");
 if(!status&&kind==0){
  cache_out("KI13",&ki);printf("D13A %u %u",current_id,current_seq);
  h(word(out.pointA.x));h(word(out.pointA.y));h(word(out.pointB.x));h(word(out.pointB.y));h(word(out.normal.x));h(word(out.normal.y));h(word(out.distance));h((uint32_t)out.iterations);h((uint32_t)out.simplexCount);puts("");cache_out("K13A",&k);
  for(int i=0;i<ntrace;++i){printf("T13A %u %u %d",current_id,current_seq,i);h((uint32_t)trace[i].count);puts("");
   const b2SimplexVertex *v[]={&trace[i].v1,&trace[i].v2,&trace[i].v3};
   for(int j=0;j<trace[i].count;++j){printf("V13A %u %u %d %d",current_id,current_seq,i,j);h(trace_defined[i][j]);h(word(v[j]->wA.x));h(word(v[j]->wA.y));h(word(v[j]->wB.x));h(word(v[j]->wB.y));h(word(v[j]->w.x));h(word(v[j]->w.y));h(trace_defined[i][j]?word(v[j]->a):0);h((uint32_t)v[j]->indexA);h((uint32_t)v[j]->indexB);puts("");}
  }
 }else if(!status){printf("P13A %u %u",current_id,current_seq);h((uint32_t)proxy.count);h(word(proxy.radius));for(int j=0;j<proxy.count;++j){h(word(proxy.points[j].x));h(word(proxy.points[j].y));}puts("");}
 printf("ZA13 %u %u",current_id,current_seq);h(1);h(1);h(!status&&kind==0);h(!status&&kind==0);h(!status&&kind==0);h(!status&&kind!=0);h((uint32_t)ntrace);h((uint32_t)nvertices);puts("");
}
static void read_words(uint32_t *a,int start){for(int j=0;j<64;++j)a[j]=hexadecimal(tokens[start+j]);}
int main(int argc,char **argv){
 input=argc>1?fopen(argv[1],"rb"):stdin;if(!input)return 1;
 need_line();unsigned n;
 if(!strcmp(tokens[0],"PORT13A")){
  arity(3);if(strlen(tokens[1])!=1||(tokens[1][0]!='R'&&tokens[1][0]!='D'))fatal("INPUT_PROFILE");
  if(tokens[1][0]!=PORT13_PROFILE)fatal("INPUT_PROFILE");n=decimal(tokens[2]);if(n<1||n>128)fatal("INPUT_N");
 }else if(!strcmp(tokens[0],"GUARD13A")){
  guard=true;arity(2);n=decimal(tokens[1]);if(n!=1)fatal("INPUT_N");
 }else fatal("INPUT_TAG");
 if(!guard)printf("PORT13A %c %u\n",PORT13_PROFILE,n);
 for(current_id=1;current_id<=n;++current_id){
  unsigned count,after=0;uint32_t ga[64]={0};
  need_line();
  if(guard){
   if(strcmp(tokens[0],"G"))fatal("INPUT_TAG");arity(5);if(decimal(tokens[1])!=1)fatal("INPUT_ID");
   guard_kind=decimal(tokens[2]);after=decimal(tokens[3]);count=decimal(tokens[4]);
   if(guard_kind!=0&&guard_kind!=100&&guard_kind!=101&&guard_kind!=102&&guard_kind!=103)fatal("INPUT_OPCODE");
   if(after)fatal("INPUT_PHASE");if((guard_kind==0&&(count<1||count>16))||(guard_kind!=0&&count))fatal("INPUT_OPCOUNT");
   need_line();if(strcmp(tokens[0],"GA"))fatal("INPUT_TAG");arity(66);if(decimal(tokens[1])!=1)fatal("INPUT_ID");read_words(ga,2);
   if(guard_kind==0||guard_kind==103){for(int j=0;j<64;++j)if(ga[j])fatal("INPUT_UNUSED");}
   else {validate_syntax(guard_kind-100,ga,false,false);if(ga[0]!=1)fatal("INPUT_MODE");}
   printf("GUARD13A 1\nG 1 %u 0 %u\nGA 1",guard_kind,count);for(int j=0;j<64;++j)h(ga[j]);puts("");
  }else{
   if(strcmp(tokens[0],"C"))fatal("INPUT_TAG");arity(3);if(decimal(tokens[1])!=current_id)fatal("INPUT_ID");count=decimal(tokens[2]);
   if(count<1||count>32||(current_id>=113&&count!=1))fatal("INPUT_OPCOUNT");
  }
  printf("CASE %u %u\n",current_id,count);b2SimplexCache history={0};unsigned traced_calls=0;
  for(current_seq=1;current_seq<=count;++current_seq){
   need_line();if(strcmp(tokens[0],"O"))fatal("INPUT_TAG");arity(67);if(decimal(tokens[1])!=current_seq)fatal("INPUT_SEQ");unsigned kind=decimal(tokens[2]);uint32_t a[64];read_words(a,3);
   bool warm=!guard&&current_id>=85&&current_id<=88,cold=!guard&&current_id>=89&&current_id<=92;
   validate_syntax(kind,a,(guard&&guard_kind==0)||(!guard&&current_id>=113),warm&&current_seq>1);
   if(guard&&guard_kind==0&&a[54]&&++traced_calls>1)fatal("INPUT_OPCOUNT");
   if(cold)for(int j=46;j<=52;++j)if(a[j])fatal("INPUT_UNUSED");operation(kind,a,&history,warm,current_seq==1);
  }
  if(guard&&guard_kind){
   current_seq=0;unsigned reason=0,status=0,value1=0,value2=0;
   if(guard_kind==103){b2Vec2 p[]={{0,0},{1,0}};b2ShapeProxy source=b2MakeProxy(p,2,0),copy1=source,copy2=source;copy1.points[1].x=123;
    b2SimplexCache k={.count=1,.indexA={1,0,0}},k1=k,k2=k;k1.indexA[0]=7;
    value1=2;value2=(copy2.points[1].x==1&&source.points[1].x==1?1u:0u)|(k2.indexA[0]==1&&k.indexA[0]==1?2u:0u);
    if(copy1.points[1].x!=123||k1.indexA[0]!=7)abort();
   }else{b2SimplexCache k=decode_cache(ga);status=checked(guard_kind-100,ga,&k,&reason);}
   printf("GR13 1 0 %u",guard_kind);h(status);h(status==0&&(guard_kind!=103||value2==3));h(value1);h(value2);puts("");
  }
  printf("ENDCASE %u\n",current_id);
 }
 if(fgetc(input)!=EOF)fatal("INPUT_TRAILING_DATA");printf("END %u\n",n);if(input!=stdin)fclose(input);return ferror(stdout)?1:0;
}
#else
                                                                           
                                                                         
static int reason13;
#include "lancuchy-base12.inc"

typedef struct Chain13 {bool saved,live;b2ChainId raw;uint64_t birth,owner;} Chain13;
typedef struct Meta13 {uint64_t world,birth,owner;uint16_t generation;bool occupied;} Meta13;
typedef struct View13 {bool saved;Chain13 chain;Body body;int count;Shape child[128];} View13;
static Chain13 chains13[16];static Meta13 meta13[WORLDS][16];static View13 copies13[4];
static b2Vec2 points13[128];static b2SurfaceMaterial materials13[128];
static b2Vec2* savedPoints13;static b2SurfaceMaterial* savedMaterials13;
static int status13,query13=-1,parent13=-1,mutation13=-1;
static uint32_t count13[17],privateCount13[6],currentA13[64];
static bool guard13;
#ifdef PORT13C
static int guardPair13c(const uint32_t*);
#endif
static int chainHistory13;

static void prefix13(const char* tag,int n,int a,int b,int c)
{prefix12(tag,a,b,n<2?n:2);if(n==3)printf(" %d",c);}
static void rawchain13(b2ChainId raw){word(raw.index1);word(raw.world0);word(raw.generation);}
static void numberchain13(Chain13 c){word(c.raw.index1-1);wide(c.birth);wide(c.owner);}
static void numbershape13(Shape s){word(s.raw.index1-1);wide(s.birth);wide(s.owner);}
static void numberbody13(Body b){word(b.raw.index1-1);wide(b.birth);wide(b.owner);}
static void rawshape13(Shape s){word(s.raw.index1);word(s.raw.world0);word(s.raw.generation);}
static void chainhandle13(Chain13 c){rawchain13(c.raw);numberchain13(c);}
static bool chainlive13(const Chain13* c)
{
    if(!c->saved)return false;bool owner=false;
    for(int j=0;j<WORLDS;++j)if(world_live(worlds+j)&&worlds[j].birth==c->owner&&worlds[j].raw.index1==c->raw.world0+1)owner=true;
    if(!owner)return false;
    for(int j=0;j<16;++j)if(chains13[j].live&&chains13[j].owner==c->owner&&chains13[j].birth==c->birth&&
        b2StoreChainId(chains13[j].raw)==b2StoreChainId(c->raw))return b2Chain_IsValid(c->raw);
    return false;
}
static int chainguard13(int owner,int reg)
{if(!world_live(worlds+owner))return STALE;if(worlds[owner].birth!=chains13[reg].owner)return FOREIGN;return chainlive13(chains13+reg)?OK:STALE;}
static Chain13 publicchain13(b2ChainId raw)
{for(int j=0;j<16;++j)if(chains13[j].live&&chainlive13(chains13+j)&&b2StoreChainId(chains13[j].raw)==b2StoreChainId(raw))return chains13[j];fail("INPUT_DOMAIN");return (Chain13){0};}
static void sync13(void)
{
    for(int j=0;j<16;++j)if(chains13[j].live&&!chainlive13(chains13+j))chains13[j].live=false;
    if(OBS)for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2World* w=b2GetWorldFromId(worlds[owner].raw);
        if(w->chainIdPool.nextIndex>16)fail("INPUT_POPULATION");
        for(int j=0;j<w->chainIdPool.nextIndex;++j){Meta13* m=&meta13[owner][j];
            if(m->world!=worlds[owner].birth)*m=(Meta13){.world=worlds[owner].birth};
            m->occupied=w->chainShapes.data[j].id==j;}}
}
static bool material13(b2SurfaceMaterial m)
{return isfinite(m.friction)&&m.friction>=0&&isfinite(m.restitution)&&m.restitution>=0&&isfinite(m.rollingResistance)&&m.rollingResistance>=0&&isfinite(m.tangentSpeed);}
static float orientation13(b2Vec2 a,b2Vec2 b,b2Vec2 c,bool* finite)
{
    float x=b.x-a.x,y=b.y-a.y,u=c.x-a.x,v=c.y-a.y,p=x*v,q=y*u,r=p-q;
    *finite=*finite&&isfinite(x)&&isfinite(y)&&isfinite(u)&&isfinite(v)&&isfinite(p)&&isfinite(q)&&isfinite(r);return r;
}
static bool on13(b2Vec2 a,b2Vec2 b,b2Vec2 p)
{return fminf(a.x,b.x)<=p.x&&p.x<=fmaxf(a.x,b.x)&&fminf(a.y,b.y)<=p.y&&p.y<=fmaxf(a.y,b.y);}
static int geometry13(const b2Vec2* p,int n,bool loop)
{
    if(n<4){reason13=84;return GEOMETRY;}
    for(int i=0;i<n;++i)if(!finite_vec(p[i])){reason13=84;return GEOMETRY;}
    for(int i=0;i<n;++i)for(int j=i+1;j<n;++j){float dx=p[j].x-p[i].x,dy=p[j].y-p[i].y,xx=dx*dx,yy=dy*dy,d=xx+yy;
        if(!isfinite(dx)||!isfinite(dy)||!isfinite(xx)||!isfinite(yy)||!isfinite(d)||!(d>.005f*.005f)){reason13=84;return GEOMETRY;}}
    int edges=loop?n:n-1;
    for(int i=0;i<edges;++i)for(int j=i+1;j<edges;++j){b2Vec2 a=p[i],b=p[(i+1)%n],c=p[j],d=p[(j+1)%n];bool finite=true;
        float r0=orientation13(a,b,c,&finite),r1=orientation13(a,b,d,&finite),r2=orientation13(c,d,a,&finite),r3=orientation13(c,d,b,&finite);
        if(!finite){reason13=84;return GEOMETRY;}
        bool adjacent=j==i+1||(loop&&i==0&&j==edges-1),bad=false;
        if(adjacent){if(r0==0&&r1==0){bool x=fabsf(b.x-a.x)>=fabsf(b.y-a.y);
            float a0=x?a.x:a.y,b0=x?b.x:b.y,c0=x?c.x:c.y,d0=x?d.x:d.y;
            bad=fmaxf(fminf(a0,b0),fminf(c0,d0))<fminf(fmaxf(a0,b0),fmaxf(c0,d0));}}
        else bad=((r0<0&&r1>0||r0>0&&r1<0)&&(r2<0&&r3>0||r2>0&&r3<0))||
            (r0==0&&on13(a,b,c))||(r1==0&&on13(a,b,d))||(r2==0&&on13(c,d,a))||(r3==0&&on13(c,d,b));
        if(bad){reason13=85;return GEOMETRY;}
    }return OK;
}
static int createchain13(const Operation* o)
{
    const uint32_t* a=o->u;int owner=a[1],parent=a[2],reg=a[3],n=a[4],m=a[6];bool game=a[0];
    int status=guard(worlds+owner,bodies+parent);if(status)return status;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);if(game&&w->locked){reason13=1;return 7;}
    if(game&&b2Body_GetType(bodies[parent].raw)!=b2_staticBody){reason13=80;return PARAM;}
    if(m!=1&&m!=n){if(!game)fail("INPUT_DOMAIN");reason13=83;return PARAM;}
    for(int j=0;j<m;++j)if(!material13(materials13[j])){if(!game)fail("INPUT_DOMAIN");reason13=0;return PARAM;}
    if(game){status=geometry13(points13,n,a[5]);if(status)return status;}
    else {if(n<4)fail("INPUT_DOMAIN");for(int j=0;j<n;++j)if(!finite_vec(points13[j]))fail("INPUT_DOMAIN");}
    int count=a[5]?n:n-3,available=0;
    for(int j=0;j<SHAPES;++j)available+=!shapes[j].saved;
    if(available<count||lastIssued>UINT64_MAX-(uint64_t)(1+count))return LIMIT;
    int stored=0;for(int j=0;j<WORLDS;++j)if(worlds[j].live){b2World* ww=b2GetWorldFromId(worlds[j].raw);
        for(int k=0;k<ww->chainIdPool.nextIndex;++k)if(ww->chainShapes.data[k].id==k)stored+=ww->chainShapes.data[k].materialCount;}
    if(stored+m>256)fail("INPUT_POPULATION");
    b2Vec2* inputPoints=malloc(n*sizeof(b2Vec2));b2SurfaceMaterial* inputMaterials=malloc(m*sizeof(b2SurfaceMaterial));
    if(!inputPoints||!inputMaterials)fail("INPUT_DOMAIN");memcpy(inputPoints,points13,n*sizeof(b2Vec2));memcpy(inputMaterials,materials13,m*sizeof(b2SurfaceMaterial));
    b2ChainDef def=b2DefaultChainDef();def.points=inputPoints;def.count=n;def.isLoop=a[5];def.materials=inputMaterials;def.materialCount=m;
    def.userData=token(a[7],a[8],a[9]);def.filter=(b2Filter){(uint64_t)a[10]|(uint64_t)a[11]<<32,(uint64_t)a[12]|(uint64_t)a[13]<<32,(int32_t)a[14]};def.enableSensorEvents=a[15];
    b2ChainId raw=b2CreateChain(bodies[parent].raw,&def);if(B2_IS_NULL(raw))fail("INPUT_DOMAIN");
    chains13[reg]=(Chain13){true,true,raw,++lastIssued,worlds[owner].birth};
    if(raw.index1>16)fail("INPUT_POPULATION");
    meta13[owner][raw.index1-1]=(Meta13){worlds[owner].birth,lastIssued,worlds[owner].birth,raw.generation,true};
    b2ShapeId children[128];int actual=b2Chain_GetSegments(raw,children,128);if(actual!=count)fail("INPUT_DOMAIN");
    for(int i=0,j=0;i<count;++i){while(j<SHAPES&&shapes[j].saved)++j;if(j==SHAPES)fail("INPUT_DOMAIN");
        shapes[j++]=(Shape){true,true,children[i],worlds[owner].birth,++lastIssued};}
    free(savedPoints13);free(savedMaterials13);savedPoints13=inputPoints;savedMaterials13=inputMaterials;
    return OK;
}
static void saveview13(int reg,int target)
{
    View13* v=copies13+target;*v=(View13){.saved=true,.chain=chains13[reg]};
    b2ChainId raw=v->chain.raw;b2ShapeId children[128];v->count=b2Chain_GetSegments(raw,children,128);
    if(v->count<1)fail("INPUT_DOMAIN");v->body=public_body_number(b2Shape_GetBody(children[0]));
    for(int j=0;j<v->count;++j)v->child[j]=public_shape_number(children[j]);
}
static void execute13(const Operation* o)
{
    const uint32_t* a=o->u;int code=o->code;
    if(code<100){execute12(o);sync13();return;}
    reset_extra10();
    if(code==100)status13=createchain13(o);
    else if(code>=101&&code<=103){int owner=a[1],reg=a[2];status13=chainguard13(owner,reg);
        if(!status13&&a[0]&&b2GetWorldFromId(worlds[owner].raw)->locked){status13=7;reason13=1;}
        if(!status13&&code==103&&a[3]<2&&(!isfinite(o->f[4])||(a[3]==0||a[0])&&o->f[4]<0)){if(!a[0])fail("INPUT_DOMAIN");status13=PARAM;}
        if(!status13){b2ChainId raw=chains13[reg].raw;
            if(code==101){b2ShapeId list[128];int count=b2Chain_GetSegments(raw,list,128);for(int i=0;i<count;++i)for(int j=0;j<SHAPES;++j)
                    if(shapes[j].live&&b2StoreShapeId(shapes[j].raw)==b2StoreShapeId(list[i]))shapes[j].live=false;
                b2DestroyChain(raw);chains13[reg].live=false;}
            if(code==103){if(a[3]==0)b2Chain_SetFriction(raw,o->f[4]);else if(a[3]==1)b2Chain_SetRestitution(raw,o->f[4]);else b2Chain_SetMaterial(raw,(int32_t)a[4]);}}
        if(code==102)query13=reg;
    }else if(code==104||code==105){status13=shape_guard(worlds+a[1],shapes+a[2]);
        if(!status13&&a[0]&&b2GetWorldFromId(worlds[a[1]].raw)->locked){status13=7;reason13=1;}
        if(!status13&&code==105&&b2Shape_GetType(shapes[a[2]].raw)!=b2_chainSegmentShape){if(!a[0])fail("INPUT_DOMAIN");status13=PARAM;}
        if(code==104)parent13=a[2];
    }else if(code==106){status13=chainguard13(a[0],a[1]);if(!status13)saveview13(a[1],a[2]);}
    else if(code==108)mutation13=a[0];
    else if(code==109){if(a[0]==0){savedPoints13[0].x=123;if(a[1]){free(savedPoints13);savedPoints13=NULL;}}
        else{savedMaterials13[0].friction=2;savedMaterials13[0].userMaterialId=-7;if(a[1]){free(savedMaterials13);savedMaterials13=NULL;}}}
    sync13();population_after9();echo(case9,seq9,o);
    if(code==100){for(uint32_t j=0;j<a[4];++j){prefix13("EP13B",1,j,0,0);vec(points13[j]);putchar('\n');}
        for(uint32_t j=0;j<a[6];++j){b2SurfaceMaterial m=materials13[j];prefix13("EU13B",1,j,0,0);real(m.friction);real(m.restitution);real(m.rollingResistance);real(m.tangentSpeed);word(m.userMaterialId);word(m.customColor);putchar('\n');}}
    dump(case9,seq9,0,0,0,-1);
}
static void querychain13(const Operation* o)
{
    prefix13("CQ13",1,query13,0,0);word(status13);++count13[2];
    if(status13){for(int j=0;j<18;++j)word(0);putchar('\n');return;}
    Chain13 c=chains13[query13];b2WorldId raw=b2Chain_GetWorld(c.raw);word(raw.index1);word(0);word(raw.generation);
    word(raw.index1-1);wide(c.owner);wide(0);
    b2ShapeId first;b2Chain_GetSegments(c.raw,&first,1);Body body=public_body_number(b2Shape_GetBody(first));numberbody13(body);
    int count=b2Chain_GetSegmentCount(c.raw);b2ShapeId list[128];int returned=b2Chain_GetSegments(c.raw,list,o->u[0]?128:o->u[3]);
    word(count);word(returned);real(b2Chain_GetFriction(c.raw));real(b2Chain_GetRestitution(c.raw));word(b2Chain_GetMaterial(c.raw));putchar('\n');
    for(int j=0;j<returned;++j){prefix13("QL13",2,query13,j,0);Shape s=public_shape_number(list[j]);rawshape13(s);numbershape13(s);putchar('\n');++count13[3];}
}
static void view13(int reg,int phase,const Operation* o)
{
    View13* v=copies13+reg;prefix13("COPY13",2,reg,phase,0);putchar('\n');++count13[6];
    prefix13("CV13",2,reg,phase,0);chainhandle13(v->chain);numberbody13(v->body);word(v->count);putchar('\n');++count13[7];
    for(int j=0;j<v->count;++j){Shape s=v->child[j];prefix13("CE13",3,reg,phase,j);rawshape13(s);
        word(phase==1&&(uint32_t)j==o->u[1]?o->u[2]:(uint32_t)(s.raw.index1-1));wide(s.birth);wide(s.owner);putchar('\n');++count13[8];}
    prefix13("ENDCOPY13",2,reg,phase,0);putchar('\n');++count13[9];
}
static void observe13(const Operation* o)
{
    int saved=0,live=0;
    for(int j=0;j<16;++j)if(chains13[j].saved){prefix13("CN13",1,j,0,0);chainhandle13(chains13[j]);putchar('\n');++saved;++count13[1];}
    for(int j=0;j<16;++j)if(chains13[j].saved){prefix13("V13",1,j,0,0);word(b2Chain_IsValid(chains13[j].raw));word(chainlive13(chains13+j));putchar('\n');++count13[16];}
    if(query13>=0)querychain13(o);
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){Shape* live[128]={0};
        for(int reg=0;reg<SHAPES;++reg)if(shapes[reg].live&&shapes[reg].owner==worlds[owner].birth){int slot=shapes[reg].raw.index1-1;if(slot<0||slot>=128)fail("INPUT_POPULATION");live[slot]=shapes+reg;}
        for(int j=0;j<128;++j)if(live[j]&&b2Shape_GetType(live[j]->raw)==b2_chainSegmentShape){
            b2ChainSegment c=b2Shape_GetChainSegment(live[j]->raw);prefix13("CS13",2,owner,j,0);vec(c.ghost1);vec(c.segment.point1);vec(c.segment.point2);vec(c.ghost2);word(c.chainId);putchar('\n');++count13[4];}}
    if(parent13>=0){prefix13("PC13",1,parent13,0,0);word(status13);++count13[5];
        b2ChainId raw=status13?b2_nullChainId:b2Shape_GetParentChain(shapes[parent13].raw);word(B2_IS_NON_NULL(raw));
        if(B2_IS_NON_NULL(raw))chainhandle13(publicchain13(raw));else for(int j=0;j<8;++j)word(0);putchar('\n');}
    for(int j=0;j<4;++j)if(copies13[j].saved){view13(j,0,o);if(mutation13==j){view13(j,1,o);view13(j,2,o);}}
    for(int j=0;j<16;++j)live+=chains13[j].live;
    if(OBS){
        for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2World* w=b2GetWorldFromId(worlds[owner].raw);
            for(int j=0;j<w->chainIdPool.nextIndex;++j){b2ChainShape* c=w->chainShapes.data+j;bool alive=c->id==j;prefix13("CH13",2,owner,j,0);word(alive);
                word(alive?c->bodyId:0);word(alive?c->nextChainId:0);word(alive?c->count:0);word(alive?c->materialCount:0);putchar('\n');++privateCount13[0];}
            for(int j=0;j<w->chainIdPool.nextIndex;++j){b2ChainShape* c=w->chainShapes.data+j;if(c->id!=j)continue;
                for(int k=0;k<c->count;++k){prefix13("CI13",3,owner,j,k);b2Shape* raw=w->shapes.data+c->shapeIndices[k];Shape s=public_shape_number((b2ShapeId){raw->id+1,w->worldId,raw->generation});rawshape13(s);numbershape13(s);putchar('\n');++privateCount13[1];}}
            for(int j=0;j<w->chainIdPool.nextIndex;++j){b2ChainShape* c=w->chainShapes.data+j;if(c->id!=j)continue;
                for(int k=0;k<c->materialCount;++k){prefix13("CM13",3,owner,j,k);b2SurfaceMaterial m=c->materials[k];real(m.friction);real(m.restitution);real(m.rollingResistance);real(m.tangentSpeed);word(m.userMaterialId);word(m.customColor);putchar('\n');++privateCount13[2];}}
            for(int j=0;j<w->bodyIdPool.nextIndex;++j)if(w->bodies.data[j].id==j){prefix13("BH13",2,owner,j,0);word(w->bodies.data[j].headChainId);putchar('\n');++privateCount13[3];}
            prefix13("IP13",1,owner,0,0);word(w->chainIdPool.nextIndex);word(w->chainIdPool.freeArray.count);for(int j=0;j<w->chainIdPool.freeArray.count;++j)word(w->chainIdPool.freeArray.data[j]);putchar('\n');++privateCount13[4];
            for(int j=0;j<w->chainIdPool.nextIndex;++j){Meta13 m=meta13[owner][j];prefix13("CG13",2,owner,j,0);word(m.occupied);word(m.generation);wide(m.birth);wide(m.owner);putchar('\n');++privateCount13[5];}}
        prefix13("I13",0,0,0,0);for(int j=0;j<6;++j)word(privateCount13[j]);putchar('\n');
    }
    count13[0]=1;count13[10]=saved;count13[11]=live;count13[12]=positive11;count13[13]=seq9;
    count13[14]=o->code==100?o->u[4]:0;count13[15]=o->code==100?o->u[6]:0;
    prefix13("Z13",0,0,0,0);for(int j=0;j<17;++j)word(count13[j]);putchar('\n');
}
static uint32_t decimal13(char** p){return decimal12(p,"INPUT_DECIMAL","INPUT_DECIMAL");}
static void arity13(const char* p,int expected,const char* error)
{int n=1;for(;*p;++p)n+=*p==' ';if(n!=expected)fail(rowEof11?"INPUT_EOF":error);}
static void reg13(uint32_t reg,int capacity,bool initialized,bool create,bool live)
{if(reg>=(uint32_t)capacity)fail("INPUT_REGISTER_RANGE");if(create){if(live)fail("INPUT_REGISTER_COLLISION");}else if(!initialized)fail("INPUT_REGISTER_UNINITIALIZED");}
static void registers13(const Operation* o)
{
    const uint32_t* a=o->u;int c=o->code;
    if(c>=100){
        if(c>=107&&c<=108){if(a[0]>=4||!copies13[a[0]].saved)fail("INPUT_COPY");
            if(c==108){View13* v=copies13+a[0];if(a[1]>=(uint32_t)v->count)fail("INPUT_COPY");if(a[2]==(uint32_t)(v->child[a[1]].raw.index1-1))fail("INPUT_DOMAIN");}return;}
        if(c==109){if(a[0]==0?!savedPoints13:!savedMaterials13)fail("INPUT_COPY");return;}
        uint32_t owner=c==106?a[0]:a[1];reg13(owner,WORLDS,owner<WORLDS&&worlds[owner].saved,false,false);
        if(c==100){reg13(a[2],BODIES,a[2]<BODIES&&bodies[a[2]].saved,false,false);reg13(a[3],16,false,true,a[3]<16&&chains13[a[3]].live);}
        else if(c==104||c==105)reg13(a[2],SHAPES,a[2]<SHAPES&&shapes[a[2]].saved,false,false);
        else {uint32_t reg=c==106?a[1]:a[2];reg13(reg,16,reg<16&&chains13[reg].saved,false,false);if(c==106&&a[2]>=4)fail("INPUT_COPY");}
        return;
    }
    if(c==37||c==50){if(a[0]>=4)fail("INPUT_REGISTER_RANGE");if(c==37?!copies[a[0]].saved:!copies9[a[0]].saved)fail("INPUT_REGISTER_UNINITIALIZED");return;}
    if(c==89&&a[0]>=2){if(a[3]>=4||!copies12[a[3]].saved)fail("INPUT_COPY");return;}
    uint32_t owner=c==2||c==30||c==10||c==17||c==40?a[1]:c==16?a[2]:c==89?a[1]:a[0];
    bool make=c==0||c==54||c==56;reg13(owner,WORLDS,owner<WORLDS&&worlds[owner].saved,make,owner<WORLDS&&worlds[owner].live);
    if(make)return;
    int body=-1,shape=-1;bool newbody=false,newshape=false;
    if(c==2||c==30||c==57||c==90){body=c==2||c==30?a[0]:a[1];newbody=true;}
    else if(c==10||c==17||c==40){shape=a[0];newshape=true;body=a[2];}
    else if(c==16){body=a[0];newbody=true;shape=a[1];newshape=true;}
    else if(c==15){if(a[1]==2)body=a[2];else shape=a[2];}
    else if(c==11||c==12||c==14||c==18||c==19||c==39||c==52||c==81)shape=a[1];
    else if(c==88)shape=a[2];
    else if(c==3||c==4||c==5||c==13||c==21||c>=33&&c<=36||c==38||c==48||c>=58&&c<=60||c==62||c==80||c==84||c==92)body=a[1];
    else if(c==83||c==85||c==91){int target=c==83?a[1]+1:a[1];if(target==1)body=a[2];else if(target==2)shape=a[2];}
    if(body>=0)reg13(body,BODIES,body<BODIES&&bodies[body].saved,newbody,body<BODIES&&bodies[body].live);
    if(shape>=0)reg13(shape,SHAPES,shape<SHAPES&&shapes[shape].saved,newshape,shape<SHAPES&&shapes[shape].live);
}
static Operation read13(FILE* file,uint32_t seq)
{
    char* p=row(file);char saved[2050];snprintf(saved,sizeof(saved),"%s\n",p);if(strncmp(p,"O ",2))fail("INPUT_TAG");
    arity13(p,67,"INPUT_ARITY");p+=2;uint32_t actual=decimal13(&p);space(&p);uint32_t code=decimal13(&p);if(actual!=seq)fail("INPUT_SEQ");
    if((code>=41&&code<=45||code>=51&&code<=53||code==64)&&profile12!=15)fail("INPUT_PHASE");
#ifdef PORT13C
    if(code==120)fail("INPUT_PROFILE");
#endif
    if(!(code<=64&&used_legacy12[code]||code>=80&&code<=92||code>=100&&code<=109))fail("INPUT_OPCODE");
    Operation o={.code=code};for(int j=0;j<64;++j){space(&p);o.u[j]=hex_word(&p);o.f[j]=from_bits(o.u[j]);}if(*p)fail("INPUT_ARITY");
    uint32_t* a=o.u;
#ifndef PORT13C
    if(!guard13&&(code==31||code==32)&&o.f[1]>0)fail("INPUT_PROFILE");
#endif
    if(code>=100){int used=code==100?16:code==102?4:code==103?5:code==107?1:code==109?2:3;
        if(code<=105&&a[0]>1)fail("INPUT_MODE");if(code==100&&(a[5]>1||a[7]>1||a[15]>1)||code==109&&a[1]>1)fail("INPUT_BOOL");
        if(code==103&&a[3]>2||code==109&&a[0]>1)fail("INPUT_ENUM");
        for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
        if(code==100){if(a[4]>128||a[6]>128)fail("INPUT_POPULATION");if(!a[7]&&(a[8]||a[9]))fail("INPUT_UNUSED");}
        if(code==102&&(a[0]&&a[3]))fail("INPUT_UNUSED");if(code==102&&!a[0]&&a[3]>128)fail("INPUT_DOMAIN");
        registers13(&o);
        if(code==100){for(int group=0;group<2;++group){uint32_t count=group?a[6]:a[4];
            for(uint32_t i=0;i<count;++i){p=row(file);const char* tag=group?"U13B ":"P13B ";if(strncmp(p,tag,5))fail("INPUT_TAG");arity13(p,group?10:6,group?"INPUT_MATERIAL":"INPUT_POINT");p+=5;
                uint32_t id=decimal13(&p);space(&p);uint32_t s=decimal13(&p);space(&p);uint32_t j=decimal13(&p);if(id!=(uint32_t)case9||s!=seq||j!=i)fail(group?"INPUT_MATERIAL":"INPUT_POINT");
                uint32_t words[6]={0};for(int k=0;k<(group?6:2);++k){space(&p);words[k]=hex_word(&p);}if(*p)fail(group?"INPUT_MATERIAL":"INPUT_POINT");
                if(!group)points13[i]=(b2Vec2){from_bits(words[0]),from_bits(words[1])};
                else materials13[i]=(b2SurfaceMaterial){from_bits(words[0]),from_bits(words[1]),from_bits(words[2]),from_bits(words[3]),(int32_t)words[4],words[5]};}}
            if(!a[0]){if(a[4]<4||(a[6]!=1&&a[6]!=a[4]))fail("INPUT_DOMAIN");for(uint32_t i=0;i<a[6];++i)if(!material13(materials13[i]))fail("INPUT_DOMAIN");for(uint32_t i=0;i<a[4];++i)if(!finite_vec(points13[i]))fail("INPUT_DOMAIN");}}
        if(code==103&&!a[0]&&a[3]<2&&(!isfinite(o.f[4])||a[3]==0&&o.f[4]<0))fail("INPUT_DOMAIN");
        return o;
    }
    registers13(&o);FILE* stream=fmemopen(saved,strlen(saved),"r");if(!stream)fail("INPUT_DOMAIN");o=read12(stream,seq);fclose(stream);return o;
}
static void aggregate13(void)
{
    if(fflush(output9))fail("INPUT_DOMAIN");
    for(char* p=outputBytes9;p&&*p;){char tag[16];unsigned id,seq,index,status;int consumed=0;
        if(sscanf(p,"%15s %u %u %u %u%n",tag,&id,&seq,&index,&status,&consumed)==5&&!strcmp(tag,"R")&&status&&!status13)status13=status;
        if(!strncmp(p,"AP12 ",5)){unsigned reason;if(sscanf(p,"AP12 %u %u %u %u",&id,&seq,&status,&reason)==4&&status&&!status13){status13=status;if(reason==1)reason13=1;else if(reason13!=80&&reason13!=81)reason13=0;}}
        p=strchr(p,'\n');if(p)++p;
    }
}
static void runrow13(FILE* input,int id,uint32_t seq)
{
    reset_operation9(id,seq,0);traceCount11=0;status12=reason12=reason13=status13=0;vectorKind12=-1;vector12=b2Vec2_zero;private12=0;hasPreparedGeometry12=false;
    traceCount12=callbackAPCount12=0;readShape12=copyMutation12=-1;query13=parent13=mutation13=-1;
    memset(finals11,0,sizeof(finals11));memset(count11,0,sizeof(count11));memset(public11,0,sizeof(public11));memset(counts10,0,sizeof(counts10));memset(hitsCount10,0,sizeof(hitsCount10));memset(counts12,0,sizeof(counts12));memset(count13,0,sizeof(count13));memset(privateCount13,0,sizeof(privateCount13));
    begin_output9();Operation o=read13(input,seq);opcode9=o.code;fixture11=guard13&&guardSeedApplied10||profile12==15&&(o.code==51||o.code==52||o.code==64);
#ifdef PORT13C
    if(profile12==15)phase_check9(&o);
#endif
    population9(&o);
    int beforeChain[WORLDS]={0};for(int j=0;j<WORLDS;++j)if(worlds[j].live)beforeChain[j]=b2GetWorldFromId(worlds[j].raw)->chainIdPool.nextIndex;
    execute13(&o);for(int j=0;j<WORLDS;++j)if(worlds[j].live){int n=b2GetWorldFromId(worlds[j].raw)->chainIdPool.nextIndex;if(n>beforeChain[j])chainHistory13+=n-beforeChain[j];}
    if(chainHistory13>(guard13||profile12==15?4:16))fail("INPUT_POPULATION");
    if(o.code<100)aggregate13();prefix13("A13",0,0,0,0);word(status13);word(reason13);putchar('\n');
    hits10(&o);public_sleep11(&o);observe12();world10_dump();private_sleep11();observe13(&o);
    if(OBS){prefix12("I10",0,0,0);for(int j=0;j<6;++j)word(counts10[j]);putchar('\n');prefix12("I11",0,0,0);for(int j=0;j<11;++j)word(count11[j]);putchar('\n');}
    prefix12("Z10",0,0,0);for(int j=0;j<4;++j)word(hitsCount10[j]);word(completed10);putchar('\n');
    prefix12("Z11",0,0,0);word(public11[0]);word(public11[1]);word(positive11);putchar('\n');
    prefix12("I12",0,0,0);for(int j=0;j<11;++j)word(counts12[j]);putchar('\n');if(OBS){prefix12("IP12",0,0,0);word(private12);putchar('\n');}
    prefix12("Z12",0,0,0);word(positive11);word(seq);putchar('\n');commit10();
}
static void reset13(int id)
{reset12(id);chainHistory13=0;memset(chains13,0,sizeof(chains13));memset(meta13,0,sizeof(meta13));memset(copies13,0,sizeof(copies13));free(savedPoints13);savedPoints13=NULL;free(savedMaterials13);savedMaterials13=NULL;}
static void resultguard13(uint32_t seq,int helper,int status,bool accepted,uint64_t value)
{printf("GR13 1 %"PRIu32" %d",seq,helper);word(status);word(accepted);wide(value);putchar('\n');}
static int value_status13(World owner,Chain13 number)
{
    if(!world_live(&owner))return STALE;if(owner.birth!=number.owner)return FOREIGN;
    b2World* w=b2GetWorldFromId(owner.raw);uint32_t slot=(uint32_t)(number.raw.index1-1);
    if(slot>=(uint32_t)w->chainIdPool.nextIndex)return STALE;
    b2ChainShape* c=w->chainShapes.data+slot;Meta13 m=meta13[owner9(w)][slot];
    if(c->id!=(int)slot||m.birth!=number.birth||m.owner!=number.owner||c->generation!=number.raw.generation)return STALE;
    return b2Chain_IsValid(number.raw)?OK:STALE;
}
static void seed13(const uint32_t* a,int kind,uint32_t seq)
{
    if(kind==0)return;
    if(kind==11){if(chainguard13(a[0],a[1]))fail("INPUT_REGISTER_UNINITIALIZED");
        Chain13* c=chains13+a[1];b2World* w=b2GetWorldFromId(worlds[a[0]].raw);w->chainShapes.data[c->raw.index1-1].generation=a[2];c->raw.generation=a[2];meta13[a[0]][c->raw.index1-1].generation=a[2];guardSeedApplied10=true;return;}
    if(kind==8&&a[0]==4){int owner=a[1],source=a[2],field=a[3];uint32_t replacement=a[4];
        if(!worlds[owner].saved||!chains13[source].saved)fail("INPUT_REGISTER_UNINITIALIZED");Chain13 number=chains13[source];
        if(field==1||field==2)number.owner=replace_half10(number.owner,field==2,replacement);
        else if(field==3||field==4)number.birth=replace_half10(number.birth,field==4,replacement);
        else if(field==5)number.raw.index1=(int32_t)(replacement+1u);
        int status=STALE;
        if(world_live(worlds+owner)){b2World* w=b2GetWorldFromId(worlds[owner].raw);int oldCount=w->chainShapes.count;
            if(field==5&&replacement==(uint32_t)w->chainIdPool.nextIndex){b2ChainShape extra=w->chainShapes.data[chains13[source].raw.index1-1];extra.id=(int)replacement;
                if(w->chainShapes.count<=(int)replacement)b2ChainShapeArray_Resize(&w->chainShapes,(int)replacement+1);w->chainShapes.data[replacement]=extra;}
            if((field==6||field==7)&&number.raw.index1>0&&number.raw.index1<=w->chainIdPool.nextIndex){b2ChainShape* c=w->chainShapes.data+number.raw.index1-1;int oldId=c->id;uint16_t oldGen=c->generation;
                if(field==6)c->id=(int32_t)replacement;else c->generation=replacement;status=value_status13(worlds[owner],number);c->id=oldId;c->generation=oldGen;}
            else status=value_status13(worlds[owner],number);
            if(w->chainShapes.count>oldCount){w->chainShapes.data[oldCount].id=-1;w->chainShapes.count=oldCount;}
        }else status=value_status13(worlds[owner],number);
        guardSeedApplied10=true;resultguard13(seq+1,14,status,status==OK,0);return;
    }
    seed_guard12(a,kind,kind==8?seq+1:seq);
}
static void fixedchain13(bool lock)
{
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.maximumLinearSpeed=100;wd.enableContinuous=false;wd.enableSleep=!lock;wd.workerCount=1;wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
    if(create_world(0,wd))fail("INPUT_DOMAIN");b2BodyDef bd=b2DefaultBodyDef();bd.type=b2_staticBody;bd.enableSleep=!lock;if(create_body(0,0,bd))fail("INPUT_DOMAIN");
    Operation op={.code=100};op.u[0]=1;op.u[4]=4;op.u[6]=1;op.u[10]=1;op.u[12]=op.u[13]=UINT32_MAX;
    points13[0]=(b2Vec2){2,0};points13[1]=(b2Vec2){1,0};points13[2]=(b2Vec2){-1,0};points13[3]=(b2Vec2){-2,0};materials13[0]=(b2SurfaceMaterial){.friction=.6f};
    if(createchain13(&op))fail("INPUT_DOMAIN");
    if(lock){uint32_t a[64]={0};a[4]=to_bits(1);a[5]=a[6]=a[7]=1;a[9]=a[10]=UINT32_MAX;a[17]=to_bits(1);
        if(create_shape(1,0,0,a,false))fail("INPUT_DOMAIN");bd.type=b2_dynamicBody;bd.position=(b2Vec2){0,1.5f};
        if(create_body(1,0,bd)||create_shape(2,0,1,a,false))fail("INPUT_DOMAIN");b2Shape_EnablePreSolveEvents(shapes[1].raw,true);b2Shape_EnablePreSolveEvents(shapes[2].raw,true);}
    sync_hooks12();
}
static Operation lock13;static int lockAnswer13=-1,lockCount13;
static bool callback13(b2ShapeId a,b2ShapeId b,b2Manifold* m,void* context)
{
    (void)a;(void)b;(void)m;(void)context;++lockCount13;const uint32_t* u=lock13.u;int status;
    if(lock13.code==100)status=guard(worlds+u[1],bodies+u[2]);else status=chainguard13(u[1],u[2]);
    if(!status&&b2GetWorldFromId(worlds[u[1]].raw)->locked)status=7;
    lockAnswer13=status;return true;
}
static void readgroup13(FILE* input,uint32_t seq,const uint32_t* a)
{
    for(int group=0;group<2;++group)for(uint32_t i=0;i<(group?a[6]:a[4]);++i){char* p=row(input);if(strncmp(p,group?"U13B ":"P13B ",5))fail("INPUT_TAG");
        arity13(p,group?10:6,group?"INPUT_MATERIAL":"INPUT_POINT");p+=5;uint32_t id=decimal13(&p);space(&p);uint32_t s=decimal13(&p);space(&p);uint32_t j=decimal13(&p);
        if(id!=1||s!=seq||j!=i)fail(group?"INPUT_MATERIAL":"INPUT_POINT");uint32_t words[6]={0};for(int k=0;k<(group?6:2);++k){space(&p);words[k]=hex_word(&p);}
        if(*p)fail(group?"INPUT_MATERIAL":"INPUT_POINT");if(group)materials13[i]=(b2SurfaceMaterial){from_bits(words[0]),from_bits(words[1]),from_bits(words[2]),from_bits(words[3]),(int32_t)words[4],words[5]};
        else points13[i]=(b2Vec2){from_bits(words[0]),from_bits(words[1])};}
}
static int guardmain13(FILE* input)
{
    guard13=true;guardMode10=true;profile11=profile12=
#ifdef PORT13C
    14;
#else
    12;
#endif
    reset13(1);char* p=row(input);if(strncmp(p,"G ",2))fail("INPUT_TAG");arity13(p,5,"INPUT_ARITY");p+=2;
    uint32_t id=decimal13(&p);space(&p);uint32_t kind=decimal13(&p);space(&p);uint32_t seed=decimal13(&p);space(&p);uint32_t ops=decimal13(&p);
    if(*p)fail("INPUT_ARITY");if(id!=1)fail("INPUT_ID");bool operations=kind==0||kind==4||kind==7||kind==8||kind==11;
    if((operations&&(!ops||ops>16||seed>ops))||(!operations&&(ops||seed)))fail("INPUT_OPCOUNT");
    if(!(kind<=13||kind==200||kind==203||kind==218||kind==219||kind==280||kind==281||kind==300||kind==301||kind==303
#ifdef PORT13C
        ||kind==320
#endif
    ))fail("INPUT_OPCODE");
    p=row(input);if(strncmp(p,"GA ",3))fail("INPUT_TAG");arity13(p,66,"INPUT_ARITY");p+=3;id=decimal13(&p);if(id!=1)fail("INPUT_ID");uint32_t a[64];for(int j=0;j<64;++j){space(&p);a[j]=hex_word(&p);}if(*p)fail("INPUT_ARITY");
    int used=kind==1?11:kind==2?2:kind==3?5:kind==4?3:kind==5?2:kind==6?4:kind==7||kind==8?5:kind>=11&&kind<=13?3:kind==200||kind==300?16:kind==203||kind==303?5:kind==301?3:kind==218?2:kind==219?3:kind==280?5:kind==281?44:kind==320?43:0;
    for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
    if(kind==11){if(a[0]>=WORLDS||a[1]>=16)fail("INPUT_REGISTER_RANGE");if(a[2]>65535)fail("INPUT_DOMAIN");}
    if(kind==12&&a[2]>128)fail("INPUT_POPULATION");if(kind==13&&(a[1]>65535||a[2]>65535))fail("INPUT_DOMAIN");
    if(kind==8&&(a[0]>4||a[1]>=WORLDS||a[3]>7))fail("INPUT_DOMAIN");
    if(kind==200){if(a[0]!=1)fail("INPUT_MODE");if(a[4]>128||a[6]>128)fail("INPUT_POPULATION");if(a[5]>1||a[7]>1||a[15]>1)fail("INPUT_BOOL");if(!a[7]&&(a[8]||a[9]))fail("INPUT_UNUSED");readgroup13(input,0,a);}
    int status=OK,helper=kind;uint64_t value=0;bool accepted=false;
    if(!operations){begin_output9();
#ifdef PORT13C
        if(kind==320){status=guardPair13c(a);}
        else
#endif
        if(kind==12){helper=112;value=1+a[2];uint64_t last=(uint64_t)a[0]|(uint64_t)a[1]<<32;status=last>UINT64_MAX-value?LIMIT:OK;}
        else if(kind==13){helper=113;b2ChainId raw={(int32_t)a[0],a[1],a[2]};value=b2StoreChainId(raw);b2ChainId loaded=b2LoadChainId(value);if(loaded.index1!=raw.index1||loaded.world0!=raw.world0||loaded.generation!=raw.generation)status=PARAM;}
        else if(kind==200){if(a[6]!=1&&a[6]!=a[4])status=PARAM;else{for(uint32_t j=0;j<a[6];++j)if(!material13(materials13[j]))status=PARAM;if(!status)status=geometry13(points13,a[4],a[5]);}}
        else if(kind>=203){fixedchain13(kind>=300);Operation o={.code=kind-200};for(int j=0;j<64;++j){o.u[j]=a[j];o.f[j]=from_bits(a[j]);}
            if(kind==203){if(a[0]!=1)fail("INPUT_MODE");if(a[3]>2)fail("INPUT_ENUM");status=chainguard13(a[1],a[2]);if(!status&&a[3]<2&&(!isfinite(o.f[4])||o.f[4]<0))status=PARAM;}
            else if(kind==280){helperOnly12=true;status=body_mut12(&o);helperOnly12=false;}
            else if(kind==218||kind==219||kind==281){status=shape_guard(worlds+a[0],shapes+a[1]);if(!status&&b2Shape_GetType(shapes[a[1]].raw)==b2_chainSegmentShape)status=PARAM;}
            else {lock13=o;lockAnswer13=-1;lockCount13=0;b2World_SetPreSolveCallback(worlds[0].raw,callback13,NULL);b2World_Step(worlds[0].raw,1.0f/60.0f,1);if(lockCount13<1||lockAnswer13<0)fail("INPUT_DOMAIN");status=lockAnswer13;}
            destroy_world(0);
        }else if(kind==1){Operation o={0};for(int j=0;j<64;++j){o.u[j]=a[j];o.f[j]=from_bits(a[j]);}helper=0;status=valid_solver_world10(&o)?OK:PARAM;}
        else if(kind==2){helper=1;status=valid_step(from_bits(a[0]),(int32_t)a[1])?OK:PARAM;}
        else if(kind==3){helper=2+a[0];uint64_t n=guard_count10(a[1],a[2]),added=guard_count10(a[3],a[4]);value=n;status=(a[0]==0?upper_blocks12(n):a[0]==1?contact_blocks_fit10(n):checked_sum10(n,added,&value))?OK:LIMIT;}
        else if(kind==5){helper=20+a[0];status=isfinite(from_bits(a[1]))&&from_bits(a[1])>=0?OK:PARAM;}
        else if(kind==6){helper=9;status=material13((b2SurfaceMaterial){from_bits(a[0]),from_bits(a[1]),from_bits(a[2]),from_bits(a[3]),0,0})?OK:PARAM;}
        else if(kind==9||kind==10){helper=kind==9?40:41;status=copy_probe12(kind,&value)?OK:PARAM;}
        accepted=status==OK;bool bad=ferror(output9);if(fclose(output9))bad=true;output9=NULL;free(outputBytes9);outputBytes9=NULL;outputSize9=0;if(bad)fail("INPUT_DOMAIN");
    }
    printf("G 1 %"PRIu32" %"PRIu32" %"PRIu32"\nGA 1",kind,seed,ops);for(int j=0;j<64;++j)word(a[j]);putchar('\n');
    if(kind==200){for(uint32_t j=0;j<a[4];++j){prefix13("EP13B",1,j,0,0);vec(points13[j]);putchar('\n');}for(uint32_t j=0;j<a[6];++j){b2SurfaceMaterial m=materials13[j];prefix13("EU13B",1,j,0,0);real(m.friction);real(m.restitution);real(m.rollingResistance);real(m.tangentSpeed);word(m.userMaterialId);word(m.customColor);putchar('\n');}}
    printf("CASE 1 %"PRIu32"\n",ops);
    if(operations){if(!seed&&kind!=7)seed13(a,kind,0);for(uint32_t seq=1;seq<=ops;++seq){runrow13(input,1,seq);if(seq==seed&&kind!=7)seed13(a,kind,seq);}if(kind==7)seed13(a,kind,ops);
        for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);}
    else resultguard13(0,helper,status,accepted,value);
    printf("ENDCASE 1\n");if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input))fail("INPUT_DOMAIN");printf("END 1\n");
    if(input!=stdin&&fclose(input))fail("INPUT_DOMAIN");free(savedPoints13);free(savedMaterials13);free_tokens();free(trace12);free(callbackAP12);return ferror(stdout)||fflush(stdout)?2:0;
}
#ifdef PORT13C
#include "kontrola-lancuchy-direct.h"
#endif
int main(int argc,char** argv)
{
    if(argc>2)fail("INPUT_DOMAIN");FILE* input=argc==2?fopen(argv[1],"rb"):stdin;if(!input)fail("INPUT_DOMAIN");char* p=row(input);
#ifdef PORT13C
    if(!strncmp(p,"GUARD13C ",9)){arity13(p,2,"INPUT_ARITY");p+=9;uint32_t n=decimal13(&p);if(*p)fail("INPUT_ARITY");if(n!=1)fail("INPUT_N");printf("GUARD13C 1\n");return guardmain13(input);}
    bool component13c=!strncmp(p,"COMPONENT13C ",13);
#else
    if(!strncmp(p,"GUARD13B ",9)){arity13(p,2,"INPUT_ARITY");p+=9;uint32_t n=decimal13(&p);if(*p)fail("INPUT_ARITY");if(n!=1)fail("INPUT_N");printf("GUARD13B 1\n");return guardmain13(input);}
#endif
#ifdef PORT13C
    if(!component13c&&strncmp(p,"PORT13C ",8))fail("INPUT_TAG");arity13(p,2,"INPUT_ARITY");p+=component13c?13:8;uint32_t n=decimal13(&p);if(*p)fail("INPUT_ARITY");if(n<1||n>(component13c?32:432))fail("INPUT_N");
    profile11=profile12=component13c?15:13;printf("%s %"PRIu32"\n",component13c?"COMPONENT13C":"PORT13C",n);
#else
    if(strncmp(p,"PORT13B ",8))fail("INPUT_TAG");arity13(p,2,"INPUT_ARITY");p+=8;uint32_t n=decimal13(&p);if(*p)fail("INPUT_ARITY");if(n<1||n>64)fail("INPUT_N");
    profile11=profile12=11;printf("PORT13B %"PRIu32"\n",n);
#endif
    for(uint32_t id=1;id<=n;++id){p=row(input);if(strncmp(p,"C ",2))fail("INPUT_TAG");arity13(p,3,"INPUT_ARITY");p+=2;
        uint32_t actual=decimal13(&p);space(&p);uint32_t count=decimal13(&p);if(*p)fail("INPUT_ARITY");if(actual!=id)fail("INPUT_ID");
#ifdef PORT13C
        uint32_t bound=component13c?64:id<=384?32:id>=421&&id<=426?1320:720;if(!count||count>bound)fail("INPUT_OPCOUNT");
        reset13(id);b2SimplexCache previous=b2_emptySimplexCache;printf("CASE %"PRIu32" %"PRIu32"\n",id,count);
        for(uint32_t seq=1;seq<=count;++seq){if(!component13c&&id<=384)direct13c(input,id,seq,&previous);else runrow13(input,id,seq);}
#else
        if(!count||count>64)fail("INPUT_OPCOUNT");
        reset13(id);printf("CASE %"PRIu32" %"PRIu32"\n",id,count);for(uint32_t seq=1;seq<=count;++seq)runrow13(input,id,seq);
#endif
#ifdef PORT13C
        if(component13c&&phase9)fail("INPUT_CAPTURE_UNCLOSED");
#endif
        printf("ENDCASE %"PRIu32"\n",id);for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);
    }
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input))fail("INPUT_DOMAIN");if(input!=stdin&&fclose(input))fail("INPUT_DOMAIN");printf("END %"PRIu32"\n",n);
    free(savedPoints13);free(savedMaterials13);free_tokens();free(trace12);free(callbackAP12);return ferror(stdout)||fflush(stdout)?2:0;
}
#endif
