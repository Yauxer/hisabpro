"""Vrais appels HTTP et PostgreSQL natif nonce ;clés fictives privées temporaires."""
from contextlib import closing
from pathlib import Path
import json,tempfile,os
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text
from test_personnel883_regimes_isole import (
    application as application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,
    client,ok,role_client,grant,activer,CAPS,W,P,equipe,identite,comptabilite)
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];C=W+'/coffre';PDF=b'%PDF-1.4\nPIECE-RH-FICTIVE-PRIVEE885\n%%EOF'

@pytest.fixture(scope='module',autouse=True)
def cles_coffre885():
    ancien=os.environ.get('PERSONNEL_COFFRE_CLES_FICHIER')
    with tempfile.TemporaryDirectory(prefix='hisabpro_cles885_') as td:
        p=Path(td)/'cles.json';d={'version':1,'active':'test-a','cles':{'test-a':Fernet.generate_key().decode('ascii')}}
        p.write_text(json.dumps(d),encoding='utf8');p.chmod(0o600);os.environ['PERSONNEL_COFFRE_CLES_FICHIER']=str(p)
        try:yield {'path':p,'configuration':d}
        finally:
            if ancien is None:os.environ.pop('PERSONNEL_COFFRE_CLES_FICHIER',None)
            else:os.environ['PERSONNEL_COFFRE_CLES_FICHIER']=ancien

@pytest.fixture(scope='module')
def application(application110,cles_coffre885):
    app=application110;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/111_personnel_coffre.sql').read_text(encoding='utf8'))
        finally:raw.close()
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items())
    yield dict(app,cles885=cles_coffre885)

def config(a):
    return ok(a.post(C+'/politique',json={'reference_garde_cles':'GARDE-FICTIVE885','reference_conservation':'POLITIQUE-FICTIVE885',
      'reference_rotation_sauvegarde':'RESTAURATION-FICTIVE885','motif':'Déclaration fictive885','confirmation':'DECLARER_POLITIQUE_COFFRE_RH'}),201)

def depot(a,eid,contenu=PDF,categorie='contrat'):
    return a.post(f'{C}/{eid}/pieces',params={'categorie':categorie},content=contenu,headers={'Content-Type':'application/octet-stream'})

def test_885_configuration_explicite_avant_collecte_et_droits(equipe):
    eq=equipe;a=eq['a'];eid=identite(eq)
    assert not ok(a.get(C))['collecte_autorisee']
    assert depot(a,eid).status_code==403
    grant(a,eq['uid'],'personnel.lire_identifiants_sensibles')
    assert depot(a,eid).status_code==409
    config(a);assert ok(a.get(C))['collecte_autorisee']
    assert eq['b'].post(C+'/politique',json={}).status_code==403
    assert eq['l'].get(f'{C}/{eid}/pieces').status_code==403

def test_885_depot_prive_restitution_exacte_masques_isolation_et_immutabilite(application,equipe):
    eq=equipe;a=eq['a'];eid=identite(eq);grant(a,eq['uid'],'personnel.lire_identifiants_sensibles');config(a)
    avant=comptabilite(application,eq['sid']);piece=ok(depot(a,eid),201);ident=piece['id']
    r=a.get(f'{C}/{eid}/pieces/{ident}');assert r.status_code==200 and r.content==PDF
    assert r.headers['cache-control']=='no-store' and r.headers['x-content-type-options']=='nosniff'
    assert 'attachment;' in r.headers['content-disposition'] and 'SECRET' not in r.headers['content-disposition']
    liste=a.get(f'{C}/{eid}/pieces');assert liste.status_code==200 and 'SECRET' not in liste.text and 'contenu_chiffre' not in liste.text
    with application['engine'].connect() as db:
        row=db.execute(text('SELECT contenu_chiffre,cle_id FROM personnel_coffre_pieces WHERE id=:i'),{'i':ident}).one()
        assert 'PIECE-RH-FICTIVE' not in row[0] and row[1]=='test-a'
        assert 'NOM-PERSONNEL-SECRET885' not in db.scalar(text('SELECT to_jsonb(p)::text FROM personnel_coffre_pieces p WHERE id=:i'),{'i':ident})
    from test_personnel_dossiers875_isole import refuser
    for sql in ['DELETE FROM personnel_coffre_pieces WHERE id=:i',"UPDATE personnel_coffre_pieces SET categorie='autre' WHERE id=:i"]:
        refuser(application,sql,{'i':ident});refuser(application,sql,{'i':ident},engine=application['personnel_runtime'])
    assert eq['l'].get(f'{C}/{eid}/pieces/{ident}').status_code==403
    with closing(client(application)[0]) as etranger:
        uid=ok(etranger.get('/api/auth/me'))['id']
        for cap in CAPS:grant(etranger,uid,cap)
        grant(etranger,uid,'personnel.lire_identifiants_sensibles');activer(etranger)
        assert etranger.get(f'{C}/{eid}/pieces/{ident}').status_code==404
    assert comptabilite(application,eq['sid'])==avant

