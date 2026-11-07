"""Exécute le vrai export JS et lit les octets du Blob, sans API simulée."""
import base64
import csv
import io
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE = r"""
import { exporterCSV } from './src/services/exportCSV.js';
const cas=JSON.parse(process.argv[1]);
const specials={nan:NaN,inf:Infinity,moins_inf:-Infinity,absent:undefined};
const valeur=cas.special ? specials[cas.special] : cas.valeur;
let blob,lien,clicked=false,revoked;
let attache=false;
globalThis.document={body:{appendChild(a){attache=a===lien;}},createElement(tag){if(tag!=='a')throw Error(tag);lien={style:{},remove(){},click(){clicked=attache;}};return lien;}};
globalThis.setTimeout=f=>f();  // révocation différée exécutée immédiatement dans le test
URL.createObjectURL=v=>{blob=v;return 'blob:export-test';};
URL.revokeObjectURL=v=>{revoked=v;};
exporterCSV('recette', [{label:cas.label || 'Valeur',get:r=>r.valeur,type:cas.type},
    {label:'Témoin',get:()=>'CONST'}], [{valeur}]);
console.log(JSON.stringify({csv:Buffer.from(await blob.arrayBuffer()).toString('base64'),
    nom:lien.download,clicked,revoked,type:blob.type}));
"""


def exporter(cas):
    if not shutil.which('node'):
        pytest.skip('Node.js absent')
    r = subprocess.run(['node','--input-type=module','-e',CODE,json.dumps(cas)],
        cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=15)
    assert r.returncode == 0,r.stderr
    data=json.loads(r.stdout)
    contenu=base64.b64decode(data['csv'])
    assert contenu.startswith(b'\xef\xbb\xbf')
    assert data['nom']=='recette.csv' and data['clicked']
    assert data['revoked']=='blob:export-test' and data['type']=='text/csv;charset=utf-8;'
    rows=list(csv.reader(io.StringIO(contenu.decode('utf-8-sig'),newline=''),delimiter=';',strict=True))
    assert len(rows)==2 and all(len(row)==2 for row in rows),rows
    assert rows[0][1]=='Témoin' and rows[1][1]=='CONST'
    return [[row[0]] for row in rows]


@pytest.mark.parametrize('cas',[
    {'special':'nan'},{'special':'inf'},{'special':'moins_inf'},
    *({'valeur':v} for v in ['NaN','Infinity','-Infinity','12abc','1,5','','  ',
                              True,False,[],[12],{},'0x10','1e999','=1+1']),
])
def test_montant_invalide_ne_devient_pas_un_nombre_ou_une_formule(cas):
    assert exporter({**cas,'type':'nombre'})[1]==['À vérifier']


@pytest.mark.parametrize('valeur,attendu',[
    (120.25,'120,25'),(-120.5,'-120,50'),(0,'0,00'),
    (' 120.25 ','120,25'),('+.5','0,50'),('1e2','100,00'),(1.005,'1,00'),
])
def test_montants_finis_format_fr_et_arrondi_existant_preserves(valeur,attendu):
    assert exporter({'type':'nombre','valeur':valeur})[1]==[attendu]


@pytest.mark.parametrize('valeur',[
    '=1+1','+SUM(1;2)','-1+1','@SUM(1)',' \t=1+1','\n=1+1','\r=1+1',
])
def test_texte_potentiellement_interprete_comme_formule_exporte_en_texte(valeur):
    assert exporter({'valeur':valeur})[1]==["'"+valeur]


@pytest.mark.parametrize('valeur',['Texte\rAutre ligne','Texte\nAutre ligne',
    'Écriture "précise"; transport','normal','01234','Client - Casablanca'])
def test_texte_et_separateurs_restitues_integralement(valeur):
    assert exporter({'valeur':valeur})[1]==[valeur]


@pytest.mark.parametrize('cas',[{'valeur':None},{'special':'absent'}])
def test_source_absente_reste_vide(cas):
    assert exporter(cas)[1]==['']


def test_entete_texte_protege_aussi():
    assert exporter({'valeur':'normal','label':'=1+1'})[0]==["'=1+1"]
