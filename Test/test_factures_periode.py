"""Helpers réellement exécutés par Node ; bornes, totaux et pagination."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not shutil.which('node'), reason='Node absent')
def test_dates_totaux_avoirs_remises_et_pagination():
    script = r'''
const assert=require('node:assert/strict');
(async()=>{
 const p=await import('./src/utils/facturesPeriod.js');
 const {collecterPages}=await import('./src/utils/collecterPages.js');
 assert.equal(p.dansPeriode({date:'2026-02-01'},'2026-02-01','2026-02-28'),true);
 assert.equal(p.dansPeriode({date:'2026-02-28'},'2026-02-01','2026-02-28'),true);
 assert.equal(p.dansPeriode({date:'2026-01-31'},'2026-02-01','2026-02-28'),false);
 assert.equal(p.dansPeriode({date:'2026-03-01'},'2026-02-01','2026-02-28'),false);
 assert.equal(p.dansPeriode({date:'2026-02-01'},'2026-02-28','2026-02-01'),false);
 assert.equal(p.facturePubliee({est_validee:true,statut:'en_attente'}),true);
 for(const f of [{est_validee:false},{est_validee:true,est_proforma:true},{est_validee:true,statut:'annulee'}])assert.equal(p.facturePubliee(f),false);
 assert.equal(p.avoirPublie({statut:'annule'}),false);
 const factures=[{type:'vente',total_ht:182,total_ttc:218.4,remise_globale:10,
  lignes:[{description:'Conseil',quantite:1,prix_unitaire:200,remise:10,tva:20}]}];
 const avoirs=[{type:'vente',total_ht:25,total_ttc:30,lignes:[{description:'Ancien service',quantite:.25,montant_ht:25,montant_ttc:30}]}];
 assert.deepEqual(p.totauxFacturation(factures,avoirs),{caNetHT:157,ventesNettesTTC:188.4,achatsNetsTTC:0});
 assert.deepEqual(p.totauxFacturation([...factures,{type:'achat',total_ht:100,total_ttc:120}],
  [...avoirs,{type:'achat',total_ht:20,total_ttc:24}]),{caNetHT:157,ventesNettesTTC:188.4,achatsNetsTTC:96});
 const escompte=p.ventilationCA([{type:'vente',escompte:10,total_ht:100,total_ttc:108,
  lignes:[{description:'Service avec escompte',quantite:1,prix_unitaire:100,tva:20}]}],[]);
 assert.equal(escompte[0].ca_ht,100); assert.equal(escompte[0].ca_ttc,108);
 const lignes=p.ventilationCA(factures,avoirs,{});
 assert.equal(lignes.find(l=>l.designation==='Conseil').ca_ht,162);
 assert.equal(lignes.find(l=>l.designation==='Frais et écarts d’arrondi').ca_ht,20);
 assert.equal(lignes.find(l=>l.designation==='Ancien service').ca_ht,-25);
 assert.equal(Math.round(lignes.reduce((t,l)=>t+l.ca_ht,0)*100),15700);
 assert.equal(Math.round(lignes.reduce((t,l)=>t+l.ca_ttc,0)*100),18840);
 const consigne=p.ventilationCA([{type:'vente',frais_emballage_mode:'consigne',frais_emballage_ht:50,total_ht:50,total_ttc:50,lignes:[]}],[]);
 assert.equal(consigne.length,1); assert.equal(consigne[0].hors_article,true); assert.equal(consigne[0].ca_ht,50);
 for(const n of [100,101]) {
  const source=Array.from({length:n},(_,id)=>({id})); const appels=[];
  const total=await collecterPages(async ({skip,limit})=>{appels.push(skip);return source.slice(skip,skip+limit)});
  assert.equal(total.length,n); assert.deepEqual(appels,[0,100]);
 }
 await assert.rejects(collecterPages(async ()=>Array.from({length:100},(_,id)=>({id}))),/changé/);
 await assert.rejects(collecterPages(async ({skip})=>{if(skip)throw Error('API indisponible');return Array.from({length:100},(_,id)=>({id}))}),/indisponible/);
 console.log('OK bornes, sources documentaires, remises, avoir seul et pagination100/101');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stderr
    assert 'OK bornes' in result.stdout
