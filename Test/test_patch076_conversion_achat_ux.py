"""076 — origine du BC, numéro fournisseur, délai effectif et fiche avoir responsive."""
from pathlib import Path
import json
import re
import shutil
import subprocess

import pytest
from jsx_syntax import assert_jsx

ROOT = Path(__file__).resolve().parents[1]
COMMERCIAL = (ROOT / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
FACTURES = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
AVOIRS = (ROOT / 'src/pages/Avoirs.jsx').read_text(encoding='utf-8')
CSS = (ROOT / 'src/pages/Avoirs.module.css').read_text(encoding='utf-8')


def test_076_reference_fournisseur_ne_reprend_pas_le_bc_et_lien_source_preserve():
    conversion = COMMERCIAL.split('function confirmerFacture(bc) {', 1)[1].split("  // À l'ouverture", 1)[0]
    assert "reference: bc.type === 'achat' ? '' : bc.numero" in conversion
    assert 'source_document_numero: bc.numero' in conversion
    assert 'bc_id: bc.id' in conversion
    assert 'source_ligne_bc_id: l.id' in conversion
    assert 'setReference(initialData.type === \'achat\' && initialData.bc_id ? \'\' : (initialData.reference || \'\'))' in FACTURES
    assert 'Commande fournisseur d’origine' in FACTURES
    assert 'le numéro figurant sur la facture du fournisseur' in FACTURES
    # Le numéro réellement émis par le fournisseur reste obligatoire lors
    # d'une validation d'achat : pas de numéro fictif ou silencieux.
    assert "if (comptabiliser && type === 'achat' && !estProforma && !reference.trim())" in FACTURES


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js absent')
def test_076_conversion_bc_vente_et_achat_execution_reelle():
    source = 'function confirmerFacture(bc) {' + COMMERCIAL.split('function confirmerFacture(bc) {', 1)[1].split("  // À l'ouverture", 1)[0]
    js = r'''
const assert = require('node:assert/strict');
let captured = null;
const navigate = (path, options) => { captured = {path, data: options.state.nouvelleFacture}; };
const setBcAFacturer = () => {};
const f = new Function('navigate', 'setBcAFacturer', 'qualificationParDefautPourTaux', JSON.parse(process.argv[1]) + '\nreturn confirmerFacture;')(navigate, setBcAFacturer, () => 'taxable');
const bc = {id: 4, numero:'BC-2026-002', tiers:'FOURNISSEUR RECETTE BETA', tiers_id:18,
    lignes:[{id:12, description:'Prestation de conseil', quantite:1, prix_unitaire:500, tva:20, article_id:3}]};
f({...bc, type:'achat'});
assert.equal(captured.path, '/factures');
assert.equal(captured.data.reference, '');
assert.equal(captured.data.source_document_numero, 'BC-2026-002');
assert.equal(captured.data.bc_id, 4);
assert.equal(captured.data.lignes[0].source_ligne_bc_id, 12);
assert.equal(captured.data.lignes[0].prix_unitaire, 500);
f({...bc, type:'vente'});
assert.equal(captured.data.reference, 'BC-2026-002');
console.log('OK conversion achat sans fausse référence, vente et traçabilité BC');
'''
    result = subprocess.run(['node','-e',js,json.dumps(source)], cwd=ROOT, text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'OK conversion' in result.stdout


def test_076_delai_tiers_affiche_et_modifiable_sans_bloquer_utilisateur():
    body = FACTURES.split('function handleTiersSelect(tiersObj) {', 1)[1].split('  const totaux = useMemo', 1)[0]
    assert 'setDelaiPaiement(delai ?? 60)' in body
    assert 'setDelaiAuto(delai !== null && delai !== undefined)' in body
    champ = FACTURES.split('<label className={styles.label}>Délai de paiement</label>',1)[1].split('<label className={styles.label}>Échéance contractuelle</label>',1)[0]
    assert 'value={delaiEffectif}' in champ
    assert 'disabled={delaiAuto' not in champ
    assert 'setDelaiAuto(false)' in champ
    assert 'title="Reprendre le délai du tiers"' in champ
    assert 'setDelaiPaiement(delaiTiers)' in champ
    assert 'dateEcheanceContractuelle || null' in FACTURES


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js absent')
def test_076_delai_selection_tiers_30_zero_sans_delai():
    match = re.search(r'  function handleTiersSelect\(tiersObj\) \{(?P<body>.*?)\n  \}', FACTURES, re.S)
    assert match
    js = r'''
const assert = require('node:assert/strict');
let result = {};
const setter = key => value => result[key] = value;
const handler = new Function('setTiersId','setTiersSelectionne','setDelaiTiers','setDelaiPaiement','setDelaiAuto','setRasTaux','setFieldErrors',
    'return function handleTiersSelect(tiersObj) {'+ JSON.parse(process.argv[1]) +'\n};')(
    setter('id'),setter('tiers'),setter('delaiTiers'),setter('champ'),setter('auto'),setter('ras'),()=>{});
handler({id:1,delai_paiement:30,taux_ras:0});
assert.equal(result.champ,30); assert.equal(result.delaiTiers,30); assert.equal(result.auto,true);
handler({id:2,delai_paiement:0});
assert.equal(result.champ,0); assert.equal(result.auto,true);
handler({id:3,delai_paiement:null});
assert.equal(result.champ,60); assert.equal(result.delaiTiers,null); assert.equal(result.auto,false);
console.log('OK délai tiers 30 / comptant 0 / absent 60');
'''
    result = subprocess.run(['node','-e',js,json.dumps(match.group('body'))], cwd=ROOT, text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'OK délai tiers' in result.stdout


def test_076_avoir_fiche_ouverte_sans_reduire_tableau_avec_mobile():
    assert 'className={styles.listeZone}' in AVOIRS
    assert '<Modal titre={`Avoir ${selectionne.numero}`}' in AVOIRS
    assert "flex: selectionne ? '1 1 60%'" not in AVOIRS
    assert 'detailModal' in CSS and 'grid-template-columns: repeat(2, minmax(0, 1fr))' in CSS
    assert '@media (max-width: 520px)' in CSS
    for label in ('N° Avoir', 'Total TTC', 'Facture d’origine', 'Comptabilité'):
        assert f'data-label="{label}"' in AVOIRS
    for action in ('comptabiliser(selectionne)', 'annuler(selectionne)', 'annulerUtilisation(selectionne, u)'):
        assert action in AVOIRS


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js absent')
def test_076_jsx_parse_tous_fichiers_modifies():
    assert_jsx(['src/pages/Commercial.jsx', 'src/pages/Factures.jsx', 'src/pages/Avoirs.jsx'])


def test_076_etats_facture_validation_paiement_comptabilisation_separes():
    detail = FACTURES.split('function DetailFacture(', 1)[1].split('// ─── Formulaire édition facture', 1)[0]
    assert '<span className={styles.metaLabel}>Validation</span>' in detail
    assert '<span className={styles.metaLabel}>Paiement</span>' in detail
    assert '<span className={styles.metaLabel}>Comptabilité</span>' in detail
    assert "facture.est_validee ? 'Validée' : 'Brouillon'" in detail
    assert "facture.est_comptabilisee ? 'Comptabilisée' : 'À comptabiliser'" in detail
    assert 'title="État de validation"' in FACTURES and 'title="État de paiement"' in FACTURES


def test_076_bc_avec_reception_oriente_vers_facturation_br():
    section = COMMERCIAL.split('async function ouvrirModaleFacture(bc) {', 1)[1].split('async function ouvrirModaleBL(', 1)[0]
    assert 'bc.type === \'achat\'' in section
    assert '/api/bons-reception?exercice=${annee}' in section
    assert 'Number(br.bon_commande_id) === Number(bc.id)' in section
    assert 'Ouvrez « Bons de réception »' in section
    assert 'setBcAFacturer(bc)' in section  # commandes sans BR : parcours direct conservé


def test_076_br_propose_facturer_depuis_reception_reellement_recuperee():
    section = COMMERCIAL.split('function OngletBonsReception({ annee, onOuvrirCommandes }) {', 1)[1].split('// ═════', 1)[0]
    assert "br.statut === 'livre'" in section
    assert 'ouvrirFacturationBR(br)' in section
    assert '/api/bons-livraison/${br.id}/reliquat-facturation' in section
    assert "reliquat.type !== 'achat'" in section
    assert 'Number(ligne.reste_a_facturer || 0) > 0' in section
    assert '/api/bons-livraison/${brAFacturer.id}/convertir-facture' in section
    assert 'method: \'POST\', body: JSON.stringify({ date: dateFactureBR, lignes })' in section
    assert 'setBrAFacturer(null); setReliquatBR(null); setQtesBR({})' in section
    assert 'Facture créée ; actualisez les listes' in section
    router = (ROOT / 'hisabpro-backend/routers/commercial.py').read_text(encoding='utf-8')
    assert 'source_ligne_bl_id=l.id' in router
    assert 'source_ligne_bc_id=(src_bc.id if src_bc else l.source_ligne_bc_id)' in router
    assert 'reference=(None if est_achat else bl.numero)' in router
    assert 'date_echeance=date_facture + timedelta(days=_delai_paiement_tiers(tiers_obj))' in router


@pytest.mark.skipif(not shutil.which('node'), reason='Node.js absent')
def test_076_protection_bc_avec_br_execution_simulee():
    section = COMMERCIAL.split('async function ouvrirModaleFacture(bc) {', 1)[1].split('  async function ouvrirModaleBL(', 1)[0]
    source = 'async function ouvrirModaleFacture(bc) {' + section
    js = r'''
const assert = require('node:assert/strict');
const calls = [];
let receptions = [{bon_commande_id:4,statut:'livre'}];
let failed = false;
const notifier = msg => calls.push(['message',msg]); notifier.erreur = notifier; notifier.succes = notifier;
const f = new Function('setBcAFacturer','apiFetch','notifier','annee',JSON.parse(process.argv[1])+'\nreturn ouvrirModaleFacture;')(
  v => calls.push(['open',v.id]), async url => {calls.push(['api',url]); if(failed) throw Error('réseau'); return receptions},
  notifier,2026);
const bc = {id:4,type:'achat',numero:'BC-2026-002'};
(async () => {
await f(bc);
assert(!calls.some(x=>x[0]==='open'));
assert(calls.some(x=>x[1]?.includes('Bons de réception')));
calls.length=0; receptions=[];
await f(bc);
assert.deepEqual(calls.at(-1),['open',4]);
calls.length=0; failed=true;
await f(bc);
assert(!calls.some(x=>x[0]==='open'));
assert(calls.some(x=>x[1]?.includes('réseau')));
calls.length=0;
await f({...bc,type:'vente'});
assert.deepEqual(calls.at(-1),['open',4]);
console.log('OK BC avec BR, sans BR, erreur réseau et vente');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result = subprocess.run(['node', '-e', js, json.dumps(source)], cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'OK BC avec BR' in result.stdout
