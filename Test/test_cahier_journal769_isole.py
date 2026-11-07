"""Rejeu comptable API des50opérations exactes du cahier : pas une recette commerciale UI."""
from pathlib import Path
from decimal import Decimal
from contextlib import closing
from collections import defaultdict
from uuid import uuid4
import csv,json,hashlib
import httpx
from sqlalchemy import text
from postgres_isole import verifier_cible_isolee
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)
ROOT=Path(__file__).resolve().parents[1]
D=Decimal

def test_769_cinquante_operations_cahier_balance_bilan_cpc_caf(application):
 c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
 src=ROOT/'docs/recette/jeu_donnees_recette.json';source=json.loads(src.read_text(encoding='utf8'));s=source['societe'];att=source['attendus']
 preuve={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'operations':[],'erreur':None,
 'portee':'Saisie et validation par API du journal attendu uniquement ;pas de création des documents commerciaux,stocks physiques ou registres fiscaux.',
 'ordre':'Opérations triées par date,ordre source conservé à date égale,afin de respecter la chronologie de validation des journaux.'}
 def ok(r,code=200):assert r.status_code==code,r.text;return r.json()
 try:
  with httpx.Client(base_url=application['api_url'],timeout=30) as api:
   auth=ok(api.post('/api/auth/register',json={'nom':s['nom_admin'],'email':f'cahier50-{uuid4().hex[:8]}@hisabpro-recette.example','password':s['password_test'],'raison_sociale':s['raison_sociale']}))
   api.headers['Authorization']='Bearer '+auth['access_token']
   profil=ok(api.patch('/api/societe/moi',json={k:s[k] for k in ['raison_sociale','forme_juridique','ville','adresse','capital_social','devise','identifiant_fiscal','ice','rc','patente','exercice_debut','regime_fiscal','regime_tva','periodicite_tva']}))
   sid=profil['id'];tiers={}
   for t in source['tiers']:
    body={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}
    tiers[t['code']]=ok(api.post('/api/tiers',json=body),201)
   assert ok(api.get('/api/ecritures',params={'exercice':2025}))==[]
   numeros=set();ids=[]
   for o in sorted(source['operations'],key=lambda x:x['date']):
    lignes=[]
    for l in o['lignes']:
     ligne={'compte':l['compte'],'debit':l['debit'],'credit':l['credit'],'libelle':o['description']}
     if l['tiers']:ligne['tiers_id']=tiers[l['tiers']]['id']
     lignes.append(ligne)
    e=ok(api.post('/api/ecritures',json={'date':o['date'],'date_piece':o['date'],'journal':o['journal'],'libelle':o['description'],'reference':o['reference_recette'],'lignes':lignes,'est_validee':False}),201)
    assert not e['est_validee']
    e=ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
    assert e['date_validation'] and e['numero_ecriture'];ids.append(e['id']);numeros.add(e['numero_ecriture'])
    preuve['operations'].append({'reference':o['reference_recette'],'date':o['date'],'journal':o['journal'],'id':e['id'],'numero':e['numero_ecriture']})
   assert len(ids)==len(numeros)==50
   relues=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(relues)==50 and all(e['est_validee'] for e in relues)
   with application['engine'].connect() as db:
    lignes=db.execute(text('SELECT l.compte,l.debit,l.credit FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid ORDER BY e.date,e.id,l.id'),{'sid':sid}).all()
    assert len(lignes)==118
    soldes=defaultdict(lambda:D(0))
    for l in lignes:soldes[l.compte]+=D(str(l.debit))-D(str(l.credit))
    assert sum(D(str(l.debit)) for l in lignes)==sum(D(str(l.credit)) for l in lignes)
   with (ROOT/'docs/recette/balance_attendue_2025.csv').open(encoding='utf-8-sig',newline='') as f:
    attendu={l['compte']:D(l['debit'])-D(l['credit']) for l in csv.DictReader(f,delimiter=';')}
   assert {k:v for k,v in soldes.items() if v}==attendu
   liasse=ok(api.get('/api/etats/liasse/2025'));etats=liasse['etats']
   valeurs={'banque':soldes['5141'],'stock_valeur':soldes['3111'],'total_actif_net':D(str(etats['bilan']['actif']['total']['net'])),'total_passif_net':D(str(etats['bilan']['passif']['total'])),'resultat_net':D(str(etats['cpc']['resultat_net'])),'caf':D(str(etats['esg']['caf']))}
   for k,v in valeurs.items():assert v==D(att[k]),(k,v,att[k])
   assert etats['bilan']['equilibre']
   immo=next(l for l in etats['bilan']['actif']['immobilise'] if l['code']=='23')
   assert tuple(D(str(immo[k])) for k in ['brut','amort_prov','net'])==(D('24000'),D('4800'),D('19200'))
   preuve['immobilisations_bilan']={k:immo[k] for k in ['brut','amort_prov','net']}
   detail=next(l for l in etats['bilan']['detail']['actif'] if l.get('numero')=='235')
   assert D(str(detail['valeurs'][0]))==D('24000')
   preuve['detail_materiel_informatique']=detail
   preuve['soldes']={k:str(v) for k,v in sorted(soldes.items()) if v}
   preuve['resultats']={k:str(v) for k,v in valeurs.items()};preuve['ecritures']=50;preuve['lignes']=118
   # Aucune facture/règlement commercial créé par ce rejeu comptable.
   with application['engine'].connect() as db:
    for table in ['factures','reglements']:
     assert db.scalar(text(f'SELECT count(*) FROM {table} WHERE societe_id=:sid'),{'sid':sid})==0
 except BaseException as e:
  preuve['erreur']=repr(e);raise
 finally:(ROOT/'.codex-tests/cahier50_769_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
