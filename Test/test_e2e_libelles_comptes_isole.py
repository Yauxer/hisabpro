"""Journal/Grand livre : noms exacts inactifs, CSV et vrai changement société."""
from datetime import date
import re
import uuid
import httpx
import pytest
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application


def ok(r,status=200):
    assert r.status_code==status,r.text
    return r.json()


def test_libelles_inactifs_exactement_conserves_sans_fuite_societe(application,tmp_path):
    suffix=uuid.uuid4().hex[:8]
    email,password=suffix+'@example.com','LibellesLecture2026!'
    noms=['Société lecture A '+suffix,'Société lecture B '+suffix]
    labels=['Prestations Équipe A / Audit','Prestations Équipe B / Conseil']
    # Référence déjà utilisée dans le produit ; complément du catalogue de cette fixture.
    with Session(application['engine']) as db:
        if db.get(models.CompteCGNCReference,'3421') is None:
            db.add(models.CompteCGNCReference(numero='3421',libelle='Clients',classe=3,type_compte='AC'))
            db.commit()
    with httpx.Client(base_url=application['api_url']) as api:
        token_a=ok(api.post('/api/auth/register',json={'nom':'Admin fictif','email':email,
                   'password':password,'raison_sociale':noms[0]}))['access_token']
        api.headers['Authorization']='Bearer '+token_a
        sid_a=ok(api.get('/api/societe/moi'))['id']
        sid_b=ok(api.post('/api/societes/nouvelle',json={'raison_sociale':noms[1]}),201)['id']
        token_b=ok(api.post(f'/api/societes/switcher/{sid_b}'))['access_token']
        tokens=[token_a,token_b]; sids=[sid_a,sid_b]; eids=[]; avant=[]
        for i,token in enumerate(tokens):
            api.headers['Authorization']='Bearer '+token
            ok(api.post('/api/plan-comptable',json={'numero':'71119','libelle':labels[i]}),201)
            tiers=ok(api.post('/api/tiers',json={'type':'client','nom':'Client auxiliaire '+str(i),'categorie_fiscale':'particulier'}),201)
            ec=ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'VT',
                  'libelle':'Vente synthétique','reference':'PIECE-FICTIVE-'+str(i),
                  'lignes':[{'compte':'3421','debit':120,'tiers_id':tiers['id'],'libelle':'Client'},
                  {'compte':'71119','credit':100,'libelle':'Vente'},
                  {'compte':'4455','credit':20,'libelle':'TVA'}]}),201)
            ok(api.post(f"/api/ecritures/{ec['id']}/valider"))
            eids.append(ec['id'])
            with Session(application['engine']) as db:
                e=db.get(models.Ecriture,ec['id'])
                avant.append(({c.name:getattr(e,c.name) for c in e.__table__.columns},
                     [{c.name:getattr(l,c.name) for c in l.__table__.columns} for l in e.lignes]))
                assert any(l.libelle_auxiliaire_snapshot==tiers['nom'] for l in e.lignes)
            ok(api.patch('/api/plan-comptable/71119',json={'actif':False}))
        playwright=pytest.importorskip('playwright.sync_api')
        with playwright.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            page=browser.new_page(accept_downloads=True,viewport={'width':1440,'height':1000})
            errors,server_errors=observer(page,application['api_url'])
            try:
                connexion(page,application['web_url'],email,password)
                for i in [0,1,0]:
                    if i==1:
                        page.get_by_role('button',name=noms[0],exact=True).click()
                        page.get_by_role('button',name=re.compile(re.escape(noms[1]))).click()
                    elif i==0 and page.get_by_role('button',name=noms[1],exact=True).count():
                        page.get_by_role('button',name=noms[1],exact=True).click()
                        page.get_by_role('button',name=re.compile(re.escape(noms[0]))).click()
                    page.get_by_role('button',name=noms[i],exact=True).wait_for()
                    for chemin in ['journal','grand-livre']:
                        page.goto(application['web_url']+'/'+chemin)
                        page.get_by_text(labels[i],exact=True).wait_for()
                        assert page.get_by_text(labels[1-i],exact=True).count()==0
                        with page.expect_download() as telechargement:
                            page.get_by_role('button',name='Exporter CSV',exact=True).click()
                        dest=tmp_path/f'{chemin}-{i}.csv'
                        telechargement.value.save_as(dest)
                        texte=dest.read_text(encoding='utf-8-sig')
                        assert labels[i] in texte and labels[1-i] not in texte
                        if chemin=='journal':
                            assert 'Client auxiliaire '+str(i) in texte
                assert not errors,errors
                assert not server_errors,server_errors
            except Exception:
                print('Lecture libellés :',page.url,page.locator('body').inner_text()[-7000:])
                raise
            finally:
                browser.close()
        with Session(application['engine']) as db:
            for i,eid in enumerate(eids):
                e=db.get(models.Ecriture,eid)
                apres=({c.name:getattr(e,c.name) for c in e.__table__.columns},
                    [{c.name:getattr(l,c.name) for c in l.__table__.columns} for l in e.lignes])
                assert apres==avant[i], 'Désactiver/lire le compte ne réécrit pas la pièce ni ses auxiliaires.'
