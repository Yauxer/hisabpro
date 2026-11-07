"""072 — conversion BL → facture visible sans F5 ; brouillon sans « Facture null »."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMERCIAL = (ROOT / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
FACTURES = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')


def _bl():
    return COMMERCIAL.split('function OngletBonsLivraison({ annee }) {', 1)[1].split('function FormulaireReglementComplet', 1)[0]


def _conversion():
    return 'async function facturerBL() {' + _bl().split('async function facturerBL() {', 1)[1].split('  async function changerStatut(', 1)[0]


def test_072_contexte_partage_et_raffraichissement_apres_conversion():
    bl = _bl()
    assert "import { useFactures } from '../data/FacturesContext.jsx'" in COMMERCIAL
    assert 'const { recharger: rechargerFactures } = useFactures()' in bl
    conversion = _conversion()
    assert conversion.index('await apiFetch(') < conversion.index('await rechargerFactures()') < conversion.index('await charger()')
    assert 'window.location.reload' not in conversion
    assert 'navigate(' not in conversion
    # Ne pas modifier les autres créations ni les règles de conversion côté API.
    assert 'POST' in conversion and 'convertir-facture' in conversion


@pytest.mark.parametrize('echec', [False, True])
def test_072_conversion_bl_avec_api_simulee_et_erreur_sans_fausse_maj(echec):
    if not shutil.which('node'):
        pytest.skip('Node.js absent')
    js = r'''
const assert = require('node:assert/strict');
const source = JSON.parse(process.argv[1]);
const echec = process.argv[2] === 'true';
const calls = [];
const make = new Function(
  'blAFacturer', 'reliquatFacturation', 'qtesFacturees', 'setFacturation',
  'apiFetch', 'notifier', 'setBlAFacturer', 'setReliquatFacturation',
  'setQtesFacturees', 'rechargerFactures', 'charger', 'dateFactureBL',
  source + '\nreturn facturerBL;'
);
const facturerBL = make(
  { id: 12, numero: 'BL-2026-001' },
  { lignes: [{ ligne_bl_id: 15, reste_a_facturer: 2 }] },
  { '15': '2' },
  value => calls.push(['loading', value]),
  async (url, opts) => {
    calls.push(['api', url, opts.method, JSON.parse(opts.body).lignes]);
    // Date de facturation choisie par l'utilisateur, transmise à l'API.
    assert.equal(JSON.parse(opts.body).date, '2026-09-20');
    if (echec) throw new Error('Erreur API');
    return { id: 73, numero: null };
  },
  Object.assign(msg => calls.push(['message', msg]), {
    erreur: msg => calls.push(['message', msg]), succes: msg => calls.push(['message', msg]) }),
  value => calls.push(['fermeture', value]),
  value => calls.push(['reliquat', value]),
  value => calls.push(['quantites', value]),
  async () => { calls.push(['factures_actualisees']); },
  async () => { calls.push(['bl_actualises']); },
  '2026-09-20',
);
(async () => {
  await facturerBL();
  const indexes = calls.map(call => call[0]);
  assert.equal(indexes[0], 'loading');
  assert.deepEqual(calls[1], ['api', '/api/bons-livraison/12/convertir-facture', 'POST', [{ ligne_bl_id: 15, quantite: 2 }]]);
  if (echec) {
    assert.equal(indexes.includes('factures_actualisees'), false);
    assert.equal(indexes.includes('bl_actualises'), false);
    assert(indexes.includes('message'));
    assert.equal(indexes.includes('fermeture'), false);
  } else {
    assert(indexes.indexOf('factures_actualisees') > indexes.indexOf('api'));
    assert(indexes.indexOf('bl_actualises') > indexes.indexOf('factures_actualisees'));
    assert(indexes.indexOf('fermeture') > indexes.indexOf('api'));
    assert(calls.find(call => call[0] === 'message')[1].includes('Brouillon de facture #73'));
  }
  assert.deepEqual(calls.at(-1), ['loading', null]);
  console.log('OK : ' + (echec ? 'échec API sans fausse actualisation' : 'actualisation BL + factures après création'));
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
    proc = subprocess.run(
        ['node', '-e', js, json.dumps(_conversion()), str(echec).lower()],
        cwd=ROOT, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert 'OK :' in proc.stdout


def test_072_brouillon_dans_fiche_et_chaine_documentaire():
    detail = FACTURES.split('function DetailFacture(', 1)[1].split('// ─── Formulaire édition facture', 1)[0]
    assert 'titre={facture.numero ? `Facture ${facture.numero}` : `Brouillon #${facture.id}`}' in detail
    assert '{facture.numero || `Brouillon #${facture.id}`} ← ici' in detail
    assert 'Facture ${facture.numero}`}' not in detail
    # Ne pas attribuer de numéro définitif côté interface.
    creation = FACTURES.split('async function handleSubmit', 1)[-1]
    assert 'numero: estProforma ? numero : null' in creation


def test_072_conversions_bc_et_bl_reprennent_delai_tiers_sans_changer_numerotation():
    import ast
    from types import SimpleNamespace
    from datetime import date, timedelta

    path = ROOT / 'hisabpro-backend/routers/commercial.py'
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_delai_paiement_tiers')
    ctx = {}
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(path), 'exec'), ctx)
    delai = ctx['_delai_paiement_tiers']
    for valeur, attendu in [(30, 30), (0, 0), (None, 60)]:
        tiers = SimpleNamespace(delai_paiement=valeur)
        assert delai(tiers) == attendu
        assert date(2026, 9, 20) + timedelta(days=delai(tiers)) == date(2026, 9, 20) + timedelta(days=attendu)
    assert delai(None) == 60
    for marqueur in ('@router_bc.post("/{bc_id}/convertir-facture"', '@router_bl.post("/{bl_id}/convertir-facture"'):
        segment = source.split(marqueur, 1)[1].split('    db.add(facture); db.flush()', 1)[0]
        assert 'delai_paiement=_delai_paiement_tiers(tiers_obj)' in segment
        assert 'date_facture + timedelta(days=_delai_paiement_tiers(tiers_obj))' in segment
        assert 'numero_f = None' in segment  # le brouillon ne reçoit pas de numéro final
        assert 'societe_id=' in segment and 'tiers_obj = _resoudre_tiers(' in segment
