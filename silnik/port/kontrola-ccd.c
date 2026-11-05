                                                                                 
                                                                                  
   
#include "constants.h"
#include "core.h"
#include "box2d/collision.h"
#include "box2d/math_functions.h"
#include <float.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned case_id, sequence, ordinal;
static bool observing;
static uint32_t ccd_bits(float x) { uint32_t u; memcpy(&u,&x,4); return u; }
static float value(uint32_t u) { float f; memcpy(&f,&u,4); return f; }
static void hex(uint32_t u) { printf(" %08"PRIx32,u); }
static void event(unsigned kind,unsigned n,const uint32_t *w) {
    if(!CCD_OBS || !observing)return;
    printf("Q16 %u %u 16 %u %u %u",case_id,sequence,ordinal++,kind,n);
    for(unsigned i=0;i<n;i++)hex(w[i]); puts("");
}
static void ccd_make(uint32_t type,uint32_t x,uint32_t y,uint32_t px,uint32_t py) {
    uint32_t w[]={type,x,y,px,py};event(4,5,w);
}
static void cache_words(uint32_t *w,const b2SimplexCache *c) {
    w[0]=c->count;
    for(int i=0;i<3;i++) { w[1+i]=i<c->count?c->indexA[i]:0;w[4+i]=i<c->count?c->indexB[i]:0; }
}
static void ccd_before(int it,const b2SimplexCache *c) {
    uint32_t w[8]={(uint32_t)it};cache_words(w+1,c);event(7,8,w);
}
static void ccd_after(int it,const b2SimplexCache *c,const b2DistanceOutput *d) {
    uint32_t w[17]={(uint32_t)it};cache_words(w+1,c);
    w[8]=ccd_bits(d->pointA.x);w[9]=ccd_bits(d->pointA.y);w[10]=ccd_bits(d->pointB.x);w[11]=ccd_bits(d->pointB.y);
    w[12]=ccd_bits(d->normal.x);w[13]=ccd_bits(d->normal.y);w[14]=ccd_bits(d->distance);w[15]=d->iterations;w[16]=d->simplexCount;
    event(8,17,w);
}
static void ccd_root(int d,int p,int r,uint32_t a1,uint32_t a2,uint32_t s1,uint32_t s2,uint32_t t,uint32_t s) {
    uint32_t w[]={(uint32_t)d,(uint32_t)p,(uint32_t)r,a1,a2,s1,s2,t,s};event(5,9,w);
}
static void ccd_final(int state,uint32_t fraction,int it) {uint32_t w[]={(uint32_t)state,fraction,(uint32_t)it};event(6,3,w);}

                                                                       
#include "ccd-original.inc"
#undef F
#include "ccd-recipes.inc"

