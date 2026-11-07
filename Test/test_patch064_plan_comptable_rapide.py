# -*- coding: utf-8 -*-
"""Patch 064 : rechargement instantané sans fuite inter-sociétés ni N+1 SQL."""
import ast
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_064_endpoint_plan_sans_n_plus_un_et_sans_reinitialisation_systematique():
    source = (ROOT / 'hisabpro-backend/routers/plan_comptable.py').read_text(encoding='utf-8')
    ast.parse(source)
    bloc = source.split('def lister_plan(', 1)[1].split('\n@router.post(', 1)[0]
    assert 'assurer_plan_societe(db, sid)' not in bloc
    assert 'db.commit()' not in bloc
    assert 'group_by(models.LigneEcriture.compte)' in bloc
    assert 'if inclure_inactifs and rows:' in bloc
    assert 'return [_out(db, sid, c, usages=usages) for c in rows]' in bloc
    assert 'db.commit()\n    return [_out(db, sid, c)' not in bloc


def test_064_layout_cache_prioritaire_mais_toujours_actualise_en_arriere_plan():
    layout = (ROOT / 'src/components/Layout.jsx').read_text(encoding='utf-8')
    assert 'useState(() => restaurerPlanSociete(getToken()))' in layout
    assert 'planComptableAPI.lister(true)' in layout
    assert 'enregistrerPlanSociete(rows, getToken(), societe.id)' in layout
    assert 'if (!enCache) setPlanClePrete(null)' in layout
    assert 'Première initialisation du plan comptable de cette société…' not in layout
    assert 'Plan comptable non actualisé' in layout
    assert 'cleCachePlan(getToken(), societe.id)' in layout
    plan_page = (ROOT / 'src/pages/PlanComptes.jsx').read_text(encoding='utf-8')
    assert 'enregistrerPlanSociete(rows, getToken())' in plan_page
    assert 'notifierPlanModifie(cle)' in plan_page
    api = (ROOT / 'src/services/api.js').read_text(encoding='utf-8')
    assert "cle?.startsWith('hisabpro_plan_societe_v1:')" in api


def test_064_cache_scope_actualisation_et_resilience_js():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js requis pour les tests du cache navigateur.')
    js = r'''
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { PLAN_COMPTES, trouverCompte } from './src/data/planComptes.js';
import {
  cleCachePlan, restaurerPlanSociete, enregistrerPlanSociete,
  notifierPlanModifie, EVENEMENT_PLAN_MODIFIE,
} from './src/data/planComptableCache.js';
const donnees = new Map();
const events = [];
globalThis.window = {
  sessionStorage: {
    getItem: key => donnees.get(key) ?? null,
    setItem: (key, value) => { donnees.set(key, value); },
    removeItem: key => { donnees.delete(key); },
  },
  dispatchEvent: ev => events.push(ev),
};
const token = (uid, societe) =>
  'entete.' + Buffer.from(JSON.stringify({sub:String(uid),societe_id:societe})).toString('base64url') + '.signature';
const a = token(7, 10), b = token(7, 11), c = token(8, 10);
assert.equal(cleCachePlan(a, 11), null, 'aucune restauration cross-company');
assert.equal(cleCachePlan(a, 10), 'hisabpro_plan_societe_v1:7:10');
assert.notEqual(cleCachePlan(a), cleCachePlan(b));
assert.notEqual(cleCachePlan(a), cleCachePlan(c));
assert.equal(restaurerPlanSociete(a, 10), null, 'première visite sans cache');
assert.equal(restaurerPlanSociete(b, 11), null);
assert.equal(restaurerPlanSociete(null), null);
assert.equal(restaurerPlanSociete('bad-token'), null);
const rows = [
  {compte:'7111',libelle:'Ventes société A',classe:7,type:'PD',origine:'personnalise',actif:true,nb_ecritures:99},
  {compte:'7112',libelle:'Désactivé',classe:7,type:'PD',origine:'cgnc',actif:false,nb_ecritures:9},
];
const first = enregistrerPlanSociete(rows, a, 10);
assert.equal(first.modifie,true);
assert.equal(PLAN_COMPTES.length, 1, 'pas de compte désactivé en autocomplete');
assert.equal(trouverCompte('7111').libelle, 'Ventes société A');
assert.ok(!donnees.get(first.cle).includes('nb_ecritures'), 'usage non stocké');
assert.equal(restaurerPlanSociete(a, 10), first.cle, 'rafraîchissement sans appel réseau');
assert.equal(enregistrerPlanSociete(rows, a, 10).modifie,false, 'plan inchangé = pas de remontage');
notifierPlanModifie(first.cle);
assert.equal(events.at(-1).type, EVENEMENT_PLAN_MODIFIE);
assert.equal(events.at(-1).detail.cle, first.cle);
const update = enregistrerPlanSociete([{compte:'7111',libelle:'Ventes modifiées',actif:true,classe:7,type:'PD'}],a,10);
assert.equal(update.modifie,true);
assert.equal(trouverCompte('7111').libelle, 'Ventes modifiées');
assert.equal(restaurerPlanSociete(b,11),null,'cache A invisible depuis B');
assert.equal(restaurerPlanSociete(c,10),null,'cache autre utilisateur invisible');
const other = enregistrerPlanSociete([{compte:'6111',libelle:'Achats B',actif:true,classe:6,type:'CH'}],b,11);
assert.equal(restaurerPlanSociete(a,10),first.cle);
assert.equal(trouverCompte('7111').libelle, 'Ventes modifiées', 'retour à A restaure son plan');
assert.equal(restaurerPlanSociete(b,11),other.cle);
assert.equal(trouverCompte('6111').libelle,'Achats B');
donnees.set(other.cle,'{invalide');
assert.equal(restaurerPlanSociete(b,11),null,'cache corrompu ignoré');
assert.equal(donnees.has(other.cle),false,'cache corrompu supprimé');
console.log('Cache société/utilisateur, réhydratation, fraîcheur et corruption : OK');
'''
    result = subprocess.run(
        [node, '--input-type=module', '-e', js], cwd=ROOT,
        capture_output=True, text=True, timeout=25,
    )
    assert result.returncode == 0, result.stdout + '\n' + result.stderr
    assert 'corruption : OK' in result.stdout
