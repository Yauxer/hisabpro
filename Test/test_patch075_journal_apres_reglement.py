"""075 — synchronisation des factures et du journal après un règlement."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')


def _reglement_handler():
    section = SOURCE.split('function FormulaireReglementPartiel(', 1)[1].split('const MODES =', 1)[0]
    return 'async function handleSave() {' + section.split('  async function handleSave() {', 1)[1]


def test_075_reglement_attend_la_synchronisation_sans_dupliquer_la_requete():
    handler = _reglement_handler()
    assert handler.index("fetch(API_BASE + '/api/reglements'") < handler.index('if (!res.ok)')
    assert handler.index('if (!res.ok)') < handler.index('await onSuccess?.()') < handler.index('onFermer()')
    assert handler.count("fetch(API_BASE + '/api/reglements'") == 1
    assert 'window.location.reload' not in handler


def test_075_deux_parcours_reglement_actualisent_factures_et_journal():
    quick = SOURCE.split('{peutModifier && factureEncaisser && (', 1)[1].split('{peutModifier && blDateModal && (', 1)[0]
    detail = SOURCE.split('const panneauDroit = factureOuv', 1)[1].split('// Compte les factures en retard', 1)[0]
    modal = SOURCE.split('{factureOuv && (', 1)[1].split('<div className={styles.content}>', 1)[0]
    for section in (quick, detail, modal):
        success = section.split('={async () => {', 1)[1]
        assert 'await Promise.all([recharger(), ecrituresCtx?.recharger?.()])' in success
        assert success.index('await Promise.all(') < success.index('setFactureOuv(null)' if section != quick else 'setFactureEncaisser(null)')
    nested = SOURCE.split('{/* Formulaire règlement partiel */}', 1)[1].split('{peutModifier && showReglement ?', 1)[1].split('/>', 1)[0]
    assert 'onSuccess={async () =>' in nested
    assert 'await onStatutChange?.()' in nested


@pytest.mark.parametrize('scenario', ['succes', 'erreur_api', 'attente_rechargement'])
def test_075_parcours_reglement_simule(scenario):
    if not shutil.which('node'):
        pytest.skip('Node.js absent')
    script = r'''
const assert = require('node:assert/strict');
const body = JSON.parse(process.argv[1]);
const scenario = process.argv[2];
const events = [];
let unblock;
let apiCalls = 0;
const deps = {
  form: { montant: '1200', mode: 'virement', date: '2026-09-20', reference: '', banque: '' },
  solde: 2400,
  facture: { id: 73, tiers: 'CLIENT RECETTE ALPHA' },
  formatMAD: n => String(n),
  setLoading: v => events.push(v ? 'loading' : 'idle'),
  setErreur: v => events.push('erreur:' + v),
  localStorage: { getItem: () => 'jeton-test' },
  API_BASE: 'http://localhost:8000',
  fetch: async (url, opts) => {
    apiCalls++;
    events.push('api');
    assert.equal(url, 'http://localhost:8000/api/reglements');
    assert.equal(opts.method, 'POST');
    assert.equal(opts.headers.Authorization, 'Bearer jeton-test');
    const payload = JSON.parse(opts.body);
    assert.equal(payload.facture_id, 73);
    assert.equal(payload.montant, 1200);
    assert.equal(payload.mode, 'virement');
    assert.equal(payload.reference, null);
    assert.equal(payload.banque, null);
    return scenario === 'erreur_api'
      ? { ok: false, json: async () => ({ detail: 'Erreur serveur' }) }
      : { ok: true };
  },
  onSuccess: async () => {
    events.push('debut_actualisation');
    if (scenario === 'attente_rechargement') await new Promise(resolve => { unblock = resolve });
    events.push('fin_actualisation');
  },
  onFermer: () => events.push('fermeture'),
};
const save = new Function('deps', `with (deps) { ${body}; return handleSave; }`)(deps);
(async () => {
  const pending = save();
  if (scenario === 'attente_rechargement') {
    for (let i = 0; i < 10 && !unblock; i++) await Promise.resolve();
    assert.equal(typeof unblock, 'function');
    assert(!events.includes('fermeture'));
    unblock();
  }
  await pending;
  assert.equal(apiCalls, 1);
  if (scenario === 'erreur_api') {
    assert(!events.includes('debut_actualisation'));
    assert(!events.includes('fermeture'));
    assert(events.includes('erreur:Erreur serveur'));
  } else {
    assert(events.indexOf('api') < events.indexOf('debut_actualisation'));
    assert(events.indexOf('fin_actualisation') < events.indexOf('fermeture'));
  }
  assert.equal(events.at(-1), 'idle');
  console.log('OK ' + scenario);
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
    result = subprocess.run(
        ['node', '-e', script, json.dumps(_reglement_handler()), scenario],
        cwd=ROOT, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert f'OK {scenario}' in result.stdout
