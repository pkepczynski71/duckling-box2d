                                                                             
                                                                         
static bool body_upper_fit11(uint64_t count)
{return count<=128||count/4+3<=INT16_MAX;}
static void probe_world11(bool asleep)
{
    b2WorldDef w=b2DefaultWorldDef();w.gravity=b2Vec2_zero;w.enableSleep=true;w.enableContinuous=false;
    if(create_world(0,w))fail("INPUT_DOMAIN");
    b2BodyDef d=b2DefaultBodyDef();d.type=b2_dynamicBody;d.isAwake=!asleep;
    if(create_body(0,0,d))fail("INPUT_DOMAIN");
}
static bool threshold_probe11(uint32_t route,float threshold)
{
    b2BodyDef d=b2DefaultBodyDef();d.type=b2_dynamicBody;d.sleepThreshold=threshold;
    if(route<5)return valid_body11(&d);                                                      
    probe_world11(false);bool valid=threshold11(threshold);
    if(valid)b2Body_SetSleepThreshold(bodies[0].raw,threshold);
    destroy_world(0);return valid;
}
static bool move_probe11(uint64_t* value)
{
    probe_world11(false);b2BodyDef d=b2DefaultBodyDef();d.type=b2_dynamicBody;
    if(create_body(1,0,d))fail("INPUT_DOMAIN");
    for(int j=0;j<4;++j)b2World_Step(worlds[0].raw,0.125f,1);
    b2BodyEvents source=b2World_GetBodyEvents(worlds[0].raw);bool good=source.moveCount==2;
    SavedMove first[2]={0},second[2]={0},saved[2]={0};
    if(good){for(int j=0;j<2;++j){b2BodyMoveEvent e=source.moveEvents[j];
            saved[j].body=public_body_number(e.bodyId);saved[j].transform=e.transform;
            copy_object(saved[j].object,e.userData);saved[j].fellAsleep=e.fellAsleep;}
        memcpy(first,saved,sizeof(first));memcpy(second,saved,sizeof(second));
        first[0].fellAsleep=false;SavedMove swap=first[0];first[0]=first[1];first[1]=swap;first[0].object[1]^=1;
    }
    b2BodyEvents reread=b2World_GetBodyEvents(worlds[0].raw);
    good=good&&reread.moveCount==2;
    if(good)for(int j=0;j<2;++j){uint32_t object[3];copy_object(object,reread.moveEvents[j].userData);
        good=good&&reread.moveEvents[j].fellAsleep&&second[j].fellAsleep
            &&b2StoreBodyId(reread.moveEvents[j].bodyId)==b2StoreBodyId(saved[j].body.raw)
            &&b2StoreBodyId(second[j].body.raw)==b2StoreBodyId(saved[j].body.raw)
            &&!memcmp(object,saved[j].object,sizeof(object))&&!memcmp(second[j].object,saved[j].object,sizeof(object));}
    uint64_t mask=(reread.moveCount>0&&reread.moveEvents[0].fellAsleep?1:0)|(second[0].fellAsleep?2:0);
    *value=(mask<<32)|(uint32_t)reread.moveCount;destroy_world(0);return good;
}
typedef struct SleepValue11 {Body number;bool awake,sleeping,enabled;float threshold;} SleepValue11;
static SleepValue11 sleep_value11(void)
{
    b2BodyId id=bodies[0].raw;bool awake=b2Body_IsAwake(id);
    return (SleepValue11){bodies[0],awake,b2Body_IsEnabled(id)&&b2Body_GetType(id)!=b2_staticBody&&!awake,
                         b2Body_IsSleepEnabled(id),b2Body_GetSleepThreshold(id)};
}
static bool state_probe11(uint64_t* value)
{
    probe_world11(true);SleepValue11 first=sleep_value11(),second=sleep_value11();
    first.sleeping=false;first.threshold=0;SleepValue11 reread=sleep_value11();
    bool good=second.sleeping&&reread.sleeping&&to_bits(second.threshold)==to_bits(0.05f)&&to_bits(reread.threshold)==to_bits(0.05f);
    *value=((uint64_t)((reread.sleeping?1:0)|(second.sleeping?2:0))<<32)|reread.sleeping;
    destroy_world(0);return good;
}
static void seed_guard11(const uint32_t* a,int kind,uint32_t seq)
{
    if(kind==7){uint64_t awake=guard_count10(a[1],a[2]),sleeping=guard_count10(a[3],a[4]),upper;
        bool sum=checked_sum10(awake,sleeping,&upper),accepted=false;
        if(sum&&awake<=INT_MAX&&sleeping<=INT_MAX){
            int owner=a[0];if(!worlds[owner].saved||!world_live(worlds+owner))fail("INPUT_REGISTER_UNINITIALIZED");
            b2World* w=b2GetWorldFromId(worlds[owner].raw);int next=w->solverSetIdPool.nextIndex,count=w->solverSets.count;
            int n=next<4?4:next;int* counts=calloc((size_t)n,sizeof(int));if(!counts)fail("INPUT_DOMAIN");
            if(w->solverSets.count<n)b2SolverSetArray_Resize(&w->solverSets,n);
            b2SolverSet slot3={0};if(count>3)slot3=w->solverSets.data[3];else w->solverSets.data[3]=slot3;
            for(int j=2;j<next;++j){counts[j]=w->solverSets.data[j].bodySims.count;w->solverSets.data[j].bodySims.count=0;}
            w->solverSetIdPool.nextIndex=n;w->solverSets.data[3].setIndex=3;
            w->solverSets.data[2].bodySims.count=(int)awake;w->solverSets.data[3].bodySims.count=(int)sleeping;
            accepted=body_upper_fit11(port11BodyUpper(w));
            for(int j=2;j<next;++j)w->solverSets.data[j].bodySims.count=counts[j];
            w->solverSets.data[3]=slot3;w->solverSets.count=count;w->solverSetIdPool.nextIndex=next;free(counts);
        }else if(sum)accepted=body_upper_fit11(upper);
        guard_result10(seq+1,30,accepted?OK:LIMIT,upper);return;
    }
    if(kind==8&&a[0]==1&&a[3]>=6){
        guardSeedApplied10=true;int owner=a[1],slot=a[2];if(!worlds[owner].saved||!bodies[slot].saved)fail("INPUT_REGISTER_UNINITIALIZED");
        int status=guard(worlds+owner,bodies+slot);
        if(!status){b2World* w=b2GetWorldFromId(worlds[owner].raw);int id=bodies[slot].raw.index1-1;
            b2Body saved=w->bodies.data[id];if(a[3]==6)memcpy(&w->bodies.data[id].id,a+4,4);else memcpy(&w->bodies.data[id].setIndex,a+4,4);
            status=guard(worlds+owner,bodies+slot);
            if(status==OK&&(w->bodies.data[id].id!=id||w->bodies.data[id].setIndex==B2_NULL_INDEX))status=STALE;
            w->bodies.data[id]=saved;}
        guard_result10(seq,11,status,0);return;
    }
    seed_guard10(a,kind,seq);
}
static int guard_main11(FILE* input)
{
    char* p=row(input);if(strncmp(p,"G ",2))fail("INPUT_TAG");arity10(p,5);p+=2;
    uint32_t id=decimal(&p);space(&p);uint32_t kind=decimal(&p);space(&p);uint32_t seed=decimal(&p);space(&p);uint32_t ops=decimal(&p);
    if(*p)fail("INPUT_ARITY");if(id!=1)fail("INPUT_ID");if(kind>10)fail("INPUT_DOMAIN");
    bool operations=kind==0||kind==4||kind==7||kind==8;
    if((operations&&(!ops||ops>16||seed>ops))||(!operations&&(ops||seed)))fail("INPUT_OPCOUNT");
    int prefix[1];uint32_t a[64];fields10(input,"GA",1,64,prefix,a);if(prefix[0]!=1)fail("INPUT_ID");
    int used=kind==1?11:kind==2||kind==5?2:kind==3||kind==7||kind==8?5:kind==4?3:kind==6?4:0;
    if(kind==1){if(a[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");if(a[1]>1||a[10]>1)fail("INPUT_BOOL");}
    if(kind==3){if(a[0]>2)fail("INPUT_DOMAIN");if(a[0]!=2&&(a[3]||a[4]))fail("INPUT_UNUSED");}
    if((kind==4||kind==7)&&a[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");
    if(kind==5&&a[0]>5)fail("INPUT_DOMAIN");
    if(kind==8){if(a[0]>3||a[3]>7||(a[0]!=1&&a[0]!=3&&a[3]>5))fail("INPUT_DOMAIN");
        if(a[1]>=WORLDS||a[2]>=(a[0]==2?SHAPES:BODIES))fail("INPUT_REGISTER_RANGE");if(a[0]==0&&a[2])fail("INPUT_UNUSED");}
    for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
                                                                             
    guardMode10=true;case9=1;reset_case10();positive11=0;
    bool accepted=false;int helper=0;uint64_t value=0;
    if(kind==1){Operation parameters={0};for(int j=0;j<11;++j){parameters.u[j]=a[j];parameters.f[j]=from_bits(a[j]);}accepted=valid_solver_world10(&parameters);}
    else if(kind==2){int n;memcpy(&n,a+1,4);helper=1;accepted=valid_step(from_bits(a[0]),n);}
    else if(kind==3){helper=2+a[0];uint64_t count=guard_count10(a[1],a[2]),add=guard_count10(a[3],a[4]);value=count;
        accepted=a[0]==0?body_upper_fit11(count):a[0]==1?contact_blocks_fit10(count):checked_sum10(count,add,&value);}
    else if(kind==5){helper=20+a[0];accepted=threshold_probe11(a[0],from_bits(a[1]));}
    else if(kind==6){uint32_t material[64]={0};memcpy(material+45,a,4*sizeof(*a));helper=9;accepted=material9(material);}
    else if(kind==9){helper=40;accepted=move_probe11(&value);}
    else if(kind==10){helper=41;accepted=state_probe11(&value);}
    printf("GUARD11 1\nG 1 %"PRIu32" %"PRIu32" %"PRIu32"\nGA 1",kind,seed,ops);
    for(int j=0;j<64;++j)word(a[j]);printf("\nCASE 1 %"PRIu32"\n",ops);
    if(!operations)guard_result10(0,helper,accepted?OK:kind==3?LIMIT:PARAM,value);
    else{if(!seed&&kind!=7)seed_guard11(a,kind,0);
        for(uint32_t seq=1;seq<=ops;++seq){run_row11(input,seq);if(seq==seed&&kind!=7)seed_guard11(a,kind,seq);}
        if(kind==7)seed_guard11(a,kind,ops);
        for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);}
    printf("ENDCASE 1\n");if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input)||fclose(input))fail("INPUT_DOMAIN");
    printf("END 1\n");free_tokens();return ferror(stdout)||fflush(stdout)?2:0;
}
