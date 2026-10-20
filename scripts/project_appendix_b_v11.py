"""ArtifactTool软件补充页机械附加；原v10九表XML不变，旧模板不改。"""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from xml.etree import ElementTree as E
import argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v10.xlsx'
TARGET=ROOT/'resources/excel_templates/gb_t_32151_34_2024_appendix_b_v11.xlsx'
SOURCE_SHA='705a9326f6910bceaad34ce955975a6150731fa8ed2b50ddfe8c2c5188deb729'
ASSET=ROOT/'data-source/carbon_accounting/templates/external_co2'
N='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
P='http://schemas.openxmlformats.org/package/2006/relationships'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
E.register_namespace('',N);E.register_namespace('r',R)
def q(name):return '{'+N+'}'+name

def import_authored(path):
    ASSET.mkdir(parents=True,exist_ok=True)
    with ZipFile(path) as z:
        sheet=E.fromstring(z.read('xl/worksheets/sheet1.xml'))
        strings=E.fromstring(z.read('xl/sharedStrings.xml')) if 'xl/sharedStrings.xml' in z.namelist() else []
        for c in sheet.iter(q('c')):
            if c.get('t')=='s':
                si=strings[int(c.find(q('v')).text)];c.remove(c.find(q('v')));c.set('t','inlineStr')
                inline=E.SubElement(c,q('is'))
                for node in si:inline.append(deepcopy(node))
        (ASSET/'sheet.xml').write_bytes(E.tostring(sheet,encoding='utf-8'))
        (ASSET/'styles.xml').write_bytes(z.read('xl/styles.xml'))

def generated_bytes():
    raw=SOURCE.read_bytes()
    if sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('v10母版身份不匹配')
    out=BytesIO()
    with ZipFile(BytesIO(raw)) as src,ZipFile(out,'w') as dst:
        styles=E.fromstring(src.read('xl/styles.xml'));extra=E.fromstring((ASSET/'styles.xml').read_bytes())
        offsets={}
        for group in ('fonts','fills','borders','cellXfs'):
            old=styles.find(q(group));new=extra.find(q(group));offsets[group]=len(old)
            for node in new:
                clone=deepcopy(node)
                if group=='cellXfs':
                    for attr,kind in [('fontId','fonts'),('fillId','fills'),('borderId','borders')]:clone.set(attr,str(int(clone.get(attr,'0'))+offsets[kind]))
                    if int(clone.get('numFmtId','0'))>=164:raise ValueError('未登记自定义数值格式')
                    clone.set('xfId','0')
                old.append(clone)
            old.set('count',str(len(old)))
        sheet=E.fromstring((ASSET/'sheet.xml').read_bytes())
        for c in sheet.iter(q('c')):c.set('s',str(int(c.get('s','0'))+offsets['cellXfs']))
        for info in src.infolist():
            data=src.read(info.filename)
            if info.filename=='xl/styles.xml':data=E.tostring(styles,encoding='utf-8')
            elif info.filename=='xl/workbook.xml':
                root=E.fromstring(data);E.SubElement(root.find(q('sheets')),q('sheet'),{'name':'软件补充','sheetId':'10','{'+R+'}id':'rIdExternalSupplement'})
                data=E.tostring(root,encoding='utf-8')
            elif info.filename=='xl/_rels/workbook.xml.rels':
                data=data.decode('utf-8').replace('</Relationships>', '<Relationship Id="rIdExternalSupplement" Type="'+R+'/worksheet" Target="/xl/worksheets/sheet10.xml"/></Relationships>').encode('utf-8')
            elif info.filename=='[Content_Types].xml':
                data=data.decode('utf-8').replace('</Types>', '<Override PartName="/xl/worksheets/sheet10.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>').encode('utf-8')
            dst.writestr(info,data)
        info=ZipInfo('xl/worksheets/sheet10.xml',(2026,10,20,0,0,0));info.compress_type=ZIP_DEFLATED
        dst.writestr(info,E.tostring(sheet,encoding='utf-8'))
    return out.getvalue()
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--import-authored',type=Path);p.add_argument('--write',action='store_true');a=p.parse_args()
    if a.import_authored:import_authored(a.import_authored)
    data=generated_bytes()
    if a.write:TARGET.write_bytes(data)
    elif not TARGET.exists() or TARGET.read_bytes()!=data:raise ValueError('v11机械投影不一致')
    print('v11 projection PASS '+sha256(data).hexdigest())
