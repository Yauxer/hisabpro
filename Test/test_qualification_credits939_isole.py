"""Versions de crédits déclarés :inconnu,ancien/type à qualifier,néant confirmé."""
from contextlib import closing
import json
from test_balance_credits749_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,creer,body,url,controles)
from pathlib import Path

def test_939_versions_inconnues_et_absence_confirmee_sans_imputation(application):
 with closing(client(application)[0]) as api:
  e=ok(api.post('/api/ecritures',json={'date':'2026-01-01','journal':'BQ','reference':'TEMOIN-FICTIF939','libelle':'Témoin indépendant des crédits externes','lignes':[{'compte':'5141','debit':333},{'compte':'1111','credit':333}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
  v=creer(api);v=ok(api.post(url(v),json=body(v)),201);assert controles(v)['montants']['credits_proposes']=='325.00';versions=[v];avant=donnees_metier(application);preuves={}
  for cas in ['utilisations_inconnues','ancien_credit','type_a_qualifier','absence_non_exhaustive','absence_confirmee']:
   b=body(v);p,t=b['tables'];a=t['lignes'][0]
   if cas=='utilisations_inconnues':a['autres_utilisations']=''
   elif cas=='ancien_credit':a['exercice_rattachement']='2025'
   elif cas=='type_a_qualifier':a['type_credit']='Autre — à qualifier'
   else:
    p['lignes'][0]['absence_credits']='oui';t.update(statut='neant_declare',lignes=[])
    if cas=='absence_non_exhaustive':p['lignes'][0]['exhaustivite']='non'
   v=ok(api.post(url(v),json=b),201);versions.append(v);c=controles(v);attendu='0.00' if cas=='absence_confirmee' else None
   assert c['montants']['credits_proposes']==attendu and c['solde_final'] is None and not c['imputation_confirmee'] and not c['liquidation_confirmee']
   preuves[cas]=attendu
  for r in versions:assert ok(api.get(BASE+f'/{r["id"]}'))==r
  apres=donnees_metier(application);assert all(apres[k]==h for k,h in avant.items() if k!='liasse_balances_preparation')
  (Path(__file__).resolve().parents[1]/'.codex-tests/credits939_variantes.json').write_text(json.dumps({'fiches':['CR749-04','CR749-06'],'propositions':preuves,'versions_precedentes_figees':True,'inconnu_non_assimile_zero':True,'absence_zero_seulement_confirmee_et_exhaustive':True,'temoin_definitif333_et_journal_inchanges':True},ensure_ascii=False,indent=2),encoding='utf8')
