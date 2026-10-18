"""受控机械演进B.9热力输入；仅改v9的sheet9部件，旧模板原字节保留。"""
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import argparse, re
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v9.xlsx'
TARGET=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v10.xlsx'
SOURCE_SHA='0fa20cbc126fadd2807fe02bea9b26b4a8855285e6b90fc171985557a895fae9'
NOTE='数据提示：热力输入规则 V10（2.8.0）。H明确选已知焓并在F填写kJ/kg；不采用D/E辅助状态推算或替换已知值。自动物性暂不可用，不回退旧表。I选缺省值时G留空，由软件核验真实适用来源；选实测值须填G，空白不回缺省，0保留。购入热力在J确认热源位于本企业边界内/外，K声明供热燃料是否已计入本企业。内部且已计不重复计购热，不删除原燃料；其他内部/未知/冲突需澄清。输出不要求购入边界资格。L来源说明选填。新增数据行放本提示上方。'
HEADERS={'H':'焓值方式','I':'因子来源','J':'热源所在边界','K':'供热燃料已计入本企业','L':'来源说明（选填）'}

def cell(col,row,value,style=47):
 return f'<c r="{col}{row}" s="{style}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'

def generated_bytes():
 raw=SOURCE.read_bytes()
 if sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('原v9身份不匹配')
 out=BytesIO()
 with ZipFile(BytesIO(raw)) as source,ZipFile(out,'w') as target:
  for info in source.infolist():
   content=source.read(info.filename)
   if info.filename=='xl/worksheets/sheet9.xml':
    text=content.decode().replace('A1:G7','A1:L7').replace('A1:G1','A1:L1')
    for row in (5,6,7):text=text.replace(f'A{row}:G{row}',f'A{row}:L{row}')
    text=text.replace('</cols>','<col width="20" customWidth="1" min="8" max="9"/><col width="28" customWidth="1" min="10" max="12"/></cols>')
    def update(match):
     n=int(match[1]);part=match[0]
     if n==2:extra=''.join(cell(c,n,label,16) for c,label in HEADERS.items())
     elif n in (3,4):
      for c in ('F','G'):part=re.sub(fr'<c r="{c}{n}".*?</c>',cell(c,n,''),part,flags=re.S)
      extra=''.join(cell(c,n,'') for c in HEADERS)
     elif n==6:
      part=re.sub(r'<c r="A6".*?</c>',cell('A',6,NOTE,15),part,flags=re.S).replace('ht="27"','ht="84"');extra=''
     elif n==7:
      part=re.sub(r'<c r="A7".*?</c>',cell('A',7,'使用提示：仅支持饱和蒸汽、过热蒸汽。Excel只收集输入并预览，正式核算及记录由软件统一生成。',15),part,flags=re.S);extra=''
     else:extra=''
     return part.replace('</row>',extra+'</row>')
    text=re.sub(r'<row r="(\d+)"[^>]*>.*?</row>',update,text,flags=re.S)
    validation=''.join(f'<dataValidation sqref="{c}3:{c}4" allowBlank="1" showErrorMessage="1" errorStyle="stop" type="list"><formula1>"{values}"</formula1></dataValidation>' for c,values in [('B','饱和蒸汽,过热蒸汽'),('H','已知焓,自动物性'),('I','缺省值,实测值'),('J','边界外,边界内,待核实'),('K','已计入,未计入,待核实')])
    text=re.sub(r'<dataValidations.*?</dataValidations>',f'<dataValidations count="5">{validation}</dataValidations>',text,flags=re.S)
    text=re.sub(r'<conditionalFormatting.*?</conditionalFormatting>','',text,flags=re.S)
    content=text.encode()
   target.writestr(info,content)
 return out.getvalue()

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
 content=generated_bytes()
 if args.write:TARGET.write_bytes(content)
 elif not TARGET.is_file() or TARGET.read_bytes()!=content:raise ValueError('v10机械投影不一致')
 print('v10 controlled projection: PASS '+sha256(content).hexdigest())
