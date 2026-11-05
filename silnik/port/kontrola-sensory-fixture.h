                                                                                  
static unsigned fixtureRoute17;
static const uint32_t *fixtureContext17,*fixturePayload17;
static int fixtureLength17,fixtureCalls17;
static Gate17 fixtureResult17;

static Operation fixtureShape17(int dst,int parent,bool sensor)
{
    Operation o={.code=400};uint32_t* a=o.u;
    a[0]=dst;a[2]=parent;a[6]=to_bits(sensor?1.0f:.2f);
    a[44]=to_bits(1);a[45]=to_bits(.6f);a[50]=1;
    a[52]=a[53]=UINT32_MAX;a[59]=sensor;a[60]=a[61]=1;
    return o;
}

static void fixtureBody17(int reg,int kind,float x,bool enabled)
{
    b2BodyDef d=b2DefaultBodyDef();d.type=kind;d.position.x=x;d.isEnabled=enabled;
    if(create_body(reg,0,d))fail("INPUT_FIXTURE");
}

static void fixtureHook17(int kind,int flag,int function)
{
    Operation o={.code=86,.u={0,0,kind,flag,function}};
    if(install12(&o))fail("INPUT_FIXTURE");
}

static int fixtureStep17(float dt)
{
    Operation o={.code=31,.u={0,0,4}};o.u[1]=to_bits(dt);o.f[1]=dt;
                                                                            
                                                                                
    finals11[0].present=false;
    int st=step10(&o);freshBegin17[0]=true;refresh17();return st;
}

static void fixtureWorld17(const uint32_t* c)
{
    b2WorldDef d=b2DefaultWorldDef();d.gravity=b2Vec2_zero;d.enableContinuous=false;
    d.workerCount=1;d.enqueueTask=port9Enqueue;d.finishTask=port9Finish;
    if(create_world(0,d))fail("INPUT_FIXTURE");sync_hooks12();
    memset(&meta9[0],0,sizeof(meta9[0]));metadataOwner9[0]=worlds[0].birth;
    fixtureBody17(0,0,0,c[32]!=0);fixtureBody17(1,2,0,true);
    Operation s=fixtureShape17(0,0,c[19]!=0);s.u[60]=c[30];
    if(create17(&s))fail("INPUT_FIXTURE");
    s=fixtureShape17(1,1,false);if(create17(&s))fail("INPUT_FIXTURE");
}

static Gate17 fixtureCall17(unsigned route,const uint32_t* c,const uint32_t* p,int length)
{
    int st=0;reason17=0;int target=(int32_t)c[18]<0?1:0;
    if(route<=8){
        if(b2GetWorldFromId(worlds[0].raw)->locked)return (Gate17){7,1};
        Gate17 gate=gate17(c,p,route,length);if(gate.status)return gate;
        Operation o={.code=400};memcpy(o.u,p+(route>=6?57:0),63*4);
        o.u[0]=4;o.u[1]=0;o.u[2]=route>=6?4:0;
        if(route>=6){Operation bd={0};memcpy(bd.u,p,57*4);for(int j=0;j<57;j++)bd.f[j]=from_bits(p[j]);
            b2BodyDef d=body11(&bd);d.isEnabled=p[19];d.isBullet=p[56];
            st=create_body(4,0,d);if(st)return (Gate17){st,0};}
        st=create17(&o);
    }else if(route>=9&&route<=14){
        st=access17(0,target,true,route!=10&&route!=11,route>=12,route>=12);
        if(!st){
            b2ShapeId raw=shapes[target].raw;
            if(route==9)b2Shape_EnableSensorEvents(raw,p[3]);
            if(route==10)(void)b2Shape_IsSensor(raw);
            if(route==11)(void)b2Shape_AreSensorEventsEnabled(raw);
            if(route==12)(void)b2Shape_GetSensorCapacity(raw);
            if(route==13||route==14){b2ShapeId ids[128];Touch17 values[128];int n=b2Shape_GetSensorOverlaps(raw,ids,128);
                for(int j=0;j<n;j++)visitor17(0,raw.index1-1,ids[j],false,values[j].u);
                if(route==14){Rows17 r={.saved=true,.count={n,0},.list={values,NULL}};saveRows17(overlapCopies17+p[2],&r);}}
        }
    }else if(route==15){
        b2World* w=b2GetWorldFromId(worlds[0].raw);
        if(w->locked){st=7;reason17=1;}
        else if(w->sensors.count&&w->customFilterFcn){st=PARAM;reason17=20;}
        else{Rows17 r=currentEvents17(0);saveRows17(eventCopies17+p[2],&r);clearRows17(&r);}
    }else if(route==16){Operation o={.code=86};memcpy(o.u,p,7*4);o.u[0]=0;st=install12(&o);if(st==7)reason17=1;}
    else if(route==17||route==18){Operation o={.code=32};memcpy(o.u,p,4*4);o.u[0]=0;
        for(int j=0;j<4;j++)o.f[j]=from_bits(o.u[j]);st=step10(&o);
        if(!st){freshBegin17[0]=true;refresh17();}}
    else fail("INPUT_FIXTURE");
    return (Gate17){st,reason17};
}

