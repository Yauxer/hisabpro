"""Traçabilité documentaire, sans valider de paie : Edge / API / PG isolé."""
from copy import deepcopy
from datetime import date
from pathlib import Path
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application as application_base
from test_e2e_paie_grh_isole import compte, navigateur
from test_e2e_administration_isole import connexion, observer, deconnexion


@pytest.fixture(scope='module')
def application(application_base):
    app = application_base
    cible = app['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    with app['engine'].begin() as db:
        db.exec_driver_sql((Path(__file__).resolve().parents[1] / 'hisabpro-backend' / '080_dossiers_employes.sql').read_text(encoding='utf-8'))
        db.exec_driver_sql((Path(__file__).resolve().parents[1] / 'hisabpro-backend' / '082_paie_referentiels.sql').read_text(encoding='utf-8'))
    # Une seule rubrique volontairement incomplète de laboratoire permet
    # d'exercer PATCH sans pouvoir débloquer une simulation de paie.
    with Session(app['engine']) as db:
        taux = models.TauxCotisation(annee=date.today().year, code='preuve_ui_fictive', libelle='Taux fictif de laboratoire', taux_sal=.01, taux_pat=.02)
        db.add(taux); db.commit(); app['taux_fictif_id'] = taux.id
    return app


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def ouvrir_paie(page, app):
    page.goto(app['web_url'] + '/cnss')
    page.get_by_role('button', name='Préparation mensuelle', exact=True).click()
    carte = page.get_by_role('region', name='Traçabilité annuelle du référentiel', exact=True)
    carte.get_by_role('button', name='Consigner une preuve', exact=True).wait_for()
    return carte


def remplir_preuve(carte, titre):
    carte.get_by_role('button', name='Consigner une preuve', exact=True).click()
    form = carte.get_by_role('form', name='Consigner une preuve documentaire', exact=True)
    form.get_by_label('Titre du document', exact=False).fill(titre)
    form.get_by_label('Article / référence', exact=True).fill('Document fictif de recette UI')
    form.get_by_label('Périmètre documenté', exact=True).fill('Traçabilité seulement, aucun taux marocain validé')
    form.get_by_label('Limites de la preuve', exact=True).fill('Document fictif sans source officielle ; paie non autorisée')
    return form


@pytest.mark.parametrize('largeur', [1440, 390])
def test_referentiel_documentaire_versions_permissions_et_scope_reels(application, largeur):
    suffix = uuid.uuid4().hex[:8]
    annee = date.today().year
    with httpx.Client(base_url=application['api_url']) as api:
        email, password = compte(api, suffix)
        company = ok(api.get('/api/societe/moi'))
        sid = company['id']
        ok(api.post('/api/exercices', json={'annee': annee + 1, 'date_debut': f'{annee+1}-01-01', 'date_fin': f'{annee+1}-12-31'}), 201)
        initial = ok(api.get(f'/api/employes/referentiel?annee={annee}'))
        assert initial['statut'] == 'non_verifie' and initial['version_courante'] is None
        assert initial['peut_consigner'] and initial['paie_definitive_autorisee'] is False
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=navigateur(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(15000)
                errors, server_errors = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                carte = ouvrir_paie(page, application)
                playwright.expect(carte.get_by_text('Non vérifié', exact=True)).to_be_visible()
                form = remplir_preuve(carte, 'Preuve fictive A ' + suffix)
                assert form.locator('input[type="number"]').count() == 0
                with page.expect_response(lambda r: '/api/employes/referentiel?' in r.url and r.request.method == 'POST') as consignation:
                    form.get_by_role('button', name='Enregistrer la preuve', exact=True).click()
                assert consignation.value.status == 201, consignation.value.text()
                premiere = consignation.value.json()
                assert premiere['statut'] == 'preuves_partielles' and premiere['paie_definitive_autorisee'] is False
                snapshot = deepcopy(premiere['version_courante'])
                assert snapshot['created_at'][:10] == date.today().isoformat()
                assert snapshot['sources'][0]['url'] is None
                assert snapshot['sources'][0]['date_effet'] is None and snapshot['sources'][0]['date_consultation'] is None
                playwright.expect(carte.get_by_text('Preuves partielles', exact=True)).to_be_visible()
                carte.get_by_text('Preuve fictive A ' + suffix, exact=True).wait_for()
                assert page.get_by_role('button', name='Exporter la préparation CSV', exact=True).is_disabled()
                dimensions = carte.evaluate("""e => ({largeur:e.clientWidth,contenu:e.scrollWidth,
                  elements:[...e.querySelectorAll('*')].filter(n=>n.scrollWidth>n.clientWidth+1).map(n=>({tag:n.tagName,classe:n.className,largeur:n.clientWidth,contenu:n.scrollWidth,texte:n.innerText?.slice(0,100)}))})""")
                assert dimensions['contenu'] <= dimensions['largeur'] + 1, dimensions
                taux = ok(api.get(f'/api/parametres/taux-cotisations/{annee}'))
                actuel = next(t for t in taux if t['id'] == application['taux_fictif_id'])
                ok(api.patch(f'/api/parametres/taux-cotisations/{actuel["id"]}', json={'taux_sal': actuel['taux_sal'] + .001}))
                page.get_by_role('button', name='Actualiser', exact=True).click()
                carte.get_by_text('Périmé', exact=True).wait_for()
                apres = ok(api.get(f'/api/employes/referentiel?annee={annee}'))
                assert apres['version_courante'] == snapshot and apres['statut'] == 'perime'
                assert apres['empreinte_actuelle'] != snapshot['empreinte']
                # Retenir une vraie réponse POST après commit, changer d'année,
                # puis la libérer : ni le formulaire ni le succès A ne fuitent.
                retenue = []
                def retarder(route):
                    reponse = route.fetch()
                    assert reponse.status == 201, reponse.text()
                    retenue.append((route, reponse))
                    page.evaluate('window.__preuvePostRetenue = true')
                page.route('**/api/employes/referentiel?*', lambda route: retarder(route) if route.request.method == 'POST' else route.continue_())
                form = remplir_preuve(carte, 'Preuve fictive A suivante ' + suffix)
                form.get_by_role('button', name='Enregistrer la preuve', exact=True).click()
                page.wait_for_function('window.__preuvePostRetenue === true')
                page.get_by_label('Année de paie', exact=True).select_option(str(annee + 1))
                carte.get_by_text('Non vérifié', exact=True).wait_for()
                playwright.expect(carte.get_by_role('form')).to_have_count(0)
                route, reponse = retenue[0]
                with page.expect_response(lambda r: '/api/employes/referentiel?' in r.url and r.request.method == 'POST'):
                    route.fulfill(response=reponse)
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                playwright.expect(carte.get_by_text('Non vérifié', exact=True)).to_be_visible()
                playwright.expect(carte.get_by_text('Preuve fictive A suivante ' + suffix, exact=True)).to_have_count(0)
                playwright.expect(carte.get_by_role('status')).to_have_count(0)
                page.unroute('**/api/employes/referentiel?*')
                vieux_payload = {'empreinte_attendue': apres['empreinte_actuelle'], 'sources': snapshot['sources']}
                assert api.post(f'/api/employes/referentiel?annee={annee+1}', json=vieux_payload).status_code == 409
                page.get_by_label('Année de paie', exact=True).select_option(str(annee))
                carte.get_by_text('Preuve fictive A suivante ' + suffix, exact=True).wait_for()
                carte.locator('summary').filter(has_text='Historique documentaire').click()
                carte.get_by_text('Preuve fictive A ' + suffix, exact=True).wait_for()
                histoire = ok(api.get(f'/api/employes/referentiel?annee={annee}'))
                assert next(v for v in histoire['historique'] if v['id'] == snapshot['id']) == snapshot
                # Même preuve de concurrence pour le chargement GET annuel :
                # le corps HTTP historique reste celui du serveur réel.
                get_retenu = []
                def retarder_get(route):
                    if route.request.method == 'GET' and f'annee={annee}' in route.request.url:
                        reponse = route.fetch()
                        assert reponse.status == 200, reponse.text()
                        assert reponse.json()['version_courante']['id'] == histoire['version_courante']['id']
                        get_retenu.append((route, reponse))
                        page.evaluate('window.__referentielGetRetenu = true')
                    else:
                        route.continue_()
                page.route('**/api/employes/referentiel?*', retarder_get)
                page.get_by_role('button', name='Actualiser', exact=True).click()
                page.wait_for_function('window.__referentielGetRetenu === true')
                page.get_by_label('Année de paie', exact=True).select_option(str(annee + 1))
                carte.get_by_text('Non vérifié', exact=True).wait_for()
                route, reponse = get_retenu[0]
                with page.expect_response(lambda r: '/api/employes/referentiel?' in r.url and f'annee={annee}' in r.url and r.request.method == 'GET'):
                    route.fulfill(response=reponse)
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                playwright.expect(carte.get_by_text('Non vérifié', exact=True)).to_be_visible()
                playwright.expect(carte.get_by_text('Preuve fictive A suivante ' + suffix, exact=True)).to_have_count(0)
                assert page.get_by_label('Année de paie', exact=True).input_value() == str(annee + 1)
                page.unroute('**/api/employes/referentiel?*')
                page.get_by_label('Année de paie', exact=True).select_option(str(annee))
                carte.get_by_text('Preuve fictive A suivante ' + suffix, exact=True).wait_for()
                # Société B de même administrateur : contexte réel et hash distinct.
                page.get_by_role('button', name=company['raison_sociale'], exact=True).click()
                page.get_by_role('button', name='Nouvelle société', exact=True).click()
                nom_b = 'GRH preuve B ' + suffix
                page.get_by_placeholder('Raison sociale *').fill(nom_b)
                page.get_by_role('button', name='Créer', exact=True).click()
                page.get_by_role('button', name=nom_b, exact=True).wait_for()
                carte = ouvrir_paie(page, application)
                playwright.expect(carte.get_by_text('Non vérifié', exact=True)).to_be_visible()
                assert 'Preuve fictive A ' + suffix not in carte.inner_text()
                resultat_b = page.evaluate("async ({url,annee,payload}) => {const r=await fetch(url+'/api/employes/referentiel?annee='+annee,{method:'POST',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),'Content-Type':'application/json'},body:JSON.stringify(payload)});return r.status}", {'url': application['api_url'], 'annee': annee, 'payload': vieux_payload})
                assert resultat_b == 409
                # Lecteur A : permissions GET réelles, bouton absent, POST refusé.
                email_lecture = f'preuve-lecture-{suffix}@example.com'
                ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur preuves', 'email': email_lecture, 'mot_de_passe': password, 'role': 'lecture'}), 201)
                deconnexion(page)
                connexion(page, application['web_url'], email_lecture, password)
                page.goto(application['web_url'] + '/cnss')
                page.get_by_role('button', name='Préparation mensuelle', exact=True).click()
                carte = page.get_by_role('region', name='Traçabilité annuelle du référentiel')
                carte.get_by_text('Preuve fictive A suivante ' + suffix, exact=True).wait_for()
                playwright.expect(carte.get_by_role('button', name='Consigner une preuve', exact=True)).to_have_count(0)
                refuse = page.evaluate("async ({url,annee,payload}) => (await fetch(url+'/api/employes/referentiel?annee='+annee,{method:'POST',headers:{Authorization:'Bearer '+localStorage.getItem('hisabpro_token'),'Content-Type':'application/json'},body:JSON.stringify(payload)})).status", {'url': application['api_url'], 'annee': annee, 'payload': vieux_payload})
                assert refuse == 403
                assert not errors, errors
                assert not server_errors, server_errors
            except Exception:
                print('Écran preuve fictive :', page.url, page.locator('body').inner_text()[:8000])
                print('Erreurs :', errors, server_errors)
                raise
            finally:
                browser.close()
        with Session(application['engine']) as db:
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0
