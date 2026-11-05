                                          
                               
                                                                                  
   
                                                                             
                                                                            
                                        
#include <box2d/box2d.h>
#ifndef OBS
#define OBS 1
#endif
#ifndef GUARD8
#define GUARD8 1
#endif
#if 1
#include "world.h"
#include "body.h"
#include "shape.h"
#include "broad_phase.h"
#include "solver_set.h"
#include "solver.h"
#include "atomic.h"
_Static_assert(B2_VALIDATE == 0, "Release validation configuration");
_Static_assert(_Generic(((b2SolverBlock*)0)->count, int16_t: 1, default: 0), "B13 signed int16 count");
#endif
#if !defined(NDEBUG) || defined(B2_ENABLE_ASSERT)
#error PORT8 requires Release / NDEBUG without B2_ENABLE_ASSERT
#endif
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>




extern void* port9Enqueue(b2TaskCallback*,int,int,void*,void*);
extern void port9Finish(void*,void*);
enum { CASES = 64, WORLDS = 16, BODIES = 256, SHAPES = 512, GEOMETRY = 4, OK = 0, STALE = 1, FOREIGN = 2, LIMIT = 3, PARAM = 5, UNSUPPORTED_PAIR = 6 };
_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "IEEE binary32 required");
_Static_assert(CHAR_BIT == 8 && sizeof(int) == 4, "32-bit int required");
typedef struct World { bool saved, live;
    b2WorldId raw;
    uint64_t birth;
    } World;
typedef struct Body { bool saved, live;
    b2BodyId raw;
    uint64_t owner, birth;
    } Body;
typedef struct Operation { uint32_t code, u[64];
    float f[64];
    } Operation;
static void validate9(const Operation*);
static World worlds[WORLDS];
static Body bodies[BODIES];
typedef struct Shape { bool saved, live;
    b2ShapeId raw;
    uint64_t owner, birth;
    } Shape;
static Shape shapes[SHAPES];
static uint64_t lastIssued;
                                                                              
                                                                               
static FILE* output9;
static char* outputBytes9;
static size_t outputSize9;

static void fail(const char* message)
{
    const char* code=message;
    if(strncmp(code,"INPUT_",6)){
        if(strstr(code,"unsaved"))code="INPUT_REGISTER_UNINITIALIZED";
        else if(strstr(code,"replace live")||!strcmp(code,"shape registers"))code="INPUT_REGISTER_COLLISION";
        else if(strstr(code,"decimal"))code="INPUT_DECIMAL";
        else if(strstr(code,"hex")||strstr(code,"word"))code="INPUT_WORD";
        else if(strstr(code,"bool")||strstr(code,"game update"))code="INPUT_BOOL";
        else if(strstr(code,"unused")||strstr(code,"absent"))code="INPUT_UNUSED";
        else if(strstr(code,"rotation"))code="INPUT_ROTATION";
        else if(!strcmp(code,"tag")||strstr(code,"kind")||strstr(code,"type"))code="INPUT_ENUM";
        else if(strstr(code,"tag"))code="INPUT_TAG";
        else if(strstr(code,"seq"))code="INPUT_SEQ";
        else if(strstr(code,"opcode"))code="INPUT_OPCODE";
        else if(strstr(code,"register")||!strcmp(code,"body definition"))code="INPUT_REGISTER_RANGE";
        else if(strstr(code,"tokens")||strstr(code,"space"))code="INPUT_ARITY";
        else code="INPUT_DOMAIN";
    }
    if(output9){fclose(output9);output9=NULL;free(outputBytes9);outputBytes9=NULL;}
    fprintf(stderr,"PORT9B: %s\n",code);exit(2);
}
static void begin_output9(void)
{
    outputBytes9=NULL;outputSize9=0;output9=open_memstream(&outputBytes9,&outputSize9);
    if(!output9)fail("INPUT_DOMAIN");
}
static void commit_output9(void)
{
    bool bad=ferror(output9)!=0;if(fclose(output9))bad=true;output9=NULL;
    if(bad){free(outputBytes9);outputBytes9=NULL;fail("INPUT_DOMAIN");}
    size_t written=fwrite(outputBytes9,1,outputSize9,stdout);free(outputBytes9);outputBytes9=NULL;
    if(written!=outputSize9)fail("INPUT_DOMAIN");
}
#define printf(...) fprintf(output9?output9:stdout,__VA_ARGS__)
#define putchar(c) fputc((c),output9?output9:stdout)
static float from_bits(uint32_t u) { float f;
    memcpy(&f, &u, 4);
    return f;
    }
static uint32_t to_bits(float f) { uint32_t u;
    memcpy(&u, &f, 4);
    return u;
    }
static void word(uint32_t u) { printf(" %08" PRIx32, u);
    }
static void wide(uint64_t u) { word((uint32_t)u);
    word((uint32_t)(u >> 32));
    }
static void real(float f) { word(to_bits(f));
    }
static void vec(b2Vec2 v) { real(v.x);
    real(v.y);
    }
static void world_raw(World w) { word(w.raw.index1);
    word(0);
    word(w.raw.generation);
    word(b2StoreWorldId(w.raw));
    word(0);
    }
static void body_raw(Body b) { word((uint32_t)b.raw.index1);
    word(b.raw.world0);
    word(b.raw.generation);
    wide(b2StoreBodyId(b.raw));
    }
static void world_handle(World w) { world_raw(w);
    wide(0);
    wide(w.birth);
    }
static void body_handle(Body b) { body_raw(b);
    wide(b.owner);
    wide(b.birth);
    }

static bool world_live(const World* w)
{
    if (!w->saved) return false;
                                                                              
                                                                                
    for (int i = 0; i < WORLDS; ++i)
        if (worlds[i].live && worlds[i].raw.index1 == w->raw.index1 && worlds[i].birth == w->birth)
            return b2World_IsValid(w->raw);
    return false;
}
static bool body_live(const Body* b)
{
    if (!b->saved) return false;
    bool ownerLive = false;
    for (int i = 0; i < WORLDS; ++i)
        if (worlds[i].birth == b->owner && world_live(worlds+i)) ownerLive = true;
    if (!ownerLive) return false;
    for (int i = 0; i < BODIES; ++i) {
        const Body* current = bodies+i;
        if (current->live && current->raw.world0 == b->raw.world0 && current->raw.index1 == b->raw.index1
            && current->owner == b->owner && current->birth == b->birth) return b2Body_IsValid(b->raw);
    }
    return false;
}
static int guard(const World* w, const Body* b)
{
    if (!world_live(w)) return STALE;
    if (w->birth != b->owner) return FOREIGN;
    return body_live(b) ? OK : STALE;
}
static bool ticket_next(uint64_t current, uint64_t* candidate)
{
    if (current == UINT64_MAX) return false;
    *candidate = current+1;
    return true;
}
static int create_world(int slot, b2WorldDef def)
{
    uint64_t next;
    if (!ticket_next(lastIssued, &next)) return LIMIT;
    b2WorldId raw = b2CreateWorld(&def);
    if (B2_IS_NULL(raw)) fail("public CreateWorld failed");
    worlds[slot] = (World){true, true, raw, next};
    lastIssued = next;
#ifdef SPEC9_FALSE
    b2World_EnableSpeculative(raw,false);
#endif
    return OK;
}
static int create_body(int slot, int owner, b2BodyDef def)
{
    if (!world_live(worlds+owner)) return STALE;
    uint64_t next;
    if (!ticket_next(lastIssued, &next)) return LIMIT;
    b2BodyId raw = b2CreateBody(worlds[owner].raw, &def);
    if (B2_IS_NULL(raw)) fail("public CreateBody failed");
    bodies[slot] = (Body){true, true, raw, worlds[owner].birth, next};
    lastIssued = next;
    return OK;
}
static void destroy_world(int slot)
{
    World* w = worlds+slot;
    b2DestroyWorld(w->raw);
    w->live = false;
    for (int i = 0; i < SHAPES; ++i) if (shapes[i].owner == w->birth) shapes[i].live = false;
    for (int i = 0; i < BODIES; ++i)
        if (bodies[i].owner == w->birth) bodies[i].live = false;
}
static void destroy_body(int slot)
{
    b2BodyId id = bodies[slot].raw;
    for (int i = 0; i < SHAPES; ++i) if (shapes[i].live && shapes[i].owner == bodies[slot].owner) {
        b2BodyId parent = b2Shape_GetBody(shapes[i].raw);
        if (b2StoreBodyId(parent) == b2StoreBodyId(id)) shapes[i].live = false;
    }
    b2DestroyBody(id);
    bodies[slot].live = false;
}

                                                                                 
static char line[2049];
static char* row(FILE* file)
{
    size_t n=0;int c;
    while((c=fgetc(file))!=EOF&&c!='\n'){
        if(c==0||c>127)fail("INPUT_ASCII");
        if(n>=2048)fail("INPUT_ARITY");line[n++]=(char)c;
    }
    if(c==EOF&&!n)fail("INPUT_EOF");
    if(n&&line[n-1]=='\r'&&c=='\n')--n;
    line[n]=0;
    if(strchr(line,'\r'))fail("INPUT_CR");
    if(!n)fail("INPUT_EMPTY_LINE");
    if(line[0]==' '||line[n-1]==' '||strstr(line,"  ")||strchr(line,'\t'))fail("INPUT_SPACING");
    return line;
}
static uint32_t decimal(char** cursor)
{
    char* p = *cursor;
    if (*p < '0' || *p > '9' || (*p == '0' && p[1] >= '0' && p[1] <= '9')) fail("canonical decimal");
    uint64_t u = 0;
    do {
        u = 10*u+(uint32_t)(*p++-'0');
        if (u > UINT32_MAX) fail("decimal overflow");
    } while (*p >= '0' && *p <= '9');
    *cursor = p;
    return (uint32_t)u;
}
static void space(char** p) { if (*(*p)++ != ' ') fail("single space required");
    }
