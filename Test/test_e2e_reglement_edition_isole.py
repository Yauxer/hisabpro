"""Édition réelle des règlements vente/achat : Edge, API et PostgreSQL nonce."""
from datetime import date, timedelta
import uuid
import httpx
import pytest
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion, observer


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


@pytest.mark.parametrize('sens', ['vente', 'achat'])
def test_reglement_edition_montant_date_mode_commentaire_et_blocage(application, sens):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'reglement-{suffix}@example.com', 'ReglementEdition2026!'
    aujourdhui = date.today()
    initiale = (aujourdhui - timedelta(days=2)).isoformat()
    nouvelle = (aujourdhui - timedelta(days=1)).isoformat()
    with httpx.Client(base_url=application['api_url']) as api:
        auth = ok(api.post('/api/auth/register', json={'nom':'Admin laboratoire','email':email,
            'password':password,'raison_sociale':'Édition fictive '+suffix}))
        api.headers['Authorization'] = 'Bearer '+auth['access_token']
        tiers = ok(api.post('/api/tiers', json={'nom':f'Tiers édition {suffix}',
            'type':'client' if sens == 'vente' else 'fournisseur'}), 201)
        f = ok(api.post('/api/factures', json={'type':sens,'date':initiale,'tiers':tiers['nom'],
            'tiers_id':tiers['id'],'reference': 'ACH-'+suffix if sens=='achat' else None,
            'lignes':[{'description':'Service laboratoire','quantite':1,'prix_unitaire':1000,'tva':20}]}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        # 977 : la caisse est alimentée avant tout paiement fournisseur en espèces.
        ok(api.post('/api/ecritures', json={'date':(aujourdhui - timedelta(days=5)).isoformat(),'journal':'CA','libelle':'Apport en caisse fictif',
            'est_validee':True,'lignes':[{'compte':'5161','libelle':'Caisse','debit':5000,'credit':0},{'compte':'1111','libelle':'Apport','debit':0,'credit':5000}]}), 201)
        r = ok(api.post('/api/reglements', json={'facture_id':f['id'],'tiers':tiers['nom'],
            'date':initiale,'montant':400,'mode':'virement','comptabiliser':False}), 201)
        date_seule = ok(api.patch(f"/api/reglements/{r['id']}", json={'date':nouvelle}))
        assert date_seule['statut']=='complet' and date_seule['date_encaissement']==nouvelle
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            page = browser.new_page(viewport={'width':1440,'height':1000})
            page.set_default_timeout(15000)
            erreurs, serveurs = observer(page, application['api_url'])
            try:
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button', name='Vente' if sens=='vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                ligne = page.locator('tbody tr').filter(has_text=tiers['nom'])
                ligne.get_by_title('Modifier', exact=True).click()
                modal = page.get_by_role('dialog', name='Modifier règlement', exact=True)
                modal.locator('input[type=number]').fill('600')
                modal.locator('input[type=date]').first.fill(nouvelle)
                mode = 'cheque' if sens=='vente' else 'effet'
                modal.locator('select').first.select_option(mode)
                if mode=='effet':
                    modal.locator('input[type=date]').nth(1).fill(aujourdhui.isoformat())
                problemes = []
                commentaire = modal.locator('textarea')
                if commentaire.count():
                    commentaire.fill('Commentaire modifié par recette UI')
                else:
                    problemes.append('Champ commentaire absent du formulaire édition')
                with page.expect_response(lambda rep: rep.url.endswith(f"/api/reglements/{r['id']}") and rep.request.method=='PATCH') as sauvegarde:
                    modal.get_by_role('button', name='Enregistrer', exact=True).click()
                modifie = sauvegarde.value.json()
                assert sauvegarde.value.status == 200, modifie
                modal.wait_for(state='hidden')
                playwright.expect(ligne).to_contain_text('600,00 MAD')
                assert modifie['date']==nouvelle and modifie['mode']==mode and modifie['montant']==600
                # La réouverture vérifie le commentaire réellement relu côté serveur.
                ligne.get_by_title('Modifier', exact=True).click()
                modal = page.get_by_role('dialog', name='Modifier règlement', exact=True)
                if modal.locator('textarea').count():
                    playwright.expect(modal.locator('textarea')).to_have_value('Commentaire modifié par recette UI')
                modal.get_by_role('button', name='Annuler', exact=True).click()
                attendu = 'portefeuille' if sens=='vente' else 'a_payer'
                if modifie['statut'] != attendu or modifie['date_encaissement'] is not None:
                    problemes.append(f"Mode différé incohérent : statut={modifie['statut']}, date_encaissement={modifie['date_encaissement']}")
                if modifie['notes'] != 'Commentaire modifié par recette UI':
                    problemes.append('Commentaire non enregistré')
                situation = ok(api.get(f"/api/factures/{f['id']}/reglements"))
                assert situation['solde_restant']==600, situation
                assert not erreurs and not serveurs, (erreurs, serveurs)
                assert not problemes, problemes
                # Un moyen immédiat reprend les règles déjà utilisées à la création.
                ligne.get_by_title('Modifier', exact=True).click()
                modal = page.get_by_role('dialog', name='Modifier règlement', exact=True)
                modal.locator('input[type=number]').fill('1200')
                modal.locator('select').first.select_option('especes')
                with page.expect_response(lambda rep: rep.url.endswith(f"/api/reglements/{r['id']}") and rep.request.method=='PATCH') as sauvegarde:
                    modal.get_by_role('button', name='Enregistrer', exact=True).click()
                assert sauvegarde.value.status == 200, sauvegarde.value.text()
                immediat = sauvegarde.value.json()
                assert immediat['statut']=='complet' and immediat['date_encaissement']==nouvelle
                modal.wait_for(state='hidden')
                playwright.expect(ligne).to_contain_text('Soldée')
                assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==0
                ok(api.patch('/api/societe/modules', json={'module':'comptabilite','actif':True}))
                ok(api.post(f"/api/reglements/{r['id']}/comptabiliser"))
                r_compta = next(v for v in ok(api.get('/api/reglements', params={'exercice':aujourdhui.year})) if v['id']==r['id'])
                eid = r_compta['ecriture_id']
                ok(api.post(f'/api/ecritures/{eid}/valider'))
                original = ok(api.get(f'/api/ecritures/{eid}'))
                page.reload()
                page.get_by_role('button', name='Vente' if sens=='vente' else 'Achat', exact=True).click()
                page.get_by_role('button', name='Règlements', exact=True).click()
                playwright.expect(ligne.get_by_title('Modifier', exact=True)).to_have_count(0)
                playwright.expect(ligne.get_by_title('Annuler par contrepassation', exact=True)).to_have_count(1)
                avant = ok(api.get(f"/api/factures/{f['id']}/reglements"))
                assert api.patch(f"/api/reglements/{r['id']}", json={'montant':100}).status_code==409
                assert ok(api.get(f"/api/factures/{f['id']}/reglements"))==avant
                page.once('dialog', lambda dialog: dialog.accept())
                with page.expect_response(lambda rep: rep.url.endswith(f"/api/reglements/{r['id']}/annuler")) as annulation:
                    ligne.get_by_title('Annuler par contrepassation', exact=True).click()
                    page.get_by_role('dialog',name='Annuler le règlement',exact=True).get_by_role('button',name='Confirmer l’annulation',exact=True).click()
                assert annulation.value.status==200, annulation.value.text()
                assert annulation.value.json()['statut']=='annule'
                assert ok(api.get(f'/api/ecritures/{eid}'))==original
                assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==1200
                if sens=='vente':
                    # Cycle bancaire engagé sans réception comptabilisée : protection identique.
                    engage = ok(api.post('/api/reglements', json={'facture_id':f['id'],'tiers':tiers['nom'],
                        'date':nouvelle,'montant':400,'mode':'cheque','comptabiliser':False}), 201)
                    engage = ok(api.post(f"/api/reglements/{engage['id']}/transition",
                        json={'action':'remettre','date_effective':aujourdhui.isoformat()}))
                    assert engage['statut']=='encaissement' and not engage['est_comptabilisee']
                    assert api.patch(f"/api/reglements/{engage['id']}", json={'montant':100}).status_code==409
                    note = ok(api.patch(f"/api/reglements/{engage['id']}", json={'notes':'Note cycle engagé'}))
                    assert note['montant']==400 and note['statut']=='encaissement'
                    assert note['notes']=='Note cycle engagé'
            finally:
                browser.close()
