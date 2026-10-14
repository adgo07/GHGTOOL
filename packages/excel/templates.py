"""Approved per-standard Excel resources; downloads always copy verified bytes."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from packages.standards.carbon_material import STANDARD_ID, STANDARD_VERSION
from .appendix_b_legacy_structure import LEGACY_HEADER_CELLS, LEGACY_HEADER_MERGES

APPROVED_SOURCE_SHA256 = "c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4"
APPROVED_TEMPLATE_V2_SHA256 = "58b38c15d487bdc173f573a50e5b8f3446b5bb4df4693dd696a83742da5235b4"
APPROVED_TEMPLATE_V2_RESOURCE = "excel_templates/gb_t_32151_34_2024_appendix_b_v2.xlsx"
APPROVED_TEMPLATE_V3_SHA256 = "f303ad02ca03e0464f736dafc39967abd06366a902f1b502dd17470656eb1718"
APPROVED_TEMPLATE_V3_RESOURCE = "excel_templates/gb_t_32151_34_2024_appendix_b_v3.xlsx"
APPROVED_TEMPLATE_SHA256 = "64779587def196532ba8a315d985a2286e3c5c990aec032899c7c3e5b7bb60ac"
APPROVED_TEMPLATE_RESOURCE = "excel_templates/gb_t_32151_34_2024_appendix_b_v4.xlsx"
APPENDIX_B_SHEETS = tuple(f"B.{number}" for number in range(1, 10))


@dataclass(frozen=True, slots=True)
class ExcelTemplate:
    standard_id: str
    standard_version: str
    template_id: str
    template_version: str
    resource_path: str
    sha256: str

    @property
    def approved_master_path(self):
        return files("resources").joinpath(self.resource_path)


APPENDIX_B_TEMPLATE = ExcelTemplate(
    STANDARD_ID, STANDARD_VERSION,
    "GHGTOOL_GBT_32151_34_2024_APPENDIX_B", "2.2.0",
    APPROVED_TEMPLATE_RESOURCE, APPROVED_TEMPLATE_SHA256,
)


class ExcelTemplateService:
    """Small explicit registry, with no template generation or business formulas."""

    def __init__(self, templates: tuple[ExcelTemplate, ...] = (APPENDIX_B_TEMPLATE,)):
        self._templates = {item.standard_id: item for item in templates}
        if len(self._templates) != len(templates):
            raise ValueError("同一标准不能登记多个当前正式模板。")

    @classmethod
    def default(cls) -> "ExcelTemplateService":
        return cls()

    def get(self, standard_id: str = STANDARD_ID) -> ExcelTemplate:
        try:
            return self._templates[standard_id]
        except KeyError as exc:
            raise ValueError("此标准尚未登记经批准的 Excel 模板。") from exc

    def read_bytes(self, standard_id: str = STANDARD_ID) -> bytes:
        template = self.get(standard_id)
        content = template.approved_master_path.read_bytes()
        if sha256(content).hexdigest() != template.sha256:
            raise ValueError("正式 Excel 模板校验失败，请重新安装完整软件。")
        return content

    def copy_to(self, target: str | Path, standard_id: str = STANDARD_ID) -> Path:
        # Read and verify before touching the destination. Never re-save with openpyxl.
        content = self.read_bytes(standard_id)
        destination = Path(target)
        if destination.suffix.lower() != ".xlsx":
            raise ValueError("模板文件必须使用 .xlsx 扩展名。")
        master = self.get(standard_id).approved_master_path
        if isinstance(master, Path) and destination.resolve() == master.resolve():
            raise ValueError("不能覆盖软件内的正式模板资源。")
        destination.write_bytes(content)
        return destination

    def validate_structure(self, workbook, standard_id: str = STANDARD_ID) -> str:
        """Recognize approved headers while allowing inserted business data rows.

        Filled workbooks have their own hash. Formatting changes from Excel/WPS
        are allowed; fixed headers and their column grouping must remain intact.
        """
        if standard_id != STANDARD_ID:
            raise ValueError("此标准尚未实现正式 Excel 输入映射。")
        if tuple(workbook.sheetnames) != APPENDIX_B_SHEETS:
            raise ValueError("工作簿必须按原顺序保留 B.1 至 B.9 九张工作表。")
        is_v21 = (
            workbook["B.2"]["M2"].value == "名称类型"
            and workbook["B.2"]["N2"].value == "FCh来源"
            and workbook["B.7"]["I2"].value == "名称类型"
            and workbook["B.7"]["J2"].value == "因子来源"
        )
        current_note = workbook["B.2"]["A20"].value
        is_v22 = (
            is_v21 and isinstance(current_note, str)
            and current_note.startswith("来源栏用于确认参数来源；缺省值须有当前期间适用的 Resolver 绑定。")
        )
        is_v20 = (
            workbook["B.2"]["M2"].value == "名称类型"
            and workbook["B.7"]["I2"].value == "名称类型"
        )
        if not is_v21 and not is_v20:
            for name in APPENDIX_B_SHEETS:
                sheet = workbook[name]
                if sheet.sheet_state != "visible":
                    raise ValueError(f"{name} 工作表必须保持可见。")
                for coordinate,value in LEGACY_HEADER_CELLS[name].items():
                    if sheet[coordinate].value != value:
                        raise ValueError(f"{name}!{coordinate} 表头与已登记模板版本不一致。")
                end = 3 if name in {"B.2","B.3","B.4","B.5"} else 2
                actual = sorted(str(a) for a in sheet.merged_cells.ranges if a.min_row <= end)
                if actual != LEGACY_HEADER_MERGES[name]:
                    raise ValueError(f"{name} 表头合并区域与已登记模板版本不一致。")
                width = max(sheet[coordinate].column for coordinate in LEGACY_HEADER_CELLS[name])
                if any(c.value is not None for row in sheet.iter_rows(max_row=end,min_col=width+1) for c in row):
                    raise ValueError(f"{name} 存在未登记的新增表头，请使用软件当前模板。")
            return "1.0.0"
        if is_v22:
            template_version = "2.2.0"
            reference_bytes = self.read_bytes(standard_id)
        elif is_v21:
            template_version = "2.1.0"
            legacy_master = files("resources").joinpath(APPROVED_TEMPLATE_V3_RESOURCE)
            reference_bytes = legacy_master.read_bytes()
            if sha256(reference_bytes).hexdigest() != APPROVED_TEMPLATE_V3_SHA256:
                raise ValueError("旧版2.1 Excel模板校验失败，无法安全读取该版本工作簿。")
        else:
            template_version = "2.0.0"
            legacy_master = files("resources").joinpath(APPROVED_TEMPLATE_V2_RESOURCE)
            reference_bytes = legacy_master.read_bytes()
            if sha256(reference_bytes).hexdigest() != APPROVED_TEMPLATE_V2_SHA256:
                raise ValueError("旧版2.0 Excel模板校验失败，无法安全读取该版本工作簿。")
        reference = load_workbook(BytesIO(reference_bytes), data_only=False)
        try:
            for name in APPENDIX_B_SHEETS:
                sheet, approved = workbook[name], reference[name]
                if sheet.sheet_state != "visible":
                    raise ValueError(f"{name} 工作表必须保持可见。")
                header_end = 3 if name in {"B.2", "B.3", "B.4", "B.5"} else 2
                for row in approved.iter_rows(max_row=header_end):
                    for expected in row:
                        actual = sheet[expected.coordinate]
                        if actual.value != expected.value:
                            raise ValueError(f"{name}!{expected.coordinate} 表头与正式模板不一致。")
                expected_merges = {
                    str(area) for area in approved.merged_cells.ranges
                    if area.min_row <= header_end
                }
                actual_merges = {
                    str(area) for area in sheet.merged_cells.ranges
                    if area.min_row <= header_end
                }
                if actual_merges != expected_merges:
                    raise ValueError(f"{name} 表头合并区域与正式模板不一致。")
        finally:
            reference.close()
        return template_version
