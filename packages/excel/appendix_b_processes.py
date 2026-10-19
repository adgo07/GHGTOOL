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


def parse_process_sheets(importer,workbook,context,reader,errors,warnings,outputs,involved,unit_id,*,template_version="2.1.0"):
    from .appendix_b import _PROCESS_META,_has_value,_is_appendix_footer_row,_stable_id
    for sheet_name,meta in _PROCESS_META.items():
        source_id,model_type,parameter_id,parameter_name,index=meta
        sheet=workbook[sheet_name]
        stop=next((r for r in range(4,sheet.max_row+1) if _is_appendix_footer_row(sheet,r)),sheet.max_row+1)
        materials={}
        for row in range(4,stop):
            if not any(_has_value(sheet[f"{column}{row}"]) for column in ("DEIJKLM" if template_version in {"2.4.0", "2.5.0", "2.6.0", "2.7.0", "2.8.0"} else "DE")):
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
            role,component=role_kind
            mass=reader.number(workbook,sheet_name,f"D{row}",errors,required=True,field_label="活动数据")
            percentage=reader.number(workbook,sheet_name,f"E{row}",errors,field_label="碳/挥发分含量")
            source=reader.text(workbook,sheet_name,f"F{row}",errors,field_label="碳/挥发分来源")
            source_kind = {None:MaterialDataSource.MEASURED, "实测值":MaterialDataSource.MEASURED}.get(source)
            extra = {}
            unit = "%"
            if template_version in {"2.4.0", "2.5.0", "2.6.0", "2.7.0", "2.8.0"}:
                source_kind = {None:MaterialDataSource.MEASURED, "实测值":MaterialDataSource.MEASURED,
                               "计算值":MaterialDataSource.CHEMICAL_CALCULATION}.get(source)
                if template_version == "2.4.0" and source == "收到基换算":
                    source_kind = MaterialDataSource.CHEMICAL_CALCULATION
                mass_basis = reader.text(workbook,sheet_name,f"I{row}",errors,field_label="质量基准")
                comp_basis = reader.text(workbook,sheet_name,f"J{row}",errors,field_label="含量基准")
                moisture = reader.number(workbook,sheet_name,f"K{row}",errors,field_label="收到基水分")
                method = reader.text(workbook,sheet_name,f"L{row}",errors,field_label="换算方法")
                unit = reader.text(workbook,sheet_name,f"M{row}",errors,field_label="含量单位") or "%"
                bases = {None:"RECEIVED", "收到基":"RECEIVED", "干基":"DRY"}
                extra = {"mass_basis":bases.get(mass_basis, "UNKNOWN"),
                         "composition_basis":bases.get(comp_basis, "UNKNOWN"),
                         "moisture_received_percent":moisture,
                         "conversion_method": {None:None, "按收到基水分归一":"DRY_TO_RECEIVED_MOISTURE"}.get(method, "UNKNOWN")}
            if source_kind is None:
                errors.append(ImportMessage("EXB01_PROCESS_SOURCE_UNSUPPORTED","请选择此模板支持的材料来源。",f"{sheet_name}!F{row}","碳/挥发分来源"))
                source_kind = MaterialDataSource.STANDARD_DEFAULT
            if not all((name,process,material)):
                continue
            key=(process,material)
            entry=materials.setdefault(key,{"role":role,"name":name,"masses":[],"fixed":[],"volatile":[], "extra":extra, "sources":{}, "units":{}})
            if entry["extra"] != extra:
                errors.append(ImportMessage("EXB01_PROCESS_BASIS_MISMATCH","同一物料两行的基准、水分和方法必须一致。",f"{sheet_name}!I{row}","基准换算"))
            entry["sources"][component] = source_kind
            entry["units"][component] = unit
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
                fixed_carbon_source=entry["sources"].get("fixed",MaterialDataSource.MEASURED),
                volatile_matter_percent=entry["volatile"][0][1] if entry["volatile"] else None,
                volatile_matter_source=entry["sources"].get("volatile",MaterialDataSource.MEASURED),
                fixed_carbon_unit=entry["units"].get("fixed","%"),
                volatile_matter_unit=entry["units"].get("volatile","%"), **entry["extra"])
            processes.setdefault(process,[]).append(line)
        for process,lines in processes.items():
            factor=importer._default_factor(parameter_id,context.period)
            parameter=importer._parameter_value(factor,"采用当前期间Resolver核验的标准一般参数。") if factor else None
            # Business process names are unique within this workbook; no technical ID is requested from users.
            outputs[index].append(model_type(instance_id=_stable_id("process",unit_id,sheet_name,process),instance_name=process,material_rows=tuple(lines),**{parameter_name:parameter}))
            involved.add(source_id)
