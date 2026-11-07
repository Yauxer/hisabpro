"""RAS calculée existante : sortie API, historique invalide et éditeur réel."""
from datetime import date
from contextlib import closing
import math
import uuid
import httpx
import pytest
from sqlalchemy.orm import Session
import models
from test_ras_taux_finis import facture
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import connexion
from browser_support import chromium_executable


def client(application):
    suffix = uuid.uuid4().hex[:8]
    email, password = suffix + '@example.com', 'RasLecture2026!'
    api = httpx.Client(base_url=application['api_url'])
    r = api.post('/api/auth/register', json={'nom':'Admin fictif','email':email,
                 'password':password,'raison_sociale':'RAS lecture fictive '+suffix})
    assert r.status_code == 200, r.text
    api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
    return api, email, password


def lire(api, fid):
    r = api.get('/api/factures', params={'exercice': date.today().year})
    assert r.status_code == 200, r.text
    return next(f for f in r.json() if f['id'] == fid)


def verifier_ras(f):
    assert f['ras_taux'] == 10
    assert f['montant_ras'] == 100
    assert f['net_a_payer'] == 1100
    assert f['ras_anomalie'] is None
    assert (f['total_ht'],f['total_tva'],f['total_ttc']) == (1000,200,1200)


def test_post_get_patch_notes_conservent_ras(application):
    api, _, _ = client(application)
    with closing(api):
        r = api.post('/api/factures', json=facture())
        assert r.status_code == 201, r.text
        verifier_ras(r.json())
        fid = r.json()['id']
        verifier_ras(lire(api, fid))
        r = api.patch(f'/api/factures/{fid}',json={'notes':'Conservation fictive','ras_taux':None})
        assert r.status_code == 200,r.text
        verifier_ras(lire(api,fid))


@pytest.mark.parametrize('taux',[float('nan'),float('inf'),float('-inf'),-1,150])
def test_historique_invalide_diagnostique_sans_recriture(application,taux):
    api, _, _ = client(application)
    with closing(api):
        r = api.post('/api/factures',json=facture())
        assert r.status_code == 201,r.text
        fid = r.json()['id']
        with Session(application['engine']) as db:
            f = db.get(models.Facture,fid)
            sid = f.societe_id
            f.ras_taux = taux
            f.est_proforma = True  # Permet le PDF sans validation ni écriture réelle.
            db.commit()
            lignes_avant = [(l.id,l.quantite,l.prix_unitaire) for l in f.lignes]
        f = lire(api,fid)
        assert f['ras_taux'] is f['montant_ras'] is f['net_a_payer'] is None
        assert 'historique invalide' in f['ras_anomalie']
        assert (f['total_ht'],f['total_tva'],f['total_ttc']) == (1000,200,1200)
        r = api.get(f'/api/factures/{fid}/reglements')
        assert r.status_code == 200,r.text
        situation = r.json()
        assert situation['montant_ras'] is situation['solde_restant'] is situation['credit_tiers'] is None
        assert situation['total_regle'] == situation['total_encaisse'] == 0
        assert not situation['est_solde'] and situation['ras_anomalie']
        r = api.get(f'/api/factures/{fid}/pdf')
        assert r.status_code == 409,r.text
        assert 'historique invalide' in r.json()['detail']
        with Session(application['engine']) as db:
            f = db.get(models.Facture,fid)
            assert math.isnan(f.ras_taux) if math.isnan(taux) else f.ras_taux == taux
            assert [(l.id,l.quantite,l.prix_unitaire) for l in f.lignes] == lignes_avant
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count() == 0


def test_editeur_navigateur_conserve_ras_10(application):
    playwright = pytest.importorskip('playwright.sync_api')
    api, email, password = client(application)
    with closing(api):
        r = api.post('/api/factures',json=facture(tiers='Client conservation RAS'))
        assert r.status_code == 201,r.text
        fid = r.json()['id']
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(),headless=True)
            page = browser.new_page(viewport={'width':1440,'height':1000})
            try:
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures',wait_until='domcontentloaded')
                row = page.locator('tbody tr').filter(has_text='Client conservation RAS')
                row.locator('button[title="Modifier le brouillon"]').click()
                modal = page.get_by_role('dialog')
                select = modal.locator('label').filter(has_text='Retenue à la source (sur HT)').locator('..').locator('select')
                playwright.expect(select).to_have_value('10')
                with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{fid}') and r.request.method=='PATCH') as save:
                    modal.get_by_role('button',name='Enregistrer les modifications',exact=False).click()
                assert save.value.status == 200,save.value.text()
                modal.wait_for(state='hidden')
                verifier_ras(lire(api,fid))
                with Session(application['engine']) as db:
                    assert db.get(models.Facture,fid).ras_taux == 10
            except Exception:
                print('Éditeur RAS :', page.locator('body').inner_text()[-8000:])
                raise
            finally:
                browser.close()
