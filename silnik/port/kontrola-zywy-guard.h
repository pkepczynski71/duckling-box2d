                                                                            
                                                                             
                                                                 
static void guard_result12(uint32_t seq,int helper,int status,uint64_t value)
{printf("GR12 1 %"PRIu32" %d",seq,helper);word(status);word(status==OK);wide(value);putchar('\n');}
#include "zywy-seed.inc"
static bool upper_blocks12(uint64_t count){return count<=128||count/4+3<=INT16_MAX;}
static void setup_guard12(bool lock)
{
    b2WorldDef world=b2DefaultWorldDef();world.gravity=b2Vec2_zero;world.maximumLinearSpeed=100;
    world.contactHertz=30;world.contactDampingRatio=10;world.maxContactPushSpeed=3;world.restitutionThreshold=1;world.hitEventThreshold=1;
    world.enableSleep=!lock;world.enableContinuous=false;world.workerCount=1;world.enqueueTask=port9Enqueue;world.finishTask=port9Finish;
    if(create_world(0,world))fail("INPUT_DOMAIN");
    b2BodyDef body=b2DefaultBodyDef();body.type=lock?b2_staticBody:b2_dynamicBody;body.sleepThreshold=.05f;body.enableSleep=!lock;
    if(create_body(0,0,body))fail("INPUT_DOMAIN");
    uint32_t shape[64]={0};shape[4]=to_bits(1);shape[5]=1;shape[6]=1;shape[7]=1;shape[9]=shape[10]=UINT32_MAX;shape[17]=to_bits(1);
                                                                       
    if(create_shape(0,0,0,shape,false))fail("INPUT_DOMAIN");
    b2Shape_SetSurfaceMaterial(shapes[0].raw,(b2SurfaceMaterial){.friction=.5f,.userMaterialId=3});
    if(lock){body.type=b2_dynamicBody;body.position=(b2Vec2){0,1.5f};if(create_body(1,0,body)||create_shape(1,0,1,shape,false))fail("INPUT_DOMAIN");
        b2Shape_EnablePreSolveEvents(shapes[0].raw,true);b2Shape_EnablePreSolveEvents(shapes[1].raw,true);}
    sync_hooks12();
}
static int helper_live12(int code,const uint32_t* a)
{
    Operation o={0};o.code=code;for(int j=0;j<64;++j){o.u[j]=a[j];o.f[j]=from_bits(a[j]);}
    validate_new12(&o,false);
    int mode=code==82?1:code==87?-1:2;if(mode>=0&&a[mode]!=1)fail("INPUT_MODE");
    setup_guard12(false);
    if(code==87&&a[1]<2){b2BodyDef body=b2DefaultBodyDef();body.type=b2_dynamicBody;if(create_body(1,0,body))fail("INPUT_DOMAIN");
        uint32_t shape[64]={0};shape[4]=to_bits(1);shape[5]=shape[6]=shape[7]=1;shape[9]=shape[10]=UINT32_MAX;shape[17]=to_bits(1);
        if(create_shape(1,0,1,shape,false))fail("INPUT_DOMAIN");}
    if(code!=90)validate_new12(&o,true);
    helperOnly12=true;int status;
    if(code==80)status=body_mut12(&o);else if(code==81)status=shape_mut12(&o);else if(code==82)status=world_mut12(&o);
    else if(code==84)status=utf8_12(a+5,a[4])?OK:PARAM;
    else if(code==87)status=rule12(&o);else if(code==90)status=create12(&o);else status=vector_get12(&o);
    helperOnly12=false;destroy_world(0);return status;
}
static int helper_lock12(int code,const uint32_t* a)
{
    if(!(code==1||code==2||code==3||code==4||code>=10&&code<=13||code>=15&&code<=19||code==30||code==32||
        code>=34&&code<=36||code==40||code==55||code>=57&&code<=61||code>=80&&code<=87||code==90))fail("INPUT_DOMAIN");
    if(code>=80){Operation o={0};o.code=code;for(int j=0;j<64;++j){o.u[j]=a[j];o.f[j]=from_bits(a[j]);}validate_new12(&o,false);}
    setup_guard12(true);
    Operation syntax={0};syntax.code=code;for(int j=0;j<64;++j){syntax.u[j]=a[j];syntax.f[j]=from_bits(a[j]);}
    if(code<80)legacy_source12(&syntax);else validate_new12(&syntax,true);
    lockOperation12=syntax;hookOwner12=0;lockRoute12=code;lockStatus12=-1;
    Hooks12* h=hooks12;h->installed[1]=true;h->function[1]=0;b2World_SetPreSolveCallback(worlds[0].raw,pre12,h);
    b2World_Step(worlds[0].raw,1.0f/60.0f,1);
    int status=lockStatus12;lockRoute12=-1;destroy_world(0);if(status<0)fail("INPUT_DOMAIN");return status;
}
static bool copy_probe12(int kind,uint64_t* value)
{
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;wd.workerCount=1;wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
    if(create_world(0,wd))fail("INPUT_DOMAIN");b2BodyDef bd=b2DefaultBodyDef();bd.type=b2_dynamicBody;bd.isAwake=kind==9;
    if(create_body(0,0,bd))fail("INPUT_DOMAIN");bool good=false;
    if(kind==9){if(create_body(1,0,bd))fail("INPUT_DOMAIN");
        for(int j=0;j<4;++j)b2World_Step(worlds[0].raw,.125f,1);
        b2BodyEvents source=b2World_GetBodyEvents(worlds[0].raw);SavedMove first[2],second[2];
        if(source.moveCount==2){for(int j=0;j<2;++j){b2BodyMoveEvent event=source.moveEvents[j];
                first[j].body=public_body_number(event.bodyId);first[j].transform=event.transform;first[j].fellAsleep=event.fellAsleep;copy_object(first[j].object,event.userData);}
            memcpy(second,first,sizeof(first));
            first[0].fellAsleep=false;SavedMove changed=first[0];first[0]=first[1];first[1]=changed;first[0].object[1]^=1;
            b2BodyEvents reread=b2World_GetBodyEvents(worlds[0].raw);
            good=reread.moveCount==2&&second[0].fellAsleep&&second[1].fellAsleep&&reread.moveEvents[0].fellAsleep&&reread.moveEvents[1].fellAsleep&&
                b2StoreBodyId(second[0].body.raw)==b2StoreBodyId(reread.moveEvents[0].bodyId)&&b2StoreBodyId(second[1].body.raw)==b2StoreBodyId(reread.moveEvents[1].bodyId)&&
                second[0].object[1]==0&&second[1].object[1]==0&&reread.moveEvents[0].userData==NULL&&reread.moveEvents[1].userData==NULL;
            *value=(uint64_t)(reread.moveEvents[0].fellAsleep|(second[0].fellAsleep<<1))<<32|(uint32_t)reread.moveCount;
        }else *value=(uint32_t)source.moveCount;
    }else{
        bool first=!b2Body_IsAwake(bodies[0].raw),second=!b2Body_IsAwake(bodies[0].raw);float threshold=b2Body_GetSleepThreshold(bodies[0].raw);
        first=false;bool reread=!b2Body_IsAwake(bodies[0].raw);(void)first;
        good=second&&reread&&to_bits(threshold)==UINT32_C(0x3d4ccccd)&&to_bits(b2Body_GetSleepThreshold(bodies[0].raw))==UINT32_C(0x3d4ccccd);
        *value=((uint64_t)(reread|(second<<1))<<32)|reread;
    }
    destroy_world(0);return good;
}
static void seed_guard12(const uint32_t* a,int kind,uint32_t seq)
{
    if(kind==7){uint64_t value;bool valid=checked_sum10(guard_count10(a[1],a[2]),guard_count10(a[3],a[4]),&value);
        if(!worlds[a[0]].saved||!world_live(worlds+a[0]))fail("INPUT_REGISTER");
        guard_result12(seq+1,30,valid&&upper_blocks12(value)?OK:LIMIT,value);return;}
    if(kind==8&&a[0]==1&&(a[3]==6||a[3]==7)){
        if(!worlds[a[1]].saved||!bodies[a[2]].saved)fail("INPUT_REGISTER");int status=guard(worlds+a[1],bodies+a[2]);
        if(!status){b2World* w=b2GetWorldFromId(worlds[a[1]].raw);b2Body* b=w->bodies.data+bodies[a[2]].raw.index1-1;b2Body old=*b;
            if(a[3]==6)memcpy(&b->id,a+4,4);else memcpy(&b->setIndex,a+4,4);status=guard(worlds+a[1],bodies+a[2]);*b=old;}
        guardSeedApplied10=true;guard_result12(seq,11,status,0);return;}
    seed_base12(a,kind,seq);
}
static int guard_main12(FILE* input)
{
    profile12=9;profile11=8;guardMode10=true;reset12(1);
    physical12="INPUT_SEQUENCE";char* p=row(input);if(strncmp(p,"G ",2))fail("INPUT_SEQUENCE");arity12(p,5);p+=2;
    uint32_t id=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");space(&p);uint32_t kind=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");
    space(&p);uint32_t seed=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");space(&p);uint32_t ops=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");
    if(*p||id!=1)fail("INPUT_SEQUENCE");bool operations=kind==0||kind==4||kind==7||kind==8;
    bool live=kind==180||kind==181||kind==182||kind==184||kind==187||kind==190||kind==192;
    if(kind>10&&!live&&kind<200)fail("INPUT_DOMAIN");
    if((operations&&(ops<1||ops>16||seed>ops))||(!operations&&(ops||seed)))fail("INPUT_SEQUENCE");
    physical12="INPUT_WORDS";p=row(input);if(strncmp(p,"GA ",3))fail("INPUT_WORDS");arity12(p,66);p+=3;
    id=decimal12(&p,"INPUT_SEQUENCE","INPUT_SEQUENCE");if(id!=1)fail("INPUT_SEQUENCE");uint32_t a[64];for(int j=0;j<64;++j){space(&p);a[j]=hex_word(&p);}if(*p)fail("INPUT_WORDS");
    int used=kind==1?11:kind==2?2:kind==3?5:kind==4?3:kind==5?2:kind==6?4:kind==7||kind==8?5:0;
    if(kind<100){
        if(kind==1){if(a[0]>=WORLDS)fail("INPUT_REGISTER");if(a[1]>1||a[10]>1)fail("INPUT_BOOL");}
        if(kind==3){if(a[0]>2)fail("INPUT_DOMAIN");if(a[0]!=2&&(a[3]||a[4]))fail("INPUT_UNUSED");}
        if((kind==4||kind==7)&&a[0]>=WORLDS)fail("INPUT_REGISTER");if(kind==5&&a[0]>5)fail("INPUT_DOMAIN");
        if(kind==8){if(a[0]>3||a[3]>7||(a[0]!=1&&a[0]!=3&&a[3]>5))fail("INPUT_DOMAIN");
            if(a[1]>=WORLDS||a[2]>=(a[0]==2?SHAPES:BODIES))fail("INPUT_REGISTER");if(a[0]==0&&a[2])fail("INPUT_UNUSED");}
        for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
    }else if(live){Operation o={0};o.code=kind-100;for(int j=0;j<64;++j){o.u[j]=a[j];o.f[j]=from_bits(a[j]);}validate_new12(&o,false);}
    int status=PARAM,helper=0;uint64_t value=0;
                                                                            
                                                                               
    if(!operations)begin_output9();
    if(kind==1){Operation o={0};for(int j=0;j<11;++j){o.u[j]=a[j];o.f[j]=from_bits(a[j]);}status=valid_solver_world10(&o)?OK:PARAM;}
    else if(kind==2){int n;memcpy(&n,a+1,4);helper=1;status=valid_step(from_bits(a[0]),n)?OK:PARAM;}
    else if(kind==3){helper=2+a[0];uint64_t n=guard_count10(a[1],a[2]),added=guard_count10(a[3],a[4]);value=n;
        bool fit=a[0]==0?upper_blocks12(n):a[0]==1?contact_blocks_fit10(n):checked_sum10(n,added,&value);status=fit?OK:LIMIT;}
    else if(kind==5){helper=20+a[0];float threshold=from_bits(a[1]);status=isfinite(threshold)&&threshold>=0?OK:PARAM;}
    else if(kind==6){uint32_t material[64]={0};memcpy(material+45,a,4*sizeof(*a));helper=9;status=material9(material)?OK:PARAM;}
    else if(kind==9||kind==10){helper=kind==9?40:41;status=copy_probe12(kind,&value)?OK:PARAM;}
    else if(live){helper=1000+(kind-100);status=helper_live12(kind-100,a);}
    else if(kind>=200){helper=2000+(kind-200);status=helper_lock12(kind-200,a);}
    if(!operations){bool bad=ferror(output9)!=0;if(fclose(output9))bad=true;output9=NULL;free(outputBytes9);outputBytes9=NULL;outputSize9=0;if(bad)fail("INPUT_DOMAIN");}
    printf("GUARD12 1\nG 1 %"PRIu32" %"PRIu32" %"PRIu32"\nGA 1",kind,seed,ops);for(int j=0;j<64;++j)word(a[j]);printf("\nCASE 1 %"PRIu32"\n",ops);
    if(!operations)guard_result12(0,helper,status,value);
    else{if(!seed&&kind!=7)seed_guard12(a,kind,0);
        for(uint32_t seq=1;seq<=ops;++seq){run_row12(input,1,seq);if(seq==seed&&kind!=7)seed_guard12(a,kind,seq);}
        if(kind==7)seed_guard12(a,kind,ops);for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);}
    trailing12(input);if(fclose(input))fail("INPUT_DOMAIN");printf("ENDCASE 1\nEND 1\n");free_tokens();free(trace12);free(callbackAP12);return ferror(stdout)||fflush(stdout)?2:0;
}
