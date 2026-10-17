"""机械生成F02来源文案修订v7；保留原v6及其他OOXML部件原字节。"""
from __future__ import annotations
from hashlib import sha256
from html import unescape,escape
from io import BytesIO
from pathlib import Path
import argparse,re
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v6.xlsx'
TARGET=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v7.xlsx'
SOURCE_SHA='ca61cf3133c2663c78ca7409d23f7dd20726e43a8c79adca2aa78faecb3c031a'
NOTE='材料输入规则 V7（2.5.0）：来源仅实测值/计算值，方法另填。空基准为收到基，空含量单位为%。干基须填实际收到基水分和方法；质量/含量分别只换算一次，无数值默认。同物料两行的基准、水分、方法须一致。'
def generated_bytes():
 raw=SOURCE.read_bytes()
 if sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('原v6身份不匹配')
 out=BytesIO()
 with ZipFile(BytesIO(raw)) as source,ZipFile(out,'w') as target:
  for info in source.infolist():
   content=source.read(info.filename)
   if info.filename in ('xl/worksheets/sheet3.xml','xl/worksheets/sheet4.xml','xl/worksheets/sheet5.xml'):
    text=content.decode('utf-8');count=0
    def source_label(match):
     nonlocal count
     if unescape(match[1])=='"实测值,收到基换算"':
      count+=1;return '<formula1>"实测值,计算值"</formula1>'
     return match[0]
    text=re.sub(r'<formula1>(.*?)</formula1>',source_label,text)
    if count!=1:raise ValueError('预期恰好一个材料来源下拉')
    count=0
    def note(match):
     nonlocal count
     if unescape(match[2]).startswith('材料输入规则 V6：'):
      count+=1;return match[1]+escape(NOTE)+match[3]
     return match[0]
    text=re.sub(r'(<t>)(.*?)(</t>)',note,text)
    if count!=1:raise ValueError('预期恰好一个原材料说明行')
    content=text.encode('utf-8')
   target.writestr(info,content)
 return out.getvalue()
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
 content=generated_bytes()
 if args.write:TARGET.write_bytes(content)
 elif not TARGET.is_file() or TARGET.read_bytes()!=content:raise ValueError('v7与机械生成结果不一致')
 print('v7 controlled projection: PASS '+sha256(content).hexdigest())
