"""086 : acomptes/avoirs sous vrai LOGIN non propriétaire et JWT réels."""
from datetime import date
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import acomptes
import avoirs
import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK
from test_complements_structure_postgres import refuser
from test_permissions_documents_commerciaux_postgres import (
    cible as cible_documents, acl, inscrire, ok,
)

SQL = '086_permissions_acomptes_avoirs.sql'
TABLES = ('acomptes','avoirs','lignes_avoir')


@pytest.fixture(scope='module')
def cible(cible_documents):
    c=cible_documents
    c['avant086']=acl(c['owner'])
    for table in TABLES:
        refuser(c['runtime'],f'INSERT INTO public.{table} DEFAULT VALUES','42501')
    if (BACK/SQL).is_file():
        c['migration'](SQL);c['migration'](SQL)
    c['client'].app.include_router(acomptes.router)
    c['client'].app.include_router(avoirs.router)
    with TestClient(c['client'].app) as client:
        yield {**c,'client':client}


def valider(api):
    rows=ok(api.get('/api/ecritures',params={'exercice':date.today().year}))
    for row in rows:
        if not row['est_validee']:
            ok(api.post(f"/api/ecritures/{row['id']}/valider"))


def dossier(cible,sens):
    api=cible['client'];_,user=inscrire(cible,'avance-credit-'+sens)
    tier=ok(api.post('/api/tiers',json={'nom':'Tiers particulier fictif086',
        'type':'client' if sens=='vente' else 'fournisseur','categorie_fiscale':'particulier'}),201)
    factures=[];jour=date.today().isoformat()
    for i in range(2):
        f=ok(api.post('/api/factures',json={'type':sens,'date':jour,'tiers':tier['nom'],
            'tiers_id':tier['id'],'reference':f'PIECE086-{i}',
            'nature_tva_achat':'charge','tva_deductible_pct':100,
            'lignes':[{'description':'Prestation fictive086','quantite':1,'prix_unitaire':100,'tva':20}]}),201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        factures.append(f)
    valider(api)
    return api,user,tier,factures


def solde(api,fid):
    return ok(api.get(f'/api/factures/{fid}/reglements'))['solde_restant']


def originaux(cible,sid):
    with cible['owner'].connect() as db:
        return {e.id:(e.j,db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l '
            'WHERE ecriture_id=:eid ORDER BY id'),{'eid':e.id}).scalars().all())
            for e in db.execute(text('SELECT id,row_to_json(e)::text AS j FROM ecritures e '
                'WHERE societe_id=:sid AND est_validee ORDER BY id'),{'sid':sid})}


def conserver(cible,sid,avant):
    apres=originaux(cible,sid)
    assert all(apres[eid]==row for eid,row in avant.items())


