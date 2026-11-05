                                                                              
                                                                              
   
#define _GNU_SOURCE
#include "wybuch19-base14.inc"
#include "wybuch19-helpers.inc"
#include "wybuch19-fixtures.inc"

static int id19,seq19,profile19,ntrace19;static bool diagnostic19,trace19;
static const uint32_t* fixture19;
static bool bankSaved19[2];static uint32_t bank19[2][19];
static void fatal19(const char* reason){fprintf(stderr,"PORT19A: INPUT_%s\n",reason);exit(2);}
static void words19(const uint32_t* p,int n){for(int i=0;i<n;++i)fprintf(stdout," %08"PRIx32,p[i]);fputc('\n',stdout);}
static void discard19(void){if(output9){fclose(output9);output9=NULL;free(outputBytes9);outputBytes9=NULL;outputSize9=0;}}

void port19Trace(int phase,int shape,int body,float distance,b2Vec2 point,b2Vec2 direction,float perimeter,float scale,float magnitude,b2Vec2 impulse)
{
 if(!trace19)return;if(ntrace19>=64)fatal19("OUTPUT_LIMIT");int ordinal=ntrace19++;
 if(OBS19){uint32_t p[]={bits19(distance),bits19(point.x),bits19(point.y),bits19(direction.x),bits19(direction.y),bits19(perimeter),bits19(scale),bits19(magnitude),bits19(impulse.x),bits19(impulse.y)};
 fprintf(stdout,"X19 %d %d %d %d %d %d %d",id19,seq19,ordinal,shape,body,phase,phase==2?10:1);words19(p,phase==2?10:1);}
}

static b2ExplosionDef definition19(const uint32_t* a)
{return (b2ExplosionDef){(uint64_t)a[0]|(uint64_t)a[1]<<32,{float19(a[2]),float19(a[3])},float19(a[4]),float19(a[5]),float19(a[6])};}
static int domain19(const uint32_t* a)
{
 for(int i=2;i<7;++i)if(!isfinite(float19(a[i])))return 5;
 float r=float19(a[4]),fall=float19(a[5]);if(r<0||fall<0)return 5;
 float e=r+fall;if(!isfinite(e))return 5;
 float p[]={float19(a[2])-e,float19(a[3])-e,float19(a[2])+e,float19(a[3])+e};
 for(int i=0;i<4;++i)if(!isfinite(p[i]))return 5;return 0;
}
                                                                         
                                                                             
   