static void port17PreSolveRoute(void)
{
    if(fixtureCalls17++)return;
    fixtureResult17=fixtureCall17(fixtureRoute17,fixtureContext17,fixturePayload17,fixtureLength17);
}

static Gate17 fixtureOwned17(unsigned route,const uint32_t* p)
{
    if(fixtureStep17(1.0f/60))fail("INPUT_FIXTURE");
    if(route==19&&p[2]==1){b2Body_SetTransform(bodies[1].raw,(b2Vec2){4,0},b2Rot_identity);
        if(fixtureStep17(1.0f/60))fail("INPUT_FIXTURE");}
    Rows17 rows={0};
    if(route==19)rows=currentEvents17(0);
    else{b2ShapeId ids[128];int n=b2Shape_GetSensorOverlaps(shapes[0].raw,ids,128);
        rows.saved=true;rows.count[0]=n;rows.list[0]=calloc(n,sizeof(Touch17));
        if(n&&!rows.list[0])fail("INPUT_DOMAIN");
        for(int j=0;j<n;j++)visitor17(0,shapes[0].raw.index1-1,ids[j],false,rows.list[0][j].u);}
    Rows17* banks=route==19?eventCopies17:overlapCopies17;
    saveRows17(banks,&rows);saveRows17(banks+1,&rows);clearRows17(&rows);
    int list=route==19?p[2]:0;if(!banks[0].count[list])fail("INPUT_FIXTURE");
    if(p[1])banks[0].list[list][0].u[p[0]]^=1;
    destroy_world(0);
    b2WorldDef d=b2DefaultWorldDef();d.gravity=b2Vec2_zero;d.enableContinuous=false;
    d.workerCount=1;d.enqueueTask=port9Enqueue;d.finishTask=port9Finish;
    if(create_world(0,d))fail("INPUT_FIXTURE");sync_hooks12();
    memset(&meta9[0],0,sizeof(meta9[0]));metadataOwner9[0]=worlds[0].birth;
    return (Gate17){0,0};
}

static Gate17 fixtureWrap17(const uint32_t* p)
{
    if(fixtureStep17(1.0f/60))fail("INPUT_FIXTURE");
    Shape old=shapes[1];Rows17 rows=currentEvents17(0);saveRows17(eventCopies17,&rows);clearRows17(&rows);
    b2DestroyShape(shapes[1].raw,true);shapes[1].live=false;
    Operation churn={.code=20,.u={0,1,2,65536,1}};
    churnWork17(&churn,false);
    register17();b2Shape_EnableSensorEvents(shapes[2].raw,true);
    if(fixtureStep17(1.0f/60))fail("INPUT_FIXTURE");
    if(p[0]!=65536)fail("INPUT_FIXTURE");
    if(p[1])return (Gate17){shape_guard(worlds,shapes+2),0};
    return (Gate17){shape_guard(worlds,&old),0};
}

static Gate17 state17(unsigned id,unsigned phase,unsigned route,const uint32_t* c,const uint32_t* p,int length)
{
    if(id==630||id==633)fail("INPUT_FIXTURE");                              
    for(int w=0;w<16;w++)if(worlds[w].live)destroy_world(w);
    reset17(id);resetOperation14(id,phase);traceCount17=0;reason17=0;
    resultWorld17=resultShape17=-1;listCount17=0;
    fixtureWorld17(c);Gate17 result;
    if(route==19||route==20)result=fixtureOwned17(route,p);
    else if(route==21)result=fixtureWrap17(p);
    else{
        if(c[20])fixtureHook17(0,1,0);
        if(c[17]){
            fixtureBody17(2,0,10,true);fixtureBody17(3,2,10.1f,true);
            for(int reg=2;reg<=3;reg++){Operation s=fixtureShape17(reg,reg,false);s.u[6]=to_bits(1);s.u[62]=1;
                if(create17(&s))fail("INPUT_FIXTURE");}
            fixtureRoute17=route;fixtureContext17=c;fixturePayload17=p;fixtureLength17=length;fixtureCalls17=0;
            fixtureHook17(1,1,9);if(fixtureStep17(1.0f/60)||fixtureCalls17!=1)fail("INPUT_FIXTURE");
            result=fixtureResult17;
        }else result=fixtureCall17(route,c,p,length);
    }
    refresh17();printf("G17 %u %u %d %d %d 0\n",id,phase,result.status,result.reason,result.status==0);
    Operation marker={.code=400};status14=result.status;
    dump(id,phase,0,0,0,-1);
    if(OBS)for(int q=0;q<traceCount17;q++){printf("Q17 %u %u %u %d 4",id,phase,trace17[q][0],q);for(int k=1;k<5;k++)word(trace17[q][k]);putchar('\n');}
    finishOperation14(&marker);
    return result;
}
