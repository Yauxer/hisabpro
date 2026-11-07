"""Navigation de recette : terminer les polices locales avant la page suivante.

Aucun délai augmenté, aucune police ignorée et aucun changement applicatif.
"""
import pytest
from playwright.sync_api import Page

@pytest.fixture
def navigations_completes823(monkeypatch):
 original=Page.goto
 def aller(page,url,**kwargs):
  if page.url.startswith('http://127.0.0.1:'):
   page.wait_for_function("document.fonts.status === 'loaded'",timeout=15000)
  reponse=original(page,url,**kwargs)
  page.wait_for_function("document.fonts.status === 'loaded'",timeout=15000)
  return reponse
 monkeypatch.setattr(Page,'goto',aller)
