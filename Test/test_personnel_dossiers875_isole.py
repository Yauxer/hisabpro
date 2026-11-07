"""Migration106 et préflight connectés à PG natif nonce, jamais base utilisateur."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from decimal import Decimal
import time
import pytest
import httpx
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_personnel_habilitations873_isole import (
    application as application873, application093, application092, application091,
    application090, application089, application087, migration,
    employee,role_client,grant,activer,originaux,P,IDENTITE,AUDIT,client,ok)
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1]
TABLES=['personnel_dossiers','personnel_demandes','personnel_contrats_versions','personnel_remunerations_versions','personnel_evenements']


def appliquer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cursor:cursor.execute((R/'hisabpro-backend/106_personnel_dossiers_versions.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application873):
    app=application873
    avant=empreintes_tables(app['engine'])
    appliquer(app);appliquer(app)
    apres=empreintes_tables(app['engine'])
    assert all(apres[t]==h for t,h in avant.items())
    yield app


def exec_owner(app,sql,params=None):
    with app['engine'].begin() as db:
        resultat=db.execute(text(sql),params or {})
        return resultat.scalar() if resultat.returns_rows else None


def refuser(app,sql,params=None,engine=None,codes=('23514','23503','23505','42501')):
    with pytest.raises(DBAPIError) as e:
        with (engine or app['engine']).begin() as db:db.execute(text(sql),params or {})
    assert e.value.orig.pgcode in codes


def preparer(app,api,*,matricule='002'):
    from test_paie_grh_postgres import dossier
    e=ok(api.post('/api/employes',json=dossier(matricule=matricule)),201)
    me=ok(api.get('/api/auth/me'));lecteur,u,_,_=role_client(app,api,'comptable');lecteur.close()
    p={'e':e['id'],'s':me['societe_id'],'u':me['id'],'v':u['id'],'m':matricule.strip(' \t\n\r\f\v')}
    exec_owner(app,"INSERT INTO personnel_dossiers(employe_id,societe_id,matricule_cle,origine,cree_par) VALUES(:e,:s,:m,'historique_a_confirmer',:u)",p)
    return p


def demande(app,p,nature='CONTRAT',*,approuve=True):
    sql="INSERT INTO personnel_demandes(societe_id,employe_id,nature,revision_attendue,prepare_par,motif,statut,soumis_at,decision_par,decision_at,motif_decision) VALUES(:s,:e,:n,0,:u,'Fictif875',:st,CASE WHEN :a THEN CURRENT_TIMESTAMP END,CASE WHEN :a THEN :v END,CASE WHEN :a THEN CURRENT_TIMESTAMP END,CASE WHEN :a THEN 'Accord fictif875' END) RETURNING id"
    return exec_owner(app,sql,dict(p,n=nature,st='APPROUVE' if approuve else 'BROUILLON',a=approuve))


def contrat(app,p,version=1,effet='2026-01-01',*,approuve=True):
    d=demande(app,p,approuve=approuve)
    return exec_owner(app,"INSERT INTO personnel_contrats_versions(societe_id,employe_id,demande_id,version,date_effet,type_contrat,date_debut,reference_justificatif,approuvee_par,approuvee_at) SELECT :s,:e,:d,:v,CAST(:dt AS date),'CDI','2026-01-01','Justificatif fictif',decision_par,decision_at FROM personnel_demandes WHERE id=:d RETURNING id",dict(p,d=d,v=version,dt=effet))


def remuneration(app,p,c,version=1,effet='2026-01-01',montant='9000.10',*,approuve=True):
    d=demande(app,p,'REMUNERATION',approuve=approuve)
    return exec_owner(app,"INSERT INTO personnel_remunerations_versions(societe_id,employe_id,demande_id,contrat_version_id,version,date_effet,montant,periodicite,reference_justificatif,approuvee_par,approuvee_at) SELECT :s,:e,:d,:c,:v,CAST(:dt AS date),:mt,'mensuelle','Justificatif fictif',decision_par,decision_at FROM personnel_demandes WHERE id=:d RETURNING id",dict(p,d=d,c=c,v=version,dt=effet,mt=montant))


def test_875_preflight_vierge_historique_et_droits(application):
    app=application
    with closing(client(app)[0]) as api:
        r=api.get(P+'/preflight-dossiers');assert r.status_code==200 and r.headers['cache-control']=='no-store'
        q=r.json();assert q['nombre_employes']==0 and q['schema_versions']=='installe' and not q['activation_paie_autorisee']
        employee(api);me=ok(api.get('/api/auth/me'));avant=originaux(app,me['societe_id'])
        activer(api);assert api.get(P+'/preflight-dossiers').status_code==403
        grant(api,me['id'],IDENTITE);assert api.get(P+'/preflight-dossiers').status_code==403
        grant(api,me['id'],AUDIT)
        q=ok(api.get(P+'/preflight-dossiers'));assert q['nombre_employes']==1 and not q['historique_atteste']
        lecteur,u,_,_=role_client(app,api)
        with closing(lecteur):
            grant(api,u['id'],IDENTITE);grant(api,u['id'],AUDIT)
            assert lecteur.get(P+'/preflight-dossiers').status_code==403
        assert originaux(app,me['societe_id'])==avant
        ok(api.patch('/api/societe/modules',json={'module':'paie_grh','actif':False}))
        assert api.get(P+'/preflight-dossiers').status_code==403
    with httpx.Client(base_url=app['api_url']) as anon:assert anon.get(P+'/preflight-dossiers').status_code==401


def test_875_diagnostic_collisions_inconnus_et_pas_de_fuite(application):
    app=application
    from test_paie_grh_postgres import dossier
    with closing(client(app)[0]) as api,closing(client(app)[0]) as autre:
        secret=ok(autre.post('/api/employes',json=dossier(matricule='AUTRE-SOCIETE-PRIVE')),201)
        ids=[]
        for m in ['002','002','02','2',None,'X']:
            ids.append(ok(api.post('/api/employes',json=dossier(matricule=m,date_embauche=None)),201)['id'])
        me=ok(api.get('/api/auth/me'));sid=me['societe_id']
        exec_owner(app,"UPDATE employes SET matricule=E' 002\t' WHERE id=:e",{'e':ids[1]})
        exec_owner(app,"UPDATE employes SET salaire_brut='NaN'::float8 WHERE id=:e",{'e':ids[-1]})
        avant=originaux(app,sid)
        r=api.get(P+'/preflight-dossiers?limite=1&societe_id='+str(ok(autre.get('/api/auth/me'))['societe_id']))
        q=ok(r);assert q['societe_id']==sid and q['nombre_employes']==6
        assert q['collisions_matricules']=={'nombre':1,'groupes':[{'matricule_cle':'002','employe_ids':[ids[0]],'nombre':2}],'tronque':False}
        assert q['matricules_manquants']['nombre']==1 and q['dates_entree_inconnues']['nombre']==6
        assert q['dates_entree_inconnues']['tronque'] and q['salaires_invalides']['employe_ids']==[ids[-1]]
        assert not q['reprise_sans_ambiguite_matricule']
        assert 'AUTRE-SOCIETE-PRIVE' not in r.text and '10000' not in r.text and 'FICTIF-NON-DECLARABLE' not in r.text
        assert api.get(P+'/preflight-dossiers?limite=0').status_code==422
        assert api.get(P+'/preflight-dossiers?limite=101').status_code==422
        assert originaux(app,sid)==avant


def test_875_matricule_normalise_sql_et_python_identiques(application):
    from services.personnel_dossiers_service import normaliser_matricule
    for v in [None,'',' \t\n',' 002\t','02','2','Ab','aB','a  b','\u00a0X\u00a0']:
        assert exec_owner(application,'SELECT hisabpro_personnel_matricule(:v)',{'v':v})==normaliser_matricule(v)


def test_875_matricules_source_ambigu_pas_de_reparation(application):
    app=application
    from test_paie_grh_postgres import dossier
    with closing(client(app)[0]) as api:
        a=ok(api.post('/api/employes',json=dossier(matricule='DUP')),201)
        b=ok(api.post('/api/employes',json=dossier(matricule='DUP')),201)
        me=ok(api.get('/api/auth/me'));p={'s':me['societe_id'],'u':me['id'],'e':a['id']};avant=originaux(app,p['s'])
        refuser(app,"INSERT INTO personnel_dossiers(employe_id,societe_id,matricule_cle,origine,cree_par) VALUES(:e,:s,'DUP','historique_a_confirmer',:u)",p)
        assert originaux(app,p['s'])==avant
        assert exec_owner(app,'SELECT count(*) FROM personnel_dossiers WHERE societe_id=:s',p)==0


def test_875_versions_exactes_futures_sans_recriture_et_rejeu(application):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api);avant=originaux(app,p['s']);c=contrat(app,p)
        a=remuneration(app,p,c);b=remuneration(app,p,c,2,'2027-01-01','9876.54')
        remuneration(app,p,c,3,'2026-06-01','9999.99',approuve=False)
        with app['personnel_runtime'].connect() as db:
            rows=db.execute(text('SELECT id,montant,date_effet,date_fin_effet_exclue FROM personnel_remunerations_periodes WHERE societe_id=:s ORDER BY date_effet'),p).all()
            assert len(rows)==2 and rows[0][0]==a and rows[1][0]==b
            assert rows[0][1]==Decimal('9000.10') and str(rows[0][3])=='2027-01-01' and rows[1][3] is None
            for jour,mt in [('2026-12-31','9000.10'),('2027-01-01','9876.54')]:
                v=db.execute(text('SELECT montant FROM personnel_remunerations_periodes WHERE societe_id=:s AND date_effet<=CAST(:d AS date) AND (date_fin_effet_exclue IS NULL OR date_fin_effet_exclue>CAST(:d AS date))'),dict(p,d=jour)).all()
                assert v==[(Decimal(mt),)]
        avant_rejeu=empreintes_tables(app['engine']);appliquer(app);appliquer(app)
        assert empreintes_tables(app['engine'])==avant_rejeu
        assert originaux(app,p['s'])==avant


@pytest.mark.parametrize('table',['personnel_contrats_versions','personnel_remunerations_versions','personnel_demandes','personnel_evenements','personnel_dossiers'])
def test_875_historique_pas_de_suppression_ou_truncate(application,table):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api);c=contrat(app,p);remuneration(app,p,c)
        exec_owner(app,"INSERT INTO personnel_evenements(societe_id,employe_id,revision,nature,auteur_id,motif) VALUES(:s,:e,0,'CONSTAT',:u,'Fictif875')",p)
        refuser(app,f'DELETE FROM {table} WHERE societe_id=:s',p)
        refuser(app,f'TRUNCATE {table} CASCADE')
        if table=='personnel_evenements':refuser(app,f"UPDATE {table} SET motif='Effacement' WHERE societe_id=:s",p)
        elif table.endswith('_versions'):refuser(app,f'UPDATE {table} SET date_effet=date_effet+1 WHERE societe_id=:s',p)
        elif table=='personnel_demandes':refuser(app,f"UPDATE {table} SET motif='Effacement' WHERE societe_id=:s",p)


@pytest.mark.parametrize('montant',['NaN','Infinity','-Infinity','-0.01','10000000000000000'])
def test_875_sql_montants_invalides(application,montant):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api);c=contrat(app,p)
        with pytest.raises(DBAPIError):remuneration(app,p,c,montant=montant)


def test_875_grants_runtime_lecture_seule_et_approbation_independante(application):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api);c=contrat(app,p)
        for table in TABLES:
            assert exec_owner(app,"SELECT has_table_privilege('hisabpro',:t,'SELECT')",{'t':table})
            assert not exec_owner(app,"SELECT has_table_privilege('hisabpro',:t,'INSERT,UPDATE,DELETE,TRUNCATE')",{'t':table})
        refuser(app,'UPDATE personnel_dossiers SET revision=1 WHERE employe_id=:e',p,engine=app['personnel_runtime'])
        # Pas d'auto-approbation même comme propriétaire SQL.
        refuser(app,"INSERT INTO personnel_demandes(societe_id,employe_id,nature,revision_attendue,prepare_par,motif,statut,soumis_at,decision_par,decision_at,motif_decision) VALUES(:s,:e,'CONTRAT',0,:u,'Fictif','APPROUVE',CURRENT_TIMESTAMP,:u,CURRENT_TIMESTAMP,'Refus')",p)
        refuser(app,"UPDATE personnel_dossiers SET utilisateur_beneficiaire_id=:v WHERE employe_id=:e",dict(p,v=999999))
        refuser(app,"UPDATE employes SET matricule='AUTRE' WHERE id=:e",p)


def test_875_cle_composite_et_date_approbation_coherentes(application):
    app=application
    with closing(client(app)[0]) as api,closing(client(app)[0]) as autre:
        p=preparer(app,api);b=preparer(app,autre);c=contrat(app,p)
        d=demande(app,b,'REMUNERATION')
        refuser(app,"INSERT INTO personnel_remunerations_versions(societe_id,employe_id,demande_id,contrat_version_id,version,date_effet,montant,periodicite,reference_justificatif) VALUES(:s,:e,:d,:c,1,'2026-01-01',100,'mensuelle','Fictif')",dict(b,d=d,c=c))
        d=demande(app,p,'REMUNERATION',approuve=False)
        refuser(app,"INSERT INTO personnel_remunerations_versions(societe_id,employe_id,demande_id,contrat_version_id,version,date_effet,montant,periodicite,reference_justificatif,approuvee_par,approuvee_at) VALUES(:s,:e,:d,:c,1,'2026-01-01',100,'mensuelle','Fictif',:v,CURRENT_TIMESTAMP)",dict(p,d=d,c=c))
        refuser(app,"INSERT INTO personnel_demandes(societe_id,employe_id,nature,revision_attendue,prepare_par,motif,statut,soumis_at,decision_par,motif_decision) VALUES(:s,:e,'CONTRAT',0,:u,'Fictif','APPROUVE',CURRENT_TIMESTAMP,:v,'Refus sans date')",p)


def test_875_meme_matricule_autre_societe_et_concurrence(application):
    app=application
    with closing(client(app)[0]) as api,closing(client(app)[0]) as autre:
        p=preparer(app,api);b=preparer(app,autre)
        assert p['m']==b['m'] and p['s']!=b['s']
        c=contrat(app,p)
        def inserer(v):
            try:return remuneration(app,p,c,v,'2027-01-01')
            except DBAPIError as exc:
                assert exc.orig.pgcode=='23505';return None
        with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(inserer,[1,2]))
        assert sum(x is not None for x in r)==1
        assert exec_owner(app,'SELECT count(*) FROM personnel_remunerations_versions WHERE societe_id=:s',p)==1


def test_875_utilisateur_historique_sans_grant_non_supprimable(application):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api)
        exec_owner(app,"INSERT INTO personnel_evenements(societe_id,employe_id,revision,nature,auteur_id,motif) VALUES(:s,:e,0,'CONSTAT',:v,'Fictif875')",p)
        assert exec_owner(app,'SELECT count(*) FROM personnel_habilitations WHERE utilisateur_id=:v',p)==0
        assert api.delete(f'/api/utilisateurs/{p["v"]}').status_code==409
        ok(api.patch(f'/api/utilisateurs/{p["v"]}',json={'actif':False}))
        assert exec_owner(app,'SELECT count(*) FROM personnel_evenements WHERE auteur_id=:v',p)==1


def test_875_beneficiaire_ne_peut_pas_approuver_et_source_liee_protegee(application):
    app=application
    from test_paie_grh_postgres import dossier
    with closing(client(app)[0]) as api:
        p=preparer(app,api)
        exec_owner(app,'UPDATE personnel_dossiers SET utilisateur_beneficiaire_id=:v WHERE employe_id=:e',p)
        refuser(app,"INSERT INTO personnel_demandes(societe_id,employe_id,nature,revision_attendue,prepare_par,beneficiaire_snapshot,motif,statut,soumis_at,decision_par,decision_at,motif_decision) VALUES(:s,:e,'CONTRAT',0,:u,:v,'Fictif','APPROUVE',CURRENT_TIMESTAMP,:v,CURRENT_TIMESTAMP,'Auto-approbation interdite')",p)
        # L'ancien formulaire ne peut créer un homonyme du matricule déjà lié.
        r=api.post('/api/employes',json=dossier(matricule='002'))
        assert r.status_code==409
        activer(api)
        assert api.post('/api/employes',json=dossier(matricule='002')).status_code==409


def test_875_contenu_soumis_fige_et_approbation_sans_recriture(application):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api);c=contrat(app,p,approuve=False)
        d=exec_owner(app,'SELECT demande_id FROM personnel_contrats_versions WHERE id=:c',{'c':c})
        p=dict(p,c=c,d=d)
        exec_owner(app,"UPDATE personnel_demandes SET statut='SOUMIS',soumis_at=CURRENT_TIMESTAMP WHERE id=:d",p)
        refuser(app,"UPDATE personnel_contrats_versions SET type_contrat='CDD' WHERE id=:c",p)
        refuser(app,"UPDATE personnel_demandes SET motif='Substitution' WHERE id=:d",p)
        refuser(app,'UPDATE personnel_contrats_versions SET approuvee_par=:v,approuvee_at=CURRENT_TIMESTAMP WHERE id=:c',p)
        exec_owner(app,"UPDATE personnel_demandes SET statut='APPROUVE',decision_par=:v,decision_at=CURRENT_TIMESTAMP,motif_decision='Accord fictif' WHERE id=:d",p)
        exec_owner(app,'UPDATE personnel_contrats_versions c SET approuvee_par=d.decision_par,approuvee_at=d.decision_at FROM personnel_demandes d WHERE c.id=:c AND d.id=c.demande_id',p)
        refuser(app,'UPDATE personnel_contrats_versions SET approuvee_par=NULL,approuvee_at=NULL WHERE id=:c',p)


@pytest.mark.parametrize('effet',['infinity','-infinity','2025-12-31'])
def test_875_date_version_connue_et_finie(application,effet):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api)
        with pytest.raises(DBAPIError) as e:contrat(app,p,effet=effet)
        assert e.value.orig.pgcode=='23514'


def test_875_remuneration_pas_de_contrat_non_approuve(application):
    app=application
    with closing(client(app)[0]) as api:
        p=preparer(app,api);c=contrat(app,p,approuve=False)
        with pytest.raises(DBAPIError) as e:remuneration(app,p,c)
        assert e.value.orig.pgcode=='23514'


def test_875_creation_source_concurrente_attend_puis_refuse(application):
    app=application
    from test_paie_grh_postgres import dossier
    with closing(client(app)[0]) as api:
        e=ok(api.post('/api/employes',json=dossier(matricule='RACE875')),201);me=ok(api.get('/api/auth/me'))
        p={'s':me['societe_id'],'u':me['id'],'e':e['id']}
        with app['engine'].connect() as db,ThreadPoolExecutor(max_workers=1) as pool:
            tx=db.begin()
            try:
                db.execute(text("INSERT INTO personnel_dossiers(employe_id,societe_id,matricule_cle,origine,cree_par) VALUES(:e,:s,'RACE875','historique_a_confirmer',:u)"),p)
                def creer():
                    with httpx.Client(base_url=app['api_url'],headers=dict(api.headers),timeout=30) as autre:
                        return autre.post('/api/employes',json=dossier(matricule='RACE875')).status_code
                future=pool.submit(creer);time.sleep(.25);assert not future.done()
                tx.commit();assert future.result(timeout=30)==409
            finally:
                if tx.is_active:tx.rollback()
        assert exec_owner(app,"SELECT count(*) FROM employes WHERE societe_id=:s AND matricule='RACE875'",p)==1