static FILE *input;
static char row[2050],*tokens[80];
static int nt;
static bool diagnostic,guard_profile;
static void fail(const char *s) {fprintf(stderr,"PORT16A: INPUT_%s\n",s);exit(2);}
static bool line(bool first) {
    int c,n=0;bool cr=false;
    while((c=fgetc(input))!=EOF) {
        if(c=='\n')break;
        if(c=='\r') {if(cr)fail("ASCII");cr=true;continue;}
        if(cr)fail("ASCII");
        if(first&&n==0&&c==239) {
            int b=fgetc(input),d=fgetc(input);if(b==187&&d==191)fail("HEADER");fail("ASCII");
        }
        if(c==0||c>126||c<32)fail("ASCII");
        if(n>=2048)fail("LINE_LENGTH");
        row[n++]=(char)c;
    }
    if(c==EOF&&cr)fail("ASCII");
    if(c==EOF&&n==0)return false;
    row[n]=0;
    if(n==0||row[0]==' '||row[n-1]==' ')fail(first?"HEADER":"ARITY");
    nt=0;tokens[nt++]=row;
    for(int i=0;i<n;i++)if(row[i]==' ') {
        if(row[i+1]==' ')fail(first?"HEADER":"ARITY");
        row[i]=0;if(nt>=80)fail("ARITY");tokens[nt++]=row+i+1;
    }
    return true;
}
static void need(void) {if(!line(false))fail("EOF");}
static unsigned decimal(const char *s) {
    uint64_t n=0;if(!*s||(s[0]=='0'&&s[1]))fail("NUMBER");
    for(;*s;s++) {if(*s<'0'||*s>'9')fail("NUMBER");n=n*10+(*s-'0');if(n>UINT32_MAX)fail("NUMBER");}
    return (unsigned)n;
}
static uint32_t word(const char *s) {
    uint32_t u=0;if(strlen(s)!=8)fail("WORD");
    for(int i=0;i<8;i++) {char c=s[i];if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))fail("WORD");u=(u<<4)+(c<='9'?c-'0':c-'a'+10);}
    return u;
}
static b2Vec2 vec(const uint32_t *w) {return (b2Vec2){value(w[0]),value(w[1])};}
static b2Sweep sweep(const uint32_t *w) {
    return (b2Sweep){.localCenter=vec(w),.c1=vec(w+2),.c2=vec(w+4),.q1={value(w[6]),value(w[7])},.q2={value(w[8]),value(w[9])}};
}
static b2ShapeProxy proxy(const uint32_t *w) {
    b2ShapeProxy p={0};p.count=(int)w[0];p.radius=value(w[1]);
    for(int i=0;i<8;i++)p.points[i]=vec(w+2+2*i);return p;
}
static b2TOIInput toi_input(const uint32_t *w) {
    return (b2TOIInput){.proxyA=proxy(w+1),.proxyB=proxy(w+19),.sweepA=sweep(w+37),.sweepB=sweep(w+47),.maxFraction=value(w[57])};
}
static bool finite_vec(b2Vec2 v) {return b2IsValidFloat(v.x)&&b2IsValidFloat(v.y);}
static bool valid_sweep(const b2Sweep *s) {
    return finite_vec(s->localCenter)&&finite_vec(s->c1)&&finite_vec(s->c2)&&
           b2IsValidRotation(s->q1)&&b2IsNormalizedRot(s->q1)&&b2IsValidRotation(s->q2)&&b2IsNormalizedRot(s->q2);
}
static bool valid_radius(float r) {return b2IsValidFloat(r)&&r>=0.0f;}
static bool valid_count(int n) {return n>=1&&n<=8;}
static bool valid_points(const b2ShapeProxy *p) {
    for(int i=0;i<8;i++)if(i<p->count&&!finite_vec(p->points[i]))return false;return true;
}
typedef struct Check {unsigned status,reason;} Check;
                                                                              
                                                                              
static Check preflight_sweep(const b2Sweep *s,float t) {
    if(!(t>=0.0f&&t<=1.0f))return (Check){5,16};
    if(!valid_sweep(s))return (Check){5,16};return (Check){0,0};
}
static Check preflight_toi(const b2TOIInput *t) {
    if(!(t->maxFraction>=0.0f&&t->maxFraction<=1.0f))return (Check){5,16};
    if(!valid_radius(t->proxyA.radius)||!valid_radius(t->proxyB.radius))return (Check){5,16};
    if(!valid_sweep(&t->sweepA)||!valid_sweep(&t->sweepB))return (Check){5,16};
    if(!valid_count(t->proxyA.count)||!valid_count(t->proxyB.count))return (Check){4,0};
    if(!valid_points(&t->proxyA)||!valid_points(&t->proxyB))return (Check){4,0};return (Check){0,0};
}
static b2Transform checked_sweep(const b2Sweep *s,float t,Check *c) {
    *c=preflight_sweep(s,t);return c->status?(b2Transform){0}:b2GetSweepTransform(s,t);
}
static b2TOIOutput checked_toi(const b2TOIInput *t,Check *c) {
    *c=preflight_toi(t);return c->status?(b2TOIOutput){0}:b2TimeOfImpact(t);
}
static void proxy_format(const uint32_t *w) {
    if(w[0]>10)fail("POPULATION");
    for(unsigned i=0;i<8;i++)if(i>=w[0]&&(w[2+2*i]!=0||w[3+2*i]!=0))fail("UNUSED");
}
static void validate(unsigned op,const uint32_t *w,bool helper) {
    if(helper)return;
    if(w[0]>1||(op>=306&&w[0]!=0))fail("MODE");
    if(op==300) {
        b2Sweep s=sweep(w+1);if(!w[0]&&preflight_sweep(&s,value(w[11])).status)fail("DOMAIN");return;
    }
    if(op==307&&w[1]>2)fail("ENUM");
    unsigned pa=op==307?6:1,pb=pa+18,sa=op==307?42:37,sb=sa+10;
    if(op==306) {
        if(w[57]<1||w[57]>2)fail("CACHE");
        for(unsigned i=0;i<3;i++) {
            if(w[58+i]>255||w[61+i]>255)fail("CACHE");
            if(i<w[57]&&(w[58+i]>=w[pa]||w[61+i]>=w[pb]))fail("CACHE");
            if(i>=w[57]&&(w[58+i]||w[61+i]))fail("UNUSED");
        }
    }
    proxy_format(w+pa);proxy_format(w+pb);
    if(w[0]==0) {
        b2ShapeProxy a=proxy(w+pa),b=proxy(w+pb);b2Sweep a_s=sweep(w+sa),b_s=sweep(w+sb);
        if(!valid_count(a.count)||!valid_count(b.count)||!valid_radius(a.radius)||!valid_radius(b.radius)||
           !valid_points(&a)||!valid_points(&b)||!valid_sweep(&a_s)||!valid_sweep(&b_s))fail("DOMAIN");
        unsigned ti=op==301?57:op==306?64:62;
        if(!(value(w[ti])>=0.0f&&value(w[ti])<=1.0f))fail("DOMAIN");
        if(op==306&&!(value(w[65])>=0.0f&&value(w[65])<=1.0f))fail("DOMAIN");
        if(op==307)for(int i=2;i<6;i++)if(!b2IsValidFloat(value(w[i])))fail("DOMAIN");
    }
}
static void record(const char *tag,unsigned phase,unsigned n,const uint32_t *w) {
    printf("%s %u %u %u %u",tag,case_id,sequence,phase,n);for(unsigned i=0;i<n;i++)hex(w[i]);puts("");
}
                                                                                    
