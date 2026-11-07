"""Horloge navigateur seule : scénario RAS complet, API/PG nonce non interceptés."""
from datetime import date
import pytest
from playwright.sync_api import Browser
from test_e2e_facturation_isole import application
from test_e2e_ras_capture_isole import (
    test_captures_declarees_reglements_od_et_annulation_tracees as scenario_ras,
)


@pytest.mark.parametrize('largeur', [1365, 390])
@pytest.mark.parametrize('nature', ['vente', 'achat'])
def test_annulation_ras_a_minuit_local_conserve_la_date(application, monkeypatch, largeur, nature):
    jour = date.today()
    original = Browser.new_page

    def page_a_minuit(browser, **kwargs):
        kwargs['timezone_id'] = 'Europe/Paris'
        page = original(browser, **kwargs)
        page.add_init_script(f"""
          const NativeDate = Date;
          const now = new NativeDate({jour.year}, {jour.month - 1}, {jour.day}, 0, 30).getTime();
          window.Date = class extends NativeDate {{
            constructor(...args) {{ super(...(args.length ? args : [now])); }}
            static now() {{ return now; }}
          }};
        """)
        return page

    monkeypatch.setattr(Browser, 'new_page', page_a_minuit)
    # Le scénario vérifie aussi capture/OD/validation/lettrage/délettrage,
    # annulation et intégrité de toutes les écritures définitives existantes.
    scenario_ras(application, largeur, nature)
