                                                                              
                                                                             
#include <box2d/box2d.h>
#include "world.h"
#include "body.h"
#include "shape.h"
#include "joint.h"
#include "contact.h"
#include "atomic.h"
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef TRACE
#define TRACE 1
#endif
#if !defined(NDEBUG) || defined(B2_ENABLE_ASSERT)
#error KONTRAKT-5 requires Release / NDEBUG without B2_ENABLE_ASSERT
#endif
_Static_assert(B2_VALIDATE == 0, "Release validation configuration");
_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "IEEE binary32 required");
_Static_assert(sizeof(int) == 4 && CHAR_BIT == 8, "32-bit int required");

#if TRACE
static b2TreeStats observed_query(const b2DynamicTree*, b2AABB, uint64_t, b2TreeQueryCallbackFcn*, void*);
                                                                                
#define b2DynamicTree_Query observed_query
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-value"
#include "broad_phase.c"
#pragma GCC diagnostic pop
#undef b2DynamicTree_Query
#endif

enum { CASES = 75, MAX_SHAPES = 128, MAX_OPS = 1024, MAX_RULES = 256,
       MAX_QUERIES = 384, MAX_PAIRS = 16384, ROW_SIZE = 200000 };
typedef struct ShapeInput { uint32_t body, group, sensor, generation; uint64_t category, mask; } ShapeInput;
typedef struct Triple { uint32_t a, b, decision; } Triple;
typedef struct Operation {
    uint32_t kind, n, m;
    b2AABB box;
    uint64_t mask;
    bool force;
} Operation;
typedef struct Input {
    uint32_t mode, bodyCount, shapeCount, jointCount, custom, ruleCount, count, dump, world, capacity;
    b2BodyType bodies[MAX_SHAPES];
    ShapeInput shapes[MAX_SHAPES];
    Triple joints[MAX_SHAPES], rules[MAX_RULES];
    Operation ops[MAX_OPS];
} Input;
typedef struct Query {
    int move, key, type, count;
    b2TreeStats stats;
    int proxies[MAX_SHAPES], shapes[MAX_SHAPES];
} Query;
typedef struct Filter { b2ShapeId a, b; bool decision; } Filter;
typedef struct Request { int move, a, b; } Request;
static Query queries[MAX_QUERIES];
static Filter filters[MAX_PAIRS];
static Request requests[MAX_PAIRS];
static int queryCount, filterCount, requestCount, heapCount;

static void fail(const char* message)
{
    fprintf(stderr, "KONTRAKT-5: %s\n", message);
    exit(2);
}
static float from_bits(uint32_t w) { float f; memcpy(&f, &w, 4); return f; }
static uint32_t to_bits(float f) { uint32_t w; memcpy(&w, &f, 4); return w; }
static void word(uint32_t w) { printf(" %" PRIu32, w); }
static void integer(int i) { word((uint32_t)i); }
static void u64(uint64_t u) { word((uint32_t)u); word((uint32_t)(u >> 32)); }
static uint64_t join(uint32_t lo, uint32_t hi) { return (uint64_t)lo | (uint64_t)hi << 32; }
static void box_words(b2AABB a)
{
    word(to_bits(a.lowerBound.x)); word(to_bits(a.lowerBound.y));
    word(to_bits(a.upperBound.x)); word(to_bits(a.upperBound.y));
}
static b2AABB decode_box(const uint32_t* w)
{
    return (b2AABB){{from_bits(w[0]), from_bits(w[1])}, {from_bits(w[2]), from_bits(w[3])}};
}
static bool valid_box(b2AABB a)
{
    return isfinite(a.lowerBound.x) && isfinite(a.lowerBound.y) && isfinite(a.upperBound.x)
        && isfinite(a.upperBound.y) && a.lowerBound.x <= a.upperBound.x && a.lowerBound.y <= a.upperBound.y
        && a.upperBound.x-a.lowerBound.x < 100000.0f && a.upperBound.y-a.lowerBound.y < 100000.0f;
}
static bool contains(b2AABB a, b2AABB b)
{
    return a.lowerBound.x <= b.lowerBound.x && a.lowerBound.y <= b.lowerBound.y
        && a.upperBound.x >= b.upperBound.x && a.upperBound.y >= b.upperBound.y;
}

