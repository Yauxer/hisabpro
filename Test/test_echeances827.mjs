import test from 'node:test'
import assert from 'node:assert/strict'
import { dateEcheanceAffichee, joursAvantEcheance, joursCalendairesAvant, factureEnRetard } from '../src/utils/echeancesFactures.js'
const f = Object.freeze({statut:'partiellement_payee',est_validee:true,date:'2025-04-01',date_echeance:'2025-04-30',date_prochaine_echeance:'2025-05-31',echeances:[{montant:600},{montant:600}]})
test('première échéance réglée : seule la prochaine ouverte détermine le retard',()=>{
 assert.equal(dateEcheanceAffichee(f),'2025-05-31')
 assert.equal(joursAvantEcheance(f,new Date(2025,4,30,23,59)),1)
 assert.equal(factureEnRetard(f,new Date(2025,4,30,23,59)),false)
 assert.equal(f.date_echeance,'2025-04-30')
})
test('échéance du jour sans retard, puis retard dès le lendemain',()=>{
 assert.equal(joursAvantEcheance(f,new Date(2025,4,31,23,59)),0)
 assert.equal(factureEnRetard(f,new Date(2025,4,31,23,59)),false)
 assert.equal(joursAvantEcheance(f,new Date(2025,5,1,0,1)),-1)
 assert.equal(factureEnRetard(f,new Date(2025,5,1,0,1)),true)
})
test('absence de prochaine échéance qualifiée : ne pas réutiliser la première soldée',()=>{
 assert.equal(joursAvantEcheance({...f,date_prochaine_echeance:null},new Date(2025,5,1)),null)
 const ancien={...f};delete ancien.date_prochaine_echeance
 assert.equal(dateEcheanceAffichee(ancien),null)
 assert.equal(factureEnRetard(ancien,new Date(2025,5,1)),false)
})
test('paiement unique et repli sur délai contractuel restent disponibles',()=>{
 assert.equal(joursAvantEcheance({date:'2025-05-31',delai_paiement:0},new Date(2025,5,1)),-1)
 assert.equal(dateEcheanceAffichee({date:'2025-04-01',date_echeance:'2025-05-31'}),'2025-05-31')
 assert.equal(dateEcheanceAffichee({date:'2025-04-01',delai_paiement:60}),'2025-05-31')
})
test('dates invalides et factures exclues du retard ne sont pas devinées',()=>{
 assert.equal(joursCalendairesAvant('2025-02-30',new Date(2025,2,1)),null)
 for(const statut of ['payee','annulee','brouillon'])assert.equal(joursAvantEcheance({...f,statut},new Date(2025,5,1)),null)
 assert.equal(joursAvantEcheance({...f,est_validee:false},new Date(2025,5,1)),null)
 assert.equal(joursAvantEcheance({...f,est_proforma:true},new Date(2025,5,1)),null)
})
