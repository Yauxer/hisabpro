"""Oracles chiffrés indépendants, module JavaScript réellement importé par Node."""
import json
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'src/utils/montantsModeles.js'
SCRIPT="""
import {readFileSync} from 'node:fs';
const {calculerMontantsModele,montantLigneModele}=await import(process.argv[1]);
const p=JSON.parse(readFileSync(0,'utf8'));
const montant=p.invalide==='nan'?NaN:p.invalide==='inf'?Infinity:p.invalide==='moins_inf'?-Infinity:p.montant;
if(p.taux_inf)p.modele.lignes.find(l=>l.est_tva).taux_tva=Infinity;
const source=p.source===null?null:p.modele.lignes[p.source];
const m=calculerMontantsModele(p.modele,source,montant);
console.log(JSON.stringify(m===null?null:p.modele.lignes.map(l=>[l.compte,montantLigneModele(p.modele,l,m).toFixed(2)])));
"""


def modele(sens,taux=20):
    if sens=='achat':
        lignes=[{'compte':'6111','est_principal':True},{'compte':'34552','est_tva':True,'taux_tva':taux},{'compte':'4411'}]
    elif sens=='vente':
        lignes=[{'compte':'3421','est_principal':True},{'compte':'4455','est_tva':True,'taux_tva':taux},{'compte':'7111'}]
    else:lignes=[{'compte':'5141','est_principal':True},{'compte':'1111'}]
    return {'lignes':lignes}


def executer(payload):
    node=shutil.which('node')
    if not node:pytest.skip('Node.js requis pour exécuter le module JavaScript réel.')
    r=subprocess.run([node,'--input-type=module','-e',SCRIPT,MODULE.as_uri()],
        input=json.dumps(payload),text=True,encoding='utf-8',capture_output=True,timeout=15)
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)


CAS=[
    ('achat',20,0,100,['100.00','20.00','120.00']),
    ('achat',20,1,20,['100.00','20.00','120.00']),
    ('achat',20,2,120,['100.00','20.00','120.00']),
    ('vente',20,0,120,['120.00','20.00','100.00']),
    ('vente',20,1,20,['120.00','20.00','100.00']),
    ('vente',20,2,100,['120.00','20.00','100.00']),
    ('achat',10,0,100,['100.00','10.00','110.00']),
    ('achat',10,1,10,['100.00','10.00','110.00']),
    ('achat',10,2,110,['100.00','10.00','110.00']),
    ('vente',10,0,110,['110.00','10.00','100.00']),
    ('vente',10,1,10,['110.00','10.00','100.00']),
    ('vente',10,2,100,['110.00','10.00','100.00']),
    ('achat',0,0,100,['100.00','0.00','100.00']),
    ('vente',0,0,100,['100.00','0.00','100.00']),
    ('achat',20,0,33.33,['33.33','6.67','40.00']),
    ('vente',20,0,40,['40.00','6.67','33.33']),
    ('vente',20,1,6.67,['40.02','6.67','33.35']),
    ('achat',20,2,0.01,['0.01','0.00','0.01']),
    ('capital',0,0,100,['100.00','100.00']),
    ('capital',0,1,100,['100.00','100.00']),
]


@pytest.mark.parametrize('sens,taux,source,montant,attendu',CAS)
def test_montants_par_ligne_de_saisie(sens,taux,source,montant,attendu):
    m=modele(sens,taux)
    result=executer({'modele':m,'source':source,'montant':montant})
    assert result==[[l['compte'],v] for l,v in zip(m['lignes'],attendu)]


@pytest.mark.parametrize('erreur',['nan','inf','moins_inf','source_absente','taux_inf','debordement'])
def test_montants_non_determinables_ne_produisent_pas_nan(erreur):
    payload={'modele':modele('vente'),'source':2,'montant':100,'invalide':erreur}
    if erreur=='source_absente':payload['source']=None
    if erreur=='taux_inf':payload['taux_inf']=True
    if erreur=='debordement':payload['montant']=1.7e308
    assert executer(payload) is None
