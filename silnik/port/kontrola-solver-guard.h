                                                                                 
                                                                              
static bool body_blocks_fit10(uint64_t count)
{
    uint64_t base=32,blocks=count?(count-1)/32+1:0;
    if(count>128){base=count/4;blocks=4;}
    if(!blocks)return true;
    if(blocks>1&&base>INT16_MAX)return false;
    uint64_t last=count-(blocks-1)*base;
    return last>0&&last<=INT16_MAX;
}
static bool contact_blocks_fit10(uint64_t count)
{return count<=16||count/4+3<=INT16_MAX;}
static bool checked_sum10(uint64_t count,uint64_t added,uint64_t* value)
{
    *value=0;
    if(count>INT64_MAX||added>INT64_MAX||count>(uint64_t)INT64_MAX-added)return false;
    *value=count+added;return true;
}
static uint64_t guard_count10(uint32_t low,uint32_t high)
{
    if(high>INT32_MAX)fail("INPUT_DOMAIN");
    return (uint64_t)low|((uint64_t)high<<32);
}
static void guard_result10(uint32_t seq,int helper,int status,uint64_t value)
{
    printf("GR10 1 %"PRIu32" %d",seq,helper);word((uint32_t)status);word(status==OK);wide(value);putchar('\n');
}
static uint64_t replace_half10(uint64_t value,int high,uint32_t replacement)
{return high?((value&UINT32_MAX)|((uint64_t)replacement<<32)):((value&(~UINT64_C(0)<<32))|replacement);}
static void seed_guard10(const uint32_t* a,int kind,uint32_t seq)
{
    if(kind==4){lastIssued=(uint64_t)a[1]|((uint64_t)a[2]<<32);guardSeedApplied10=true;return;}
    if(kind!=8)return;
    guardSeedApplied10=true;
    int selector=(int)a[0],owner=(int)a[1],source=(int)a[2],field=(int)a[3],status=STALE;
    uint32_t replacement=a[4];
    if(!worlds[owner].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    if(selector==0){World number=worlds[owner];
        if(field==3||field==4)number.birth=replace_half10(number.birth,field==4,replacement);
        else if(field==5)number.raw.index1=replacement<UINT16_MAX?(uint16_t)(replacement+1u):0;
        status=world_live(&number)?OK:STALE;
    }else if(selector==1){
        if(!bodies[source].saved)fail("INPUT_REGISTER_UNINITIALIZED");Body number=bodies[source];
        if(field==1||field==2)number.owner=replace_half10(number.owner,field==2,replacement);
        else if(field==3||field==4)number.birth=replace_half10(number.birth,field==4,replacement);
        else if(field==5)memcpy(&number.raw.index1,&(uint32_t){replacement+1u},4);
        status=guard(worlds+owner,&number);
    }else if(selector==2){
        if(!shapes[source].saved)fail("INPUT_REGISTER_UNINITIALIZED");Shape number=shapes[source];
        if(field==1||field==2)number.owner=replace_half10(number.owner,field==2,replacement);
        else if(field==3||field==4)number.birth=replace_half10(number.birth,field==4,replacement);
        else if(field==5)memcpy(&number.raw.index1,&(uint32_t){replacement+1u},4);
        status=shape_guard(worlds+owner,&number);
    }else{
        if(!saved9[source].saved)fail("INPUT_REGISTER_UNINITIALIZED");Number9 number=saved9[source].number;
        if(field==1||field==2)number.owner=replace_half10(number.owner,field==2,replacement);
        else if(field==3||field==4)number.birth=replace_half10(number.birth,field==4,replacement);
        else if(field==5)memcpy(&number.slot,&replacement,4);
        if(world_live(worlds+owner)){
            b2World* w=b2GetWorldFromId(worlds[owner].raw);
            if(field==5&&number.slot==w->contactIdPool.nextIndex&&number.slot>=0){
                int original=saved9[source].number.slot;
                if(original>=0&&original<w->contactIdPool.nextIndex){
                    b2Contact seeded=w->contacts.data[original];seeded.contactId=number.slot;
                    if(w->contacts.count<=number.slot)b2ContactArray_Resize(&w->contacts,number.slot+1);
                    w->contacts.data[number.slot]=seeded;
                    if(number.slot>=CONTACTS9)fail("INPUT_POPULATION");
                    meta9[owner].birth[number.slot]=number.birth;
                }
            }
            if((field==6||field==7)&&number.slot>=0&&number.slot<w->contactIdPool.nextIndex){
                b2Contact original=w->contacts.data[number.slot];
                if(field==6)memcpy(&w->contacts.data[number.slot].contactId,&replacement,4);
                else memcpy(&w->contacts.data[number.slot].setIndex,&replacement,4);
                status=contact_status9(owner,number);w->contacts.data[number.slot]=original;
            }else status=contact_status9(owner,number);
        }else status=contact_status9(owner,number);
    }
    guard_result10(seq,10+selector,status,0);
}
static int guard_main10(FILE* input)
{
    char* p=row(input);int id,kind,seed,ops;
    if(strncmp(p,"G ",2))fail("INPUT_TAG");arity10(p,5);p+=2;
    id=(int)decimal(&p);space(&p);kind=(int)decimal(&p);space(&p);seed=(int)decimal(&p);space(&p);ops=(int)decimal(&p);
    if(*p)fail("INPUT_ARITY");if(id!=1)fail("INPUT_ID");
    if(kind<0||kind>8||kind==5||kind==7)fail("INPUT_ENUM");
    bool operations=kind==0||kind==4||kind==8;
    if((operations&&(ops<1||ops>16||seed<0||seed>ops))||(!operations&&(ops||seed)))fail("INPUT_OPCOUNT");
    int prefix[1];uint32_t a[64];fields10(input,"GA",1,64,prefix,a);if(prefix[0]!=1)fail("INPUT_ID");
    int used=kind==1?11:kind==2?2:kind==3?5:kind==4?3:kind==6?4:kind==8?5:0;
    if(kind==1){if(a[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");if(a[1]>1||a[10]>1)fail("INPUT_BOOL");}
    if(kind==3){if(a[0]>2)fail("INPUT_ENUM");if(a[0]!=2&&(a[3]||a[4]))fail("INPUT_UNUSED");}
    if(kind==4&&a[0]>=WORLDS)fail("INPUT_REGISTER_RANGE");
    if(kind==8){
        if(a[0]>3||a[3]>7||(a[0]!=3&&a[3]>5))fail("INPUT_ENUM");
        if(a[1]>=WORLDS||a[2]>=(a[0]==2?SHAPES:BODIES))fail("INPUT_REGISTER_RANGE");
        if(a[0]==0&&a[2])fail("INPUT_UNUSED");
    }
    for(int j=used;j<64;++j)if(a[j])fail("INPUT_UNUSED");
    bool accepted=false;int helper=0;uint64_t value=0;
    if(kind==1){Operation parameters={0};for(int j=0;j<11;++j){parameters.u[j]=a[j];parameters.f[j]=from_bits(a[j]);}accepted=valid_solver_world10(&parameters);}
    else if(kind==2){int count;memcpy(&count,a+1,4);helper=1;accepted=valid_step(from_bits(a[0]),count);}
    else if(kind==3){
        helper=2+(int)a[0];uint64_t count=guard_count10(a[1],a[2]),added=guard_count10(a[3],a[4]);value=count;
        accepted=a[0]==0?body_blocks_fit10(count):a[0]==1?contact_blocks_fit10(count):checked_sum10(count,added,&value);
    }else if(kind==6){uint32_t material[64]={0};memcpy(material+45,a,4*sizeof(*a));helper=9;accepted=material9(material);}
    guardMode10=true;case9=1;reset_case10();
    printf("GUARD10 1\nG 1 %d %d %d\nGA 1",kind,seed,ops);for(int j=0;j<64;++j)word(a[j]);printf("\nCASE 1 %d\n",ops);
    if(!operations)guard_result10(0,helper,accepted?OK:kind==3?LIMIT:PARAM,value);
    else{
        if(!seed)seed_guard10(a,kind,0);
        for(uint32_t seq=1;seq<=(uint32_t)ops;++seq){
            run_row10(input,seq);
            if(seq==(uint32_t)seed)seed_guard10(a,kind,seq);
        }
        for(int j=0;j<WORLDS;++j)if(worlds[j].live)destroy_world(j);
    }
    printf("ENDCASE 1\n");if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input)||fclose(input))fail("INPUT_DOMAIN");
    printf("END 1\n");free_tokens();return (ferror(stdout)||fflush(stdout))?2:0;
}
