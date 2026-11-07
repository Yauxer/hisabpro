"""Préfixe et modèle de libellé distincts : vrais paramètres/écritures/UI."""
from datetime import date
import uuid

import httpx
import pytest
from sqlalchemy import text

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


def instantane(application, fid, eid):
    with application['engine'].connect() as db:
        return {
            'facture': db.execute(text('SELECT row_to_json(t)::text FROM factures t WHERE id=:id'), {'id': fid}).scalar_one(),
            'ecriture': db.execute(text('SELECT row_to_json(t)::text FROM ecritures t WHERE id=:id'), {'id': eid}).scalar_one(),
            'lignes': db.execute(text('SELECT row_to_json(t)::text FROM lignes_ecriture t WHERE ecriture_id=:id ORDER BY id'), {'id': eid}).scalars().all(),
        }


def sequence(application, sid):
    with application['engine'].connect() as db:
        return db.execute(text('SELECT row_to_json(t)::text FROM facturation_sequences t WHERE societe_id=:sid ORDER BY exercice,type_doc'), {'sid': sid}).scalars().all()


def facture_comptabilisee(api, annee, tiers, ref):
    r = api.post('/api/factures', json={'type': 'vente', 'date': f'{annee}-03-15',
        'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'reference': ref,
        'lignes': [{'description': 'Prestation fictive paramètres', 'quantite': 1, 'prix_unitaire': 100, 'tva': 20}]})
    assert r.status_code == 201, r.text
    fid = r.json()['id']
    r = api.post(f'/api/factures/{fid}/valider')
    assert r.status_code == 200, r.text
    r = api.post(f'/api/factures/{fid}/comptabiliser')
    assert r.status_code == 200, r.text
    eid = r.json()['ecriture_id']
    r = api.post(f'/api/ecritures/{eid}/valider')
    assert r.status_code == 200, r.text
    factures = api.get('/api/factures', params={'exercice': annee})
    ecriture = api.get(f'/api/ecritures/{eid}')
    assert factures.status_code == ecriture.status_code == 200, (factures.text, ecriture.text)
    facture = next(f for f in factures.json() if f['id'] == fid)
    return fid, eid, facture, ecriture.json()


def enregistrer(page, api, champ_nom, valeur):
    attendu = 'prefixe_facture' if champ_nom == 'Préfixe Factures' else 'format_libelle_vente'
    with page.expect_response(lambda r: r.url.endswith('/api/societe/moi') and r.request.method == 'PATCH') as reponse:
        champ(page, champ_nom).fill(valeur)
        page.get_by_role('button', name='Enregistrer', exact=True).click()
    assert reponse.value.status == 200, reponse.value.text()
    assert reponse.value.request.post_data_json[attendu] == valeur, reponse.value.request.post_data_json
    page.get_by_text('Enregistré', exact=True).wait_for()
    assert api.get('/api/societe/moi').json()[attendu] == valeur