def bilan(cible,sid,attendus):
    with cible['runtime'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid AND est_validee'),{'sid':sid})==len(attendus)
        par_piece=db.execute(text('SELECT sum(l.debit),sum(l.credit) FROM lignes_ecriture l '
            'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid GROUP BY e.id ORDER BY e.id'),{'sid':sid}).all()
        assert par_piece==[(montant,montant) for montant in attendus]
        assert db.execute(text('SELECT sum(l.debit),sum(l.credit) FROM lignes_ecriture l '
            'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid'),{'sid':sid}).one()==(sum(attendus),sum(attendus))


@pytest.mark.parametrize('sens',['vente','achat'])
def test086_cycle_acompte_partiel_imputations_annulations_conserve_origines(cible,sens):
    api,user,tier,fs=dossier(cible,sens);sid=user['societe_id'];jour=date.today().isoformat()
    a=ok(api.post('/api/acomptes',json={'type':'client' if sens=='vente' else 'fournisseur',
        'date':jour,'tiers':tier['nom'],'tiers_id':tier['id'],'montant':60,
        'mode':'virement','reference':'AVANCE086','comptabiliser':True}),201)
    aid=a['id'];valider(api)
    avant=originaux(cible,sid)
    for f,montant in zip(fs,[40,20]):
        a=ok(api.post(f'/api/acomptes/{aid}/imputer',json={'facture_id':f['id'],
            'montant':montant,'date_imputation':jour,'comptabiliser':True}))
    valider(api);conserver(cible,sid,avant)
    assert [solde(api,f['id']) for f in fs]==[80,100]
    a=next(row for row in ok(api.get('/api/acomptes',params={'exercice':date.today().year})) if row['id']==aid)
    imps=a['imputations'];assert len(imps)==2
    assert api.post(f'/api/acomptes/{aid}/annuler',json={}).status_code==409
    avant=originaux(cible,sid)
    for row in imps:
        ok(api.post(f"/api/acomptes/{aid}/imputations/{row['id']}/annuler"))
        valider(api);conserver(cible,sid,avant)
    ok(api.post(f'/api/acomptes/{aid}/annuler',json={}))
    valider(api);conserver(cible,sid,avant)
    assert [solde(api,f['id']) for f in fs]==[120,120]
    assert api.delete(f'/api/acomptes/{aid}').status_code==409
    with cible['runtime'].connect() as db:
        assert db.scalar(text('SELECT statut FROM acomptes WHERE id=:id'),{'id':aid})=='annule'
        rows=db.execute(text('SELECT statut,ecriture_id,ecriture_annulation_id,annulee_par '
            'FROM imputations_acomptes WHERE acompte_id=:id'),{'id':aid}).all()
        assert len(rows)==2 and all(r.statut=='annulee' and r.ecriture_id and r.ecriture_annulation_id
                                  and r.annulee_par==user['id'] for r in rows)
    bilan(cible,sid,[120,120,60,40,20,40,20,60])


@pytest.mark.parametrize('sens',['vente','achat'])
def test086_cycle_avoir_credit_remboursement_annulation_conserve_origines(cible,sens):
    api,user,tier,fs=dossier(cible,sens);sid=user['societe_id'];jour=date.today().isoformat()
    ok(api.post('/api/reglements',json={'facture_id':fs[0]['id'],'tiers':tier['nom'],
        'date':jour,'montant':120,'mode':'virement','comptabiliser':True}),201)
    valider(api);avant=originaux(cible,sid)
    a=ok(api.post('/api/avoirs',json={'facture_id':fs[0]['id'],'date':jour,
        'motif':'Correction fictive086','retour_stock':False,
        'lignes':[{'facture_ligne_id':fs[0]['lignes'][0]['id'],'quantite':0.5}]}),201)
    aid=a['id'];ok(api.post(f'/api/avoirs/{aid}/comptabiliser'));valider(api)
    conserver(cible,sid,avant)
    for nature,montant in [('imputation',30),('remboursement',20)]:
        a=ok(api.post(f'/api/avoirs/{aid}/utiliser',json={'type_utilisation':nature,
            'date_utilisation':jour,'facture_id':fs[1]['id'] if nature=='imputation' else None,
            'montant':montant,'mode':'virement','reference':'CREDIT086'}))
    valider(api);assert solde(api,fs[1]['id'])==90
    assert a['montant_disponible']==10
    assert api.post(f'/api/avoirs/{aid}/annuler').status_code==409
    avant=originaux(cible,sid)
    for row in a['utilisations']:
        ok(api.post(f"/api/avoirs/{aid}/utilisations/{row['id']}/annuler"))
        valider(api);conserver(cible,sid,avant)
    ok(api.post(f'/api/avoirs/{aid}/annuler'));valider(api)
    conserver(cible,sid,avant)
    assert [solde(api,f['id']) for f in fs]==[0,120]
    assert api.delete(f'/api/avoirs/{aid}').status_code==409
    with cible['runtime'].connect() as db:
        assert db.scalar(text('SELECT statut FROM avoirs WHERE id=:id'),{'id':aid})=='annule'
        assert db.scalar(text("SELECT count(*) FROM utilisations_avoirs WHERE avoir_id=:id AND statut='annulee'"),{'id':aid})==2
    # Deux factures120,paiement120,avoir60,remboursement20,inverse20,inverseavoir60.
    bilan(cible,sid,[120,120,120,60,20,20,60])


def test086_acl_minimales_rejeu_et_heritage_des_traces_preserves(cible):
    assert (BACK/SQL).is_file()
    avant,seq_avant=cible['avant086'];apres,seq_apres=acl(cible['owner'])
    assert seq_avant==seq_apres
    assert all(apres[t]==avant[t] for t in avant if t not in TABLES)
    for table in TABLES:
        assert apres[table]=={'SELECT':True,'INSERT':True,'UPDATE':table!='lignes_avoir',
                              'DELETE':False,'TRUNCATE':False}
        refuser(cible['runtime'],f'DELETE FROM public.{table}','42501')
        refuser(cible['runtime'],f'TRUNCATE public.{table}','42501')
        with cible['runtime'].connect() as db:
            seq=db.scalar(text("SELECT pg_get_serial_sequence(:table,'id')"),{'table':table})
            for op in ('USAGE','SELECT'):
                assert db.scalar(text('SELECT has_sequence_privilege(current_user,:seq,:op)'),{'seq':seq,'op':op})
    refuser(cible['runtime'],'UPDATE lignes_avoir SET quantite=quantite','42501')
    cible['migration'](SQL)
    assert acl(cible['owner'])==(apres,seq_apres)


def test086_rejeu_conserve_les_documents_traces_et_origines(cible):
    def photo():
        with cible['owner'].connect() as db:
            return {t:db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY id')).scalars().all()
                for t in (*TABLES,'imputations_acomptes','utilisations_avoirs',
                          'factures','lignes_facture','reglements','ecritures','lignes_ecriture')}
    avant=photo();cible['migration'](SQL)
    assert photo()==avant


def test086_auth_roles_et_isolation_societe(cible):
    api,user,tier,fs=dossier(cible,'vente');jour=date.today().isoformat()
    token=api.headers['Authorization']
    body={'type':'client','tiers':tier['nom'],'tiers_id':tier['id'],'date':jour,
          'montant':60,'mode':'virement','comptabiliser':False}
    a=ok(api.post('/api/acomptes',json=body),201)
    with Session(cible['owner']) as db:
        admin=db.get(models.Utilisateur,user['id'])
        email=f'lecture086-{uuid.uuid4().hex[:8]}@example.invalid'
        db.add(models.Utilisateur(societe_id=user['societe_id'],nom='Lecture fictive086',email=email,
            hashed_password=admin.hashed_password,role='lecture',actif=True));db.commit()
    login=ok(api.post('/api/auth/login',json={'email':email,'password':'Documents085!Sure'}))
    entete={'Authorization':'Bearer '+login['access_token']}
    assert ok(api.get('/api/acomptes',params={'exercice':date.today().year},headers=entete))
    assert api.post('/api/acomptes',json=body,headers=entete).status_code==403
    assert api.post('/api/avoirs',json={'facture_id':fs[0]['id'],'date':jour,
        'lignes':[{'facture_ligne_id':fs[0]['lignes'][0]['id'],'quantite':0.5}]},headers=entete).status_code==403
    inscrire(cible,'autre086')
    assert ok(api.get('/api/acomptes',params={'exercice':date.today().year}))==[]
    assert api.post(f"/api/acomptes/{a['id']}/annuler",json={}).status_code==404
    assert api.post('/api/avoirs',json={'facture_id':fs[0]['id'],'date':jour,
        'lignes':[{'facture_ligne_id':fs[0]['lignes'][0]['id'],'quantite':0.5}]}).status_code==404
    api.headers['Authorization']=token


def test086_role_absent_ne_cree_aucun_objet():
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
