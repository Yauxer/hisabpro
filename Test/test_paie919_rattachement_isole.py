from pathlib import Path
from contextlib import closing
import json,pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_paie915_ir_source_isole import (
    application as application122,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite)
from test_paie891_variables_isole import rubrique,envoyer,submit,choix,V,entree
from test_paie893_campagnes_isole import salarie,simuler
from test_paie919_rattachement_unitaire import declaration
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1]

def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/123_paie_rattachement_revenus.sql').read_text(encoding='utf8'))
    finally:raw.close()

@pytest.fixture(scope='module')
def application(application122):
    a=application122;avant=empreintes_tables(a['engine']);installer(a);installer(a);apres=empreintes_tables(a['engine']);assert all(apres[t]==h for t,h in avant.items());yield a

def preparer(eq,**kw):
    eid,_=salarie(eq);rid=rubrique(eq);r=envoyer(eq,eid,rid,rattachement_revenus=declaration(**kw));submit(eq,r['id']);ok(eq['b'].post(f'{V}/{r["id"]}/approuver',json=choix()));return eid,rid,r

def test_919_faits_approbation_sources_sans_changer_le_brut(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid']);eid,_,v=preparer(eq)
    r=ok(eq['a'].get(f'{V}/{v["id"]}'));assert r['donnees']['rattachement_revenus']==declaration() and r['periode']=='2026-11-01' and r['date_effet']=='2026-11-15'
    q=simuler(eq,[eid]);e=q['contenu']['employes'][0];assert e['brut']=='9800.11'
    assert e['variables'][0]['rattachement_revenus']=={'reference_debut':'2025-01-01','reference_fin':'2025-12-31','versement_date':'2026-12-05'}
    assert 'PRIME-ANNUELLE-FICTIVE919' not in json.dumps(q['contenu']) and 'VERSEMENT-DECLARE-FICTIF919' not in json.dumps(q['contenu'])
    for engine in [application['engine'],application['personnel_runtime']]:
        with pytest.raises(DBAPIError) as erreur:
            with engine.begin() as db:db.execute(text("UPDATE paie_variables SET donnees=jsonb_set(donnees,'{rattachement_revenus,versement_date}','\"2026-11-01\"') WHERE id=:i"),{'i':v['id']})
        assert erreur.value.orig.pgcode==('23514' if engine is application['engine'] else '42501')
    assert comptabilite(application,eq['sid'])==avant
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant

def test_919_anciens_json_sans_reconstruction_ni_dates_inventees(equipe):
    eq=equipe;eid,_=salarie(eq);rid=rubrique(eq);v=envoyer(eq,eid,rid);submit(eq,v['id']);ok(eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()))
    assert 'rattachement_revenus' not in ok(eq['a'].get(f'{V}/{v["id"]}'))['donnees']
    assert 'rattachement_revenus' not in simuler(eq,[eid])['contenu']['employes'][0]['variables'][0]

@pytest.mark.parametrize('r',[{},[],True,{'reference_debut':'2025-02-30'},declaration(reference_fin='2024-01-01'),declaration(versement_reference=''),declaration(versement_date=True),declaration(inconnu=1)])
def test_919_garde_postgresql_native_json(application,equipe,r):
    eq=equipe;eid,_=salarie(eq);rid=rubrique(eq);v=envoyer(eq,eid,rid)
    for engine in [application['engine'],application['personnel_runtime']]:
        with pytest.raises(DBAPIError,match='Rattachement documentaire') as e:
            with engine.begin() as db:db.execute(text("INSERT INTO paie_variables(societe_id,employe_id,rubrique_id,rubrique_version_id,contrat_version_id,remuneration_version_id,beneficiaire_snapshot,periode,annee,date_effet,periodicite,mode,montant,donnees,instantane,source_reference,prepare_par) SELECT societe_id,employe_id,rubrique_id,rubrique_version_id,contrat_version_id,remuneration_version_id,beneficiaire_snapshot,periode,annee,date_effet,periodicite,mode,montant,jsonb_set(donnees,'{rattachement_revenus}',CAST(:r AS jsonb)),instantane,'GUARDE-FICTIVE919',prepare_par FROM paie_variables WHERE id=:i"),{'i':v['id'],'r':json.dumps(r)})
        assert e.value.orig.pgcode=='23514'

def test_919_masquage_references_societes_et_revocation(application,equipe):
    eq=equipe;eid,_,v=preparer(eq);role,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(role):
        for cap in ['personnel.lire_identite','personnel.lire_remuneration']:g=grant(eq['a'],u['id'],cap)
        d=ok(role.get(f'{V}/{v["id"]}'));r=d['donnees']['rattachement_revenus'];assert d['historique_masque'] and r['reference_justification'] is None and r['versement_reference'] is None and r['reference_debut']=='2025-01-01'
        ok(eq['a'].post('/api/employes/securite/habilitations/'+str(g['id'])+'/revoquer',json={'motif':'Fin lecture FICTIF919'}));assert role.get(f'{V}/{v["id"]}').status_code==403
    with closing(client(application)[0]) as autre:
        u=ok(autre.get('/api/auth/me'))
        for cap in CAPS:grant(autre,u['id'],cap)
        activer(autre);assert autre.get(f'{V}/{v["id"]}').status_code==404

def test_919_garde_absent_ne_casse_pas_saisie_historique(application,equipe):
    a=application;eq=equipe;eid,_=salarie(eq);rid=rubrique(eq);c=a['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    try:
        with a['engine'].begin() as db:db.execute(text('ALTER TABLE paie_variables DISABLE TRIGGER aaa_paie_reference123'))
        assert eq['a'].post(V,json=entree(eid,rid,rattachement_revenus=declaration())).status_code==503
        assert eq['a'].post(V,json=entree(eid,rid)).status_code==201
    finally:
        with a['engine'].begin() as db:db.execute(text('ALTER TABLE paie_variables ENABLE TRIGGER aaa_paie_reference123'))
