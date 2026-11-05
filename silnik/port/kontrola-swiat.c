                                                                      
                                                                              
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

enum { CASES = 64, WORLDS = 16, BODIES = 256, OK = 0, STALE = 1, FOREIGN = 2, LIMIT = 3 };
_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "IEEE binary32 required");
_Static_assert(CHAR_BIT == 8 && sizeof(int) == 4, "32-bit int required");
typedef struct World { bool saved, live; b2WorldId raw; uint64_t birth; } World;
typedef struct Body { bool saved, live; b2BodyId raw; uint64_t owner, birth; } Body;
typedef struct Operation { uint32_t code, u[24]; float f[24]; } Operation;
static World worlds[WORLDS];
static Body bodies[BODIES];
static uint64_t lastIssued;

static void fail(const char* message) { fprintf(stderr, "PORT6: %s\n", message); exit(2); }
static float from_bits(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }
static uint32_t to_bits(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
static void word(uint32_t u) { printf(" %08" PRIx32, u); }
static void wide(uint64_t u) { word((uint32_t)u); word((uint32_t)(u >> 32)); }
static void real(float f) { word(to_bits(f)); }
static void vec(b2Vec2 v) { real(v.x); real(v.y); }
static void world_raw(World w) { word(w.raw.index1); word(0); word(w.raw.generation); word(b2StoreWorldId(w.raw)); word(0); }
static void body_raw(Body b) { word((uint32_t)b.raw.index1); word(b.raw.world0); word(b.raw.generation); wide(b2StoreBodyId(b.raw)); }
static void world_handle(World w) { world_raw(w); wide(0); wide(w.birth); }
static void body_handle(Body b) { body_raw(b); wide(b.owner); wide(b.birth); }

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
    for (int i = 0; i < BODIES; ++i)
        if (bodies[i].owner == w->birth) bodies[i].live = false;
}
static void destroy_body(int slot) { b2DestroyBody(bodies[slot].raw); bodies[slot].live = false; }

                                                                                 
static char line[512];
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
static void space(char** p) { if (*(*p)++ != ' ') fail("single space required"); }
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
static bool float_field(uint32_t code, int i)
{
    return (code == 0 && i >= 1 && i <= 3) || (code == 2 && i >= 3 && i <= 9)
        || (code == 4 && i >= 2 && i <= 5);
}
static b2WorldDef world_def(const Operation* o)
{
    b2WorldDef d = b2DefaultWorldDef();
    d.gravity = (b2Vec2){o->f[1], o->f[2]}; d.maximumLinearSpeed = o->f[3];
    d.enableSleep = false; d.enableContinuous = false; d.workerCount = 1;
    return d;
}
static b2BodyDef body_def(const Operation* o)
{
    b2BodyDef d = b2DefaultBodyDef();
    d.type = (b2BodyType)o->u[2]; d.position = (b2Vec2){o->f[3], o->f[4]};
    d.rotation = (b2Rot){o->f[5], o->f[6]}; d.linearVelocity = (b2Vec2){o->f[7], o->f[8]};
    d.angularVelocity = o->f[9]; d.fixedRotation = o->u[10] != 0;
    d.linearDamping = 0; d.angularDamping = 0; d.gravityScale = 1;
    d.enableSleep = false; d.isAwake = true; d.isEnabled = true;
    d.isBullet = false; d.allowFastRotation = false; d.name = NULL; d.userData = NULL;
    return d;
}
static Operation read_operation(FILE* file, uint32_t seq)
{
    char* p = row(file);
    if (*p++ != 'O') fail("O tag");
    space(&p);
    if (decimal(&p) != seq) fail("seq");
    space(&p);
    Operation o = {0}; o.code = decimal(&p);
    if (o.code > 6) fail("opcode");
    static const int used[] = {4, 1, 11, 2, 6, 2, 4};
    for (int i = 0; i < 24; ++i) {
        space(&p); uint32_t u = hex_word(&p);
        if (i >= used[o.code] && u) fail("nonzero unused word");
        if (float_field(o.code, i)) {
            o.f[i] = from_bits(u);
            if (!isfinite(o.f[i])) fail("NaN / Inf");
        } else o.u[i] = u;
    }
    if (*p) fail("extra operation tokens");
    if (o.code == 0) {
        if (o.u[0] >= WORLDS || !(o.f[3] > 0)) fail("world definition");
    } else if (o.code == 2) {
        if (o.u[0] >= BODIES || o.u[1] >= WORLDS || o.u[2] > 2 || o.u[10] > 1) fail("body definition");
    } else if (o.u[0] >= WORLDS || (o.code != 1 && o.u[1] >= BODIES)) fail("register range");
    if (o.code == 2 || o.code == 4) {
        int i = o.code == 2 ? 5 : 4;
        if (!b2IsNormalizedRot((b2Rot){o.f[i], o.f[i+1]})) fail("rotation");
    }
    if (o.code == 6 && (!o.u[2] || o.u[2] > 65536 || o.u[3] >= BODIES || o.u[1] == o.u[3]))
        fail("CHURN arguments");
    return o;
}
static void echo(int id, uint32_t seq, const Operation* o)
{
    printf("E %d %" PRIu32 " %" PRIu32, id, seq, o->code);
    for (int i = 0; i < 24; ++i) word(float_field(o->code, i) ? to_bits(o->f[i]) : o->u[i]);
    putchar('\n');
}
static void trace(int id, uint32_t seq, uint32_t j, int phase, int slot, int old, int owner)
{
    printf("J %d %" PRIu32 " %" PRIu32 " %d", id, seq, j, phase); body_handle(bodies[slot]);
    word(b2Body_IsValid(bodies[old].raw)); word(body_live(bodies+old));
    b2Counters c = b2World_GetCounters(worlds[owner].raw);
    word((uint32_t)c.bodyCount); word((uint32_t)c.islandCount); putchar('\n');
}
static void dump(int id, uint32_t seq)
{
    uint32_t savedW = 0, savedB = 0, liveW = 0, liveB = 0;
    for (int i = 0; i < WORLDS; ++i) if (worlds[i].saved) {
        ++savedW;
        printf("V %d %" PRIu32 " 1 %d", id, seq, i);
        word(b2World_IsValid(worlds[i].raw)); word(world_live(worlds+i)); putchar('\n');
    }
    for (int i = 0; i < BODIES; ++i) if (bodies[i].saved) {
        ++savedB;
        printf("V %d %" PRIu32 " 2 %d", id, seq, i);
        word(b2Body_IsValid(bodies[i].raw)); word(body_live(bodies+i)); putchar('\n');
    }
    for (int i = 0; i < WORLDS; ++i) if (worlds[i].live) {
        World w = worlds[i];
        if (!world_live(&w)) fail("live world invalid");
        ++liveW;
        printf("W %d %" PRIu32 " %d", id, seq, i); world_raw(w); wide(w.birth);
        vec(b2World_GetGravity(w.raw)); real(b2World_GetMaximumLinearSpeed(w.raw));
        b2Counters c = b2World_GetCounters(w.raw);
        word((uint32_t)c.bodyCount); word((uint32_t)c.shapeCount); word((uint32_t)c.islandCount); putchar('\n');
    }
    for (int i = 0; i < BODIES; ++i) if (bodies[i].live) {
        Body b = bodies[i];
        if (!body_live(&b)) fail("live body invalid");
        ++liveB;
        printf("B %d %" PRIu32 " %d", id, seq, i); body_handle(b);
        word((uint32_t)b2Body_GetType(b.raw)); vec(b2Body_GetPosition(b.raw));
        b2Rot q = b2Body_GetRotation(b.raw); real(q.c); real(q.s);
        vec(b2Body_GetWorldCenterOfMass(b.raw)); vec(b2Body_GetLinearVelocity(b.raw));
        real(b2Body_GetAngularVelocity(b.raw)); real(b2Body_GetMass(b.raw)); real(b2Body_GetRotationalInertia(b.raw));
        vec(b2Body_GetLocalCenterOfMass(b.raw)); word((uint32_t)b2Body_GetShapeCount(b.raw));
        word(b2Body_IsAwake(b.raw)); word(b2Body_IsEnabled(b.raw)); word(b2Body_IsFixedRotation(b.raw)); putchar('\n');
    }
    printf("Z %d %" PRIu32, id, seq);
    word(savedW); word(savedB); word(liveW); word(liveB); word(savedW+savedB); word(liveW); word(liveB); putchar('\n');
}
static void execute(int id, uint32_t seq, const Operation* o)
{
    uint32_t x = o->u[0], y = o->u[1];
    int owner = o->code == 2 ? (int)y : (int)x;
    if (o->code == 0) {
        if (worlds[x].live) fail("replace live world register");
    } else if (!worlds[owner].saved) fail("unsaved world register");
    if (o->code == 2 && bodies[x].live) fail("replace live body register");
    if ((o->code == 3 || o->code == 4 || o->code == 5) && !bodies[y].saved) fail("unsaved body register");
    if (o->code == 6 && (!world_live(worlds+owner) || bodies[y].live || !bodies[o->u[3]].saved
        || body_live(bodies+o->u[3]) || bodies[o->u[3]].owner != worlds[owner].birth)) fail("CHURN lifecycle");
    echo(id, seq, o);
    int status = OK, kind = 0;
    switch (o->code) {
        case 0: status = create_world((int)x, world_def(o)); kind = status == OK ? 1 : 0; break;
        case 1:
            kind = 1; status = world_live(worlds+x) ? OK : STALE;
            if (status == OK) destroy_world((int)x);
            break;
        case 2: status = create_body((int)x, (int)y, body_def(o)); kind = status == OK ? 2 : 0; break;
        case 3: case 4: case 5:
            kind = 2; status = guard(worlds+x, bodies+y);
            if (status == OK && o->code == 3) destroy_body((int)y);
            if (status == OK && o->code == 4)
                b2Body_SetTransform(bodies[y].raw, (b2Vec2){o->f[2], o->f[3]}, (b2Rot){o->f[4], o->f[5]});
            break;
        case 6: {
            b2BodyDef d = b2DefaultBodyDef(); d.type = b2_dynamicBody; d.enableSleep = false;
            for (uint32_t j = 1; j <= o->u[2]; ++j) {
                if (j > 1) { destroy_body((int)y); trace(id, seq, j, 0, (int)y, (int)o->u[3], owner); }
                status = create_body((int)y, owner, d);
                if (status != OK) fail("CHURN ticket limit");
                trace(id, seq, j, 1, (int)y, (int)o->u[3], owner);
            }
            kind = 2; break;
        }
    }
    printf("R %d %" PRIu32 " %d %d", id, seq, status, kind);
    if (kind == 1) world_handle(worlds[x]);
    else if (kind == 2) body_handle(bodies[o->code == 2 ? x : y]);
    else for (int i = 0; i < 9; ++i) word(0);
    putchar('\n'); dump(id, seq);
    int wc = 0, bc = 0;
    for (int i = 0; i < WORLDS; ++i) wc += worlds[i].live;
    for (int i = 0; i < BODIES; ++i) bc += bodies[i].live;
    if (wc > 4 || bc > 256) fail("corpus live limits");
}

                                                                         
                                                                                 
