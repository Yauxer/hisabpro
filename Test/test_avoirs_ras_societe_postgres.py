"""Crédit d'avoir : société réelle, estimation et capture sur PG nonce."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux
from test_ras_capture_reglement_postgres import appliquer, paiement, payload


@pytest.mark.parametrize('nature',['vente','achat'])
@pytest.mark.parametrize('capture',[False,True])
def test_credit_avoir_ras_effective_et_scope_societe(application,nature,capture):
    if capture:
        appliquer(application)
    with closing(client(application)[0]) as api:
        sid=ok(api.get('/api/societe/moi'))['id']
        tid=ok(api.post('/api/tiers',json={'nom':'Avoir RAS fictif','type':'les_deux'}),201)['id']
        f=ok(api.post('/api/factures',json={'type':nature,'date':date.today().isoformat(),
            'tiers':'Avoir RAS fictif','tiers_id':tid,'reference':'AV-RAS-FICTIF','ras_taux':10,
            **({'nature_tva_achat':'charge','tva_deductible_pct':100} if nature=='achat' else {}),
            'lignes':[{'description':'Service fictif','quantite':2,'prix_unitaire':500,'tva':20}]}),201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        compta=ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        ok(api.post(f"/api/ecritures/{compta['ecriture_id']}/valider"))
        r=paiement(api,f,1100)
        ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
        if capture:
            c=ok(api.post(f"/api/reglements/{r['id']}/ras",json=payload(100,nature)))
            ok(api.post(f"/api/ecritures/{c['ecriture_id']}/valider"))
        avant=originaux(application,sid)
        av=ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':date.today().isoformat(),
            'motif':'Crédit partiel fictif','retour_stock':False,
            'lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':1}]}),201)
        assert av['total_ttc']==600
        attendu=600 if capture else 500
        assert av['credit_excedentaire']==av['montant_disponible']==attendu
        assert av['montant_utilise']==0
        rows=ok(api.get('/api/avoirs',params={'exercice':date.today().year}))
        assert next(x for x in rows if x['id']==av['id'])['montant_disponible']==attendu
        assert originaux(application,sid)==avant
        with closing(client(application)[0]) as autre:
            assert ok(autre.get('/api/avoirs',params={'exercice':date.today().year}))==[]
            assert autre.get(f"/api/avoirs/{av['id']}/factures-imputables").status_code==404
            refus=autre.post(f"/api/avoirs/{av['id']}/utiliser",json={'type_utilisation':'remboursement',
                'date_utilisation':date.today().isoformat(),'montant':1,'mode':'virement'})
            if refus.status_code!=404:
                print(application['api_log'].read_text(encoding='utf-8',errors='replace')[-7000:])
            assert refus.status_code==404,refus.text
        assert originaux(application,sid)==avant
        if not capture:
            ok(api.post(f"/api/avoirs/{av['id']}/comptabiliser"))
            utilisation=ok(api.post(f"/api/avoirs/{av['id']}/utiliser",json={
                'type_utilisation':'remboursement','date_utilisation':date.today().isoformat(),
                'montant':100,'mode':'virement','reference':'REMBOURSEMENT-FICTIF'}))
            assert utilisation['credit_excedentaire']==500
            assert utilisation['montant_utilise']==100 and utilisation['montant_disponible']==400
            assert originaux(application,sid)[:len(avant)]==avant
        if capture:
            ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Annulation fictive du cash et capture'}))
            apres_annulation=originaux(application,sid)
            assert apres_annulation[:len(avant)]==avant
            row=next(x for x in ok(api.get('/api/avoirs',params={'exercice':date.today().year})) if x['id']==av['id'])
            assert row['montant_disponible']==row['credit_excedentaire']==0
            assert originaux(application,sid)==apres_annulation
        with Session(application['engine']) as db:
            assert db.get(models.Facture,f['id']).ras_comptabilisee is False
