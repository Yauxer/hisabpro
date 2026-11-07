"""Diagnostic manuel de navigations rapides et de l’attente des polices.

Lancer explicitement pytest Test/diagnostic_navigation_polices817.py.
Ce stress a échoué ; il ne constitue pas une validation fonctionnelle.
"""
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire
from test_e2e_cahier_avant_is817_isole import (observer_navigation,
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)


@pytest.mark.parametrize('serie',[1,2])
def test_817_navigation_locale_repetee_diagnostic(application,tmp_path,serie):
 with laboratoire(application,1440,tmp_path,'navigation817_'+str(serie)) as (api,page,sid,preuve):
  observer_navigation(page,preuve);preuve['navigations_terminees']=[]
  try:
   for route in ['/journal','/immobilisations','/factures','/lettrage','/grand-livre']*6:
    page.goto(application['web_url']+route);expect(page.get_by_role('main')).to_be_visible();preuve['navigations_terminees'].append(route)
  except BaseException:
   log=tmp_path/'serveur_navigation817.log';log.write_bytes(application['web_log'].read_bytes());preuve['journal_serveur_navigation']=str(log);raise
  assert len(preuve['navigations_terminees'])==30
