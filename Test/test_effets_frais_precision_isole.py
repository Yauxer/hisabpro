"""Frais au centime : refus avant mutation et écritures exactes sur PGnonce."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import json
import pytest
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier
from test_lecture_reglements_historiques import photo

def preparer(api,mode='cheque',sens='vente'):
    _,ids,p=dossier(api,sens)
    r=api.post('/api/reglements',json={'facture_id':ids[0],'tiers_id':p['tiers_id'],
        'tiers':'Tiers fictif','date':date.today().isoformat(),'date_echeance':date.today().isoformat(),
        'montant':120,'mode':mode,'reference':'FRAIS-PRECISION-FICTIF'})
    assert r.status_code==201,r.text
    return r.json()

@pytest.mark.parametrize('frais',[True,False,0.001,10.005,float('nan'),float('inf'),float('-inf'),-1,1e100],
 ids=['vrai','faux','millieme','demicentime','nan','inf','moinsinf','negatif','horscapacite'])
def test_frais_invalides_refuses_sans_mutation(application,frais):
    with closing(client(application)[0]) as api:
        row=preparer(api);avant=photo(application)
        r=api.post(f"/api/reglements/{row['id']}/transition",content=json.dumps({'action':'encaisser',
            'frais':frais,'date_effective':date.today().isoformat()}),headers={'Content-Type':'application/json'})
        assert r.status_code==422,r.text
        assert photo(application)==avant

@pytest.mark.parametrize('action,sens,mode',[('remettre','vente','cheque'),('payer','achat','effet')])
def test_frais_non_traites_ne_sont_pas_silencieusement_ignores(application,action,sens,mode):
    with closing(client(application)[0]) as api:
        row=preparer(api,mode,sens);avant=photo(application)
        r=api.post(f"/api/reglements/{row['id']}/transition",json={'action':action,'frais':1.01,
            'date_effective':date.today().isoformat()})
        assert r.status_code==422,r.text
        assert photo(application)==avant

@pytest.mark.parametrize('frais',[0,None,0.01,10.01,'10.01'])
def test_frais_exacts_encaissement_bank_plus_charge_egal120(application,frais):
    with closing(client(application)[0]) as api:
        row=preparer(api)
        r=api.post(f"/api/reglements/{row['id']}/transition",json={'action':'encaisser','frais':frais,
            'date_effective':date.today().isoformat()})
        assert r.status_code==200,r.text
        fee=Decimal(str(frais or 0))
        with Session(application['engine']) as db:
            sid=db.get(models.Reglement,row['id']).societe_id
            e=db.query(models.Ecriture).filter_by(societe_id=sid,journal='BQ').one()
            bank=next(x for x in e.lignes if x.compte=='5141')
            assert bank.debit==Decimal(120)-fee and bank.credit==0
            assert sum(x.debit for x in e.lignes)==sum(x.credit for x in e.lignes)==Decimal(120)
            charges=[x for x in e.lignes if x.compte=='61472']
            assert len(charges)==(1 if fee else 0)
            if fee:assert charges[0].debit==fee
