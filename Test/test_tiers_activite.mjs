import assert from 'node:assert/strict'
import test from 'node:test'
import { resumerActivite, chargerSoldes, joursDepuis, categorieDelaiPaiement, correspondDelaiPaiement } from '../src/utils/tiersActivite.js'
import { collecterPages } from '../src/utils/collecterPages.js'

const tiers = [{ id: 1, nom: 'Même nom' }, { id: 2, nom: 'Même nom' }]
const facture = (id, champs = {}) => ({ id, tiers_id: 1, tiers: 'Même nom', type: 'vente', date: '2026-10-07', est_validee: true, statut: 'partiellement_payee', total_ttc: 1200, ...champs })

test('Identifiants séparent les homonymes et le reliquat remplace le TTC', () => {
  const r = resumerActivite(tiers, [facture(1), facture(2,{ tiers_id: 2 })], { 1: { solde_restant: 800 }, 2: { solde_restant: 200 } })
  assert.equal(r.parTiers[1].creances, 800)
  assert.equal(r.parTiers[2].creances, 200)
  assert.equal(r.parTiers[1].nb, 1)
})
test('Pas de rapprochement nominal historique ni attribution à un tiers absent', () => {
  const r = resumerActivite(tiers, [facture(1,{ tiers_id: null }), facture(2,{ tiers_id: 99 })], {})
  assert.equal(r.nonRattachees, 2)
  assert.deepEqual(r.parTiers, {})
})
test('Brouillons, proformas et annulées ne sont pas une activité publiée', () => {
  const r = resumerActivite(tiers,[facture(1,{ est_validee: false }),facture(2,{ est_proforma: true }),facture(3,{ statut: 'annulee' })],{})
  assert.deepEqual(r.parTiers,{})
})
test('Créances et dettes sont séparées, facture soldée ne recrée pas un impayé', () => {
  const r = resumerActivite(tiers,[facture(1),facture(2,{type:'achat'}),facture(3,{statut:'payee'})],{1:{solde_restant:800},2:{solde_restant:300}})
  assert.equal(r.parTiers[1].creances,800)
  assert.equal(r.parTiers[1].dettes,300)
  assert.equal(r.parTiers[1].nb,3)
  assert.equal(r.parTiers[1].indetermines,0)
})
test('RAS nulle ou détail en erreur reste indéterminé, jamais TTC ou zéro', () => {
  const r = resumerActivite(tiers,[facture(1),facture(2),facture(3)],{1:{solde_restant:null},2:{erreur:'HTTP500'},3:{solde_restant:0}})
  assert.equal(r.parTiers[1].indetermines,2)
  assert.equal(r.parTiers[1].impaye,0)
})
test('Dates calendaires valides et futures', () => {
  const ref = new Date(2026,9,7,15)
  assert.equal(joursDepuis('2026-10-07',ref),0)
  assert.equal(joursDepuis('2026-10-08',ref),-1)
  assert.equal(joursDepuis('2026-02-30',ref),null)
})
test('Pagination exhaustive dépasse anciennes bornes200 et2000', async () => {
  const donnees = Array.from({length:2001},(_,i)=>({id:i+1}))
  const all = await collecterPages(async ({skip,limit}) => donnees.slice(skip,skip+limit))
  assert.equal(all.length,2001)
  assert.equal(all.at(-1).id,2001)
})
test('Chargement borné et erreur isolée ne supprime pas les soldes connus', async () => {
  let actifs=0,max=0
  const result = await chargerSoldes(Array.from({length:9},(_,i)=>facture(i+1)),async id=>{
    actifs++;max=Math.max(max,actifs)
    await new Promise(resolve=>setTimeout(resolve,2))
    actifs--
    if(id===3) throw new Error('Indisponible')
    return {solde_restant:800}
  })
  assert.equal(max,4)
  assert.equal(result[1].solde_restant,800)
  assert.equal(result[3].erreur,'Indisponible')
})

test('Délai du tiers : frontières exactes et aucune conversion implicite en comptant', () => {
  for (const [valeur, attendu] of [[0,'comptant'],[1,'1_30'],[30,'1_30'],[31,'31_60'],[60,'31_60'],[61,'plus_60'],[1000000,'plus_60']]) {
    assert.equal(categorieDelaiPaiement(valeur), attendu)
    assert.equal(correspondDelaiPaiement(valeur, attendu), true)
    assert.equal(correspondDelaiPaiement(valeur, 'a_verifier'), false)
  }
  for (const valeur of [null,undefined,'','0','30',false,true,NaN,Infinity,-Infinity,-1,1.5,{},[]]) {
    assert.equal(categorieDelaiPaiement(valeur), 'a_verifier')
    assert.equal(correspondDelaiPaiement(valeur, 'comptant'), false)
    assert.equal(correspondDelaiPaiement(valeur, 'TOUS'), true)
  }
})
