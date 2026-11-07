"""Régimes déclarés,dates connues,versionnement et masques sur PG natif isolé."""
from pathlib import Path
from contextlib import closing
import pytest
from sqlalchemy import text
from test_personnel881_profil_isole import (
    application as application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,
    client,ok,role_client,grant,activer,CAPS,W,P)
from test_personnel_workflow877_isole import equipe,creation,decision,soumettre,approuver,proposition,comptabilite
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1]
REGIMES=('regime_amo','regime_retraite','regime_mutuelle')

@pytest.fixture(scope='module')
def application(application109):
    app=application109;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with app['engine'].connect() as db:anciens=db.execute(text('SELECT to_jsonb(c) FROM personnel_contrats_versions c ORDER BY id')).scalars().all()
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/110_personnel_regimes_contrat.sql').read_text(encoding='utf8'))
        finally:raw.close()
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items() if t!='personnel_contrats_versions')
    with app['engine'].connect() as db:
        rows=db.execute(text('SELECT to_jsonb(c) FROM personnel_contrats_versions c ORDER BY id')).scalars().all()
        assert [{k:v for k,v in r.items() if k not in REGIMES} for r in rows]==anciens
        assert all(all(r[k] is None for k in REGIMES) for r in rows)
    yield app

def identite(eq):
    e=ok(eq['a'].post(W,json=creation('P883',date_embauche='2025-12-15')),201);i=e['demande']['id']
    assert ok(eq['a'].get(f'{W}/{e["employe_id"]}'))['date_embauche'] is None
    soumettre(eq['a'],i,0);approuver(eq,i,0)
    return e['employe_id']

def contrat(effet='2026-01-01',**kw):
    return dict(type_contrat='CDI',date_effet=effet,date_debut='2026-01-01',date_fin=None,reference_justificatif='REGIME-PRIVE-FICTIF883',**kw)

