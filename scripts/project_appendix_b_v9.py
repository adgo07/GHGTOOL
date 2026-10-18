"""机械生成P04A监测分段v9；仅改v8的B.6，旧模板原字节保留。"""
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import argparse, re
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v8.xlsx'
TARGET=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v9.xlsx'
SOURCE_SHA='a8ee7272ee4ac3665997f7ce93f78e8fd78c58cb4215ee477c01b76b6f87dff4'
NOTE='数据提示：烟气分段输入规则 V9（2.7.0）。每行对应真实源实例/同计量边界的一个监测段；同实例同边界复用同编号，不同真实实例用不同编号；段编号唯一。K/L以文字填写真实起止时间（年-月-日 时:分:秒，终点不含），M选d或h，F为本段时长且与区间精确一致。Q与QVar及参数只属于本段。报告期独立，不回填段时长；缺口只形成已覆盖合计，不补零、不年化。结果列G不填写，新增行位于本提示上方。'
HEADERS={'H':'排放源编号','I':'计量边界编号','J':'监测段编号','K':'监测开始（文字）','L':'监测结束（文字，不含终点）','M':'时长单位（d/h）'}
def cell(col,row,value,style=47):
 return f'<c r="{col}{row}" s="{style}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
def generated_bytes():
 raw=SOURCE.read_bytes()
 if sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('原v8身份不匹配')
 out=BytesIO()
 with ZipFile(BytesIO(raw)) as source, ZipFile(out,'w') as target:
  for info in source.infolist():
   content=source.read(info.filename)
   if info.filename=='xl/worksheets/sheet6.xml':
    text=content.decode().replace('A1:G8','A1:M8').replace('A1:G1','A1:M1').replace('A8:G8','A8:M8')
    text=text.replace('</cols>','<col width="22" customWidth="1" min="8" max="10"/><col width="28" customWidth="1" min="11" max="12"/><col width="18" customWidth="1" min="13" max="13"/></cols>')
    text=re.sub(r'<c r="F2".*?</c>',cell('F',2,'监测段时长\n（单位见M列）',3),text,flags=re.S)
    def row(match):
     n=int(match[1]);part=match[0]
     if n==2:extra=''.join(cell(c,n,label,16) for c,label in HEADERS.items())
     elif 3<=n<=7:extra=''.join(cell(c,n,'') for c in HEADERS)
     elif n==8:
      part=re.sub(r'<c r="A8".*?</c>',cell('A',8,NOTE,15),part,flags=re.S).replace('ht="28"','ht="72"');extra=''
     else:extra=''
     return part.replace('</row>',extra+'</row>')
    text=re.sub(r'<row r="(\d+)"[^>]*>.*?</row>',row,text,flags=re.S)
    text=text.replace('<pageMargins','<dataValidations count="1"><dataValidation sqref="M3:M7" allowBlank="0" showErrorMessage="1" errorStyle="stop" type="list"><formula1>"d,h"</formula1></dataValidation></dataValidations><pageMargins')
    content=text.encode()
   target.writestr(info,content)
 return out.getvalue()
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
 content=generated_bytes()
 if args.write:TARGET.write_bytes(content)
 elif not TARGET.is_file() or TARGET.read_bytes()!=content:raise ValueError('v9机械投影不一致')
 print('v9 controlled projection: PASS '+sha256(content).hexdigest())
