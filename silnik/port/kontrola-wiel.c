                                                                      
                                                                       
   
#include <box2d/collision.h>
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { CASE_COUNT = 252, INPUT_WORDS = 80, PARAM_WORDS = 58 };
_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "Requires IEEE binary32");
_Static_assert(sizeof(int) == 4 && CHAR_BIT == 8 && B2_MAX_POLYGON_VERTICES == 8,
               "Requires 32-bit int, 8-bit bytes, eight polygon vertices");

static float from_bits(uint32_t word)
{
    float value;
    memcpy(&value, &word, sizeof(value));
    return value;
}

static uint32_t to_bits(float value)
{
    uint32_t word;
    memcpy(&word, &value, sizeof(word));
    return word;
}

static void field(float value) { printf(" %" PRIu32, to_bits(value)); }

static void point(b2ManifoldPoint p)
{
    field(p.point.x); field(p.point.y);
    field(p.anchorA.x); field(p.anchorA.y);
    field(p.anchorB.x); field(p.anchorB.y);
    field(p.separation); field(p.normalImpulse); field(p.tangentImpulse);
    field(p.totalNormalImpulse); field(p.normalVelocity);
    printf(" %" PRIu16 " %d", p.id, p.persisted ? 1 : 0);
}

static int read_row(FILE *input, int id, uint32_t *words, int count)
{
                                                                                      
    char line[2048];
    if (fgets(line, sizeof(line), input) == NULL) return 0;
    size_t length = strlen(line);
    if (length > 0 && line[length - 1] == '\n') line[--length] = '\0';
    if (length > 0 && line[length - 1] == '\r') line[--length] = '\0';
    char prefix[16];
    int prefix_length = snprintf(prefix, sizeof(prefix), "%d ", id);
    if (strncmp(line, prefix, (size_t)prefix_length) != 0) return 0;
    const char *p = line + prefix_length;
    if (strlen(p) != (size_t)(9 * count - 1)) return 0;
    for (int j = 0; j < count; ++j) {
        char token[9];
        memcpy(token, p, 8); token[8] = '\0';
        if (strspn(token, "0123456789abcdef") != 8) return 0;
        words[j] = (uint32_t)strtoul(token, NULL, 16);
        p += 8;
        if (j + 1 < count && *p++ != ' ') return 0;
    }
    return *p == '\0';
}

static b2Transform transform(const uint32_t *w)
{
    return (b2Transform){ .p = {from_bits(w[0]), from_bits(w[1])},
                          .q = {from_bits(w[2]), from_bits(w[3])} };
}

static void encode(const b2Polygon *p, b2Transform t, uint32_t *w)
{
    w[0] = (uint32_t)p->count;
    for (int i = 0; i < 8; ++i) {
        w[1 + 2*i] = i < p->count ? to_bits(p->vertices[i].x) : 0;
        w[2 + 2*i] = i < p->count ? to_bits(p->vertices[i].y) : 0;
        w[17 + 2*i] = i < p->count ? to_bits(p->normals[i].x) : 0;
        w[18 + 2*i] = i < p->count ? to_bits(p->normals[i].y) : 0;
    }
    w[33] = to_bits(p->centroid.x); w[34] = to_bits(p->centroid.y); w[35] = to_bits(p->radius);
    w[36] = to_bits(t.p.x); w[37] = to_bits(t.p.y);
    w[38] = to_bits(t.q.c); w[39] = to_bits(t.q.s);
}

static int decode(const uint32_t *w, b2Polygon *p)
{
    *p = (b2Polygon){0};
    if (w[0] < 3 || w[0] > 8) return 0;
    p->count = (int)w[0];
    for (int j = 1; j < 40; ++j) if (!isfinite(from_bits(w[j]))) return 0;
    for (int i = 0; i < 8; ++i) {
        if (i >= p->count && (w[1+2*i] || w[2+2*i] || w[17+2*i] || w[18+2*i])) return 0;
        p->vertices[i] = (b2Vec2){from_bits(w[1+2*i]), from_bits(w[2+2*i])};
        p->normals[i] = (b2Vec2){from_bits(w[17+2*i]), from_bits(w[18+2*i])};
    }
    p->centroid = (b2Vec2){from_bits(w[33]), from_bits(w[34])};
    p->radius = from_bits(w[35]);
    return p->radius >= 0.0f;
}

