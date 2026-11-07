"""Identité et montant inconnus :versions durables,aucune réparation implicite."""
from contextlib import closing
import json
from tiers759_support import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,body,url,verifier,controles,R)
from test_qualification_fiscale933_isole import dossier

def test_935_conserver_identite_et_somme_inconnues_sans_zero_ni_ecriture(application):
 with closing(client(application)[0]) as api:
  v=dossier(api);avant=donnees_metier(application)
  b=body(v);b['tables'][1]['lignes'][0]['cnss']=''
  v1=ok(api.post(url(v),json=b),201);assert not controles(v1)['revue_documentaire_declaree']
  q=body(v1);q['tables'][2]['lignes'][0]['soumis']=''
  v2=ok(api.post(url(v1),json=q),201);c=controles(v2);assert c['montants']['soumis'] is None and not c['revue_documentaire_declaree']
  v3=ok(api.post(url(v2),json=body(v2)),201);verifier(v3)
  assert ok(api.get(BASE+f'/{v1["id"]}'))==v1 and ok(api.get(BASE+f'/{v2["id"]}'))==v2
  apres=donnees_metier(application);assert all(apres[k]==h for k,h in avant.items() if k!='liasse_balances_preparation')
  (R/'.codex-tests/tiers935_inconnus.json').write_text(json.dumps({'fiche':'TIERS759-04','identite_incomplete_conservee':True,'somme_inconnue_conservee':None,'versions_incompletes_reconsultables':True,'reprise_complete':controles(v3)['montants'],'temoin_definitif333_sources_et_journal_inchanges':True},ensure_ascii=False,indent=2),encoding='utf8')