static int worldStatus19(World owner)
{
 if(owner.raw.index1<1||owner.raw.index1>128)return 1;
 if(!b2World_IsValid(owner.raw))return 1;b2World* w=b2GetWorldFromId(owner.raw);
 if(!w->inUse||w->worldId!=owner.raw.index1-1)return 1;
 if(!worlds[0].live||owner.birth!=worlds[0].birth||b2StoreWorldId(owner.raw)!=b2StoreWorldId(worlds[0].raw))return 1;return 0;
}
static int preflight19(uint32_t selector,const uint32_t* a,int* reason)
{
 World owner=worlds[0];b2World* w=b2GetWorldFromId(owner.raw);uint16_t savedId=w->worldId;bool savedLock=w->locked;
 b2WorldId temporary=b2_nullWorldId;*reason=0;
 if(selector==1)owner.raw.index1=0;
 else if(selector==2)owner.raw.index1=129;
 else if(selector==3||selector==4){b2WorldDef wd=b2DefaultWorldDef();b2WorldId old=b2CreateWorld(&wd);b2DestroyWorld(old);owner.raw=old;if(selector==4)temporary=b2CreateWorld(&wd);}
 else if(selector==5)w->worldId=127;
 else if(selector==6)owner.birth^=1;
 else if(selector==7)w->locked=true;
 int status=worldStatus19(owner);
 if(!status&&w->locked){status=7;*reason=1;}
 if(!status&&domain19(a)){status=5;*reason=25;}
 w->worldId=savedId;w->locked=savedLock;if(B2_IS_NON_NULL(temporary))b2DestroyWorld(temporary);return status;
}
static void save19(int bank)
{state19(bodies[0].raw,bank19[bank]);bodyNumber14(bodies[0].raw,bank19[bank]+14);bankSaved19[bank]=true;}
static void copies19(void)
{for(int i=0;i<2;++i)if(bankSaved19[i]){fprintf(stdout,"V19 %d %d %d 19",id19,seq19,i);words19(bank19[i],19);}}

                                                                                   
static void shape19(int slot,int parent,b2ShapeDef sd,b2Shape s)
{
 b2ShapeId raw=b2_nullShapeId;b2BodyId body=bodies[parent].raw;
 if(s.type==b2_circleShape)raw=b2CreateCircleShape(body,&sd,&s.circle);
 else if(s.type==b2_capsuleShape)raw=b2CreateCapsuleShape(body,&sd,&s.capsule);
 else if(s.type==b2_segmentShape)raw=b2CreateSegmentShape(body,&sd,&s.segment);
 else if(s.type==b2_polygonShape)raw=b2CreatePolygonShape(body,&sd,&s.polygon);
 if(!b2Shape_IsValid(raw))fatal19("DOMAIN");shapes[slot]=(Shape){true,true,raw,worlds[0].birth,++lastIssued};
}
static void step19(void)
{
 Operation step={.code=31,.u={0,fixture19[23],fixture19[22]}};step.f[1]=float19(fixture19[23]);
 if(step10(&step))fatal19("DOMAIN");++positive11;
}
static void scene19Create(const uint32_t* p)
{
 b2WorldDef wd=b2DefaultWorldDef();wd.gravity=(b2Vec2){0,float19(p[25])};wd.workerCount=1;wd.enableContinuous=false;
 wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
 if(create_world(0,wd))fatal19("DOMAIN");metadataOwner9[0]=worlds[0].birth;sync_hooks12();
 b2BodyDef bd=b2DefaultBodyDef();bd.type=p[0];bd.isEnabled=(p[1]&1)!=0;bd.isAwake=(p[1]&2)!=0;bd.fixedRotation=(p[1]&4)!=0;
 bd.position=(b2Vec2){float19(p[6]),float19(p[7])};bd.rotation=(b2Rot){float19(p[8]),float19(p[9])};bd.linearVelocity=(b2Vec2){float19(p[15]),float19(p[16])};bd.angularVelocity=float19(p[17]);
 if(create_body(0,0,bd))fatal19("DOMAIN");
 b2ShapeDef sd=b2DefaultShapeDef();sd.density=float19(p[18]);sd.isSensor=(p[1]&8)!=0;sd.filter.categoryBits=(uint64_t)p[4]|(uint64_t)p[5]<<32;sd.filter.maskBits=UINT64_MAX;
 for(uint32_t j=0;j<p[3];++j){uint32_t g[]={p[2],p[10],p[11],p[12],bits19(float19(p[13])+2.0f*(float)j*float19(p[11])),p[14],0,0};shape19(j,0,sd,geometry19(g));}
 if(p[1]&16){bd.type=b2_dynamicBody;bd.position.x+=4;bd.isAwake=bd.isEnabled=true;if(create_body(1,0,bd))fatal19("DOMAIN");b2Shape s={.type=b2_circleShape,.circle={{0,0},.5f}};shape19(p[3],1,sd,s);
  b2DistanceJointDef jd=b2DefaultDistanceJointDef();jd.bodyIdA=bodies[0].raw;jd.bodyIdB=bodies[1].raw;jd.length=4;
  b2JointId j=b2CreateDistanceJoint(worlds[0].raw,&jd);uint64_t birth=++lastIssued;joints14[0]=(Joint14){true,j,birth,worlds[0].birth,worlds[0],j.index1-1};metadata14[j.world0][j.index1-1]=(Meta14){birth,worlds[0].birth,0,false};
  if(!(p[1]&2))b2Body_SetAwake(bodies[0].raw,false);}
 for(uint32_t j=0;j<p[20];++j){resetOperation14(id19,0);step19();discard19();}
}

