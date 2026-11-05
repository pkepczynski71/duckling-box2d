                                                                                 
#include "joint.h"
#include "solver.h"
extern void port14OriginalPrepare(b2JointSim*,b2StepContext*);
extern void port14OriginalWarm(b2JointSim*,b2StepContext*);
extern void port14OriginalSolve(b2JointSim*,b2StepContext*,bool);
extern void port14JointEvent(b2JointSim*,b2StepContext*,int);
void b2PrepareDistanceJoint(b2JointSim* joint,b2StepContext* context)
{port14JointEvent(joint,context,0);port14OriginalPrepare(joint,context);}
void b2WarmStartDistanceJoint(b2JointSim* joint,b2StepContext* context)
{port14JointEvent(joint,context,1);port14OriginalWarm(joint,context);}
void b2SolveDistanceJoint(b2JointSim* joint,b2StepContext* context,bool bias)
{port14JointEvent(joint,context,bias?2:3);port14OriginalSolve(joint,context,bias);}

#ifdef PORT14_PART_B
extern void port14OriginalRPrepare(b2JointSim*,b2StepContext*);
void b2PrepareRevoluteJoint(b2JointSim* joint,b2StepContext* context)
{port14JointEvent(joint,context,0);port14OriginalRPrepare(joint,context);}
extern void port14OriginalRWarm(b2JointSim*,b2StepContext*);
void b2WarmStartRevoluteJoint(b2JointSim* joint,b2StepContext* context)
{port14JointEvent(joint,context,1);port14OriginalRWarm(joint,context);}
extern void port14OriginalRSolve(b2JointSim*,b2StepContext*,bool);
void b2SolveRevoluteJoint(b2JointSim* joint,b2StepContext* context,bool bias)
{port14JointEvent(joint,context,bias?2:3);port14OriginalRSolve(joint,context,bias);}
extern void port14OriginalPPrepare(b2JointSim*,b2StepContext*);
void b2PreparePrismaticJoint(b2JointSim* joint,b2StepContext* context)
{port14JointEvent(joint,context,0);port14OriginalPPrepare(joint,context);}
extern void port14OriginalPWarm(b2JointSim*,b2StepContext*);
void b2WarmStartPrismaticJoint(b2JointSim* joint,b2StepContext* context)
{port14JointEvent(joint,context,1);port14OriginalPWarm(joint,context);}
extern void port14OriginalPSolve(b2JointSim*,b2StepContext*,bool);
void b2SolvePrismaticJoint(b2JointSim* joint,b2StepContext* context,bool bias)
{port14JointEvent(joint,context,bias?2:3);port14OriginalPSolve(joint,context,bias);}
#endif
