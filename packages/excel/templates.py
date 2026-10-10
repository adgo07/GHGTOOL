"""Approved per-standard Excel resources; downloads always copy verified bytes."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from packages.standards.carbon_material import STANDARD_ID, STANDARD_VERSION

APPROVED_SOURCE_SHA256 = "c805e446994e0863221063109f2b425a545d0c7db88544ba5583102219c1d9e4"
APPROVED_TEMPLATE_SHA256 = "e6a070bf28adb47939e24713f676136b5a023017d6f695e0031c68d51c389c3d"
APPROVED_TEMPLATE_RESOURCE = "excel_templates/gb_t_32151_34_2024_appendix_b_v1.xlsx"
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
    "GHGTOOL_GBT_32151_34_2024_APPENDIX_B", "1.0.0",
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

    def validate_structure(self, workbook, standard_id: str = STANDARD_ID) -> None:
        """Recognize approved headers while allowing inserted business data rows.

        Filled workbooks have their own hash. Formatting changes from Excel/WPS
        are allowed; fixed headers and their column grouping must remain intact.
        """
        if standard_id != STANDARD_ID:
            raise ValueError("此标准尚未实现正式 Excel 输入映射。")
        if tuple(workbook.sheetnames) != APPENDIX_B_SHEETS:
            raise ValueError("工作簿必须按原顺序保留 B.1 至 B.9 九张工作表。")
        reference = load_workbook(BytesIO(self.read_bytes(standard_id)), data_only=False)
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
