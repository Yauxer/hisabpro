"""073 — édition : rafraîchissement immédiat et détail lié aux données à jour."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')


def _edition():
    return SOURCE.split('function FormulaireEditionFacture(', 1)[1].split('function ModalEncaissementRapide(', 1)[0]


def _handle_save():
    section = _edition()
    return 'async function handleSave() {' + section.split('  async function handleSave() {', 1)[1].split('\n  return (\n    <Modal titre={`Modifier', 1)[0]


def test_073_edition_actualise_apres_sauvegarde_et_avant_fermeture():
    edition = _edition()
    handler = _handle_save()
    assert handler.index('if (!res.ok)') < handler.index('await onSuccess?.()') < handler.index('onFermer()')
    assert 'onSuccess={async () => { await recharger(); setFactureEdit(null) }}' in SOURCE
    assert 'onSuccess={() => setFactureEdit(null)}' not in SOURCE
    assert 'window.location.reload' not in handler
    assert "method: 'PATCH'" in handler
    assert "`${API_BASE}/api/factures/${facture.id}`" in handler
    # La validation et l'édition restent deux parcours distincts.
    assert 'await recharger()' in SOURCE.split('const validation = await validerFacture(f.id)', 1)[1].split('} catch (err)', 1)[0]


def test_073_fiche_affiche_le_dernier_etat_du_contexte():
    assert 'facture={factures.find(f => f.id === factureOuv.id) || factureOuv}' in SOURCE
    assert 'facture={factureOuv}\n' not in SOURCE
    assert 'onClick={() => setFactureOuv(factureOuv?.id === f.id ? null : f)}' in SOURCE
    # La fenêtre tient compte de la date, des montants et du numéro du dernier rechargement.
    detail = SOURCE.split('function DetailFacture(', 1)[1].split('// ─── Formulaire édition facture', 1)[0]
    for key in ('facture.numero', 'facture.total_ttc', 'facture.est_comptabilisee'):
        assert key in detail
    # L'échéance est rendue par BadgeEcheance à partir de la même facture à jour.
    assert '<BadgeEcheance facture={facture} />' in detail
    echeances = (ROOT / 'src/utils/echeancesFactures.js').read_text(encoding='utf-8')
    assert 'if (facture.date_echeance) return facture.date_echeance' in echeances


@pytest.mark.parametrize('scenario', ['succes', 'erreur_patch', 'attente_actualisation'])
def test_073_sauvegarde_simulee_et_ordre_des_evenements(scenario):
    if not shutil.which('node'):
        pytest.skip('Node.js absent')
    script = r'''
const assert = require('node:assert/strict');
const body = JSON.parse(process.argv[1]);
const scenario = process.argv[2];
const events = [];
let resolveReload;
const deps = {
  tiers: 'CLIENT RECETTE ALPHA', date: '2026-09-20', tiersId: 14,
  reference: 'BL-2026-001', delaiPaiement: 30, dateEcheanceEdit: '2026-10-20',
  modeReglementPrevu: '', referenceReglementPrevue: '', verrouille: true,
  rasTaux: 10, rasInitialInvalide: false, rasChoisi: false,
  // État React de la qualification achat, même pour une vente verrouillée.
  tvaDeductiblePctEdit: '', natureTVAAchatEdit: '', qualificationAchatChoisie: false,
  facture: { id: 73, type: 'vente' }, API_BASE: 'http://localhost:8000',
  localStorage: { getItem: () => 'jeton-test' },
  entierOuDefaut: (v, d) => v === '' ? d : Number(v),
  setLoading: v => events.push(['chargement', v]),
  setErreur: v => events.push(['erreur', v]),
  fetch: async (url, opts) => {
    events.push(['patch', url, opts.method, JSON.parse(opts.body)]);
    assert.equal(opts.headers.Authorization, 'Bearer jeton-test');
    return scenario === 'erreur_patch'
      ? { ok: false, json: async () => ({ detail: 'Refus du serveur' }) }
      : { ok: true };
  },
  onSuccess: async () => {
    events.push(['debut_rechargement']);
    if (scenario === 'attente_actualisation') await new Promise(resolve => { resolveReload = resolve });
    events.push(['fin_rechargement']);
  },
  onFermer: () => events.push(['fermeture']),
};
const save = new Function('deps', `with (deps) { ${body}; return handleSave; }`)(deps);
(async () => {
  const pending = save();
  if (scenario === 'attente_actualisation') {
    for (let i = 0; i < 8 && !resolveReload; i++) await Promise.resolve();
    assert.equal(typeof resolveReload, 'function');
    assert(!events.some(e => e[0] === 'fermeture'));
    resolveReload();
  }
  await pending;
  const actions = events.map(e => e[0]);
  assert.equal(events[0][0], 'chargement');
  assert.equal(events[0][1], true);
  if (scenario === 'erreur_patch') {
    assert(!actions.includes('debut_rechargement'));
    assert(!actions.includes('fermeture'));
    assert(events.some(e => e[0] === 'erreur' && e[1] === 'Refus du serveur'));
  } else {
    assert(actions.indexOf('patch') < actions.indexOf('debut_rechargement'));
    assert(actions.indexOf('debut_rechargement') < actions.indexOf('fin_rechargement'));
    assert(actions.indexOf('fin_rechargement') < actions.indexOf('fermeture'));
    const payload = events.find(e => e[0] === 'patch')[3];
    assert.equal(payload.delai_paiement, 30);
    assert.equal(payload.date_echeance, '2026-10-20');
    assert.equal(Object.hasOwn(payload, 'ras_taux'), false, 'Ne pas réécrire la RAS d’une pièce validée');
  }
  assert.deepEqual(events.at(-1), ['chargement', false]);
  console.log('OK ' + scenario);
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
    run = subprocess.run(
        ['node', '-e', script, json.dumps(_handle_save()), scenario],
        cwd=ROOT, capture_output=True, text=True, timeout=15,
    )
    assert run.returncode == 0, run.stderr
    assert f'OK {scenario}' in run.stdout