def test_883_regimes_proposes_decides_dates_et_conservation(application,equipe):
    eq=equipe;a=eq['a'];b=eq['b'];eid=identite(eq);avant=comptabilite(application,eq['sid'])
    contenu=contrat(regime_amo='AMO-PRIVEE-FICTIVE883',regime_retraite='RETRAITE-PRIVEE-FICTIVE883',regime_mutuelle='MUTUELLE-PRIVEE-FICTIVE883')
    proposition(eq,eid,1,'CONTRAT',contenu,403)
    grant(a,eq['uid'],'personnel.lire_identifiants_sensibles')
    p=proposition(eq,eid,1,'CONTRAT',contenu);soumettre(a,p['id'],1)
    assert ok(a.get(f'{W}/{eid}?au=2026-12-31'))['contrat'] is None
    assert b.post(f'{W}/demandes/{p["id"]}/approuver',json=decision(1)).status_code==403
    grant(a,eq['bid'],'personnel.lire_identifiants_sensibles');approuver(eq,p['id'],1)
    d=ok(a.get(f'{W}/{eid}?au=2026-12-31'));assert d['date_embauche']=='2025-12-15' and d['contrat']['date_debut']=='2026-01-01'
    assert d['contrat']['regimes']=={k:contenu[k] for k in REGIMES}
    cid=d['contrat']['id']
    with application['engine'].connect() as db:ancien=db.scalar(text('SELECT to_jsonb(c) FROM personnel_contrats_versions c WHERE id=:i'),{'i':cid})
    futur=proposition(eq,eid,2,'CONTRAT',contrat('2027-01-01',regime_amo='AMO-FUTURE-FICTIVE883',regime_mutuelle=None))
    soumettre(a,futur['id'],2);approuver(eq,futur['id'],2)
    f=ok(a.get(f'{W}/{eid}?au=2027-01-01'))['contrat']['regimes']
    assert f=={'regime_amo':'AMO-FUTURE-FICTIVE883','regime_retraite':contenu['regime_retraite'],'regime_mutuelle':None}
    assert ok(a.get(f'{W}/{eid}?au=2026-12-31'))['contrat']['id']==cid
    with application['engine'].connect() as db:
        assert db.scalar(text('SELECT to_jsonb(c) FROM personnel_contrats_versions c WHERE id=:i'),{'i':cid})==ancien
    grant(a,eq['lid'],'personnel.audit_lire')
    for path in [W,f'{W}/{eid}?au=2026-12-31',W+'/demandes',f'{W}/demandes/{p["id"]}',f'{W}/{eid}/historique']:
        q=eq['l'].get(path);assert q.status_code==200
        assert all(x not in q.text for x in ['AMO-PRIVEE-FICTIVE883','RETRAITE-PRIVEE-FICTIVE883','MUTUELLE-PRIVEE-FICTIVE883','REGIME-PRIVE-FICTIF883'])
    assert comptabilite(application,eq['sid'])==avant
    # Le runtime ne peut réécrire une version soumise/approuvée.
    from test_personnel_dossiers875_isole import refuser
    refuser(application,"UPDATE personnel_contrats_versions SET regime_amo='MODIF' WHERE id="+str(cid))
    refuser(application,"UPDATE personnel_contrats_versions SET regime_amo='MODIF' WHERE id="+str(cid),engine=application['personnel_runtime'])
    with closing(client(application)[0]) as etranger:
        uid=ok(etranger.get('/api/auth/me'))['id']
        for cap in CAPS:grant(etranger,uid,cap)
        grant(etranger,uid,'personnel.lire_identifiants_sensibles');activer(etranger)
        assert etranger.get(f'{W}/{eid}?au=2026-12-31').status_code==404
        assert ok(etranger.get(W))['total']==0
    h=next(x for x in ok(a.get(P+'/habilitations')) if x['utilisateur_id']==eq['uid'] and x['capacite']=='personnel.lire_identifiants_sensibles')
    ok(a.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Révocation fictive883'}))
    proposition(eq,eid,3,'CONTRAT',contrat('2028-01-01'),403)

@pytest.mark.parametrize('donnees',[{'date_embauche':123},{'date_embauche':'2026-01-01T00:00:00'}])
def test_883_date_entree_pas_de_coercition(equipe,donnees):
    assert equipe['a'].post(W,json=creation(**donnees)).status_code==422

@pytest.mark.parametrize('valeur',['', 'X'*121,42])
def test_883_regime_incorrect_refuse(equipe,valeur):
    eid=identite(equipe)
    proposition(equipe,eid,1,'CONTRAT',contrat(regime_amo=valeur),422)

def test_883_regimes_inconnus_pas_de_valeur_inventee(equipe):
    eq=equipe;eid=identite(eq)
    p=proposition(eq,eid,1,'CONTRAT',contrat());soumettre(eq['a'],p['id'],1);approuver(eq,p['id'],1)
    d=ok(eq['a'].get(f'{W}/{eid}?au=2026-12-31'));assert d['contrat']['regimes_masques']
    grant(eq['a'],eq['uid'],'personnel.lire_identifiants_sensibles')
    assert ok(eq['a'].get(f'{W}/{eid}?au=2026-12-31'))['contrat']['regimes']==dict.fromkeys(REGIMES)

def test_883_contrat_expire_ne_presume_pas_regime_du_nouveau(equipe):
    eq=equipe;a=eq['a'];eid=identite(eq)
    hs=grant(a,eq['uid'],'personnel.lire_identifiants_sensibles')['id'];grant(a,eq['bid'],'personnel.lire_identifiants_sensibles')
    c=contrat(regime_amo='AMO-CDD-EXPIRE-FICTIF883');c.update(type_contrat='CDD',date_fin='2026-12-31')
    p=proposition(eq,eid,1,'CONTRAT',c);soumettre(a,p['id'],1);approuver(eq,p['id'],1)
    ok(a.post(P+f'/habilitations/{hs}/revoquer',json={'motif':'Fin de mission de saisie883'}))
    nouveau=contrat('2027-01-01');nouveau['date_debut']='2027-01-01'
    q=proposition(eq,eid,2,'CONTRAT',nouveau)
    assert all(k not in ok(a.get(f'{W}/demandes/{q["id"]}'))['contenu'] for k in REGIMES)

def test_883_nouveau_contrat_ne_strande_pas_salaire_futur_approuve(equipe):
    from test_personnel_workflow877_isole import avec_salaire
    eq=equipe;eid,cid=avec_salaire(eq)
    p=proposition(eq,eid,3,'REMUNERATION',{'contrat_version_id':cid,'montant':'9876.54','date_effet':'2027-01-01',
      'periodicite':'mensuelle','reference_justificatif':'Avenant fictif883'})
    soumettre(eq['a'],p['id'],3);approuver(eq,p['id'],3)
    proposition(eq,eid,4,'CONTRAT',contrat('2027-01-01'),409)
    assert ok(eq['a'].get(f'{W}/{eid}?au=2027-01-01'))['remuneration']['montant']=='9876.54'
