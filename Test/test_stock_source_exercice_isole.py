"""Source réelle d'une régularisation : FK, société, exercice et référence."""
from contextlib import closing
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_stock_comptabilisation_concurrente_isole import preparer,generer
from test_inventaire_cloture_concurrente_isole import compter
from test_stock_validation_journal_concurrente_isole import lignes,audit
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from recette_restauration_consolidee_084 import empreintes_tables


def ref(p):return f"STOCK-CLOTURE-{p['a']}"


def manuelle(api,p,*,annee=None,reference=None,validee=False):
    return ok(api.post('/api/ecritures',json={'date':f"{annee or p['a']}-12-31",'journal':'OD',
        'reference':reference or ref(p),'libelle':'Pièce manuelle fictive526',
        'est_validee':validee,'lignes':[{'compte':'5141','debit':10},{'compte':'4481','credit':10}]}),201)['id']


def ancien_exercice(api,p):
    a=p['a']-1
    ok(api.post('/api/exercices',json={'annee':a,'date_debut':f'{a}-01-01','date_fin':f'{a}-12-31'}),201)
    return a


def inv_id(api,p):
    return ok(api.get('/api/inventaire/stock/cloture',params={'exercice':p['a']}))['inventaire_id']


def lier(app,api,p,eid):
    iid=inv_id(api,p)
    with app['engine'].begin() as c:
        assert c.execute(text('UPDATE inventaires_stock SET ecriture_stock_id=:e WHERE id=:i AND societe_id=:s'),{'e':eid,'i':iid,'s':p['s']}).rowcount==1


def metier(app):return {k:v for k,v in empreintes_tables(app['engine']).items() if k!='audit_actions'}


def verifier_piece(app,api,eid,avant):
    r=api.get(f'/api/ecritures/{eid}')
    assert r.status_code==200,f'Pièce source disparue #{eid}: {r.status_code} {r.text}'
    assert lignes(app,eid)==avant


@pytest.mark.parametrize('validee',[False,True])
def test_meme_reference_autre_exercice_preserve_piece(application,validee):
    with closing(client(application)[0]) as api:
        p=preparer(api);a=ancien_exercice(api,p)
        eid=manuelle(api,p,annee=a,validee=validee);avant=lignes(application,eid);audits=audit(application,eid)
        r=generer(api,p)
        verifier_piece(application,api,eid,avant)
        assert set(audits).issubset(audit(application,eid))
        assert r.status_code==200,r.text
        courant=r.json()['ecriture_id'];assert courant!=eid
        detail=ok(api.get(f'/api/ecritures/{courant}'))
        assert detail['exercice']==p['a'] and detail['source']=='stock'
        assert ok(api.get(f'/api/ecritures/{eid}'))['est_validee']==validee
        ok(api.post(f'/api/ecritures/{courant}/valider'))


def test_doublons_non_rattaches_refuses_sans_choisir_piece(application):
    with closing(client(application)[0]) as api:
        p=preparer(api);manuelle(api,p);manuelle(api,p);avant=metier(application)
        r=generer(api,p)
        assert metier(application)==avant
        assert r.status_code==409,r.text


def test_reference_manuelle_unique_non_rattachee_preservee(application):
    with closing(client(application)[0]) as api:
        p=preparer(api);manuelle(api,p);avant=metier(application)
        r=generer(api,p)
        assert metier(application)==avant
        assert r.status_code==409,r.text


def test_lien_reel_prioritaire_sur_reference_renommee_et_collision(application):
    with closing(client(application)[0]) as api:
        p=preparer(api);ancien=ok(generer(api,p))['ecriture_id']
        ok(api.patch(f'/api/ecritures/{ancien}',json={'reference':'RENOMMEE-FICTIVE526'}))
        autre=manuelle(api,p);avant=lignes(application,autre);audits=audit(application,ancien)
        r=generer(api,p)
        verifier_piece(application,api,autre,avant)
        assert r.status_code==200,r.text
        courant=r.json()['ecriture_id'];assert courant not in (ancien,autre)
        assert api.get(f'/api/ecritures/{ancien}').status_code==404
        assert set(audits).issubset(audit(application,ancien))
        etat=ok(api.get('/api/inventaire/stock/cloture',params={'exercice':p['a']}))
        assert etat['ecriture_stock_id']==courant
        ok(api.post(f'/api/ecritures/{courant}/valider'))
        # La pièce manuelle n'est pas supprimée pour contourner le contrôle.
        r=api.post('/api/cloture/cloturer',params={'exercice':p['a']})
        assert r.status_code==400 and 'brouillon' in r.text,r.text
        verifier_piece(application,api,autre,avant)


@pytest.mark.parametrize('incoherence',['exercice','societe','source'])
def test_lien_incoherent_refuse_sans_reparation_silencieuse(application,incoherence):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        p=preparer(api)
        if incoherence=='exercice':
            a=ancien_exercice(api,p);q={**p,'a':a};ok(compter(api,q,8,'ANCIEN-FICTIF526'))
            eid=ok(generer(api,q))['ecriture_id']
        elif incoherence=='societe':
            q=preparer(autre);eid=ok(generer(autre,q))['ecriture_id']
        else:eid=manuelle(api,p,reference='MANUELLE-LIEE-FICTIVE526')
        # Incohérence synthétique injectée seulement dans le cluster nonce.
        lier(application,api,p,eid);avant=metier(application)
        r=generer(api,p)
        assert metier(application)==avant
        assert r.status_code==409,r.text


def test_stock_sans_lien_retrouve_par_source_reference_exercice_uniques(application):
    with closing(client(application)[0]) as api:
        p=preparer(api);ancien=ok(generer(api,p))['ecriture_id'];audits=audit(application,ancien)
        lier(application,api,p,None)
        courant=ok(generer(api,p))['ecriture_id'];assert courant!=ancien
        assert api.get(f'/api/ecritures/{ancien}').status_code==404
        assert set(audits).issubset(audit(application,ancien))
        ok(api.post(f'/api/ecritures/{courant}/valider'))
        assert ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))['resultat_net']==-2840
        assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200
