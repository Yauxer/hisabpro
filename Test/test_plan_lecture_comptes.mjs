import assert from 'node:assert/strict'
import test from 'node:test'
import { PLAN_COMPTES, trouverCompte } from '../src/data/planComptes.js'
import { cleCachePlan, enregistrerPlanSociete, restaurerPlanSociete, trouverCompteLecture } from '../src/data/planComptableCache.js'

const stockage = new Map()
globalThis.window = { sessionStorage: {
  getItem: k => stockage.get(k) ?? null,
  setItem: (k,v) => stockage.set(k,v),
  removeItem: k => stockage.delete(k),
} }
const token = (uid,sid) => 'header.' + Buffer.from(JSON.stringify({sub:String(uid),societe_id:sid})).toString('base64url') + '.signature'
const a = token(7,10), b = token(7,11), autreUser = token(8,10)
const actif = {compte:'7111',libelle:'Ventes exactes : société A',classe:7,type:'PD',actif:true}
const inactif = {compte:'71119',libelle:'Prestations archivées — Équipe A',classe:7,type:'PD',actif:false}

test('Lecture conserve exactement le libellé inactif sans le proposer en saisie', () => {
  enregistrerPlanSociete([actif,inactif],a)
  assert.equal(trouverCompteLecture('71119',a).libelle,inactif.libelle)
  assert.equal(trouverCompte('71119'),null)
  assert.equal(PLAN_COMPTES.length,1)
  assert.equal(trouverCompte('7111').libelle,actif.libelle)
})
test('Les tokens autre société, autre utilisateur, déconnecté ne lisent pas A', () => {
  assert.equal(trouverCompteLecture('71119',b),null)
  assert.equal(trouverCompteLecture('71119',autreUser),null)
  assert.equal(trouverCompteLecture('71119',null),null)
  assert.equal(trouverCompteLecture('71119','invalide'),null)
  assert.equal(trouverCompteLecture('5111',a),null,'aucun fallback statique inventé')
})
test('Cache complet et retour société conservent le bon libellé', () => {
  enregistrerPlanSociete([{...actif,libelle:'Ventes B'}, {...inactif,libelle:'Archive B'}],b)
  assert.equal(trouverCompteLecture('71119',a),null)
  assert.equal(trouverCompteLecture('71119',b).libelle,'Archive B')
  restaurerPlanSociete(a)
  assert.equal(trouverCompteLecture('71119',a).libelle,inactif.libelle)
  assert.equal(trouverCompteLecture('71119',b),null)
})
test('Ancien cache v1 actif seulement fonctionne et sera complété au refresh', () => {
  stockage.set(cleCachePlan(a),JSON.stringify({version:1,comptes:[actif]}))
  assert.equal(restaurerPlanSociete(a),cleCachePlan(a))
  assert.equal(trouverCompteLecture('7111',a).libelle,actif.libelle)
  assert.equal(trouverCompteLecture('71119',a),null)
  assert.equal(enregistrerPlanSociete([actif,inactif],a).modifie,true)
  assert.equal(enregistrerPlanSociete([actif,inactif],a).modifie,false)
})
test('Modifier uniquement un inactif demande un rafraîchissement des lectures', () => {
  assert.equal(enregistrerPlanSociete([actif,{...inactif,libelle:'Archive corrigée'}],a).modifie,true)
  assert.equal(trouverCompteLecture('71119',a).libelle,'Archive corrigée')
  assert.equal(trouverCompte('71119'),null)
})