@pytest.mark.parametrize('contenu,statut',[(b'',413),(b'<svg>FICTIF</svg>',400),(b'X'*(4194304+1),413)],ids=['vide','type_refuse','trop_grand'])
def test_885_types_et_taille_bornes(equipe,contenu,statut):
    eq=equipe;a=eq['a'];eid=identite(eq);grant(a,eq['uid'],'personnel.lire_identifiants_sensibles');config(a)
    assert depot(a,eid,contenu).status_code==statut
    assert ok(a.get(f'{C}/{eid}/pieces'))==[]

def test_885_rotation_active_restauration_cle_et_indisponibilite_sans_fuite(application,equipe):
    eq=equipe;a=eq['a'];eid=identite(eq);grant(a,eq['uid'],'personnel.lire_identifiants_sensibles');config(a)
    premier=ok(depot(a,eid),201)['id'];p=application['cles885']['path'];sauve=p.read_bytes()
    nouveau=json.loads(sauve);nouveau['active']='test-b';nouveau['cles']['test-b']=Fernet.generate_key().decode('ascii')
    try:
        p.write_text(json.dumps(nouveau),encoding='utf8')
        second=ok(depot(a,eid),201)['id']
        with application['engine'].connect() as db:assert db.scalar(text('SELECT cle_id FROM personnel_coffre_pieces WHERE id=:i'),{'i':second})=='test-b'
        assert a.get(f'{C}/{eid}/pieces/{premier}').content==PDF and a.get(f'{C}/{eid}/pieces/{second}').content==PDF
        sauvegarde_rotation=p.read_bytes();nouveau['cles'].pop('test-a');p.write_text(json.dumps(nouveau),encoding='utf8')
        r=a.get(f'{C}/{eid}/pieces/{premier}');assert r.status_code==503 and 'PIECE-RH-FICTIVE' not in r.text
        p.write_bytes(sauvegarde_rotation)
        assert a.get(f'{C}/{eid}/pieces/{premier}').content==PDF
        p.write_text('{}',encoding='utf8');r=depot(a,eid);assert r.status_code==503 and str(p) not in r.text
    finally:p.write_bytes(sauve)

def test_885_profil_personnel_depot_et_substitution_chiffree_refusee(application,equipe):
    eq=equipe;a=eq['a'];eid=identite(eq);config(a)
    perso,u,_,_=role_client(application,a,'personnel')
    with closing(perso):
        for cap in CAPS:grant(a,u['id'],cap)
        grant(a,u['id'],'personnel.lire_identifiants_sensibles')
        ident=ok(depot(perso,eid),201)['id']
        assert perso.get(f'{C}/{eid}/pieces/{ident}').content==PDF
        assert perso.post(C+'/politique',json={}).status_code==403
        with application['engine'].begin() as db:
            autre=db.scalar(text('INSERT INTO personnel_coffre_pieces(societe_id,employe_id,politique_id,categorie,mime,octets,cle_id,contenu_chiffre,deposee_par) '
              'SELECT societe_id,employe_id,politique_id,categorie,mime,octets,cle_id,contenu_chiffre,deposee_par FROM personnel_coffre_pieces WHERE id=:i RETURNING id'),{'i':ident})
        r=perso.get(f'{C}/{eid}/pieces/{autre}');assert r.status_code==409 and 'PIECE-RH-FICTIVE' not in r.text
