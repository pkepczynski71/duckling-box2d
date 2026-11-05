                                                                             
                                                                         
                                                                           
typedef struct Rule12 {
    Number9 a,b;bool allow,replace; b2Vec2 direction,normal;float threshold,value;int ma,mb;
} Rule12;
typedef struct Hooks12 {
    uint64_t birth;int owner;bool installed[4],game[4];uint32_t function[4],context[2][2];
    int count[4];Rule12 rules[4][16];
    b2FrictionCallback* defaultFriction;b2RestitutionCallback* defaultRestitution;
} Hooks12;
typedef struct Trace12 {int owner,kind; b2ShapeId a,b;bool allow;b2Manifold before,after;float x,y,result;int ma,mb;} Trace12;
typedef struct Value12 {Number9 contact,a,b;bool touching;b2Manifold manifold;} Value12;
typedef struct List12 {bool saved;int status,count;Value12 values[512];} List12;
static Hooks12 hooks12[WORLDS];
static Trace12* trace12;static size_t traceCount12,traceCapacity12;
static uint32_t (*callbackAP12)[4];static size_t callbackAPCount12,callbackAPCapacity12;
static List12 copies12[4],readList12;
static int readShape12=-1,copyMutation12=-1,hookOwner12;
static int lockRoute12=-1,lockStatus12=-1;