def test_prefixe_modele_libelle_journal_et_immutabilite(application, tmp_path):
    suffixe = uuid.uuid4().hex[:10]
    email, password, annee = suffixe+'@example.com', 'LibellePrefixe2026!', date.today().year
    with httpx.Client(base_url=application['api_url'], timeout=30) as api:
        r = api.post('/api/auth/register', json={'nom': 'Admin fictif', 'email': email,
            'password': password, 'raison_sociale': 'Libellés fictifs '+suffixe})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer '+r.json()['access_token']
        # Modèle littéral choisi explicitement pour reproduire la configuration
        # FA° décrite par l'utilisateur, sans toucher une société existante.
        r = api.patch('/api/societe/moi', json={'format_libelle_vente': 'FA° {numero} {tiers}'})
        assert r.status_code == 200, r.text
        sid = r.json()['id']
        r = api.post('/api/tiers', json={'nom': 'CLIENT LIBELLÉ FICTIF', 'type': 'client'})
        assert r.status_code == 201, r.text
        tiers = r.json()
        fid0, eid0, f0, e0 = facture_comptabilisee(api, annee, tiers, 'REF-INITIAL')
        assert f0['numero'] == f'FA-{annee}-001'
        assert e0['libelle'] == f"FA° {f0['numero']} {tiers['nom']}"
        original = instantane(application, fid0, eid0)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable: pytest.skip('Chromium/Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(20000)
                errors, server = observer(page, application['api_url'])
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url']+'/parametres', wait_until='domcontentloaded')
                champ(page, 'Préfixe Factures').wait_for()
                playwright.expect(champ(page, 'Raison sociale *')).to_have_value('Libellés fictifs '+suffixe)
                avant_sequence = sequence(application, sid)
                enregistrer(page, api, 'Préfixe Factures', 'VTE')
                assert sequence(application, sid) == avant_sequence
                assert instantane(application, fid0, eid0) == original
                # Exemple contextuel, distinct du numéro réellement attribué.
                page.get_by_role('button', name='Fiscalité', exact=True).click()
                apercu = champ(page, 'Facture de vente').locator('..').get_by_text('Aperçu (exemple) :', exact=False).inner_text()
                print('Aperçu illustratif actuel après préfixe VTE :', apercu)
                assert f'FA° VTE-{annee}-014' in apercu
                fid1, eid1, f1, e1 = facture_comptabilisee(api, annee, tiers, 'REF-PREFIXE')
                assert f1['numero'] == f'VTE-{annee}-002'
                assert e1['libelle'] == f"FA° {f1['numero']} {tiers['nom']}"
                prefixe_seul = instantane(application, fid1, eid1)
                modele = 'VENTE {numero} / {tiers} / {ref} / {date}'
                avant_sequence = sequence(application, sid)
                enregistrer(page, api, 'Facture de vente', modele)
                assert sequence(application, sid) == avant_sequence
                assert instantane(application, fid0, eid0) == original
                assert instantane(application, fid1, eid1) == prefixe_seul
                fid2, eid2, f2, e2 = facture_comptabilisee(api, annee, tiers, 'REF-MODELE')
                assert f2['numero'] == f'VTE-{annee}-003'
                assert e2['libelle'] == f"VENTE {f2['numero']} / {tiers['nom']} / REF-MODELE / 15/03/{annee}"
                derniere = instantane(application, fid2, eid2)
                for f, e in ((f0, e0), (f1, e1), (f2, e2)):
                    assert f['total_ht'] == 100 and f['total_tva'] == 20 and f['total_ttc'] == 120
                    assert sum(l['debit'] for l in e['lignes']) == sum(l['credit'] for l in e['lignes']) == 120
                page.goto(application['web_url']+'/journal', wait_until='domcontentloaded')
                page.get_by_text('CLIENT LIBELLÉ FICTIF', exact=False).first.wait_for()
                with page.expect_download() as telechargement:
                    page.get_by_role('button', name='Exporter CSV', exact=True).click()
                fichier = tmp_path/'journal-avant.csv'
                telechargement.value.save_as(fichier)
                contenu = fichier.read_text(encoding='utf-8-sig')
                for e in (e0, e1, e2): assert e['libelle'] in contenu
                page.goto(application['web_url']+'/parametres', wait_until='domcontentloaded')
                playwright.expect(champ(page, 'Raison sociale *')).to_have_value('Libellés fictifs '+suffixe)
                page.get_by_role('button', name='Fiscalité', exact=True).click()
                enregistrer(page, api, 'Facture de vente', 'NOUVEAU {numero}')
                assert instantane(application, fid0, eid0) == original
                assert instantane(application, fid1, eid1) == prefixe_seul
                assert instantane(application, fid2, eid2) == derniere
                page.goto(application['web_url']+'/journal', wait_until='domcontentloaded')
                page.get_by_text('CLIENT LIBELLÉ FICTIF', exact=False).first.wait_for()
                with page.expect_download() as telechargement:
                    page.get_by_role('button', name='Exporter CSV', exact=True).click()
                fichier = tmp_path/'journal-apres.csv'
                telechargement.value.save_as(fichier)
                assert fichier.read_text(encoding='utf-8-sig') == contenu
                assert not errors and not server, (errors, server)
            finally:
                browser.close()
