                                                                             
static void fixtureSeed14(const Operation* o)
{
    const uint32_t* a=o->u;unsigned f=a[0];
    if(f==12){for(int i=0;i<2;++i)if(!physicalBodySaved14[i]){physicalBodySaved14[i]=true;physicalBody14[i]=operandBody14[i]=bodies[i];}
        worlds[0].birth=(uint64_t)a[1]|(uint64_t)a[2]<<32;return;}
    if(f==9||f==10||f==11||f==14||f==15){
        for(int i=0;i<2;++i)if(!physicalBodySaved14[i]){physicalBodySaved14[i]=true;physicalBody14[i]=operandBody14[i]=bodies[i];}
        if(f==9){if(a[1]||a[2])fail("INPUT_UNUSED");operandBody14[1]=operandBody14[0];}
        else if(f==10||f==11)operandBody14[f-10].owner=(uint64_t)a[1]|(uint64_t)a[2]<<32;
        else operandBody14[f-14].birth=(uint64_t)a[1]|(uint64_t)a[2]<<32;
        return;}
    if(f==16){if(a[2])fail("INPUT_UNUSED");pendingKind14=f;pendingLow14=a[1];return;}
    if(!joints14[0].saved)fail("INPUT_REGISTER_UNINITIALIZED");
    Joint14* j=joints14;
    if(f==1){if(a[1]>65535)fail("INPUT_DOMAIN");if(a[2])fail("INPUT_UNUSED");
        b2World* w=b2GetWorldFromId(worlds[0].raw);w->joints.data[j->raw.index1-1].generation=a[1];j->raw.generation=a[1];}
    else if(f==2)j->owner=(uint64_t)a[1]|(uint64_t)a[2]<<32;
    else if(f==3)j->birth=(uint64_t)a[1]|(uint64_t)a[2]<<32;
    else if(f==4){if(a[2])fail("INPUT_UNUSED");j->slot=(int32_t)a[1];}
    else if(f==5||f==6||f==7||f==13){
        if(a[2])fail("INPUT_UNUSED");if((f==5||f==13)&&a[1]>1)fail("INPUT_BOOL");
        if(f==6&&a[1])fail("INPUT_UNUSED");if(f==7&&a[1]>7)fail("INPUT_ENUM");
        pendingKind14=f;pendingLow14=a[1];}
    else fail("INPUT_PROFILE");
}
static int typedGetter14(int owner,int reg)
{
    int status=jointStatus14(worlds[owner],joints14[reg]);if(status)return status;
    b2World* w=b2GetWorldFromId(worlds[owner].raw);
    int type=w->joints.data[joints14[reg].slot].type,selector=guardArgs14[2];int expected=selector==1||selector>=80&&selector<=92?4:selector>=64&&selector<=75?5:-1;
    if(PORT14_PART_B?(expected>=0?type!=expected:type==0):type==b2_distanceJoint){reason14=6;return PARAM;}
    return OK;                                                                   
}
static int copyProbe14(unsigned kind,uint64_t* value)
{
    if(kind>2)fail("INPUT_ENUM");
    if(!live14(joints14[0]))fail("INPUT_DOMAIN");
    Copy14 first=copies14[0],second=copies14[1],list=copies14[2];uint32_t description[21];memcpy(description,definition14[0],sizeof description);
    uint32_t originalView[51]={0};publicView14(joints14[0],originalView);
    bool correct=true;
    if(kind==0){if(first.kind!=1||second.kind!=1)fail("INPUT_COPY");copies14[0].view[38]^=1;
        uint32_t live[51]={0};publicView14(joints14[0],live);correct=memcmp(copies14+1,&second,sizeof second)==0&&(PORT14_PART_B?memcmp(live,originalView,viewCount14(jointTypes14[0])*sizeof(uint32_t))==0:to_bits(b2DistanceJoint_GetLength(joints14[0].raw))==second.view[38]);}
    else if(kind==1){if(list.kind!=2||list.count<1)fail("INPUT_COPY");copies14[3]=copies14[2];copies14[2].identity[0][3]^=1;
        b2JointId current[128];int count=b2Body_GetJoints(bodies[1].raw,current,128);
        correct=memcmp(copies14+3,&list,sizeof list)==0&&count==list.count&&current[0].index1==list.identity[0][0];}
    else{definition14[0][4]^=1;uint32_t live[51]={0};publicView14(joints14[0],live);correct=(PORT14_PART_B?memcmp(live,originalView,viewCount14(jointTypes14[0])*sizeof(uint32_t))==0:to_bits(b2DistanceJoint_GetLength(joints14[0].raw))==description[4])&&memcmp(copies14+1,&second,sizeof second)==0;}
    Copy14 changed[4];memcpy(changed,copies14,sizeof changed);uint32_t changedDescription[21];memcpy(changedDescription,definition14[0],sizeof changedDescription);
    b2DestroyJoint(joints14[0].raw);helperOnly14=false;
    Operation recreate={.code=201,.u={0,0,0,1,1,0}};if(create14(&recreate))correct=false;
    correct=correct&&memcmp(changed,copies14,sizeof changed)==0;
    destroy_world(0);
    correct=correct&&memcmp(changed,copies14,sizeof changed)==0&&memcmp(changedDescription,definition14[0],sizeof changedDescription)==0;
    *value=correct;return correct?OK:PARAM;
}
static int wrapProbe14(uint64_t* value)
{
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;wd.workerCount=1;
    wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
    if(create_world(0,wd))fail("INPUT_DOMAIN");sync_hooks12();
    b2BodyDef bd=b2DefaultBodyDef();bd.type=b2_staticBody;
    if(create_body(0,0,bd)||create_body(1,0,bd))fail("INPUT_DOMAIN");
    descriptions14[0]=true;memset(definition14[0],0,sizeof definition14[0]);
    definition14[0][4]=to_bits(1);definition14[0][10]=to_bits(100000);
    Operation create={.code=201,.u={1,0,0,1,0,0}};
    helperOnly14=false;if(create14(&create))fail("INPUT_DOMAIN");
    Joint14 historical=joints14[0];
    if(historical.raw.index1!=1||historical.raw.generation!=1)fail("INPUT_DOMAIN");
    b2DestroyJoint(historical.raw);create.u[4]=1;
    for(uint32_t i=0;i<65535;++i){
        if(create14(&create))fail("INPUT_DOMAIN");
        b2JointId actual=joints14[1].raw;
        if(!b2Joint_IsValid(actual)||actual.index1!=historical.raw.index1||actual.world0!=historical.raw.world0||actual.generation!=(uint16_t)(i+2))fail("INPUT_DOMAIN");
        b2DestroyJoint(actual);
    }
    if(create14(&create))fail("INPUT_DOMAIN");
    b2JointId current=joints14[1].raw;
    bool ok=current.index1==historical.raw.index1&&current.generation==historical.raw.generation&&
        b2Joint_IsValid(historical.raw)&&!live14(historical)&&live14(joints14[1]);
    validReg14=0;*value=ok;helperOnly14=true;return ok?STALE:PARAM;
}
static int blockProbe14(uint64_t* value)
{
    uint32_t count=guardArgs14[0],kind=guardArgs14[1];
    if(kind>2)fail("INPUT_ENUM");
    if(kind!=2){
                                                                   
                                                                      
                                                                             
        uint32_t size=count>16?count/4:4,blocks=count>16?4:count?(count-1)/4+1:0;
        uint64_t covered=0;
        for(uint32_t b=0;b<blocks;++b){uint32_t start=b*size,n=b+1==blocks?count-start:size;
            if(start!=covered||!n)fail("INPUT_DOMAIN");covered+=n;}
        if(covered!=count)fail("INPUT_DOMAIN");*value=(uint64_t)size<<32|blocks;return OK;
    }
    b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;wd.workerCount=1;
    wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
    if(create_world(0,wd))fail("INPUT_DOMAIN");sync_hooks12();
    b2BodyDef bd=b2DefaultBodyDef();bd.type=b2_staticBody;
    if(create_body(0,0,bd)||create_body(1,0,bd))fail("INPUT_DOMAIN");
    b2DistanceJointDef jd=b2DefaultDistanceJointDef();jd.bodyIdA=bodies[0].raw;jd.bodyIdB=bodies[1].raw;
    b2World* w=b2GetWorldFromId(worlds[0].raw);
    for(uint32_t i=0;i<count;++i){
        if(!reservation14(lastIssued,1,(uint32_t)w->jointIdPool.nextIndex))fail("INPUT_DOMAIN");
        b2JointId raw=b2CreateDistanceJoint(worlds[0].raw,&jd);++lastIssued;
        if(!b2Joint_IsValid(raw)||raw.index1!=(int32_t)i+1||raw.generation!=1||raw.world0!=w->worldId)fail("INPUT_DOMAIN");
    }
    if((uint32_t)b2GetIdCount(&w->jointIdPool)!=count||w->solverSets.data[b2_staticSet].jointSims.count!=(int32_t)count||
       w->solverSets.data[b2_awakeSet].jointSims.count||b2World_GetCounters(worlds[0].raw).jointCount!=(int32_t)count)fail("INPUT_DOMAIN");
    Operation step={.code=32};step.u[1]=to_bits(1.0f/60.0f);step.f[1]=1.0f/60.0f;step.u[2]=1;
    int status=step10(&step);if(status==OK)++positive11;else if(status==LIMIT)reason14=1;
    compact14=true;*value=count;return status;
}
static void guardHelper14(unsigned kind,unsigned seq)
{
    resetOperation14(case9,seq);opcode9=211;uint32_t* a=guardArgs14;uint64_t value=0;
    b2World* w=worlds[0].live?b2GetWorldFromId(worlds[0].raw):NULL;
    b2Joint savedJoint={0};Meta14 savedMeta={0};bool savedInUse=false;
    if(pendingKind14==5||pendingKind14==7){savedJoint=w->joints.data[0];
        if(pendingKind14==5)w->joints.data[0].setIndex=pendingLow14?savedJoint.setIndex:-1;
        else w->joints.data[0].type=pendingLow14;}
    if(pendingKind14==6){savedJoint=w->joints.data[1];savedMeta=metadata14[w->worldId][1];
        w->joints.data[1]=w->joints.data[0];w->joints.data[1].jointId=1;metadata14[w->worldId][1]=metadata14[w->worldId][0];}
    if(pendingKind14==13){savedInUse=w->inUse;w->inUse=pendingLow14;}
    helperOnly14=true;
    if(kind==1)status14=wrapProbe14(&value);
    else if(kind==2)status14=jointStatus14(worlds[a[0]],joints14[a[1]]);
    else if(kind==3||kind==6){Operation o={.code=a[2]};
        if(a[2]==201){uint32_t saved[21];int savedType=descriptionTypes14[15];bool init=descriptions14[15];memcpy(saved,definition14[15],sizeof saved);memcpy(definition14[15],a+4,sizeof saved);descriptionTypes14[15]=PORT14_PART_B?a[25]:0;descriptions14[15]=true;
            uint32_t args[]={1,a[0],kind==3?a[1]:0,kind==3?a[3]:1,1,15};memcpy(o.u,args,sizeof args);status14=create14(&o);
            memcpy(definition14[15],saved,sizeof saved);descriptions14[15]=init;descriptionTypes14[15]=savedType;
        }else if(a[2]==203){o.u[0]=1;o.u[1]=a[0];o.u[2]=a[1];o.u[3]=a[3];int n=mutationArity14(a[3]);if(n<0)fail("INPUT_ENUM");
            for(int i=0;i<n;++i){o.u[4+i]=a[4+i];o.f[4+i]=from_bits(a[4+i]);}status14=mutate14(&o);
        }else fail("INPUT_OPCODE");}
    else if(kind==4)status14=typedGetter14(a[0],a[1]);
    else if(kind==5){if(!callbackCount14||callbackStatus14<0)fail("INPUT_DOMAIN");status14=callbackStatus14;reason14=callbackReason14;}
    else if(kind==7){uint64_t last=(uint64_t)a[0]|(uint64_t)a[1]<<32;
        status14=reservation14(last,a[2],a[3])?OK:LIMIT;value=last+(status14?0:a[2]);}
    else if(kind==8){Operation o={.code=80,.u={a[0],a[1],1,a[2],a[3]}};helperOnly12=true;status14=body_mut12(&o);helperOnly12=false;
        if(reason14!=8)reason14=reason13?reason13:reason12;}
    else if(kind==9)status14=blockProbe14(&value);
    else if(kind==10)status14=copyProbe14(a[0],&value);
    else fail("INPUT_PROFILE");                                                           
    helperOnly14=false;
    if(pendingKind14==5||pendingKind14==7)w->joints.data[0]=savedJoint;
    if(pendingKind14==6){w->joints.data[1]=savedJoint;metadata14[w->worldId][1]=savedMeta;}
    if(pendingKind14==13)w->inUse=savedInUse;
    pendingKind14=-1;fixture11=fixture14;dump(case9,seq9,0,0,0,-1);
    jp14(0,16,kind,11,4);word(status14);word(status14==OK);wide(value);putchar('\n');
    Operation helper={.code=211};finishOperation14(&helper);
}
static int guardMain14(FILE* input,unsigned n)
{
    guardMode14=true;profile11=profile12=14;printf("PORT14 %c GUARD %u\n",PORT14_PART_B?'B':'A',n);
    for(unsigned id=1;id<=n;++id){resetCase14(id);char* p=row(input);if(strncmp(p,"G14 ",4))fail("INPUT_TAG");arity13(p,5,"INPUT_ARITY");p+=4;
        unsigned got=decimal13(&p);space(&p);unsigned kind=decimal13(&p);space(&p);unsigned seed=decimal13(&p);space(&p);unsigned count=decimal13(&p);
        if(got!=id)fail("INPUT_ID");if(kind>10)fail("INPUT_ENUM");if(count>64||seed>count||kind==0&&!count)fail("INPUT_OPCOUNT");
        p=row(input);if(strncmp(p,"GA14 ",5))fail("INPUT_TAG");arity13(p,66,"INPUT_ARITY");p+=5;got=decimal13(&p);if(got!=id)fail("INPUT_ID");
        for(int i=0;i<64;++i){space(&p);guardArgs14[i]=hex_word(&p);}if(*p)fail("INPUT_ARITY");
        int used=kind==0||kind==1?0:kind==2?2:kind==3?23:kind==4?3:kind==5||kind==6?22:kind==7||kind==8?4:kind==9?2:1;
        if(PORT14_PART_B&&(kind==3||kind==6)&&guardArgs14[2]==201)used=26;
        for(int i=used;i<64;++i)if(guardArgs14[i])fail("INPUT_UNUSED");
        if(guardArgs14[0]>=16&&(kind==2||kind==3||kind==4||kind==5||kind==6||kind==8))fail("INPUT_REGISTER_RANGE");
        if(guardArgs14[1]>=256&&(kind==2||kind==3||kind==4||kind==5||kind==6||kind==8))fail("INPUT_REGISTER_RANGE");
        printf("G14 %u %u %u %u\nGA14 %u",id,kind,seed,count,id);array14(guardArgs14,64);printf("CASE %u %u\n",id,count);
        for(unsigned seq=1;seq<=count;++seq)run14(input,id,seq);
        if(kind)guardHelper14(kind,count?count+1:0);
        printf("ENDCASE %u\n",id);for(int r=0;r<WORLDS;++r)if(worlds[r].live)destroy_world(r);
    }
    if(fgetc(input)!=EOF)fail("INPUT_TRAILING_DATA");if(ferror(input))fail("INPUT_DOMAIN");printf("END %u\n",n);return ferror(stdout)||fflush(stdout)?2:0;
}
