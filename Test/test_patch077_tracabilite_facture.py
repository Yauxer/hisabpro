"""077 — une réception n'est pas une livraison ; chaînage BC → BR → facture."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import pytest
from jsx_syntax import assert_jsx

ROOT = Path(__file__).resolve().parents[1]
FACTURES = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
BACKEND = (ROOT / 'hisabpro-backend/routers/commercial.py').read_text(encoding='utf-8')


def _helper_source():
    match = re.search(r'function construireTracabiliteFacture\(facture, bcs, bls, brs\) \{.*?\n\}', FACTURES, re.S)
    assert match, 'Fonction de traçabilité introuvable'
    return match.group()


def test_077_cause_doublon_br_partage_table_livraisons():
    assert 'router_br = APIRouter(prefix="/api/bons-reception"' in BACKEND
    assert '.filter_by(societe_id=current_user["societe_id"], type="achat")' in BACKEND
    # L'API générique bons-livraison retourne les deux types en l'absence de filtre.
    assert 'if type:   q = q.filter(models.BonLivraison.type == type)' in BACKEND
    assert "bl.type === 'vente'" in _helper_source()
    assert "br.type === 'achat'" in _helper_source()


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js absent')
def test_077_tracabilite_runtime_achat_vente_et_bc_indirect():
    js = r'''
const assert = require('node:assert/strict');
const helper = new Function(JSON.parse(process.argv[1])+'\nreturn construireTracabiliteFacture;')();
const bc = { id: 19, numero:'BC-2026-002', facture_id:null };
const br = { id: 42, type:'achat', numero:'BR-2026-001', facture_id:76, bon_commande_id:19, statut:'livre' };
const saleBl = { id: 7, type:'vente', numero:'BL-2026-001', facture_id:23, bon_commande_id:6, statut:'livre' };
const dataA = helper({id:76,type:'achat'},[bc],[br,saleBl],[br]);
assert.equal(dataA.bc.numero,'BC-2026-002');
assert.equal(dataA.bls.length,0,'Un BR ne doit jamais apparaître comme BL');
assert.deepEqual(dataA.brs.map(r => r.numero),['BR-2026-001']);
const dataV = helper({id:23,type:'vente'},[{id:6,numero:'BC-2026-001'}],[saleBl,br],[br]);
assert.equal(dataV.bc.numero,'BC-2026-001');
assert.deepEqual(dataV.bls.map(b => b.numero),['BL-2026-001']);
assert.equal(dataV.brs.length,0);
const direct = helper({id:99,type:'achat'},[{id:19,numero:'BC-2026-002',facture_id:99}],[br],[br]);
assert.equal(direct.brs.length,1,'Facturation directe du BC : BR lié conservé');
assert.equal(direct.bls.length,0);
const vide = helper({id:555,type:'achat'},[],[br],[br]);
assert.equal(vide.bc,null);
assert.equal(vide.bls.length,0);
assert.equal(vide.brs.length,0);
console.log('OK BR unique, BC indirect, vente BL et absence de fausses liaisons');
'''
    proc = subprocess.run(['node', '-e', js, json.dumps(_helper_source())], capture_output=True, text=True, timeout=15, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    assert 'OK BR unique' in proc.stdout


def test_077_affichage_ordre_document_commercial_et_reference_achat():
    detail = FACTURES.split('function DetailFacture(', 1)[1].split('// ─── Formulaire édition facture', 1)[0]
    docs = detail.split('{/* Traçabilité — documents liés */}',1)[1].split('{/* 066 :',1)[0]
    assert docs.index('tracabilite.bc.numero') < docs.index('tracabilite.brs.map')
    assert docs.index('tracabilite.brs.map') < docs.index('← ici')
    assert 'N° fournisseur' in detail
    assert 'À renseigner avant validation' in detail
    assert 'facture.est_validee' in detail
    # Ne pas substituer la référence de la commande au numéro du fournisseur.
    assert 'setTracabilite(construireTracabiliteFacture(facture, bcs, bls, brs))' in detail


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js absent')
def test_077_jsx_syntaxe():
    assert_jsx(['src/pages/Factures.jsx'])
