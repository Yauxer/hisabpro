"""Justificatifs/modèles sur le serveur réel, schéma091 et LOGIN non propriétaire.

Toutes les sociétés, références, écritures et pièces sont fictives et jetables.
"""
from contextlib import closing
from datetime import date
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from test_e2e_runtime_session_isole import (
    application, application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import champ
from browser_support import chromium_executable
from test_complements_structure_postgres import refuser


def ecriture(api, *, validee=True, reference='ORIGINE-FICTIVE-451'):
    return ok(api.post('/api/ecritures',json={
        'date':date.today().isoformat(),'journal':'BQ','reference':reference,
        'libelle':'Pièce fictive justificatifs451','est_validee':validee,
        'lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}],
    }),201)['id']


def original(app,eid):
    with app['engine'].connect() as db:
        return (db.scalar(text('SELECT row_to_json(e)::text FROM ecritures e WHERE id=:id'),{'id':eid}),
                db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l WHERE ecriture_id=:id ORDER BY id'),{'id':eid}).scalars().all())


def pdf_fictif():
    from io import BytesIO
    from reportlab.pdfgen import canvas
    out=BytesIO();c=canvas.Canvas(out,invariant=True)
    c.drawString(40,800,'JUSTIFICATIF FICTIF451 - AUCUNE OPERATION REELLE')
    c.save();return out.getvalue()


def test_modeles_lecture_sans_droits_de_modification(application):
    with closing(client(application)[0]) as api:
        modeles=ok(api.get('/api/modeles'))
        assert modeles and len({m['id'] for m in modeles})==len(modeles)
        assert all(len(m['lignes'])>=2 for m in modeles)
        capital=next(m for m in modeles if m['code']=='capital_souscription')
        assert {(l['compte'],l['sens']) for l in capital['lignes']}=={('3461','debit'),('1111','credit')}
        propositions=ok(api.get('/api/modeles/par-compte/3461'))
        assert capital['id'] in {m['id'] for m in propositions}
    runtime=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'))
    try:
        for table in ('modeles_ecritures','lignes_modele'):
            for sql in (f'UPDATE {table} SET id=id',f'DELETE FROM {table}',f'TRUNCATE {table}'):
                refuser(runtime,sql,'42501')
    finally:runtime.dispose()


def test_references_prioritaires_et_fichiers_definitifs_sans_reecrire_original(application):
    with closing(client(application)[0]) as api:
        eid=ecriture(api);before=original(application,eid)
        contenu=pdf_fictif()
        fichiers=[]
        for _ in range(2):
            f=ok(api.post(f'/api/attachments/ecriture/{eid}',files={'file':('contrat451.pdf',contenu,'application/pdf')}))
            fichiers.append(f)
            download=api.get(f['url']);assert download.status_code==200
            assert hashlib.sha256(download.content).digest()==hashlib.sha256(contenu).digest()
        assert fichiers[0]['nom']!=fichiers[1]['nom']
        assert len(ok(api.get(f'/api/attachments/ecriture/{eid}')))==2
        assert api.delete(f"/api/attachments/ecriture/{eid}/{fichiers[0]['nom']}").status_code==409
        for ref in ('JUSTIF-FICTIF-451-A','JUSTIF-FICTIF-451-B'):
            ok(api.post(f'/api/ecritures/{eid}/justificatifs',json={
                'reference':ref,'date_piece':date.today().isoformat(),'motif':'Réception fictive après validation',
            }),201)
        infos=ok(api.get(f'/api/ecritures/{eid}/justificatifs'))
        assert infos['reference_origine']=='ORIGINE-FICTIVE-451'
        assert infos['reference_fec']=='JUSTIF-FICTIF-451-B'
        assert len(infos['complements'])==4
        assert [j['source_type'] for j in infos['complements']].count('fichier')==2
        assert all(j['created_by'] for j in infos['complements'])
        found=ok(api.get('/api/ecritures/par-piece',params={'reference':'JUSTIF-FICTIF-451-B'}))
        assert any(e['id']==eid for e in found)
        assert original(application,eid)==before
        fec=api.get('/api/fec/export',params={'exercice':date.today().year})
        assert fec.status_code==200,fec.text
        rows=[line.split('\t') for line in fec.text.rstrip('\r\n').splitlines()]
        assert len(rows)==3 and all(len(row)==18 for row in rows)
        assert {row[8] for row in rows[1:]}=={'JUSTIF-FICTIF-451-B'}
        # La protection append-only est également exercée en SQL, hors API.
        refuser(application['engine'],f"DELETE FROM ecriture_justificatifs WHERE ecriture_id={eid}",'P0001')
        assert original(application,eid)==before


def test_piece_brouillon_supprimable_et_refus_multisociete_lecture(application):
    a,email_a,_=client(application);b,email_b,_=client(application)
    with closing(a),closing(b):
        eid=ecriture(a,validee=False);before=original(application,eid)
        f=ok(a.post(f'/api/attachments/ecriture/{eid}',files={'file':('brouillon.pdf',pdf_fictif(),'application/pdf')}))
        for method,url,kwargs in (
            ('GET',f'/api/ecritures/{eid}/justificatifs',{}),
            ('POST',f'/api/ecritures/{eid}/justificatifs',{'json':{'reference':'INTERDIT'}}),
            ('GET',f'/api/attachments/ecriture/{eid}',{}),
            ('GET',f['url'],{}),
            ('DELETE',f"/api/attachments/ecriture/{eid}/{f['nom']}",{}),
        ):
            assert b.request(method,url,**kwargs).status_code==404
        assert a.delete(f"/api/attachments/ecriture/{eid}/{f['nom']}").status_code==204
        assert ok(a.get(f'/api/attachments/ecriture/{eid}'))==[]
        assert ok(a.get(f'/api/ecritures/{eid}/justificatifs'))['complements']==[]
        assert original(application,eid)==before
        sid=ok(a.get('/api/auth/me'))['societe_id']
        ok(a.post(f'/api/societes/{sid}/inviter',params={'email':email_b,'role':'lecture'}))
        b.headers['Authorization']='Bearer '+ok(b.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert b.get('/api/modeles').status_code==200
        assert b.get(f'/api/ecritures/{eid}/justificatifs').status_code==200
        assert b.post(f'/api/ecritures/{eid}/justificatifs',json={'reference':'LECTURE-INTERDITE'}).status_code==403
        assert b.post(f'/api/attachments/ecriture/{eid}',files={'file':('interdit.pdf',pdf_fictif(),'application/pdf')}).status_code==403
        assert original(application,eid)==before


def test_refus_sql_suppression_conserve_fichier_et_trace(application):
    """Défaillance SQL réelle : le document doit rester récupérable au refus.

    Le retrait du seul DELETE est injecté et restauré dans le cluster nonce.
    Aucun monkeypatch d'API, de transaction ou de système de fichiers.
    """
    from postgres_isole import verifier_cible_isolee
    c=application['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with closing(client(application)[0]) as api:
        eid=ecriture(api,validee=False)
        contenu=pdf_fictif()
        f=ok(api.post(f'/api/attachments/ecriture/{eid}',files={'file':('conserver451.pdf',contenu,'application/pdf')}))
        avant=ok(api.get(f'/api/ecritures/{eid}/justificatifs'))
        with application['engine'].begin() as db:
            db.execute(text('REVOKE DELETE ON ecriture_justificatifs FROM hisabpro'))
        try:
            assert api.delete(f"/api/attachments/ecriture/{eid}/{f['nom']}").status_code==500
            assert ok(api.get(f'/api/ecritures/{eid}/justificatifs'))==avant
            download=api.get(f['url'])
            assert download.status_code==200,'Un refus SQL ne doit pas supprimer le fichier physique.'
            assert download.content==contenu
        finally:
            with application['engine'].begin() as db:
                db.execute(text('GRANT DELETE ON ecriture_justificatifs TO hisabpro'))


def test_validation_concurrente_protege_la_piece_devenue_definitive(application):
    with closing(client(application)[0]) as api:
        api.timeout=20
        eid=ecriture(api,validee=False)
        contenu=pdf_fictif()
        f=ok(api.post(f'/api/attachments/ecriture/{eid}',files={'file':('course451.pdf',contenu,'application/pdf')}))
        with application['engine'].connect() as garde,ThreadPoolExecutor(max_workers=2) as pool:
            garde.execute(text('SELECT id FROM ecritures WHERE id=:id FOR UPDATE'),{'id':eid})
            bloqueur=garde.scalar(text('SELECT pg_backend_pid()'))
            validation=pool.submit(api.post,f'/api/ecritures/{eid}/valider')
            try:
                limite=time.monotonic()+5
                while True:
                    with application['engine'].connect() as db:
                        # La validation verrouille maintenant par SELECT FOR UPDATE.
                        # Cibler notre bloqueur évite aussi une attente étrangère au test.
                        attend=db.execute(text("SELECT pid,query,pg_blocking_pids(pid) AS bloqueurs FROM pg_stat_activity WHERE usename='hisabpro' "
                            "AND wait_event_type='Lock' AND query ILIKE '%ecritures%' AND :b=ANY(pg_blocking_pids(pid))"),{'b':bloqueur}).mappings().all()
                    if attend:
                        print('Validation réellement bloquée par notre transaction :',[(x['query'],x['bloqueurs']) for x in attend])
                        assert not validation.done()
                        break
                    assert time.monotonic()<limite,'La vraie validation doit attendre le verrou SQL.'
                    time.sleep(.02)
                suppression=pool.submit(api.delete,f"/api/attachments/ecriture/{eid}/{f['nom']}")
                # La validation attend déjà le verrou parent avant la suppression.
                time.sleep(.15)
            finally:garde.commit()
            assert validation.result(timeout=15).status_code==200
            r=suppression.result(timeout=15)
            assert r.status_code==409,r.text
        assert api.get(f['url']).content==contenu
        assert len(ok(api.get(f'/api/ecritures/{eid}/justificatifs'))['complements'])==1


def test_edge_refus_suppression_garde_la_piece_visible(application):
    playwright=pytest.importorskip('playwright.sync_api')
    api,email,password=client(application)
    with closing(api),playwright.sync_playwright() as p:
        eid=ecriture(api,validee=False,reference='REFUS-UI-FICTIF451')
        f=ok(api.post(f'/api/attachments/ecriture/{eid}',files={'file':('refus451.pdf',pdf_fictif(),'application/pdf')}))
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000})
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
            page.locator('tbody tr').filter(has_text='REFUS-UI-FICTIF451').first.locator('button[title^="Justificatifs"]').click()
            page.get_by_text(f['nom'],exact=True).wait_for()
            with application['engine'].begin() as db:
                db.execute(text('REVOKE DELETE ON ecriture_justificatifs FROM hisabpro'))
            try:
                page.on('dialog',lambda dialogue:dialogue.accept())
                # Un500 non géré peut être filtré par CORS :le navigateur voit
                # alors un échec réseau, pas un événement response exploitable.
                # Le test API distinct vérifie le statut500 et le rollback réels.
                with page.expect_request(lambda r:r.url.endswith('/'+f['nom']) and r.method=='DELETE'):
                    page.locator('button[title="Supprimer"]').click()
                playwright.expect(page.get_by_text('Suppression impossible',exact=False)).to_be_visible()
                playwright.expect(page.get_by_text(f['nom'],exact=True)).to_be_visible()
            finally:
                with application['engine'].begin() as db:
                    db.execute(text('GRANT DELETE ON ecriture_justificatifs TO hisabpro'))
        finally:browser.close()


def test_edge_modele_validation_justificatif_et_telechargement(application,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    api,email,password=client(application)
    with closing(api),playwright.sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000)
            errors,server_errors=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/journal',wait_until='domcontentloaded')
            page.get_by_role('button',name='Nouvelle écriture',exact=True).click()
            modal=page.get_by_role('dialog')
            modal.get_by_role('button',name="Choisir un modèle d'écriture",exact=True).click()
            page.get_by_placeholder('Rechercher une opération...').fill('Souscription du capital')
            page.get_by_role('button',name='Souscription du capital — engagement des associés',exact=False).click()
            # Le formulaire ajoute volontairement une ligne vide de saisie.
            lignes=modal.locator('tbody tr');playwright.expect(lignes).to_have_count(3)
            playwright.expect(lignes.nth(0).get_by_placeholder('Ex: 6111')).to_have_value('3461')
            playwright.expect(lignes.nth(1).get_by_placeholder('Ex: 6111')).to_have_value('1111')
            lignes.nth(0).locator('td[data-label="Débit (MAD)"] input').fill('100')
            champ(modal,'Référence du justificatif').fill('CAPITAL-FICTIF451')
            modal.get_by_label('Valider immédiatement',exact=False).check()
            with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as save:
                modal.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
            assert save.value.status==201,save.value.text()
            eid=save.value.json()['id'];modal.wait_for(state='hidden')
            before=original(application,eid)
            row=page.locator('tbody tr').filter(has_text='CAPITAL-FICTIF451').first
            row.locator('button[title^="Justificatifs"]').click()
            # Le champ enveloppé par son label est accessible sans dépendre du CSS.
            page.get_by_label('Référence du justificatif',exact=True).fill('PV-FICTIF451')
            with page.expect_response(lambda r:r.url.endswith(f'/api/ecritures/{eid}/justificatifs') and r.request.method=='POST') as ajout:
                page.get_by_role('button',name='Ajouter la référence',exact=True).click()
            assert ajout.value.status==201,ajout.value.text()
            contenu=pdf_fictif()
            with page.expect_response(lambda r:r.url.endswith(f'/api/attachments/ecriture/{eid}') and r.request.method=='POST') as upload:
                page.locator('input[type=file]').set_input_files({'name':'preuve451.pdf','mimeType':'application/pdf','buffer':contenu})
            assert upload.value.status==200,upload.value.text()
            nom=upload.value.json()['nom']
            page.get_by_text(nom,exact=True).wait_for()
            with page.expect_download() as dl:
                page.get_by_role('button',name='Télécharger',exact=True).click()
            assert Path(dl.value.path()).read_bytes()==contenu
            assert page.get_by_role('button',name='Supprimer',exact=True).count()==0
            page.get_by_role('button',name='Fermer',exact=True).click()
            page.reload(wait_until='domcontentloaded')
            page.locator('tbody tr').filter(has_text='PV-FICTIF451').first.wait_for()
            assert original(application,eid)==before
            with application['engine'].connect() as db:
                assert db.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':eid}).all()==[('1111',0,100),('3461',100,0)]
            assert not errors and not server_errors,(errors,server_errors)
        except BaseException:
            page.screenshot(path=str(tmp_path/'justificatifs451.png'),full_page=True)
            print(page.locator('body').inner_text()[-6000:])
            raise
        finally:browser.close()
