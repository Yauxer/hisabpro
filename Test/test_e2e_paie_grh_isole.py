"""Paie & GRH : vraie UI, vrai FastAPI et cluster PostgreSQL éphémère."""
from datetime import date
from pathlib import Path
import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from postgres_isole import verifier_cible_isolee
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application as application_base


@pytest.fixture(scope="module")
def application(application_base):
    app = application_base
    cible = app['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    with app['engine'].begin() as db:
        db.exec_driver_sql((Path(__file__).resolve().parents[1] / 'hisabpro-backend' / '080_dossiers_employes.sql').read_text(encoding='utf-8'))
    return app


def compte(api, suffix):
    email, password = f'grh-{suffix}@example.com', 'PaieE2E2026!'
    response = api.post('/api/auth/register', json={'nom': 'Admin GRH fictif', 'email': email, 'password': password, 'raison_sociale': f'GRH fictive {suffix}'})
    assert response.status_code == 200, response.text
    api.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return email, password


def navigateur():
    executable = chromium_executable()
    if not executable:
        pytest.skip('Chromium / Edge requis')
    return executable


def test_paie_grh_dossier_crud_periode_et_calcul_absent_ui(application):
    suffix = uuid.uuid4().hex[:8]
    annee = date.today().year
    with httpx.Client(base_url=application['api_url']) as api:
        email, password = compte(api, suffix)
        sid = api.get('/api/societe/moi').json()['id']
        nom = f'LeilaFictive-{suffix}-' + 'NomLongSansEspace' * 6
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=navigateur(), headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_role('heading', name='Paie & GRH', exact=True).wait_for()
                # Les styles du module Délais sont chargés dans le même bundle.
                # Une table étrangère à ce module doit garder sa largeur naturelle.
                fuite = page.evaluate("""() => {
                    const holder = document.createElement('div'); holder.style.width='180px';
                    holder.innerHTML='<table><thead><tr><th>Titre</th></tr></thead><tbody><tr><td>Valeur</td></tr></tbody></table>';
                    document.body.appendChild(holder);
                    try { return {largeur:holder.querySelector('table').getBoundingClientRect().width,
                        entete:getComputedStyle(holder.querySelector('th')).position}; }
                    finally { holder.remove(); }
                }""")
                assert fuite['largeur'] <= 180, fuite
                assert fuite['entete'] != 'sticky', fuite
                page.get_by_role('button', name='Ajouter un salarié', exact=True).click()
                page.get_by_label('Nom complet', exact=False).fill(nom)
                page.get_by_label('Poste', exact=True).fill('Comptable')
                page.get_by_label('Type de contrat', exact=True).select_option('CDI')
                page.get_by_label('Matricule interne', exact=True).fill('GRH-001')
                page.get_by_label('Numéro CNSS', exact=True).fill('000000001')
                page.get_by_label('Date d’embauche', exact=True).fill(f'{annee}-01-01')
                page.get_by_label('Salaire brut mensuel (MAD)', exact=False).fill('10000')
                page.get_by_label('Personnes à charge IR confirmées', exact=True).select_option('0')
                with page.expect_response(lambda r: r.url.endswith('/api/employes') and r.request.method == 'POST') as creation:
                    page.get_by_role('button', name='Enregistrer la fiche', exact=True).click()
                assert creation.value.status == 201, creation.value.text()
                eid = creation.value.json()['id']
                page.get_by_role('status').get_by_text('Fiche salariée enregistrée.', exact=True).wait_for()
                ligne = page.locator('tbody tr').filter(has_text=nom)
                assert ligne.count() == 1
                assert page.locator('table').first.evaluate('(t) => t.parentElement.scrollWidth <= t.parentElement.clientWidth + 1'), 'Le tableau équipe déborde inutilement à 1440 px'
                assert ligne.locator('td').nth(3).inner_text().replace('.', '').replace(' ', '').replace('\u202f', '').replace('\u00a0', '') == '10000,00MAD'
                page.get_by_role('button', name=f'Modifier {nom}', exact=True).click()
                page.get_by_label('Poste', exact=True).fill('Responsable comptable')
                page.get_by_label('Salaire brut mensuel (MAD)', exact=False).fill('12000')
                with page.expect_response(lambda r: f'/api/employes/{eid}' in r.url and r.request.method == 'PUT') as modification:
                    page.get_by_role('button', name='Enregistrer la fiche', exact=True).click()
                assert modification.value.status == 200, modification.value.text()
                page.get_by_role('status').wait_for()
                page.get_by_role('button', name='Préparation mensuelle', exact=True).click()
                with page.expect_response(lambda r: '/api/employes/cotisations?' in r.url and 'mois=2' in r.url) as periode:
                    page.get_by_label('Mois de paie', exact=True).select_option('2')
                calcul = periode.value.json()
                assert periode.value.status == 200, periode.value.text()
                assert calcul['mois'] == 2 and calcul['annee_taux'] == annee and calcul['statut'] == 'bloque'
                assert calcul['totaux'] is None and calcul['employes'][0]['cotisations'] is None
                page.get_by_text('Préparation indisponible : compléter les paramètres et les fiches signalés.', exact=False).wait_for()
                assert page.get_by_role('button', name='Exporter la préparation CSV', exact=True).is_disabled()
                ligne = page.locator('tbody tr').filter(has_text=nom)
                assert ligne.locator('td').all_text_contents()[2:6] == ['—', '—', '—', '—']
                page.get_by_role('button', name=nom, exact=True).click()
                page.get_by_role('heading', name=f'{nom} · Février {annee}', exact=True).wait_for()
                page.get_by_role('button', name='Équipe', exact=True).click()
                page.once('dialog', lambda dialog: dialog.accept())
                with page.expect_response(lambda r: f'/api/employes/{eid}' in r.url and r.request.method == 'DELETE') as archivage:
                    page.get_by_role('button', name=f'Archiver {nom}', exact=True).click()
                assert archivage.value.status == 204
                page.get_by_role('status').get_by_text('Fiche archivée et conservée.', exact=True).wait_for()
                assert page.locator('tbody tr').filter(has_text=nom).count() == 0
                page.get_by_label('Statut des salariés', exact=True).select_option('archives')
                page.get_by_role('button', name=f'Réactiver {nom}', exact=True).wait_for()
                page.once('dialog', lambda dialog: dialog.accept())
                with page.expect_response(lambda r: f'/api/employes/{eid}' in r.url and r.request.method == 'PUT') as restauration:
                    page.get_by_role('button', name=f'Réactiver {nom}', exact=True).click()
                assert restauration.value.status == 200, restauration.value.text()
                page.get_by_label('Statut des salariés', exact=True).select_option('actifs')
                page.get_by_role('button', name=f'Modifier {nom}', exact=True).wait_for()
                page.reload(wait_until='domcontentloaded')
                page.get_by_role('button', name=f'Modifier {nom}', exact=True).wait_for()
                assert 'Responsable comptable' in page.locator('tbody tr').filter(has_text=nom).inner_text()
                # Largeur mobile : formulaire utilisable et défilement vertical réel.
                page.set_viewport_size({'width': 720, 'height': 700})
                assert page.locator('table').first.evaluate('(t) => getComputedStyle(t.parentElement).overflowX === "auto"')
                assert page.locator('table').first.evaluate('(t) => t.parentElement.scrollWidth > t.parentElement.clientWidth')
                page.get_by_role('button', name=f'Archiver {nom}', exact=True).scroll_into_view_if_needed()
                assert page.get_by_role('button', name=f'Archiver {nom}', exact=True).is_visible()
                assert page.locator('table').first.evaluate('(t) => t.parentElement.scrollLeft > 0'), 'Actions accessibles en faisant défiler le tableau mobile'
                page.get_by_role('button', name=f'Modifier {nom}', exact=True).click()
                page.get_by_label('Téléphone', exact=True).fill('0600000000')
                page.get_by_role('button', name='Annuler', exact=True).click()
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()
        with Session(application['engine']) as db:
            employe = db.get(models.Employe, eid)
            assert employe.actif and employe.salaire_brut == 12000 and employe.poste == 'Responsable comptable'
            assert employe.numero_cnss == '000000001' and employe.personnes_charge_ir == 0
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
            assert db.query(models.LigneEcriture).join(models.Ecriture).filter(models.Ecriture.societe_id == sid).count() == 0


def test_paie_grh_lecture_et_isolation_societes_ui(application):
    suffix = uuid.uuid4().hex[:8]
    with httpx.Client(base_url=application['api_url']) as api:
        email_admin, password = compte(api, suffix)
        response = api.post('/api/employes', json={'nom': 'Salarié privé A ' + suffix, 'salaire_brut': 5000, 'personnes_charge_ir': 0})
        assert response.status_code == 201, response.text
        eid = response.json()['id']
        email = 'lecture-grh-' + suffix + '@example.com'
        response = api.post('/api/utilisateurs', json={'nom': 'Lecture GRH fictive', 'email': email, 'mot_de_passe': password, 'role': 'lecture'})
        assert response.status_code == 201, response.text
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=navigateur(), headless=True)
            try:
                page = browser.new_page()
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_text('Salarié privé A ' + suffix, exact=True).wait_for()
                assert page.get_by_role('button', name='Ajouter un salarié', exact=True).count() == 0
                assert page.get_by_role('button', name='Modifier Salarié privé A ' + suffix, exact=True).count() == 0
                page.get_by_role('button', name='Consulter Salarié privé A ' + suffix, exact=True).click()
                assert page.get_by_label('Salaire brut mensuel (MAD)', exact=False).is_disabled()
                assert page.get_by_role('button', name='Enregistrer la fiche', exact=True).count() == 0
                page.get_by_role('button', name='Fermer la fiche', exact=True).click()
                statut = page.evaluate("async ({url,id}) => (await fetch(url+'/api/employes/'+id,{method:'DELETE',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token')}})).status", {'url': application['api_url'], 'id': eid})
                assert statut == 403
                page.get_by_role('button', name='Déconnexion', exact=True).click()
                # Une autre société indépendante ne voit aucun dossier de A.
                with httpx.Client(base_url=application['api_url']) as api_b:
                    email_b, password_b = compte(api_b, suffix + 'b')
                    assert api_b.get('/api/employes?inclure_archives=true').json() == []
                    assert api_b.delete(f'/api/employes/{eid}').status_code == 404
                connexion(page, application['web_url'], email_b, password_b)
                page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                page.get_by_text('Aucun salarié dans cette sélection.', exact=True).wait_for()
                assert page.get_by_text('Salarié privé A ' + suffix, exact=True).count() == 0
                assert not errors, errors
                assert not server_errors, server_errors
            finally:
                browser.close()