static void* grow12(void* data,size_t* capacity,size_t used,size_t item)
{
    if(used<*capacity)return data;
    size_t next=*capacity?2**capacity:32;
    if(next<*capacity||next>SIZE_MAX/item)fail("INPUT_POPULATION");
    void* value=realloc(data,next*item);if(!value)fail("INPUT_DOMAIN");*capacity=next;return value;
}
static Trace12* new_trace12(int owner,int kind)
{
    trace12=grow12(trace12,&traceCapacity12,traceCount12,sizeof(*trace12));
    Trace12* t=trace12+traceCount12++;memset(t,0,sizeof(*t));t->owner=owner;t->kind=kind;return t;
}
static bool same_number12(Number9 a,Number9 b){return a.slot==b.slot&&a.birth==b.birth&&a.owner==b.owner;}
static int mutation_world12(int owner)
{
    if(!world_live(worlds+owner))return STALE;
    if(b2GetWorldFromId(worlds[owner].raw)->locked){reason12=1;return 7;}return OK;
}
static bool filter_value12(Hooks12* h,b2ShapeId a,b2ShapeId b)
{
    if(!h->game[0])return h->function[0]!=1;
    Number9 na=shape_number9(a),nb=shape_number9(b);
    for(int j=0;j<h->count[0];++j){Rule12* r=h->rules[0]+j;
        if(same_number12(na,r->a)&&same_number12(nb,r->b))return r->allow;}
    return true;
}
static bool filter12(b2ShapeId a,b2ShapeId b,void* context)
{
    Hooks12* h=context;bool value=filter_value12(h,a,b);
    Trace12* t=new_trace12(h->owner,0);t->a=a;t->b=b;t->allow=value;return value;
}
static bool predict_filter12(b2ShapeId a,b2ShapeId b,void* context)
{return filter_value12(context,a,b);}
static int port12Prepare(b2World* w,b2ShapeId* first,b2ShapeId* second,bool capture)
{
                                                                        
                                                                              
    b2CustomFilterFcn* saved=w->customFilterFcn;void* context=w->customFilterContext;
    int owner=owner9(w);w->customFilterFcn=hooks12[owner].installed[0]?predict_filter12:NULL;
    w->customFilterContext=hooks12+owner;
    int result=port9Prepare(w,first,second,capture);
    w->customFilterFcn=saved;w->customFilterContext=context;return result;
}
static void callback_ap12(int status,int reason,int kind,int reg)
{
    callbackAP12=grow12(callbackAP12,&callbackAPCapacity12,callbackAPCount12,sizeof(*callbackAP12));
    uint32_t* v=callbackAP12[callbackAPCount12++];v[0]=status;v[1]=reason;v[2]=kind;v[3]=reg;
}
static bool pre12(b2ShapeId a,b2ShapeId b,b2Manifold* manifold,void* context)
{
    Hooks12* h=context;Trace12* t=new_trace12(h->owner,1);t->a=a;t->b=b;t->before=*manifold;
    bool allow=true;
    if(lockRoute12>=0){lockStatus12=locked_call12();}
    else if(h->game[1]){
        Number9 na=shape_number9(a),nb=shape_number9(b);
        for(int j=0;j<h->count[1];++j){Rule12* r=h->rules[1]+j;
            float x=manifold->normal.x*r->direction.x,y=manifold->normal.y*r->direction.y,dot=x+y;
            if(same_number12(na,r->a)&&same_number12(nb,r->b)&&dot>=r->threshold){
                allow=r->allow;if(allow&&r->replace)manifold->normal=r->normal;break;}}
    }else{
        switch(h->function[1]){
            case 1:allow=false;break;
            case 2:manifold->normal=(b2Vec2){0,1};break;
            case 4:{
                int world=mutation_world12(h->owner);callback_ap12(world,world==7,0,h->owner);
                int target=-1;for(int j=0;j<SHAPES;++j)if(shapes[j].live&&b2StoreShapeId(shapes[j].raw)==b2StoreShapeId(b))target=j;
                if(target<0)fail("INPUT_DOMAIN");
                int status=shape_guard(worlds+h->owner,shapes+target);if(!status)status=mutation_world12(h->owner);
                callback_ap12(status,status==7,2,target);status=mutation_world12(h->owner);callback_ap12(status,status==7,0,h->owner);break;
            }
            case 5:
                manifold->normal=(b2Vec2){0,1};
                for(int j=0;j<manifold->pointCount;++j){float delta=j==0?.25f:-.25f;
                    manifold->points[j].point.x+=delta;manifold->points[j].anchorA.x+=delta;manifold->points[j].anchorB.x+=delta;}break;
        }
    }
                                                                        
                                                                
    t->allow=allow;t->after=*manifold;return allow;
}
static float mix12(float a,int ma,float b,int mb,int kind)
{
    Hooks12* h=hooks12+hookOwner12;
    float result=0;bool matched=false;
    if(h->game[kind]){
        for(int j=0;j<h->count[kind];++j){Rule12* r=h->rules[kind]+j;if(r->ma==ma&&r->mb==mb){result=r->value;matched=true;break;}}
    }else if(h->function[kind]==3&&ma==3&&mb==5){result=kind==2?.5f:1.0f;matched=true;}
    if(!matched)result=kind==2?h->defaultFriction(a,ma,b,mb):h->defaultRestitution(a,ma,b,mb);
    Trace12* t=new_trace12(hookOwner12,kind);t->x=a;t->y=b;t->ma=ma;t->mb=mb;t->result=result;return result;
}
static float friction12(float a,int ma,float b,int mb){return mix12(a,ma,b,mb,2);}
static float restitution12(float a,int ma,float b,int mb){return mix12(a,ma,b,mb,3);}
static void sync_hooks12(void)
{
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live&&hooks12[owner].birth!=worlds[owner].birth){
        Hooks12* h=hooks12+owner;memset(h,0,sizeof(*h));h->owner=owner;h->birth=worlds[owner].birth;
        b2World* w=b2GetWorldFromId(worlds[owner].raw);h->defaultFriction=w->frictionCallback;h->defaultRestitution=w->restitutionCallback;}
}
static bool world_values12(const Operation* o)
{
    const uint32_t* a=o->u;int kind=a[2];bool game=a[1];
    if(kind==0)return true;
    if(kind==5)return isfinite(o->f[3])&&isfinite(o->f[4]);
    if(kind==4)return isfinite(o->f[3])&&o->f[3]>0;
    for(int j=3;j<(kind==3?6:4);++j)if(!isfinite(o->f[j])||(game&&o->f[j]<0))return false;
    return true;
}
static int world_mut12(const Operation* o)
{
    int owner=o->u[0],kind=o->u[2],status=world_live(worlds+owner)?OK:STALE;
    if(status)return status;if(o->u[1]&&(status=mutation_world12(owner)))return status;
    if(!world_values12(o)){if(!o->u[1])fail("INPUT_DOMAIN");return PARAM;}
    if(helperOnly12)return OK;b2WorldId id=worlds[owner].raw;
    if(kind==0)b2World_EnableWarmStarting(id,o->u[3]);
    else if(kind==1)b2World_SetRestitutionThreshold(id,o->f[3]);
    else if(kind==2)b2World_SetHitEventThreshold(id,o->f[3]);
    else if(kind==3)b2World_SetContactTuning(id,o->f[3],o->f[4],o->f[5]);
    else if(kind==4)b2World_SetMaximumLinearSpeed(id,o->f[3]);
    else b2World_SetGravity(id,(b2Vec2){o->f[3],o->f[4]});return OK;
}
static int rule12(const Operation* o)
{
    const uint32_t* a=o->u;int owner=a[0],kind=a[1],status=world_live(worlds+owner)?OK:STALE;
    if(status)return status;
    Rule12 r={0};
    if(a[2]&&kind<2){status=shape_guard(worlds+owner,shapes+a[3]);if(status)return status;
        status=shape_guard(worlds+owner,shapes+a[4]);if(status)return status;
        r.a=shape_number9(shapes[a[3]].raw);r.b=shape_number9(shapes[a[4]].raw);r.allow=a[5];}
    if((status=mutation_world12(owner)))return status;
    if(a[2]){
        if(kind==1){r.direction=(b2Vec2){o->f[6],o->f[7]};r.threshold=o->f[8];r.replace=a[9];r.normal=(b2Vec2){o->f[10],o->f[11]};
            if(!finite_vec(r.direction)||!isfinite(r.threshold)||(r.replace&&(!finite_vec(r.normal)||!b2IsNormalized(r.normal)))){reason12=4;return PARAM;}}
        if(kind>=2){r.ma=(int32_t)a[3];r.mb=(int32_t)a[4];r.value=o->f[5];if(!isfinite(r.value)||r.value<0){reason12=4;return PARAM;}}
    }
    if(helperOnly12)return OK;
    Hooks12* h=hooks12+owner;if(!a[2])h->count[kind]=0;
    else{if(h->count[kind]>=16)fail("INPUT_POPULATION");h->rules[kind][h->count[kind]++]=r;}
    return OK;
}
static int install12(const Operation* o)
{
    const uint32_t* a=o->u;int owner=a[0],kind=a[2],status=world_live(worlds+owner)?OK:STALE;
    if(status)return status;if(a[1]&&(status=mutation_world12(owner)))return status;
    Hooks12* h=hooks12+owner;h->installed[kind]=a[3];h->game[kind]=a[1];h->function[kind]=a[4];
    if(kind<2){h->context[kind][0]=a[5];h->context[kind][1]=a[6];}
    b2WorldId id=worlds[owner].raw;
    if(kind==0)b2World_SetCustomFilterCallback(id,a[3]?filter12:NULL,h);
    else if(kind==1)b2World_SetPreSolveCallback(id,a[3]?pre12:NULL,h);
    else if(kind==2)b2World_SetFrictionCallback(id,a[3]?friction12:NULL);
    else b2World_SetRestitutionCallback(id,a[3]?restitution12:NULL);
    return OK;
}
static List12 contact_list12(int owner,int reg,bool shape,int capacity)
{
    List12 result={0};result.saved=true;
    result.status=shape?shape_guard(worlds+owner,shapes+reg):guard(worlds+owner,bodies+reg);
    if(result.status)return result;
    b2ContactData data[512];
    int count=shape?b2Shape_GetContactData(shapes[reg].raw,data,capacity):b2Body_GetContactData(bodies[reg].raw,data,capacity);
    if(count<0||count>capacity)fail("INPUT_POPULATION");result.count=count;b2World* w=b2GetWorldFromId(worlds[owner].raw);
    for(int j=0;j<count;++j){b2ContactData* d=data+j;int slot=find_contact9(w,d->shapeIdA.index1-1,d->shapeIdB.index1-1);
        if(slot<0)fail("INPUT_DOMAIN");b2Contact* c=w->contacts.data+slot;
        result.values[j]=(Value12){{slot,meta9[owner].birth[slot],worlds[owner].birth},shape_number9(d->shapeIdA),shape_number9(d->shapeIdB),(c->flags&b2_contactTouchingFlag)!=0,d->manifold};}
    return result;
}
static int extended12(const Operation* o,int* kind,int* reg)
{
    const uint32_t* a=o->u;int owner=a[0],code=o->code,status;
    if(code==82||code==86||code==87){*kind=0;*reg=owner;
        return code==82?world_mut12(o):code==86?install12(o):rule12(o);}
    if(code==89){int action=a[0],copy=a[3];
        if(action>=2){*kind=0;*reg=copy;if(action==3)copyMutation12=copy;return OK;}
        owner=a[1];*reg=a[2];*kind=action+1;List12 value=contact_list12(owner,a[2],action==1,512);
        if(!value.status)copies12[copy]=value;return value.status;}
    if(code==88){*kind=2;*reg=a[2];readShape12=a[2];readList12=contact_list12(owner,a[2],true,a[1]?512:a[3]);return readList12.status;}
    bool shape=code==83?a[1]!=0:code==85?a[1]==2:false;
    *kind=code==85?a[1]:code==83?a[1]+1:1;*reg=code==84?a[1]:a[2];if(*kind==0)*reg=owner;
    status=*kind==0?(world_live(worlds+owner)?OK:STALE):shape?shape_guard(worlds+owner,shapes+*reg):guard(worlds+owner,bodies+*reg);
    if(status)return status;int mode=code==84?a[2]:a[3];if(mode&&(status=mutation_world12(owner)))return status;
    if(code==83){
        if(!shape&&a[4]==2){if(!mode)fail("INPUT_PROFILE");reason12=2;return PARAM;}
        if(shape){b2ShapeId id=shapes[*reg].raw;
            if(a[4]==0)b2Shape_EnableContactEvents(id,a[5]);else if(a[4]==1)b2Shape_EnableHitEvents(id,a[5]);else b2Shape_EnablePreSolveEvents(id,a[5]);}
        else{b2BodyId id=bodies[*reg].raw;if(a[4]==0)b2Body_EnableContactEvents(id,a[5]);else b2Body_EnableHitEvents(id,a[5]);}
    }else if(code==84){
        if(mode&&!utf8_12(a+5,a[4])){reason12=3;return PARAM;}
        char text[33]={0};for(uint32_t j=0;j<a[4];++j)text[j]=(char)a[5+j];b2Body_SetName(bodies[*reg].raw,a[3]?NULL:text);
    }else{
        void* value=token(a[4],a[5],a[6]);
        if(*kind==0)b2World_SetUserData(worlds[owner].raw,value);
        else if(*kind==1)b2Body_SetUserData(bodies[*reg].raw,value);else b2Shape_SetUserData(shapes[*reg].raw,value);
    }
    return OK;
}
static void raw_shape12(b2ShapeId id){word(id.index1);word(id.world0);word(id.generation);}
static void print_list12(const List12* list,int kind,int reg,int phase)
{
    printf("CL12 %d %"PRIu32" %d %d %d",case9,seq9,kind,reg,phase);word(list->status);word(list->count);putchar('\n');++counts12[7];
    for(int j=0;j<list->count;++j){Value12 v=list->values[j];printf("CV12 %d %"PRIu32" %d %d %d %d",case9,seq9,kind,reg,phase,j);
        number9(v.contact);number9(v.a);number9(v.b);word(v.touching);manifold9(v.manifold);putchar('\n');++counts12[8];}
}
static void observe_hooks12(void)
{
    for(size_t j=0;j<callbackAPCount12;++j){prefix12("AP12",0,0,0);for(int k=0;k<4;++k)word(callbackAP12[j][k]);putchar('\n');++counts12[0];}
    for(int owner=0;owner<WORLDS;++owner)if(worlds[owner].live){Hooks12* h=hooks12+owner;b2World* w=b2GetWorldFromId(worlds[owner].raw);
        if(OBS&&((w->customFilterFcn!=NULL)!=h->installed[0]||(w->preSolveFcn!=NULL)!=h->installed[1]||
            (w->frictionCallback!=h->defaultFriction)!=h->installed[2]||(w->restitutionCallback!=h->defaultRestitution)!=h->installed[3]))fail("INPUT_DOMAIN");
        prefix12("HC12",owner,0,1);uint32_t mask=0;for(int k=0;k<4;++k)mask|=h->installed[k]<<k;word(mask);
        for(int k=0;k<4;++k)word(h->function[k]);for(int k=0;k<2;++k){word(h->context[k][0]);word(h->context[k][1]);}
        for(int k=0;k<4;++k)word(h->count[k]);putchar('\n');++counts12[4];
        for(int k=0;k<4;++k)for(int j=0;j<h->count[k];++j){Rule12* r=h->rules[k]+j;printf("HR12 %d %"PRIu32" %d %d %d",case9,seq9,owner,k,j);
            if(k<2){number9(r->a);number9(r->b);word(r->allow);if(k==1){vec(r->direction);real(r->threshold);word(r->replace);vec(r->normal);}}
            else{word(r->ma);word(r->mb);real(r->value);}putchar('\n');++counts12[5];}}
    for(size_t j=0;j<traceCount12;++j){Trace12* t=trace12+j;printf("HT12 %d %"PRIu32" %d %zu %d",case9,seq9,t->owner,j,t->kind);
        if(t->kind<2){raw_shape12(t->a);raw_shape12(t->b);word(t->allow);if(t->kind==1){manifold9(t->before);manifold9(t->after);}}
        else{real(t->x);word(t->ma);real(t->y);word(t->mb);real(t->result);}putchar('\n');++counts12[6];}
    if(readShape12>=0)print_list12(&readList12,1,readShape12,0);
    for(int k=0;k<4;++k)if(copies12[k].saved){print_list12(copies12+k,2,k,0);
        if(k==copyMutation12){List12 value=copies12[k];if(value.count)value.values[0].manifold.normal.x=123;
            if(value.count>=2){Value12 first=value.values[0];value.values[0]=value.values[1];value.values[1]=first;}
            print_list12(&value,2,k,1);print_list12(copies12+k,2,k,2);}}
}
