                                                                     
#include <box2d/collision.h>
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { CASE_COUNT = 50, MAX_OPS = 200, ROW_SIZE = 14500 };
_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "Requires IEEE binary32");
_Static_assert(sizeof(int) == 4 && CHAR_BIT == 8, "Requires 32-bit int and 8-bit bytes");

static float from_bits(uint32_t w)
{
    float f;
    memcpy(&f, &w, sizeof(f));
    return f;
}

static uint32_t to_bits(float f)
{
    uint32_t w;
    memcpy(&w, &f, sizeof(w));
    return w;
}

static void word(uint32_t w) { printf(" %" PRIu32, w); }
static void integer(int i) { word((uint32_t)i); }
static void u64(uint64_t u) { word((uint32_t)u); word((uint32_t)(u >> 32)); }

static void box_words(b2AABB a)
{
    word(to_bits(a.lowerBound.x)); word(to_bits(a.lowerBound.y));
    word(to_bits(a.upperBound.x)); word(to_bits(a.upperBound.y));
}

typedef struct Operation
{
    uint32_t kind, n;
    b2AABB box;
    uint64_t category, user;
    bool full;
} Operation;

typedef struct Input
{
    uint32_t count, dump;
    Operation ops[MAX_OPS];
} Input;

static b2AABB decode_box(const uint32_t *w)
{
    return (b2AABB){{from_bits(w[0]), from_bits(w[1])}, {from_bits(w[2]), from_bits(w[3])}};
}

static int valid_box(b2AABB a)
{
    return isfinite(a.lowerBound.x) && isfinite(a.lowerBound.y)
        && isfinite(a.upperBound.x) && isfinite(a.upperBound.y)
        && a.upperBound.x >= a.lowerBound.x && a.upperBound.y >= a.lowerBound.y
        && a.upperBound.x - a.lowerBound.x < 100000.0f
        && a.upperBound.y - a.lowerBound.y < 100000.0f;
}

static int contains(b2AABB a, b2AABB b)
{
    return a.lowerBound.x <= b.lowerBound.x && a.lowerBound.y <= b.lowerBound.y
        && a.upperBound.x >= b.upperBound.x && a.upperBound.y >= b.upperBound.y;
}

static int decode_op(Operation *op, const uint32_t w[8])
{
    *op = (Operation){.kind = w[0]};
    int used = 0;
    switch (op->kind) {
        case 0:
            op->box = decode_box(w+1);
            op->category = (uint64_t)w[5] | (uint64_t)w[6] << 32;
            op->user = w[7];
            if (!(fabsf(op->box.lowerBound.x) < 100000.0f && fabsf(op->box.lowerBound.y) < 100000.0f
                && fabsf(op->box.upperBound.x) < 100000.0f && fabsf(op->box.upperBound.y) < 100000.0f)) return 0;
            used = 8;
            break;
        case 1: op->n = w[1]; used = 2; break;
        case 2: case 3: op->n = w[1]; op->box = decode_box(w+2); used = 6; break;
        case 4:
            op->n = w[1]; op->category = (uint64_t)w[2] | (uint64_t)w[3] << 32;
            used = 4;
            break;
        case 5:
            op->box = decode_box(w+1);
            op->category = (uint64_t)w[5] | (uint64_t)w[6] << 32;
            used = 7;
            break;
        case 6:
            if (w[1] > 1) return 0;
            op->full = w[1] != 0; used = 2;
            break;
        default: return 0;
    }
    for (int j = used; j < 8; ++j) if (w[j] != 0) return 0;
    return (op->kind != 0 && op->kind != 2 && op->kind != 3 && op->kind != 5) || valid_box(op->box);
}

static int read_word(const char **cursor, uint32_t *w, int last)
{
    const char *p = *cursor;
    if (strlen(p) < 8) return 0;
    char token[9];
    memcpy(token, p, 8); token[8] = '\0';
    if (strspn(token, "0123456789abcdef") != 8) return 0;
    *w = (uint32_t)strtoul(token, NULL, 16);
    p += 8;
    if (last ? *p != '\0' : *p++ != ' ') return 0;
    *cursor = p;
    return 1;
}

static int read_row(FILE *input, int id, Input *d)
{
    char line[ROW_SIZE];
    if (fgets(line, sizeof(line), input) == NULL) return 0;
    size_t length = strlen(line);
    if (length > 0 && line[length-1] == '\n') line[--length] = '\0';
    if (length > 0 && line[length-1] == '\r') line[--length] = '\0';
    char prefix[16];
    int n = snprintf(prefix, sizeof(prefix), "%d ", id);
    if (strncmp(line, prefix, (size_t)n) != 0) return 0;
    const char *p = line+n;
    if (!read_word(&p, &d->count, 0) || !read_word(&p, &d->dump, 0)
        || d->count < 1 || d->count > MAX_OPS || d->dump > 1) return 0;
    for (uint32_t i = 0; i < d->count; ++i) {
        uint32_t w[8];
        for (int j = 0; j < 8; ++j)
            if (!read_word(&p, &w[j], i+1 == d->count && j == 7)) return 0;
        if (!decode_op(&d->ops[i], w)) return 0;
    }
    return *p == '\0';
}

                                                                              
static void echo(const Operation *op)
{
    word(op->kind);
    switch (op->kind) {
        case 0: box_words(op->box); u64(op->category); word((uint32_t)op->user); break;
        case 1: word(op->n); for (int j = 0; j < 6; ++j) word(0); break;
        case 2: case 3: word(op->n); box_words(op->box); word(0); word(0); break;
        case 4: word(op->n); u64(op->category); for (int j = 0; j < 4; ++j) word(0); break;
        case 5: box_words(op->box); u64(op->category); word(0); break;
        case 6: word(op->full ? 1u : 0u); for (int j = 0; j < 6; ++j) word(0); break;
    }
}

