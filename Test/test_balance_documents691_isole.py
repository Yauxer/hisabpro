"""Justificatifs104 : traces SQL, octets réels, rôles et limites sur cibles nonce."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from reportlab.pdfgen import canvas
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_balance_dossier689_isole import (
    application as application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier)
from test_avances_salaries_isole import appliquer
from test_restauration_runtime_acl_089 import catalogue_acl
from postgres_isole import verifier_cible_isolee


def path(v):return BASE+f'/{v["id"]}/documents'


def pdf_fictif():
    out=BytesIO();c=canvas.Canvas(out);c.drawString(50,750,'JUSTIFICATIF FICTIF691 - aucune valeur fiscale');c.save();return out.getvalue()


def joindre(api,v,*,cle=None,nom='justificatif_fictif691.pdf',raw=None,reference='Source fictive691',empreinte=None):
    return api.post(path(v),data={'cle':str(cle or uuid4()),'empreinte':empreinte or v['empreinte_sha256'],'reference':reference},
                    files={'file':(nom,pdf_fictif() if raw is None else raw,'application/pdf')})


@pytest.fixture(scope='module')
def application(application103):
    app=application103;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with closing(client(app)[0]) as api:
        v=creer(api);assert api.get(path(v)).status_code==503
        z=api.get(BASE+f'/{v["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert json.loads(zip.read('justificatifs.json'))['statut']=='indisponible_migration104'
    avant,acl=donnees_metier(app),catalogue_acl(app['engine'])
    appliquer(app,'104_liasse_balance_documents.sql')
    apres,droits=donnees_metier(app),catalogue_acl(app['engine'])
    assert all(apres[k]==v for k,v in avant.items())
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    appliquer(app,'104_liasse_balance_documents.sql')
    assert donnees_metier(app)==apres and catalogue_acl(app['engine'])==droits
    yield app


def test_691_upload_rejeu_auteur_et_preparation_inchanges(application):
    with closing(client(application)[0]) as api:
        v=creer(api);raw=pdf_fictif();cle=uuid4();avant=donnees_metier(application)
        r=ok(joindre(api,v,cle=cle,raw=raw),201)
        assert r['sha256']==hashlib.sha256(raw).hexdigest() and r['taille']==len(raw)
        assert r['created_by']==ok(api.get('/api/auth/me'))['id'] and r['acteur_nom']
        assert r['empreinte_preparation']==v['empreinte_sha256']
        assert ok(joindre(api,v,cle=cle,raw=raw),201)==r
        assert joindre(api,v,cle=cle,raw=b'Autre contenu fictif').status_code==409
        d=ok(api.get(path(v)));assert d['documents']==[r] and d['taille_totale']==len(raw)
        assert api.get(path(v)+f'/{r["id"]}').content==raw
        assert api.delete(path(v)+f'/{r["id"]}').status_code==405
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        apres=donnees_metier(application)
        assert all(apres[k]==value for k,value in avant.items() if k!='liasse_balance_documents')


@pytest.mark.parametrize('nom,raw,empreinte,statut',[
    ('test.exe',b'fictif',None,422),('vide.pdf',b'',None,422),
    ('test.pdf',b'fictif','0'*64,409),('tropgrand.pdf',b'x'*(10*1024*1024+1),None,413)],
    ids=['extension','vide','empreinte','taille'])
def test_691_entrees_refusees_sans_fichier_orphelin(application,nom,raw,empreinte,statut):
    with closing(client(application)[0]) as api:
        v=creer(api);sid=ok(api.get('/api/auth/me'))['societe_id']
        assert joindre(api,v,nom=nom,raw=raw,empreinte=empreinte).status_code==statut
        assert ok(api.get(path(v)))['documents']==[]
        dossier=application['uploads_dir']/str(sid)/'balance_preparation_documents'/str(v['id'])
        assert not dossier.exists() or not list(dossier.iterdir())


def test_691_fichiers_modifies_ou_absents_bloquent_download_et_zip(application):
    with closing(client(application)[0]) as api:
        v=creer(api);raw=pdf_fictif();r=ok(joindre(api,v,raw=raw),201)
        sid=ok(api.get('/api/auth/me'))['societe_id']
        fichier=application['uploads_dir']/str(sid)/'balance_preparation_documents'/str(v['id'])/r['nom_stockage']
        assert fichier.resolve().is_relative_to(application['directory'].resolve())
        try:
            fichier.write_bytes(b'ALTERATION FICTIVE691')
            assert api.get(path(v)+f'/{r["id"]}').status_code==409
            assert api.get(BASE+f'/{v["id"]}/zip').status_code==409
            fichier.unlink()
            assert api.get(path(v)+f'/{r["id"]}').status_code==409
        finally:fichier.write_bytes(raw)
        assert api.get(path(v)+f'/{r["id"]}').content==raw


def test_691_droits_cloisonnement_version_et_zip_avec_octets(application):
    admin,email,password=client(application)
    with closing(admin),closing(client(application)[0]) as autre:
        v=creer(admin);raw=pdf_fictif();r=ok(joindre(admin,v,raw=raw,nom='../../faux691.pdf'),201)
        assert r['nom_original']=='faux691.pdf'
        sid=ok(admin.get('/api/auth/me'))['societe_id']
        assert autre.get(path(v)).status_code==404 and joindre(autre,v).status_code==404
        ae=ok(autre.get('/api/auth/me'))['email']
        ok(admin.post(f'/api/societes/{sid}/inviter',params={'email':ae,'role':'lecture'}))
        token=ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token'];autre.headers['Authorization']='Bearer '+token
        assert autre.get(path(v)).status_code==200 and joindre(autre,v).status_code==403
        assert autre.get(path(v)+f'/{r["id"]}').content==raw
        z=autre.get(BASE+f'/{v["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert zip.testzip() is None
            noms=zip.namelist();assert not any(n.startswith('/') or '..' in n or '\\' in n for n in noms)
            fichier='justificatifs/'+r['nom_stockage'];assert zip.read(fichier)==raw
            meta=json.loads(zip.read('justificatifs.json'));assert meta['documents']==[r]
            manifeste=json.loads(zip.read('MANIFESTE_SHA256.json'))
            assert set(noms)==set(manifeste['fichiers'])|{'MANIFESTE_SHA256.json'}
            assert manifeste['fichiers'][fichier]['sha256']==r['sha256']
            assert json.loads(zip.read('preparation.json'))==v
        v2=ok(admin.post(chemin(v),json=demande(v)),201)
        assert ok(admin.get(path(v2)))['documents']==[]
        assert admin.get(path(v2)+f'/{r["id"]}').status_code==404
        assert ok(admin.get(path(v)))['documents']==[r]


def test_691_sql_immuable_rollback_fichier_et_liens_directs(application):
    with closing(client(application)[0]) as api:
        v=creer(api);r=ok(joindre(api,v),201);sid=ok(api.get('/api/auth/me'))['societe_id']
        with application['engine'].connect() as db:
            for sql in ('UPDATE liasse_balance_documents SET reference=reference','DELETE FROM liasse_balance_documents','TRUNCATE liasse_balance_documents'):
                with pytest.raises(DBAPIError):db.execute(text(sql))
                db.rollback()
            with pytest.raises(DBAPIError):
                db.execute(text('''INSERT INTO liasse_balance_documents(societe_id,preparation_id,empreinte_preparation,cle,
                  nom_original,nom_stockage,reference,taille,sha256,created_by)
                  SELECT societe_id,preparation_id,:h,CAST(:c AS uuid),nom_original,:nom,reference,taille,sha256,created_by
                  FROM liasse_balance_documents WHERE id=:id'''),{'h':'0'*64,'c':str(uuid4()),'nom':uuid4().hex+'.pdf','id':r['id']})
            db.rollback()
        # RefusSQL réel après écriture du fichier : le fichier nouvellement créé doit disparaître.
        from sqlalchemy import create_engine
        from sqlalchemy.engine import make_url
        engine=create_engine(make_url(application['cluster']['url']))
        try:
            with engine.begin() as db:db.execute(text('REVOKE INSERT ON liasse_balance_documents FROM hisabpro'))
            cle=uuid4();assert joindre(api,v,cle=cle).status_code==409
            fichier=application['uploads_dir']/str(sid)/'balance_preparation_documents'/str(v['id'])/(cle.hex+'.pdf')
            assert not fichier.exists()
        finally:
            with engine.begin() as db:db.execute(text('GRANT INSERT ON liasse_balance_documents TO hisabpro'))
            engine.dispose()
        assert len(ok(api.get(path(v)))['documents'])==1


def test_691_concurrence_rejeu_et_capacite_documentaire(application):
    import httpx
    with closing(client(application)[0]) as api:
        v=creer(api);cle=uuid4();raw=pdf_fictif()
        def post(cle,raw):
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=60) as c:return joindre(c,v,cle=cle,raw=raw)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a,b=list(pool.map(lambda _:post(cle,raw),range(2)))
        assert a.status_code==b.status_code==201 and a.json()==b.json()
        bloc=b'FICTIF691'*(10*1024*1024//9)+b'x'*(10*1024*1024%9)
        assert len(bloc)==10*1024*1024
        for _ in range(4):ok(joindre(api,v,raw=bloc),201)
        # Ajouter quatreMo moins le petitPDF deja present : total44Mo.
        ok(joindre(api,v,raw=b'x'*(4*1024*1024-len(raw))),201)
        with ThreadPoolExecutor(max_workers=2) as pool:
            reps=list(pool.map(lambda _:post(uuid4(),b'x'*(4*1024*1024)),range(2)))
        assert sorted(r.status_code for r in reps)==[201,409]
        assert ok(api.get(path(v)))['taille_totale']==48*1024*1024


def test_691_rejeu_sql_sur_traces_et_fichier_deja_conserves(application):
    with closing(client(application)[0]) as api:
        v=creer(api);raw=pdf_fictif();r=ok(joindre(api,v,raw=raw),201)
        avant=donnees_metier(application);acl=catalogue_acl(application['engine'])
        with application['engine'].connect() as db:
            sequence=db.execute(text('SELECT last_value,is_called FROM liasse_balance_documents_id_seq')).one()
        appliquer(application,'104_liasse_balance_documents.sql')
        assert donnees_metier(application)==avant and catalogue_acl(application['engine'])==acl
        with application['engine'].connect() as db:
            assert db.execute(text('SELECT last_value,is_called FROM liasse_balance_documents_id_seq')).one()==sequence
        assert ok(api.get(path(v)))['documents']==[r]
        assert api.get(path(v)+f'/{r["id"]}').content==raw
