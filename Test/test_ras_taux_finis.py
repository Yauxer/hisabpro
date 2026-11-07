"""Pourcentages RAS numériques ; aucun nouveau barème fiscal imposé."""
from datetime import date
import json
import uuid
import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session
import models,schemas
from test_e2e_facturation_isole import application


def facture(**champs):
    return {'type':'vente','date':date.today().isoformat(),'tiers':'Tiers RAS fictif',
            'ras_taux':10,'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':1000,'tva':20}],**champs}


@pytest.mark.parametrize('schema',[schemas.FactureCreate,schemas.FactureUpdate])
@pytest.mark.parametrize('taux',[float('nan'),float('inf'),float('-inf'),'NaN','Infinity',True,False,-1,100.01,{},[]])
def test_taux_ras_invalide_refuse(schema,taux):
    with pytest.raises(ValidationError):
        schema(**(facture(ras_taux=taux) if schema is schemas.FactureCreate else {'ras_taux':taux}))


@pytest.mark.parametrize('taux',[0,.5,5,10,15,20,100,'10.5'])
def test_pourcentage_mathematique_valide_sans_liste_legale(taux):
    assert schemas.FactureCreate(**facture(ras_taux=taux)).ras_taux==float(taux)
    assert schemas.FactureUpdate(ras_taux=taux).ras_taux==float(taux)


def test_patch_none_omet_taux_et_creation_none_refusee():
    assert schemas.FactureUpdate(ras_taux=None).ras_taux is None
    with pytest.raises(ValidationError):
        schemas.FactureCreate(**facture(ras_taux=None))


@pytest.mark.parametrize('methode',['POST','PATCH'])
@pytest.mark.parametrize('valeur',[float('nan'),float('inf'),True,-1,150])
def test_api_ras_invalide_ne_modifie_aucune_facture(application,methode,valeur):
    suffix=uuid.uuid4().hex[:8]
    nom='RAS fictive '+suffix
    with httpx.Client(base_url=application['api_url']) as api:
        r=api.post('/api/auth/register',json={'nom':'Admin fictif','email':suffix+'@example.com','password':'RasFinis2026!','raison_sociale':nom})
        assert r.status_code==200,r.text
        api.headers['Authorization']='Bearer '+r.json()['access_token']
        r=api.post('/api/factures',json=facture())
        assert r.status_code==201,r.text
        fid=r.json()['id']
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,fid).societe_id
        def instantane():
            with Session(application['engine']) as db:
                fs=db.query(models.Facture).filter_by(societe_id=sid).order_by(models.Facture.id).all()
                return [({c.name:getattr(f,c.name) for c in f.__table__.columns},
                        [{c.name:getattr(l,c.name) for c in l.__table__.columns} for l in f.lignes]) for f in fs], db.query(models.Ecriture).filter_by(societe_id=sid).count()
        avant=instantane()
        url='/api/factures' if methode=='POST' else f'/api/factures/{fid}'
        payload=facture(ras_taux=valeur) if methode=='POST' else {'ras_taux':valeur}
        r=api.request(methode,url,content=json.dumps(payload),headers={'Content-Type':'application/json'})
        assert r.status_code==422,r.text
        assert instantane()==avant


def test_api_patch_none_preserve_ras_enregistree(application):
    suffix=uuid.uuid4().hex[:8]
    with httpx.Client(base_url=application['api_url']) as api:
        r=api.post('/api/auth/register',json={'nom':'Admin fictif','email':suffix+'@example.com','password':'RasFinis2026!','raison_sociale':'RAS None fictive '+suffix})
        assert r.status_code==200,r.text
        api.headers['Authorization']='Bearer '+r.json()['access_token']
        fid=api.post('/api/factures',json=facture()).json()['id']
        r=api.patch(f'/api/factures/{fid}',json={'ras_taux':None,'notes':'Note fictive'})
        assert r.status_code==200,r.text
        with Session(application['engine']) as db:
            f=db.get(models.Facture,fid)
            assert f.ras_taux==10 and f.notes=='Note fictive'