def test_paie_simulation_export_csv_reference_fictive(application):
    # Référentiel volontairement fictif de laboratoire ; aucun taux marocain
    # n'est déclaré validé par cet oracle mathématique indépendant.
    suffix = uuid.uuid4().hex[:8]
    annee = date.today().year
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    ids_taux, ids_bareme, ids_deductions = [], [], []
    with Session(application['engine']) as db:
        assert db.query(models.TauxCotisation).filter_by(annee=annee).count() == 0
        assert db.query(models.BaremeIR).filter_by(annee=annee).count() == 0
        assert db.query(models.DeductionIR).filter_by(annee=annee).count() == 0
        taux = [models.TauxCotisation(annee=annee, code=code, libelle='Laboratoire fictif ' + code,
                    taux_sal=sal, taux_pat=pat, plafond=None) for code, sal, pat in [
                    ('cnss_retraite', .04, .08), ('cnss_prest_fam', 0, .05),
                    ('amo', .02, .02), ('amo_participation', 0, .01), ('formation_prof', 0, .01)]]
        bareme = models.BaremeIR(annee=annee, tranche_min=0, tranche_max=None, taux=0, deduction=0)
        reduction = models.DeductionIR(annee=annee, code='enfant', libelle='Réduction fictive nulle', montant_an=0, max_beneficiaires=6)
        db.add_all([*taux, bareme, reduction]); db.commit()
        ids_taux = [t.id for t in taux]; ids_bareme = [bareme.id]; ids_deductions = [reduction.id]
    try:
        with httpx.Client(base_url=application['api_url']) as api:
            email, password = compte(api, suffix + 'sim')
            response = api.post('/api/exercices', json={'annee': annee + 1, 'date_debut': f'{annee + 1}-01-01', 'date_fin': f'{annee + 1}-12-31'})
            assert response.status_code in (200, 201), response.text
            nom = '=Salarié fictif ' + suffix
            response = api.post('/api/employes', json={'nom': nom, 'salaire_brut': 10000, 'matricule': '+GRH-FICTIF', 'personnes_charge_ir': 0, 'date_embauche': f'{annee}-01-01'})
            assert response.status_code == 201, response.text
            eid = response.json()['id']
            assert response.json()['type_contrat'] is None
            playwright = pytest.importorskip('playwright.sync_api')
            with playwright.sync_playwright() as p:
                browser = p.chromium.launch(executable_path=navigateur(), headless=True)
                try:
                    page = browser.new_page()
                    page.set_default_timeout(20000)
                    errors, server_errors = observer(page, application['api_url'])
                    connexion(page, application['web_url'], email, password)
                    page.goto(application['web_url'] + '/cnss', wait_until='domcontentloaded')
                    page.get_by_role('button', name=f'Modifier {nom}', exact=True).wait_for()
                    page.get_by_role('button', name='Préparation mensuelle', exact=True).click()
                    with page.expect_response(lambda r: '/api/employes/cotisations?' in r.url and 'mois=3' in r.url) as simulation:
                        page.get_by_label('Mois de paie', exact=True).select_option('3')
                    data = simulation.value.json()
                    assert simulation.value.status == 200 and data['statut'] == 'simulation'
                    assert data['totaux'] == {'salaire_brut': 10000, 'total_retenues_sal': 600, 'ir': 0, 'salaire_net': 9400, 'total_charges_pat': 1700, 'cout_employeur': 11700}
                    page.get_by_text('Simulation disponible', exact=False).wait_for()
                    assert not page.get_by_role('button', name='Exporter la préparation CSV', exact=True).is_disabled()
                    ligne = page.locator('tbody tr').filter(has_text=nom)
                    valeurs = [v.replace('.', '').replace(' ', '').replace('\u202f', '').replace('\u00a0', '') for v in ligne.locator('td').all_text_contents()]
                    assert valeurs[1:6] == ['10000,00', '600,00', '0,00', '9400,00', '1700,00']
                    with page.expect_download() as export:
                        page.get_by_role('button', name='Exporter la préparation CSV', exact=True).click()
                    download = export.value
                    assert download.suggested_filename == f'preparation-paie-{annee}-03.csv'
                    contenu = Path(download.path()).read_text(encoding='utf-8-sig')
                    assert 'Préparation de paie — simulation' in contenu and f'Mars {annee}' in contenu
                    assert f'"\'{nom}"' in contenu and '"\'+GRH-FICTIF"' in contenu
                    assert '"10000";"600";"0";"9400";"1700";"11700"' in contenu
                    page.get_by_role('button', name=nom, exact=True).click()
                    page.get_by_role('heading', name=f'{nom} · Mars {annee}', exact=True).wait_for()
                    assert '82.800,00 MAD' in page.locator('body').inner_text()
                    # Poste optionnel null : édition et réactivation doivent rester possibles.
                    page.get_by_role('button', name='Équipe', exact=True).click()
                    page.get_by_role('button', name=f'Modifier {nom}', exact=True).click()
                    assert page.get_by_label('Poste', exact=True).input_value() == ''
                    assert page.get_by_label('Type de contrat', exact=True).input_value() == ''
                    page.get_by_role('button', name='Enregistrer la fiche', exact=True).click()
                    page.get_by_role('status').get_by_text('Fiche salariée enregistrée.', exact=True).wait_for()
                    assert api.get('/api/employes?inclure_archives=true').json()[0]['type_contrat'] is None
                    page.once('dialog', lambda d: d.accept())
                    page.get_by_role('button', name=f'Archiver {nom}', exact=True).click()
                    page.get_by_role('status').get_by_text('Fiche archivée et conservée.', exact=True).wait_for()
                    page.get_by_label('Statut des salariés', exact=True).select_option('archives')
                    page.once('dialog', lambda d: d.accept())
                    page.get_by_role('button', name=f'Réactiver {nom}', exact=True).click()
                    page.get_by_role('status').get_by_text('Fiche réactivée.', exact=True).wait_for()
                    assert api.get('/api/employes?inclure_archives=true').json()[0]['id'] == eid
                    assert api.get('/api/employes?inclure_archives=true').json()[0]['type_contrat'] is None
                    page.get_by_role('button', name='Préparation mensuelle', exact=True).click()
                    with page.expect_response(lambda r: '/api/employes/cotisations?' in r.url and f'annee={annee + 1}' in r.url) as autre_annee:
                        page.get_by_label('Année de paie', exact=True).select_option(str(annee + 1))
                    assert autre_annee.value.status == 200 and autre_annee.value.json()['statut'] == 'bloque'
                    page.get_by_text('Préparation indisponible : compléter les paramètres et les fiches signalés.', exact=False).wait_for()
                    assert page.get_by_role('button', name='Exporter la préparation CSV', exact=True).is_disabled()
                    assert not errors, errors
                    assert not server_errors, server_errors
                finally:
                    browser.close()
    finally:
        verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        with Session(application['engine']) as db:
            db.query(models.TauxCotisation).filter(models.TauxCotisation.id.in_(ids_taux)).delete(synchronize_session=False)
            db.query(models.BaremeIR).filter(models.BaremeIR.id.in_(ids_bareme)).delete(synchronize_session=False)
            db.query(models.DeductionIR).filter(models.DeductionIR.id.in_(ids_deductions)).delete(synchronize_session=False)
            db.commit()
