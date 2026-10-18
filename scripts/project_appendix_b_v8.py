"""机械生成脱硫显式来源v8；仅改v7的B.7部件，保留全部旧模板原字节。"""
from __future__ import annotations
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import argparse,re
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v7.xlsx'
TARGET=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v8.xlsx'
SOURCE_SHA='e4203f0d5bf9133df5b6abde3bfede8b82905d11d795cd29ba590ea60f7ebb5a'
NOTE='数据提示：脱硫输入规则 V8（2.6.0）。K/L明确选择含量/转化率来源，实测须填D/F，空白不采用缺省。单批单有效组分才允许含量缺省；多组分逐项实测。同批整剂净耗量只计一次，组分含量不归一。J仅为EF来源，精确C.2用缺省，否则实测填写H。M可填企业设施编号，同编号批次归属同设施，批次仍独立。'
def cell(column,row,value,style=47):
 return f'<c r="{column}{row}" s="{style}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
def generated_bytes():
 raw=SOURCE.read_bytes()
 if sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('原v7身份不匹配')
 out=BytesIO()
 with ZipFile(BytesIO(raw)) as source,ZipFile(out,'w') as target:
  for info in source.infolist():
   content=source.read(info.filename)
   if info.filename=='xl/worksheets/sheet7.xml':
    text=content.decode('utf-8')
    text=text.replace('ref="A1:J9"','ref="A1:M9"').replace('ref="A1:J1"','ref="A1:M1"').replace('ref="A9:I9"','ref="A9:M9"')
    text=text.replace('</cols>','<col width="18" customWidth="1" min="11" max="12"/><col width="22" customWidth="1" min="13" max="13"/></cols>')
    def add_cells(match):
     row=int(match[1]);part=match[0]
     if row==2: extra=cell('K',row,'含量来源',16)+cell('L',row,'转化率来源',16)+cell('M',row,'设施编号（选填）',16)
     elif 3<=row<=8:extra=cell('K',row,'')+cell('L',row,'')+cell('M',row,'')
     elif row==9:
      part=re.sub(r'(<c r="A9"[^>]*><is><t>).*?(</t></is></c>)',lambda m:m[1]+escape(NOTE)+m[2],part,flags=re.S)
      part=part.replace('ht="54"','ht="90"');extra=''
     else:extra=''
     return part.replace('</row>',extra+'</row>')
    text=re.sub(r'<row r="(\d+)"[^>]*>.*?</row>',add_cells,text,flags=re.S)
    validation=''.join(f'<dataValidation sqref="{c}3:{c}8" allowBlank="0" showErrorMessage="1" errorStyle="stop" type="list"><formula1>"缺省值,实测值"</formula1></dataValidation>' for c in ('K','L'))
    text=text.replace('<dataValidations count="2">','<dataValidations count="4">').replace('</dataValidations>',validation+'</dataValidations>')
    content=text.encode('utf-8')
   target.writestr(info,content)
 return out.getvalue()
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
 content=generated_bytes()
 if args.write:TARGET.write_bytes(content)
 elif not TARGET.is_file() or TARGET.read_bytes()!=content:raise ValueError('v8与机械生成结果不一致')
 print('v8 controlled projection: PASS '+sha256(content).hexdigest())
