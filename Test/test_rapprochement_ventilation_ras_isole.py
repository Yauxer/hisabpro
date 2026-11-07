"""Retenue distincte du virement : profil fictif10%, aucune règle fiscale nouvelle."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier,poster
from test_ras_capture_reglement_postgres import appliquer,payload as ras_payload
from test_rapprochement_ventilation_isole import migration,rapprocher,situation
from test_lecture_reglements_historiques import photo

@pytest.mark.parametrize('sens',['vente','achat'])
def test_releve210_exclut_retenue10_preexistante_et_conserve_capture(application,migration,sens):
    appliquer(application)
    with closing(client(application)[0]) as api:
        _,ids,p=dossier(api,sens,ras=10)
        f=next(x for x in api.get('/api/factures',params={'exercice':date.today().year}).json() if x['id']==ids[0])
        r=api.post('/api/reglements',json={'facture_id':ids[0],'date':date.today().isoformat(),
            'tiers':f['tiers'],'montant':20,'mode':'virement'})
        assert r.status_code==201,r.text
        r=api.post(f"/api/reglements/{r.json()['id']}/ras",json=ras_payload(10,sens,'RAS-FICT-BANQUE'))
        assert r.status_code==200,r.text
        assert api.get(f'/api/factures/{ids[0]}/reglements').json()['solde_restant']==90
        p['ventilations'][0]['montant']=90;p['montant']=210
        r=poster(api,p);assert r.status_code==201,r.text
        rows=r.json()
        for row in rows:
            r=api.post(f"/api/ecritures/{row['ecriture_id']}/valider",json={})
            assert r.status_code==200,r.text
        r=api.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),
            'libelle':p['reference'],'montant':210,'sens':'credit' if sens=='vente' else 'debit'})
        assert r.status_code==201,r.text
        rid=r.json()['id'];avant=photo(application)
        r=rapprocher(api,rid,p);assert r.status_code==200,r.text
        d=situation(api)
        assert len(d['ventilations'])==1 and d['ventilations'][0]['montant']==210
        assert len([x for x in d['ecritures'] if x['rapprochee']])==2
        assert api.get(f'/api/factures/{ids[0]}/reglements').json()['solde_restant']==0
        assert api.get(f'/api/factures/{ids[1]}/reglements').json()['solde_restant']==120
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,ids[0]).societe_id
            captures=db.query(models.Ecriture).filter_by(societe_id=sid,source='ras_reglement').all()
            assert len(captures)==1
            assert sum(x.debit for x in captures[0].lignes)==sum(x.credit for x in captures[0].lignes)==Decimal(10)
            assert all(x.compte!='5141' for x in captures[0].lignes)
        assert photo(application)==avant
        assert api.post(f'/api/rapprochement/{rid}/derapprocher',json={}).status_code==200
        assert photo(application)==avant
