import dataclasses
import hashlib
import json
import sys
import warnings
from collections import defaultdict
from collections.abc import Mapping
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from openpyxl import load_workbook

repo=Path(sys.argv[1]); before_path=Path(sys.argv[2]); saved_path=Path(sys.argv[3]); run_dir=Path(sys.argv[4])
# This evidence helper may read the repository but only writes/opens TEMP copies.
import tempfile
_temp_root = Path(tempfile.gettempdir()).resolve()
for _path in (before_path, saved_path, run_dir):
    if not _path.resolve().is_relative_to(_temp_root):
        raise ValueError("native round-trip evidence paths must stay inside TEMP")
# The default reproduces the historical 2.0 evidence; newer runs pass their exact approved SHA.
expected_template_sha=sys.argv[5] if len(sys.argv)>5 else "58b38c15d487bdc173f573a50e5b8f3446b5bb4df4693dd696a83742da5235b4"
sys.path.insert(0,str(repo))
from packages.application.catalog_queries import CatalogQueryService
from packages.application.carbon_accounting import CarbonAccountingPreviewUseCase, CarbonAccountingUseCase, create_g06_parameter_resolver
from packages.excel.appendix_b import AppendixBWorkbookImporter
import packages.excel.appendix_b as appendix_b_module
from packages.persistence import build_catalog_database, SQLiteCatalogRepository
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.standards.carbon_material import CarbonMaterialCalculator
from tests.exb01_fixture_helper import appendix_b_context

checks=[]; failures=[]
def add_check(name,condition,detail=None):
    checks.append({"name":name,"status":"PASS" if condition else "FAIL","detail":detail})
    if not condition: failures.append(name)
com_evidence_path=run_dir/"native-roundtrip-com-evidence.json"
com_evidence=json.loads(com_evidence_path.read_text(encoding="utf-8-sig"))
add_check("native_com_roundtrip_and_instance_safety",com_evidence.get("status")=="PASS",{"engine":com_evidence.get("engine"),"process_id":com_evidence.get("process_id"),"initial_workbooks":com_evidence.get("initial_workbooks"),"gate_passed_before_open":com_evidence.get("gate_passed_before_open")})
def sha_bytes(data): return hashlib.sha256(data).hexdigest()
def sha_file(path): return sha_bytes(path.read_bytes())

def workbook_audit(path):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        wb=load_workbook(path,data_only=False,read_only=False)
    try:
        sheets=[]; formula_cells=[]; blank_serialization=[]
        for ws in wb.worksheets:
            lock=hashlib.sha256(); total=locked=unlocked=0
            protection=ws.protection
            pfields=("sheet","objects","scenarios","selectLockedCells","selectUnlockedCells","formatCells","formatColumns","formatRows","insertColumns","insertRows","insertHyperlinks","deleteColumns","deleteRows","sort","autoFilter","pivotTables","password","algorithmName","hashValue","saltValue","spinCount")
            p={name:getattr(protection,name,None) for name in pfields}
            for row in ws.iter_rows(min_row=1,max_row=ws.max_row,min_col=1,max_col=ws.max_column):
                for cell in row:
                    is_locked=bool(cell.protection.locked); total+=1
                    locked+=int(is_locked); unlocked+=int(not is_locked)
                    lock.update(f"{cell.coordinate}:{int(is_locked)};".encode("ascii"))
                    if cell.data_type=="f": formula_cells.append((ws.title,cell.coordinate,str(cell.value)))
            sheets.append({"name":ws.title,"max_row":ws.max_row,"max_column":ws.max_column,"protection":p,"used_cells":total,"locked_cells":locked,"unlocked_cells":unlocked,"lock_map_sha256":lock.hexdigest()})
        return {"sheet_names":list(wb.sheetnames),"sheets":sheets,"formula_cells":formula_cells,"warnings":[str(x.message) for x in caught]}
    finally: wb.close()

def normalized_cell(value):
    return None if value is None or value=="" else value