static uint32_t read_word(char** cursor)
{
    char* p = *cursor;
    if (strlen(p) < 8) fail("short input word");
    char token[9]; memcpy(token, p, 8); token[8] = '\0';
    if (strspn(token, "0123456789abcdef") != 8) fail("noncanonical input word");
    uint32_t w = (uint32_t)strtoul(token, NULL, 16);
    p += 8;
    if (*p == ' ') ++p;
    else if (*p != '\0') fail("input word separator");
    *cursor = p;
    return w;
}
static void read_row(FILE* stream, int id, Input* d)
{
    static char line[ROW_SIZE];
    if (!fgets(line, sizeof(line), stream)) fail("missing input row");
    size_t len = strlen(line);
    if (len && line[len-1] == '\n') line[--len] = '\0';
    if (len && line[len-1] == '\r') line[--len] = '\0';
    char prefix[16]; int prefixLength = snprintf(prefix, sizeof(prefix), "%d ", id);
    if (strncmp(line, prefix, (size_t)prefixLength)) fail("input case id");
    char* p = line+prefixLength;
    memset(d, 0, sizeof(*d));
    d->mode = read_word(&p);
    if (d->mode == 0) {
        d->bodyCount = read_word(&p); d->shapeCount = read_word(&p); d->jointCount = read_word(&p);
        d->custom = read_word(&p); d->ruleCount = read_word(&p); d->count = read_word(&p);
        d->dump = read_word(&p); d->world = read_word(&p);
        if (d->bodyCount > MAX_SHAPES || d->shapeCount > MAX_SHAPES || d->jointCount > MAX_SHAPES
            || d->ruleCount > MAX_RULES || d->custom > 3 || d->world > 3
            || (d->custom != 3 && d->ruleCount)) fail("header bounds");
        for (uint32_t i = 0; i < d->bodyCount; ++i) {
            uint32_t t = read_word(&p);
            if (t > 2) fail("body type");
            d->bodies[i] = (b2BodyType)t;
        }
        for (uint32_t i = 0; i < d->shapeCount; ++i) {
            ShapeInput* s = d->shapes+i;
            s->body = read_word(&p);
            uint32_t lo = read_word(&p), hi = read_word(&p); s->category = join(lo, hi);
            lo = read_word(&p); hi = read_word(&p); s->mask = join(lo, hi);
            s->group = read_word(&p); s->sensor = read_word(&p); s->generation = read_word(&p);
            if (s->body >= d->bodyCount || s->sensor > 1 || !s->generation || s->generation > 65535)
                fail("shape descriptor");
        }
        for (uint32_t i = 0; i < d->jointCount+d->ruleCount; ++i) {
            Triple* t = i < d->jointCount ? d->joints+i : d->rules+i-d->jointCount;
            t->a = read_word(&p); t->b = read_word(&p); t->decision = read_word(&p);
            if (t->decision > 1) fail("triple decision");
            if (i < d->jointCount) {
                if (t->a >= d->bodyCount || t->b >= d->bodyCount || t->a == t->b
                    || (d->bodies[t->a] != b2_dynamicBody && d->bodies[t->b] != b2_dynamicBody))
                    fail("distance joint bodies");
            } else {
                if (t->a >= d->shapeCount || t->b >= d->shapeCount) fail("rule shapes");
                for (uint32_t j = 0; j < i-d->jointCount; ++j)
                    if (d->rules[j].a == t->a && d->rules[j].b == t->b) fail("duplicate rule");
            }
        }
    } else if (d->mode == 1) {
        d->capacity = read_word(&p); d->count = read_word(&p); d->dump = read_word(&p);
        if (d->capacity != 16 && d->capacity != 32 && d->capacity != 64) fail("unsafe B01 capacity");
    } else fail("input mode");
    if (!d->count || d->count > MAX_OPS || d->dump > 1) fail("operation count / dump flag");
    for (uint32_t i = 0; i < d->count; ++i) {
        uint32_t w[16];
        for (int j = 0; j < 16; ++j) w[j] = read_word(&p);
        Operation* o = d->ops+i;
        o->kind = w[0];
        int used = 1;
        if (d->mode) {
            if (o->kind > 3) fail("set operation");
            if (o->kind != 3) { o->mask = join(w[1], w[2]); used = 3; if (!o->mask) fail("zero set key"); }
        } else {
            static const int usedWords[] = {7, 2, 6, 6, 2, 1, 1, 3, 2, 3, 8};
            if (o->kind > 10) fail("broad phase operation");
            used = usedWords[o->kind];
            if (used >= 2) o->n = w[1];
            if (o->kind == 7 || o->kind == 9) o->m = w[2];
            if (o->kind == 0 || o->kind == 2 || o->kind == 3 || o->kind == 10) {
                o->box = decode_box(w+2);
                if (!valid_box(o->box)) fail("AABB bounds");
            }
            if (o->kind == 0) {
                if (w[6] > 1 || !(fabsf(o->box.lowerBound.x) < 100000.0f
                    && fabsf(o->box.lowerBound.y) < 100000.0f && fabsf(o->box.upperBound.x) < 100000.0f
                    && fabsf(o->box.upperBound.y) < 100000.0f)) fail("create bounds/force");
                o->force = w[6] != 0;
            }
            if (o->kind == 10) { if (o->n > 2) fail("query type"); o->mask = join(w[6], w[7]); }
        }
        for (int j = used; j < 16; ++j) if (w[j]) fail("nonzero unused word");
    }
    if (*p || (len && line[len-1] == ' ')) fail("extra input words");
}

