"""v1.2.1 设计契约与独立语义模型核对；不是生产 Runtime/DB 测试。"""
from pathlib import Path
import argparse,copy,json,re,hashlib
from dataclasses import dataclass,field
from collections import Counter
from jsonschema import Draft202012Validator,FormatChecker

CURRENT_MARKDOWN = ('01_需求基线/DataAgentX_SRS_v1.2.md', '01_需求基线/DataAgentX_需求优先级清单_v1.2.md', '01_需求基线/DataAgentX_需求评审记录_v1.2.md', '02_总体设计与方案验证/DataAgentX_总体设计方案_v1.2.md', '02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md', '02_总体设计与方案验证/DataAgentX_设计总册与完成性评审_v1.2.1.md', '04_详细设计与实现准备/DataAgentX_DD01_身份权限与生命周期_v1.2.md', '04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md', '04_详细设计与实现准备/DataAgentX_DD03_Runtime与Provider_v1.2.1.md', '04_详细设计与实现准备/DataAgentX_DD04_检索证据与报告_v1.2.md', '04_详细设计与实现准备/DataAgentX_DD05_存储接口与集成_v1.2.1.md', '04_详细设计与实现准备/DataAgentX_DD08_增强功能与扩展设计_v1.2.md', '06_评测与验收/DataAgentX_DD06_评测与验收设计_v1.2.1.md', '07_发布与求职材料/DataAgentX_DD07_部署运维与交付设计_v1.2.1.md', '07_发布与求职材料/DataAgentX_求职能力与工程证据矩阵_v1.2.md', '01_需求基线/DataAgentX_需求补充与变更记录_v1.2.1.md', '07_发布与求职材料/DataAgentX_设计发布说明_v1.2.1.md')

def document_root(root):
 candidates=[root/"docs"/"engineering",root/"docs",root]
 matches=[p for p in candidates if (p/"04_详细设计与实现准备"/"DataAgentX_对象Schema_v1.2.1.json").is_file()]
 if len(matches)!=1:raise ValueError("请指定唯一的当前工程文档目录或其项目根目录；不递归查找历史副本")
 return matches[0].resolve()

