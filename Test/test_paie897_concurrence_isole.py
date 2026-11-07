"""Courses entre deux branches distinctes et qualification au niveau SQL."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import httpx
from sqlalchemy import text
from test_paie897_social_isole import (
    application,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,creer,qualifie,dec,grant,refuser,ok,S)


def test_897_concurrence_deux_branches_api(application,equipe):
    eq=equipe;branches=[creer(eq,'COURT_TERME'),creer(eq,'IPE')];barriere=Barrier(2)
    def approuver(v):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['b'].headers),timeout=30) as c:
            barriere.wait(timeout=15);return c.post(f'{S}/versions/{v["id"]}/approuver',json=dec()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(approuver,branches))==[200,409]
    with application['engine'].connect() as db:assert db.scalar(text("SELECT count(*) FROM paie_branche_sociale_versions WHERE societe_id=:s AND statut='APPROUVEE'"),{'s':eq['sid']})==1


def test_897_concurrence_deux_branches_sql_runtime(application,equipe):
    eq=equipe;branches=[creer(eq,'COURT_TERME'),creer(eq,'IPE')];barriere=Barrier(2)
    def approuver(v):
        try:
            with application['personnel_runtime'].begin() as db:
                barriere.wait(timeout=15)
                db.execute(text("UPDATE paie_branche_sociale_versions SET statut='APPROUVEE',decision_par=:u,decision_at=clock_timestamp(),motif_decision='FICTIF',reference_controle='FICTIF' WHERE id=:i"),{'u':eq['bid'],'i':v['id']})
            return 'OK'
        except Exception as e:
            assert getattr(getattr(e,'orig',None),'pgcode',None)=='23514',str(e)
            return 'REFUS'
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(approuver,branches))==['OK','REFUS']


def test_897_sql_qualification_refuse_capacite_absente_puis_revoquee(application,equipe):
    eq=equipe;v=ok(eq['a'].post(S,json={'code':'SOURCE_FICTIVE','regime':'FICTIF','contenu':qualifie(),'motif':'Preuve FICTIVE uniquement pour test'}),201)
    sql="UPDATE paie_branche_sociale_versions SET statut='APPROUVEE',decision_par=:u,decision_at=clock_timestamp(),motif_decision='FICTIF',reference_controle='FICTIF',verification_reglementaire_confirmee=true WHERE id=:i"
    params={'u':eq['bid'],'i':v['id']}
    refuser(application,sql,params,engine=application['personnel_runtime'])
    h=grant(eq['a'],eq['bid'],'personnel.valider_regles_paie')
    ok(eq['a'].post('/api/employes/securite/habilitations/'+str(h['id'])+'/revoquer',json={'motif':'Fin contrôle FICTIF897'}))
    refuser(application,sql,params,engine=application['personnel_runtime'])
    assert ok(eq['a'].get(f'{S}/{v["branche_id"]}'))['versions'][0]['statut']=='PROPOSEE'
