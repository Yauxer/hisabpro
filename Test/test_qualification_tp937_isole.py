"""Variantes documentairesTP :persistance sans zéro fictif ni montant dû."""
from contextlib import closing
import json
from tp761_support import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,body,url,verifier,controles,R)
from tiers759_support import body as tiers_body,url as tiers_url
from test_qualification_fiscale933_isole import dossier

def test_937_variantes_base_classe_avis_conservees_sans_du_ni_ecriture(application):
 with closing(client(application)[0]) as api:
  v=dossier(api);v=ok(api.post(tiers_url(v),json=tiers_body(v)),201);v=ok(api.post(url(v),json=body(v)),201);verifier(v)
  initial=v;versions=[v];avant=donnees_metier(application);preuves={}
  for cas,attendu in [('base_inconnue',None),('base_non_revue',None),('petit','1210.00'),('arrondi','1200.01'),('avis_partage','7200.00')]:
   b=body(v);a=b['tables'][1]['lignes'][0]
   if cas=='base_inconnue':a['valeur_locative']=''
   elif cas=='base_non_revue':a['base_revue']='non'
   elif cas=='petit':a.update(valeur_locative='100',classe='C3')
   elif cas=='arrondi':a.update(valeur_locative='0.05',classe='C3')
   else:b['tables'][1]['lignes'][1]['reference_avis']=' avis761-a '
   v=ok(api.post(url(v),json=b),201);versions.append(v);c=controles(v);assert c['montants']['brut_propose']==attendu
   if cas=='base_inconnue':assert c['montants']['valeur_locative_totale'] is None
   if cas=='arrondi':assert c['etablissements'][0]['brut_exact']=='0.005'
   if cas=='avis_partage':assert c['montants']['avis_comparables'] is None and c['montants']['ecart_brut_avis'] is None
   assert c['montant_du_confirme'] is None and not c['imposition_confirmee'] and not c['paiement_confirme'] and not c['pret_a_deposer']
   preuves[cas]=c['montants']
  for r in versions:assert ok(api.get(BASE+f'/{r["id"]}'))==r
  assert controles(initial)['montants']['brut_propose']=='7200.00'
  apres=donnees_metier(application);assert all(apres[k]==h for k,h in avant.items() if k!='liasse_balances_preparation')
  (R/'.codex-tests/tp937_variantes.json').write_text(json.dumps({'fiches':['TP761-03','TP761-05','TP761-06'],'variantes':preuves,'versions_sources_figees':True,'aucun_du_confirme':True,'temoin_definitif333_journal_sources_inchanges':True},ensure_ascii=False,indent=2),encoding='utf8')
