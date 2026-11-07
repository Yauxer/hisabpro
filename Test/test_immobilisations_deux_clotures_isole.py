"""Deux exercices décalés, ouverture explicite et cession : HTTP/Edge/PG nonce."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration, reconcilier,
)
from test_registre_immobilisations_cloture_isole import acquisition
from test_dotations_concurrentes_isole import generer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from recette_restauration_consolidee_084 import empreintes_tables
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer


def dossier(api):
    annee=date.today().year-2
    for a in (annee,annee+1):
        ok(api.post('/api/exercices',json={'annee':a,'date_debut':f'{a-1}-07-01','date_fin':f'{a}-06-30'}),201)
    immo=ok(api.post('/api/immobilisations',params={'generer_ecriture':False},json=acquisition(annee-2)),201)
    iid=immo['id'];sid=ok(api.get('/api/societe/moi'))['id']
    r=ok(api.post('/api/immobilisations/reconciliation-historique/reconstituer-acquisitions',json={
        'exercice':annee,'items':[{'immo_id':iid,'mode':'reprise_anterieure','compte_contrepartie':'4481'}]}))
    ok(api.post(f"/api/ecritures/{r['generees'][0]['ecriture_id']}/valider"))
    am=ok(generer(api,'unitaire',annee,iid));assert am['dotation']==2000
    ok(api.post(f"/api/ecritures/{am['ecriture_id']}/valider"))
    return annee,iid,sid


def verifier_report(application,api,sid,annee,cumul):
    with application['engine'].connect() as c:
        e=c.execute(text('SELECT id,date FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':sid,'r':f'AN-{annee+1}'}).one()
        assert e.date==date(annee,7,1)
        immos=c.execute(text("SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id AND compte IN ('2355','28355') ORDER BY compte"),{'id':e.id}).all()
        assert immos==([('2355',10000,0),('28355',0,cumul)] if cumul else [])
    assert api.get('/api/fec/export',params={'exercice':annee}).status_code==200


def test_deux_clotures_decalees_et_continuite_dates_dans_navigateur(application):
    import playwright.sync_api as pw
    executable=chromium_executable();assert executable,'Edge/Chromium requis pour cette recette'
    api,email,password=client(application)
    with closing(api):
        annee,iid,sid=dossier(api);sources=originaux(application,sid)
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=executable,headless=True)
            try:
                page=browser.new_page();page.set_default_timeout(20000)
                erreurs,serveur=observer(page,application['api_url']);dialogues=[]
                def accepter(d):dialogues.append((d.type,d.message));d.accept()
                page.on('dialog',accepter)
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/cloture',wait_until='domcontentloaded')
                page.get_by_label('Exercice actif',exact=True).select_option(str(annee))
                bouton=page.get_by_role('button',name=f"Clôturer l'exercice {annee}",exact=True)
                pw.expect(bouton).to_be_enabled()
                with page.expect_response(lambda r:f'/api/cloture/cloturer?exercice={annee}' in r.url) as r:
                    bouton.click()
                assert r.value.status==200 and r.value.json()['resultat_net']==-5000,r.value.text()
                page.get_by_text(f'Exercice {annee} clôturé définitivement',exact=False).wait_for()
                verifier_report(application,api,sid,annee,5000)
                am=ok(generer(api,'unitaire',annee+1,iid));assert am['dotation']==2000
                ok(api.post(f"/api/ecritures/{am['ecriture_id']}/valider"))
                page.get_by_label('Exercice actif',exact=True).select_option(str(annee+1))
                bouton=page.get_by_role('button',name=f"Clôturer l'exercice {annee+1}",exact=True)
                pw.expect(bouton).to_be_enabled();tables=empreintes_tables(application['engine'])
                with page.expect_response(lambda r:f'/api/cloture/cloturer?exercice={annee+1}' in r.url) as r:
                    bouton.click()
                assert r.value.status==409,r.value.text()
                pw.expect(bouton).to_be_enabled()
                pw.expect(page.locator('[data-notification]').filter(has_text='Continuité des exercices')).to_be_visible()
                apres=empreintes_tables(application['engine'])
                assert {k:v for k,v in apres.items() if k!='audit_actions'}=={k:v for k,v in tables.items() if k!='audit_actions'}
                # Régler explicitement N+2 encore vide dans le formulaire réel.
                page.get_by_label('Exercice actif',exact=True).select_option(str(annee+2))
                champs=page.locator('input[type="date"]')
                pw.expect(champs.nth(0)).to_be_enabled()
                champs.nth(0).fill(f'{annee+1}-07-01');champs.nth(1).fill(f'{annee+2}-06-30')
                with page.expect_response(lambda r:r.url.endswith(f'/api/exercices/{annee+2}') and r.request.method=='PATCH') as r:
                    page.get_by_role('button',name='Enregistrer',exact=True).click()
                assert r.value.status==200,r.value.text()
                page.get_by_label('Exercice actif',exact=True).select_option(str(annee+1))
                bouton=page.get_by_role('button',name=f"Clôturer l'exercice {annee+1}",exact=True)
                pw.expect(bouton).to_be_enabled()
                with page.expect_response(lambda r:f'/api/cloture/cloturer?exercice={annee+1}' in r.url) as r:
                    bouton.click()
                assert r.value.status==200 and r.value.json()['resultat_net']==-5000,r.value.text()
                page.get_by_text(f'Exercice {annee+1} clôturé définitivement',exact=False).wait_for()
                verifier_report(application,api,sid,annee+1,7000)
                assert not erreurs and not serveur,(erreurs,serveur)
            finally:browser.close()
        fin=originaux(application,sid)
        for table,lignes in sources.items():assert all(l in fin[table] for l in lignes)


def test_cession_apres_reprise_ne_recree_pas_annuites_anterieures(application):
    with closing(client(application)[0]) as api:
        annee,iid,sid=dossier(api)
        ok(api.post('/api/cloture/cloturer',params={'exercice':annee}))
        verifier_report(application,api,sid,annee,5000)
        avant=originaux(application,sid)
        with application['engine'].connect() as c:
            ids=set(c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s'),{'s':sid}).scalars())
        r=ok(api.post(f'/api/immobilisations/{iid}/sortie',json={'date_sortie':f'{annee}-12-31',
            'type_sortie':'cession','prix_cession_ht':7500,'taux_tva_cession':20,'encaissement_immediat':False}))
        assert (r['cumul_amortissement'],r['vnc'],r['resultat_cession'],r['ttc_cession'])==(6000,4000,3500,9000)
        with application['engine'].connect() as c:
            nouvelles=c.execute(text('SELECT id,exercice,date,reference FROM ecritures WHERE societe_id=:s ORDER BY id'),{'s':sid}).all()
            nouvelles=[e for e in nouvelles if e.id not in ids]
            assert len(nouvelles)==3,nouvelles
            assert all(e.exercice==annee+1 and e.date==date(annee,12,31) for e in nouvelles),nouvelles
            assert {e.reference for e in nouvelles}=={f'AM-{annee+1}-{iid}',f'SORTIE-IMMO-{iid}',f'CESSION-IMMO-{iid}'}
            am=next(e for e in nouvelles if e.reference.startswith('AM-'))
            assert c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':am.id}).all()==[('28355',0,1000),('61935',1000,0)]
        for e in nouvelles:ok(api.post(f'/api/ecritures/{e.id}/valider'))
        ok(api.patch(f'/api/exercices/{annee+2}',json={'date_debut':f'{annee+1}-07-01','date_fin':f'{annee+2}-06-30'}))
        cloture=ok(api.post('/api/cloture/cloturer',params={'exercice':annee+1}))
        assert cloture['resultat_net']==-500
        verifier_report(application,api,sid,annee+1,0)
        fin=originaux(application,sid)
        for table,lignes in avant.items():assert all(l in fin[table] for l in lignes)


@pytest.mark.parametrize('ouverture,validee',[(2000,True),(4000,True),(3000,False)])
def test_sortie_ne_masque_pas_ecart_reprise_ou_brouillon(application,ouverture,validee):
    with closing(client(application)[0]) as api:
        annee=date.today().year-2
        ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee-1}-07-01','date_fin':f'{annee}-06-30'}),201)
        immo=ok(api.post('/api/immobilisations',params={'generer_ecriture':False},json=acquisition(annee-2)),201)
        iid=immo['id'];sid=ok(api.get('/api/societe/moi'))['id']
        eid=ok(api.post('/api/immobilisations/reconciliation-historique/reconstituer-acquisitions',json={
            'exercice':annee,'items':[{'immo_id':iid,'mode':'reprise_anterieure','compte_contrepartie':'4481'}]}))['generees'][0]['ecriture_id']
        if ouverture!=3000:
            ok(api.patch(f'/api/ecritures/{eid}',json={'lignes':[{'compte':'2355','debit':10000},
                {'compte':'28355','credit':ouverture},{'compte':'4481','credit':10000-ouverture}]}))
        if validee:ok(api.post(f'/api/ecritures/{eid}/valider'))
        avant=originaux(application,sid);tables=empreintes_tables(application['engine'])
        r=api.post(f'/api/immobilisations/{iid}/sortie',json={'date_sortie':f'{annee-1}-12-31',
            'type_sortie':'cession','prix_cession_ht':7500,'taux_tva_cession':20,'encaissement_immediat':False})
        assert r.status_code==409,r.text
        assert ('cumul' if validee else 'valid') in r.text.lower(),r.text
        assert originaux(application,sid)==avant
        apres=empreintes_tables(application['engine'])
        assert {k:v for k,v in apres.items() if k!='audit_actions'}=={k:v for k,v in tables.items() if k!='audit_actions'}


@pytest.mark.parametrize('initiale',[None,500,3000])
def test_cession_reconnait_charge_annuelle_corrigee_sans_nouvelle_am(application,initiale):
    with closing(client(application)[0]) as api:
        annee,iid,sid=dossier(api)
        ok(api.post('/api/cloture/cloturer',params={'exercice':annee}))
        if initiale is not None:
            ok(api.post('/api/ecritures',json={'date':f'{annee+1}-06-30','journal':'AM',
                'reference':f'AM-{annee+1}-{iid}','libelle':'Dotation fictive corrigée506',
                'est_validee':True,'lignes':[{'compte':'61935','debit':initiale},{'compte':'28355','credit':initiale}]}),201)
        correction=ok(reconcilier(api,'corriger',annee+1,iid))['generees'][0]['ecriture_id']
        ok(api.post(f'/api/ecritures/{correction}/valider'));avant=originaux(application,sid)
        with application['engine'].connect() as c:
            ids=set(c.execute(text('SELECT id FROM ecritures WHERE societe_id=:s'),{'s':sid}).scalars())
        r=ok(api.post(f'/api/immobilisations/{iid}/sortie',json={'date_sortie':f'{annee+1}-06-30',
            'type_sortie':'cession','prix_cession_ht':7500,'taux_tva_cession':20,'encaissement_immediat':False}))
        assert (r['cumul_amortissement'],r['vnc'],r['resultat_cession'])==(7000,3000,4500)
        with application['engine'].connect() as c:
            nouv=c.execute(text('SELECT id,reference FROM ecritures WHERE societe_id=:s ORDER BY id'),{'s':sid}).all()
            nouv=[e for e in nouv if e.id not in ids]
            assert {e.reference for e in nouv}=={f'SORTIE-IMMO-{iid}',f'CESSION-IMMO-{iid}'}
        for e in nouv:ok(api.post(f'/api/ecritures/{e.id}/valider'))
        ok(api.patch(f'/api/exercices/{annee+2}',json={'date_debut':f'{annee+1}-07-01','date_fin':f'{annee+2}-06-30'}))
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':annee+1}))['resultat_net']==-500
        verifier_report(application,api,sid,annee+1,0)
        apres=originaux(application,sid)
        for table,lignes in avant.items():assert all(l in apres[table] for l in lignes)


def test_sortie_avant_reprise_refusee_sans_effet(application):
    with closing(client(application)[0]) as api:
        annee,iid,sid=dossier(api)
        ok(api.post('/api/exercices',json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-06-30'}),201)
        avant=empreintes_tables(application['engine'])
        r=api.post(f'/api/immobilisations/{iid}/sortie',json={'date_sortie':f'{annee-1}-06-30',
            'type_sortie':'rebut'})
        assert r.status_code==409 and 'précéder la reprise' in r.text,r.text
        apres=empreintes_tables(application['engine'])
        assert {k:v for k,v in apres.items() if k!='audit_actions'}=={k:v for k,v in avant.items() if k!='audit_actions'}
