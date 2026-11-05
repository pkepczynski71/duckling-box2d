                                                                               
#pragma once
#include "box2d/box2d.h"
#include "solver.h"
#include <stdint.h>
void port10Record(const char* tag, const int* prefix, int np, const uint32_t* words, int nw);
uint32_t port10Bits(float value);
void port10CaptureSolver(b2TaskCallback* task, void* context);
void port10Trace(b2StepContext* context, int sub, int phase, bool packets);
void port10Constraints(b2StepContext* context, int sub, int phase, bool packets);
void port10Integrate(b2StepContext* context, bool positions, int count);
void port10ComponentContacts(b2StepContext* context, int phase);
void port10Helpers(int helper, int kind, const uint32_t* words);
void port10Created(b2World* world, int shapeA, int shapeB);
bool port10Observe(void);
