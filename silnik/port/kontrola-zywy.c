                                                               
                                                                             
                                                                            
#include "box2d/box2d.h"
#include "world.h"
static int port12Prepare(b2World*,b2ShapeId*,b2ShapeId*,bool);
static int profile12=8;
struct Geometry;
static bool valid_mass_geometry12(const struct Geometry*);
static bool badMassGeometry12;
#include "zywy-sen11.inc"
#include "zywy-preflight.inc"

static uint32_t counts12[11],private12;
static int status12,reason12,vectorKind12=-1,vectorBody12;
static b2Vec2 vector12;
static Geometry preparedGeometry12;
static bool hasPreparedGeometry12,helperOnly12;
static void arity12(const char* text,int expected)
{
    int count=1;for(const char* p=text;*p;++p)count+=*p==' ';
    if(count!=expected)fail(rowEof11?"INPUT_EOF":physical12);
}
static uint32_t decimal12(char** cursor,const char* error,const char* overflow)
{
    char* p=*cursor;if(*p<'0'||*p>'9'||(*p=='0'&&p[1]>='0'&&p[1]<='9'))fail(error);
    uint64_t value=0;
    do{value=10*value+(uint32_t)(*p++-'0');if(value>UINT32_MAX)fail(overflow);}while(*p>='0'&&*p<='9');
    *cursor=p;return (uint32_t)value;
}