static uint32_t hex_word(char** cursor)
{
    char* p = *cursor;
    uint32_t u = 0;
    for (int i = 0; i < 8; ++i) {
        unsigned char c = (unsigned char)*p++;
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) fail("canonical hex");
        u = (u << 4) | (uint32_t)(c <= '9' ? c-'0' : c-'a'+10);
    }
    *cursor = p;
    return u;
}
static void shape_raw(Shape s) { word((uint32_t)s.raw.index1);
    word(s.raw.world0);
    word(s.raw.generation);
    wide(b2StoreShapeId(s.raw));
    }
static void shape_handle(Shape s) { shape_raw(s);
    wide(s.owner);
    wide(s.birth);
    }
static void aabb(b2AABB a) { vec(a.lowerBound);
    vec(a.upperBound);
    }
static void mass(b2MassData m) { real(m.mass);
    vec(m.center);
    real(m.rotationalInertia);
    }
static bool shape_live(const Shape* s)
{
    if (!s->saved) return false;
    bool ownerLive=false;
    for (int i=0;i<WORLDS;++i)if(worlds[i].birth==s->owner&&world_live(worlds+i))ownerLive=true;
    if(!ownerLive)return false;
    for(int i=0;i<SHAPES;++i)if(shapes[i].live&&shapes[i].owner==s->owner&&shapes[i].birth==s->birth
        &&b2StoreShapeId(shapes[i].raw)==b2StoreShapeId(s->raw))return b2Shape_IsValid(s->raw);
    return false;
}
static int shape_guard(const World* w, const Shape* s)
{
    if (!world_live(w)) return STALE;
    if (w->birth != s->owner) return FOREIGN;
    return shape_live(s) ? OK : STALE;
}
                                                                               
typedef struct Token { uint32_t low, high;
    struct Token* next;
    } Token;
static Token* tokens;
static void* token(uint32_t present, uint32_t low, uint32_t high)
{
    if (!present) return NULL;
    Token* t = malloc(sizeof(*t));
    if (!t) fail("token allocation");
    *t = (Token){low, high, tokens};
    tokens = t;
    return t;
}
static void object(void* address)
{
    if (!address) { word(0);
        word(0);
        word(0);
        return;
        }
    Token* t = tokens;
    while (t && t != address) t = t->next;
    if (!t) fail("unknown public userData token");
    word(1);
    word(t->low);
    word(t->high);
}
static void free_tokens(void) { while (tokens) { Token* t = tokens;
        tokens = t->next;
        free(t);
        } }
typedef struct Geometry {
    int type;
    b2Circle circle;
    b2Capsule capsule;
    b2Segment segment;
    b2Polygon polygon;
} Geometry;
static bool finite_vec(b2Vec2 v) { return isfinite(v.x) && isfinite(v.y);
    }
