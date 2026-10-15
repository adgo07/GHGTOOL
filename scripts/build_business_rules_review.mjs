// Development-only review artifact; never imported by the desktop application.
import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const args = process.argv.slice(2);
function option(key, fallback) { const i=args.indexOf(key); return i<0?fallback:args[i+1]; }
const input=option("--input"), output=option("--output"), previous=option("--previous");
if(!input || !output) throw new Error("Required: --input candidate-review.json --output review.xlsx [--previous review.xlsx]");
const reviewText=await fs.readFile(input,"utf8");
const reviewHash=createHash("sha256").update(reviewText.replace(/\r\n/g,"\n"),"utf8").digest("hex");
const payload=JSON.parse(reviewText);
const wb=Workbook.create();
const comments=new Map();
const feedbackHeaders=["审阅意见","处理状态","审阅编号"];
if(previous){
  const prior=await SpreadsheetFile.importXlsx(await FileBlob.load(previous));
  for(const name of ["业务规则","操作与影响","本次变化"]){
    let sheet;
    try { sheet=prior.worksheets.getItem(name); } catch (error) { if(name!=="业务规则") throw error; sheet=prior.worksheets.getItem("字段与条件规则"); }
    const matrix=sheet.getUsedRange().values;
    const index=matrix.findIndex(r=>r.includes("稳定审阅键"));
    if(index<0) throw new Error(`Previous review lacks stable keys: ${name}`);
    const header=matrix[index], keyCol=header.indexOf("稳定审阅键");
    for(const row of matrix.slice(index+1)){
      const key=row[keyCol];
      if(!key) continue;
      const feedback=feedbackHeaders.map(h=>row[header.indexOf(h)]??"");
      if(feedback.some(v=>v!=="")) comments.set(String(key),feedback);
    }
  }
}
const objectLabels={state:"状态",reason:"理由",values:"允许来源",value:"值",source:"来源",parameter_id:"参数ID",binding_id:"绑定ID",tags:"匹配条件",ranges:"范围与边界",origin:"对象类别",binding_status:"绑定资格",business_source:"当前来源",direction:"方向",attribute:"电力属性",source_path:"因子路径",catalog_table:"来源表",province:"省份",region:"区域",min:"下界",max:"上界",include_min:"包含下界",include_max:"包含上界",carbonate_component_count:"本实例组分数",channel:"渠道",label:"渠道名称",unit:"单位",binding:"控件/模型绑定"};
const stateLabels={NONE:"无自动默认",NOT_APPLICABLE:"不适用",NO_LEGAL_SOURCES:"无合法来源",FIXED:"固定定义",BINDING:"引用参数绑定",POLICY:"登记策略",PENDING:"待核验",EDITABLE:"可填写/选择",LOCKED:"只读",CONDITIONAL:"条件待展开",STANDARD_DEFAULT:"缺省值",CALCULATED:"计算值",MEASURED:"实测值",CATALOG:"目录对象",CUSTOM:"自定义",LEGACY_UNSPECIFIED:"历史身份未确认",PURCHASED:"购入",EXPORTED:"输出",CONVENTIONAL:"常规电力",NONFOSSIL:"非化石",FOSSIL:"化石",VERIFIED:"来源登记已核验",ABSENT:"无适用绑定",READY:"可用",BLOCKED:"受阻",RESOLVED:"已求值",SOURCE_NOT_ALLOWED:"所选来源不合法",SUPPLY_UNIT_MEASURED:"供电单位实测",ENTERPRISE_MEASURED:"企业实测",ENTERPRISE_CALCULATED:"企业计算",ARBITRARY_OVERRIDE:"任意覆盖路径（现有候选未开放）",NONFOSSIL_ZERO:"非化石购电零排放",CATALOGUE_TABLE_1:"目录表1",CATALOGUE_TABLE_2:"目录表2",CATALOGUE_TABLE_3:"目录表3",CATALOGUE_TABLE_4:"目录表4",CATALOGUE_TABLE_5:"目录表5"};
function literalCell(value){ const raw=String(value??""); return raw.startsWith("=")?"'"+raw:raw; }
function text(value){
  if(value===null || value===undefined) return "";
  if(Array.isArray(value)) return value.map(text).join("\n");
  if(typeof value==="object" && Array.isArray(value.groups)) return summaryText(value);
  if(typeof value==="object") return Object.entries(value).map(([k,v])=>`${objectLabels[k]??k}: ${text(v)}`).join("\n");
  const raw=String(value).replaceAll("Canonical","统一输入").replaceAll("Catalog","参数库").replaceAll("Record","正式记录").replaceAll("numeric default","数值默认").replaceAll("default_source","初始来源");
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
      if(value.state==="FIXED") result=value.values?value.values.map(v=>stateLabels[v]??v).join(" / "):value.source?(stateLabels[value.source]??value.source):text(value.value);
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
let seen=0;
for(const [name,records,tableName] of [["业务规则",payload.fields,"FieldsReview"],["操作与影响",payload.operations,"OperationsReview"],["本次变化",payload.changes,"ChangesReview"]]){
  if(!Array.isArray(records)) throw new Error(`Review JSON missing ${name} rows`);
  const rows=records.map(r=>{ const row={...r};
    if(Array.isArray(row.channels)){
      row.visibility=row.channels.map(p=>{
        const marker=String(p.notes??"").match(/可见性[：:]([^\n]*)/);
        return `${p.channel} / ${p.binding}: ${marker?marker[1]:"见渠道说明（未独立声明控件显隐）"}`;
      });
      row.projection_notes=row.channels.map(p=>`${p.channel} / ${p.binding}: ${p.notes??""}`);
      row.channels=row.channels.map(({notes,...projection})=>projection);
    } if(row.review_key && row.key!==undefined){ if(row.key!==row.review_key) row.definition_key=row.key; delete row.key; } return row; });
  if(name==="本次变化"){
    const retained=new Set([...(payload.fields??[]),...(payload.operations??[]),...rows].map(r=>String(r.review_key??r.key??"")));
    for(const [key,feedback] of comments){if(!retained.has(key))rows.push({review_key:key,change_type:"未完成审阅意见保留",reason:"对应行已变化，请按稳定ID复核",preserved_feedback:feedback});}
  }
  const present=[...new Set(rows.flatMap(r=>Object.keys(r)).filter(k=>k!=="preserved_feedback"))];
  const preferred=name==="业务规则"
    ? ["name","mapping_refs","unit","source","default_source","default","locking","pending","basis","review_key"]
    : name==="操作与影响"
      ? ["name","changes","preserves","invalidates","pending","review_key"]
      : ["change_type","before","after","reason","pending","review_key"];
  const keys=preferred.filter(k=>present.includes(k) && k!=="review_key" && k!=="key");
  const matrix=[keys.map(k=>labels[k]??k).concat(["",...feedbackHeaders,"稳定审阅键"])];
  const unique=new Set();
  for(const row of rows){
    const key=String(row.review_key??row.key??"");
    if(!key || unique.has(key)) throw new Error(`Missing/duplicate review key: ${name} ${key}`);
    unique.add(key);
    matrix.push(keys.map(k=>k==="unit"?unitText(row[k]):text(row[k])).concat(["",...(comments.get(key)??row.preserved_feedback??["","",""]).map(literalCell),key]));
  }
  const sheet=wb.worksheets.add(name);sheet.showGridLines=false;
  sheet.getRange("A1").values=[[`审阅数据SHA256：${reviewHash}`]];
  sheet.getRange("A1").format.font={name:"Microsoft YaHei",size:9,color:"#666666"};
  sheet.getRange("A2").values=[[name]];
  sheet.getRange("A2").format.font={name:"Microsoft YaHei",size:14,bold:true};
  sheet.getRange("A3").values=[[`A包候选 · ${text(metadata.revision??metadata.rule_set??"1.0")} · 不切生产`]];
  sheet.getRange("A4").values=[["现有业务政策摘要；最终对齐等待映射批准。技术组合由测试核验，黄色列保留审阅意见。"]];
  const range=sheet.getRangeByIndexes(4,0,matrix.length,matrix[0].length);
  range.values=matrix;
  range.format.font={name:"Microsoft YaHei",size:11};
  range.format.verticalAlignment="top";range.format.wrapText=true;
  range.format.columnWidth=30;range.format.rowHeight=108;
  const table=sheet.tables.add(`A5:${columnName(keys.length)}${matrix.length+4}`,true,tableName);
  table.showFilterButton=true;
  sheet.getRangeByIndexes(4,0,matrix.length,1).format.columnWidth=26;
  sheet.getRangeByIndexes(4,1,matrix.length,1).format.columnWidth=34;
  for(const [key,width] of [["mapping_refs",36],["unit",18],["condition",48],["source",38],["default_source",34],["default",38],["locking",48],["visibility",42],["channels",65],["basis",75],["consumers",75],["cases",75],["projection_notes",90]]){
    const index=keys.indexOf(key);
    if(index>=0) sheet.getRangeByIndexes(4,index,matrix.length,1).format.columnWidth=width;
  }
  const header=sheet.getRangeByIndexes(4,0,1,matrix[0].length);
  header.format.fill="#23445E";header.format.font={name:"Microsoft YaHei",size:11,color:"#FFFFFF",bold:true};header.format.rowHeight=36;
  const feedback=sheet.getRangeByIndexes(5,keys.length+1,Math.max(1,rows.length),3);
  feedback.format.fill="#FFF4D6";
  sheet.getRangeByIndexes(5,keys.length+2,Math.max(1,rows.length),1).dataValidation={rule:{type:"list",values:["待处理","已落实","需决定","保留"]}};
  sheet.freezePanes.freezeRows(5);sheet.freezePanes.freezeColumns(Math.min(3,keys.length));
  const keyIndex=keys.length+1+feedbackHeaders.length;
  if(keyIndex>=0) { const keyRange=sheet.getRangeByIndexes(5,keyIndex,Math.max(1,rows.length),1); keyRange.format.wrapText=true; keyRange.format.columnWidth=70; keyRange.format.font={name:"Microsoft YaHei",size:9,color:"#777777"}; }
  range.format.autofitRows();
  header.format.rowHeight=36;
  sheet.tabColor="#23445E";
  seen+=rows.length;
}
function columnName(n){let s="";while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
wb.recalculate();
await fs.mkdir(path.dirname(output),{recursive:true});
console.log((await wb.inspect({kind:"table",range:"业务规则!A5:H8",include:"values",tableMaxRows:4,tableMaxCols:8,maxChars:1800})).ndjson);
console.log((await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!",options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
for(const name of ["业务规则","操作与影响","本次变化"]){
  const image=await wb.render({sheetName:name,range:"A1:H8",scale:1,format:"png"});
  await fs.writeFile(path.join(path.dirname(output),`${name}.png`),new Uint8Array(await image.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
console.log(JSON.stringify({status:"PASS",sheets:3,review_rows:seen,retained_feedback:comments.size,output}));
