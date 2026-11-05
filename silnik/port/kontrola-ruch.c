                                                                      
#include <box2d/box2d.h>
#include <box2d/collision.h>
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { CASE_COUNT = 70, INPUT_WORDS = 86 };
_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "Requires IEEE binary32");
_Static_assert(sizeof(int) == 4 && CHAR_BIT == 8, "Requires 32-bit int and 8-bit bytes");

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

static int integer_field(int i)
{
    return i == 4 || i == 5 || i == 16 || i == 17 || i == 18 || i == 19 || i == 28 || i == 37
        || (i >= 38 && (i - 38) % 6 < 2);
}

typedef struct Input
{
                                                                                   
    uint32_t u[INPUT_WORDS];
    float f[INPUT_WORDS];
} Input;

static int read_row(FILE *input, int id, Input *data)
{
    char line[1024];
    if (fgets(line, sizeof(line), input) == NULL) return 0;
    size_t length = strlen(line);
    if (length > 0 && line[length - 1] == '\n') line[--length] = '\0';
    if (length > 0 && line[length - 1] == '\r') line[--length] = '\0';
    char prefix[16];
    int n = snprintf(prefix, sizeof(prefix), "%d ", id);
    if (strncmp(line, prefix, (size_t)n) != 0) return 0;
    const char *p = line + n;
    if (strlen(p) != 9 * INPUT_WORDS - 1) return 0;
    *data = (Input){0};
    for (int i = 0; i < INPUT_WORDS; ++i) {
        char token[9];
        memcpy(token, p, 8); token[8] = '\0';
        if (strspn(token, "0123456789abcdef") != 8) return 0;
        uint32_t word = (uint32_t)strtoul(token, NULL, 16);
        if (integer_field(i)) data->u[i] = word;
        else {
            data->f[i] = from_bits(word);
            if (!isfinite(data->f[i])) return 0;
        }
        p += 8;
        if (i + 1 < INPUT_WORDS && *p++ != ' ') return 0;
    }
    return *p == '\0';
}

static uint32_t encoded(const Input *d, int i)
{
    return integer_field(i) ? d->u[i] : to_bits(d->f[i]);
}

static int zero_range(const Input *d, int begin, int end)
{
    for (int i = begin; i < end; ++i) if (encoded(d, i) != 0) return 0;
    return 1;
}

static int valid_rotation(float c, float s)
{
    return fabsf(c*c+s*s-1.0f) <= 0x1p-19f;
}

static int validate(const Input *d)
{
    const float *f = d->f;
    const uint32_t *u = d->u;
    if (!(f[2] > 0 && f[3] > 0 && f[13] >= 0 && f[14] >= 0
          && u[4] >= 1 && u[4] <= 8 && u[5] >= 1 && u[5] <= 600
          && u[16] <= 1 && u[17] <= 1 && u[18] >= 1 && u[18] <= 2 && u[37] <= 8
          && valid_rotation(f[8], f[9]))) return 0;
    for (uint32_t i = 0; i < 2; ++i) {
        int o = 19 + 9*(int)i;
        if (i >= u[18]) {
            if (!zero_range(d, o, o+9)) return 0;
        } else if (u[o] > 1 || f[o+1] <= 0) return 0;
        else if (u[o] == 0) {
            if (f[o+4] <= 0 || !zero_range(d, o+5, o+9)) return 0;
        } else if (f[o+2] <= 0 || f[o+3] <= 0 || f[o+8] < 0
                   || !valid_rotation(f[o+6], f[o+7])) return 0;
    }
    for (uint32_t i = 0; i < 8; ++i) {
        int o = 38 + 6*(int)i;
        if (i >= u[37]) {
            if (!zero_range(d, o, o+6)) return 0;
        } else {
            if (u[o] < 1 || u[o] > u[5] || u[o+1] > 5) return 0;
            if ((u[o+1] == 1 || u[o+1] == 4) && !zero_range(d, o+4, o+6)) return 0;
            if ((u[o+1] == 2 || u[o+1] == 5) && !zero_range(d, o+3, o+6)) return 0;
        }
    }
    return 1;
}

