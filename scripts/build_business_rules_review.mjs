// Development-only review artifact; never imported by the desktop application.
import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
let FileBlob, SpreadsheetFile, Workbook;
try {
  const at=process.argv.indexOf("--node-modules"), modules=at<0?null:process.argv[at+1];
  const specifier=modules?pathToFileURL(createRequire(path.join(path.resolve(modules),"..","__review_loader__.cjs")).resolve("@oai/artifact-tool")).href:"@oai/artifact-tool";
  ({FileBlob,SpreadsheetFile,Workbook}=await import(specifier));
}
catch(error) { throw new Error("审阅开发工具 @oai/artifact-tool 不可用。请先调用 load_workspace_dependencies 获取 bundled Node/module 路径，以 --node-modules 明确传入 packages 路径并按 PREFLIGHT 步骤运行；无需安装或更改生产依赖。原始错误："+error.message,{cause:error}); }

const args = process.argv.slice(2);
function option(key, fallback) { const i=args.indexOf(key); return i<0?fallback:args[i+1]; }
const input=option("--input"), output=option("--output"), previous=option("--previous");
if(!input || !output) throw new Error("Required: --input candidate-review.json --details technical-review.json --output review.xlsx [--previous review.xlsx]");
const reviewText=await fs.readFile(input,"utf8");
const reviewHash=createHash("sha256").update(reviewText.replace(/\r\n/g,"\n"),"utf8").digest("hex");
const payload=JSON.parse(reviewText);
const wb=Workbook.create();
const feedbackHeaders=["审阅意见","处理状态","审阅编号"];
const objectLabels={object:"业务对象",state:"状态",reason:"理由",values:"允许来源",value:"值",source:"来源",parameter_id:"参数ID",binding_id:"绑定ID",tags:"匹配条件",ranges:"范围与边界",origin:"对象类别",binding_status:"绑定资格",business_source:"当前来源",direction:"方向",attribute:"电力属性",source_path:"因子路径",catalog_table:"来源表",province:"省份",region:"区域",min:"下界",max:"上界",include_min:"包含下界",include_max:"包含上界",carbonate_component_count:"本批有效组分数",material_calculation_path:"已定义物料换算路径",channel:"渠道",label:"渠道名称",unit:"单位",binding:"控件/模型绑定"};
const stateLabels={OTHER:"其他来源",NONE:"无自动默认",NOT_APPLICABLE:"不适用",NO_LEGAL_SOURCES:"无合法来源",FIXED:"固定定义",BINDING:"引用参数绑定",POLICY:"登记策略",PENDING:"待核验",EDITABLE:"可填写/选择",LOCKED:"只读",CONDITIONAL:"条件待展开",STANDARD_DEFAULT:"缺省值",CALCULATED:"计算值",MEASURED:"实测值",CATALOG:"目录对象",CUSTOM:"自定义",LEGACY_UNSPECIFIED:"历史身份未确认",PURCHASED:"购入",EXPORTED:"输出",CONVENTIONAL:"常规电力",NONFOSSIL:"非化石",FOSSIL:"化石",VERIFIED:"来源登记已核验",ABSENT:"无适用绑定",READY:"可用",BLOCKED:"受阻",RESOLVED:"已求值",SOURCE_NOT_ALLOWED:"所选来源不合法",DEFINED_RECEIVED_BASIS_CONVERSION:"已批准收到基换算（仍核必要数值/基准）",SUPPLY_UNIT_MEASURED:"供电单位实测",ENTERPRISE_MEASURED:"企业实测",ENTERPRISE_CALCULATED:"企业计算",ARBITRARY_OVERRIDE:"库外自行填写（输入方式，非来源类别）",NONFOSSIL_ZERO:"非化石购电零排放",CATALOGUE_TABLE_1:"目录表1",CATALOGUE_TABLE_2:"目录表2",CATALOGUE_TABLE_3:"目录表3",CATALOGUE_TABLE_4:"目录表4",CATALOGUE_TABLE_5:"目录表5"};
function literalCell(value){ const raw=String(value??""); return raw.startsWith("=")?"'"+raw:raw; }
function text(value){
  if(value===null || value===undefined) return "";
  if(Array.isArray(value)) return value.map(text).join("\n");
  if(typeof value==="object" && Array.isArray(value.groups)) return summaryText(value);
  if(typeof value==="object") return Object.entries(value).map(([k,v])=>`${objectLabels[k]??k}: ${text(v)}`).join("\n");
  const raw=String(value).replaceAll("Canonical","统一输入").replaceAll("Catalog","参数库").replaceAll("Record","正式记录").replaceAll("正式正式记录","正式记录").replaceAll("统一输入输入","统一输入").replaceAll("numeric default","数值默认").replaceAll("default_source","初始来源");
  const literal=stateLabels[raw]?`${stateLabels[raw]}（${raw}）`:raw;
  return literal.startsWith("=")?"'"+literal:literal;
}
const labels={mapping_refs:"既有映射关联",key:"稳定审阅键",review_key:"稳定审阅键",revision:"规则修订",field_id:"字段ID",condition_id:"条件ID",condition:"条件与边界",context:"求值上下文",property:"属性",name:"业务名称",kind:"字段类型",unit:"单位",source:"允许来源",locking:"读写与来源锁定",source_qualification:"合法来源",default:"数值默认及绑定",default_source:"默认来源",channels:"渠道投影",channel_projections:"渠道名称与单位",basis:"依据",consumers:"实际消费者",cases:"案例",pending:"待处理项",operation_id:"操作ID",initial_context:"初始上下文",action:"触发动作",changes:"改变什么",preserves:"保留什么",invalidates:"失效依赖",confirmation:"重新确认",change_type:"变化类型",before:"基线",after:"候选",reason:"原因",rule_set_id:"规则集ID",policy_id:"策略ID",rule_ids:"关联规则",evaluation_status:"候选求值状态",evaluation_problems:"候选求值问题",definition_key:"原定义键",scope_note:"范围说明",projection_notes:"渠道约束与补充说明",visibility:"可见性盘点",initialization_status:"初始化检查状态",selected_business_source:"选定来源",effective_context:"有效上下文"};
function conditionText(condition){
  const parts=Object.entries(condition.tags??{}).map(([key,values])=>`${objectLabels[key]??key}=${[values].flat().map(value=>stateLabels[value]??value).join("或")}`);
  for(const [key,value] of Object.entries(condition.ranges??{})) {
    const name=objectLabels[key]??key;
    if(value.min===value.max && value.min!==undefined) parts.push(`${name}=${value.min}`);
    else {
      if(value.min!==undefined) parts.push(`${name}${value.include_min?"≥":">"}${value.min}`);
      if(value.max!==undefined) parts.push(`${name}${value.include_max?"≤":"<"}${value.max}`);
    }
  }
  if(condition.exact_matches) parts.push(`须匹配精确登记组合（${condition.exact_matches.combination_count}项）`);
  return parts.join("，") || "各适用业务条件";
}
function businessConditions(conditions){
  // Merge only one tag dimension with every other tag/range/exact-match constraint identical.
  // This preserves the disjunction; it never invents a Cartesian product of separate conditions.
  let rows=conditions.map(c=>({...c,tags:Object.fromEntries(Object.entries(c.tags??{}).map(([k,v])=>[k,[v].flat()]))}));
  for(const dimension of ["business_source","direction","origin","attribute","binding_status"]){
    const groups=new Map();
    for(const row of rows){
      if(!Object.hasOwn(row.tags,dimension)) { groups.set(Symbol(),row); continue; }
      const otherTags=Object.fromEntries(Object.entries(row.tags).filter(([k])=>k!==dimension).sort(([a],[b])=>a.localeCompare(b)));
      const key=JSON.stringify([otherTags,row.ranges??{},row.exact_matches??null]);
      if(groups.has(key)){
        const prior=groups.get(key);
        prior.tags[dimension]=[...new Set([...prior.tags[dimension],...row.tags[dimension]])];
      }else groups.set(key,{...row,tags:{...row.tags}});
    }
    rows=[...groups.values()];
  }
  const commonTags={};
  if(rows.length>1){
    for(const [key,value] of Object.entries(rows[0].tags)){
      if(rows.every(row=>JSON.stringify(row.tags[key])===JSON.stringify(value))) commonTags[key]=value;
    }
  }
  const shared=Object.keys(commonTags).length?`共同条件：${conditionText({tags:commonTags})}；且满足以下任一情形：\n`:"";
  const alternatives=rows.map(row=>conditionText({...row,tags:Object.fromEntries(Object.entries(row.tags).filter(([key])=>!Object.hasOwn(commonTags,key)))}));
  return shared+alternatives.join("；\n");
}
function summaryText(summary){
  return summary.groups.map(group=>{
    const value=group.outcome;
    let result;
    if(summary.property==="locking"){
      result=`数值${stateLabels[value.value_state]??value.value_state}，来源${stateLabels[value.source_state]??value.source_state}`;
      if(value.value_state==="PENDING" || value.source_state==="PENDING") result+="；资格或适用性条件未满足，暂不可直接采用";
    }else if(summary.property==="default"){
      if(value.state==="BINDING") result="缺省路径按适用精确绑定从参数与因子库读取";
      else if(value.state==="NONE") result="不自动填写数值；按来源与输入要求填写";
      else if(value.state==="PENDING") result="适用性未完成核对，暂不自动填写";
    }
    if(result===undefined){
      if(summary.property==="source_qualification" && value.state==="NOT_APPLICABLE") result="本路径无需选择来源类别；不得冒用缺省/计算/实测";
      else if(value.state==="FIXED") result=value.values?value.values.map(v=>stateLabels[v]??v).join(" / "):value.source?(stateLabels[value.source]??value.source):text(value.value);
      else if(value.state==="BINDING") result="按适用精确绑定从参数与因子库读取";
      else result=stateLabels[value.state]??value.state;
    }
    return `${result}\n适用：${businessConditions(group.conditions??[])}`;
  }).filter((value,index,all)=>all.indexOf(value)===index).join("\n\n");
}
function unitText(value){
  return value==="ratio" ? "比值（0～1）；界面/Excel用百分数（%）" : text(value);
}
const metadata=payload.metadata??{};
const definitionRoot=option("--definition-root");
const definitionAssets={};
if(definitionRoot){
  for(const rel of ["data-source/carbon_accounting/business-rules/common/gbt_32150_2025.json","data-source/carbon_accounting/business-rules/standards/gbt_32151_34_2024.json","data-source/carbon_accounting/business-rules/software_policy.json","specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md"]){
    const bytes=await fs.readFile(path.resolve(definitionRoot,rel));
    new TextDecoder("utf-8",{fatal:true}).decode(bytes);
    definitionAssets[rel]=createHash("sha256").update(bytes.toString("utf8").replace(/\r\n/g,"\n"),"utf8").digest("hex");
  }
}
const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==="object"?Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])])):value;
const digest=value=>createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex");
const semanticSummary=value=>Array.isArray(value)?value.map(semanticSummary).sort((a,b)=>(JSON.stringify(a)<JSON.stringify(b)?-1:JSON.stringify(a)>JSON.stringify(b)?1:0)):value&&typeof value==="object"?Object.fromEntries(Object.keys(value).sort().map(k=>[k,semanticSummary(value[k])])):value;
const propertyKeys=["source","default_source","default","locking"];
const propertyLabels={source:"允许来源",default_source:"默认来源",default:"数值默认",locking:"读写锁定"};
const detailsInput=option("--details");
if(!detailsInput)throw new Error("Required: --details same-source technical-review.json with source_compact_sha256");
const detailsPayload=detailsInput?JSON.parse(await fs.readFile(detailsInput,"utf8")):payload;
const detailsName="业务规则审阅详情.html";
if(detailsInput){
  for(const key of ["revision","base","dependency"]){
    if(JSON.stringify(canonical(metadata[key]))!==JSON.stringify(canonical(detailsPayload.metadata?.[key])))throw new Error("Technical details do not match compact projection: "+key);
  }
  if(detailsPayload.metadata?.source_compact_sha256!==reviewHash)throw new Error("Technical details are bound to another compact projection");
}
const snapshotPath=option("--catalog-snapshot");
const catalogSnapshot=snapshotPath?JSON.parse(await fs.readFile(snapshotPath,"utf8")):null;
if(catalogSnapshot){
  if(catalogSnapshot.status!=="CHECKED"||catalogSnapshot.source_compact_sha256!==reviewHash)throw new Error("目录数值快照未核对或不属于当前投影");
  const catalogPath=option("--catalog-source",path.resolve(definitionRoot??process.cwd(),"data-source/carbon_accounting/catalog.json"));
  const raw=await fs.readFile(catalogPath);new TextDecoder("utf8",{fatal:true}).decode(raw);
  const hash=createHash("sha256").update(raw.toString("utf8").replace(/\r\n/g,"\n")).digest("hex");
  if(hash!==catalogSnapshot.catalog.canonical_source_lf_sha256||JSON.parse(raw).manifest.data_version!==catalogSnapshot.catalog.data_version)throw new Error("目录快照与当前Canonical目录不一致");
}
function catalogReference(row){
  const entry=catalogSnapshot?.entries?.[row.field_id];
  if(!entry)return null;
  const matches=(detailsPayload.fields??[]).some(r=>r.field_id===row.field_id&&r.policy_branch_values?.default?.state==="BINDING"&&r.condition?.tags?.binding_id===entry.binding_id&&r.policy_branch_values.default.parameter_id===entry.parameter_id);
  if(!matches)throw new Error("目录数值快照的精确绑定不在当前字段定义中："+row.field_id);
  return entry;
}
function catalogReferenceText(row){
  const hasBound=row.default?.state==="BINDING"||row.default?.groups?.some(g=>g.outcome.state==="BINDING");
  if(!hasBound)return "本组合不采用目录数值默认。";
  const e=catalogReference(row);if(!e)return "目录参考值未核对（未提供本版只读快照）；ID存在不等于数值验证。";
  const display=e.unit==="ratio"?new Intl.NumberFormat("zh-CN",{maximumFractionDigits:2}).format(Number(e.value)*100)+"%":e.value+" "+e.unit;
  return display+"；"+(e.article??e.binding_location??e.source_table_location??"")+"；"+e.source_id+" / "+(e.source_version??"")+"；目录"+catalogSnapshot.catalog.data_version+"；绑定"+e.binding_id;
}
function technicalRowsFor(row){
  const scope=String(row.stable_condition??"").match(/^source_path=([^;]+);direction=(.+)$/);
  return (detailsPayload.fields??[]).filter(r=>r.field_id===row.field_id&&r.rule_set_id===row.rule_set_id&&(!scope||conditionAllows(r.condition??r.context??{},scope[1],scope[2])));
}
function visibleProperty(row,prop){
  const summary=row[prop];if(!summary?.groups)return summary;
  const actual=prop==="source"?"source_qualification":prop;
  const ready=technicalRowsFor(row).filter(r=>r.evaluation_status==="READY");
  return {...summary,groups:summary.groups.map(g=>({...g,conditions:g.conditions.filter(c=>ready.some(r=>{
    const when=r.conditions_by_property?.[actual]??{};
    return Object.entries(c.tags??{}).every(([key,v])=>[v].flat().includes(when.tags?.[key]))&&JSON.stringify(canonical(c.ranges??{}))===JSON.stringify(canonical(when.ranges??{}));
  }))})).filter(g=>g.conditions.length)};
}
function pendingPresentation(row){
  const all=technicalRowsFor(row),notes=new Set(row.pending??[]);
  if(!all.some(r=>r.evaluation_status==="READY"))notes.add("当前路径无有效规则组合；完整原因/纠错入口见详情。");
  if(all.some(r=>(r.effective_context??r.context??r.condition?.tags)?.origin==="LEGACY_UNSPECIFIED"))notes.add("历史身份：保留可读；采用前核对真实对象与来源。");
  if(all.some(r=>(r.effective_context??r.context??r.condition?.tags)?.binding_status==="ABSENT"))notes.add("缺绑定：缺省不可借用；依字段规则补值，不是新来源或待Owner审批。");
  if(all.some(r=>(r.effective_context??r.context??r.condition?.tags)?.binding_status==="PENDING"))notes.add("绑定适用性待核；不能以已有数字替代资格。");
  if(all.some(r=>r.source_eligibility?.status==="NOT_ALLOWED"||(r.evaluation_problems??[]).some(p=>p.code==="SOURCE_NOT_ALLOWED")))notes.add("非法来源组合保留作纠错，不是获准路径；见详情。");
  if(row.stable_condition?.includes("ARBITRARY_OVERRIDE"))notes.add("其他来源已批准；需显式选择并填有效数值，规则READY不代表输入完整。");
  if(/SUPPLY_UNIT_MEASURED|ENTERPRISE_MEASURED|ENTERPRISE_CALCULATED/.test(row.stable_condition??""))notes.add("遗留企业路径：当前限制仅该路径，不阻断目录或已批准其他来源。");
  return [...notes].join("\n")||"规则求值不等于完整正式输入可计算；必要数值/单位仍须核验。";
}
const priorFeedback=[];
if(previous){
  const prior=await SpreadsheetFile.importXlsx(await FileBlob.load(previous));
  for(const name of ["业务规则","操作与影响","本次变化"]){
    let sheet;try{sheet=prior.worksheets.getItem(name);}catch(error){if(name!=="业务规则")throw error;sheet=prior.worksheets.getItem("字段与条件规则");}
    const matrix=sheet.getUsedRange().values, index=matrix.findIndex(r=>r.includes("稳定审阅键"));
    if(index<0)throw new Error("Previous review lacks stable keys: "+name);
    const header=matrix[index], get=(row,h)=>header.includes(h)?row[header.indexOf(h)]:"";
    for(const row of matrix.slice(index+1)){
      const key=String(get(row,"稳定审阅键")??"");
      const feedback=feedbackHeaders.map(h=>get(row,h)??"");
      if(!key||!feedback.some(v=>v!==""))continue;
      priorFeedback.push({key,feedback,property:get(row,"意见针对属性")||"整体",
        condition:get(row,"意见针对条件")||"当前行",originalRevision:get(row,"原审阅版本")||key.split("|")[2],
        originalHash:get(row,"原审阅投影")||String(matrix[0]?.[0]??"").replace("审阅数据SHA256：",""),
        fingerprints:get(row,"内容指纹"),baselineFingerprints:get(row,"意见基线指纹")||get(row,"内容指纹"),linkState:get(row,"意见关联状态"),originKey:get(row,"原投影键")||key});
    }
  }
}
function baseIdentity(row,kind){return kind+"|"+row.rule_set_id+"|"+(row.field_id??row.operation_id??row.key);}
function conditionAllows(condition,sourcePath,direction){
  const tags=condition.tags??{};
  return (!tags.source_path||[tags.source_path].flat().includes(sourcePath))&&
    (!tags.direction||[tags.direction].flat().includes(direction));
}
function splitFields(fields){
  return fields.flatMap(row=>{
    if(row.field_id!=="electricity.factor"){
      const scopeNotes=row.field_id==="fuel.fch"?[...new Set((detailsPayload.fields??[]).filter(r=>r.field_id===row.field_id).flatMap(r=>r.channels??[]).map(c=>c.notes).filter(Boolean))].join("\n"):"";
      return [{...row,stable_condition:"整体",business_condition:"整体；具体适用条件见各属性"+(scopeNotes?"\n"+scopeNotes:""),stable_key:baseIdentity(row,"field")+"|整体"}];
    }
    const contexts=new Map();
    for(const prop of propertyKeys)for(const group of row[prop].groups)for(const c of group.conditions){
      const paths=[c.tags?.source_path].flat().filter(Boolean), directions=[c.tags?.direction].flat().filter(Boolean);
      for(const p of paths)for(const d of directions)contexts.set(p+"|"+d,{p,d});
    }
    return [...contexts.values()].sort((a,b)=>(a.p+a.d).localeCompare(b.p+b.d)).map(({p,d})=>{
      const part={...row,stable_condition:"source_path="+p+";direction="+d,
        business_condition:(stateLabels[d]??d)+" / "+(stateLabels[p]??p)};
      for(const prop of propertyKeys)part[prop]={...row[prop],groups:row[prop].groups.map(g=>({...g,conditions:g.conditions.filter(c=>conditionAllows(c,p,d))})).filter(g=>g.conditions.length)};
      part.name=row.name+"（"+part.business_condition+"）";
      part.stable_key=baseIdentity(row,"field")+"|"+part.stable_condition;
      return part;
    });
  });
}
function technicalProperty(row,prop,compactCondition){
  const actualProp=prop==="source"?"source_qualification":prop;
  const scope=String(row.stable_condition??"").match(/^source_path=([^;]+);direction=(.+)$/);
  const values=[];
  for(const candidate of detailsPayload.fields??[]){
    if(candidate.field_id!==row.field_id||candidate.rule_set_id!==row.rule_set_id||!candidate.policy_branch_values)continue;
    const when=candidate.conditions_by_property?.[actualProp];
    if(!when)continue;
    if(scope&&!conditionAllows(when,scope[1],scope[2]))continue;
    if(compactCondition){
      if(!Object.entries(compactCondition.tags??{}).every(([k,v])=>[v].flat().includes(when.tags?.[k])))continue;
      if(JSON.stringify(canonical(compactCondition.ranges??{}))!==JSON.stringify(canonical(when.ranges??{})))continue;
    }
    values.push(JSON.stringify(semanticSummary({condition:when,value:candidate.policy_branch_values[actualProp]})));
  }
  return [...new Set(values)].sort();
}
const groups=[
  {name:"业务规则",kind:"field",rows:splitFields(payload.fields),table:"FieldsReview"},
  {name:"操作与影响",kind:"operation",rows:payload.operations.map(r=>({...r,stable_key:baseIdentity(r,"operation")+"|整体",stable_condition:"整体"})),table:"OperationsReview"},
  {name:"本次变化",kind:"change",rows:payload.changes.map(r=>({...r,stable_key:baseIdentity(r,"change")+"|整体",stable_condition:"整体"})),table:"ChangesReview"},
];
for(const group of groups)for(const row of group.rows){
  row.object_identity=baseIdentity(row,group.kind);
  row.detail_locator=detailsName+"#"+encodeURIComponent(row.object_identity);
  if(group.kind==="operation")row.trigger="初始条件："+text(row.initial_context)+"\n触发与处理："+text(row.action)+"\n确认/取消："+text(row.confirmation);
  const ignored=new Set(["review_key","revision","key","stable_key","detail_locator"]);
  const content=Object.fromEntries(Object.entries(row).filter(([k])=>!ignored.has(k)));
  for(const prop of propertyKeys)if(content[prop])content[prop]=semanticSummary(content[prop]);
  row.fingerprints={"整体":digest([content,propertyKeys.map(p=>technicalProperty(row,p))])};
  for(const prop of propertyKeys)if(row[prop])row.fingerprints[propertyLabels[prop]]=digest([semanticSummary(row[prop]),row.stable_condition,technicalProperty(row,prop)]);
  if(group.kind==="operation")row.fingerprints["操作"]=digest([row.initial_context,row.action,row.changes,row.preserves,row.invalidates,row.confirmation]);
  const conditionScopes=new Map();
  for(const prop of propertyKeys)for(const g of row[prop]?.groups??[])for(const c of g.conditions??[]){
    const label=conditionText(c), key=propertyLabels[prop]+"@@"+label;
    if(!conditionScopes.has(key))conditionScopes.set(key,[]);
    conditionScopes.get(key).push({outcome:g.outcome,condition:c,technical:technicalProperty(row,prop,c)});
  }
  for(const [key,value] of conditionScopes)row.fingerprints[key]=digest(semanticSummary(value));
  row.visible_opinion_scopes=[...conditionScopes.keys()].map(key=>{const at=key.indexOf("@@");return {property:key.slice(0,at),condition:key.slice(at+2)};});
}
const current=new Map(groups.flatMap(g=>g.rows.map(r=>[r.stable_key,r])));
const claimed=new Set();
for(const old of priorFeedback){
  let row=current.get(old.key), legacy=false;
  if(!row){
    const parts=old.key.split("|");
    // Legacy SUMMARY keys carry a revision; only map when the whole object has one unambiguous row.
    if((parts[0]==="field"&&parts.length===5&&parts[4]==="SUMMARY")||(["operation","change"].includes(parts[0])&&parts.length===4)){
      const candidates=[...current.values()].filter(r=>r.object_identity===parts[0]+"|"+parts[1]+"|"+parts[3]);
      if(candidates.length===1){row=candidates[0];legacy=true;}
    }
  }
  let oldFingerprints={};try{oldFingerprints=JSON.parse(old.baselineFingerprints||"{}");}catch{}
  const scopeKey=old.property+(["当前行","整体"].includes(old.condition)?"":"@@"+old.condition);
  const applicable=row&&!claimed.has(row.stable_key)&&Object.hasOwn(row.fingerprints,scopeKey);
  if(applicable){
    row.feedback=old;
    let priorCurrent={};try{priorCurrent=JSON.parse(old.fingerprints||"{}");}catch{}
    const confirmed=old.linkState==="已复核本版"&&priorCurrent[scopeKey]===row.fingerprints[scopeKey];
    if(confirmed)old.baselineFingerprints=JSON.stringify(row.fingerprints);
    row.link_state=confirmed?"继续关联":!legacy&&old.linkState!=="需复核"&&oldFingerprints[scopeKey]===row.fingerprints[scopeKey]?"继续关联":"需复核";
    claimed.add(row.stable_key);
  }else{
    groups[2].rows.push({stable_key:"retention|"+digest([old.originKey,old.feedback,priorFeedback.indexOf(old)]),
      object_identity:"retention|"+old.key,stable_condition:"待映射",review_key:old.originKey,revision:metadata.revision,
      change_type:"未完成审阅意见保留",reason:"对象删除、条件/属性无法唯一确认或旧整体拆分；保留原意见，待映射，不猜测适用范围。",
      feedback:old,link_state:"待映射",fingerprints:oldFingerprints,detail_locator:detailsName+"#review-scope"});
  }
}
const changeTitles={CANDIDATE_ONLY_RULE_ASSETS:"候选规则资产",C01_FIXED_VERSION_ADOPTION:"固定版本通则采用",ELECTRICITY_SOURCE_QUALIFICATION:"电力来源资格",IDENTITY_CONFIRMATION_SEMANTICS:"身份确认行为",EXPLICIT_INITIAL_SOURCE_POLICY:"明确初始来源",CHANNEL_UNIT_AND_CONVERSION_PROJECTIONS:"渠道单位与换算",EMISSION_SOURCE_INVOLVEMENT_OPERATION:"排放源启停",MAPPING_R8_ALIGNMENT:"映射批准决定对齐",COMPATIBILITY_IMPACT_SCOPE:"兼容影响范围",CALCINATION_ROLE_CONTENT_EXPANSION:"煅烧输出角色含量展开",FUME_MONITORING_SEGMENT_AGGREGATION:"烟气监测分段汇总"};
function changeText(row,key){
  if(key==="change_type")return changeTitles[row.change_type]??row.change_type;
  return text(row[key]);
}
const technicalHeaders=["意见针对属性","意见针对条件","原审阅版本","原审阅投影","意见关联状态","稳定审阅键","内容指纹","意见基线指纹","原投影键","当前投影键","规则修订"];
let seen=0;
const manifests=[];
for(const group of groups){
  const {name,kind,rows,table:tableName}=group;
  const keys=kind==="field"
    ? ["name","mapping_refs","unit","source","default_source","default","locking","pending","basis","business_condition","detail_locator"]
    :kind==="operation"?["name","trigger","changes","preserves","invalidates","pending","detail_locator"]
    :["change_type","before","after","reason","pending","detail_locator"];
  const displayLabels={...labels,business_condition:"业务条件",detail_locator:"同源详情入口",trigger:"触发条件与处理"};
  const headers=keys.map(k=>displayLabels[k]??k).concat(feedbackHeaders,technicalHeaders);
  const matrix=[headers], unique=new Set();
  for(const row of rows){
    const key=row.stable_key;if(!key||unique.has(key))throw new Error("Missing/duplicate stable identity: "+key);unique.add(key);
    const prior=row.feedback;
    const notes=(prior?.feedback??["","",""]).map(literalCell);
    const tech=[prior?.property??"整体",prior?.condition??"当前行",prior?.originalRevision??row.revision??metadata.revision,
      prior?.originalHash??reviewHash,row.link_state??"",key,JSON.stringify(row.fingerprints),prior?(prior.baselineFingerprints||"{}"):JSON.stringify(row.fingerprints),prior?.originKey??row.review_key??row.key,row.review_key??row.key,row.revision??metadata.revision];
    matrix.push(keys.map(k=>{
      if(k==="unit")return unitText(row[k]);
      if(kind==="change")return changeText(row,k);
      if(kind==="field"&&propertyKeys.includes(k)){
        const normal=visibleProperty(row,k);let value=text(normal)||"此路径无有效普通组合；见待处理项及详情。";
        if(k==="default"&&normal?.groups?.some(g=>g.outcome.state==="BINDING"))value+="\n只读目录核对："+catalogReferenceText(row);
        return value;
      }
      if(kind==="field"&&k==="pending")return pendingPresentation(row);
      return text(row[k]);
    }).concat(notes,tech.map(literalCell)));
  }
  const sheet=wb.worksheets.add(name);sheet.showGridLines=false;
  sheet.getRange("A1").values=[["审阅数据SHA256："+reviewHash]];
  sheet.getRange("A2").values=[[name+" · 紧凑审阅V2"]];
  sheet.getRange("A3").values=[["候选修订："+(metadata.revision??"")+"；未接生产。整体意见可直接填写；条件意见请复制同源HTML中本行“合法条件值”，不要复制合并适用说明；需复核须人工确认本版，不自动清除。"]];
  sheet.getRange("A4").values=[["业务、意见和身份同属一个Table；打开同目录HTML后按对象目录或旁列定位查看详情。无生产codec/模板/数据库/历史Record兼容变化。"]];
  sheet.getRange("A1:A4").format.font={name:"Microsoft YaHei",size:10,color:"#555555"};
  sheet.getRange("A2").format.font={name:"Microsoft YaHei",size:15,bold:true,color:"#23445E"};
  const range=sheet.getRangeByIndexes(4,0,matrix.length,headers.length);
  range.values=matrix;range.format.font={name:"Microsoft YaHei",size:11};range.format.wrapText=true;range.format.verticalAlignment="top";
  range.format.columnWidth=55;range.format.rowHeight=80;
  sheet.getRangeByIndexes(4,0,matrix.length,1).format.columnWidth=32;
  if(kind==="field"){sheet.getRangeByIndexes(4,1,matrix.length,2).format.columnWidth=30;sheet.getRangeByIndexes(4,3,matrix.length,4).format.columnWidth=70;}
  if(kind==="operation"){sheet.getRangeByIndexes(4,1,matrix.length,1).format.columnWidth=90;}
  const metadataStart=keys.length+feedbackHeaders.length;
  sheet.getRangeByIndexes(4,metadataStart,matrix.length,technicalHeaders.length).format.columnWidth=28;
  sheet.getRangeByIndexes(4,metadataStart+5,matrix.length,6).format.wrapText=false;
  sheet.getRangeByIndexes(4,metadataStart+5,matrix.length,6).format.font={name:"Microsoft YaHei",size:9,color:"#777777"};
  const tableRef="A5:"+columnName(headers.length)+(matrix.length+4);
  const table=sheet.tables.add(tableRef,true,tableName);table.showFilterButton=true;
  sheet.getRangeByIndexes(5,keys.length,Math.max(1,rows.length),5).format.fill="#FFF4D6";
  sheet.getRangeByIndexes(5,keys.length+1,Math.max(1,rows.length),1).dataValidation={rule:{type:"list",values:["待处理","已落实","需决定","保留"]}};
  sheet.getRangeByIndexes(5,metadataStart,Math.max(1,rows.length),1).dataValidation={rule:{type:"list",values:kind==="field"?["整体","允许来源","默认来源","数值默认","读写锁定"]:kind==="operation"?["整体","操作"]:["整体"]}};
  sheet.getRangeByIndexes(5,metadataStart+4,Math.max(1,rows.length),1).dataValidation={rule:{type:"list",values:["继续关联","需复核","待映射","已复核本版"]}};
  sheet.freezePanes.freezeRows(5);sheet.freezePanes.freezeColumns(3);
  // Only human-readable business/feedback columns affect height; long identity/hash evidence stays single-line.
  for(let i=1;i<matrix.length;i++){
    let lineCount=1;
    for(let j=0;j<metadataStart+5;j++){
      const width=j===0?32:kind==="field"&&j<3?30:kind==="field"&&j>=3&&j<=6?70:kind==="operation"&&j===1?90:j>=metadataStart?28:55;
      const lines=String(matrix[i][j]??"").split("\n").reduce((n,line)=>n+Math.max(1,Math.ceil([...line].reduce((sum,c)=>sum+(c.charCodeAt(0)>=0x2e80?2:1),0)/(width-5))),0);
      lineCount=Math.max(lineCount,lines);
    }
    const height=Math.max(80,lineCount*16+8);
    if(height>409)throw new Error("Readable row needs further splitting: "+name+"!"+(i+5)+" ("+height+")");
    sheet.getRangeByIndexes(i+4,0,1,headers.length).format.rowHeight=height;
  }
  const header=sheet.getRangeByIndexes(4,0,1,headers.length);header.format.fill="#23445E";header.format.font={name:"Microsoft YaHei",size:11,color:"#FFFFFF",bold:true};header.format.rowHeight=42;
  sheet.tabColor="#23445E";seen+=rows.length;manifests.push({sheet:name,table:tableRef,rows:rows.length,headers});
}
function columnName(n){let s="";while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
function escapeHtml(s){return String(s??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");}
const detailGroups=new Map();
for(const [kind,rows] of [["field",detailsPayload.fields??[]],["operation",detailsPayload.operations??[]],["change",detailsPayload.changes??[]]]){
  for(const row of rows){const id=baseIdentity(row,kind);if(!detailGroups.has(id))detailGroups.set(id,[]);detailGroups.get(id).push(row);}
}
for(const group of groups)for(const row of group.rows){
  if(row.object_identity.startsWith("retention|"))continue;
  if(!detailGroups.has(row.object_identity))throw new Error("同源详情缺少工作簿定位对象："+row.object_identity);
}
function detailText(value){
  // Full details never reuse the compact groups formatter, which omits exact binding IDs.
  if(value===null||value===undefined)return "";
  if(Array.isArray(value))return value.map(detailText).join("\n");
  if(typeof value==="object")return Object.entries(value).map(([key,item])=>key+": "+detailText(item)).join("\n").replace(/[ \t]+$/gm,"");
  return text(value);
}
function detailBusinessSummary(row){
  const source=row.source??{},lock=row.locking??{};
  const legal=source.state==="FIXED"?(source.values??[]).map(v=>stateLabels[v]??v).join(" / "):stateLabels[source.state]??source.state??"未核对";
  const initial=row.default_source?.state==="FIXED"?stateLabels[row.default_source.source]??row.default_source.source:row.default_source?.reason??"无自动默认来源";
  const current=stateLabels[row.selected_business_source]??row.selected_business_source??"未选择";
  const reasons=[row.source_eligibility?.reason,row.source_correction?.reason,...(row.evaluation_problems??[]).map(x=>x.message)].filter(Boolean);
  const values=[["合法来源",legal],["默认来源/初始来源",initial],["当前来源",current],["数值可编辑性",stateLabels[lock.value?.state]??lock.value?.state??"见条件"],["来源选择可编辑性",stateLabels[lock.source?.state]??lock.source?.state??"见条件"],["规则组合求值状态",(stateLabels[row.evaluation_status]??row.evaluation_status??"未求值")+"；仅规则资格，不代表完整正式输入可计算"],["原因/纠错边界",[...new Set(reasons)].join("；")||"按本组合条件核验，不将编辑权限当作合法来源"],["只读目录默认核对",catalogReferenceText(row)]];
  return '<dl>'+values.map(([k,v])=>'<dt>'+escapeHtml(k)+'</dt><dd>'+escapeHtml(v)+'</dd>').join('')+'</dl>';
}
function kindForDetail(id){return id.split("|")[0];}
function detailTitle(row,index){
  const c=row.effective_context??row.context??row.condition?.tags??{};
  const businessKeys=["origin","source_path","direction","attribute","binding_status","material_calculation_path"];
  const context=conditionText({tags:Object.fromEntries(businessKeys.filter(k=>c[k]!==undefined).map(k=>[k,c[k]])),ranges:row.condition?.ranges??{}});
  const current=stateLabels[row.selected_business_source]??row.selected_business_source??"未选择来源";
  const status=row.evaluation_status==="READY"?"规则组合有效（非输入完成）":"规则受阻/待核";
  return "条件"+(index+1)+"："+context+" · 当前来源："+current+" · "+status;
}
let html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>业务规则审阅同源详情</title><style>body{font:16px/1.6 "Microsoft YaHei",sans-serif;max-width:1100px;margin:30px auto;padding:0 20px;color:#243746}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7fa;padding:14px}summary{cursor:pointer;font-weight:bold;padding:10px}section{border-bottom:1px solid #ddd}</style><h1>业务规则审阅同源详情</h1><p>候选未接生产；本文件由同一生成器和候选定义派生，不是第二真值源。</p><section id="review-scope"><h2>视图范围与审阅方式</h2><p>主表按业务概念汇总，电力按输入方式及方向拆分；不恢复442内部镜像或千行条件主表。此处保留各渠道、消费者、案例、完整条件、绑定与理由。意见可针对整体或指定属性；无明确条件映射时保留待映射。跨版本内容变化必须复核。</p><p>当前可见性审阅范围及原V1.2 §11要求的取代说明见STANDARD_SEMANTICS_POLICY.md §7；业务适用条件仍由既有Mapping和策略约束。</p><p>兼容影响：本轮候选未接生产，不改正式输入codec、批准模板、报告结构、DB迁移或历史Record。历史电力证据见ELECTRICITY_AND_COMPATIBILITY_EVIDENCE.md；electricity-paths.json中的旧head保持历史身份，不能作为当前候选的重验结果。</p><p>正式投影SHA256：'+reviewHash+'；详情输入SHA256：'+digest(detailsPayload)+'</p></section>';
html+=' <nav><h2>对象目录</h2><ul>'+[...detailGroups].map(([id,rows])=>'<li><a href="#'+escapeHtml(encodeURIComponent(id))+'">'+escapeHtml(rows[0].name??changeTitles[rows[0].change_type]??rows[0].change_type??id)+'</a></li>').join('')+'</ul></nav>';
for(const [id,rows] of detailGroups){
  html+='<section id="'+escapeHtml(id)+'"><h2>'+escapeHtml(rows[0].name??changeTitles[rows[0].change_type]??rows[0].change_type??id)+'</h2><p>'+escapeHtml(id)+'</p>';
  const opinionRows=groups.flatMap(g=>g.rows).filter(r=>r.object_identity===id&&r.visible_opinion_scopes?.length);
  if(opinionRows.length){
    html+='<h3>条件意见：合法条件值</h3><p>整体意见仍可用。条件意见请在表中选择下方属性，再逐条复制对应合法条件值到“意见针对条件”；主表合并后的适用说明不是可输入的条件标识。</p>';
    for(const row of opinionRows){html+='<details><summary>'+escapeHtml(row.name??row.stable_condition)+'</summary>';
      for(const scope of row.visible_opinion_scopes)html+='<p>'+escapeHtml(({"允许来源":"合法来源（意见属性：允许来源）","默认来源":"默认来源/初始来源","数值默认":"数值默认","读写锁定":"数值/来源选择可编辑性（意见属性：读写锁定）"})[scope.property]??scope.property)+'</p><pre data-review-row="'+escapeHtml(encodeURIComponent(row.stable_key))+'" data-review-property="'+escapeHtml(scope.property)+'">'+escapeHtml(scope.condition)+'</pre>';
      html+='</details>';
    }
  }
  // Share identical object-level values once; each condition retains every differing value.
  const shared=rows.length>1?Object.fromEntries(Object.entries(rows[0]).filter(([key,value])=>rows.every(r=>JSON.stringify(canonical(r[key]))===JSON.stringify(canonical(value))))):{};
  if(Object.keys(shared).length)html+='<details><summary>各条件共用信息（与下方逐条信息合并阅读）</summary><pre>'+escapeHtml(detailText(shared))+'</pre></details>';
  for(const [detailIndex,row] of rows.entries()){const unique=Object.fromEntries(Object.entries(row).filter(([key])=>!Object.hasOwn(shared,key)));
    html+='<details><summary>'+escapeHtml(kindForDetail(id)==='field'?detailTitle(row,detailIndex):row.name??changeTitles[row.change_type]??row.change_type??row.operation_id??row.review_key??'详情')+'</summary>'+(kindForDetail(id)==='field'?detailBusinessSummary(row):'')+'<details><summary>原始技术信息（保留完整身份与条件）</summary><pre>'+escapeHtml(detailText(unique))+'</pre></details></details>';
  }
  const reference=catalogReference(rows[0]);
  if(reference)html+='<details><summary>已核对目录参考值与精确来源定位（只读）</summary><p>注册数值核对不替代运行时按核算期间和采用上下文执行Resolver；有效期间按下列登记原样保留。</p><pre>'+escapeHtml(JSON.stringify(reference,null,2))+'</pre></details>';
  html+='</section>';
}
html+='<section><h2>Word报告关联与验收边界</h2><p>既有映射：specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md §13.1；既有报告结构：specs/reporting/GB_T_32151_34_2024_REPORT_SCHEMA.md「附录B业务结构」「RPT02批准表式映射」。这里只关联既有冻结记录报告能力，不新增WORD字段消费者。实际DOCX数值、表式与分页仍需后续报告专项验收；本审阅表不构成DOCX验收。</p></section></html>';
await fs.mkdir(path.dirname(output),{recursive:true});
await fs.writeFile(path.join(path.dirname(output),detailsName),html.replace(/[ \t]+$/gm,""),"utf8");
await (await SpreadsheetFile.exportXlsx(wb)).save(output);

// The bundled artifact tool has no documented column hiding/outline API.
// Use only Python's standard OOXML ZIP/XML libraries for these presentation attributes.
const foldScript=String.raw`
from pathlib import Path
import sys,zipfile,re,xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr
p=Path(sys.argv[1]); ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p) as z:
    entries=[(i,z.read(i.filename)) for i in z.infolist()]
shared=[]
for info,data in entries:
    if info.filename=='xl/sharedStrings.xml':
        shared=[''.join(x.itertext()) for x in ET.fromstring(data)]
hidden={'原审阅版本','原审阅投影','稳定审阅键','内容指纹','意见基线指纹','原投影键','当前投影键','规则修订'}
changed=[]
for info,data in entries:
    if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',info.filename):
        raw=data.decode('utf8'); root=ET.fromstring(raw); headers={}
        for c in root.findall("m:sheetData/m:row[@r='5']/m:c",ns):
            address=c.attrib['r']; col=0
            for ch in re.match('[A-Z]+',address)[0]: col=col*26+ord(ch)-64
            value=c.find('m:v',ns)
            headers[col]=shared[int(value.text)] if c.attrib.get('t')=='s' else ''.join(c.find('m:is',ns).itertext()) if c.find('m:is',ns) is not None else value.text if value is not None else ''
        cols=root.find('m:cols',ns)
        if cols is None or not hidden.issubset(set(headers.values())): raise ValueError('Review technical columns not found')
        prefix=re.search(r'<((?:[\w]+:)?)cols\b',raw).group(1)
        parts=[]
        for coldef in cols:
            for index in range(int(coldef.attrib['min']),int(coldef.attrib['max'])+1):
                attrs=dict(coldef.attrib);attrs.update(min=str(index),max=str(index))
                if headers.get(index) in hidden: attrs.update(hidden='1',outlineLevel='1')
                parts.append('<'+prefix+'col '+ ' '.join(k+'='+quoteattr(v) for k,v in attrs.items())+'/>')
        raw,count=re.subn(r'<(?:[\w]+:)?cols\b[^>]*>.*?</(?:[\w]+:)?cols>',lambda _: '<'+prefix+'cols>'+''.join(parts)+'</'+prefix+'cols>',raw,count=1,flags=re.S)
        if count!=1: raise ValueError('Unsupported worksheet cols representation')
        raw=re.sub(r'<(?:[\w]+:)?sheetFormatPr\b[^>]*/>',lambda m:m[0][:-2]+' outlineLevelCol="1"/>',raw,count=1)
        data=raw.encode('utf8')
    changed.append((info,data))
with zipfile.ZipFile(p,'w') as z:
    for info,data in changed:z.writestr(info,data)
`;
const fold=spawnSync(option("--python",process.env.PYTHON??"python"),["-c",foldScript,output],{encoding:"utf8"});
if(fold.error||fold.status!==0)throw new Error("技术列折叠失败；请用 --python 指定已有Python运行时（只用标准库，无新增生产依赖）："+(fold.error?.message??fold.stderr));

await fs.writeFile(path.join(path.dirname(output),"review-view-manifest.json"),JSON.stringify({view_revision:"compact-business-v2",definition_assets_hash_policy:"UTF8_TEXT_CRLF_TO_LF_SHA256",definition_assets_sha256:definitionAssets,projection_sha256:reviewHash,generator:"scripts/build_business_rules_review.mjs",details:detailsName,details_revision:detailsPayload.metadata?.revision,details_counts:Object.fromEntries(["fields","operations","changes"].map(k=>[k,detailsPayload[k]?.length??0])),details_sha256:digest(detailsPayload),details_projection_bound:detailsPayload.metadata?.source_compact_sha256===reviewHash,catalog_snapshot:catalogSnapshot?{catalog:catalogSnapshot.catalog,entries:catalogSnapshot.entries}:null,tables:manifests,retained_feedback:priorFeedback.length},null,2)+"\n","utf8");
if(!option("--skip-preview")){
 for(const name of ["业务规则","操作与影响","本次变化"]){const im=await wb.render({sheetName:name,range:"A1:G8",scale:1,format:"png"});await fs.writeFile(path.join(path.dirname(output),name+".png"),new Uint8Array(await im.arrayBuffer()));}
 const powerStart=groups[0].rows.findIndex(r=>r.field_id==="electricity.factor");
 if(powerStart>=0){const im=await wb.render({sheetName:"业务规则",range:"A"+(powerStart+6)+":G"+(powerStart+7),scale:1,format:"png"});await fs.writeFile(path.join(path.dirname(output),"电力长行.png"),new Uint8Array(await im.arrayBuffer()));}
}
console.log(JSON.stringify({status:"GENERATED",sheets:3,review_rows:seen,retained_feedback:priorFeedback.length,output,details:detailsName}));