static void snapshot19(int tick)
{
 for(int i=0;i<BODIES;++i)if(bodies[i].live){uint32_t a[14];state19(bodies[i].raw,a);fprintf(stdout,"S19 %d %d %d 0 %d 14",id19,seq19,tick,i);words19(a,14);}
 Operation o={.code=600};dump(case9,seq9,0,0,0,-1);
 hits10(&o);public_sleep11(&o);observe12();world10_dump();private_sleep11();observe13(&o);observe14(&o);
 prefix12("I10",0,0,0);for(int j=0;j<6;++j)word(counts10[j]);putchar('\n');prefix12("I11",0,0,0);for(int j=0;j<11;++j)word(count11[j]);putchar('\n');
 prefix12("Z10",0,0,0);for(int j=0;j<4;++j)word(hitsCount10[j]);word(completed10);putchar('\n');prefix12("Z11",0,0,0);word(public11[0]);word(public11[1]);word(positive11);putchar('\n');
 prefix12("I12",0,0,0);for(int j=0;j<11;++j)word(counts12[j]);putchar('\n');prefix12("IP12",0,0,0);word(private12);putchar('\n');prefix12("Z12",0,0,0);word(positive11);word(seq9);putchar('\n');commit14();
 int nb=0,ns=0,nj=0;for(int i=0;i<WORLDS;++i)if(worlds[i].live){b2Counters c=b2World_GetCounters(worlds[i].raw);nb+=c.bodyCount;ns+=c.shapeCount;nj+=c.jointCount;}
 fprintf(stdout,"Z19 %d %d %d %d %d %d %d\n",id19,seq19,tick,nb,ns,nj,ntrace19);
}

typedef struct Lock19 {uint32_t count,locked,before[14],after[14];int status,reason;} Lock19;
static bool locked19(b2ShapeId a,b2ShapeId b,b2Manifold* m,void* context)
{
 (void)a;(void)b;(void)m;Lock19* p=context;++p->count;p->locked=b2GetWorldFromId(worlds[0].raw)->locked;state19(bodies[0].raw,p->before);
 uint32_t words[]={UINT32_MAX,UINT32_MAX,0,0,0x40800000,0x40000000,0x42c80000};b2ExplosionDef e=definition19(words);
 b2World_Explode(worlds[0].raw,&e);p->status=preflight19(0,words,&p->reason);state19(bodies[0].raw,p->after);return true;
}
static int native19(int selector,uint32_t* result)
{
 b2WorldDef wd=b2DefaultWorldDef();wd.gravity=b2Vec2_zero;wd.enableContinuous=false;wd.workerCount=1;wd.enqueueTask=port9Enqueue;wd.finishTask=port9Finish;
 create_world(0,wd);metadataOwner9[0]=worlds[0].birth;sync_hooks12();b2BodyDef bd=b2DefaultBodyDef();bd.type=b2_dynamicBody;create_body(0,0,bd);
 b2ShapeDef sd=b2DefaultShapeDef();sd.enablePreSolveEvents=true;b2Shape circle={.type=b2_circleShape,.circle={{0,0},.5f}};shape19(0,0,sd,circle);
 if(selector==0){bd.position.x=.5f;create_body(1,0,bd);shape19(1,1,sd,circle);static Lock19 lock;lock=(Lock19){0};b2World_SetPreSolveCallback(worlds[0].raw,locked19,&lock);
  step19();
  result[0]=lock.count;result[1]=lock.locked;memcpy(result+2,lock.before,sizeof lock.before);memcpy(result+16,lock.after,sizeof lock.after);
  if(lock.status!=7||lock.reason!=1||memcmp(lock.before,lock.after,sizeof lock.before))fatal19("DOMAIN");return 30;}
 save19(0);save19(1);memcpy(result,bank19[0],14*4);b2BodyId old=bodies[0].raw;World saved=worlds[0];Body oldNumber=bodies[0];destroy_body(0);result[14]=b2Body_IsValid(old);
 if(guard(&saved,&oldNumber)!=STALE)fatal19("DOMAIN");
 create_body(0,0,bd);shape19(0,0,sd,circle);result[15]=b2Body_IsValid(old);if(guard(&saved,&oldNumber)!=STALE)fatal19("DOMAIN");
 b2BodyId newer=bodies[0].raw;Body newerNumber=bodies[0];destroy_world(0);result[16]=b2World_IsValid(saved.raw);result[17]=b2Body_IsValid(newer);
 if(guard(&saved,&newerNumber)!=STALE)fatal19("DOMAIN");
 create_world(0,wd);result[18]=b2World_IsValid(saved.raw);if(guard(&saved,&oldNumber)!=STALE)fatal19("DOMAIN");destroy_world(0);return 19;
}

                                                                             
                                                                         