static Query* new_query(int move, int key, int type)
{
    if (queryCount == MAX_QUERIES) fail("query trace overflow");
    Query* q = queries+queryCount++;
    *q = (Query){.move=move, .key=key, .type=type};
    return q;
}
typedef struct Forward { Query* q; b2TreeQueryCallbackFcn* callback; void* context; } Forward;
static bool forward_hit(int proxy, uint64_t user, void* context)
{
    Forward* f = context;
    Query* q = f->q;
    if (q->count == MAX_SHAPES || user >= MAX_SHAPES) fail("hit trace overflow");
    q->proxies[q->count] = proxy; q->shapes[q->count++] = (int)user;
    return f->callback ? f->callback(proxy, user, f->context) : true;
}
#if TRACE
static b2TreeStats observed_query(const b2DynamicTree* tree, b2AABB box, uint64_t mask,
                                 b2TreeQueryCallbackFcn* callback, void* context)
{
    b2QueryPairContext* c = context;
    int moveIndex = (int)(c->moveResult-c->world->broadPhase.moveResults);
    Query* q = new_query(moveIndex, c->queryProxyKey, c->queryTreeType);
    Forward f = {q, callback, context};
    q->stats = b2DynamicTree_Query(tree, box, mask, forward_hit, &f);
    return q->stats;
}
#endif
static void* enqueue(b2TaskCallback* task, int count, int minRange, void* context, void* user)
{
    (void)minRange; (void)user;
    task(0, count, 0, context);
#if TRACE
    b2World* w = context;
    for (int i = 0; i < count; ++i) {
        for (b2MovePair* pair = w->broadPhase.moveResults[i].pairList; pair; pair = pair->next) {
            if (requestCount == MAX_PAIRS) fail("request trace overflow");
            requests[requestCount++] = (Request){i, pair->shapeIndexA, pair->shapeIndexB};
            heapCount += pair->heap;
        }
    }
#endif
    return NULL;
}
static void finish(void* task, void* user) { (void)task; (void)user; fail("unexpected asynchronous task"); }
static bool custom_filter(b2ShapeId a, b2ShapeId b, void* context)
{
    const Input* d = context;
    bool answer = d->custom != 2;
    if (d->custom == 3) {
        for (uint32_t i = 0; i < d->ruleCount; ++i)
            if (d->rules[i].a+1 == (uint32_t)a.index1 && d->rules[i].b+1 == (uint32_t)b.index1)
                answer = d->rules[i].decision != 0;
    }
#if TRACE
    if (filterCount == MAX_PAIRS) fail("filter trace overflow");
    filters[filterCount++] = (Filter){a, b, answer};
#endif
    return answer;
}

