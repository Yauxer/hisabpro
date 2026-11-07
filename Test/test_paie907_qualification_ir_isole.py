"""API et garde SQL sur PostgreSQL natif nonce ; aucune base utilisateur."""
from pathlib import Path
from contextlib import closing
import json,pytest
from sqlalchemy import text
from test_paie901_ir_annuel_isole import (
    application as application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser)
from test_paie889_catalogue_isole import E,creer as rubrique,contenu as contenu_rubrique,dec
from test_paie897_social_isole import S,creer as branche,contenu as contenu_branche
from test_paie907_qualification_ir_unitaire import preuve
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1]


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/119_paie_qualifications_fiscales.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application118):
    app=application118;avant=empreintes_tables(app['engine']);installer(app);installer(app)
    assert empreintes_tables(app['engine'])==avant
    yield app


@pytest.mark.parametrize('api,creer,champ,traitement',[(E,rubrique,'frais_professionnels','INCLUS'),(S,branche,'deductibilite_ir','DEDUCTIBLE')])
def test_907_qualification_independante_habilitation_et_attestation(application,equipe,api,creer,champ,traitement):
    eq=equipe;avant=comptabilite(application,eq['sid']);v=creer(eq,**{champ:preuve(traitement)})
    url=f'{api}/versions/{v["id"]}/approuver'
    assert eq['a'].post(url,json=dec(verification_reglementaire_confirmee=True)).status_code==403
    assert eq['b'].post(url,json=dec(verification_reglementaire_confirmee=True)).status_code==403
    grant(eq['a'],eq['bid'],'personnel.valider_regles_paie')
    assert eq['b'].post(url,json=dec()).status_code==400
    ok(eq['b'].post(url,json=dec(verification_reglementaire_confirmee=True)))
    rid=v['rubrique_id' if api==E else 'branche_id'];d=ok(eq['a'].get(f'{api}/{rid}'))['versions'][0]
    assert d['contenu'][champ]==preuve(traitement) and d['verification_reglementaire_confirmee']
    assert comptabilite(application,eq['sid'])==avant


@pytest.mark.parametrize('api,creer,champ,traitement,table',[(E,rubrique,'frais_professionnels','EXCLUS','paie_rubrique_versions'),(S,branche,'deductibilite_ir','NON_DEDUCTIBLE','paie_branche_sociale_versions')])
def test_907_garde_sql_directe_sans_habilitation_ni_attestation(application,equipe,api,creer,champ,traitement,table):
    eq=equipe;v=creer(eq,**{champ:preuve(traitement)})
    sql=f"UPDATE {table} SET statut='APPROUVEE',decision_par=:u,decision_at=clock_timestamp(),motif_decision='FICTIF907',reference_controle='FICTIF907',verification_reglementaire_confirmee=:p WHERE id=:i"
    for moteur in [application['engine'],application['personnel_runtime']]:
        refuser(application,sql,{'u':eq['bid'],'i':v['id'],'p':True},engine=moteur)
    grant(eq['a'],eq['bid'],'personnel.valider_regles_paie')
    for moteur in [application['engine'],application['personnel_runtime']]:
        refuser(application,sql,{'u':eq['bid'],'i':v['id'],'p':False},engine=moteur)
    ok(eq['b'].post(f'{api}/versions/{v["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)))


@pytest.mark.parametrize('api,creer,champ,contenu,traitement',[(E,rubrique,'frais_professionnels',contenu_rubrique,'EXCLUS'),(S,branche,'deductibilite_ir',contenu_branche,'NON_DEDUCTIBLE')])
def test_907_versions_historiques_isolation_et_rejeu(application,equipe,api,creer,champ,contenu,traitement):
    eq=equipe;v=creer(eq);rid=v['rubrique_id' if api==E else 'branche_id'];ok(eq['b'].post(f'{api}/versions/{v["id"]}/approuver',json=dec()))
    ancien=ok(eq['a'].get(f'{api}/{rid}'))['versions'][0];assert ancien['contenu'][champ] is None
    n=ok(eq['a'].post(f'{api}/{rid}/versions',json={'version_attendue':1,'contenu':contenu(date_debut='2027-01-01',**{champ:preuve(traitement)}),'motif':'Version fiscale FICTIVE907'}),201)
    grant(eq['a'],eq['bid'],'personnel.valider_regles_paie');ok(eq['b'].post(f'{api}/versions/{n["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)))
    assert ok(eq['a'].get(api,params={'au':'2026-12-31'}))['elements'][0]['courante_id']==v['id']
    assert ok(eq['a'].get(api,params={'au':'2027-01-01'}))['elements'][0]['courante_id']==n['id']
    assert ok(eq['a'].get(f'{api}/{rid}'))['versions'][1]==ancien
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre);assert autre.get(f'{api}/{rid}').status_code==404
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant


@pytest.mark.parametrize('champ,table,creer', [('frais_professionnels','paie_rubrique_versions',rubrique),('deductibilite_ir','paie_branche_sociale_versions',branche)])
@pytest.mark.parametrize('modif',[{'url_source':'https://finances.gov.ma.attacker.invalid/'},{'date_consultation':'infinity'},{'empreinte_preuve':None},{'conditions':''},{'traitement':'A_VERIFIER'},{'conditions':42},{'date_consultation':'2026-1-1'},{'taux':'35'}])
def test_907_insertion_sql_preuve_invalide_refusee(application,equipe,champ,table,creer,modif):
    v=creer(equipe);c=(contenu_rubrique() if champ=='frais_professionnels' else contenu_branche());c['date_debut']='2027-01-01';c[champ]={**preuve('INCLUS' if champ=='frais_professionnels' else 'DEDUCTIBLE'),**modif}
    # INSERT d'une autre proposition ; ne pas confondre rejet de preuve et immutabilité d'une ligne existante.
    racine='rubrique_id' if champ=='frais_professionnels' else 'branche_id'
    sql=f"INSERT INTO {table}(societe_id,{racine},numero,contenu,date_debut,date_fin,prepare_par,motif) VALUES(:s,:r,2,CAST(:c AS jsonb),'2027-01-01',NULL,:u,'FICTIF907')"
    for moteur in [application['engine'],application['personnel_runtime']]:
        from sqlalchemy.exc import DBAPIError
        with pytest.raises(DBAPIError,match='Qualification fiscale invalide|Preuves de qualification fiscale incomplètes|Consultation invalide'):
            with moteur.begin() as db:db.execute(text(sql),{'s':equipe['sid'],'r':v[racine],'c':json.dumps(c),'u':equipe['uid']})


def test_907_installation_manquante_refus_explicite_sans_casser_anciennes_saisies(application,equipe):
    c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    try:
        with application['engine'].begin() as db:db.execute(text('DROP FUNCTION public.hisabpro_paie_qualification_ir119() CASCADE'))
        rubrique(equipe,'ANCIEN_SANS119');branche(equipe,'ANCIEN_SANS119')
        for api,contenu,champ,traitement in [(E,contenu_rubrique,'frais_professionnels','INCLUS'),(S,contenu_branche,'deductibilite_ir','DEDUCTIBLE')]:
            d={'code':'QUALIFICATION_SANS119','contenu':contenu(**{champ:preuve(traitement)}),'motif':'FICTIF907'}
            if api==S:d['regime']='FICTIF907'
            reponse=equipe['a'].post(api,json=d);assert reponse.status_code==503 and '119' in reponse.text
    finally:installer(application)
