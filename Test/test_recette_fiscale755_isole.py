"""Scénario755 : API réelle, sources exactes et contrôles négatifs sans toucher au Journal."""
from contextlib import closing
from copy import deepcopy
import pytest
from fiscal755_support import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok,BASE,donnees_metier,R,D,payload,creer,bodies,verifier,verifier_export,
 credits_url,ap_url,liq_url)
from test_logo_societe import image_data


def test_755_api_csv_sources_solde_et_exports_sans_ecriture(application):
 with closing(client(application)[0]) as api:
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
  v=creer(api);verifier(v);r=api.get(BASE+f'/{v["id"]}/zip');assert r.status_code==200
  verifier_export(r.content,v);apres=donnees_metier(application)
  assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('cas',['doublon','nonfini'])
def test_755_csv_errone_sans_nouvelle_preparation(application,cas):
 with closing(client(application)[0]) as api:
  q=payload()
  if cas=='doublon':q['lignes_n'].append(deepcopy(q['lignes_n'][0]))
  else:q['lignes_n'][0]['credit']='NaN'
  avant=donnees_metier(application);assert api.post(BASE,json=q).status_code==422 and donnees_metier(application)==avant


def test_755_payeur_avant_juillet_revue_et_dependances_reprises(application):
 with closing(client(application)[0]) as api:
  v=creer(api);ancien=deepcopy(v);q=bodies(v)['credits'];q['tables'][1]['lignes'][1]['categorie_payeur']='Banque ou assurance'
  v2=ok(api.post(credits_url(v),json=q),201);assert v2['contenu']['credits_is_documentaires']['controle_credits']['montants']['credits_proposes'] is None
  assert ok(api.get(liq_url(v2)))['sources_is_modifiees']
  v3=ok(api.post(ap_url(v2),json=bodies(v2)['acomptes']),201);assert v3['contenu']['acomptes_is_documentaires']['controle_acomptes']['montants']['acomptes_proposes'] is None
  v4=ok(api.post(liq_url(v3),json=bodies(v3)['liquidation']),201);assert v4['contenu']['liquidation_is_documentaire']['controle_liquidation']['montants']['solde_is_propose'] is None
  v5=ok(api.post(credits_url(v4),json=bodies(v4)['credits']),201)
  v6=ok(api.post(ap_url(v5),json=bodies(v5)['acomptes']),201)
  v7=ok(api.post(liq_url(v6),json=bodies(v6)['liquidation']),201);verifier(v7)
  assert ok(api.get(BASE+f'/{ancien["id"]}'))==ancien
