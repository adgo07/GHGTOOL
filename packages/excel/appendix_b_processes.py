"""Explicit process/material grouping for the current approved template."""
from packages.standards.carbon_material_normalization import MaterialInputLine,MaterialDataSource
from packages.standards.carbon_material_process_inputs import process_role_component
from .ingress import ImportMessage


def _group_label(sheet,row):
    value=sheet[f"A{row}"].value
    if value is not None:
        return value
    for area in sheet.merged_cells.ranges:
        if area.min_col==1 and area.max_col==1 and area.min_row<=row<=area.max_row:
            return sheet.cell(area.min_row,1).value
    return None


def parse_process_sheets(importer,workbook,context,reader,errors,warnings,outputs,involved,unit_id):
    from .appendix_b import _PROCESS_META,_has_value,_is_appendix_footer_row,_stable_id
    for sheet_name,meta in _PROCESS_META.items():
        source_id,model_type,parameter_id,parameter_name,index=meta
        sheet=workbook[sheet_name]
        stop=next((r for r in range(4,sheet.max_row+1) if _is_appendix_footer_row(sheet,r)),sheet.max_row+1)
        materials={}
        for row in range(4,stop):
            if not any(_has_value(sheet[f"{column}{row}"]) for column in "DE"):
                continue
            category=reader.text(workbook,sheet_name,f"B{row}",errors,required=True,field_label="物料类别")
            name=reader.text(workbook,sheet_name,f"C{row}",errors,required=True,field_label="实际物料名称")
            process=reader.text(workbook,sheet_name,f"G{row}",errors,required=True,field_label="工序名称")
            material=reader.text(workbook,sheet_name,f"H{row}",errors,required=True,field_label="物料序号")
            group=_group_label(sheet,row)
            if not group:
                errors.append(ImportMessage("EXB01_PROCESS_GROUP_REQUIRED","该活动行缺少明确过程分组。",f"{sheet_name}!A{row}","过程分组"))
                continue
            role_kind=process_role_component(sheet_name,group,category)
            if role_kind is None:
                errors.append(ImportMessage("EXB01_PROCESS_ROW_UNMAPPED","物料类别与过程分组不匹配；请选择明确的类别与碳/挥发分分组。",f"{sheet_name}!B{row}","物料类别"))
                continue
            mass=reader.number(workbook,sheet_name,f"D{row}",errors,required=True,field_label="活动数据")
            percentage=reader.number(workbook,sheet_name,f"E{row}",errors,field_label="碳/挥发分含量")
            source=reader.text(workbook,sheet_name,f"F{row}",errors,field_label="碳/挥发分来源")
            if source not in (None,"实测值"):
                errors.append(ImportMessage("EXB01_PROCESS_SOURCE_UNSUPPORTED","该表的碳/挥发分来源仅支持实测值。",f"{sheet_name}!F{row}","碳/挥发分来源"))
            if not all((name,process,material)):
                continue
            role,component=role_kind
            key=(process,material)
            entry=materials.setdefault(key,{"role":role,"name":name,"masses":[],"fixed":[],"volatile":[]})
            if entry["role"] is not role or entry["name"]!=name:
                errors.append(ImportMessage("EXB01_PROCESS_IDENTITY_MISMATCH","同一工序与物料序号必须对应同一类别和实际名称；新物料请使用独立序号。",f"{sheet_name}!C{row}","物料归属"))
                continue
            if mass is not None:entry["masses"].append((row,mass))
            if percentage is not None:entry[component].append((row,percentage))
        processes={}
        for (process,material),entry in materials.items():
            masses=entry["masses"]
            if len({mass for _,mass in masses})>1:
                errors.append(ImportMessage("EXB01_PROCESS_PAIRED_MASS_MISMATCH","同一物料碳与挥发分行的活动数据必须完全一致；不相加或猜测。",f"{sheet_name}!D{masses[-1][0]}","活动数据"))
            for component in ("fixed","volatile"):
                if len(entry[component])>1:
                    errors.append(ImportMessage("EXB01_PROCESS_DUPLICATE_COMPONENT","同一工序和物料序号存在重复组分；新增物料请给出独立序号。",f"{sheet_name}!E{entry[component][1][0]}","碳/挥发分含量"))
            line=MaterialInputLine(line_id=_stable_id("material",unit_id,sheet_name,process,material),role=entry["role"],name=entry["name"],
                mass_t=masses[0][1] if masses else None,
                fixed_carbon_percent=entry["fixed"][0][1] if entry["fixed"] else None,
                fixed_carbon_source=MaterialDataSource.MEASURED,
                volatile_matter_percent=entry["volatile"][0][1] if entry["volatile"] else None,
                volatile_matter_source=MaterialDataSource.MEASURED)
            processes.setdefault(process,[]).append(line)
        for process,lines in processes.items():
            factor=importer._default_factor(parameter_id,context.period)
            parameter=importer._parameter_value(factor,"采用当前期间Resolver核验的标准一般参数。") if factor else None
            # Business process names are unique within this workbook; no technical ID is requested from users.
            outputs[index].append(model_type(instance_id=_stable_id("process",unit_id,sheet_name,process),instance_name=process,material_rows=tuple(lines),**{parameter_name:parameter}))
            involved.add(source_id)
