"""V5 template resource and compatibility protections; no native Office claim."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from zipfile import ZipFile
from openpyxl import load_workbook
from packages.excel.templates import (ExcelTemplateService, APPENDIX_B_SHEETS,
 APPROVED_TEMPLATE_SHA256, APPROVED_TEMPLATE_RESOURCE, APPROVED_TEMPLATE_V4_RESOURCE,
 APPROVED_TEMPLATE_V4_SHA256, APPROVED_TEMPLATE_V3_RESOURCE, APPROVED_TEMPLATE_V3_SHA256,
 APPROVED_TEMPLATE_V2_RESOURCE, APPROVED_TEMPLATE_V2_SHA256)

class FuelPowerTemplateV5Tests(TestCase):
 def test_download_copies_exact_registered_bytes_and_recognizes_v5(self):
  service=ExcelTemplateService.default()
  content=service.read_bytes()
  self.assertEqual(sha256(content).hexdigest(),APPROVED_TEMPLATE_SHA256)
  with TemporaryDirectory() as tmp:
   output=service.copy_to(Path(tmp)/"template.xlsx")
   self.assertEqual(output.read_bytes(),content)
  workbook=load_workbook(BytesIO(content))
  try:
   self.assertEqual(tuple(workbook.sheetnames),APPENDIX_B_SHEETS)
   self.assertEqual(service.validate_structure(workbook),"2.3.0")
   self.assertTrue(workbook["B.2"]["A20"].value.startswith("燃料输入规则 V5："))
   formulas={str(d.sqref):d.formula1 for d in workbook["B.2"].data_validations.dataValidation}
   self.assertIn("直接计算值",formulas["E4:E18"])
   self.assertEqual(formulas["G4:G18"],'"缺省值,实测值"')
   self.assertEqual(formulas["N4:N18"],'"缺省值,实测值"')
  finally: workbook.close()
 def test_all_other_ooxml_parts_are_identical_to_v4(self):
  with ZipFile(Path("resources")/APPROVED_TEMPLATE_RESOURCE) as new, ZipFile(Path("resources")/APPROVED_TEMPLATE_V4_RESOURCE) as old:
   self.assertEqual(new.namelist(),old.namelist())
   changed=[name for name in old.namelist() if old.read(name)!=new.read(name)]
   self.assertEqual(changed,["xl/worksheets/sheet2.xml"])
 def test_prior_template_bytes_and_version_identity_remain_intact(self):
  service=ExcelTemplateService.default()
  for resource,digest,version in [(APPROVED_TEMPLATE_V2_RESOURCE,APPROVED_TEMPLATE_V2_SHA256,"2.0.0"),(APPROVED_TEMPLATE_V3_RESOURCE,APPROVED_TEMPLATE_V3_SHA256,"2.1.0"),(APPROVED_TEMPLATE_V4_RESOURCE,APPROVED_TEMPLATE_V4_SHA256,"2.2.0")]:
   with self.subTest(version=version):
    content=(Path("resources")/resource).read_bytes()
    self.assertEqual(sha256(content).hexdigest(),digest)
    workbook=load_workbook(BytesIO(content))
    try: self.assertEqual(service.validate_structure(workbook),version)
    finally: workbook.close()
