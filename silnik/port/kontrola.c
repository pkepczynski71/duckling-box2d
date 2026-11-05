                                                                          
                                                             
   
#include <box2d/collision.h>
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "Requires IEEE binary32");
_Static_assert(sizeof(int) == 4 && CHAR_BIT == 8, "Requires 32-bit int and 8-bit bytes");

static float from_bits(uint32_t bits)
{
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static void field(float value)
{
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    printf(" %" PRIu32, bits);
}

                                                                                     
static void point(b2ManifoldPoint p)
{
    field(p.point.x); field(p.point.y);
    field(p.anchorA.x); field(p.anchorA.y);
    field(p.anchorB.x); field(p.anchorB.y);
    field(p.separation); field(p.normalImpulse); field(p.tangentImpulse);
    field(p.totalNormalImpulse); field(p.normalVelocity);
    printf(" %" PRIu16 " %d", p.id, p.persisted ? 1 : 0);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fputs("usage: kontrola przypadki.csv\n", stderr);
        return 2;
    }
    FILE *input = fopen(argv[1], "r");
    if (input == NULL) { perror(argv[1]); return 2; }
    puts("PORT1 180");
    for (int id = 1; id <= 180; ++id) {
        int read_id;
        uint32_t words[14];
        float v[14];
        if (fscanf(input, "%d", &read_id) != 1 || read_id != id) {
            fputs("Bad/missing case id\n", stderr); fclose(input); return 2;
        }
        for (int j = 0; j < 14; ++j) {
            char token[64];
            if (fscanf(input, "%63s", token) != 1 || strlen(token) != 8 ||
                strspn(token, "0123456789abcdef") != 8) {
                fputs("Expected eight lowercase hex digits\n", stderr); fclose(input); return 2;
            }
            words[j] = (uint32_t)strtoul(token, NULL, 16);
            v[j] = from_bits(words[j]);
        }
                                                                                 
        b2Circle a = { .center = {v[0], v[1]}, .radius = v[2] };
        b2Transform ta = { .p = {v[3], v[4]}, .q = {v[5], v[6]} };
        b2Circle b = { .center = {v[7], v[8]}, .radius = v[9] };
        b2Transform tb = { .p = {v[10], v[11]}, .q = {v[12], v[13]} };
        b2Manifold m = b2CollideCircles(&a, ta, &b, tb);
        printf("R %d", id);
                                                                                    
        for (int j = 0; j < 14; ++j) field(v[j]);
        printf(" %d", m.pointCount);
        field(m.normal.x); field(m.normal.y); field(m.rollingImpulse);
        point(m.points[0]); point(m.points[1]);
        putchar('\n');
    }
    char extra[2];
    if (fscanf(input, "%1s", extra) == 1 || ferror(input)) {
        fputs("Extra input/read error\n", stderr); fclose(input); return 2;
    }
    if (fclose(input) != 0) { perror("fclose"); return 2; }
    puts("END 180");
    return (ferror(stdout) || fflush(stdout) != 0) ? 2 : 0;
}
