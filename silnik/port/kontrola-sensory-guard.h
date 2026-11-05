                                                                        
                                                                            
   
#include "sensory-guard-schema.inc"
typedef struct Gate17 {int status,reason;} Gate17;
static Gate17 gate17(const uint32_t* c,const uint32_t* p,unsigned route,int length)
{
    Gate17 ok={0},stale={STALE,0},param={PARAM,0},geometry={GEOMETRY,0};
    if((int32_t)c[0]<0||c[0]>=c[3]||!c[4]||c[1]!=c[5]||c[2]!=c[6])return stale;
    bool target=route<=5||route>=9&&route<=14;
    if(target){
        if(c[10]!=c[1]||c[11]!=c[2])return (Gate17){FOREIGN,0};
        if((int32_t)c[7]<0||c[7]>=c[12]||(int32_t)c[13]<0||(int32_t)c[14]<0||c[8]!=c[15]||c[9]!=c[16])return stale;
    }
    if(route!=10&&route!=11&&c[17])return (Gate17){7,1};
    if(route>=12&&route<=14&&(int32_t)c[18]<0)return (Gate17){PARAM,21};
    if(route<=8){
        const uint32_t* a=p+(route>=6?57:0);
        if(route>=6){Operation body={0};memcpy(body.u,p,57*4);for(int i=0;i<57;i++)body.f[i]=from_bits(p[i]);b2BodyDef d=body11(&body);if(!isfinite(d.sleepThreshold)||d.sleepThreshold<0)return param;if((int)d.type<0||d.type>2||!valid_body11(&d))return geometry;}
        b2ShapeDef d=shapeDef17(a);if(!valid_material_definition9(d))return param;
        if(!isfinite(d.density)||d.density<0)return geometry;
        if(a[3]==4&&!b2IsNormalizedRot((b2Rot){from_bits(a[8]),from_bits(a[9])}))return geometry;
        Geometry g;
        if(!geometry12(a[3],a+4,&g)||!valid_mass_geometry12(&g))return geometry;
        if(length>(route>=6?120:63))for(int i=route>=6?120:63;i<length;i++)if(!isfinite(from_bits(p[i])))return geometry;
        b2MassData mass=geo_mass(&g,d.density);if(!isfinite(mass.mass)||!finite_vec(mass.center)||!isfinite(mass.rotationalInertia))return geometry;
        if(a[59]&&c[20])return (Gate17){PARAM,20};
        uint64_t last=(uint64_t)c[22]|((uint64_t)c[23]<<32);unsigned required=route>=6?2:1;
        if(!c[24]||last>UINT64_MAX-required)return (Gate17){LIMIT,0};
    }else if(route==17||route==18){float dt=from_bits(c[21]);if(!isfinite(dt)||dt<0||(int32_t)p[2]<=0)return param;if(dt>0&&c[19]&&c[20])return (Gate17){PARAM,20};}
    else if(route>=12&&route<=15&&c[19]&&c[20])return (Gate17){PARAM,20};
    else if(route==16&&c[31]&&c[19])return (Gate17){PARAM,20};
    return ok;
}

#include "kontrola-sensory-fixture.h"
static void guard17(FILE* input,unsigned n)
{
    printf("PORT17 GUARD %u\n",n);unsigned prior=0;
    for(unsigned item=0;item<n;item++){
        char* line=row(input);arity13(line,3,"INPUT_ARITY");if(strncmp(line,"C ",2))fail("INPUT_TAG");char* p=line+2;
        unsigned id=decimal13(&p);space(&p);unsigned m=decimal13(&p);
        if(id<=prior||id>697||!diagnostic17&&id!=item+1)fail("INPUT_ID");prior=id;if(m)fail("INPUT_OPCOUNT");
        reset17(id);printf("CASE %u 0\n",id);
        for(unsigned phase=0;phase<2;phase++){
            line=row(input);p=line;if(strncmp(p,"G ",2))fail("INPUT_TAG");p+=2;
            unsigned actual=decimal13(&p);space(&p);unsigned guard=decimal13(&p);space(&p);unsigned ph=decimal13(&p);space(&p);unsigned route=decimal13(&p);space(&p);unsigned count=decimal13(&p);
            if(actual!=id)fail("INPUT_ID");if(guard!=id)fail("INPUT_GUARD");if(ph!=phase)fail("INPUT_PHASE");if(route>21||route!=guardSchema17[id-1][0])fail("INPUT_FIXTURE");
            if(count!=guardSchema17[id-1][1+phase])fail("INPUT_ARITY");arity13(line,6+count,"INPUT_ARITY");uint32_t words[256];if(count>256)fail("INPUT_ARITY");
            for(unsigned j=0;j<count;j++){space(&p);words[j]=hex_word(&p);}if(*p)fail("INPUT_ARITY");
            for(int j=38;j<64;j++)if(words[j])fail("INPUT_UNUSED");
            if(guardSchema17[id-1][3]){
                Gate17 result=gate17(words,words+64,route,count-64);
                printf("G17 %u %u %d %d %d 0\n",id,phase,result.status,result.reason,result.status==0);
            }else state17(id,phase,route,words,words+64,count-64);
        }
        printf("ENDCASE %u\n",id);for(int w=0;w<16;w++)if(worlds[w].live)destroy_world(w);
    }
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");printf("END %u\n",n);
}