static int test_tickets(void)
{
    uint64_t candidate = 99;
    if (!ticket_next(UINT64_C(0xffffffff), &candidate) || candidate != UINT64_C(0x100000000)) return 2;
    candidate = 99;
    if (ticket_next(UINT64_MAX, &candidate) || candidate != 99) return 2;
    b2WorldDef wd = b2DefaultWorldDef(); wd.enableSleep = false; wd.enableContinuous = false;
    b2BodyDef bd = b2DefaultBodyDef(); bd.type = b2_dynamicBody; bd.enableSleep = false;
    lastIssued = UINT64_MAX-2;
    if (create_world(0, wd) != OK || worlds[0].birth != UINT64_MAX-1 || create_body(0, 0, bd) != OK
        || bodies[0].birth != UINT64_MAX || lastIssued != UINT64_MAX) return 2;
    World w = worlds[0]; Body b = bodies[0];
    if (create_world(1, wd) != LIMIT || create_body(1, 0, bd) != LIMIT || worlds[1].saved || bodies[1].saved
        || lastIssued != UINT64_MAX || worlds[0].birth != w.birth || bodies[0].birth != b.birth
        || !world_live(worlds) || !body_live(bodies) || b2World_GetCounters(w.raw).bodyCount != 1) return 2;
    destroy_body(0);
    if (create_body(0, 0, bd) != LIMIT || bodies[0].birth != b.birth || bodies[0].owner != b.owner
        || b2StoreBodyId(bodies[0].raw) != b2StoreBodyId(b.raw) || bodies[0].live
        || lastIssued != UINT64_MAX || b2World_GetCounters(w.raw).bodyCount != 0) return 2;
    destroy_world(0);
                                                                               
    if (create_world(0, wd) != LIMIT || worlds[0].birth != w.birth || worlds[0].live) return 2;
    if (create_body(0, 0, bd) != STALE || bodies[0].birth != b.birth || lastIssued != UINT64_MAX) return 2;
    puts("TICKETS OK"); return 0;
}
int main(int argc, char** argv)
{
    if (argc == 2 && strcmp(argv[1], "--test-tickets") == 0) return test_tickets();
    if (argc != 2) { fputs("usage: kontrola-swiat input | --test-tickets\n", stderr); return 2; }
    FILE* input = fopen(argv[1], "rb");
    if (!input) { perror(argv[1]); return 2; }
    char* p = row(input);
    uint32_t cases = decimal(&p);
    if ((cases != CASES && cases != 72) || *p) fail("N");
    printf("PORT6 %" PRIu32 "\n", cases);
    for (int id = 1; id <= (int)cases; ++id) {
        memset(worlds, 0, sizeof(worlds)); memset(bodies, 0, sizeof(bodies));
        p = row(input);
        if (*p++ != 'C') fail("C tag");
        space(&p); if (decimal(&p) != (uint32_t)id) fail("case id");
        space(&p); uint32_t count = decimal(&p);
        if (*p || !count || count > 256) fail("opCount");
        printf("CASE %d %" PRIu32 "\n", id, count);
        for (uint32_t seq = 1; seq <= count; ++seq) {
            Operation o = read_operation(input, seq); execute(id, seq, &o);
        }
        printf("ENDCASE %d\n", id);
        for (int i = 0; i < WORLDS; ++i) if (worlds[i].live) destroy_world(i);
    }
    if (fgetc(input) != EOF || ferror(input)) fail("extra input / read error");
    if (fclose(input)) fail("input close error");
    printf("END %" PRIu32 "\n", cases);
    return (ferror(stdout) || fflush(stdout)) ? 2 : 0;
}
