"""Activité tiers connectée : reliquats, homonymes, pagination et historique."""
from datetime import date
import uuid
import re
import httpx
import pytest
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(r,status=200):
    assert r.status_code == status,r.text
    return r.json()


def dossier(application):
    suffix = uuid.uuid4().hex[:8]
    email,password = suffix+'@example.com','TiersActivite2026!'
    api = httpx.Client(base_url=application['api_url'])
    admin = ok(api.post('/api/auth/register',json={'nom':'Admin fictif','email':email,
               'password':password,'raison_sociale':'Activité fictive '+suffix}))
    api.headers['Authorization'] = 'Bearer '+admin['access_token']
    sid = ok(api.get('/api/societe/moi'))['id']
    a = ok(api.post('/api/tiers',json={'nom':'Tiers homonyme','type':'client','ville':'Lien A'}),201)
    b = ok(api.post('/api/tiers',json={'nom':'Tiers homonyme','type':'les_deux','ville':'Lien B'}),201)
    return api,email,password,sid,a,b


def facture(api,t,pu=1000,type='vente',publier=True):
    f = ok(api.post('/api/factures',json={'type':type,'date':date.today().isoformat(),
           'tiers':t['nom'],'tiers_id':t['id'],'reference':'FR-'+uuid.uuid4().hex[:8] if type=='achat' else None,
           'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':pu,'tva':20}]}),201)
    if publier: ok(api.post(f"/api/factures/{f['id']}/valider"))
    return f['id']


def payer(api,fid,t,montant):
    ok(api.post('/api/reglements',json={'date':date.today().isoformat(),'facture_id':fid,
       'tiers':t['nom'],'montant':montant,'mode':'virement','comptabiliser':False}),201)


@pytest.mark.parametrize('historique',[False,True])
def test_tiers_reliquats_et_identifiants_ui_connectee(application,historique):
    api,email,password,sid,a,b = dossier(application)
    try:
        first = facture(api,a)
        payer(api,first,a,400)
        facture(api,a,publier=False)  # Ne doit pas doubler la fréquence.
        if not historique:
            facture(api,b)
            achat = facture(api,b,500,'achat')
            payer(api,achat,b,300)
            with Session(application['engine']) as db:
                db.add_all([models.Tiers(societe_id=sid,nom=f'ZZ fictif {i:03d}',type='client') for i in range(199)])
                db.commit()
        else:
            # Historiques synthétiques insérés dans le cluster de test uniquement.
            # Tous les vrais déclencheurs restent actifs et les pièces ne sont pas réécrites.
            with Session(application['engine']) as db:
                for i,tid,taux in [(1,None,0),(2,b['id'],float('nan'))]:
                    historique_f = models.Facture(societe_id=sid,numero=f'LEG-FICTIF-{sid}-{i}',
                           type='vente',date=date.today(),date_echeance=date.today(),exercice=date.today().year,
                           tiers='Tiers homonyme',tiers_id=tid,est_validee=False,est_proforma=False,
                           statut='en_attente',ras_taux=taux,lignes=[models.LigneFacture(
                               description='Historique synthétique',quantite=1,prix_unitaire=1000,tva=20)])
                    db.add(historique_f)
                    db.flush()  # Lignes créées avant l'état définitif ; garde inchangé.
                    historique_f.est_validee = True
                    db.flush()
                db.commit()
        playwright = pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium_executable(),headless=True)
            page = browser.new_page(viewport={'width':1440,'height':1000})
            page.set_default_timeout(20000)
            errors,server_errors = observer(page,application['api_url'])
            lectures=[]
            page.on('request',lambda r:lectures.append(r.url) if '/api/tiers?' in r.url else None)
            try:
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/tiers')
                row_a = page.locator('tbody tr').filter(has_text='Lien A')
                row_b = page.locator('tbody tr').filter(has_text='Lien B')
                playwright.expect(row_a).to_contain_text('800,00 MAD à recevoir')
                playwright.expect(row_a).to_contain_text('1 fact.')
                if historique:
                    playwright.expect(row_b).to_contain_text('Solde à vérifier')
                    playwright.expect(row_b).to_contain_text('1 fact.')
                    playwright.expect(row_b).not_to_contain_text('MAD à recevoir')
                    page.get_by_text('1 facture(s) non rattachée(s)',exact=False).wait_for()
                else:
                    playwright.expect(row_b).to_contain_text(re.compile(r'1[.\s]*200,00 MAD à recevoir'))
                    playwright.expect(row_b).to_contain_text('300,00 MAD à payer')
                    playwright.expect(row_b).to_contain_text('2 fact.')
                    playwright.expect(page.locator('tbody tr')).to_have_count(201)
                    assert any('skip=200' in url for url in lectures),lectures
                page.get_by_role('button',name='Avec impayés',exact=True).click()
                playwright.expect(row_a).to_have_count(1)
                playwright.expect(row_b).to_have_count(0 if historique else 1)
                page.get_by_role('button',name='Réguliers (3 factures et +)',exact=True).click()
                playwright.expect(page.locator('tbody tr')).to_have_count(0)
                assert not errors,errors
                assert not server_errors,server_errors
                with Session(application['engine']) as db:
                    assert db.query(models.Ecriture).filter_by(societe_id=sid).count()==0
            except Exception:
                print('Tiers UI :',page.locator('body').inner_text()[-8000:])
                raise
            finally:
                browser.close()
    finally:
        api.close()