static void header(int id, const Input* d)
{
    printf("I %d", id); word(d->mode);
    if (d->mode) { word(d->capacity); word(d->count); word(d->dump); }
    else {
        word(d->bodyCount); word(d->shapeCount); word(d->jointCount); word(d->custom);
        word(d->ruleCount); word(d->count); word(d->dump); word(d->world);
    }
    putchar('\n');
}
static void echo(const Operation* o, bool set)
{
    word(o->kind);
    int used = 1;
    if (set) {
        if (o->kind != 3) { u64(o->mask); used = 3; }
    } else {
        switch (o->kind) {
            case 0: word(o->n); box_words(o->box); word(o->force); used=7; break;
            case 1: case 4: case 8: word(o->n); used=2; break;
            case 2: case 3: word(o->n); box_words(o->box); used=6; break;
            case 7: case 9: word(o->n); word(o->m); used=3; break;
            case 10: word(o->n); box_words(o->box); u64(o->mask); used=8; break;
        }
    }
    for (int j = used; j < 16; ++j) word(0);
}
static void dump_set(int id, int k, int kind, const b2HashSet* set)
{
    printf("HS %d %d", id, k); integer(kind); word(set->capacity); word(set->count);
    for (uint32_t i = 0; i < set->capacity; ++i) { u64(set->items[i].key); word(set->items[i].hash); }
    putchar('\n');
}
static uint64_t pair_key(int a, int b) { return B2_SHAPE_PAIR_KEY(a, b); }
static int compare_u64(const void* a, const void* b)
{
    uint64_t x = *(const uint64_t*)a, y = *(const uint64_t*)b;
    return (x > y)-(x < y);
}
static void verify_contacts(b2World* w, uint64_t* sorted, int* count)
{
    *count = 0;
    for (int i = 0; i < w->contacts.count; ++i) {
        const b2Contact* c = w->contacts.data+i;
        if (c->setIndex == B2_NULL_INDEX) continue;
        if (*count == MAX_PAIRS || (c->flags & b2_contactTouchingFlag)) fail("contact count/touching state");
        uint64_t key = pair_key(c->shapeIdA, c->shapeIdB);
        if (!b2ContainsKey(&w->broadPhase.pairSet, key)) fail("contact missing from pairSet");
        sorted[(*count)++] = key;
    }
    if ((uint32_t)*count != w->broadPhase.pairSet.count) fail("contacts vs pairSet count");
    qsort(sorted, (size_t)*count, sizeof(uint64_t), compare_u64);
    for (int i = 1; i < *count; ++i) if (sorted[i-1] == sorted[i]) fail("duplicate actual contact");
}
static void dump_world(int id, int k, b2World* w, const Input* d)
{
    b2BroadPhase* bp = &w->broadPhase;
    int live = 0;
    for (uint32_t n = 0; n < d->shapeCount; ++n) live += w->shapes.data[n].proxyKey != B2_NULL_INDEX;
    printf("D %d %d", id, k); integer(bp->moveArray.count); word(bp->moveSet.count);
    word(bp->pairSet.count); integer(live); integer(bp->movePairCapacity); integer(b2AtomicLoadInt(&bp->movePairIndex));
    putchar('\n');
    printf("M %d %d", id, k); integer(bp->moveArray.count);
    for (int i = 0; i < bp->moveArray.count; ++i) integer(bp->moveArray.data[i]);
    putchar('\n');
    for (int t = 0; t < 3; ++t) {
        b2DynamicTree* tree = bp->trees+t;
        printf("T %d %d", id, k); integer(t); integer(tree->root); integer(tree->nodeCount);
        integer(tree->nodeCapacity); integer(tree->freeList); integer(b2DynamicTree_GetProxyCount(tree));
        integer(b2DynamicTree_GetHeight(tree)); box_words(b2DynamicTree_GetRootBounds(tree)); putchar('\n');
    }
    for (uint32_t n = 0; n < d->shapeCount; ++n) {
        int key = w->shapes.data[n].proxyKey;
        if (key == B2_NULL_INDEX) continue;
        b2DynamicTree* tree = bp->trees+B2_PROXY_TYPE(key);
        printf("P %d %d", id, k); word(n); integer(key); box_words(b2DynamicTree_GetAABB(tree, B2_PROXY_ID(key)));
        u64(b2DynamicTree_GetCategoryBits(tree, B2_PROXY_ID(key))); integer(b2BroadPhase_GetShapeIndex(bp, key));
        putchar('\n');
    }
    dump_set(id, k, 0, &bp->moveSet); dump_set(id, k, 1, &bp->pairSet);
    static uint64_t contacts[MAX_PAIRS]; int count;
    verify_contacts(w, contacts, &count);
    printf("PS %d %d", id, k); integer(count);
    for (int i = 0; i < count; ++i) { word((uint32_t)(contacts[i] >> 32)); word((uint32_t)contacts[i]); }
    putchar('\n');
}
static void traces(int id, int k)
{
    for (int i = 0; i < queryCount; ++i) {
        Query* q = queries+i;
        printf("Q %d %d", id, k); integer(i); integer(q->move); integer(q->key); integer(q->type);
        integer(q->stats.nodeVisits); integer(q->stats.leafVisits); integer(q->count);
        for (int j = 0; j < q->count; ++j) { integer(q->proxies[j]); integer(q->shapes[j]); }
        putchar('\n');
    }
    for (int i = 0; i < filterCount; ++i) {
        Filter* f = filters+i;
        printf("F %d %d", id, k); integer(i); integer(f->a.index1); word(f->a.world0); word(f->a.generation);
        integer(f->b.index1); word(f->b.world0); word(f->b.generation); word(f->decision); putchar('\n');
    }
    for (int i = 0; i < requestCount; ++i) {
        Request* r = requests+i;
        printf("C %d %d", id, k); integer(i); integer(r->move); integer(r->a); integer(r->b); putchar('\n');
    }
}
static void execute_set(int id, const Input* d)
{
    b2HashSet set = b2CreateSet((int)d->capacity);
    header(id, d);
    for (uint32_t i = 0; i < d->count; ++i) {
        const Operation* o = d->ops+i; bool result = false;
        switch (o->kind) {
            case 0: result = b2AddKey(&set, o->mask); break;
            case 1: result = b2RemoveKey(&set, o->mask); break;
            case 2: result = b2ContainsKey(&set, o->mask); break;
            case 3: b2ClearSet(&set); break;
        }
        printf("O %d %" PRIu32, id, i+1); echo(o, true);
        if (o->kind != 3) word(result);
        putchar('\n');
        if (d->dump || i+1 == d->count) dump_set(id, (int)i+1, 2, &set);
    }
    b2DestroySet(&set);
}
static void execute_world(int id, const Input* d)
{
    b2WorldId worlds[4];
    b2WorldDef wd = b2DefaultWorldDef();
    wd.workerCount = 1; wd.enqueueTask = enqueue; wd.finishTask = finish;
    for (uint32_t i = 0; i <= d->world; ++i) worlds[i] = b2CreateWorld(&wd);
    b2World* w = b2GetWorldFromId(worlds[d->world]);
    if (w->worldId != d->world) fail("world index differs from table");
    b2BodyId bodies[MAX_SHAPES];
    for (uint32_t i = 0; i < d->bodyCount; ++i) {
        b2BodyDef bd = b2DefaultBodyDef(); bd.type = d->bodies[i];
        bd.position = (b2Vec2){(float)i*10.0f, 0.0f};
        bodies[i] = b2CreateBody(worlds[d->world], &bd);
        if (bodies[i].index1 != (int)i+1) fail("body index differs from table");
    }
    for (uint32_t i = 0; i < d->shapeCount; ++i) {
        const ShapeInput* s = d->shapes+i;
        b2ShapeDef sd = b2DefaultShapeDef();
        sd.filter.categoryBits = s->category; sd.filter.maskBits = s->mask;
        memcpy(&sd.filter.groupIndex, &s->group, 4); sd.isSensor = s->sensor != 0;
        b2Circle circle = {{0.0f, 0.0f}, 0.25f};
        b2ShapeId shapeId = b2CreateCircleShape(bodies[s->body], &sd, &circle);
        if (shapeId.index1 != (int)i+1) fail("shape index differs from table");
    }
    for (uint32_t i = 0; i < d->jointCount; ++i) {
        const Triple* j = d->joints+i;
        b2DistanceJointDef jd = b2DefaultDistanceJointDef();
        jd.bodyIdA = bodies[j->a]; jd.bodyIdB = bodies[j->b]; jd.collideConnected = j->decision != 0;
        jd.length = 1.0f;
        b2JointId jointId = b2CreateDistanceJoint(worlds[d->world], &jd);
        if (jointId.index1 != (int)i+1) fail("joint index differs from table");
    }
    if (w->broadPhase.pairSet.count || w->contacts.count) fail("contact before boundary reset");
    b2DestroyBroadPhase(&w->broadPhase); b2CreateBroadPhase(&w->broadPhase);
    for (uint32_t i = 0; i < d->shapeCount; ++i) {
        w->shapes.data[i].proxyKey = B2_NULL_INDEX;
        w->shapes.data[i].generation = (uint16_t)d->shapes[i].generation;
    }
    if (d->custom) b2World_SetCustomFilterCallback(worlds[d->world], custom_filter, (void*)d);
    header(id, d);
    for (uint32_t i = 0; i < d->bodyCount; ++i) {
        printf("EB %d", id); word(i); integer(w->bodies.data[i].type); putchar('\n');
    }
    for (uint32_t i = 0; i < d->shapeCount; ++i) {
        b2Shape* s = w->shapes.data+i;
        printf("ES %d", id); word(i); integer(s->bodyId); u64(s->filter.categoryBits); u64(s->filter.maskBits);
        integer(s->filter.groupIndex); word(s->sensorIndex != B2_NULL_INDEX); word(s->generation); putchar('\n');
    }
    for (uint32_t i = 0; i < d->jointCount; ++i) {
        b2Joint* j = w->joints.data+i;
        printf("EJ %d", id); word(i); integer(j->edges[0].bodyId); integer(j->edges[1].bodyId);
        word(j->collideConnected); putchar('\n');
    }
    for (uint32_t i = 0; i < d->ruleCount; ++i) {
        printf("EF %d", id); word(i); word(d->rules[i].a); word(d->rules[i].b); word(d->rules[i].decision); putchar('\n');
    }
    b2BroadPhase* bp = &w->broadPhase;
    for (uint32_t i = 0; i < d->count; ++i) {
        const Operation* o = d->ops+i;
        b2Shape* s = NULL; int result = 0;
        queryCount = filterCount = requestCount = heapCount = 0;
        if (o->kind <= 4 || o->kind == 7 || o->kind == 8 || o->kind == 9) {
            if (o->n >= d->shapeCount) fail("unknown shape");
            s = w->shapes.data+o->n;
            if ((o->kind == 0) != (s->proxyKey == B2_NULL_INDEX)) fail("dead / already live proxy");
        }
        if ((o->kind == 7 || o->kind == 9)
            && (o->m >= d->shapeCount || w->shapes.data[o->m].proxyKey == B2_NULL_INDEX)) fail("second dead proxy");
        int entry = bp->moveArray.count;
        switch (o->kind) {
            case 0:
                s->proxyKey = b2BroadPhase_CreateProxy(bp, w->bodies.data[s->bodyId].type,
                    o->box, s->filter.categoryBits, (int)o->n, o->force);
                result = s->proxyKey; break;
            case 1:
                for (int j = 0; j < w->contacts.count; ++j) {
                    b2Contact* c = w->contacts.data+j;
                    if (c->setIndex != B2_NULL_INDEX && (c->shapeIdA == (int)o->n || c->shapeIdB == (int)o->n))
                        fail("DestroyProxy with incident contact");
                }
                b2BroadPhase_DestroyProxy(bp, s->proxyKey); s->proxyKey = B2_NULL_INDEX; break;
            case 2: b2BroadPhase_MoveProxy(bp, s->proxyKey, o->box); break;
            case 3:
                if (B2_PROXY_TYPE(s->proxyKey) == b2_staticBody || contains(
                    b2DynamicTree_GetAABB(bp->trees+B2_PROXY_TYPE(s->proxyKey), B2_PROXY_ID(s->proxyKey)), o->box))
                    fail("invalid EnlargeProxy");
                b2BroadPhase_EnlargeProxy(bp, s->proxyKey, o->box); break;
            case 4: b2BufferMove(bp, s->proxyKey); break;
            case 5: b2UpdateBroadPhasePairs(w); break;
            case 6: b2BroadPhase_RebuildTrees(bp); break;
            case 7: result = b2BroadPhase_TestOverlap(bp, s->proxyKey, w->shapes.data[o->m].proxyKey); break;
            case 8: result = b2BroadPhase_GetShapeIndex(bp, s->proxyKey); break;
            case 9: {
                b2Contact* found = NULL;
                for (int j = 0; j < w->contacts.count; ++j) {
                    b2Contact* c = w->contacts.data+j;
                    if (c->setIndex != B2_NULL_INDEX && pair_key(c->shapeIdA, c->shapeIdB) == pair_key((int)o->n, (int)o->m)) {
                        if (found) fail("duplicate release contact");
                        found = c;
                    }
                }
                if (!found) fail("release missing contact");
                b2DestroyContact(w, found, false); break;
            }
            case 10: {
                Query* q = new_query(B2_NULL_INDEX, B2_NULL_INDEX, (int)o->n);
                Forward f = {q, NULL, NULL};
                q->stats = b2DynamicTree_Query(bp->trees+o->n, o->box, o->mask, forward_hit, &f); break;
            }
        }
        printf("O %d %" PRIu32, id, i+1); echo(o, false);
        if (o->kind == 0 || o->kind == 7 || o->kind == 8) integer(result);
        putchar('\n');
        traces(id, (int)i+1);
        if (o->kind == 5) {
            int index = b2AtomicLoadInt(&bp->movePairIndex);
            printf("U %d %" PRIu32, id, i+1); word(entry != 0); integer(entry); integer(bp->movePairCapacity); integer(index);
#if TRACE
            integer(heapCount); integer(requestCount);
            if ((entry ? index : 0) != requestCount) fail("trace vs movePairIndex");
#else
            integer(entry && index > bp->movePairCapacity ? index-bp->movePairCapacity : 0);
            integer(entry ? index : 0);
#endif
            putchar('\n');
        }
                                                                                     
        static uint64_t contacts[MAX_PAIRS]; int count;
        verify_contacts(w, contacts, &count);
        if (d->dump || i+1 == d->count) dump_world(id, (int)i+1, w, d);
    }
    for (int i = (int)d->world; i >= 0; --i) b2DestroyWorld(worlds[i]);
}
int main(int argc, char** argv)
{
    if (argc != 2) { fputs("usage: kontrola-szeroka przypadki-szeroka.csv\n", stderr); return 2; }
    FILE* input = fopen(argv[1], "r");
    if (!input) { perror(argv[1]); return 2; }
    printf("PORT5 %d\n", CASES);
    static Input d;
    for (int id = 1; id <= CASES; ++id) {
        read_row(input, id, &d);
        if (d.mode) execute_set(id, &d); else execute_world(id, &d);
    }
    if (fgetc(input) != EOF || ferror(input)) fail("extra input / read error");
    if (fclose(input)) fail("input close error");
    printf("END %d\n", CASES);
    return (ferror(stdout) || fflush(stdout)) ? 2 : 0;
}
