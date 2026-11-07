"""Délai paramétré du tiers : vrais Edge/API/PostgreSQL isolés, lecture seule."""
from datetime import date
import uuid
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def photographie(application):
    with application['engine'].connect() as db:
        return {table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
                for table in ['tiers', 'ecritures', 'lignes_ecriture']}


@pytest.mark.parametrize('largeur', [1365, 390])
def test_delai_tiers_combine_roles_recherche_activite_et_scopes(application, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = suffix+'@example.com', 'DelaiTiersFictif2026!'
    with httpx.Client(base_url=application['api_url']) as api:
        admin = ok(api.post('/api/auth/register', json={'nom': 'Admin fictif', 'email': email,
            'password': password, 'raison_sociale': 'Délais fictifs A '+suffix}))
        api.headers['Authorization'] = 'Bearer '+admin['access_token']
        societe = ok(api.get('/api/societe/moi'))
        annee = date.today().year
        ok(api.post('/api/exercices', json={'annee': annee+1,
            'date_debut': f'{annee+1}-01-01', 'date_fin': f'{annee+1}-12-31'}), 201)
        donnees = [('C0','client',0), ('C1','client',1), ('F30','fournisseur',30),
                   ('D31','les_deux',31), ('F60','fournisseur',60), ('C61','client',61),
                   ('NUL','les_deux',None)]
        for nom, role, delai in donnees:
            ok(api.post('/api/tiers', json={'nom': nom+' fictif', 'type': role,
                'ville': 'Cas délai '+nom, 'delai_paiement': delai}), 201)
        # Pagination réelle, exclusivement dans le laboratoire nonce, avant photographie.
        with Session(application['engine']) as db:
            # Le défaut ORM applique 60 à la création API avec None. Le NULL
            # historique demandé est préparé explicitement, seulement ici.
            db.query(models.Tiers).filter_by(societe_id=societe['id'], nom='NUL fictif').update({'delai_paiement': None})
            db.add_all([models.Tiers(societe_id=societe['id'], nom=f'ZZ délai fictif {i:03d}',
                        type='client', delai_paiement=90) for i in range(195)])
            db.commit()
        nom_b = 'Délais fictifs B '+suffix
        bid = ok(api.post('/api/societes/nouvelle', json={'raison_sociale': nom_b}), 201)['id']
        jeton_b = ok(api.post(f'/api/societes/switcher/{bid}'))['access_token']
        with httpx.Client(base_url=application['api_url'], headers={'Authorization': 'Bearer '+jeton_b}) as autre:
            ok(autre.post('/api/tiers', json={'nom': 'B seulement fictif', 'type': 'fournisseur',
                'delai_paiement': 0}), 201)
        avant = photographie(application)
        pw = pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                erreurs, serveur = observer(page, application['api_url'])
                mutations, lectures = [], []
                page.on('request', lambda r: mutations.append((r.method, r.url))
                        if '/api/tiers' in r.url and r.method != 'GET' else None)
                page.on('request', lambda r: lectures.append(r.url) if '/api/tiers?' in r.url else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/tiers')
                rows = page.locator('tbody tr')
                pw.expect(rows).to_have_count(202)
                assert any('skip=200' in url for url in lectures), lectures
                filtre = page.get_by_role('combobox', name='Délai de paiement', exact=True)
                recherche = page.get_by_placeholder('Rechercher nom, ICE, ville...')

                def visibles(noms):
                    pw.expect(rows).to_have_count(len(noms))
                    assert set(rows.locator('td:first-child').all_text_contents()) == set(noms)

                filtre.select_option('comptant'); visibles(['C0 fictif'])
                filtre.select_option('1_30'); visibles(['C1 fictif', 'F30 fictif'])
                page.get_by_role('button', name='Clients', exact=True).click(); visibles(['C1 fictif'])
                page.get_by_role('button', name='Fournisseurs', exact=True).click(); visibles(['F30 fictif'])
                page.get_by_role('button', name='Tous', exact=True).click()
                filtre.select_option('31_60'); visibles(['D31 fictif', 'F60 fictif'])
                page.get_by_role('button', name='Clients', exact=True).click(); visibles(['D31 fictif'])
                page.get_by_role('button', name='Fournisseurs', exact=True).click(); visibles(['D31 fictif', 'F60 fictif'])
                page.get_by_role('button', name='Clients & Fournis.', exact=True).click(); visibles(['D31 fictif'])
                page.get_by_role('button', name='Tous', exact=True).click()
                recherche.fill('Cas délai F60'); visibles(['F60 fictif'])
                recherche.fill('')
                dormant = page.get_by_role('button', name='Sans mouvement (> 90 j)', exact=True)
                pw.expect(dormant).to_be_enabled(); dormant.click(); visibles(['D31 fictif', 'F60 fictif'])
                page.get_by_role('button', name='Avec impayés', exact=True).click(); visibles([])
                page.get_by_role('button', name='Toute activité', exact=True).click()
                filtre.select_option('a_verifier'); visibles(['NUL fictif'])
                filtre.select_option('plus_60'); pw.expect(rows).to_have_count(196)
                recherche.fill('C61'); visibles(['C61 fictif'])
                recherche.fill(''); filtre.select_option('TOUS'); pw.expect(rows).to_have_count(202)
                filtre.select_option('a_verifier')
                exercice = page.locator('select').filter(has=page.locator(f'option[value="{annee+1}"]')).first
                exercice.select_option(str(annee+1))
                pw.expect(filtre).to_have_value('a_verifier'); visibles(['NUL fictif'])
                pw.expect(dormant).to_be_enabled()
                page.get_by_role('button', name=societe['raison_sociale'], exact=True).click()
                with page.expect_response(lambda r: r.url.endswith(f'/api/societes/switcher/{bid}')):
                    page.get_by_text(nom_b, exact=True).click()
                page.get_by_role('button', name=nom_b, exact=True).wait_for()
                pw.expect(filtre).to_have_value('TOUS'); visibles(['B seulement fictif'])
                filtre.select_option('comptant'); visibles(['B seulement fictif'])
                filtre.select_option('a_verifier'); visibles([])
                assert mutations == []
                assert not erreurs and not serveur, (erreurs, serveur)
            finally:
                browser.close()
        assert photographie(application) == avant