static void prefix12(const char* tag,int a,int b,int n)
{
    printf("%s %d %"PRIu32,tag,case9,seq9);
    if(n>0)printf(" %d",a);if(n>1)printf(" %d",b);
}
static bool utf8_12(const uint32_t* bytes,uint32_t n)
{
    if(n>31)return false;
    for(uint32_t i=0;i<n;){uint32_t c=bytes[i++],value=0,need=0,minimum=0;
        if(c==0)return false;if(c<128)continue;
        if(c>=194&&c<=223){value=c&31;need=1;minimum=128;}
        else if(c>=224&&c<=239){value=c&15;need=2;minimum=2048;}
        else if(c>=240&&c<=244){value=c&7;need=3;minimum=65536;}
        else return false;
        if(i+need>n)return false;
        while(need--){c=bytes[i++];if(c<128||c>191)return false;value=(value<<6)|(c&63);}
        if(value<minimum||value>0x10ffff||(value>=0xd800&&value<=0xdfff))return false;
    }return true;
}
static bool geometry12(int tag,const uint32_t* words,Geometry* result)
{
    int used=tag==0?3:tag==1?5:tag==2?4:words[0]<=8?2+2*(int)words[0]:40;
    for(int j=tag==3?1:0;j<used;++j)if(!isfinite(from_bits(words[j])))return false;
    if(!prepare((uint32_t)tag,words,result))return false;
    if(tag==1){result->type=1;result->capsule=(b2Capsule){{from_bits(words[0]),from_bits(words[1])},
        {from_bits(words[2]),from_bits(words[3])},from_bits(words[4])};
        if(!isfinite(b2DistanceSquared(result->capsule.center1,result->capsule.center2)))return false;}
    return true;
}
static bool raw_geometry12(int tag,const uint32_t* words,Geometry* result)
{
                                                                          
                                                                  
    if(tag>=3)return geometry12(tag,words,result);
    int used=tag==0?3:tag==1?5:4;
    for(int j=0;j<used;++j)if(!isfinite(from_bits(words[j])))return false;
    memset(result,0,sizeof(*result));result->type=tag;
    if(tag==0)result->circle=(b2Circle){{from_bits(words[0]),from_bits(words[1])},from_bits(words[2])};
    else if(tag==1)result->capsule=(b2Capsule){{from_bits(words[0]),from_bits(words[1])},{from_bits(words[2]),from_bits(words[3])},from_bits(words[4])};
    else result->segment=(b2Segment){{from_bits(words[0]),from_bits(words[1])},{from_bits(words[2]),from_bits(words[3])}};
    return true;
}
static bool valid_mass_geometry12(const Geometry* g)
{
    if(g->type==0)return finite_vec(g->circle.center)&&isfinite(g->circle.radius)&&g->circle.radius>0;
    if(g->type==1)return finite_vec(g->capsule.center1)&&finite_vec(g->capsule.center2)&&isfinite(g->capsule.radius)&&g->capsule.radius>0&&isfinite(b2DistanceSquared(g->capsule.center1,g->capsule.center2));
    if(g->type==2){float n=b2DistanceSquared(g->segment.point1,g->segment.point2);return finite_vec(g->segment.point1)&&finite_vec(g->segment.point2)&&isfinite(n)&&n>.005f*.005f;}
    if(g->type!=3||g->polygon.count<3||g->polygon.count>8||!isfinite(g->polygon.radius)||g->polygon.radius<0||!finite_vec(g->polygon.centroid))return false;
    for(int j=0;j<g->polygon.count;++j)if(!finite_vec(g->polygon.vertices[j])||!finite_vec(g->polygon.normals[j]))return false;
    return true;
}
static bool body_values12(const Operation* o)
{
    int kind=o->u[3];bool game=o->u[2]!=0;
    if(kind==2)return isfinite(o->f[4])&&o->f[4]>=0&&finite_vec((b2Vec2){o->f[5],o->f[6]})&&isfinite(o->f[7])&&o->f[7]>=0;
    if(kind>=4&&kind<=6)return isfinite(o->f[4])&&(kind==6||o->f[4]>=0);
    if(kind==8)return finite_vec((b2Vec2){o->f[4],o->f[5]})&&isfinite(o->f[6])&&isfinite(o->f[7])&&
        b2IsNormalizedRot((b2Rot){o->f[6],o->f[7]})&&isfinite(o->f[8])&&(!game||o->f[8]>0);
    return true;
}
static bool shape_values12(const Operation* o)
{
    int kind=o->u[3];if(kind<=1)return isfinite(o->f[4])&&o->f[4]>=0;
    if(kind==3)for(int j=4;j<=7;++j)if(!isfinite(o->f[j])||(j!=7&&o->f[j]<0))return false;
    return true;
}
static int body_mut12(const Operation* o)
{
    const uint32_t* a=o->u;int owner=a[0],reg=a[1],kind=a[3];bool game=a[2]!=0;
    int status=guard(worlds+owner,bodies+reg);if(status)return status;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);if(game&&w->locked){reason12=1;return 7;}
    b2BodyId id=bodies[reg].raw;
    if(kind==0&&b2Body_GetType(id)==(b2BodyType)a[4])return OK;
    if(kind==1&&b2Body_IsEnabled(id)==(a[4]!=0))return OK;
    if(kind==7&&b2Body_IsFixedRotation(id)==(a[4]!=0))return OK;
    bool valid=body_values12(o);
    if(!valid){if(!game)fail("INPUT_DOMAIN");return PARAM;}
    if(game&&(kind==0||kind==3||kind==7)){
        if(!preflight12(id,NULL,NULL,0,b2_nullShapeId,false,0,
            kind==0?(int)a[4]:-1,kind==7?(int)a[4]:-1,NULL)){reason12=badMassGeometry12?0:5;return GEOMETRY;}}
    if(game&&kind==2){float im=o->f[4]>0?1.0f/o->f[4]:0,ii=o->f[7]>0?1.0f/o->f[7]:0;
        if(!isfinite(im)||!isfinite(ii)||!finite_vec(b2TransformPoint(b2Body_GetTransform(id),(b2Vec2){o->f[5],o->f[6]}))){reason12=5;return GEOMETRY;}}
    if(game&&kind==8){b2Body* b=w->bodies.data+id.index1-1;b2BodySim* s=b2GetBodySim(w,b);
        b2Vec2 center=b2TransformPoint((b2Transform){{o->f[4],o->f[5]},{o->f[6],o->f[7]}},s->localCenter);
        float inv=1.0f/o->f[8];b2Vec2 velocity=b2MulSV(inv,b2Sub(center,s->center));
        float angular=b->fixedRotation?0:inv*b2RelativeAngle((b2Rot){o->f[6],o->f[7]},s->transform.q);
        float maximum=b2Length(velocity)+b2AbsFloat(angular)*s->maxExtent;
        if(!isfinite(inv)||!finite_vec(velocity)||!isfinite(angular)||!isfinite(maximum))return PARAM;}
    if(helperOnly12)return OK;
    switch(kind){
        case 0:b2Body_SetType(id,(b2BodyType)a[4]);break;
        case 1:if(a[4])b2Body_Enable(id);else b2Body_Disable(id);break;
        case 2:b2Body_SetMassData(id,(b2MassData){o->f[4],{o->f[5],o->f[6]},o->f[7]});break;
        case 3:b2Body_ApplyMassFromShapes(id);break;
        case 4:b2Body_SetLinearDamping(id,o->f[4]);break;
        case 5:b2Body_SetAngularDamping(id,o->f[4]);break;
        case 6:b2Body_SetGravityScale(id,o->f[4]);break;
        case 7:b2Body_SetFixedRotation(id,a[4]!=0);break;
        case 8:b2Body_SetTargetTransform(id,(b2Transform){{o->f[4],o->f[5]},{o->f[6],o->f[7]}},o->f[8]);break;
    }return OK;
}
static int shape_mut12(const Operation* o)
{
    const uint32_t* a=o->u;int owner=a[0],reg=a[1],kind=a[3];bool game=a[2]!=0;
    int status=shape_guard(worlds+owner,shapes+reg);if(status)return status;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);if(game&&w->locked){reason12=1;return 7;}
    b2ShapeId id=shapes[reg].raw;b2BodyId parent=b2Shape_GetBody(id);bool valid=shape_values12(o);
    if(!valid){if(!game)fail("INPUT_DOMAIN");return PARAM;}
    Geometry geometry;
    if(kind>=5){bool good=hasPreparedGeometry12?(geometry=preparedGeometry12,true):(game?geometry12(kind-5,a+4,&geometry):raw_geometry12(kind-5,a+4,&geometry));
        if(!good){if(!game)fail("INPUT_DOMAIN");return GEOMETRY;}
        if(game&&!preflight12(parent,NULL,NULL,0,id,false,b2Shape_GetDensity(id),-1,-1,&geometry)){reason12=badMassGeometry12?0:5;return GEOMETRY;}}
    if(helperOnly12)return OK;
    switch(kind){
        case 0:b2Shape_SetFriction(id,o->f[4]);break;
        case 1:b2Shape_SetRestitution(id,o->f[4]);break;
        case 2:b2Shape_SetMaterial(id,(int32_t)a[4]);break;
        case 3:b2Shape_SetSurfaceMaterial(id,(b2SurfaceMaterial){o->f[4],o->f[5],o->f[6],o->f[7],(int32_t)a[8],a[9]});break;
        case 4:b2Shape_SetFilter(id,(b2Filter){(uint64_t)a[4]|(uint64_t)a[5]<<32,(uint64_t)a[6]|(uint64_t)a[7]<<32,(int32_t)a[8]});break;
        case 5:b2Shape_SetCircle(id,&geometry.circle);break;
        case 6:b2Shape_SetCapsule(id,&geometry.capsule);break;
        case 7:b2Shape_SetSegment(id,&geometry.segment);break;
        case 8:b2Shape_SetPolygon(id,&geometry.polygon);break;
    }
    if(game&&kind>=5)b2Body_ApplyMassFromShapes(parent);
    return OK;
}
static int create12(const Operation* o)
{
    const uint32_t* a=o->u;int owner=a[0],target=a[1];bool game=a[2]!=0;
    if(!world_live(worlds+owner))return STALE;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);if(game&&w->locked){reason12=1;return 7;}
    b2BodyDef d=body11(o);d.isEnabled=a[19]!=0;
    if(!valid_body8(&d)||!isfinite(d.sleepThreshold)||d.sleepThreshold<0){if(!game)fail("INPUT_DOMAIN");return PARAM;}
    if(game&&!utf8_12(a+21,a[20])){reason12=3;return PARAM;}
    if(helperOnly12)return OK;
    char name[33]={0};for(uint32_t j=0;j<a[20];++j)name[j]=(char)a[21+j];d.name=name;
    d.userData=token(a[53],a[54],a[55]);return create_body(target,owner,d);
}
static int vector_get12(const Operation* o)
{
    const uint32_t* a=o->u;vectorKind12=(int)a[3];vectorBody12=(int)a[1];
    int status=guard(worlds+a[0],bodies+a[1]);if(status)return status;
    b2Vec2 v={o->f[4],o->f[5]};if(!finite_vec(v)){if(!a[2])fail("INPUT_DOMAIN");return PARAM;}
    if(helperOnly12)return OK;
    b2BodyId id=bodies[a[1]].raw;
    switch(a[3]){case 0:vector12=b2Body_GetLocalPoint(id,v);break;case 1:vector12=b2Body_GetWorldPoint(id,v);break;
        case 2:vector12=b2Body_GetLocalVector(id,v);break;case 3:vector12=b2Body_GetWorldVector(id,v);break;
        case 4:vector12=b2Body_GetLocalPointVelocity(id,v);break;case 5:vector12=b2Body_GetWorldPointVelocity(id,v);break;}
    return OK;
}
static int locked_call12(void);
#include "kontrola-zywy-haki.h"
static Operation lockOperation12;
static int locked_call12(void)
{
    const Operation* o=&lockOperation12;int kind=0,reg=0;
    if(o->code==80)return body_mut12(o);
    if(o->code==81)return shape_mut12(o);
    if(o->code==90)return create12(o);
    if(o->code>=82&&o->code<=87)return extended12(o,&kind,&reg);
                                                                            
                                                                              
    return mutation_world12(hookOwner12);
}
static void execute12(const Operation* o)
{
    hookOwner12=(int)o->u[0];
    if(o->code<80){execute11(o);sync_hooks12();return;}
    reset_extra10();int owner=o->u[0],reg=o->u[1],kind=o->code==81?2:1;
    if(o->code==80)status12=body_mut12(o);
    else if(o->code==81)status12=shape_mut12(o);
    else if(o->code==90)status12=create12(o);
    else if(o->code==92)status12=vector_get12(o);
    else if(o->code>=82&&o->code<=89)status12=extended12(o,&kind,&reg);
    else if(o->code==91){int target=o->u[1];reg=target?(int)o->u[2]:owner;kind=target;
        status12=target==0?(world_live(worlds+owner)?OK:STALE):target==1?guard(worlds+owner,bodies+reg):shape_guard(worlds+owner,shapes+reg);}
    else fail("INPUT_OPCODE");
    population_after9();echo(case9,seq9,o);
    if(o->code==90)result(case9,seq9,0,status12,status12?0:2,reg);
    dump(case9,seq9,o->code==90,0,0,-1);
    prefix12("AP12",0,0,0);word(status12);word(reason12);word(kind);word(reg);putchar('\n');++counts12[0];
}
static void observe12(void)
{
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2WorldId id=worlds[owner].raw;b2World* w=b2GetWorldFromId(id);
        prefix12("WS12",owner,0,1);vec(b2World_GetGravity(id));real(b2World_GetMaximumLinearSpeed(id));
        real(OBS?w->contactHertz:0);real(OBS?w->contactDampingRatio:0);real(OBS?w->maxContactPushSpeed:0);
        real(b2World_GetRestitutionThreshold(id));real(b2World_GetHitEventThreshold(id));word(w->enableWarmStarting);
        word(b2World_IsSleepingEnabled(id));word(b2World_GetAwakeBodyCount(id));putchar('\n');++counts12[1];
    }
    for(int reg=0;reg<BODIES;++reg)if(bodies[reg].live){const char* name=b2Body_GetName(bodies[reg].raw);int n=0;
        if(name)while(n<32&&name[n])++n;
        prefix12("NM12",reg,0,1);word(n);for(int j=0;j<32;++j)word(j<n?(unsigned char)name[j]:0);putchar('\n');++counts12[2];}
    for(int kind=0;kind<3;++kind){int end=kind==0?WORLDS:kind==1?BODIES:SHAPES;
        for(int reg=0;reg<end;++reg){bool live=kind==0?worlds[reg].live:kind==1?bodies[reg].live:shapes[reg].live;if(!live)continue;
            prefix12("UD12",kind,reg,2);object(kind==0?b2World_GetUserData(worlds[reg].raw):kind==1?b2Body_GetUserData(bodies[reg].raw):b2Shape_GetUserData(shapes[reg].raw));putchar('\n');++counts12[3];}}
    for(int reg=0;reg<SHAPES;++reg)if(shapes[reg].live){b2ShapeId id=shapes[reg].raw;prefix12("EF12",reg,0,1);
        word(b2Shape_AreContactEventsEnabled(id));word(b2Shape_AreHitEventsEnabled(id));word(b2Shape_ArePreSolveEventsEnabled(id));putchar('\n');++counts12[10];}
    observe_hooks12();
    if(vectorKind12>=0){prefix12("VR12",vectorBody12,vectorKind12,2);word(status12);vec(status12?b2Vec2_zero:vector12);putchar('\n');++counts12[9];}
    if(OBS)for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){b2World* w=b2GetWorldFromId(worlds[owner].raw);
        for(int slot=0;slot<w->bodyIdPool.nextIndex;++slot){b2Body* b=w->bodies.data+slot;if(b->id!=slot)continue;
            prefix12("NP12",owner,slot,2);for(int j=0;j<32;++j)word((unsigned char)b->name[j]);putchar('\n');++private12;}}
}
static void run_rows12(FILE*,int,uint32_t);
static void trailing12(FILE* input){if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input))fail("INPUT_DOMAIN");}
static int math12(FILE* input,uint32_t count)
{
    profile12=10;profile11=7;
    printf("COMPONENT12 %"PRIu32"\n",count);
    for(uint32_t id=1;id<=count;++id){int first=fgetc(input);if(first!=EOF)ungetc(first,input);physical12=first=='C'?"INPUT_SEQUENCE":"INPUT_WORDS";char* p=row(input);
        if(!strncmp(p,"C ",2)){arity12(p,3);p+=2;uint32_t actual=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");space(&p);uint32_t ops=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");
            if(*p||actual!=id||ops<1||ops>64)fail("INPUT_SEQUENCE");
            run_rows12(input,id,ops);if(phase9)fail("INPUT_PHASE");if(id==count)trailing12(input);
            printf("ENDCASE %"PRIu32"\n",id);for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);continue;}
        if(strncmp(p,"F ",2))fail("INPUT_WORDS");arity12(p,67);p+=2;
        uint32_t actual=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");space(&p);uint32_t kind=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");if(actual!=id)fail("INPUT_SEQUENCE");
        if(kind!=100&&kind!=101)fail("INPUT_OPCODE");uint32_t a[64];float f[4]={0};
        for(int j=0;j<64;++j){space(&p);a[j]=hex_word(&p);if(j<4)f[j]=from_bits(a[j]);}if(*p)fail("INPUT_WORDS");
        int used=kind==100?2:4;for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
        for(int j=0;j<used;++j)if(!isfinite(f[j]))fail("INPUT_DOMAIN");
        if(kind==101&&(!b2IsNormalizedRot((b2Rot){f[0],f[1]})||!b2IsNormalizedRot((b2Rot){f[2],f[3]})))fail("INPUT_DOMAIN");
        printf("CASE %"PRIu32" 1\nFE12 %"PRIu32" %"PRIu32,id,id,kind);for(int j=0;j<64;++j)word(a[j]);putchar('\n');
        float value=kind==100?b2Atan2(f[0],f[1]):b2RelativeAngle((b2Rot){f[0],f[1]},(b2Rot){f[2],f[3]});
        printf("FV12 %"PRIu32" %"PRIu32,id,kind);real(value);putchar('\n');if(id==count)trailing12(input);printf("ENDCASE %"PRIu32"\n",id);
    }
    if(fclose(input))fail("INPUT_DOMAIN");
    printf("END %"PRIu32"\n",count);return ferror(stdout)||fflush(stdout)?2:0;
}
static void validate_new12(Operation* op,bool registers)
{
    Operation o=*op;uint32_t* a=o.u;int code=o.code,used=0;
    int mode=code==82||code==86||code==88?1:code==83||code==85||code==91?3:code==87||code==89?-1:2;
    if(mode>=0&&a[mode]>1)fail("INPUT_MODE");
    if(code==80||code==81){if(a[3]>8)fail("INPUT_OPCODE");
        if(code==80){used=a[3]==2?8:a[3]==3?4:a[3]==8?9:5;
            if(a[3]==0&&a[4]>2)fail("INPUT_DOMAIN");if((a[3]==1||a[3]==7)&&a[4]>1)fail("INPUT_BOOL");}
        else{used=a[3]<3?5:a[3]==3?10:a[3]==4?9:44;
            if(a[3]>=5){int tag=(int)a[3]-5,geom=tag==0?3:tag==1?5:tag==2?4:a[4]<=8?2+2*(int)a[4]:40;
                for(int j=geom;j<40;++j)if(a[4+j])fail("INPUT_UNUSED");}}
    }else if(code==82){if(a[2]>5)fail("INPUT_OPCODE");used=a[2]==3?6:a[2]==5?5:4;if(a[2]==0&&a[3]>1)fail("INPUT_BOOL");}
    else if(code==83){used=6;if(a[1]>1||a[4]>2)fail("INPUT_DOMAIN");if(a[5]>1)fail("INPUT_BOOL");}
    else if(code==84){used=37;if(a[3]>1)fail("INPUT_BOOL");if(a[4]>32)fail("INPUT_DOMAIN");
        for(int j=0;j<32;++j){if(a[5+j]>255)fail("INPUT_WORDS");if((uint32_t)j>=a[4]&&a[5+j])fail("INPUT_UNUSED");}if(a[3]&&a[4])fail("INPUT_UNUSED");}
    else if(code==85){used=7;if(a[1]>2)fail("INPUT_DOMAIN");if(a[4]>1)fail("INPUT_BOOL");if(a[1]==0&&a[2]||!a[4]&&(a[5]||a[6]))fail("INPUT_UNUSED");}
    else if(code==86){used=7;if(a[2]>3)fail("INPUT_OPCODE");if(a[3]>1)fail("INPUT_BOOL");
        if(a[1]&&(a[4]||a[5]||a[6])||a[2]>=2&&(a[5]||a[6]))fail("INPUT_UNUSED");
        if(!a[1]&&(!a[3]&&a[4]||a[2]==0&&a[4]>1||a[2]==1&&a[4]!=0&&a[4]!=1&&a[4]!=2&&a[4]!=4&&a[4]!=5||a[2]>=2&&a[4]!=0&&a[4]!=3))fail("INPUT_DOMAIN");}
    else if(code==87){if(a[1]>3)fail("INPUT_OPCODE");if(a[2]>1)fail("INPUT_DOMAIN");used=!a[2]?3:a[1]==1?12:6;
        if(a[2]&&a[1]<2){if(a[5]>1||a[1]==1&&a[9]>1)fail("INPUT_BOOL");if(a[1]==1&&!a[9]&&(a[10]||a[11]))fail("INPUT_UNUSED");}}
    else if(code==88){used=4;if(a[1]>1)fail("INPUT_MODE");if(a[1]&&a[3])fail("INPUT_UNUSED");}
    else if(code==89){used=4;if(a[0]>3)fail("INPUT_DOMAIN");if(a[0]>=2&&(a[1]||a[2]))fail("INPUT_UNUSED");}
    else if(code==90){used=56;if(a[3]>2)fail("INPUT_DOMAIN");
        for(int j=14;j<=17;++j)if(a[j]>1)fail("INPUT_BOOL");if(a[19]>1||a[53]>1)fail("INPUT_BOOL");if(a[20]>32)fail("INPUT_DOMAIN");
        for(int j=0;j<32;++j){if(a[21+j]>255)fail("INPUT_WORDS");if((uint32_t)j>=a[20]&&a[21+j])fail("INPUT_UNUSED");}if(!a[53]&&(a[54]||a[55]))fail("INPUT_UNUSED");
    }else if(code==91){used=4;if(a[1]>2)fail("INPUT_DOMAIN");if(a[1]==0&&a[2])fail("INPUT_UNUSED");}
    else{used=6;if(a[3]>5)fail("INPUT_OPCODE");}
    for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
    if(code==89){if(a[3]>=4)fail("INPUT_REGISTER");
        if(a[0]<2&&(a[1]>=WORLDS||a[2]>=(a[0]?SHAPES:BODIES)))fail("INPUT_REGISTER");}
    else{
        if(a[0]>=WORLDS)fail("INPUT_REGISTER");
        if((code==80||code==84||code==90||code==92)&&a[1]>=BODIES||code==81&&a[1]>=SHAPES||code==88&&a[2]>=SHAPES)fail("INPUT_REGISTER");
        if(code==83||code==85||code==91){int target=code==83?a[1]+1:a[1];if(target&&a[2]>=(target==1?BODIES:SHAPES))fail("INPUT_REGISTER");}
        if(code==87&&a[2]&&a[1]<2&&(a[3]>=SHAPES||a[4]>=SHAPES))fail("INPUT_REGISTER");
    }
    if(registers){
        int owner=code==89?a[1]:a[0];
        if(code==89){if(a[3]>3)fail("INPUT_REGISTER");if(a[0]>=2){if(!copies12[a[3]].saved)fail("INPUT_COPY");return;}}
        if(owner>=WORLDS||!worlds[owner].saved)fail("INPUT_REGISTER");
        if(code==90){if(a[1]>=BODIES||bodies[a[1]].live)fail("INPUT_REGISTER");}
        else if(code==80||code==84||code==92){if(a[1]>=BODIES||!bodies[a[1]].saved)fail("INPUT_REGISTER");}
        else if(code==81||code==88){int reg=code==88?a[2]:a[1];if(reg>=SHAPES||!shapes[reg].saved)fail("INPUT_REGISTER");}
        else if(code==83||code==85||code==91){int target=code==83?a[1]+1:a[1],reg=a[2];
            if(target==1&&(reg>=BODIES||!bodies[reg].saved))fail("INPUT_REGISTER");if(target==2&&(reg>=SHAPES||!shapes[reg].saved))fail("INPUT_REGISTER");}
        else if(code==87&&a[2]&&a[1]<2){for(int j=3;j<=4;++j)if(a[j]>=SHAPES||!shapes[a[j]].saved)fail("INPUT_REGISTER");}
        else if(code==89){if(a[0]==0&&(a[2]>=BODIES||!bodies[a[2]].saved))fail("INPUT_REGISTER");if(a[0]==1&&(a[2]>=SHAPES||!shapes[a[2]].saved))fail("INPUT_REGISTER");}
    }
    if(code==80&&!a[2]&&!body_values12(&o))fail("INPUT_DOMAIN");
    if(code==81&&!a[2]){if(!shape_values12(&o))fail("INPUT_DOMAIN");if(a[3]>=5){if(!raw_geometry12((int)a[3]-5,a+4,&preparedGeometry12))fail("INPUT_DOMAIN");hasPreparedGeometry12=true;}}
    if(code==82&&!a[1]&&!world_values12(&o))fail("INPUT_DOMAIN");
    if(code==83&&!a[3]&&!a[1]&&a[4]==2)fail("INPUT_PROFILE");
    if(code==88&&!a[1]&&a[3]>512)fail("INPUT_DOMAIN");
    if(code==90&&!a[2]){b2BodyDef d=body11(&o);if(!valid_body8(&d)||!isfinite(d.sleepThreshold)||d.sleepThreshold<0)fail("INPUT_DOMAIN");}
    if(code==92&&!a[2]&&!finite_vec((b2Vec2){o.f[4],o.f[5]}))fail("INPUT_DOMAIN");
}
#include "zywy-used.inc"
static void legacy_source12(const Operation* o)
{
    const uint32_t* a=o->u;int c=o->code,mode=-1;
    if(c==30)mode=15;else if(c==35)mode=4;else if(c==36)mode=3;else if(c==40)mode=58;
    else if(c==54||c==56||c==61)mode=1;else if(c==57||c==58||c==59||c==60||c==62)mode=2;
    if(mode>=0&&a[mode]>1)fail("INPUT_MODE");
    uint64_t flags=0;
#define B12(j) (UINT64_C(1)<<(j))
    if(c==2||c==30)flags=B12(10)|(c==30?B12(14)|B12(15):0);
    else if(c==10||c==17)flags=B12(5)|B12(6)|B12(12);
    else if(c==16)flags=B12(11)|B12(14)|B12(15);
    else if(c==15)flags=B12(3);
    else if(c==11||c==38||c==47||c==48||c==53)flags=B12(2);
    else if(c==12||c==36)flags=B12(3);
    else if(c==33||c==34)flags=B12(7);
    else if(c==35)flags=B12(4);
    else if(c==40)flags=B12(55)|B12(56)|B12(57)|B12(58);
    else if(c==50||c==55)flags=B12(1);
    else if(c==54)flags=B12(10);
    else if(c==56)flags=B12(10)|B12(11);
    else if(c==57)flags=B12(14)|B12(15)|B12(16)|B12(17);
    else if(c==58||c==59)flags=B12(3);
    else if(c==61)flags=B12(2);
    int geometry=-1,tag=-1;
    if(c==10||c==17||c==40){tag=3;geometry=c==40?4:15;}else if(c==16){tag=12;geometry=23;}
    if(tag>=0&&a[tag]>4||(c==2||c==30)&&a[2]>2||c==16&&a[3]>2||c==57&&a[3]>2||c==15&&a[1]!=2&&a[1]!=3||
        (c==33||c==34)&&a[2]>5||c==64&&(a[1]<1||a[1]>3))fail("INPUT_DOMAIN");
    for(int j=0;j<64;++j)if((flags&B12(j))&&a[j]>1)fail("INPUT_BOOL");
    if(c==17&&a[5]!=1)fail("INPUT_BOOL");
    for(int j=used_legacy12[c];j<64;++j)if(a[j])fail("INPUT_UNUSED");
    if(geometry>=0){int kind=a[tag],n=kind==0?3:kind==1?5:kind==2?4:kind==4?6:a[geometry]<=8?2+2*a[geometry]:40;
        for(int j=n;j<40;++j)if(a[geometry+j])fail("INPUT_UNUSED");}
#undef B12
    if(c==37||c==50){if(a[0]>=4)fail("INPUT_REGISTER");if(c==37?!copies[a[0]].saved:!copies9[a[0]].saved)fail("INPUT_REGISTER");return;}
    int owner=(c==2||c==30||c==10||c==17||c==40)?a[1]:c==16?a[2]:a[0];
    if(owner>=WORLDS)fail("INPUT_REGISTER");
    bool makeWorld=c==0||c==54||c==56;
    if(makeWorld){if(worlds[owner].live)fail("INPUT_REGISTER");return;}
    if(!worlds[owner].saved)fail("INPUT_REGISTER");
    if(c==2||c==30||c==57){int reg=c==57?a[1]:a[0];if(reg>=BODIES||bodies[reg].live)fail("INPUT_REGISTER");}
    else if(c==10||c==17||c==40){if(a[0]>=SHAPES||shapes[a[0]].live||a[2]>=BODIES||!bodies[a[2]].saved)fail("INPUT_REGISTER");}
    else if(c==16){if(a[0]>=BODIES||bodies[a[0]].live||a[1]>=SHAPES||shapes[a[1]].live)fail("INPUT_REGISTER");}
    else if(c==15){if(a[1]==2?(a[2]>=BODIES||!bodies[a[2]].saved):(a[2]>=SHAPES||!shapes[a[2]].saved))fail("INPUT_REGISTER");}
    else if(c==46){if(a[1]>=SHAPES||!shapes[a[1]].saved||a[2]>=SHAPES||!shapes[a[2]].saved||a[3]>=256)fail("INPUT_REGISTER");}
    else if(c==47||c==51||c==53){if(a[1]>=256||!saved9[a[1]].saved)fail("INPUT_REGISTER");}
    else if(c==49){if(a[1]>=4)fail("INPUT_REGISTER");}
    else if(c==32){if(a[3]>=4)fail("INPUT_REGISTER");}
    else if(c==11||c==12||c==14||c==18||c==19||c==39||c==52){if(a[1]>=SHAPES||!shapes[a[1]].saved)fail("INPUT_REGISTER");}
    else if(c==3||c==4||c==5||c==13||c==21||c>=33&&c<=36||c==38||c==48||c>=58&&c<=60||c==62){if(a[1]>=BODIES||!bodies[a[1]].saved)fail("INPUT_REGISTER");}
}
static Operation read12(FILE* input,uint32_t seq)
{
    physical12="INPUT_WORDS";char* text=row(input);char saved[2050];snprintf(saved,sizeof(saved),"%s\n",text);char* p=text;
    if(strncmp(p,"O ",2))fail("INPUT_WORDS");p+=2;
    uint32_t actual=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");if(actual!=seq)fail("INPUT_SEQUENCE");space(&p);uint32_t code=decimal12(&p,"INPUT_OPCODE","INPUT_OPCODE");
    if(code>92||(code<80&&(code>=65||!used_legacy12[code])))fail("INPUT_OPCODE");arity12(text,67);
    Operation o={0};o.code=code;for(int j=0;j<64;++j){space(&p);o.u[j]=hex_word(&p);o.f[j]=from_bits(o.u[j]);}if(*p)fail("INPUT_WORDS");
    if(code<80){legacy_source12(&o);FILE* file=fmemopen(saved,strlen(saved),"r");if(!file)fail("INPUT_DOMAIN");o=read11(file,seq);fclose(file);return o;}
    validate_new12(&o,true);return o;
}
static void run_row12(FILE* input,int id,uint32_t seq)
{
    reset_operation9(id,seq,0);traceCount11=0;status12=reason12=0;vectorKind12=-1;vector12=b2Vec2_zero;private12=0;hasPreparedGeometry12=false;
    traceCount12=callbackAPCount12=0;readShape12=copyMutation12=-1;
    memset(finals11,0,sizeof(finals11));memset(count11,0,sizeof(count11));memset(public11,0,sizeof(public11));memset(counts10,0,sizeof(counts10));memset(hitsCount10,0,sizeof(hitsCount10));memset(counts12,0,sizeof(counts12));
    begin_output9();Operation o=read12(input,seq);opcode9=o.code;fixture11=profile12==9?guardSeedApplied10:profile12==10&&(o.code==51||o.code==52||o.code==64);population9(&o);execute12(&o);hits10(&o);public_sleep11(&o);observe12();world10_dump();private_sleep11();
    if(OBS){prefix12("I10",0,0,0);for(int j=0;j<6;++j)word(counts10[j]);putchar('\n');prefix12("I11",0,0,0);for(int j=0;j<11;++j)word(count11[j]);putchar('\n');}
    prefix12("Z10",0,0,0);for(int j=0;j<4;++j)word(hitsCount10[j]);word(completed10);putchar('\n');
    prefix12("Z11",0,0,0);word(public11[0]);word(public11[1]);word(positive11);putchar('\n');
    prefix12("I12",0,0,0);for(int j=0;j<11;++j)word(counts12[j]);putchar('\n');
    if(OBS){prefix12("IP12",0,0,0);word(private12);putchar('\n');}
    prefix12("Z12",0,0,0);word(positive11);word(seq);putchar('\n');commit10();
}
static void reset12(int id)
{
    reset_case10();positive11=0;case9=id;memset(hooks12,0,sizeof(hooks12));memset(copies12,0,sizeof(copies12));
}
static void run_rows12(FILE* input,int id,uint32_t count)
{
    reset12(id);printf("CASE %d %"PRIu32"\n",id,count);
    for(uint32_t seq=1;seq<=count;++seq)run_row12(input,id,seq);
}
#include "kontrola-zywy-guard.h"
int main(int argc,char** argv)
{
    if(argc!=2)fail("INPUT_DOMAIN");FILE* input=fopen(argv[1],"rb");if(!input)fail("INPUT_DOMAIN");
    char* p=row(input);
    if(rowEof11&&(!strncmp("GUARD12 ",p,strlen(p))||!strncmp("COMPONENT12 ",p,strlen(p))||!strncmp("PORT12 ",p,strlen(p))))fail("INPUT_EOF");
    if(!strncmp(p,"GUARD12 ",8)){arity12(p,2);p+=8;uint32_t count=decimal12(&p,"INPUT_HEADER","INPUT_N_RANGE");if(*p)fail("INPUT_HEADER");if(count!=1)fail("INPUT_N_RANGE");return guard_main12(input);}
    if(!strncmp(p,"COMPONENT12 ",12)){arity12(p,2);p+=12;uint32_t count=decimal12(&p,"INPUT_HEADER","INPUT_N_RANGE");if(*p)fail("INPUT_HEADER");if(count<1||count>32)fail("INPUT_N_RANGE");return math12(input,count);}
    if(strncmp(p,"PORT12 ",7))fail("INPUT_HEADER");arity12(p,2);p+=7;
    uint32_t n=decimal12(&p,"INPUT_HEADER","INPUT_N_RANGE");if(*p)fail("INPUT_HEADER");if(n<1||n>160)fail("INPUT_N_RANGE");profile11=8;profile12=8;
    printf("PORT12 %"PRIu32"\n",n);
    for(int id=1;id<=(int)n;++id){physical12="INPUT_SEQUENCE";p=row(input);if(strncmp(p,"C ",2))fail("INPUT_SEQUENCE");arity12(p,3);p+=2;
        uint32_t actual=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");space(&p);uint32_t count=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");if(*p||actual!=(uint32_t)id||!count||count>(uint32_t)limits10[id-1][3])fail("INPUT_SEQUENCE");
        run_rows12(input,id,count);if(id==(int)n)trailing12(input);
        printf("ENDCASE %d\n",id);for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);
    }
    if(fclose(input))fail("INPUT_DOMAIN");printf("END %"PRIu32"\n",n);free_tokens();free(trace12);free(callbackAP12);return ferror(stdout)||fflush(stdout)?2:0;
}