static b2MassData geo_mass(const Geometry* g, float density)
{
    if (g->type == 0) return b2ComputeCircleMass(&g->circle, density);
    if (g->type == 1) return b2ComputeCapsuleMass(&g->capsule, density);
    if (g->type == 3) return b2ComputePolygonMass(&g->polygon, density);
    return (b2MassData){0};
}
static b2AABB geo_aabb(const Geometry* g, b2Transform t)
{
    if (g->type == 0) return b2ComputeCircleAABB(&g->circle, t);
    if (g->type == 1) return b2ComputeCapsuleAABB(&g->capsule, t);
    if (g->type == 3) return b2ComputePolygonAABB(&g->polygon, t);
    return b2ComputeSegmentAABB(&g->segment, t);
}
static Geometry public_geometry(b2ShapeId id)
{
    Geometry g = {0};
    g.type = b2Shape_GetType(id);
    if (g.type == 0) g.circle = b2Shape_GetCircle(id);
    else if (g.type == 1) g.capsule = b2Shape_GetCapsule(id);
    else if (g.type == 2) g.segment = b2Shape_GetSegment(id);
    else if (g.type == 3) g.polygon = b2Shape_GetPolygon(id);
    else fail("unexpected public shape type");
    return g;
}
static bool prepare(uint32_t tag, const uint32_t* u, Geometry* g)
{
    float f[40];
    for (int i = 0; i < 40; ++i) f[i] = from_bits(u[i]);
    memset(g, 0, sizeof(*g));
    g->type = (int)tag;
    if (tag == 0) {
        if (!(f[2] > 0)) return false;
        g->circle = (b2Circle){{f[0], f[1]}, f[2]};
    } else if (tag == 1) {
        if (!(f[4] > 0)) return false;
        g->capsule = (b2Capsule){{f[0], f[1]}, {f[2], f[3]}, f[4]};
        if (b2DistanceSquared(g->capsule.center1, g->capsule.center2) <= 0.005f*0.005f) {
            g->type = 0;
            g->circle = (b2Circle){b2Lerp(g->capsule.center1, g->capsule.center2, 0.5f), f[4]};
        }
    } else if (tag == 2) {
        g->segment = (b2Segment){{f[0], f[1]}, {f[2], f[3]}};
        if (b2DistanceSquared(g->segment.point1, g->segment.point2) <= 0.005f*0.005f) return false;
    } else if (tag == 4) {
        if (!(f[0] > 0 && f[1] > 0 && f[6] >= 0)) return false;
        g->type = 3;
        g->polygon = b2MakeOffsetRoundedBox(f[0], f[1], (b2Vec2){f[2], f[3]}, (b2Rot){f[4], f[5]}, f[6]);
    } else {
        uint32_t count = u[0];
        if (count < 3 || count > 8 || !(f[1] >= 0)) return false;
        b2Hull h = {0};
        h.count = (int)count;
        for (uint32_t i = 0; i < count; ++i) h.points[i] = (b2Vec2){f[2+2*i], f[3+2*i]};
        float area = 0;
        for (int i = 0; i < h.count; ++i) {
            b2Vec2 e = b2Sub(h.points[(i+1)%h.count], h.points[i]);
            float dd = b2Dot(e,e);
            if (!(dd > 0) || !isfinite(dd)) return false;
        }
        for (int i = 1; i+1 < h.count; ++i)
            area += 0.5f*b2Cross(b2Sub(h.points[i],h.points[0]), b2Sub(h.points[i+1],h.points[0]));
        if (!(area > FLT_EPSILON) || !isfinite(area) || !b2ValidateHull(&h)) return false;
        g->polygon = b2MakePolygon(&h, f[1]);
    }
    if (g->type == 3) {
        if (!finite_vec(g->polygon.centroid) || !isfinite(g->polygon.radius)) return false;
        for (int i = 0; i < g->polygon.count; ++i)
            if (!finite_vec(g->polygon.vertices[i]) || !finite_vec(g->polygon.normals[i])) return false;
    }
    return true;
}
                                                                            
                                                                                
static bool add_mass(b2MassData md, float* total, b2Vec2* center, float* inertia)
{
    *total += md.mass;
    *center = b2MulAdd(*center, md.mass, md.center);
    *inertia += md.rotationalInertia;
    return isfinite(*total) && finite_vec(*center) && isfinite(*inertia);
}
static bool finite_extent(const Geometry* g, b2Vec2 center, b2Transform t)
{
    b2Vec2 points[8];
    int count = 0;
    float radius = 0;
    if (g->type == 0) { points[0] = g->circle.center;
        count = 1;
        radius = g->circle.radius;
        }
                                                                       
                                                                          
    if (g->type == 1 && !isfinite(b2DistanceSquared(g->capsule.center1, g->capsule.center2))) return false;
    if (g->type == 2 && !isfinite(b2DistanceSquared(g->segment.point1, g->segment.point2))) return false;
    if (g->type == 1) { points[0] = g->capsule.center1;
        points[1] = g->capsule.center2;
        count = 2;
        radius = g->capsule.radius;
        }
    if (g->type == 2) { points[0] = g->segment.point1;
        points[1] = g->segment.point2;
        count = 2;
        }
    if (g->type == 3) { count = g->polygon.count;
        radius = g->polygon.radius;
        for (int i=0;i<count;++i) points[i]=g->polygon.vertices[i];
        }
    for (int i=0;i<count;++i) {
        b2Vec2 d = b2Sub(points[i], center);
        float dd = b2Dot(d,d);
        if (!isfinite(dd) || !isfinite(sqrtf(dd)+radius)) return false;
    }
    b2AABB a = geo_aabb(g,t);
    return finite_vec(a.lowerBound) && finite_vec(a.upperBound)
        && isfinite(a.lowerBound.x-0.07f) && isfinite(a.lowerBound.y-0.07f)
        && isfinite(a.upperBound.x+0.07f) && isfinite(a.upperBound.y+0.07f);
}
static bool preflight(b2BodyId id, const b2BodyDef* fresh, const Geometry* added, float density,
                      b2ShapeId changed, bool remove, float newDensity)
{
    b2ShapeId list[256];
    int count = 0;
    b2BodyType type;
    bool fixed;
    b2Transform t;
    b2Vec2 oldCenter, velocity;
    float angular;
    if (fresh) {
        type=fresh->type;
        fixed=fresh->fixedRotation;
        t=(b2Transform){fresh->position,fresh->rotation};
        oldCenter=fresh->position;
        velocity=type==b2_staticBody ? b2Vec2_zero : fresh->linearVelocity;
        angular=type==b2_staticBody ? 0 : fresh->angularVelocity;
    } else {
        type=b2Body_GetType(id);
        fixed=b2Body_IsFixedRotation(id);
        t=b2Body_GetTransform(id);
        oldCenter=b2Body_GetWorldCenterOfMass(id);
        velocity=b2Body_GetLinearVelocity(id);
        angular=b2Body_GetAngularVelocity(id);
        int expected=b2Body_GetShapeCount(id);
        if (expected>256) fail("preflight capacity");
        count=b2Body_GetShapes(id,list,256);
        if(count!=expected) fail("public GetShapes count");
    }
    if ((added && !(density>=0)) || (!remove && !B2_IS_NULL(changed) && !(newDensity>=0))) return false;
    float total=0, inertia=0;
    b2Vec2 center=b2Vec2_zero;
    if (type==b2_dynamicBody) {
        if (added && density!=0 && !add_mass(geo_mass(added,density),&total,&center,&inertia)) return false;
        for (int i=0;i<count;++i) {
            bool match=b2StoreShapeId(list[i])==b2StoreShapeId(changed);
            if (match && remove) continue;
            float d=match ? newDensity : b2Shape_GetDensity(list[i]);
            if (d==0) continue;
            Geometry g=public_geometry(list[i]);
            if (!add_mass(geo_mass(&g,d),&total,&center,&inertia)) return false;
        }
        if (total>0) { float inv=1.0f/total;
            if(!isfinite(inv)) return false;
            center=b2MulSV(inv,center);
            }
        if (inertia>0 && !fixed) { inertia-=total*b2Dot(center,center);
            if(!(inertia>0) || !isfinite(1.0f/inertia)) return false;
            }
        else inertia=0;
        if (total>0 && !fixed && !(inertia>0)) return false;
        b2Vec2 moved=b2TransformPoint(t,center);
        velocity=b2Add(velocity,b2CrossSV(angular,b2Sub(moved,oldCenter)));
        if (!isfinite(total) || !finite_vec(center) || !isfinite(inertia) || !finite_vec(moved) || !finite_vec(velocity)) return false;
    }
    if (added && !finite_extent(added,center,t)) return false;
    for(int i=0;i<count;++i) {
        if(remove && b2StoreShapeId(list[i])==b2StoreShapeId(changed)) continue;
        Geometry g=public_geometry(list[i]);
        if(!finite_extent(&g,center,t)) return false;
    }
    return true;
}
static b2ShapeDef shape_def(const uint32_t* a)
{
    b2ShapeDef d=b2DefaultShapeDef();
    d.density=from_bits(a[4]);
    d.updateBodyMass=a[5]!=0;
    d.invokeContactCreation=a[6]!=0;
    d.filter.categoryBits=(uint64_t)a[7]|(uint64_t)a[8]<<32;
    d.filter.maskBits=(uint64_t)a[9]|(uint64_t)a[10]<<32;
    memcpy(&d.filter.groupIndex,a+11,4);
    d.material.friction=0.6f;
    d.material.restitution=0;
    d.material.rollingResistance=0;
    d.material.tangentSpeed=0;
    d.material.userMaterialId=0;
    d.material.customColor=0;
#ifdef MATERIAL9_FIELD
    if(MATERIAL9_FIELD==0)d.material.friction=from_bits(MATERIAL9_BITS);
    if(MATERIAL9_FIELD==1)d.material.restitution=from_bits(MATERIAL9_BITS);
    if(MATERIAL9_FIELD==2)d.material.rollingResistance=from_bits(MATERIAL9_BITS);
    if(MATERIAL9_FIELD==3)d.material.tangentSpeed=from_bits(MATERIAL9_BITS);
#endif
    d.isSensor=false;
    d.enableSensorEvents=false;
    d.enableContactEvents=false;
    d.enableHitEvents=false;
    d.enablePreSolveEvents=false;
    d.userData=NULL;
    return d;
}
static bool valid_material_definition9(b2ShapeDef d)
{
    return isfinite(d.material.friction)&&d.material.friction>=0 && isfinite(d.material.restitution)&&d.material.restitution>=0
        && isfinite(d.material.rollingResistance)&&d.material.rollingResistance>=0 && isfinite(d.material.tangentSpeed);
}
static int create_shape(int slot, int owner, int parent, const uint32_t* a, bool game)
{
    int status=guard(worlds+owner,bodies+parent);
    if(status) return status;
    if(game&&!valid_material_definition9(shape_def(a)))return PARAM;
    Geometry g;
    bool valid=prepare(a[3],a+15,&g);
    if (!valid) {
        if(!game && a[3]==2) {
            b2Segment seg={{from_bits(a[15]),from_bits(a[16])},{from_bits(a[17]),from_bits(a[18])}};
            b2ShapeDef def=shape_def(a);
            b2ShapeId raw=b2CreateSegmentShape(bodies[parent].raw,&def,&seg);
            if(!B2_IS_NULL(raw)) fail("short segment unexpectedly allocated");
        }
        if(!game && a[3]!=2) fail("raw geometry");
        return GEOMETRY;
    }
    if(game && !preflight(bodies[parent].raw,NULL,&g,from_bits(a[4]),b2_nullShapeId,false,0)) return GEOMETRY;
    uint64_t next;
    if(!ticket_next(lastIssued,&next)) return LIMIT;
    b2ShapeDef d=shape_def(a);
    d.userData=token(a[12],a[13],a[14]);
    b2ShapeId raw;
                                                                    
    if(a[3]==1) {
        b2Capsule c={{from_bits(a[15]),from_bits(a[16])},{from_bits(a[17]),from_bits(a[18])},from_bits(a[19])};
        raw=b2CreateCapsuleShape(bodies[parent].raw,&d,&c);
    } else if(g.type==0) raw=b2CreateCircleShape(bodies[parent].raw,&d,&g.circle);
    else if(g.type==2) raw=b2CreateSegmentShape(bodies[parent].raw,&d,&g.segment);
    else raw=b2CreatePolygonShape(bodies[parent].raw,&d,&g.polygon);
    if(B2_IS_NULL(raw)) return GEOMETRY;
    shapes[slot]=(Shape){true,true,raw,worlds[owner].birth,next};
    lastIssued=next;
    return OK;
}
static b2WorldDef world_def(const Operation* o)
{
    b2WorldDef d=b2DefaultWorldDef();
    d.gravity=(b2Vec2){o->f[1],o->f[2]};
    d.maximumLinearSpeed=o->f[3];
    d.enableSleep=false;
    d.enableContinuous=false;
    d.workerCount=1;
    d.enqueueTask=port9Enqueue;
    d.finishTask=port9Finish;
    return d;
}
static b2BodyDef body_def(const uint32_t* a)
{
    b2BodyDef d=b2DefaultBodyDef();
    d.type=(b2BodyType)a[2];
    d.position=(b2Vec2){from_bits(a[3]),from_bits(a[4])};
    d.rotation=(b2Rot){from_bits(a[5]),from_bits(a[6])};
    d.linearVelocity=(b2Vec2){from_bits(a[7]),from_bits(a[8])};
    d.angularVelocity=from_bits(a[9]);
    d.fixedRotation=a[10]!=0;
    d.linearDamping=0;
    d.angularDamping=0;
    d.gravityScale=1;
    d.enableSleep=false;
    d.isAwake=true;
    d.isEnabled=true;
    d.isBullet=false;
    d.allowFastRotation=false;
    d.name=NULL;
    d.userData=NULL;
    return d;
}
static void pair_args(const uint32_t* a,uint32_t* ba,uint32_t* sa)
{
    memset(ba,0,64*sizeof(uint32_t));
    memset(sa,0,64*sizeof(uint32_t));
    ba[0]=a[0];
    ba[1]=a[2];
    ba[2]=a[3];
    memcpy(ba+3,a+4,7*sizeof(uint32_t));
    ba[10]=a[11];
    sa[0]=a[1];
    sa[1]=a[2];
    sa[2]=a[0];
    sa[3]=a[12];
    sa[4]=a[13];
    sa[5]=1;
    sa[6]=a[14];
    memcpy(sa+7,a+18,5*sizeof(uint32_t));
    memcpy(sa+12,a+15,3*sizeof(uint32_t));
    memcpy(sa+15,a+23,40*sizeof(uint32_t));
}
static int create_pair(const uint32_t* a)
{
    int owner=(int)a[2];
    if(!world_live(worlds+owner)) return STALE;
    uint32_t ba[64],sa[64];
    pair_args(a,ba,sa);
    b2BodyDef bd=body_def(ba);
    if(!valid_material_definition9(shape_def(sa)))return PARAM;
    Geometry g;
    if(!prepare(sa[3],sa+15,&g) || !preflight(b2_nullBodyId,&bd,&g,from_bits(sa[4]),b2_nullShapeId,false,0)) return GEOMETRY;
    if(lastIssued>UINT64_MAX-2) return LIMIT;
    bd.userData=token(a[15],a[16],a[17]);
    int status=create_body((int)a[0],owner,bd);
    if(status) fail("reserved body ticket failed");
    status=create_shape((int)a[1],owner,(int)a[0],sa,false);
    if(status) fail("reserved shape ticket failed");
    return OK;
}
static bool geometry_float(uint32_t tag,const uint32_t* g,int j)
{
    if(tag==3) return j==1 || (j>=2 && j<2+2*(int)(g[0]>8?8:g[0]));
    static const int counts[]={3,5,4,0,7};
    return j<counts[tag];
}
static void validate_new(const Operation* o)
{
    const uint32_t* a=o->u;
    int c=(int)o->code;
    bool floats[64]={false},bools[64]={false},allow=false;
    if(c==30) {
        if(a[0]>=BODIES||a[1]>=WORLDS||a[2]>2)fail("body definition");
        for(int i=3;i<=9;++i)floats[i]=true;
        floats[11]=floats[12]=floats[13]=true;
        bools[10]=bools[14]=bools[15]=true;
        allow=a[15]!=0;
        if(!allow&&(!b2IsNormalizedRot((b2Rot){o->f[5],o->f[6]})||o->f[11]<0||o->f[12]<0))fail("raw body definition");
    } else if(c==31||c==32) {
        if(a[0]>=WORLDS||(c==32&&a[3]>3))fail("register");
        allow=true;
        floats[1]=true;
    } else if(c==33||c==34) {
        if(a[0]>=WORLDS||a[1]>=BODIES||a[2]>5)fail("register/kind");
        for(int i=3;i<=6;++i)floats[i]=true;
        bools[7]=true;
        allow=c==34;
        if((a[2]==1||a[2]==4)&&(a[5]||a[6]))fail("unused force point");
        if((a[2]==2||a[2]==5)&&(a[4]||a[5]||a[6]))fail("unused scalar");
    } else if(c==35||c==36) {
        if(a[0]>=WORLDS||a[1]>=BODIES)fail("register");
        floats[2]=true;
        if(c==35)floats[3]=true;
        bools[c==35?4:3]=true;
        allow=a[c==35?4:3]!=0;
    } else if(c==37) {
        if(a[0]>3)fail("copy register");
    } else if(c==38) {
        if(a[0]>=WORLDS||a[1]>=BODIES)fail("register");
        bools[2]=true;
    } else if(c==39) {
        if(a[0]>=WORLDS||a[1]>=SHAPES)fail("register");
    }
    for(int i=0;i<64;++i) {
        if(bools[i]&&a[i]>1)fail("bool");
        if(!allow&&floats[i]&&!isfinite(o->f[i]))fail("NaN / Inf");
    }
}
static Operation read_operation(FILE* file,uint32_t seq)
{
    char* p=row(file);
    int tokens_=1;for(char* t=p;*t;++t)tokens_+=*t==' ';
    if(tokens_!=67)fail("INPUT_ARITY");
    if(*p++!='O') fail("O tag");
    space(&p);
    if(decimal(&p)!=seq)fail("seq");
    space(&p);
    Operation o={0};
    o.code=decimal(&p);
    int used=0;
    switch(o.code) {
        case 0:used=4;
        break;
        case 1:used=1;
        break;
        case 2:used=11;
        break;
        case 3:case 5:case 13:case 14:case 18:used=2;
        break;
        case 4:case 15:used=6;
        break;
        case 10:case 17:used=55;
        break;
        case 11:case 19:case 21:used=3;
        break;
        case 12:used=4;
        break;
        case 16:used=63;
        break;
        case 30:used=16;
        break;
        case 31:case 36:case 38:used=3;
        if(o.code==36)used=4;
        break;
        case 32:used=4;
        break;
        case 33:case 34:used=8;
        break;
        case 35:used=5;
        break;
        case 37:used=1;
        break;
        case 39:used=2;
        break;
        case 40:used=59;break;
        case 41:case 42:case 43:case 44:case 45:used=1;break;
        case 46:used=4;break;
        case 47:case 48:case 53:used=3;break;
        case 49:case 50:used=2;break;
        case 51:used=39;break;
        case 52:used=7;break;
        default:fail("opcode");
    }
    for(int i=0;i<64;++i) {space(&p);
        o.u[i]=hex_word(&p);
        o.f[i]=from_bits(o.u[i]);
        if(i>=used && o.u[i])fail("unused");
        }
    if(*p)fail("extra operation tokens");
    uint32_t* a=o.u;
    if(o.code==0&&a[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");
    if((o.code==2||o.code==30)&&a[2]>2)fail("INPUT_ENUM");
    bool isFloat[64]={false},isBool[64]={false};
    int rot=-1;
    if(o.code>=40){validate9(&o);return o;}
    if(o.code>=30) {
        validate_new(&o);
        return o;
    }
    if(o.code<=5) {
        if(o.code==0) {if(a[0]>=WORLDS || !(o.f[3]>0))fail("world definition");
            for(int i=1;i<=3;++i)isFloat[i]=true;
            }
        else if(o.code==2) {if(a[0]>=BODIES||a[1]>=WORLDS||a[2]>2)fail("body definition");
            for(int i=3;i<=9;++i)isFloat[i]=true;
            isBool[10]=true;
            rot=5;
            }
        else {if(a[0]>=WORLDS||(o.code!=1&&a[1]>=BODIES))fail("register");
            if(o.code==4){for(int i=2;i<=5;++i)isFloat[i]=true;
                rot=4;
                }}
    } else if(o.code==10||o.code==17||o.code==16) {
        bool pair=o.code==16;
        uint32_t tag=a[pair?12:3];
        int start=pair?23:15;
        if(tag>4)fail("tag");
        if(pair) {
            if(a[0]>=BODIES||a[1]>=SHAPES||a[2]>=WORLDS||a[3]>2)fail("register/type");
            for(int i=4;i<=10;++i)isFloat[i]=true;
            isFloat[13]=true;
            isBool[11]=true;
            isBool[14]=true;
            isBool[15]=true;
            rot=6;
            if(!a[15]&&(a[16]||a[17]))fail("object absent");
        } else {
            if(a[0]>=SHAPES||a[1]>=WORLDS||a[2]>=BODIES)fail("register");
            isFloat[4]=true;
            isBool[5]=true;
            isBool[6]=true;
            isBool[12]=true;
            if(o.code==17 && a[5]!=1)fail("game update");
            if(!a[12]&&(a[13]||a[14]))fail("object absent");
        }
        for(int j=0;j<40;++j) {
            if(geometry_float(tag,a+start,j))isFloat[start+j]=true;
            else if(!(tag==3&&j==0)&&a[start+j])fail("unused geometry");
        }
        if(tag==4 && !b2IsNormalizedRot((b2Rot){o.f[start+4],o.f[start+5]}))fail("rotation");
    } else {
        uint32_t max=(o.code==13||o.code==20||o.code==21)?BODIES:SHAPES;
        if(a[0]>=WORLDS||a[1]>=max)fail("register");
        if(o.code==11)isBool[2]=true;
        if(o.code==12||o.code==19)isFloat[2]=true;
        if(o.code==12)isBool[3]=true;
        if(o.code==15) {
            if((a[1]!=2&&a[1]!=3)||a[2]>=(a[1]==2?BODIES:SHAPES))fail("object kind/register");
            isBool[3]=true;
            if(!a[3]&&(a[4]||a[5]))fail("object absent");
        }
        if(o.code==20&&(a[2]>=SHAPES||!a[3]||a[3]>65536||a[4]>=SHAPES||a[2]==a[4]))fail("CHURN");
        if(o.code==21&&a[2]>256)fail("capacity");
    }
    if((o.code==10 && o.f[4]<0) || (o.code==12 && o.f[2]<0)) fail("raw density");
    for(int i=0;i<64;++i) {
        if(isFloat[i]&&!isfinite(o.f[i]))fail("NaN / Inf");
        if(isBool[i]&&a[i]>1)fail("bool");
    }
    if(rot>=0&&!b2IsNormalizedRot((b2Rot){o.f[rot],o.f[rot+1]}))fail("rotation");
    return o;
}
static void echo(int id,uint32_t seq,const Operation* o)
{
    printf("E %d %"PRIu32" %"PRIu32,id,seq,o->code);
    for(int i=0;i<64;++i)word(o->u[i]);
    putchar('\n');
}
static void geometry_dump(b2ShapeId id)
{
    Geometry g=public_geometry(id);
    uint32_t h[40]={0};
    h[0]=(uint32_t)g.type;
    b2Vec2 points[8]={0},normals[8]={0};
    int count;
    if(g.type==0) {count=1;
        points[0]=g.circle.center;
        h[2]=to_bits(g.circle.radius);
        }
    else if(g.type==1) {count=2;
        points[0]=g.capsule.center1;
        points[1]=g.capsule.center2;
        h[2]=to_bits(g.capsule.radius);
        }
    else if(g.type==2) {count=2;
        points[0]=g.segment.point1;
        points[1]=g.segment.point2;
        }
    else {count=g.polygon.count;
        h[2]=to_bits(g.polygon.radius);
        h[3]=to_bits(g.polygon.centroid.x);
        h[4]=to_bits(g.polygon.centroid.y);
        for(int i=0;i<count;++i){points[i]=g.polygon.vertices[i];
            normals[i]=g.polygon.normals[i];
            }}
    h[1]=(uint32_t)count;
    for(int i=0;i<count;++i) {h[5+2*i]=to_bits(points[i].x);
        h[6+2*i]=to_bits(points[i].y);
        }
    if(g.type==3)for(int i=0;i<count;++i){h[21+2*i]=to_bits(normals[i].x);
        h[22+2*i]=to_bits(normals[i].y);
        }
    for(int i=0;i<40;++i)word(h[i]);
}
                                                                       
                                                                           
typedef struct SavedMove {
    Body body;
    b2Transform transform;
    uint32_t object[3];
    bool fellAsleep;
} SavedMove;
typedef struct MoveCopy { bool saved; int count; SavedMove moves[65]; } MoveCopy;
static MoveCopy copies[4];
static struct {
    int k, moves, mcn, mc, up, qgn, qg, sb;
    int world, copy, listBody, listChange, parentShape, status, effective;
    uint32_t dt, requested;
    bool didSolve;
    b2BodyMoveEvent events[65];
    Shape pairA,pairB;
} extra;

static void dump(int id,uint32_t seq,int nR,uint32_t nJ,int qBody,int capacity);
static void result(int id,uint32_t seq,int index,int status,int kind,int slot);

static Body public_body_number(b2BodyId raw)
{
    for(int i=0;i<BODIES;++i)
        if(bodies[i].live&&body_live(bodies+i)&&b2StoreBodyId(bodies[i].raw)==b2StoreBodyId(raw))return bodies[i];
    fail("public body has no live ticket");
    return (Body){0};
}
static Shape public_shape_number(b2ShapeId raw)
{
    for(int i=0;i<SHAPES;++i)
        if(shapes[i].live&&shape_live(shapes+i)&&b2StoreShapeId(shapes[i].raw)==b2StoreShapeId(raw))return shapes[i];
    fail("public shape has no live ticket");
    return (Shape){0};
}
#include "kontrola-kontakty9.h"

static void copy_object(uint32_t* dest,void* address)
{
    memset(dest,0,3*sizeof(uint32_t));
    if(!address)return;
    Token* t=tokens;
    while(t&&t!=address)t=t->next;
    if(!t)fail("unknown public userData token");
    dest[0]=1;dest[1]=t->low;dest[2]=t->high;
}
static bool valid_body8(const b2BodyDef* d)
{
    return finite_vec(d->position)&&finite_vec(d->linearVelocity)&&isfinite(d->angularVelocity)
        &&isfinite(d->rotation.c)&&isfinite(d->rotation.s)&&b2IsNormalizedRot(d->rotation)
        &&isfinite(d->linearDamping)&&d->linearDamping>=0
        &&isfinite(d->angularDamping)&&d->angularDamping>=0&&isfinite(d->gravityScale);
}
static bool valid_step(float dt,int n)
{
    if(!isfinite(dt)||dt<0||n<=0)return false;
    if(dt==0)return true;
    float inv_dt=1.0f/dt;
    float h=dt/(float)n;
    float inv_h=(float)n*inv_dt;
    return h>0&&isfinite(inv_dt)&&isfinite(h)&&isfinite(inv_h);
}
                                                                  
                                                                     
static bool block_width_ok(int count)
{
    if(count<0)return false;
    int size=32,blocks=count==0?0:(count-1)/32+1;
    if(count>128){size=count/4;blocks=4;}
    for(int j=0;j<blocks;++j) {
        int width=j==blocks-1?count-j*size:size;
        if(width<0||width>INT16_MAX)return false;
    }
    return true;
}

#if GUARD8
                                                                             
                                                                         
static bool first_pair(int slot,b2ShapeId* first,b2ShapeId* second)
{
    b2World* w=b2GetWorldFromId(worlds[slot].raw);
    if(port9Prepare(w,first,second,false))return true;
    for(int j=0;j<w->contacts.count;++j){b2Contact* c=w->contacts.data+j;
        if(c->contactId==j){b2Shape* a=w->shapes.data+c->shapeIdA;b2Shape* b=w->shapes.data+c->shapeIdB;
            *first=(b2ShapeId){a->id+1,w->worldId,a->generation};*second=(b2ShapeId){b->id+1,w->worldId,b->generation};return true;}}
    return false;
}
static void pair_member(Shape s)
{
    word((uint32_t)(s.raw.index1-1));wide(s.birth);wide(s.owner);
}
#endif

static int do_step(int id,uint32_t seq,const Operation* o)
{
    (void)id;(void)seq;
    const uint32_t* a=o->u;
    int n;memcpy(&n,a+2,4);
    float dt=o->f[1];int slot=(int)a[0];
    extra.k=1;extra.world=slot;extra.dt=a[1];extra.requested=a[2];
    int status=world_live(worlds+slot)?OK:STALE;
    if(!status&&o->code==32&&!valid_step(dt,n))status=PARAM;
    if(status)return status;
    int awake=0;
    for(int i=0;i<BODIES;++i)if(body_live(bodies+i)&&bodies[i].owner==worlds[slot].birth&&b2Body_GetType(bodies[i].raw)!=b2_staticBody)++awake;
    if(!block_width_ok(awake))return LIMIT;
    if(o->code==31&&!isfinite(dt)&&dt>0&&awake)fail("LEGACY_DOMAIN requires empty/static world");
#if GUARD8
    b2ShapeId first=b2_nullShapeId,second=b2_nullShapeId;
    if(dt!=0&&first_pair(slot,&first,&second)) {
        extra.up=1;
                                                                        
        extra.pairA=public_shape_number(first);extra.pairB=public_shape_number(second);
        return UNSUPPORTED_PAIR;
    }
#else
    (void)id;(void)seq;
#endif
    b2World_Step(worlds[slot].raw,dt,n);
    b2Counters counters=b2World_GetCounters(worlds[slot].raw);
    if((dt!=0&&counters.contactCount)||counters.jointCount)fail("INPUT_DOMAIN");
    extra.effective=dt==0?0:n>0?n:1;
    extra.didSolve=dt>0;
    b2BodyEvents events=b2World_GetBodyEvents(worlds[slot].raw);
    if(events.moveCount<0||events.moveCount>65)fail("event capacity");
    extra.moves=events.moveCount;
    for(int j=0;j<events.moveCount;++j)extra.events[j]=events.moveEvents[j];
    if(o->code==32) {
        int dest=(int)a[3];MoveCopy* c=copies+dest;
        c->saved=true;c->count=events.moveCount;
        for(int j=0;j<events.moveCount;++j) {
            b2BodyMoveEvent event=events.moveEvents[j];
            c->moves[j].body=public_body_number(event.bodyId);
            c->moves[j].transform=event.transform;
            c->moves[j].fellAsleep=event.fellAsleep;
            copy_object(c->moves[j].object,event.userData);
        }
        extra.copy=dest;
    }
    return OK;
}

static void transform_words(b2Transform t)
{
    vec(t.p);real(t.q.c);real(t.q.s);
}
static void public8_dump(int id,uint32_t seq)
{
    if(extra.listBody>=0) {
        Shape values[257];int count=0;
        if(!extra.status) {
            b2ShapeId raw[256];count=b2Body_GetShapes(bodies[extra.listBody].raw,raw,256);
            for(int j=0;j<count;++j)values[j]=public_shape_number(raw[j]);
        }
        int phases=!extra.status&&extra.listChange?3:1;
        for(int phase=0;phase<phases;++phase) {
            if(phase==1) {
                if(count>=1)values[count]=values[0];
                if(count>=2){Shape tmp=values[0];values[0]=values[1];values[1]=tmp;}
                if(count)++count;
            }
            if(phase==2) {
                b2ShapeId raw[256];count=b2Body_GetShapes(bodies[extra.listBody].raw,raw,256);
                for(int j=0;j<count;++j)values[j]=public_shape_number(raw[j]);
            }
            printf("QGN %d %"PRIu32" %d",id,seq,phase);word((uint32_t)count);putchar('\n');++extra.qgn;
            for(int j=0;j<count;++j){printf("QG %d %"PRIu32" %d %d",id,seq,phase,j);shape_handle(values[j]);putchar('\n');++extra.qg;}
        }
    }
    if(extra.parentShape>=0) {
        printf("SB %d %"PRIu32,id,seq);word((uint32_t)extra.status);word(!extra.status);
        if(!extra.status)body_handle(public_body_number(b2Shape_GetBody(shapes[extra.parentShape].raw)));
        else for(int j=0;j<9;++j)word(0);
        putchar('\n');extra.sb=1;
    }
    if(extra.k) {
        printf("K %d %"PRIu32" %d",id,seq,extra.world);
        word(extra.dt);word(extra.requested);word((uint32_t)extra.effective);word(extra.didSolve);word((uint32_t)extra.moves);putchar('\n');
        for(int j=0;j<extra.moves;++j) {
            b2BodyMoveEvent e=extra.events[j];
            printf("M %d %"PRIu32" %d %d",id,seq,extra.world,j);
            word((uint32_t)e.bodyId.index1);word(e.bodyId.world0);word(e.bodyId.generation);
            transform_words(e.transform);object(e.userData);word(e.fellAsleep);putchar('\n');
        }
    }
    if(extra.copy>=0) {
        MoveCopy* c=copies+extra.copy;
        printf("MCN %d %"PRIu32" %d",id,seq,extra.copy);word((uint32_t)c->count);putchar('\n');extra.mcn=1;
        for(int j=0;j<c->count;++j) {
            SavedMove e=c->moves[j];
            printf("MC %d %"PRIu32" %d %d",id,seq,extra.copy,j);
            word((uint32_t)(e.body.raw.index1-1));wide(e.body.birth);wide(e.body.owner);
            transform_words(e.transform);for(int k=0;k<3;++k)word(e.object[k]);word(e.fellAsleep);putchar('\n');
        }
        extra.mc=c->count;
    }
}

#if OBS
static void private8_dump(int id,uint32_t seq)
{
    for(int i=0;i<BODIES;++i)if(bodies[i].live) {
        b2BodyId raw=bodies[i].raw;b2World* w=b2GetWorld(raw.world0);
        b2Body* b=b2BodyArray_Get(&w->bodies,raw.index1-1);
        b2BodySim* sim=b2GetBodySim(w,b);
        b2BodyState* state=b2GetBodyState(w,b);
        printf("Y %d %"PRIu32" %d",id,seq,i);
        vec(state?sim->force:b2Vec2_zero);real(state?sim->torque:0);
        vec(state?state->deltaPosition:b2Vec2_zero);
        real(state?state->deltaRotation.c:1);real(state?state->deltaRotation.s:0);
        word(sim->isSpeedCapped);word(b->isSpeedCapped);word((uint32_t)b->bodyMoveIndex);
        word((uint32_t)b->setIndex);word((uint32_t)b->localIndex);
        real(sim->linearDamping);real(sim->angularDamping);real(sim->gravityScale);
        word(sim->allowFastRotation);word(sim->isFast);putchar('\n');
    }
    for(int i=0;i<WORLDS;++i)if(worlds[i].live) {
        b2World* w=b2GetWorldFromId(worlds[i].raw);
        b2SolverSet* awake=b2SolverSetArray_Get(&w->solverSets,b2_awakeSet);
        for(int j=0;j<awake->bodySims.count;++j) {
            b2BodySim* sim=awake->bodySims.data+j;
            b2Body* b=b2BodyArray_Get(&w->bodies,sim->bodyId);
            if(b->localIndex!=j||b->setIndex!=b2_awakeSet)fail("dense body/localIndex");
            printf("DN %d %"PRIu32" %d %d",id,seq,i,j);
            word((uint32_t)(sim->bodyId+1));word(w->worldId);word(b->generation);putchar('\n');
        }
    }
    for(int i=0;i<WORLDS;++i)if(worlds[i].live) {
        b2World* w=b2GetWorldFromId(worlds[i].raw);
        for(int t=0;t<3;++t) {
            b2DynamicTree* tree=w->broadPhase.trees+t;
            printf("RT %d %"PRIu32" %d %d",id,seq,i,t);
            word((uint32_t)tree->root);word((uint32_t)tree->nodeCount);word((uint32_t)tree->nodeCapacity);word((uint32_t)tree->freeList);
            word((uint32_t)b2DynamicTree_GetProxyCount(tree));word((uint32_t)b2DynamicTree_GetHeight(tree));
            real(b2DynamicTree_GetAreaRatio(tree));aabb(b2DynamicTree_GetRootBounds(tree));putchar('\n');
        }
    }
    for(int i=0;i<WORLDS;++i)if(worlds[i].live) {
        b2World* w=b2GetWorldFromId(worlds[i].raw);
        printf("JW %d %"PRIu32" %d",id,seq,i);
        wide(w->stepIndex);real(w->inv_h);word(w->locked);word((uint32_t)w->endEventArrayIndex);
        word((uint32_t)w->bodyMoveEvents.count);word((uint32_t)w->broadPhase.movePairCapacity);
        word((uint32_t)b2AtomicLoadInt(&w->broadPhase.movePairIndex));putchar('\n');
    }
}
#endif

static void execute8(int id,uint32_t seq,const Operation* o)
{
    const uint32_t* a=o->u;int c=(int)o->code,x=(int)a[0],y=(int)a[1];
    if(c==30) {
        if(!worlds[y].saved)fail("unsaved world register");
        if(bodies[x].live)fail("replace live body register");
    } else if(c==37) {
        if(!copies[x].saved)fail("unsaved copy register");
    } else {
        if(!worlds[x].saved)fail("unsaved world register");
        if(((c>=33&&c<=36)||c==38)&&!bodies[y].saved)fail("unsaved body register");
        if(c==39&&!shapes[y].saved)fail("unsaved shape register");
    }
    int status=OK,kind=0,slot=0;
    if(c==30) {
        b2BodyDef d=body_def(a);d.linearDamping=o->f[11];d.angularDamping=o->f[12];d.gravityScale=o->f[13];d.allowFastRotation=a[14]!=0;
        status=world_live(worlds+y)?OK:STALE;
        if(!status&&a[15]&&!valid_body8(&d))status=PARAM;
        if(!status)status=create_body(x,y,d);
        kind=status?0:2;slot=x;
    } else if(c==31||c==32) {
        kind=1;slot=x;status=do_step(id,seq,o);
    } else if(c==37)extra.copy=x;
    else {
        kind=c==39?3:2;slot=y;
        status=c==39?shape_guard(worlds+x,shapes+y):guard(worlds+x,bodies+y);
        bool game=c==34||(c==35&&a[4])||(c==36&&a[3]);
        if(!status&&game) {
            int start=c==34?3:2,end=c==34?6:c==35?3:2;
            for(int j=start;j<=end;++j)if(!isfinite(o->f[j]))status=PARAM;
        }
        if(!status) {
            if(c==33||c==34) {
                b2BodyId b=bodies[y].raw;b2Vec2 v={o->f[3],o->f[4]},p={o->f[5],o->f[6]};bool wake=a[7]!=0;
                if(a[2]==0)b2Body_ApplyForce(b,v,p,wake);
                if(a[2]==1)b2Body_ApplyForceToCenter(b,v,wake);
                if(a[2]==2)b2Body_ApplyTorque(b,o->f[3],wake);
                if(a[2]==3)b2Body_ApplyLinearImpulse(b,v,p,wake);
                if(a[2]==4)b2Body_ApplyLinearImpulseToCenter(b,v,wake);
                if(a[2]==5)b2Body_ApplyAngularImpulse(b,o->f[3],wake);
            }
            if(c==35)b2Body_SetLinearVelocity(bodies[y].raw,(b2Vec2){o->f[2],o->f[3]});
            if(c==36)b2Body_SetAngularVelocity(bodies[y].raw,o->f[2]);
        }
        if(c==38){extra.listBody=y;extra.listChange=(int)a[2];}
        if(c==39)extra.parentShape=y;
    }
    extra.status=status;
    population_after9();echo(id,seq,o);
    result(id,seq,0,status,kind,slot);
#if GUARD8
    if(extra.up){printf("UP %d %"PRIu32,id,seq);pair_member(extra.pairA);pair_member(extra.pairB);putchar('\n');}
#endif
    dump(id,seq,1,0,0,-1);
}

static void dump(int id,uint32_t seq,int nR,uint32_t nJ,int qBody,int capacity)
{
    population_after9();
    uint32_t saved[3]={0},live[3]={0};
    for(int i=0;i<WORLDS;++i)if(worlds[i].saved){++saved[0];
        printf("V %d %"PRIu32" 1 %d",id,seq,i);
        word(b2World_IsValid(worlds[i].raw));
        word(world_live(worlds+i));
        putchar('\n');
        }
    for(int i=0;i<BODIES;++i)if(bodies[i].saved){++saved[1];
        printf("V %d %"PRIu32" 2 %d",id,seq,i);
        word(b2Body_IsValid(bodies[i].raw));
        word(body_live(bodies+i));
        putchar('\n');
        }
    for(int i=0;i<SHAPES;++i)if(shapes[i].saved){++saved[2];
        printf("V %d %"PRIu32" 3 %d",id,seq,i);
        word(b2Shape_IsValid(shapes[i].raw));
        word(shape_live(shapes+i));
        putchar('\n');
        }
    for(int i=0;i<WORLDS;++i)if(worlds[i].live) {
        ++live[0];
        World w=worlds[i];
        if(!world_live(&w))fail("live world invalid");
        printf("W %d %"PRIu32" %d",id,seq,i);
        world_raw(w);
        wide(w.birth);
        vec(b2World_GetGravity(w.raw));
        real(b2World_GetMaximumLinearSpeed(w.raw));
        b2Counters c=b2World_GetCounters(w.raw);
        word((uint32_t)c.bodyCount);
        word((uint32_t)c.shapeCount);
        word((uint32_t)c.islandCount);
        putchar('\n');
    }
    for(int i=0;i<BODIES;++i)if(bodies[i].live) {
        ++live[1];
        Body b=bodies[i];
        if(!body_live(&b))fail("live body invalid");
        printf("B %d %"PRIu32" %d",id,seq,i);
        body_handle(b);
        word((uint32_t)b2Body_GetType(b.raw));
        vec(b2Body_GetPosition(b.raw));
        b2Rot q=b2Body_GetRotation(b.raw);
        real(q.c);
        real(q.s);
        vec(b2Body_GetWorldCenterOfMass(b.raw));
        vec(b2Body_GetLinearVelocity(b.raw));
        real(b2Body_GetAngularVelocity(b.raw));
        real(b2Body_GetMass(b.raw));
        real(b2Body_GetRotationalInertia(b.raw));
        vec(b2Body_GetLocalCenterOfMass(b.raw));
        word((uint32_t)b2Body_GetShapeCount(b.raw));
        word(b2Body_IsAwake(b.raw));
        word(b2Body_IsEnabled(b.raw));
        word(b2Body_IsFixedRotation(b.raw));
        object(b2Body_GetUserData(b.raw));
        putchar('\n');
    }
    for(int i=0;i<SHAPES;++i)if(shapes[i].live) {
        ++live[2];
        Shape s=shapes[i];
        if(!shape_live(&s))fail("live shape invalid");
        printf("S %d %"PRIu32" %d",id,seq,i);
        shape_handle(s);
        b2BodyId b=b2Shape_GetBody(s.raw);
        b2WorldId w=b2Shape_GetWorld(s.raw);
        word((uint32_t)b.index1);
        word(b.world0);
        word(b.generation);
        word(w.index1);
        word(0);
        word(w.generation);
        word((uint32_t)b2Shape_GetType(s.raw));
        real(b2Shape_GetDensity(s.raw));
        b2SurfaceMaterial m=b2Shape_GetSurfaceMaterial(s.raw);
        real(m.friction);
        real(m.restitution);
        real(m.rollingResistance);
        real(m.tangentSpeed);
        word((uint32_t)m.userMaterialId);
        word(m.customColor);
        b2Filter f=b2Shape_GetFilter(s.raw);
        wide(f.categoryBits);
        wide(f.maskBits);
        word((uint32_t)f.groupIndex);
        word(b2Shape_IsSensor(s.raw));
        mass(b2Shape_GetMassData(s.raw));
        aabb(b2Shape_GetAABB(s.raw));
        object(b2Shape_GetUserData(s.raw));
        putchar('\n');
    }
    for(int i=0;i<SHAPES;++i)if(shapes[i].live){printf("G %d %"PRIu32" %d",id,seq,i);
        geometry_dump(shapes[i].raw);
        putchar('\n');
        }
    for(int i=0;i<BODIES;++i)if(bodies[i].live) {
        b2ShapeId list[256];
        int expected=b2Body_GetShapeCount(bodies[i].raw);
        if(expected>256)fail("GetShapes capacity");
        int count=b2Body_GetShapes(bodies[i].raw,list,256);
        if(count!=expected)fail("GetShapes count");
        printf("L %d %"PRIu32" %d",id,seq,i);
        word((uint32_t)count);
        for(int j=0;j<count;++j){word((uint32_t)list[j].index1);
            word(list[j].world0);
            word(list[j].generation);
            }putchar('\n');
        printf("A %d %"PRIu32" %d",id,seq,i);
        aabb(b2Body_ComputeAABB(bodies[i].raw));
        putchar('\n');
    }
    if(capacity>=0) {
        b2ShapeId list[256];
        int count=b2Body_GetShapes(bodies[qBody].raw,capacity?list:NULL,capacity);
        printf("Q %d %"PRIu32" %d",id,seq,qBody);
        word((uint32_t)capacity);
        word((uint32_t)count);
        for(int j=0;j<count;++j){word((uint32_t)list[j].index1);
            word(list[j].world0);
            word(list[j].generation);
            }putchar('\n');
    }
    public8_dump(id,seq);
    public9_dump(id,seq);
#if OBS
    uint32_t nu=0;
    for(int i=0;i<BODIES;++i)if(bodies[i].live) {
        b2BodyId idb=bodies[i].raw;
        b2World* w=b2GetWorld(idb.world0);
        b2Body* b=b2BodyArray_Get(&w->bodies,idb.index1-1);
        b2BodySim* sim=b2GetBodySim(w,b);
        printf("X %d %"PRIu32" %d",id,seq,i);
        real(sim->invMass);
        real(sim->invInertia);
        real(sim->minExtent);
        real(sim->maxExtent);
        vec(sim->center0);
        real(sim->rotation0.c);
        real(sim->rotation0.s);
        putchar('\n');
    }
    for(int i=0;i<SHAPES;++i)if(shapes[i].live) {
        b2ShapeId ids=shapes[i].raw;
        b2World* w=b2GetWorld(ids.world0);
        b2Shape* s=b2ShapeArray_Get(&w->shapes,ids.index1-1);
        printf("P %d %"PRIu32" %d",id,seq,i);
        word((uint32_t)s->id);
        word((uint32_t)s->bodyId);
        word((uint32_t)s->prevShapeId);
        word((uint32_t)s->nextShapeId);
        word((uint32_t)s->proxyKey);
        vec(s->localCentroid);
        aabb(s->fatAABB);
        word(s->enlargedAABB);
        putchar('\n');
    }
    for(int i=0;i<SHAPES;++i)if(shapes[i].live) {
        b2ShapeId ids=shapes[i].raw;
        b2World* w=b2GetWorld(ids.world0);
        b2Shape* s=b2ShapeArray_Get(&w->shapes,ids.index1-1);
        if(s->proxyKey!=-1) {
            int type=B2_PROXY_TYPE(s->proxyKey),proxy=B2_PROXY_ID(s->proxyKey);
            b2DynamicTree* tree=w->broadPhase.trees+type;
            printf("T %d %"PRIu32" %d",id,seq,i);
            word((uint32_t)type);
            word((uint32_t)proxy);
            aabb(b2DynamicTree_GetAABB(tree,proxy));
            wide(b2DynamicTree_GetCategoryBits(tree,proxy));
            wide(b2DynamicTree_GetUserData(tree,proxy));
            putchar('\n');
        }
    }
    for(int i=0;i<WORLDS;++i)if(worlds[i].live) {
        b2World* w=b2GetWorldFromId(worlds[i].raw);
        b2BroadPhase* bp=&w->broadPhase;
        printf("F %d %"PRIu32" %d",id,seq,i);
        word((uint32_t)bp->moveArray.count);
        for(int t=0;t<3;++t)word((uint32_t)b2DynamicTree_GetProxyCount(bp->trees+t));
        word(bp->pairSet.count);
        putchar('\n');
        for(int j=0;j<bp->moveArray.count;++j){printf("U %d %"PRIu32" %d %d",id,seq,i,j);
            word((uint32_t)bp->moveArray.data[j]);
            putchar('\n');
            ++nu;
            }
        for(int k=0;k<2;++k) {
            b2HashSet* set=k?&bp->pairSet:&bp->moveSet;
            printf("H %d %"PRIu32" %d %d",id,seq,i,k);
            word(set->capacity);
            word(set->count);
            for(uint32_t j=0;j<set->capacity;++j){wide(set->items[j].key);
                word(set->items[j].hash);
                }putchar('\n');
        }
    }
    private8_dump(id,seq);
    private9_dump(id,seq);
    printf("I8 %d %"PRIu32,id,seq);
    word(live[1]);
    word(live[2]);
    word(live[2]);
    word(live[0]);
    word(nu);
    word(2*live[0]);
    word(live[1]);
    uint32_t awake=0;
    for(int i=0;i<WORLDS;++i)if(worlds[i].live)awake+=(uint32_t)b2SolverSetArray_Get(&b2GetWorldFromId(worlds[i].raw)->solverSets,b2_awakeSet)->bodySims.count;
    word(awake);
    word(3*live[0]);
    word(live[0]);
    putchar('\n');
    printf("I9 %d %"PRIu32,id,seq);for(int k=0;k<19;++k)word(priv9[k]);word(seq);putchar('\n');
#endif
    printf("Z8 %d %"PRIu32,id,seq);
    for(int i=0;i<3;++i)word(saved[i]);
    for(int i=0;i<3;++i)word(live[i]);
    word(1);
    word((uint32_t)nR);
    word(extra.up);
    word(saved[0]+saved[1]+saved[2]);
    word(live[0]);
    word(live[1]);
    word(live[2]);
    word(live[2]);
    word(live[1]);
    word(live[1]);
    word(capacity>=0);
    (void)nJ;
    word(extra.k);word(extra.moves);word(extra.mcn);word(extra.mc);
    word(extra.qgn);word(extra.qg);word(extra.sb);
    wide(lastIssued);
    putchar('\n');
    counts9_dump(id,seq);

}
static void result(int id,uint32_t seq,int index,int status,int kind,int slot)
{
    printf("R %d %"PRIu32" %d %d %d",id,seq,index,status,kind);
    if(kind==1)world_handle(worlds[slot]);
    else if(kind==2)body_handle(bodies[slot]);
    else if(kind==3)shape_handle(shapes[slot]);
    else for(int i=0;i<9;++i)word(0);
    putchar('\n');
}
static void execute(int id,uint32_t seq,const Operation* o)
{
    const uint32_t* a=o->u;
    int x=(int)a[0],y=(int)a[1],code=(int)o->code;
    int owner=(code==2||code==30)?y:code==16?(int)a[2]:(code==10||code==17)?y:x;
    memset(&extra,0,sizeof(extra));
    extra.copy=-1;
    extra.listBody=-1;
    extra.parentShape=-1;
    if(code>=30){execute8(id,seq,o);return;}
    if(code==0){if(worlds[x].live)fail("replace live world register");
        }
    else if(!worlds[owner].saved)fail("unsaved world register");
    if((code==2||code==16)&&bodies[x].live)fail("replace live body register");
    if((code==3||code==4||code==5||code==13||code==20||code==21)&&!bodies[y].saved)fail("unsaved body register");
    if((code==10||code==17)&&(!bodies[a[2]].saved||shapes[x].live))fail("shape registers");
    if(code==16&&shapes[y].live)fail("replace live shape register");
    if((code==11||code==12||code==14||code==18||code==19)&&!shapes[y].saved)fail("unsaved shape register");
    if(code==15&&((a[1]==2&&!bodies[a[2]].saved)||(a[1]==3&&!shapes[a[2]].saved)))fail("unsaved object register");
    int status=OK,kind=0,slot=0,nR=1,capacity=-1,qBody=0;
    uint32_t nJ=0;
    switch(code) {
        case 0:status=create_world(x,world_def(o));
        kind=status?0:1;
        slot=x;
        break;
        case 1:status=world_live(worlds+x)?OK:STALE;
        kind=1;
        slot=x;
        if(!status)destroy_world(x);
        break;
        case 2:status=create_body(x,y,body_def(a));
        kind=status?0:2;
        slot=x;
        break;
        case 3:case 4:case 5:case 13:case 21:
            kind=2;
        slot=y;
        status=guard(worlds+x,bodies+y);
            if(!status) {
                if(code==3)destroy_body(y);
                if(code==4)b2Body_SetTransform(bodies[y].raw,(b2Vec2){o->f[2],o->f[3]},(b2Rot){o->f[4],o->f[5]});
                if(code==13)b2Body_ApplyMassFromShapes(bodies[y].raw);
                if(code==21){qBody=y;
                capacity=(int)a[2];
                }
            }break;
        case 10:case 17:status=create_shape(x,y,(int)a[2],a,code==17);
        kind=status?0:3;
        slot=x;
        break;
        case 11:case 12:case 14:case 18:case 19: {
            kind=3;
            slot=y;
            status=shape_guard(worlds+x,shapes+y);
            if(!status) {
                b2BodyId b=b2Shape_GetBody(shapes[y].raw);
                if(code==18||code==19) {
                    if(!preflight(b,NULL,NULL,0,shapes[y].raw,code==18,o->f[2])){status=GEOMETRY;
                        break;
                        }
                }
                if(code==11||code==18){b2DestroyShape(shapes[y].raw,code==18||a[2]!=0);
                    shapes[y].live=false;
                    }
                if(code==12)b2Shape_SetDensity(shapes[y].raw,o->f[2],a[3]!=0);
                if(code==19){b2Shape_SetDensity(shapes[y].raw,o->f[2],false);
                    b2Body_ApplyMassFromShapes(b);
                    }
            }break;
        }
        case 15:
            kind=(int)a[1];
        slot=(int)a[2];
        status=kind==2?guard(worlds+x,bodies+slot):shape_guard(worlds+x,shapes+slot);
            if(!status) {void* t=token(a[3],a[4],a[5]);
            if(kind==2)b2Body_SetUserData(bodies[slot].raw,t);
            else b2Shape_SetUserData(shapes[slot].raw,t);
            }break;
        case 16:
            status=create_pair(a);
        nR=2;
        break;

    }
    population_after9();echo(id,seq,o);
    if(nR==2){result(id,seq,0,status,status?0:2,x);result(id,seq,1,status,status?0:3,y);}
    else result(id,seq,0,status,kind,slot);
    dump(id,seq,nR,nJ,qBody,capacity);
}

int main(int argc,char** argv)
{
#ifdef BITSET9_HELPER
    return bitset_helper9();
#endif
    if(argc!=2)fail("INPUT_DOMAIN");FILE* input=fopen(argv[1],"rb");if(!input)fail("INPUT_DOMAIN");
    char* p=row(input);if(strncmp(p,"PORT9B ",7))fail("INPUT_TAG");p+=7;
    uint32_t count=decimal(&p);if(*p)fail("INPUT_ARITY");if(count<1||count>64)fail("INPUT_N");
    printf("PORT9B %"PRIu32"\n",count);
    for(int id=1;id<=(int)count;++id){
        memset(worlds,0,sizeof(worlds));memset(bodies,0,sizeof(bodies));memset(shapes,0,sizeof(shapes));memset(copies,0,sizeof(copies));
        memset(saved9,0,sizeof(saved9));memset(copies9,0,sizeof(copies9));memset(meta9,0,sizeof(meta9));phase9=0;phaseOwner9=-1;
        memset(history9,0,sizeof(history9));
        p=row(input);if(strncmp(p,"C ",2))fail("INPUT_TAG");p+=2;
        uint32_t cid=decimal(&p);space(&p);uint32_t ops=decimal(&p);if(*p)fail("INPUT_ARITY");if(cid!=(uint32_t)id)fail("INPUT_ID");
        uint32_t maximum=GUARD9?16:(id<=4?64:id>=49&&id<=52?256:128);if(!ops||ops>maximum)fail("INPUT_OPCOUNT");
        printf("CASE %d %"PRIu32"\n",id,ops);
        for(uint32_t seq=1;seq<=ops;++seq){
            reset_operation9(id,seq,0);begin_output9();Operation o=read_operation(input,seq);opcode9=o.code;
#ifdef SEED9_SEQ
            if(seq==SEED9_SEQ)lastIssued=SEED9_LAST;
#endif
            phase_check9(&o);population9(&o);
#ifdef HELPER9
            if(o.code==47){helper9(&o);commit_output9();return 0;}
#endif
            if(o.code>=40)execute9(id,seq,&o);else execute(id,seq,&o);
            commit_output9();
#ifdef STOP9_SEQ
            if(seq==STOP9_SEQ){puts("GUARD9 BATCH");return 0;}
#endif
        }
        if(phase9)fail("INPUT_CAPTURE_UNCLOSED");printf("ENDCASE %d\n",id);
        for(int i=0;i<WORLDS;++i)if(worlds[i].live)destroy_world(i);
    }
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input)||fclose(input))fail("INPUT_DOMAIN");
    printf("END %"PRIu32"\n",count);free_tokens();return (ferror(stdout)||fflush(stdout))?2:0;
}
