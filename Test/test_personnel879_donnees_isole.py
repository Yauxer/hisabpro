"""Coordonnées/CNSS/données fiscales facultatives, décidées et masquées."""
from contextlib import closing
from pathlib import Path
import pytest
from sqlalchemy import text
from test_personnel_workflow877_isole import (
    application as application107,application875,application873,application093,application092,application091,
    application090,application089,application087,migration,equipe,creation,decision,
    soumettre,approuver,proposition,ok,grant,W,P)
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables


@pytest.fixture(scope='module')
def application(application107):
    app=application107;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((Path(__file__).resolve().parents[1]/'hisabpro-backend/108_personnel_rejet_auteur_inactif.sql').read_text(encoding='utf8'))
        finally:raw.close()
    assert empreintes_tables(app['engine'])==avant
    yield app


def test_879_identite_facultative_pas_de_fuite_ni_conversion(application,equipe):
    eq=equipe;a,b,l=eq['a'],eq['b'],eq['l']
    data=creation(numero_cnss='CNSS-PRIVE-FICTIF-879',email='sal.personnel879@example.com',telephone='TEL-FICTIF',
        situation_familiale='marie',nb_enfants=2,personnes_charge_ir=2,motif='Contrôle CNSS-PRIVE-FICTIF-879')
    assert a.post(W,json=data).status_code==403
    assert ok(a.get(W))['total']==0
    grant(a,eq['uid'],'personnel.lire_identifiants_sensibles')
    e=ok(a.post(W,json=data),201);eid=e['employe_id'];i=e['demande']['id']
    with application['engine'].connect() as db:
        assert db.execute(text('SELECT numero_cnss,email,personnes_charge_ir,salaire_brut FROM employes WHERE id=:e'),{'e':eid}).one()==(None,None,None,None)
    soumettre(a,i,0)
    assert b.post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code==403
    grant(a,eq['bid'],'personnel.lire_identifiants_sensibles');approuver(eq,i,0)
    r=ok(a.get(f'{W}/{eid}'));assert r['numero_cnss']=='CNSS-PRIVE-FICTIF-879' and r['donnees_fiscales']=={'situation_familiale':'marie','nb_enfants':2,'personnes_charge_ir':2}
    assert r['email']=='sal.personnel879@example.com' and r['remuneration'] is None
    for path in [W,W+f'/{eid}',W+'/demandes',W+f'/demandes/{i}']:
        q=l.get(path);assert q.status_code==200 and 'CNSS-PRIVE-FICTIF-879' not in q.text
    grant(a,eq['lid'],'personnel.audit_lire')
    assert 'CNSS-PRIVE-FICTIF-879' not in l.get(f'{W}/{eid}/historique').text
    p=proposition(eq,eid,1,'DOSSIER',{'nom':'Nom corrigé fictif879','poste':None})
    soumettre(a,p['id'],1);approuver(eq,p['id'],1)
    r=ok(a.get(f'{W}/{eid}'));assert r['numero_cnss']=='CNSS-PRIVE-FICTIF-879' and r['donnees_fiscales']['nb_enfants']==2


@pytest.mark.parametrize('donnees',[{'email':'invalide'},{'nb_enfants':True},{'personnes_charge_ir':7},{'numero_cnss':'X'*51}])
def test_879_donnees_personnelles_incorrectes_refusees(equipe,donnees):
    assert equipe['a'].post(W,json=creation(**donnees)).status_code==422


def test_879_tentative_fiscale_sans_droit_ne_mutile_pas_identite(equipe):
    eq=equipe;a=eq['a'];h=next(x for x in ok(a.get(P+'/habilitations')) if x['utilisateur_id']==eq['uid'] and x['capacite']=='personnel.lire_remuneration')
    ok(a.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif879'}))
    assert a.post(W,json=creation(personnes_charge_ir=1)).status_code==403
    assert ok(a.get(W))['total']==0


def test_879_rejeter_preparation_compte_desactive_sans_transfert_auteur(equipe):
    eq=equipe;a,b=eq['a'],eq['b']
    e=ok(b.post(W,json=creation(matricule='INACTIF879')),201);i=e['demande']['id']
    soumettre(b,i,0)
    ok(a.patch(f'/api/utilisateurs/{eq["bid"]}',json={'actif':False}))
    assert a.post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code==409
    r=a.post(f'{W}/demandes/{i}/rejeter',json=decision(0));assert r.status_code==200,r.text
    q=ok(a.get(f'{W}/demandes/{i}'));assert q['prepare_par']==eq['bid'] and q['statut']=='REJETE'
    assert ok(a.get(f'{W}/{e["employe_id"]}'))['statut']=='BROUILLON'
