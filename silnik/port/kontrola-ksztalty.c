                                          
                               
                                                                                  
   
                                                                      
                                                                              
#include <box2d/box2d.h>
#ifndef OBS
#define OBS 1
#endif
#if OBS
#include "world.h"
#include "body.h"
#include "shape.h"
#include "broad_phase.h"
_Static_assert(B2_VALIDATE == 0, "Release validation configuration");
#endif
#if !defined(NDEBUG) || defined(B2_ENABLE_ASSERT)
#error PORT7 requires Release / NDEBUG without B2_ENABLE_ASSERT
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

enum { CASES = 64, WORLDS = 16, BODIES = 256, SHAPES = 512, GEOMETRY = 4, OK = 0, STALE = 1, FOREIGN = 2, LIMIT = 3 };
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
static World worlds[WORLDS];
static Body bodies[BODIES];
typedef struct Shape { bool saved, live;
    b2ShapeId raw;
    uint64_t owner, birth;
    } Shape;
static Shape shapes[SHAPES];
static uint64_t lastIssued;

static void fail(const char* message) { fprintf(stderr, "PORT7: %s\n", message);
    exit(2);
    }
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

                                                                                 
static char line[2048];
static char* row(FILE* file)
{
    size_t n = 0;
    int c;
    while ((c = fgetc(file)) != EOF && c != '\n') {
        if (c == 0 || c > 127 || n == sizeof(line)-1) fail("ASCII / line length");
        line[n++] = (char)c;
    }
    if (ferror(file) || (c == EOF && n == 0)) fail("truncated input / read error");
    if (n && line[n-1] == '\r' && c == '\n') --n;
    line[n] = 0;
    if (strchr(line, '\r') || !n) fail("line ending / length");
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
    if (!s->saved || !s->live) return false;
    for (int i = 0; i < WORLDS; ++i)
        if (worlds[i].birth == s->owner && world_live(worlds+i)) return b2Shape_IsValid(s->raw);
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
    d.isSensor=false;
    d.enableSensorEvents=false;
    d.enableContactEvents=false;
    d.enableHitEvents=false;
    d.enablePreSolveEvents=false;
    d.userData=NULL;
    return d;
}
static int create_shape(int slot, int owner, int parent, const uint32_t* a, bool game)
{
    int status=guard(worlds+owner,bodies+parent);
    if(status) return status;
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
static Operation read_operation(FILE* file,uint32_t seq)
{
    char* p=row(file);
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
        case 20:used=5;
        break;
        default:fail("opcode");
    }
    for(int i=0;i<64;++i) {space(&p);
        o.u[i]=hex_word(&p);
        o.f[i]=from_bits(o.u[i]);
        if(i>=used && o.u[i])fail("unused");
        }
    if(*p)fail("extra operation tokens");
    uint32_t* a=o.u;
    bool isFloat[64]={false},isBool[64]={false};
    int rot=-1;
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
static void trace(int id,uint32_t seq,uint32_t j,int phase,int slot,int old,int parent,int owner)
{
    printf("J %d %"PRIu32" %"PRIu32" %d",id,seq,j,phase);
    shape_handle(shapes[slot]);
    word(b2Shape_IsValid(shapes[old].raw));
    word(shape_live(shapes+old));
    word((uint32_t)b2World_GetCounters(worlds[owner].raw).shapeCount);
    word((uint32_t)b2Body_GetShapeCount(bodies[parent].raw));
    mass(b2Body_GetMassData(bodies[parent].raw));
    putchar('\n');
}
static void dump(int id,uint32_t seq,int nR,uint32_t nJ,int qBody,int capacity)
{
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
    printf("I %d %"PRIu32,id,seq);
    word(live[1]);
    word(live[2]);
    word(live[2]);
    word(live[0]);
    word(nu);
    word(2*live[0]);
    putchar('\n');
#endif
    printf("Z %d %"PRIu32,id,seq);
    for(int i=0;i<3;++i)word(saved[i]);
    for(int i=0;i<3;++i)word(live[i]);
    word(1);
    word((uint32_t)nR);
    word(saved[0]+saved[1]+saved[2]);
    word(live[0]);
    word(live[1]);
    word(live[2]);
    word(live[2]);
    word(live[1]);
    word(live[1]);
    word(capacity>=0);
    word(nJ);
    wide(lastIssued);
    putchar('\n');
    if(live[0]>4||live[1]>128||live[2]>256)fail("corpus live limits");
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
    int owner=code==2?y:code==16?(int)a[2]:(code==10||code==17)?y:x;
    if(code==0){if(worlds[x].live)fail("replace live world register");
        }
    else if(!worlds[owner].saved)fail("unsaved world register");
    if((code==2||code==16)&&bodies[x].live)fail("replace live body register");
    if((code==3||code==4||code==5||code==13||code==20||code==21)&&!bodies[y].saved)fail("unsaved body register");
    if((code==10||code==17)&&(!bodies[a[2]].saved||shapes[x].live))fail("shape registers");
    if(code==16&&shapes[y].live)fail("replace live shape register");
    if((code==11||code==12||code==14||code==18||code==19)&&!shapes[y].saved)fail("unsaved shape register");
    if(code==15&&((a[1]==2&&!bodies[a[2]].saved)||(a[1]==3&&!shapes[a[2]].saved)))fail("unsaved object register");
    echo(id,seq,o);
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
        result(id,seq,0,status,status?0:2,x);
        result(id,seq,1,status,status?0:3,y);
        break;
        case 20: {
            int temp=(int)a[2],old=(int)a[4];
            status=guard(worlds+x,bodies+y);
            if(status||shapes[temp].live||!shapes[old].saved||shape_live(shapes+old)||shapes[old].owner!=worlds[x].birth)fail("CHURN lifecycle");
            uint32_t sa[64]={0};
            sa[0]=(uint32_t)temp;
            sa[1]=(uint32_t)x;
            sa[2]=(uint32_t)y;
            sa[4]=to_bits(1);
            sa[5]=1;
            sa[6]=1;
            sa[7]=1;
            sa[9]=UINT32_MAX;
            sa[10]=UINT32_MAX;
            sa[17]=to_bits(.5f);
            for(uint32_t j=1;j<=a[3];++j) {
                if(j>1){b2DestroyShape(shapes[temp].raw,true);
                    shapes[temp].live=false;
                    trace(id,seq,j,0,temp,old,y,x);
                    ++nJ;
                    }
                status=create_shape(temp,x,y,sa,false);
                if(status)fail("CHURN creation");
                trace(id,seq,j,1,temp,old,y,x);
                ++nJ;
            }
            kind=3;
            slot=temp;
            break;
        }
    }
    if(nR==1)result(id,seq,0,status,kind,slot);
    dump(id,seq,nR,nJ,qBody,capacity);
}
static int test_tickets(void)
{
    b2WorldDef wd=b2DefaultWorldDef();
    wd.enableSleep=false;
    wd.enableContinuous=false;
    b2BodyDef bd=b2DefaultBodyDef();
    bd.type=b2_dynamicBody;
    bd.enableSleep=false;
    if(create_world(0,wd)||create_body(0,0,bd))return 2;
    uint32_t sa[64]={0};
    sa[4]=to_bits(1);
    sa[5]=1;
    sa[6]=1;
    sa[7]=1;
    sa[9]=UINT32_MAX;
    sa[10]=UINT32_MAX;
    sa[17]=to_bits(.5f);
    lastIssued=UINT64_C(0xffffffff);
    if(create_shape(0,0,0,sa,true)||shapes[0].birth!=UINT64_C(0x100000000))return 2;
    b2DestroyShape(shapes[0].raw,true);
    shapes[0].live=false;
    lastIssued=UINT64_MAX-1;
    if(create_shape(1,0,0,sa,true)||shapes[1].birth!=UINT64_MAX)return 2;
    Shape history=shapes[0];
    int before=b2World_GetCounters(worlds[0].raw).shapeCount;
    if(create_shape(0,0,0,sa,true)!=LIMIT||(history.saved!=shapes[0].saved || history.live!=shapes[0].live || history.owner!=shapes[0].owner || history.birth!=shapes[0].birth || b2StoreShapeId(history.raw)!=b2StoreShapeId(shapes[0].raw))||lastIssued!=UINT64_MAX||b2World_GetCounters(worlds[0].raw).shapeCount!=before)return 2;
    uint32_t pa[64]={0};
    pa[0]=1;
    pa[1]=2;
    pa[3]=2;
    pa[6]=to_bits(1);
    pa[13]=to_bits(1);
    pa[14]=1;
    pa[18]=1;
    pa[20]=UINT32_MAX;
    pa[21]=UINT32_MAX;
    pa[25]=to_bits(.5f);
    lastIssued=UINT64_MAX-1;
    if(create_pair(pa)!=LIMIT||bodies[1].saved||shapes[2].saved||lastIssued!=UINT64_MAX-1||b2World_GetCounters(worlds[0].raw).bodyCount!=1)return 2;
    lastIssued=UINT64_MAX-2;
    pa[23]=to_bits(16384);
    if(create_pair(pa)!=GEOMETRY||bodies[1].saved||shapes[2].saved||lastIssued!=UINT64_MAX-2)return 2;
    pa[23]=0;
    if(create_pair(pa)||bodies[1].birth!=UINT64_MAX-1||shapes[2].birth!=UINT64_MAX||lastIssued!=UINT64_MAX)return 2;
    destroy_world(0);
    memset(worlds,0,sizeof(worlds));
    memset(bodies,0,sizeof(bodies));
    memset(shapes,0,sizeof(shapes));
    lastIssued=UINT64_C(0xfffffffe);
    if(create_world(0,wd)||worlds[0].birth!=UINT64_C(0xffffffff)||create_body(0,0,bd)||bodies[0].birth!=UINT64_C(0x100000000)||create_shape(0,0,0,sa,true)||shapes[0].birth!=UINT64_C(0x100000001))return 2;
    destroy_world(0);
    free_tokens();
    puts("BILETY OK");
    return 0;
}
int main(int argc,char** argv)
{
    if(argc==2&&strcmp(argv[1],"--test-tickets")==0)return test_tickets();
    if(argc!=2){fputs("usage: kontrola-ksztalty input | --test-tickets\n",stderr);
        return 2;
        }
    FILE* input=fopen(argv[1],"rb");
    if(!input){perror(argv[1]);
        return 2;
        }
    char* p=row(input);
    uint32_t count=decimal(&p);
    if(!count||count>96||*p)fail("N");
    printf("PORT7 %"PRIu32"\n",count);
    for(int id=1;id<=(int)count;++id) {
        memset(worlds,0,sizeof(worlds));
        memset(bodies,0,sizeof(bodies));
        memset(shapes,0,sizeof(shapes));
        p=row(input);
        if(*p++!='C')fail("C tag");
        space(&p);
        if(decimal(&p)!=(uint32_t)id)fail("case id");
        space(&p);
        uint32_t ops=decimal(&p);
        if(!ops||ops>512||*p)fail("opCount");
        printf("CASE %d %"PRIu32"\n",id,ops);
        for(uint32_t seq=1;seq<=ops;++seq){Operation o=read_operation(input,seq);
            execute(id,seq,&o);
            }
        printf("ENDCASE %d\n",id);
        for(int i=0;i<WORLDS;++i)if(worlds[i].live)destroy_world(i);
    }
    if(fgetc(input)!=EOF||ferror(input))fail("extra input / read error");
    if(fclose(input))fail("input close error");
    printf("END %"PRIu32"\n",count);
    free_tokens();
    return (ferror(stdout)||fflush(stdout))?2:0;
}