def run(root):
 root=document_root(root)
 checks=[]
 def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),**({'details':detail} if detail is not None else {})})
 def load(pattern):
  stage='02_总体设计与方案验证' if '设计追溯矩阵' in pattern else '04_详细设计与实现准备'
  return json.loads((root/stage/pattern).read_text(encoding='utf-8'))
 s=load('DataAgentX_对象Schema_v1.2.1.json');api=load('DataAgentX_API契约_v1.2.1.openapi.json');cfg=load('DataAgentX_合成运行配置_v1.2.1.json');trace=load('DataAgentX_设计追溯矩阵_v1.2.1.json')
 Draft202012Validator.check_schema(s);check('26个Schema定义结构合法',len(s['$defs'])==26)
 def walk(x):
  if isinstance(x,dict):
   yield x
   for v in x.values():yield from walk(v)
  elif isinstance(x,list):
   for v in x:yield from walk(v)
 for name,doc in [('Schema',s),('OpenAPI',api)]:
  bad=[]
  for node in walk(doc):
   if '$ref' not in node:continue
   ref=node['$ref'];v=doc
   try:
    assert ref.startswith('#/')
    for key in ref[2:].split('/'):v=v[key.replace('~1','/').replace('~0','~')]
   except (KeyError,AssertionError):bad.append(ref)
  check(name+'内部引用完整',not bad,bad)
 def refs(j):
  if isinstance(j,dict):return {k:(v.replace('#/$defs/','#/components/schemas/') if k=='$ref' else refs(v)) for k,v in j.items()}
  if isinstance(j,list):return [refs(v) for v in j]
  return j
 check('OpenAPI和独立对象逐字段一致',api['components']['schemas']==refs(s['$defs']))
 check('7路径7操作保持',len(api['paths'])==7 and sum(k in ['get','post','put','patch','delete'] for path in api['paths'].values() for k in path)==7)
 check('载荷与工具版本维持1.2',all(n['const']=='1.2' for n in walk(s) if 'const' in n and n['const'] in ['1.2','1.2.1']))
 UID='00000000-0000-4000-8000-000000000001';DT='2026-10-09T00:00:00.000000Z'
 def sample(j):
  if '$ref' in j:return sample(s['$defs'][j['$ref'].split('/')[-1]])
  if 'const' in j:return j['const']
  if 'enum' in j:return j['enum'][0]
  if 'anyOf' in j:return sample(j['anyOf'][0])
  if 'oneOf' in j:return sample(j['oneOf'][0])
  typ=j.get('type')
  if typ=='object':return {k:sample(j['properties'][k]) for k in j.get('required',[])}
  if typ=='array':return [sample(j['items']) for _ in range(j.get('minItems',0))]
  if typ=='null':return None
  if typ=='boolean':return False
  if typ=='integer':return j.get('minimum',0)
  if typ=='string':
   if j.get('format')=='uuid':return UID
   if j.get('format')=='date-time':return DT
   if j.get('pattern')=='^[a-f0-9]{64}$':return 'a'*64
   if j.get('pattern','').startswith('^-?'):return '0'
   return 'sample'
  raise ValueError(j)
 e={n:sample(j) for n,j in s['$defs'].items()}
 e['ClarificationAnswers']={'metric_id':'refund_rate_order_horizon'};e['ClarificationRequest']['answers']=e['ClarificationAnswers']
 e['Claim'].update(evidence_ids=[UID],contribution_type=None,formula_version=None)
 e['TaskView'].update(scope=None,terminal_at=None,clarification=None)
 e['ReportView'].update(claims=[copy.deepcopy(e['Claim'])],evidence_refs=[UID])
 v={n:Draft202012Validator({**s,'$ref':'#/$defs/'+n},format_checker=FormatChecker()) for n in s['$defs']}
 for name,x in e.items():
  errors=list(v[name].iter_errors(x));check('Schema正例:'+name,not errors,[x.message for x in errors][:2])
  y=copy.deepcopy(x);y['injected']=1;check('Schema未知字段拒绝:'+name,not v[name].is_valid(y))
 def summary(status):
  x=copy.deepcopy(e['ReportView']);x.update(scope_hash=None,terminal_status=status,claims=[],evidence_refs=[],limitations=['尚未冻结Scope；仅状态摘要'],quality_summary='尚未建立调查口径/未执行质量核验',markdown='已结束；尚未建立口径，不作业务结论。');return x
 for status in ['cancelled','failed','budget_exceeded','insufficient_evidence']:check('无Scope终态摘要:'+status,v['ReportView'].is_valid(summary(status)))
 x=summary('completed');check('completed空Scope拒绝',not v['ReportView'].is_valid(x))
 for key,value,label in [('claims',[e['Claim']],'业务Claim'),('evidence_refs',[UID],'业务证据'),('limitations',[],'无局限说明')]:
  x=summary('cancelled');x[key]=value;check('无Scope摘要拒绝:'+label,not v['ReportView'].is_valid(x))
 x=copy.deepcopy(e['TaskView']);x.update(status='completed',terminal_at=DT,scope=None);check('Task完成无Scope拒绝',not v['TaskView'].is_valid(x))
 x['scope']=copy.deepcopy(e['ScopeSpec']);check('Task完成有Scope合法',v['TaskView'].is_valid(x))
 def bind(task,report):
  expected=task['scope']['scope_hash'] if task['scope'] else None
  return task['task_id']==report['task_id'] and task['status']==report['terminal_status'] and report['scope_hash']==expected and (task['status']!='completed' or task['scope'] is not None)
 task=copy.deepcopy(e['TaskView']);task.update(status='cancelled',terminal_at=DT,scope=None)
 check('关联参考:无Scope取消摘要',bind(task,summary('cancelled')))
 for status in ['failed','insufficient_evidence','budget_exceeded']:
  task['status']=status;check('关联参考:Scope前'+status,bind(task,summary(status)))
 fake=summary('cancelled');fake['scope_hash']='b'*64;task['status']='cancelled'
 check('形式合法伪hash可过Schema但不得过关联',v['ReportView'].is_valid(fake) and not bind(task,fake))
 task.update(scope=copy.deepcopy(e['ScopeSpec']),status='completed');report=copy.deepcopy(e['ReportView'])
 check('关联参考:真实Scope完成',bind(task,report))
 report['scope_hash']='b'*64;check('关联参考:串Scope拒绝',not bind(task,report))
 pending=copy.deepcopy(e['TaskView']);pending.update(status='needs_clarification',phase='pending_requeue',clarification=None,terminal_at=None)
 check('pending_requeue无需重复问题的Task正例',v['TaskView'].is_valid(pending))
 for key,value,label in [('status','running','错误公开状态'),('clarification',e['ClarificationPrompt'],'重复用户问题'),('terminal_at',DT,'伪终态时间')]:
  x=copy.deepcopy(pending);x[key]=value;check('pending_requeue拒绝:'+label,not v['TaskView'].is_valid(x))
 x=copy.deepcopy(pending);x['phase']='awaiting_user';check('awaiting_user无提示拒绝',not v['TaskView'].is_valid(x))
 x['clarification']=e['ClarificationPrompt'];check('awaiting_user有问题合法',v['TaskView'].is_valid(x))

 # 独立事件账本，只说明规格中的责任和时间转换；未调用生产调度器。
 @dataclass
 class Session:
  phase:str='awaiting_user'
  status:str='needs_clarification'
  last:float=0
  queue:float=10
  active:float=20
  human:float=1790
  accepted_answer:str=None
  started:int=0
  events:list=field(default_factory=list)
  def advance(self,now):
   assert now>=self.last
   if self.phase=='awaiting_user':self.human+=now-self.last
   elif self.phase=='pending_requeue':self.queue+=now-self.last
   elif self.phase=='active':self.active+=now-self.last
   self.last=now
  def answer(self,now,key='answer-1',valid=True,sufficient=True,full=True):
   self.advance(now)
   if self.accepted_answer==key:return 200
   if self.accepted_answer is not None:return 409
   if self.status in ['failed','cancelled']:return 409
   if self.human>=1800:self.status='failed';self.phase='terminal';return 409
   if not valid:return 400
   if not sufficient:return 200
   self.accepted_answer=key;self.phase='pending_requeue';self.events.append('answer_accepted');return 200
  def schedule(self,now,slot):
   self.advance(now)
   if self.phase!='pending_requeue':return
   if self.queue>=30:self.status='failed';self.phase='terminal';self.events.append('QUEUE_WAIT_TIMEOUT')
   elif slot:self.status='running';self.phase='active';self.started+=1;self.events.append('automatic_start')
  def cancel(self,now):
   self.advance(now)
   if self.phase=='terminal':return
   self.status='cancelled';self.phase='terminal';self.events.append('cancelled')
 sess=Session();check('满队充分答案200接受',sess.answer(5,full=True)==200 and sess.phase=='pending_requeue')
 sess.schedule(10,False);check('答案后5秒容量等待计queue/人工停表',sess.human==1795 and sess.queue==15 and sess.active==20)
 check('同答案重放200不重启等待',sess.answer(11)==200 and sess.human==1795 and sess.events.count('answer_accepted')==1)
 check('异答案409',sess.answer(11,key='answer-2')==409)
 sess.schedule(12,True);check('无需客户端重答自动持槽',sess.started==1 and sess.phase=='active' and sess.queue==17 and sess.active==20)
 sess.schedule(14,True);check('重复调度不会第二次启动',sess.started==1 and sess.active==22)
 check('已满人工期限之后不误过期',sess.human==1795 and sess.status=='running')
 timeout=Session();timeout.answer(5);timeout.schedule(25,False)
 check('pending队列累计到界用QUEUE_WAIT_TIMEOUT',timeout.queue==30 and timeout.status=='failed' and timeout.events[-1]=='QUEUE_WAIT_TIMEOUT' and timeout.human==1795)
 timeout.schedule(26,True);check('队列超时后不能复活',timeout.started==0 and timeout.status=='failed')
 invalid=Session();check('无效答案400',invalid.answer(5,valid=False)==400);invalid.advance(6)
 check('无效答案仍计人工而不计新queue',invalid.human==1796 and invalid.queue==10 and invalid.phase=='awaiting_user')
 partial=Session();check('合法部分答案200仍待用户',partial.answer(5,sufficient=False)==200 and partial.phase=='awaiting_user' and partial.accepted_answer is None)
 edge=Session();check('恰人工到界答案拒绝/不重置',edge.answer(10)==409 and edge.status=='failed')
 cancelled=Session();cancelled.answer(5);cancelled.cancel(6);cancelled.schedule(7,True)
 check('pending取消后自动调度不能复活',cancelled.status=='cancelled' and cancelled.started==0)
 cancelled2=Session();cancelled2.cancel(2);check('取消先提交则答案拒绝',cancelled2.answer(3)==409 and cancelled2.status=='cancelled')

 # 独立时间线：测量[0,60)，排空截止120（不含120）。
 tasks=[{'id':'warmup','accepted':-1,'terminal':10,'status':'completed'}, {'id':'a','accepted':0,'terminal':20,'status':'completed'}, {'id':'b','accepted':30,'terminal':60,'status':'completed'}, {'id':'c','accepted':50,'terminal':90,'status':'completed'}, {'id':'late','accepted':55,'terminal':120,'status':'completed'}, {'id':'running','accepted':59,'terminal':None,'status':'running'}, {'id':'failed','accepted':10,'terminal':40,'status':'failed'}]
 def metrics(rows,start,end,deadline):
  cohort=[x for x in rows if start<=x['accepted']<end]
  completed=[x for x in rows if x['status']=='completed' and x['terminal'] is not None]
  measure=[x for x in completed if start<=x['terminal']<end]
  successful=[x for x in cohort if x['status']=='completed' and x['terminal'] is not None and x['terminal']<deadline]
  return {'completed_throughput':len(measure)/(end-start),'measurement_completed':len(measure),'measurement_completed_from_warmup':sum(x['accepted']<start for x in measure),'accepted_cohort_size':len(cohort),'accepted_cohort_completed':len(successful),'cohort_completion_rate':len(successful)/len(cohort) if cohort else None,'drain_completed':sum(end<=x['terminal']<deadline for x in completed),'late_completed':sum(x['terminal']>=deadline for x in completed),'drain_observation_seconds':deadline-end}
 m=metrics(tasks,0,60,120)
 check('实际完成吞吐只计测量窗终态2/60',m['measurement_completed']==2 and abs(m['completed_throughput']-2/60)<1e-12)
 check('接收cohort完成率为3/6而非吞吐',m['accepted_cohort_size']==6 and m['accepted_cohort_completed']==3 and m['cohort_completion_rate']==.5)
 check('窗末60秒完成计drain不计吞吐',m['drain_completed']==2 and m['measurement_completed']==2)
 check('预热受理/测量完成计吞吐且披露来源',m['measurement_completed_from_warmup']==1)
 check('截止恰120迟到不计cohort成功',m['late_completed']==1 and m['accepted_cohort_completed']==3)
 check('排空观察耗时单列',m['drain_observation_seconds']==60)
 empty=metrics([],0,60,120);check('零接收完成率N/A不假通过',empty['cohort_completion_rate'] is None and empty['completed_throughput']==0)
 endcase=metrics([{'accepted':60,'terminal':60,'status':'completed'}],0,60,120)
 check('accepted_at恰窗末不入cohort',endcase['accepted_cohort_size']==0)
 check('config吞吐排除drain',cfg['load_calibration']['drain_completions_included_in_throughput'] is False)
 check('原三时限保持且不增加预算',all(cfg['limits'][k]==n for k,n in [('queue_wait_seconds',30),('active_seconds',120),('clarification_seconds',1800)]))
 check('需求34及25-6-3保持',len(trace['requirements'])==34 and dict(Counter(x['priority'] for x in trace['requirements']))=={'Must':25,'Should':6,'Could':3})
 clar=next(p['post'] for url,p in api['paths'].items() if url.endswith('/clarifications'))
 check('充分答案不返回重入容量429', '429' not in clar['responses'] and '200' in clar['responses'])
 for rel in CURRENT_MARKDOWN:
  p=root/rel
  if not p.is_file():
   check('发布文档相对链接:'+p.name,False,['固定清单文件缺失']);continue
  missing=[]
  for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
   if '://' not in link and not (p.parent/link.partition('#')[0]).is_file():missing.append(link)
  check('发布文档相对链接:'+p.name,not missing,missing)
 return {'date':'2026-10-09','baseline':'DAX-RB-1.2.1','scope':'JSON Schema/OpenAPI静态契约与独立状态/统计参考模型','production_application_tests_executed':False,'passed':all(x['passed'] for x in checks),'check_count':len(checks),'document_scan_policy':'fixed_current_technical_markdown_v1.2.1','document_scan_scope':list(CURRENT_MARKDOWN),'checks':checks,'throughput_boundary_reference':{'window':[0,60],'drain_deadline_exclusive':120,'tasks':tasks,'expected_metrics':m},'pending_requeue_reference':{'queue_ms':sess.queue*1000,'human_ms':sess.human*1000,'active_ms':sess.active*1000,'events':sess.events}}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);parser.add_argument('--output',type=Path);args=parser.parse_args()
 result=run(args.root)
 if args.output:
  if args.output.exists():raise FileExistsError('核对结果已存在；为保护冻结证据，请指定新路径')
  args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
 print(json.dumps({'checks':result['check_count'],'passed':result['passed'],'application_tests':False,'failures':[x for x in result['checks'] if not x['passed']]},ensure_ascii=False))
 raise SystemExit(0 if result['passed'] else 1)
