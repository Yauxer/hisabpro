"""Acomptes et revue IS :versions déclaratives sans double usage ni confirmation."""
from contextlib import closing
from pathlib import Path
import json
from test_balance_acomptes751_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,
 creer as creer_ap,body as body_ap,url as url_ap,controles as controles_ap)
from test_balance_liquidation753_isole import creer as creer_liq,body as body_liq,url as url_liq,controles as controles_liq
R=Path(__file__).resolve().parents[1]
def temoin(api,ref):
 e=ok(api.post('/api/ecritures',json={'date':'2026-01-01','journal':'BQ','reference':ref,'libelle':'Témoin indépendant du cycle IS déclaré','lignes':[{'compte':'5141','debit':333},{'compte':'1111','credit':333}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'))

def test_941_acomptes_references_inversees_annuelle_inconnue_neant_sans_zero(application):
 with closing(client(application)[0]) as api:
  temoin(api,'TEMOIN-FICTIF941-AP');v=creer_ap(api);v=ok(api.post(url_ap(v),json=body_ap(v)),201);assert controles_ap(v)['montants']['acomptes_proposes']=='1250.00';versions=[v];avant=donnees_metier(application);preuves={}
  for cas in ['references_inversees','annuelle_inconnue','neant_non_confirme']:
   b=body_ap(v);p,t=b['tables']
   if cas=='references_inversees':t['lignes'][0]['reference_credit'],t['lignes'][1]['reference_credit']=t['lignes'][1]['reference_credit'],t['lignes'][0]['reference_credit']
   elif cas=='annuelle_inconnue':p['lignes'][0]['reference_annuelle']=''
   else:t.update(statut='neant_declare',lignes=[])
   v=ok(api.post(url_ap(v),json=b),201);versions.append(v);c=controles_ap(v)
   if cas=='annuelle_inconnue':assert not c['calendrier_disponible'] and c['montants']['acomptes_proposes']=='1250.00'
   else:assert c['montants']['acomptes_proposes'] is None
   if cas=='references_inversees':assert c['montants']['ecart_retenues']=='0.00' and not all(x['coherent'] for x in c['rapprochement_retenues'])
   assert c['solde_final'] is None and not c['paiement_confirme'] and not c['liquidation_confirmee'];preuves[cas]={'acomptes_proposes':c['montants']['acomptes_proposes'],'calendrier_disponible':c['calendrier_disponible']}
  for r in versions:assert ok(api.get(BASE+f'/{r["id"]}'))==r
  apres=donnees_metier(application);assert all(apres[k]==h for k,h in avant.items() if k!='liasse_balances_preparation')
  (R/'.codex-tests/is941_acomptes.json').write_text(json.dumps({'fiches':['AP751-03','AP751-06','AP751-07'],'variantes':preuves,'sources_versions_temoins_definitifs_inchanges':True},ensure_ascii=False,indent=2),encoding='utf8')

def test_941_revue_ordre_non_et_excedent_inconnu_conserves_sans_solde(application):
 with closing(client(application)[0]) as api:
  temoin(api,'TEMOIN-FICTIF941-LIQ');v=creer_liq(api,css=True);v=ok(api.post(url_liq(v),json=body_liq(v)),201);assert controles_liq(v)['montants']['solde_is_propose']=='1425.00';versions=[v];avant=donnees_metier(application)
  for cas in ['ordre_non','excedent_inconnu']:
   b=body_liq(v);p=b['tables'][0]['lignes'][0];p['ordre_examine' if cas=='ordre_non' else 'excedent_annuel']='non' if cas=='ordre_non' else ''
   v=ok(api.post(url_liq(v),json=b),201);versions.append(v);c=controles_liq(v);assert c['montants']['solde_is_propose'] is None and not c['liquidation_confirmee'] and not c['paiement_confirme'] and not c['pret_a_deposer'] and c['total_global_is_css'] is None
  for r in versions:assert ok(api.get(BASE+f'/{r["id"]}'))==r
  apres=donnees_metier(application);assert all(apres[k]==h for k,h in avant.items() if k!='liasse_balances_preparation')
  (R/'.codex-tests/is941_revue.json').write_text(json.dumps({'fiche':'LIQ753-03','ordre_non_et_excedent_inconnu_conserves':True,'propositions_indisponibles':True,'ancienne_proposition1425_figee':True,'sources_et_temoin_definitif333_inchanges':True},ensure_ascii=False,indent=2),encoding='utf8')