static void execute(int id, const Input *d)
{
    const float *f = d->f;
    const uint32_t *u = d->u;
    b2WorldDef wd = b2DefaultWorldDef();
    wd.enableSleep = false;
    wd.enableContinuous = false;
    wd.gravity = (b2Vec2){f[0], f[1]};
    wd.maximumLinearSpeed = f[2];
    wd.workerCount = 0;                                                         
    b2WorldId world = b2CreateWorld(&wd);
    b2BodyDef bd = b2DefaultBodyDef();
    bd.type = b2_dynamicBody;
    bd.position = (b2Vec2){f[6], f[7]};
    bd.rotation = (b2Rot){f[8], f[9]};
    bd.linearVelocity = (b2Vec2){f[10], f[11]};
    bd.angularVelocity = f[12];
    bd.linearDamping = f[13];
    bd.angularDamping = f[14];
    bd.gravityScale = f[15];
    bd.fixedRotation = u[16] != 0;
    bd.allowFastRotation = u[17] != 0;
    bd.enableSleep = false;
    b2BodyId body = b2CreateBody(world, &bd);
    for (uint32_t i = 0; i < u[18]; ++i) {
        int o = 19 + 9*(int)i;
        b2ShapeDef sd = b2DefaultShapeDef();
        sd.density = f[o+1];
        sd.updateBodyMass = true;
        if (u[o] == 0) {
            b2Circle circle = {.center = {f[o+2], f[o+3]}, .radius = f[o+4]};
            (void)b2CreateCircleShape(body, &sd, &circle);
        } else {
            b2Polygon polygon = b2MakeOffsetRoundedBox(f[o+2], f[o+3],
                (b2Vec2){f[o+4], f[o+5]}, (b2Rot){f[o+6], f[o+7]}, f[o+8]);
            (void)b2CreatePolygonShape(body, &sd, &polygon);
        }
    }
    printf("M %d", id);
    for (int i = 0; i < INPUT_WORDS; ++i) printf(" %" PRIu32, encoded(d, i));
    b2MassData mass = b2Body_GetMassData(body);
    field(mass.mass); field(mass.rotationalInertia); field(mass.center.x); field(mass.center.y);
    putchar('\n');
    for (uint32_t step = 1; step <= u[5]; ++step) {
        for (uint32_t i = 0; i < u[37]; ++i) {
            int o = 38 + 6*(int)i;
            if (u[o] != step) continue;
            b2Vec2 v = {f[o+2], f[o+3]}, p = {f[o+4], f[o+5]};
            switch (u[o+1]) {
                case 0: b2Body_ApplyForce(body, v, p, true); break;
                case 1: b2Body_ApplyForceToCenter(body, v, true); break;
                case 2: b2Body_ApplyTorque(body, f[o+2], true); break;
                case 3: b2Body_ApplyLinearImpulse(body, v, p, true); break;
                case 4: b2Body_ApplyLinearImpulseToCenter(body, v, true); break;
                case 5: b2Body_ApplyAngularImpulse(body, f[o+2], true); break;
            }
        }
        b2World_Step(world, f[3], (int)u[4]);
        b2Transform t = b2Body_GetTransform(body);
        b2Vec2 center = b2Body_GetWorldCenterOfMass(body);
        b2Vec2 velocity = b2Body_GetLinearVelocity(body);
        printf("S %d %" PRIu32, id, step);
        field(t.p.x); field(t.p.y); field(t.q.c); field(t.q.s);
        field(center.x); field(center.y); field(velocity.x); field(velocity.y);
        field(b2Body_GetAngularVelocity(body));
        putchar('\n');
    }
    b2DestroyWorld(world);
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--stale") == 0) {
        const float dt[3] = {1.0f/60.0f, 1.0f/30.0f, 1.0f/240.0f};
        for (int i = 0; i < 3; ++i) printf(i ? " %08" PRIx32 : "%08" PRIx32, to_bits(dt[i]));
        for (int i = 0; i < 3; ++i) {
            float inv_dt = 1.0f/dt[i];
            float limit = (0.25f * B2_PI) * inv_dt;
            printf(" %08" PRIx32, to_bits(limit));
        }
        putchar('\n');
        return (ferror(stdout) || fflush(stdout) != 0) ? 2 : 0;
    }
    if (argc != 2) { fputs("usage: kontrola-ruch przypadki.csv | --stale\n", stderr); return 2; }
    FILE *input = fopen(argv[1], "r");
    if (input == NULL) { perror(argv[1]); return 2; }
    printf("PORT3 %d\n", CASE_COUNT);
    for (int id = 1; id <= CASE_COUNT; ++id) {
        Input d;
        if (!read_row(input, id, &d) || !validate(&d)) {
            fprintf(stderr, "Bad/missing motion input: case %d\n", id);
            fclose(input); return 2;
        }
        execute(id, &d);
    }
    if (fgetc(input) != EOF || ferror(input)) {
        fputs("Extra motion input/read error\n", stderr); fclose(input); return 2;
    }
    if (fclose(input) != 0) { perror("fclose"); return 2; }
    printf("END %d\n", CASE_COUNT);
    return (ferror(stdout) || fflush(stdout) != 0) ? 2 : 0;
}
