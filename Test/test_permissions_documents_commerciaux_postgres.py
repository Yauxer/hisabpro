"""085 : vrais JWT et SQL runtime sur un PostgreSQL nonce consolidé."""
from datetime import date
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import lettrage
import models
from database import get_db
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK
from recette_installation_vierge_consolidee import COMPLEMENTS
from routers import auth, articles, commercial, ecritures, factures, societe, tiers
from test_permissions_cycle_facturation_postgres import installation, ok
from test_complements_structure_postgres import refuser

SQL = '085_permissions_documents_commerciaux.sql'
TABLES = ('devis','lignes_devis','bons_commande','lignes_bon_commande',
          'bons_livraison','lignes_bon_livraison')


def acl(engine):
    with engine.connect() as db:
        tables=db.execute(text("SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace "
                               "AND relkind IN ('r','p') ORDER BY relname")).scalars().all()
        droits={table:{op:db.scalar(text('SELECT has_table_privilege(\'hisabpro\',:table,:op)'),
            {'table':table,'op':op}) for op in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE')}
            for table in tables}
        sequences=dict(db.execute(text("SELECT relname,has_sequence_privilege('hisabpro',oid,'UPDATE') "
            "FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='S'")).all())
    return droits,sequences


@pytest.fixture(scope='module')
def cible():
    with installation() as cible:
        for nom in COMPLEMENTS:
            if int(nom.split('_',1)[0]) >= 78:
                cible['migration'](nom)
        for nom in ('083_ras_reglements.sql','084_rapprochement_ventilations.sql'):
            cible['migration'](nom)
        cible['avant_acl']=acl(cible['owner'])
        for table in TABLES:
            refuser(cible['runtime'],f'INSERT INTO public.{table} DEFAULT VALUES','42501')
        if (BACK/SQL).exists():
            cible['migration'](SQL)
            cible['migration'](SQL)
        app=FastAPI()
        for router in (auth.router,societe.router,tiers.router,articles.router,
            commercial.router_devis,commercial.router_bc,commercial.router_bl,
            commercial.router_regl,factures.router,ecritures.router,lettrage.router):
            app.include_router(router)
        def runtime():
            cible['garde']()
            with Session(cible['runtime']) as db:
                assert db.scalar(text('SELECT current_user'))=='hisabpro'
                yield db
        app.dependency_overrides[get_db]=runtime
        with TestClient(app,raise_server_exceptions=False) as client:
            cible['client']=client
            yield cible


def inscrire(cible,tag):
    api=cible['client']
    api.headers.pop('Authorization',None)
    credentials={'email':f'{tag}-{uuid.uuid4().hex[:8]}@example.invalid','password':'Documents085!Sure'}
    token=ok(api.post('/api/auth/register',json={**credentials,'nom':'Administrateur fictif',
        'raison_sociale':'Documents085 fictifs '+tag}))['access_token']
    api.headers['Authorization']='Bearer '+token
    user=ok(api.get('/api/auth/me'))
    return credentials,user


@pytest.fixture(scope='module',params=[('vente',False),('achat',False),('vente',True),('achat',True)])
def cycle(cible,request):
    sens,stockable=request.param
    credentials,user=inscrire(cible,sens)
    api=cible['client'];jour=date.today().isoformat()
    tier=ok(api.post('/api/tiers',json={'type':'client' if sens=='vente' else 'fournisseur',
        'nom':'Tiers particulier fictif085 '+sens,'categorie_fiscale':'particulier'}),201)
    article=ok(api.post('/api/articles',json={'code':'DOC085','designation':'Article fictif085',
        'prix_vente_ht':100,'prix_achat_ht':100,'tva':20,'is_stockable':stockable,
        'stock_actuel':3 if sens=='vente' and stockable else 0,
        'compte_vente':'7111' if stockable else '7121','compte_achat':'6111' if stockable else '6126'}),201)
    ligne={'description':'Prestation fictive085','quantite':1,'prix_unitaire':100,'tva':20}
    ligne['article_id']=article['id']
    did=None
    if sens=='vente':
        devis=ok(api.post('/api/devis',json={'date':jour,'tiers':tier['nom'],
            'tiers_id':tier['id'],'reference':'SOURCE085','lignes':[ligne]}),201)
        did=devis['id']
        ok(api.patch(f'/api/devis/{did}',json={'statut':'accepte'}))
        bc=ok(api.post(f'/api/devis/{did}/convertir-bc'))
    else:
        bc=ok(api.post('/api/bons-commande',json={'type':'achat','date':jour,
            'tiers':tier['nom'],'tiers_id':tier['id'],'reference':'SOURCE085','lignes':[ligne]}),201)
    bcid=bc['id']
    bon=ok(api.post(f'/api/bons-commande/{bcid}/convertir-bl',json={'date':jour}))
    bid=bon['id']
    for statut in ('expedie','livre'):
        ok(api.patch(f'/api/bons-livraison/{bid}',json={'statut':statut}))
    with cible['runtime'].connect() as db:
        assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:id'),{'id':article['id']})==(3 if sens=='vente' and stockable else 0)
    facture=ok(api.post(f'/api/bons-livraison/{bid}/convertir-facture',json={'date':jour}))
    fid=facture['id']
    if sens=='achat':
        ok(api.patch(f'/api/factures/{fid}',json={'reference':'FOURNISSEUR085',
            'nature_tva_achat':'charge','tva_deductible_pct':100}))
    ok(api.post(f'/api/factures/{fid}/valider'))
    compta=ok(api.post(f'/api/factures/{fid}/comptabiliser'))
    paiement=ok(api.post('/api/reglements',json={'facture_id':fid,'date':jour,
        'tiers':tier['nom'],'montant':120,'mode':'virement','reference':'VIR085',
        'comptabiliser':True}),201)
    for eid in (compta['ecriture_id'],paiement['ecriture_id']):
        ok(api.post(f'/api/ecritures/{eid}/valider'))
    with cible['runtime'].connect() as db:
        lignes=db.execute(text('SELECT l.id,l.debit,l.credit FROM lignes_ecriture l '
            'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid AND l.compte=:compte ORDER BY l.id'),
            {'sid':user['societe_id'],'compte':'3421' if sens=='vente' else '4411'}).all()
    assert len(lignes)==2 and sum(l.debit-l.credit for l in lignes)==0
    resultat=ok(api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':[l.id for l in lignes]}))
    assert len(resultat['code'])>=3 and resultat['nb']==2
    return dict(sens=sens,stockable=stockable,aid=article['id'],credentials=credentials,user=user,did=did,bcid=bcid,bid=bid,fid=fid,
                code=resultat['code'],token=api.headers['Authorization'])


def test085_cycle_documentaire_facture_reglement_validation_et_lettrage(cible,cycle):
    api=cible['client'];api.headers['Authorization']=cycle['token']
    with cible['runtime'].connect() as db:
        sid=cycle['user']['societe_id']
        assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid AND est_validee'),{'sid':sid})==2
        assert db.execute(text('SELECT sum(l.debit),sum(l.credit) FROM lignes_ecriture l '
            'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid'),{'sid':sid}).one()==(240,240)
        assert db.scalar(text('SELECT count(*) FROM lettrages_comptables WHERE societe_id=:sid AND actif'),{'sid':sid})==2
        assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:id'),{'id':cycle['aid']})==(
            (2 if cycle['sens']=='vente' else 1) if cycle['stockable'] else 0)
        f=db.execute(text('SELECT f.type,b.bon_commande_id,b.id,f.est_validee,f.est_comptabilisee '
            'FROM factures f JOIN bons_livraison b ON b.facture_id=f.id WHERE f.id=:id'),{'id':cycle['fid']}).one()
        assert tuple(f)==(cycle['sens'],cycle['bcid'],cycle['bid'],True,True)
        assert db.scalar(text('SELECT count(*) FROM lignes_facture f JOIN lignes_bon_livraison b '
            'ON b.id=f.source_ligne_bl_id JOIN lignes_bon_commande c ON c.id=f.source_ligne_bc_id '
            'WHERE f.facture_id=:id AND b.bon_livraison_id=:bid AND c.bon_commande_id=:bcid'),
            {'id':cycle['fid'],'bid':cycle['bid'],'bcid':cycle['bcid']})==1
    assert next(f for f in ok(api.get('/api/factures',params={'exercice':date.today().year}))
                if f['id']==cycle['fid'])['statut']=='payee'
    assert api.post(f"/api/bons-livraison/{cycle['bid']}/convertir-facture",json={}).status_code==409
    if cycle['did']:
        assert api.post(f"/api/devis/{cycle['did']}/convertir-bc").status_code==409


def test085_acl_fermees_rejeu_et_aucun_privilege_technique_ajoute(cible):
    assert (BACK/SQL).is_file()
    avant,seq_avant=cible['avant_acl'];apres,seq_apres=acl(cible['owner'])
    assert seq_avant==seq_apres
    assert all(apres[t]==avant[t] for t in avant if t not in TABLES)
    for table in TABLES:
        assert apres[table]=={'SELECT':True,'INSERT':True,'UPDATE':True,'DELETE':True,'TRUNCATE':False}
        with cible['runtime'].begin() as db:
            seq=db.scalar(text("SELECT pg_get_serial_sequence(:table,'id')"),{'table':table})
            for op in ('USAGE','SELECT'):
                assert db.scalar(text('SELECT has_sequence_privilege(current_user,:seq,:op)'),{'seq':seq,'op':op})
            db.execute(text(f'UPDATE public.{table} SET id=id WHERE false'))
            db.execute(text(f'DELETE FROM public.{table} WHERE false'))
        refuser(cible['runtime'],f'TRUNCATE public.{table}','42501')
    refuser(cible['runtime'],'CREATE TABLE public.contournement085(id integer)','42501')
    with cible['runtime'].connect() as db:
        assert db.execute(text('SELECT current_user,session_user')).one()==('hisabpro','hisabpro')
        assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
        assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
    cible['migration'](SQL)
    assert acl(cible['owner'])==(apres,seq_apres)


def test085_auth_rbac_et_autre_societe_restent_controles(cible,cycle):
    api=cible['client'];api.headers['Authorization']=cycle['token']
    sid=cycle['user']['societe_id']
    with Session(cible['owner']) as db:
        admin=db.get(models.Utilisateur,cycle['user']['id'])
        email=f'lecture085-{uuid.uuid4().hex[:8]}@example.invalid'
        lecteur=models.Utilisateur(societe_id=sid,nom='Lecteur fictif085',email=email,
            hashed_password=admin.hashed_password,role='lecture',actif=True)
        db.add(lecteur);db.commit()
    login=ok(api.post('/api/auth/login',json={'email':email,'password':cycle['credentials']['password']}))
    entete={'Authorization':'Bearer '+login['access_token']}
    assert ok(api.get('/api/bons-commande',params={'exercice':date.today().year},headers=entete))
    assert api.patch(f"/api/bons-commande/{cycle['bcid']}",json={'notes':'Interdit'},headers=entete).status_code==403
    assert api.post(f"/api/bons-livraison/{cycle['bid']}/convertir-facture",json={},headers=entete).status_code==403
    inscrire(cible,'autre')
    assert ok(api.get('/api/bons-commande',params={'exercice':date.today().year}))==[]
    assert api.patch(f"/api/bons-commande/{cycle['bcid']}",json={'notes':'Interdit'}).status_code==404
    assert api.post(f"/api/bons-livraison/{cycle['bid']}/convertir-facture",json={}).status_code==404
    api.headers['Authorization']=cycle['token']


def test085_rejeu_sur_documents_et_ecritures_definitives_ne_change_pas_les_sources(cible,cycle):
    def photo():
        with cible['owner'].connect() as db:
            return {t:db.execute(text(f'SELECT row_to_json(t)::text FROM public.{t} t ORDER BY id')).scalars().all()
                for t in (*TABLES,'factures','lignes_facture','reglements','ecritures',
                          'lignes_ecriture','mouvements_stock','lettrages_comptables')}
    avant=photo()
    cible['migration'](SQL)
    assert photo()==avant
    sid=cycle['user']['societe_id']
    refuser(cible['runtime'],f"UPDATE ecritures SET libelle='Interdit085' WHERE societe_id={sid}",'23514')
    refuser(cible['runtime'],f'DELETE FROM lignes_ecriture WHERE ecriture_id IN (SELECT id FROM ecritures WHERE societe_id={sid})','23514')
    assert photo()==avant


def test085_modification_et_suppression_des_trois_brouillons_avec_lignes(cible):
    inscrire(cible,'brouillons')
    api=cible['client'];jour=date.today().isoformat()
    ligne={'description':'Brouillon fictif085','quantite':1,'prix_unitaire':100,'tva':20}
    for route,lignes in (('devis',[ligne]),('bons-commande',[ligne]),
        ('bons-livraison',[{'description':'Brouillon fictif085','quantite_prevue':1,
                           'quantite_livree':1,'prix_unitaire':100,'tva':20}])):
        document=ok(api.post('/api/'+route,json={'date':jour,'tiers':'Tiers fictif085','lignes':lignes}),201)
        ok(api.patch(f"/api/{route}/{document['id']}",json={'notes':'Note fictive modifiée'}))
        ok(api.delete(f"/api/{route}/{document['id']}"),204)
        assert ok(api.get('/api/'+route,params={'exercice':date.today().year}))==[]


def test085_role_absent_ne_cree_rien_et_rejeu_ne_modifie_pas_le_schema():
    with cluster_isole() as cluster:
        assert verifier_cible_isolee(cluster['url'],cluster['directory'],cluster['nonce'])
        engine=create_engine(cluster['url'])
        try:
            for _ in range(2):
                raw=engine.raw_connection()
                try:
                    with raw.cursor() as cursor:
                        cursor.execute((BACK/SQL).read_text(encoding='utf-8'))
                    raw.commit()
                finally:
                    raw.close()
            with engine.connect() as db:
                assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
                assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace"))
        finally:
            engine.dispose()
    assert not cluster['directory'].exists()