def compare_cell_values(before_path,saved_path):
    wb1=load_workbook(before_path,data_only=False,read_only=False)
    wb2=load_workbook(saved_path,data_only=False,read_only=False)
    try:
        changes=[]; blank_differences=[]; formula_differences=[]
        names=sorted(set(wb1.sheetnames)|set(wb2.sheetnames))
        for name in names:
            if name not in wb1.sheetnames or name not in wb2.sheetnames:
                changes.append({"sheet":name,"kind":"sheet_missing"}); continue
            a=wb1[name]; b=wb2[name]
            max_row=max(a.max_row,b.max_row); max_col=max(a.max_column,b.max_column)
            for row in range(1,max_row+1):
                for col in range(1,max_col+1):
                    ca=a.cell(row,col); cb=b.cell(row,col)
                    va=ca.value; vb=cb.value
                    if va!=vb:
                        if (va is None and vb=="") or (va=="" and vb is None):
                            blank_differences.append({"sheet":name,"cell":ca.coordinate,"before":va,"after":vb})
                        else:
                            item={"sheet":name,"cell":ca.coordinate,"before":repr(va),"after":repr(vb),"before_type":ca.data_type,"after_type":cb.data_type}
                            changes.append(item)
                            if ca.data_type=="f" or cb.data_type=="f":
                                formula_differences.append(item)
        return {"value_change_count_after_blank_normalization":len(changes),"value_changes_after_blank_normalization":changes,"blank_serialization_difference_count":len(blank_differences),"blank_serialization_differences":blank_differences,"formula_text_change_count":len(formula_differences),"formula_text_changes":formula_differences}
    finally: wb1.close(); wb2.close()

GENERATED_ID_FIELDS={"input_id","enterprise_id","boundary_component_ids","unit_id","fuel_id","detail_id","line_id","instance_id"}
def generated_id_map(unit, input_value, workbook_sha):
    mapping={}; counters=defaultdict(int)
    def register(value,label):
        if isinstance(value,str) and value and value not in mapping:
            counters[label]+=1
            mapping[value]=f"<generated:{label}:{counters[label]}>"
    register(workbook_sha,"workbook_sha256")
    register(unit.unit_id,"unit_id")
    register(input_value.input_id,"input_id")
    register(input_value.enterprise_id,"enterprise_id")
    for value in input_value.boundary_component_ids: register(value,"boundary_component_id")
    def visit(value):
        if dataclasses.is_dataclass(value) and not isinstance(value,type):
            for f in dataclasses.fields(value):
                item=getattr(value,f.name)
                if f.name in GENERATED_ID_FIELDS:
                    if isinstance(item,(tuple,list)):
                        for v in item: register(v,f.name)
                    else: register(item,f.name)
                visit(item)
        elif isinstance(value,Mapping):
            for item in value.values(): visit(item)
        elif isinstance(value,(tuple,list,set,frozenset)):
            for item in value: visit(item)
    visit(input_value)
    return mapping

def normalize(value,id_map,ignored_fields=frozenset()):
    if isinstance(value,Enum): return value.value
    if isinstance(value,Decimal): return str(value)
    if isinstance(value,(datetime,date)): return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value,type):
        return {f.name:normalize(getattr(value,f.name),id_map,ignored_fields) for f in dataclasses.fields(value) if f.name not in ignored_fields}
    if isinstance(value,Mapping):
        return {str(k):normalize(v,id_map,ignored_fields) for k,v in sorted(value.items(),key=lambda x:str(x[0]))}
    if isinstance(value,(tuple,list)):
        return [normalize(v,id_map,ignored_fields) for v in value]
    if isinstance(value,(set,frozenset)):
        return sorted((normalize(v,id_map,ignored_fields) for v in value),key=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True))
    if isinstance(value,str):
        for token,replacement in sorted(id_map.items(),key=lambda pair:len(pair[0]),reverse=True):
            value=value.replace(token,replacement)
        return value
    if isinstance(value,bytes): return value.hex()
    if value is None or isinstance(value,(str,int,float,bool)): return value
    return repr(value)

