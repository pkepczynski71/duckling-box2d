                                                                       
#include <box2d/box2d.h>
#include <inttypes.h>
#include <locale.h>
#include <stdio.h>

int main(void)
{
    if (setlocale(LC_NUMERIC, "C") == NULL) {
        fputs("Cannot set C numeric locale\n", stderr);
        return 1;
    }

    b2WorldDef worldDef = b2DefaultWorldDef();
    b2BodyDef bodyDef = b2DefaultBodyDef();
    b2ShapeDef shapeDef = b2DefaultShapeDef();

                                                                       
    printf("DEF world.gravity_y %.6f\n", (double)worldDef.gravity.y);
    printf("DEF world.contact_hertz %.6f\n", (double)worldDef.contactHertz);
    printf("DEF world.enable_sleep %d\n", worldDef.enableSleep ? 1 : 0);
    printf("DEF world.worker_count %d\n", worldDef.workerCount);
    printf("DEF body.type %d\n", (int)bodyDef.type);
    printf("DEF body.rotation_c %.6f\n", (double)bodyDef.rotation.c);
    printf("DEF body.gravity_scale %.6f\n", (double)bodyDef.gravityScale);
    printf("DEF body.is_enabled %d\n", bodyDef.isEnabled ? 1 : 0);
    printf("DEF body.internal_value %d\n", bodyDef.internalValue);
    printf("DEF shape.material_friction %.6f\n", (double)shapeDef.material.friction);
    printf("DEF shape.density %.6f\n", (double)shapeDef.density);
    printf("DEF shape.filter_category_bits %" PRIu64 "\n", shapeDef.filter.categoryBits);
    printf("DEF shape.filter_mask_bits %" PRIu64 "\n", shapeDef.filter.maskBits);
    printf("DEF shape.update_body_mass %d\n", shapeDef.updateBodyMass ? 1 : 0);

    worldDef.gravity = (b2Vec2){0.0f, -10.0f};
    b2WorldId world = b2CreateWorld(&worldDef);

    bodyDef.position = (b2Vec2){4.0f, 0.25f};
    bodyDef.type = b2_staticBody;
    b2BodyId floorBody = b2CreateBody(world, &bodyDef);
    b2Polygon floorBox = b2MakeBox(4.0f, 0.25f);
    b2CreatePolygonShape(floorBody, &shapeDef, &floorBox);

    bodyDef = b2DefaultBodyDef();
    bodyDef.type = b2_dynamicBody;
    bodyDef.position = (b2Vec2){4.0f, 5.0f};
    b2BodyId boxBody = b2CreateBody(world, &bodyDef);
    b2Polygon box = b2MakeBox(0.2f, 0.2f);
    b2CreatePolygonShape(boxBody, &shapeDef, &box);

    for (int step = 1; step <= 180; ++step) {
        b2World_Step(world, 1.0f / 60.0f, 4);
        b2Vec2 position = b2Body_GetPosition(boxBody);
        b2Rot rot = b2Body_GetRotation(boxBody);
        printf("POS %d %.6f %.6f %.6f %.6f\n", step,
               (double)position.x, (double)position.y, (double)rot.c, (double)rot.s);
    }

    b2DestroyWorld(world);
    puts("KONIEC OK");
    return (ferror(stdout) || fflush(stdout) != 0) ? 1 : 0;
}
