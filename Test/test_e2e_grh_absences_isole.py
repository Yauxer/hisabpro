"""Congés / absences : interface réelle, API réelle, PostgreSQL éphémère."""
from datetime import date
from pathlib import Path
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application as application_base
from test_e2e_paie_grh_isole import compte, navigateur


@pytest.fixture(scope='module')
def application(application_base):
    app = application_base
    cible = app['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    with app['engine'].begin() as db:
        for migration in ('080_dossiers_employes.sql', '081_grh_absences.sql'):
            db.exec_driver_sql((Path(__file__).resolve().parents[1] / 'hisabpro-backend' / migration).read_text(encoding='utf-8'))
    return app


def ouvrir_demande(page, eid, debut, fin, motif):
    page.get_by_role('button', name='Nouvelle demande', exact=True).click()
    page.get_by_label('Salarié concerné', exact=False).select_option(str(eid))
    page.get_by_label('Début de l’absence', exact=False).fill(debut)
    page.get_by_label('Fin de l’absence', exact=False).fill(fin)
    page.get_by_label('Motif ou précision', exact=True).fill(motif)


def test_grh_demande_decision_annulation_historique_et_negatifs_ui(application):
    suffix = uuid.uuid4().hex[:8]
    annee = date.today().year
    with httpx.Client(base_url=application['api_url']) as api:
        email, password = compte(api, suffix)
        sid = api.get('/api/societe/moi').json()['id']
        nom = 'Salariée congés fictive ' + suffix
        response = api.post('/api/employes', json={'nom': nom, 'salaire_brut': 8000, 'date_embauche': f'{annee}-01-01', 'personnes_charge_ir': 0})
        assert response.status_code == 201, response.text
        eid = response.json()['id']
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=navigateur(), headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_role('button', name='Congés & absences', exact=True).click()
                ouvrir_demande(page, eid, f'{annee}-11-05', f'{annee}-11-07', 'Demande fictive initiale')
                with page.expect_response(lambda r: r.url.endswith('/api/employes/conges') and r.request.method == 'POST') as creation:
                    page.get_by_role('button', name='Enregistrer la demande', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                aid = creation.value.json()['id']
                assert creation.value.json()['jours_calendaires'] == 3
                page.get_by_role('status').get_by_text('Demande enregistrée dans le dossier salarié.', exact=True).wait_for()
                ligne = page.locator('tbody tr').filter(has_text=nom)
                assert ligne.locator('td').nth(3).inner_text() == '3'
                assert ligne.locator('td').nth(4).inner_text() == 'Demandée'
                # Même intervalle : vrai refus409 et historique préservé.
                ouvrir_demande(page, eid, f'{annee}-11-06', f'{annee}-11-08', 'Chevauchement fictif')
                with page.expect_response(lambda r: r.url.endswith('/api/employes/conges') and r.request.method == 'POST') as chevauchement:
                    page.get_by_role('button', name='Enregistrer la demande', exact=True).click()
                assert chevauchement.value.status == 409
                page.get_by_role('alert').get_by_text('Une demande active chevauche déjà cette période', exact=False).wait_for()
                assert len(api.get('/api/employes/conges').json()) == 1
                # Dates inversées : 422 lisible, aucun [object Object].
                page.get_by_label('Début de l’absence', exact=False).fill(f'{annee}-11-10')
                page.get_by_label('Fin de l’absence', exact=False).fill(f'{annee}-11-09')
                with page.expect_response(lambda r: r.url.endswith('/api/employes/conges') and r.request.method == 'POST') as dates:
                    page.get_by_role('button', name='Enregistrer la demande', exact=True).click()
                assert dates.value.status == 422
                page.get_by_role('alert').get_by_text('La fin précède le début', exact=False).wait_for()
                assert '[object Object]' not in page.locator('body').inner_text()
                page.get_by_role('button', name='Fermer la demande', exact=True).click()
                page.get_by_role('button', name=f'Approuver demande {aid}', exact=True).click()
                page.get_by_label('Commentaire de décision', exact=True).fill('Accord fictif du responsable')
                with page.expect_response(lambda r: f'/api/employes/conges/{aid}' in r.url and r.request.method == 'PATCH') as decision:
                    page.get_by_role('button', name='Confirmer la décision', exact=True).click()
                assert decision.value.status == 200, decision.value.text()
                page.get_by_role('status').get_by_text('Décision enregistrée avec son historique.', exact=True).wait_for()
                assert page.locator('tbody tr').filter(has_text=nom).locator('td').nth(4).inner_text() == 'Approuvée'
                page.get_by_role('button', name=f'Historique demande {aid}', exact=True).click()
                histoire = page.locator('ol')
                assert histoire.locator('li').count() == 2
                assert 'Demandée → Approuvée' in histoire.inner_text()
                assert 'Accord fictif du responsable' in histoire.inner_text()
                page.once('dialog', lambda d: d.accept())
                with page.expect_response(lambda r: f'/api/employes/conges/{aid}' in r.url and r.request.method == 'PATCH') as annulation:
                    page.get_by_role('button', name=f'Annuler demande {aid}', exact=True).click()
                assert annulation.value.status == 200
                page.get_by_role('status').get_by_text('Demande annulée ; historique conservé.', exact=True).wait_for()
                assert page.locator('ol li').count() == 3
                assert page.get_by_role('button', name=f'Annuler demande {aid}', exact=True).count() == 0
                # La période libérée accepte une autre demande ; refus traçable.
                ouvrir_demande(page, eid, f'{annee}-11-05', f'{annee}-11-07', 'Nouvelle demande fictive à refuser')
                page.get_by_label('Type de demande', exact=True).select_option('absence')
                with page.expect_response(lambda r: r.url.endswith('/api/employes/conges') and r.request.method == 'POST') as creation2:
                    page.get_by_role('button', name='Enregistrer la demande', exact=True).click()
                assert creation2.value.status == 201
                bid = creation2.value.json()['id']
                page.get_by_role('button', name=f'Refuser demande {bid}', exact=True).click()
                page.get_by_label('Commentaire de décision', exact=True).fill('Refus fictif motivé')
                page.get_by_role('button', name='Confirmer la décision', exact=True).click()
                page.get_by_role('status').get_by_text('Décision enregistrée avec son historique.', exact=True).wait_for()
                page.get_by_label('Filtrer les demandes', exact=True).select_option('refuse')
                assert page.locator('tbody tr').count() == 1 and 'Refusée' in page.locator('tbody').inner_text()
                page.reload(wait_until='domcontentloaded')
                page.get_by_role('button', name='Congés & absences', exact=True).click()
                page.get_by_role('button', name=f'Historique demande {aid}', exact=True).click()
                assert page.locator('ol li').count() == 3
                assert page.get_by_text('Refus fictif motivé', exact=False).count() > 0
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
        with Session(application['engine']) as db:
            assert db.query(models.AbsenceRH).filter_by(societe_id=sid).count() == 2
            assert db.query(models.EvenementAbsenceRH).filter_by(societe_id=sid).count() == 5
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
            assert db.get(models.Employe, eid).salaire_brut == 8000


def test_grh_auteur_comptable_lecture_et_autre_societe_ui(application):
    suffix = uuid.uuid4().hex[:8]
    annee = date.today().year
    with httpx.Client(base_url=application['api_url']) as api:
        admin_email, password = compte(api, suffix)
        response = api.post('/api/employes', json={'nom': 'Salarié droits fictif ' + suffix, 'salaire_brut': 5000})
        assert response.status_code == 201
        eid = response.json()['id']
        identites = {}
        for nom, role in [('auteur', 'comptable'), ('tiers', 'comptable'), ('lecteur', 'lecture')]:
            email = f'{nom}-grh-{suffix}@example.com'
            response = api.post('/api/utilisateurs', json={'nom': nom + ' GRH fictif', 'email': email, 'mot_de_passe': password, 'role': role})
            assert response.status_code == 201, response.text
            identites[nom] = email
        token_auteur = api.post('/api/auth/login', json={'email': identites['auteur'], 'password': password}).json()['access_token']
        response = api.post('/api/employes/conges', headers={'Authorization': 'Bearer ' + token_auteur}, json={'employe_id': eid, 'date_debut': f'{annee}-10-01', 'date_fin': f'{annee}-10-02', 'motif': 'Demande de l’auteur fictif'})
        assert response.status_code == 201, response.text
        aid = response.json()['id']
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=navigateur(), headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], identites['tiers'], password)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_role('button', name='Congés & absences', exact=True).click()
                page.get_by_role('button', name=f'Historique demande {aid}', exact=True).wait_for()
                assert page.get_by_role('button', name=f'Approuver demande {aid}', exact=True).count() == 0
                assert page.get_by_role('button', name=f'Annuler demande {aid}', exact=True).count() == 0
                statut = page.evaluate("async ({url,id}) => (await fetch(url+'/api/employes/conges/'+id,{method:'PATCH',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),'Content-Type':'application/json'},body:JSON.stringify({statut:'approuve'})})).status", {'url': application['api_url'], 'id': aid})
                assert statut == 403
                page.get_by_role('button', name='Déconnexion', exact=True).click()
                connexion(page, application['web_url'], identites['auteur'], password)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_role('button', name='Congés & absences', exact=True).click()
                page.get_by_role('button', name=f'Annuler demande {aid}', exact=True).wait_for()
                assert page.get_by_role('button', name=f'Approuver demande {aid}', exact=True).count() == 0
                page.once('dialog', lambda d: d.accept())
                page.get_by_role('button', name=f'Annuler demande {aid}', exact=True).click()
                page.get_by_role('status').get_by_text('Demande annulée ; historique conservé.', exact=True).wait_for()
                page.get_by_role('button', name='Déconnexion', exact=True).click()
                connexion(page, application['web_url'], identites['lecteur'], password)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_role('button', name='Congés & absences', exact=True).click()
                page.get_by_role('button', name=f'Historique demande {aid}', exact=True).click()
                assert page.locator('ol li').count() == 2
                assert page.get_by_role('button', name='Nouvelle demande', exact=True).count() == 0
                assert page.get_by_role('button', name=f'Annuler demande {aid}', exact=True).count() == 0
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
        with httpx.Client(base_url=application['api_url']) as autre:
            compte(autre, suffix + 'autre')
            assert autre.get('/api/employes/conges').json() == []
            assert autre.patch(f'/api/employes/conges/{aid}', json={'statut': 'annule'}).status_code == 404
