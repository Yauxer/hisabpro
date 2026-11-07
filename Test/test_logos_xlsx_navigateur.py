"""Module JS de production exécuté par Node ; vrai XLSX relu avec openpyxl."""
from io import BytesIO
import json, subprocess
from pathlib import Path
from zipfile import ZipFile
import pytest
from openpyxl import load_workbook
from test_logo_societe import image_data

ROOT=Path(__file__).resolve().parents[1]
SCRIPT="""
import XLSX from 'xlsx';import {readFileSync,writeFileSync} from 'node:fs';
import {construireXlsxAvecLogo} from './src/services/exportXlsxLogo.js';
const p=JSON.parse(readFileSync(0,'utf8')), wb=XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet([['Compte','Montant'],['001234',1234.56],['=FICTIF',-10.01]]),'Balance');
wb.Sheets.Balance.B2.z='#,##0.00';
const avant=JSON.stringify(wb);const data=construireXlsxAvecLogo(XLSX,wb,p);
if(JSON.stringify(wb)!==avant) throw Error('Le classeur source a été modifié');
writeFileSync(process.argv[1],Buffer.from(data));
"""


@pytest.mark.parametrize('logo',['PNG','JPEG',None,'https://example.com/logo.png','C:/secret.png','data:image/png;base64,aW52YWxpZA=='])
def test_classeur_reel_image_cellules_types_et_source_preserves(tmp_path,logo):
    present=logo in ('PNG','JPEG')
    payload={'raison_sociale':'=SOCIETE FICTIVE <SARL> & associés','logo_url':image_data(logo) if present else logo}
    path=tmp_path/'logo.xlsx'
    r=subprocess.run(['node','--input-type=module','-e',SCRIPT,str(path)],cwd=ROOT,
        input=json.dumps(payload),text=True,encoding='utf-8',capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr
    w=load_workbook(path)
    assert w['Balance']['A2'].value=='001234' and w['Balance']['A2'].data_type=='s'
    assert w['Balance']['B2'].value==1234.56 and w['Balance']['B2'].number_format=='#,##0.00'
    assert w['Balance']['A3'].value=='=FICTIF' and w['Balance']['A3'].data_type=='s'
    assert w['Balance']['B3'].value==-10.01
    if present:
        assert w.sheetnames==['Logo société','Balance']
        assert len(w['Logo société']._images)==1
        assert w['Logo société']['A2'].value==payload['raison_sociale']
        assert w['Logo société']['A2'].data_type=='s'
    else:assert w.sheetnames==['Balance']
    with ZipFile(path) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.startswith('xl/media/')])==int(present)
