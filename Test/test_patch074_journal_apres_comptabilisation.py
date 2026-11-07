"""074 — synchronisation du journal après comptabilisation d'une facture validée."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
JOURNAL = (ROOT / 'src/pages/Journal.jsx').read_text(encoding='utf-8')


def _handler():
    return ('async function comptabiliserMaintenant(f) {' +
            SOURCE.split('  async function comptabiliserMaintenant(f) {', 1)[1]
                  .split('\n  const { annee } = useExercice()', 1)[0])


def test_074_facture_et_journal_partagent_le_contexte_des_ecritures():
    page = SOURCE.split('export default function Factures() {', 1)[1]
    action = _handler()
    assert 'const ecrituresCtx = useEcritures()' in page.split('async function comptabiliserMaintenant', 1)[0]
    assert action.index('await comptabiliserFacture(f.id)') < action.index('await ecrituresCtx.recharger()')
    assert action.index('await ecrituresCtx.recharger()') < action.index('await recharger()')
    assert 'ecrituresCtx?.recharger' in action
    assert 'const { ecritures,' in JOURNAL and ' = useEcritures()' in JOURNAL
    assert 'window.location.reload' not in action


@pytest.mark.parametrize('scenario', ['succes', 'erreur_api', 'annule', 'attente_journal'])
def test_074_flux_comptabilisation_simule(scenario):
    if not shutil.which('node'):
        pytest.skip('Node.js absent')
    script = r'''
const assert = require('node:assert/strict');
const body = JSON.parse(process.argv[1]);
const scenario = process.argv[2];
const events = [];
let resolveJournal;
const deps = {
  confirm: () => { events.push('confirmation'); return scenario !== 'annule'; },
  setComptaEnCours: id => events.push(id === null ? 'fin_chargement' : 'debut_chargement'),
  comptabiliserFacture: async id => {
    events.push('appel_api');
    assert.equal(id, 73);
    if (scenario === 'erreur_api') throw new Error('Erreur comptable');
    return { ecriture_id: 152 };
  },
  ecrituresCtx: {
    recharger: async () => {
      events.push('debut_journal');
      if (scenario === 'attente_journal') await new Promise(resolve => { resolveJournal = resolve });
      events.push('fin_journal');
    },
  },
  recharger: async () => events.push('refresh_factures'),
  alert: message => events.push('alerte:' + message),
  // 967 : les messages passent par notifier (information ou erreur).
  notifier: Object.assign(message => events.push('alerte:' + message), {
    erreur: message => events.push('alerte:' + message), succes: message => events.push('alerte:' + message) }),
};
const act = new Function('deps', `with (deps) { ${body}; return comptabiliserMaintenant; }`)(deps);
(async () => {
  const pending = act({ id: 73, numero: 'FA-2026-001' });
  if (scenario === 'attente_journal') {
    for (let i = 0; i < 8 && !resolveJournal; i++) await Promise.resolve();
    assert.equal(typeof resolveJournal, 'function');
    assert(!events.includes('refresh_factures'));
    assert(!events.includes('fin_chargement'));
    resolveJournal();
  }
  await pending;
  if (scenario === 'annule') {
    assert.deepEqual(events, ['confirmation']);
  } else if (scenario === 'erreur_api') {
    assert.deepEqual(events.slice(0, 3), ['confirmation', 'debut_chargement', 'appel_api']);
    assert(!events.includes('debut_journal'));
    assert(!events.includes('refresh_factures'));
    assert(events.some(x => x.includes('Erreur comptable')));
    assert.equal(events.at(-1), 'fin_chargement');
  } else {
    assert.deepEqual(events, ['confirmation', 'debut_chargement', 'appel_api',
      'debut_journal', 'fin_journal', 'refresh_factures', 'fin_chargement']);
    assert.equal(events.filter(x => x === 'appel_api').length, 1);
  }
  console.log('OK ' + scenario);
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
    result = subprocess.run(
        ['node', '-e', script, json.dumps(_handler()), scenario],
        cwd=ROOT, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert f'OK {scenario}' in result.stdout
