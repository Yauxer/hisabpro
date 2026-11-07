"""Calcul JS réellement exécuté, invariants de HT et modèles source immuables."""
import json,subprocess
from pathlib import Path
import pytest
from test_modeles_montants import modele

ROOT=Path(__file__).resolve().parents[1]
SCRIPT="""
import {readFileSync} from 'node:fs';
import {recalculerTauxModele,montantLigneModele,calculerMontantsModele} from './src/utils/montantsModeles.js';
const p=JSON.parse(readFileSync(0,'utf8')),m=p.modele;
if(p.ancienNan)m.lignes.find(l=>l.est_tva).taux_tva=NaN;
const avant=JSON.stringify(m),r=recalculerTauxModele(m,p.base,p.invalide?NaN:p.taux);
if(JSON.stringify(m)!==avant)throw Error('Modèle source modifié');
console.log(JSON.stringify(r?r.modele.lignes.map(l=>montantLigneModele(r.modele,l,r.montants).toFixed(2)):null));
"""


@pytest.mark.parametrize('sens,ancien,base,taux,attendu',[
    ('vente',20,120,10,['110.00','10.00','100.00']),
    ('vente',10,110,0,['100.00','0.00','100.00']),
    ('vente',0,100,20,['120.00','20.00','100.00']),
    ('achat',20,100,10,['100.00','10.00','110.00']),
    ('achat',10,100,0,['100.00','0.00','100.00']),
    ('achat',0,100,20,['100.00','20.00','120.00']),
    ('vente',20,39.996,10,['36.66','3.33','33.33']),
    ('achat',20,33.33,10,['33.33','3.33','36.66']),
    ('vente',20,0,10,['0.00','0.00','0.00']),
])
def test_changement_conserve_ht(sens,ancien,base,taux,attendu):
    r=subprocess.run(['node','--input-type=module','-e',SCRIPT],cwd=ROOT,input=json.dumps({
        'modele':modele(sens,ancien),'base':base,'taux':taux}),text=True,encoding='utf-8',capture_output=True,timeout=15)
    assert r.returncode==0,r.stderr
    assert json.loads(r.stdout)==attendu


@pytest.mark.parametrize('extras',[{'invalide':True},{'taux':-1},{'taux':101},{'ancienNan':True},{'base':1e308,'taux':100}])
def test_taux_ou_resultats_invalides_refuses(extras):
    p={'modele':modele('vente'),'base':120,'taux':10,**extras}
    r=subprocess.run(['node','--input-type=module','-e',SCRIPT],cwd=ROOT,input=json.dumps(p),text=True,encoding='utf-8',capture_output=True,timeout=15)
    assert r.returncode==0,r.stderr
    assert json.loads(r.stdout) is None