static char line19[2050];static char* tok19[80];static int nt19;
static bool read19(FILE* in)
{
 int c,n=0;bool cr=false;while((c=fgetc(in))!=EOF){if(c=='\n')break;if(cr)fatal19("ASCII");if(c=='\r'){cr=true;continue;}if(c<32||c>126)fatal19("ASCII");if(n==2048)fatal19("LINE_LENGTH");line19[n++]=c;}
 if(cr&&c!='\n')fatal19("ASCII");if(!n&&c==EOF)return false;line19[n]=0;
 if(!n||line19[0]==' '||line19[n-1]==' '||strstr(line19,"  "))fatal19("ASCII");nt19=0;tok19[nt19++]=line19;
 for(int i=0;i<n;++i)if(line19[i]==' '){line19[i]=0;if(nt19==80)fatal19("ARITY");tok19[nt19++]=line19+i+1;}return true;
}
static void need19(FILE* in){if(!read19(in))fatal19("EOF");}
static uint32_t decimal19(const char* p)
{if(!*p||(*p=='0'&&p[1]))fatal19("NUMBER");uint64_t v=0;for(;*p;++p){if(*p<'0'||*p>'9')fatal19("NUMBER");v=v*10+(*p-'0');if(v>UINT32_MAX)fatal19("NUMBER");}return v;}
static uint32_t hex19(const char* p)
{if(strlen(p)!=8)fatal19("WORD");uint32_t v=0;for(int i=0;i<8;++i){char c=p[i];if(!(c>='0'&&c<='9')&&!(c>='a'&&c<='f'))fatal19("WORD");v=v*16+(c<='9'?c-'0':c-'a'+10);}return v;}
static void validate19(uint32_t code,uint32_t n,const uint32_t* a)
{
 int needed=code==600?9:code==601||code==607?0:code==602?8:code==603?20:code==608?3:1;
 if(n!=(uint32_t)needed)fatal19("ARITY");
 if(code==600){if(a[0]>1)fatal19("MODE");if(a[1]>7)fatal19("SELECTOR");if(!a[0]&&(a[1]||domain19(a+2)))fatal19("DOMAIN");}
 if(code==602){if(a[0]>4)fatal19("DOMAIN");for(int i=1;i<8;++i){bool active=!(i==1&&(a[0]==2||a[0]==4))&&!(a[0]==0&&(i==2||i==3));if(active&&!isfinite(float19(a[i])))fatal19("DOMAIN");}if((a[0]==0||a[0]==1||a[0]==3)&&float19(a[1])<0||a[0]==3&&(!(float19(a[2])>0)||!(float19(a[3])>0)))fatal19("DOMAIN");}
 if(code==603){if(a[0]<3||a[0]>8||!isfinite(float19(a[1]))||float19(a[1])<0)fatal19("DOMAIN");b2Hull hull={.count=a[0]};for(int i=0;i<8;++i){if(i<(int)a[0]){hull.points[i]=(b2Vec2){float19(a[2+2*i]),float19(a[3+2*i])};if(!isfinite(hull.points[i].x)||!isfinite(hull.points[i].y))fatal19("DOMAIN");}else if(a[2+2*i]||a[3+2*i])fatal19("DOMAIN");}if(!b2ValidateHull(&hull)||!isfinite(float19(a[18]))||!isfinite(float19(a[19])))fatal19("DOMAIN");}
 if(code==605||code==606||code==608){if(a[0]>1)fatal19("BANK");if(code==608){if(a[1]>13)fatal19("FIELD");if((a[1]==3||a[1]==12)&&a[2]>1||a[1]==13&&a[2]>2)fatal19("VALUE");}if(code!=605&&!bankSaved19[a[0]])fatal19("BANK_EMPTY");}
 if(code==609&&a[0]>1)fatal19("SELECTOR");
}
static void execute19(uint32_t code,uint32_t n,const uint32_t* a)
{
 resetOperation14(id19,seq19);opcode9=code;ntrace19=0;
 fprintf(stdout,"E19 %d %d %u %u",id19,seq19,code,n);words19(a,n);
 uint32_t result[64]={0},arguments[39]={0};int rn=0,kind=0,status=0,reason=0,in=-1;
 if(code==600){b2ExplosionDef e=definition19(a+2);if(a[0])status=preflight19(a[1],a+2,&reason);if(!status){trace19=true;b2World_Explode(worlds[0].raw,&e);trace19=false;}
  arguments[0]=e.maskBits;arguments[1]=e.maskBits>>32;arguments[2]=bits19(e.position.x);arguments[3]=bits19(e.position.y);arguments[4]=bits19(e.radius);arguments[5]=bits19(e.falloff);arguments[6]=bits19(e.impulsePerLength);in=7;}
 else if(code==601){b2ExplosionDef e=b2DefaultExplosionDef();uint32_t d[]={e.maskBits,e.maskBits>>32,bits19(e.position.x),bits19(e.position.y),bits19(e.radius),bits19(e.falloff),bits19(e.impulsePerLength)};memcpy(result,d,sizeof d);kind=1;rn=7;in=0;}
 else if(code==602||code==603){b2Shape s; b2Vec2 line;
  if(code==602){s=geometry19(a);line=(b2Vec2){float19(a[6]),float19(a[7])};}
  else{b2Hull hull={.count=a[0]};for(int i=0;i<hull.count;++i)hull.points[i]=(b2Vec2){float19(a[2+2*i]),float19(a[3+2*i])};s=(b2Shape){.type=b2_polygonShape,.polygon=b2MakePolygon(&hull,float19(a[1]))};line=(b2Vec2){float19(a[18]),float19(a[19])};}
  b2Vec2 centroid=b2GetShapeCentroid(&s);result[0]=bits19(b2GetShapePerimeter(&s));result[1]=bits19(b2GetShapeProjectedPerimeter(&s,line));result[2]=bits19(centroid.x);result[3]=bits19(centroid.y);kind=2;rn=4;shapeInput19(&s,line,arguments);in=39;}
 else if(code==605)save19(a[0]);else if(code==606){kind=3;rn=19;memcpy(result,bank19[a[0]],sizeof bank19[0]);}
 else if(code==608)bank19[a[0]][a[1]]=a[2];else if(code==609){rn=native19(a[0],result);kind=a[0]?5:4;}
 fprintf(stdout,"A19 %d %d %u %d %d\nR19 %d %d %u %d %d",id19,seq19,code,status,reason,id19,seq19,code,kind,rn);words19(result,rn);
 if(in>=0&&OBS19){fprintf(stdout,"I19 %d %d %d",id19,seq19,in);words19(arguments,in);}copies19();
                                                                            
                                                                           
                                                                               
    
 if(code==609&&a[0]==0){b2World_SetPreSolveCallback(worlds[0].raw,NULL,NULL);snapshot19(1);resetOperation14(id19,seq19);opcode9=code;destroy_world(0);}
 if(code==607&&fixture19[21]){discard19();for(uint32_t tick=1;tick<=fixture19[21];++tick){resetOperation14(id19,seq19);step19();snapshot19(tick);}}
 else snapshot19(0);
}
int main(int argc,char** argv)
{
 if(argc==2&&!strcmp(argv[1],"--diagnostic"))diagnostic19=true;else if(argc!=1)fatal19("HEADER");
 need19(stdin);if(nt19!=4||strcmp(tok19[0],"PORT19"))fatal19("HEADER");if(strcmp(tok19[1],"A"))fatal19("PART");
 profile19=!strcmp(tok19[2],"DIRECT")?0:!strcmp(tok19[2],"PUBLIC")?1:!strcmp(tok19[2],"GUARD")?2:-1;
 if(profile19<0)fatal19("PROFILE");uint32_t n=decimal19(tok19[3]),full=profile19==0?48:profile19==1?32:48;
 if(!n||n>full||!diagnostic19&&n!=full)fatal19("N");profile11=profile12=14;uint32_t previous=0;
 for(uint32_t c=0;c<n;++c){need19(stdin);if(nt19!=3||strcmp(tok19[0],"C"))fatal19("CASE");uint32_t id=decimal19(tok19[1]),count=decimal19(tok19[2]);
  if(!id||id>full||id<=previous||!diagnostic19&&id!=c+1)fatal19("ID");previous=id;
  uint32_t expected=profile19==2?0:profile19==0||id==23||id==24?1:9;
  if(profile19==2?count!=0:!count||count>32||!diagnostic19&&count!=expected)fatal19("COUNT");
  id19=id;seq19=0;resetCase14(id);memset(bankSaved19,0,sizeof bankSaved19);fixture19=scene19[profile19==1?1:0][profile19==2?1:id];
  if(!(profile19==1&&(id==23||id==24)))scene19Create(fixture19);
  fprintf(stdout,"CASE %u %u\n",id,count);
  for(uint32_t s=0;s<(profile19==2?2:count);++s){need19(stdin);bool guard=profile19==2;
   if(nt19<4||strcmp(tok19[0],guard?"G":"O"))fatal19(guard?"GUARD":"SEQ");
   uint32_t sequence=decimal19(tok19[1]),code=decimal19(tok19[2]),arity=decimal19(tok19[3]);
   if(sequence!=(guard?s:s+1))fatal19(guard?"GUARD":"SEQ");if(code<600||code>609||code==604)fatal19("OPCODE");
   if(arity>64||nt19!=4+(int)arity)fatal19("ARITY");uint32_t a[64]={0};for(uint32_t i=0;i<arity;++i)a[i]=hex19(tok19[4+i]);
   if(guard){if(code!=600||arity!=9||a[0]!=1)fatal19("GUARD");if(a[1]>7)fatal19("SELECTOR");
    fprintf(stdout,"G19 %u %u 600 9",id,s);words19(a,9);int reason;int status=preflight19(a[1],a+2,&reason);
    fprintf(stdout,"GA19 %u %u %d %d %d\n",id,s,!status,status,reason);
   }else{validate19(code,arity,a);seq19=s+1;execute19(code,arity,a);}
  }
  fprintf(stdout,"ENDCASE %u\n",id);for(int i=0;i<WORLDS;++i)if(worlds[i].live)destroy_world(i);
 }
 if(fgetc(stdin)!=EOF)fatal19("TRAILING_DATA");fprintf(stdout,"END %u\n",n);free_tokens();free(trace12);free(callbackAP12);return ferror(stdout)||fflush(stdout)?2:0;
}