static void pack_proxy(uint32_t *w,const b2ShapeProxy *p) {
    w[0]=p->count;w[1]=ccd_bits(p->radius);for(int i=0;i<8;i++){w[2+2*i]=ccd_bits(p->points[i].x);w[3+2*i]=ccd_bits(p->points[i].y);}
}
static void pack_sweep(uint32_t *w,const b2Sweep *s) {
    float a[]={s->localCenter.x,s->localCenter.y,s->c1.x,s->c1.y,s->c2.x,s->c2.y,s->q1.c,s->q1.s,s->q2.c,s->q2.s};
    for(int i=0;i<10;i++)w[i]=ccd_bits(a[i]);
}
static void pack_input(uint32_t *w,const b2TOIInput *t) {
    pack_proxy(w,&t->proxyA);pack_proxy(w+18,&t->proxyB);pack_sweep(w+36,&t->sweepA);pack_sweep(w+46,&t->sweepB);w[56]=ccd_bits(t->maxFraction);
}
static void mutate_input(b2TOIInput *t,unsigned wi) {
    uint32_t w[58]={0};pack_input(w+1,t);w[wi]^=1;*t=toi_input(w);
}
static void v_input(unsigned phase,const b2TOIInput *t) {uint32_t w[57];pack_input(w,t);record("V16",phase,57,w);}
static void v_result(unsigned phase,b2TOIOutput t) {uint32_t w[]={(uint32_t)t.state,ccd_bits(t.fraction)};record("V16",phase,2,w);}
static void execute(unsigned op,unsigned n,const uint32_t *w,b2TOIInput *saved,b2TOIOutput *saved_result,bool *have_saved) {
    record("E16",op,n,w);ordinal=0;observing=true;Check c={0};uint32_t result[9]={0};unsigned rn=0;
    if(op==300) {
        b2Sweep s=sweep(w+1);b2Transform t=w[0]?checked_sweep(&s,value(w[11]),&c):b2GetSweepTransform(&s,value(w[11]));
        result[0]=ccd_bits(t.p.x);result[1]=ccd_bits(t.p.y);result[2]=ccd_bits(t.q.c);result[3]=ccd_bits(t.q.s);rn=4;
    } else if(op==301) {
        b2TOIInput t=toi_input(w);b2TOIOutput r=w[0]?checked_toi(&t,&c):b2TimeOfImpact(&t);
        result[0]=r.state;result[1]=ccd_bits(r.fraction);rn=2;
        printf("R16 %u %u %u %u %u %u",case_id,sequence,op,c.status,c.reason,rn);for(unsigned i=0;i<rn;i++)hex(result[i]);puts("");
        observing=false;
        if(case_id>=113) {
            b2TOIInput copy=t;v_input(0,&t);mutate_input(&copy,ccd_mut_in[case_id-1]);v_input(1,&copy);v_input(2,&t);
            b2TOIOutput other=r;v_result(3,r);
            if(ccd_mut_out[case_id-1]==0)other.state=(b2TOIState)((uint32_t)other.state^1);else other.fraction=value(ccd_bits(other.fraction)^1);
            v_result(4,other);v_result(5,r);
            if(*have_saved){v_input(6,saved);v_result(7,*saved_result);}else{*saved=t;*saved_result=r;*have_saved=true;}
        }
        return;
    } else {
        unsigned p=op==306?1:6,s=op==306?37:42;b2ShapeProxy a=proxy(w+p),b=proxy(w+p+18);b2Sweep sa=sweep(w+s),sb=sweep(w+s+10);
        b2SeparationFunction f;
        if(op==306) {
            b2SimplexCache cache={0};cache.count=w[57];for(int i=0;i<3;i++){cache.indexA[i]=w[58+i];cache.indexB[i]=w[61+i];}
            f=b2MakeSeparationFunction(&cache,&a,&sa,&b,&sb,value(w[64]));
        } else f=(b2SeparationFunction){.proxyA=&a,.proxyB=&b,.sweepA=sa,.sweepB=sb,.localPoint=vec(w+4),.axis=vec(w+2),.type=w[1]};
        int ia,ib;float time=value(w[op==306?65:62]);float min=b2FindMinSeparation(&f,&ia,&ib,time);float eval=b2EvaluateSeparation(&f,ia,ib,time);
        result[0]=f.type;result[1]=ccd_bits(f.axis.x);result[2]=ccd_bits(f.axis.y);result[3]=ccd_bits(f.localPoint.x);result[4]=ccd_bits(f.localPoint.y);
        result[5]=(uint32_t)ia;result[6]=(uint32_t)ib;result[7]=ccd_bits(min);result[8]=ccd_bits(eval);rn=9;
    }
    observing=false;printf("R16 %u %u %u %u %u %u",case_id,sequence,op,c.status,c.reason,rn);for(unsigned i=0;i<rn;i++)hex(result[i]);puts("");
}
static unsigned arity(unsigned opcode) {switch(opcode){case 300:return 12;case 301:return 58;case 306:return 66;case 307:return 63;default:fail("OPCODE");return 0;}}
int main(int argc,char **argv) {
    input=stdin;
    for(int i=1;i<argc;i++) {
        if(strcmp(argv[i],"--diagnostic")==0)diagnostic=true;
        else {input=fopen(argv[i],"rb");if(!input)fail("HEADER");}
    }
    if(!line(true)||nt!=4)fail("HEADER");
    if(strcmp(tokens[0],"PORT16"))fail("TAG");if(strcmp(tokens[1],"A"))fail("PART");
    guard_profile=!strcmp(tokens[2],"GUARD");if(!guard_profile&&strcmp(tokens[2],"DIRECT"))fail("PROFILE");
    unsigned total=decimal(tokens[3]),full=guard_profile?262:128;
    if(total<1||total>full||(!diagnostic&&total!=full))fail("N");
    unsigned previous=0;
    for(unsigned ci=1;ci<=total;ci++) {
        need();if(strcmp(tokens[0],"C"))fail("CASE");if(nt!=3)fail("ARITY");
        case_id=decimal(tokens[1]);unsigned count=decimal(tokens[2]);
        if(case_id<=previous||case_id>full||(!diagnostic&&case_id!=ci))fail("ID");previous=case_id;
        if(count!=(guard_profile?0:ccd_counts[case_id-1]))fail("COUNT");
        printf("CASE %u %u\n",case_id,count);
        b2TOIInput saved={0};b2TOIOutput saved_result={0};bool have_saved=false;
        for(unsigned oi=1;oi<=(guard_profile?2:count);oi++) {
            need();if(strcmp(tokens[0],guard_profile?"G":"O"))fail(guard_profile?"GUARD":"OPCODE");
            int shift=guard_profile?1:0;if(nt<4+shift)fail("ARITY");
            unsigned a=decimal(tokens[1]),b=guard_profile?decimal(tokens[2]):0;
            unsigned op=decimal(tokens[2+shift]),n=decimal(tokens[3+shift]);
            if(guard_profile&&(a!=case_id||b!=case_id))fail("GUARD");
            if(!guard_profile&&a!=oi)fail("SEQ");
            if(guard_profile&&op!=300&&op!=301)fail("GUARD");
            if(n!=arity(op)||nt!=(int)(4+shift+n))fail("ARITY");
            uint32_t w[66];for(unsigned j=0;j<n;j++)w[j]=word(tokens[4+shift+j]);
            validate(op,w,guard_profile);sequence=oi;
            if(guard_profile) {
                printf("G16 %u %u %u",case_id,case_id,n);for(unsigned j=0;j<n;j++)hex(w[j]);puts("");
                Check c;if(op==300){b2Sweep s=sweep(w+1);c=preflight_sweep(&s,value(w[11]));}else{b2TOIInput t=toi_input(w);c=preflight_toi(&t);}
                printf("GA16 %u %u %u %u %u\n",case_id,case_id,c.status==0,c.status,c.reason);
            } else execute(op,n,w,&saved,&saved_result,&have_saved);
        }
        printf("ENDCASE %u\n",case_id);
    }
    if(line(false))fail("TRAILING_DATA");printf("END %u\n",total);
    if(input!=stdin)fclose(input);return 0;
}