typedef struct Hits
{
    int ids[MAX_OPS];
    uint64_t users[MAX_OPS];
    int count;
    bool overflow;
} Hits;

static bool hit(int proxyId, uint64_t userData, void *context)
{
    Hits *hits = context;
    if (hits->count < MAX_OPS) {
        hits->ids[hits->count] = proxyId;
        hits->users[hits->count] = userData;
        ++hits->count;
    } else hits->overflow = true;
    return true;
}

static void dump(b2DynamicTree *tree, int id, uint32_t k, const int *proxies, int created)
{
    printf("D %d %" PRIu32, id, k);
    integer(tree->root); integer(tree->nodeCount); integer(tree->nodeCapacity); integer(tree->freeList);
    integer(b2DynamicTree_GetProxyCount(tree)); integer(b2DynamicTree_GetHeight(tree));
    word(to_bits(b2DynamicTree_GetAreaRatio(tree)));
    box_words(b2DynamicTree_GetRootBounds(tree));
    int live = 0;
    for (int n = 0; n < created; ++n) live += proxies[n] >= 0;
    integer(live);
    for (int n = 0; n < created; ++n) {
        if (proxies[n] < 0) continue;
        integer(n); integer(proxies[n]);
        box_words(b2DynamicTree_GetAABB(tree, proxies[n]));
        u64(b2DynamicTree_GetCategoryBits(tree, proxies[n]));
        u64(b2DynamicTree_GetUserData(tree, proxies[n]));
    }
    putchar('\n');
}

static int execute(int id, const Input *d)
{
    b2DynamicTree tree = b2DynamicTree_Create();
    int proxies[MAX_OPS], created = 0;
    for (uint32_t i = 0; i < d->count; ++i) {
        const Operation *op = &d->ops[i];
        if (op->kind >= 1 && op->kind <= 4) {
            if (op->n >= (uint32_t)created || proxies[op->n] < 0) goto invalid;
            if (op->kind == 3 && contains(b2DynamicTree_GetAABB(&tree, proxies[op->n]), op->box)) goto invalid;
        }
        Hits hits = {0};
        b2TreeStats stats = {0};
        int result = 0;
        switch (op->kind) {
            case 0:
                result = b2DynamicTree_CreateProxy(&tree, op->box, op->category, op->user);
                proxies[created++] = result;
                break;
            case 1: b2DynamicTree_DestroyProxy(&tree, proxies[op->n]); proxies[op->n] = -1; break;
            case 2: b2DynamicTree_MoveProxy(&tree, proxies[op->n], op->box); break;
            case 3: b2DynamicTree_EnlargeProxy(&tree, proxies[op->n], op->box); break;
            case 4: b2DynamicTree_SetCategoryBits(&tree, proxies[op->n], op->category); break;
            case 5:
                stats = b2DynamicTree_Query(&tree, op->box, op->category, hit, &hits);
                if (hits.overflow) goto invalid;
                break;
            case 6: result = b2DynamicTree_Rebuild(&tree, op->full); break;
        }
        printf("O %d %" PRIu32, id, i+1);
        echo(op);
        if (op->kind == 0 || op->kind == 6) integer(result);
        else if (op->kind == 5) {
            integer(stats.nodeVisits); integer(stats.leafVisits); integer(hits.count);
            for (int j = 0; j < hits.count; ++j) { integer(hits.ids[j]); u64(hits.users[j]); }
        }
        putchar('\n');
        if (d->dump || i+1 == d->count) dump(&tree, id, i+1, proxies, created);
        continue;
invalid:
        fprintf(stderr, "Invalid tree operation: case %d, operation %" PRIu32 "\n", id, i+1);
        b2DynamicTree_Destroy(&tree);
        return 0;
    }
    b2DynamicTree_Destroy(&tree);
    return 1;
}

int main(int argc, char **argv)
{
    if (argc != 2) { fputs("usage: kontrola-drzewo przypadki-drzewo.csv\n", stderr); return 2; }
    FILE *input = fopen(argv[1], "r");
    if (input == NULL) { perror(argv[1]); return 2; }
    printf("PORT4 %d\n", CASE_COUNT);
    for (int id = 1; id <= CASE_COUNT; ++id) {
        Input d;
        if (!read_row(input, id, &d) || !execute(id, &d)) {
            fprintf(stderr, "Bad/missing tree input: case %d\n", id);
            fclose(input); return 2;
        }
    }
    if (fgetc(input) != EOF || ferror(input)) {
        fputs("Extra tree input/read error\n", stderr); fclose(input); return 2;
    }
    if (fclose(input) != 0) { perror("fclose"); return 2; }
    printf("END %d\n", CASE_COUNT);
    return (ferror(stdout) || fflush(stdout) != 0) ? 2 : 0;
}
