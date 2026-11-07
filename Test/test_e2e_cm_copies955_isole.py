"""HP-FIS-024 : deux copies comptables indépendantes, vrais formulaires et PG nonce."""
from contextlib import closing
import json
import pytest
from playwright.sync_api import sync_playwright, expect
from fiscal947_support import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, copie, lire, core, ok, D, ROOT,
)
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer


@pytest.mark.parametrize('largeur', [1440, 390])
def test_955_cm_exoneree_et_controle_non_exonere_independants(application, largeur):
    resultats = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            for exoneree in [True, False]:
                api, email, password = client(application)
                with closing(api):
                    sid = copie(api, application)
                    avant = core(application, sid)
                    assert len(avant) == 48
                    initial = lire(api)
                    assert D(str(initial['cotisation_minimale']['base_comptable_brute'])) == D('170500')
                    assert D('170500') * D('.0025') == D('426.25')
                    assert D(str(initial['cotisation_minimale']['cm_calculee'])) == D('426.25')
                    assert D(str(initial['cotisation_minimale']['cm_exigible'])) == D('3000')
                    if exoneree:
                        refus = api.put('/api/fiscalite/is/2025/parametres', json={
                            'cm_exoneration_totale':True, 'cm_justification_exoneration':''})
                        assert refus.status_code == 422, refus.text
                        assert D(str(lire(api)['cotisation_minimale']['cm_exigible'])) == 3000
                    page = browser.new_page(viewport={'width':largeur,'height':1050})
                    page.set_default_timeout(15000)
                    errors, serveurs = observer(page, application['api_url'])
                    try:
                        connexion(page, application['web_url'], email, password)
                        page.goto(application['web_url']+'/cloture')
                        page.get_by_label('Exercice actif',exact=True).select_option('2025')
                        page.goto(application['web_url']+'/fiscalite-is')
                        cb=page.get_by_label('Exonération totale de cotisation minimale pour cet exercice',exact=True)
                        cb.set_checked(exoneree)
                        justification="CGI article144-I-C-1 ;constitution et exploitation01/01/2025 ;hors concession de service public ;justificatif FICTIF REC-CM01"
                        if exoneree:page.get_by_label("Justification de l'exonération CM",exact=True).fill(justification)
                        section=page.locator('section').filter(has=cb)
                        with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2025/parametres') and r.request.method=='PUT') as r:
                            section.get_by_role('button',name='Enregistrer',exact=True).click()
                        ok(r.value)
                        page.reload()
                        expect(cb).to_be_checked(checked=exoneree)
                        if exoneree:expect(page.get_by_label("Justification de l'exonération CM",exact=True)).to_have_value(justification)
                        apres=lire(api)
                        assert D(str(apres['cotisation_minimale']['cm_exigible'])) == (0 if exoneree else 3000)
                        assert D(str(apres['calcul']['is_theorique'])) == D('23420.25')
                        assert D(str(apres['liquidation']['solde_a_payer'])) == D('23220.25')
                        assert apres['calcul']==initial['calcul'] and core(application,sid)==avant
                        assert not errors and not serveurs,(errors,serveurs)
                        page.screenshot(path=str(ROOT/f'.codex-tests/cm955_{largeur}_{exoneree}.png'),full_page=True)
                        resultats.append({'societe_id':sid,'exoneree':exoneree,'comptabilite_inchangee':True,
                            'ecritures':48,'cm':apres['cotisation_minimale'],'calcul':apres['calcul'],
                            'liquidation':apres['liquidation'],'rechargement_UI':True})
                    finally:page.close()
            assert resultats[0]['societe_id'] != resultats[1]['societe_id']
            assert resultats[0]['calcul']==resultats[1]['calcul']
        finally:browser.close()
    (ROOT/f'.codex-tests/cm955_{largeur}_preuve.json').write_text(json.dumps({
        'largeur':largeur,'copies':resultats,'limites':'Copies de48opérations avantIS ;pas de dossiercommercial complet restauré,pas de nouvelle règle ouexonération réelle validée.'},
        ensure_ascii=False,indent=2,default=str),encoding='utf8')