def canonical_hash(value):
    return sha_bytes(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8"))

template_path=repo/"resources"/"excel_templates"/(sys.argv[6] if len(sys.argv)>6 else "gb_t_32151_34_2024_appendix_b_v2.xlsx")
template_sha=sha_file(template_path)
before_sha=sha_file(before_path); saved_sha=sha_file(saved_path)
audit_before=workbook_audit(before_path); audit_saved=workbook_audit(saved_path)
cell_compare=compare_cell_values(before_path,saved_path)
add_check("approved_template_sha_matches",template_sha==expected_template_sha,{"expected":expected_template_sha,"actual":template_sha})
add_check("nine_sheet_names_preserved",audit_before["sheet_names"]==audit_saved["sheet_names"] and len(audit_saved["sheet_names"])==9,{"before":audit_before["sheet_names"],"after":audit_saved["sheet_names"]})
add_check("sheet_protection_and_used_cell_lock_maps_preserved",audit_before["sheets"]==audit_saved["sheets"],{"before":audit_before["sheets"],"after":audit_saved["sheets"]})
add_check("all_cell_values_and_formulas_preserved_after_blank_normalization",cell_compare["value_change_count_after_blank_normalization"]==0,cell_compare)
add_check("no_new_or_changed_formula_cells",audit_before["formula_cells"]==audit_saved["formula_cells"],{"before":audit_before["formula_cells"],"after":audit_saved["formula_cells"]})

catalog=CatalogQueryService(SQLiteCatalogRepository(build_catalog_database(output_path=run_dir/"catalog-final.sqlite")))
calculator=CarbonMaterialCalculator(parameter_resolver=create_g06_parameter_resolver(catalog.repository))
importer=AppendixBWorkbookImporter(preview_use_case=CarbonAccountingPreviewUseCase(calculator),catalog_service=catalog)
context=appendix_b_context(year=2026,enterprise_name="专项业务链验收样例（合成数据）")
fixed_calculated_at=datetime(2026,10,14,10,49,tzinfo=timezone.utc)
class _FrozenDateTime(datetime):
    @classmethod
    def now(cls,tz=None): return fixed_calculated_at if tz else fixed_calculated_at.replace(tzinfo=None)
appendix_b_module.datetime=_FrozenDateTime
before_preview=importer.import_preview(before_path,context=context)
saved_preview=importer.import_preview(saved_path,context=context)
before_unit=before_preview.units[0]; saved_unit=saved_preview.units[0]
records=InMemoryRecordRepository()
add_check("before_preview_is_calculable",before_unit.can_calculate,{"error_count":len(before_unit.errors)})
add_check("saved_preview_is_calculable",saved_unit.can_calculate,{"error_count":len(saved_unit.errors)})
add_check("both_previews_create_zero_records",len(records.list_all())==0,{"record_count":len(records.list_all())})
before_ids=generated_id_map(before_unit,before_unit.input_value,before_preview.provenance.workbook_sha256)
saved_ids=generated_id_map(saved_unit,saved_unit.input_value,saved_preview.provenance.workbook_sha256)
input_before=normalize(before_unit.input_value,before_ids)
input_saved=normalize(saved_unit.input_value,saved_ids)
result_ignored=set()
snapshot_ignored=set()
trace_ignored=set()
result_before=normalize(before_unit.result,before_ids,result_ignored)
result_saved=normalize(saved_unit.result,saved_ids,result_ignored)
params_before=normalize(before_unit.calculation.parameter_snapshots,before_ids,snapshot_ignored)
params_saved=normalize(saved_unit.calculation.parameter_snapshots,saved_ids,snapshot_ignored)
traces_before=normalize(before_unit.calculation.traces,before_ids,trace_ignored)
traces_saved=normalize(saved_unit.calculation.traces,saved_ids,trace_ignored)
problems_before=normalize(before_unit.calculation.problems,before_ids)
problems_saved=normalize(saved_unit.calculation.problems,saved_ids)
warnings_before=normalize(before_unit.warnings,before_ids)
warnings_saved=normalize(saved_unit.warnings,saved_ids)
add_check("complete_business_input_matches_ignoring_generated_workbook_identity",input_before==input_saved,{"before_sha256":canonical_hash(input_before),"saved_sha256":canonical_hash(input_saved),"generated_identity_fields":["workbook_sha256","unit_id","input_id","enterprise_id","boundary_component_ids","fuel_id","detail_id","line_id","instance_id"]})
add_check("full_result_values_and_attribution_match",result_before==result_saved,{"before_sha256":canonical_hash(result_before),"saved_sha256":canonical_hash(result_saved)})
add_check("selected_parameters_sources_and_values_match",params_before==params_saved,{"before_sha256":canonical_hash(params_before),"saved_sha256":canonical_hash(params_saved),"snapshot_count":len(params_saved)})
add_check("formula_traces_and_process_attribution_match",traces_before==traces_saved,{"before_sha256":canonical_hash(traces_before),"saved_sha256":canonical_hash(traces_saved),"trace_count":len(traces_saved)})
add_check("calculation_problems_and_warnings_match_ignoring_generated_identity",problems_before==problems_saved and warnings_before==warnings_saved,{"problem_count":len(problems_saved),"warning_count":len(warnings_saved)})
record_count_after_preview=len(records.list_all())
add_check("record_count_after_preview_remains_zero",record_count_after_preview==0,{"record_count":record_count_after_preview})
formal=CarbonAccountingUseCase(calculator,records).calculate(saved_unit.input_value,calculated_at=fixed_calculated_at)
formal_result=normalize(formal.result,saved_ids,result_ignored)
add_check("formal_usecase_succeeds_and_appends_one_record",formal.successful and formal.record is not None and len(records.list_all())==1,{"successful":formal.successful,"record_count":len(records.list_all()),"problem_count":len(formal.problems)})
add_check("formal_result_matches_both_previews",formal_result==result_before==result_saved,{"before_preview_sha256":canonical_hash(result_before),"saved_preview_sha256":canonical_hash(result_saved),"formal_sha256":canonical_hash(formal_result)})

report={
 "status":"FAIL" if failures else "PASS",
 "pass_count":sum(c["status"]=="PASS" for c in checks),
 "fail_count":sum(c["status"]=="FAIL" for c in checks),
 "unexecuted_count":0,
 "checks":checks,
 "workbooks":{"before_path":str(before_path),"before_sha256":before_sha,"saved_path":str(saved_path),"saved_sha256":saved_sha,"source_workbook_sha256_before_and_after_roundtrip":"9F6C80D41BF80A504DD9C360224DAB773E3BF2C157FA0686BB2735D0E3BF7F98","template_path":str(template_path),"template_sha256":template_sha},
 "semantic_payloads":{
   "normalization_policy":{
     "identity_tokens":["workbook_sha256","unit_id","input_id","enterprise_id","boundary_component_ids","fuel_id","detail_id","line_id","instance_id"],
     "ignored_runtime_fields":[],"controlled_calculation_timestamp":fixed_calculated_at.isoformat(),
     "retained_fields":["numeric values","source/value types","selected factor IDs","parameter values and sources","process/source attribution","warning codes and messages after ID-token substitution"]
   },
   "canonical_input":{"before_equals_saved":input_before==input_saved,"sha256":canonical_hash(input_saved),"saved_payload":input_saved},
   "calculation_result":{"before_equals_saved":result_before==result_saved,"sha256":canonical_hash(result_saved),"saved_payload":result_saved},
   "parameter_snapshots":{"before_equals_saved":params_before==params_saved,"sha256":canonical_hash(params_saved),"saved_payload":params_saved},
   "calculation_traces":{"before_equals_saved":traces_before==traces_saved,"sha256":canonical_hash(traces_saved),"saved_payload":traces_saved},
   "runtime_timestamps":{
     "before_calculated_at":before_unit.result.calculated_at.isoformat() if before_unit.result else None,
     "saved_calculated_at":saved_unit.result.calculated_at.isoformat() if saved_unit.result else None,
     "before_imported_at":before_preview.provenance.imported_at.isoformat(),
     "saved_imported_at":saved_preview.provenance.imported_at.isoformat()
   }
 }, "native_roundtrip":com_evidence,"reproducibility":{"native_com_script_path":str(run_dir/"native_excel_roundtrip.ps1"),"adapter_usecase_script_path":str(Path(__file__).resolve()),"adapter_command":[str(repo/".venv"/"Scripts"/"python.exe"),str(Path(__file__).resolve()),str(repo),str(before_path),str(saved_path),str(run_dir)]},
 "cell_diff":{"blank_serialization_only_count":cell_compare["blank_serialization_difference_count"],"blank_serialization_differences":cell_compare["blank_serialization_differences"],"other_value_change_count":cell_compare["value_change_count_after_blank_normalization"],"formula_cell_count_before":len(audit_before["formula_cells"]),"formula_cell_count_after":len(audit_saved["formula_cells"]),"new_formula_count":len(set(audit_saved["formula_cells"])-set(audit_before["formula_cells"])),"formula_changes":cell_compare["formula_text_changes"]},
 "preview":{"units_before":len(before_preview.units),"units_after":len(saved_preview.units),"calculable_before":before_unit.can_calculate,"calculable_after":saved_unit.can_calculate,"record_count_after_previews":record_count_after_preview,"canonical_input_sha256":canonical_hash(input_saved),"result_sha256":canonical_hash(result_saved),"parameter_snapshot_sha256":canonical_hash(params_saved),"trace_sha256":canonical_hash(traces_saved),"selected_factor_count":sum(1 for s in saved_unit.calculation.parameter_snapshots if s.factor_id),"activity_counts":{"fuels":len(saved_unit.input_value.fuel_inputs),"calcinations":len(saved_unit.input_value.calcinations),"bakings":len(saved_unit.input_value.bakings),"graphitizations":len(saved_unit.input_value.graphitizations),"fume_incinerations":len(saved_unit.input_value.fume_incinerations),"fgd_units":len(saved_unit.input_value.fgd_units),"purchased_electricity":len(saved_unit.input_value.electricity_details),"exported_electricity":len(saved_unit.input_value.exported_electricity),"purchased_heat":len(saved_unit.input_value.purchased_heat),"exported_heat":len(saved_unit.input_value.exported_heat)},"formal_successful":formal.successful,"formal_record_count":len(records.list_all()),"formal_record_id":formal.record.record_id if formal.record else None},
 "sheet_protection":{"before":audit_before["sheets"],"after":audit_saved["sheets"]},
}
out=run_dir/"final-roundtrip-evidence.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(1 if failures else 0)