static int construct(const uint32_t *w, b2Polygon *p)
{
    if (w[0] > 2 || w[1] < 3 || w[1] > 8) return 0;
    for (int j = 2; j < 29; ++j) if (!isfinite(from_bits(w[j]))) return 0;
    float radius = from_bits(w[2]);
    if (radius < 0.0f) return 0;
    if (w[0] == 2) {
        b2Vec2 points[8] = {0};
        for (uint32_t i = 0; i < w[1]; ++i)
            points[i] = (b2Vec2){from_bits(w[9+2*i]), from_bits(w[10+2*i])};
        b2Hull hull = b2ComputeHull(points, (int)w[1]);
        if (hull.count != (int)w[1] || !b2ValidateHull(&hull)) return 0;
        *p = b2MakePolygon(&hull, radius);
    } else {
        float hx = from_bits(w[3]), hy = from_bits(w[4]);
        if (hx <= 0.0f || hy <= 0.0f || w[1] != 4) return 0;
        if (w[0] == 0) *p = b2MakeBox(hx, hy);
        else *p = b2MakeOffsetBox(hx, hy,
            (b2Vec2){from_bits(w[5]), from_bits(w[6])},
            (b2Rot){from_bits(w[7]), from_bits(w[8])});
        p->radius = radius;
    }
    return 1;
}

int main(int argc, char **argv)
{
    int generate = argc == 3 && strcmp(argv[1], "--generuj") == 0;
    if (argc != 2 && !generate) {
        fputs("usage: kontrola-wiel [--generuj] przypadki.csv\n", stderr); return 2;
    }
    const char *path = argv[generate ? 2 : 1];
    FILE *input = fopen(path, "r");
    if (input == NULL) { perror(path); return 2; }
    if (!generate) printf("PORT2 %d\n", CASE_COUNT);
    for (int id = 1; id <= CASE_COUNT; ++id) {
        uint32_t input_words[INPUT_WORDS], words[INPUT_WORDS];
        if (!read_row(input, id, input_words, generate ? PARAM_WORDS : INPUT_WORDS)) {
            fprintf(stderr, "Bad/missing polygon case %d\n", id); fclose(input); return 2;
        }
        b2Polygon a, b;
        b2Transform ta, tb;
        if (generate) {
            if (!construct(input_words, &a) || !construct(input_words + 29, &b)) {
                fprintf(stderr, "Bad polygon constructor/hull in case %d\n", id); fclose(input); return 2;
            }
            ta = transform(input_words + 25); tb = transform(input_words + 54);
        } else {
            if (!decode(input_words, &a) || !decode(input_words + 40, &b)) {
                fprintf(stderr, "Bad polygon fields in case %d\n", id); fclose(input); return 2;
            }
            ta = transform(input_words + 36); tb = transform(input_words + 76);
        }
                                                                                        
        encode(&a, ta, words); encode(&b, tb, words + 40);
        if (generate) {
            printf("%d", id);
            for (int j = 0; j < INPUT_WORDS; ++j) printf(" %08" PRIx32, words[j]);
        } else {
            b2Manifold m = b2CollidePolygons(&a, ta, &b, tb);
            printf("R %d", id);
            for (int j = 0; j < INPUT_WORDS; ++j) printf(" %" PRIu32, words[j]);
            printf(" %d", m.pointCount);
            field(m.normal.x); field(m.normal.y); field(m.rollingImpulse);
            point(m.points[0]); point(m.points[1]);
        }
        putchar('\n');
    }
    if (fgetc(input) != EOF || ferror(input)) {
        fputs("Extra polygon input/read error\n", stderr); fclose(input); return 2;
    }
    if (fclose(input) != 0) { perror("fclose"); return 2; }
    if (!generate) printf("END %d\n", CASE_COUNT);
    return (ferror(stdout) || fflush(stdout) != 0) ? 2 : 0;
}
