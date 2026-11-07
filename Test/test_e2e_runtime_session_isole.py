"""Parcours regroupés sur une même application complète090,LOGIN SQL limité."""
from test_multi_societes_runtime_isole import (
    application as application090, application089, application087, migration, annee_banque,
)
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from recette_installation_vierge import BACK
from postgres_isole import cluster_isole, verifier_cible_isolee
from test_permissions_documents_commerciaux_postgres import acl
from test_complements_structure_postgres import refuser
from test_permissions_acomptes_avoirs_postgres import originaux, conserver
from recette_restauration_consolidee_084 import empreintes_tables

SQL='091_permissions_affectation_resultat.sql'


@pytest.fixture(scope='module')
def application(application090):
    app=application090;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    app['avant091']=acl(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((BACK/SQL).read_text(encoding='utf-8'))
        finally:raw.close()
    yield app
from test_e2e_runtime_consolide_isole import (
    test_runtime_facture_journal_lettrage as test_facture_validation_paiements_lettrage,
    test_runtime_import_csv_pointage as test_import_csv_pointage_et_soldes,
    test_runtime_propositions_simple_et_lot as test_propositions_bureau_mobile,
)
from test_e2e_runtime_annuel_isole import (
    test_runtime_immo_degressif as test_degressif_cinq_ans_normal_et_latence,
    test_runtime_annee_banque as test_annee_ventilation_banque_cloture_an,
)
from test_multi_societes_runtime_isole import (
    test090_creation_seconde_societe_et_switch_api as test_seconde_societe_api,
    test090_invitation_changement_role_desactivation_et_suppression_secondaire as test_acces_secondaires,
    test090_creation_switch_et_plan_dans_edge as test_multisociete_edge,
)
from test_e2e_annee_connectee_isole import (
    test_annee_connectee_stock_paiements_lettrage_tva_immo_cloture_an as test_annee_stock_tva_inventaire_cloture,
    test_oracle_annuel_independant_equilibre_et_resultats as test_oracle_annuel,
)
from test_e2e_immobilisations_degressif_isole import (
    test_oracle_degressif_bascule_lineaire_independant as test_oracle_degressif,
)


def _affecter_perte_fictive(annee_banque):
    import httpx
    app=annee_banque
    with app['engine'].connect() as db:
        email,sid=db.execute(text('SELECT u.email,c.societe_id FROM utilisateurs u JOIN clotures_exercice c '
            'ON c.societe_id=u.societe_id WHERE u.nom=\'Admin fictif\' ORDER BY u.id LIMIT 1')).one()
    with httpx.Client(base_url=app['api_url']) as api:
        r=api.post('/api/auth/login',json={'email':email,'password':'RasLecture2026!'})
        assert r.status_code==200,r.text
        api.headers['Authorization']='Bearer '+r.json()['access_token']
        before=originaux({'owner':app['engine']},sid)
        body={'date_decision':'2026-06-30','date_affectation':'2026-06-30',
              'reference_decision':'PV-FICTIF-448-2025','organe_decision':'Assemblée fictive de laboratoire',
              'reserve_legale':0,'autres_reserves':0,'report_a_nouveau':3000,'dividendes':0}
        r=api.post('/api/cloture/affecter-resultat',params={'exercice_origine':2025},json=body)
        assert r.status_code==200,r.text
        result=r.json();assert result['montant']==3000 and result['compte_source']=='1199'
        assert api.post('/api/cloture/affecter-resultat',params={'exercice_origine':2025},json=body).status_code==409
        conserver({'owner':app['engine']},sid,before)
        with app['engine'].connect() as db:
            lignes=db.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:eid ORDER BY compte'),
                              {'eid':result['ecriture_id']}).all()
            assert lignes==[('1169',3000,0),('1199',0,3000)]
            assert db.scalar(text('SELECT est_validee FROM ecritures WHERE id=:id'),{'id':result['ecriture_id']}) is True
            assert db.scalar(text("SELECT count(*) FROM ecriture_justificatifs WHERE ecriture_id=:id AND reference='PV-FICTIF-448-2025'"),
                             {'id':result['ecriture_id']})==1
        assert api.get('/api/cloture/etat',params={'exercice':2025}).status_code==200


@pytest.fixture(scope='module')
def affectation_perte(annee_banque):
    _affecter_perte_fictive(annee_banque)
    return annee_banque


def test_affectation_perte_3000_tracee_sans_modifier_les_originaux(affectation_perte):
    with affectation_perte['engine'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM decisions_affectation_resultat'))==1


def test091_acl_rejeu_et_preuve_immutable(affectation_perte):
    app=affectation_perte;c=app['cluster']
    before,seq_before=app['avant091'];after,seq_after=acl(app['engine'])
    assert seq_before==seq_after
    assert all(before[t]==after[t] for t in before if t!='decisions_affectation_resultat')
    assert after['decisions_affectation_resultat']=={'SELECT':True,'INSERT':True,'UPDATE':False,'DELETE':False,'TRUNCATE':False}
    runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
    try:
        for sql in ('UPDATE decisions_affectation_resultat SET id=id','DELETE FROM decisions_affectation_resultat',
                    'TRUNCATE decisions_affectation_resultat'):
            refuser(runtime,sql,'42501')
        refuser(app['engine'],'UPDATE decisions_affectation_resultat SET id=id','P0001')
        data=empreintes_tables(app['engine'])
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((BACK/SQL).read_text(encoding='utf-8'))
        finally:raw.close()
        assert empreintes_tables(app['engine'])==data and acl(app['engine'])==(after,seq_after)
    finally:runtime.dispose()


def test091_role_absent_aucun_objet():
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine=create_engine(c['url'])
        try:
            for _ in range(2):
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute((BACK/SQL).read_text(encoding='utf-8'))
                finally:raw.close()
            with engine.connect() as db:
                assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace"))
                assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
        finally:engine.dispose()
