"""Annulation historique : une OD exacte unique, jamais un choix arbitraire."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
import models
from services.auxiliaire_service import rattacher_tiers_aux_lignes
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux
from test_ras_capture_reglement_postgres import paiement


def preparer_historique(app, api, nature, variante):
    tid=ok(api.post('/api/tiers',json={'nom':'Historique RAS fictif','type':'les_deux'}),201)['id']
    f=ok(api.post('/api/factures',json={'type':nature,'date':date.today().isoformat(),
        'reference':'FOURN-RAS-HISTORIQUE','tiers':'Historique RAS fictif','tiers_id':tid,'ras_taux':10,
        'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':1000,'tva':20}]}),201)
    with Session(app['engine']) as db:
        doc=db.get(models.Facture,f['id']);doc.ras_comptabilisee=True;db.commit();sid=doc.societe_id
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    r=paiement(api,f,1100 if variante!='autres' else 600)
    od_ids=[]
    with Session(app['engine']) as db:
        doc=db.get(models.Facture,f['id'])
        for _ in range(0 if variante=='absente' else 2 if variante=='double' else 1):
            vente=nature=='vente';montant=99 if variante=='malformee' else 100
            od=models.Ecriture(societe_id=sid,journal='OD',source='reglement',date=date.today(),
                exercice=date.today().year,reference=doc.numero if vente else doc.reference,
                libelle=f'Retenue à la source — {doc.numero} {doc.tiers}',lignes=[
                  models.LigneEcriture(compte='3453' if vente else '4457',debit=montant if vente else 0,credit=0 if vente else montant),
                  models.LigneEcriture(compte='3421' if vente else '4411',tiers_id=tid,debit=0 if vente else montant,credit=montant if vente else 0)])
            rattacher_tiers_aux_lignes(db,sid,od.lignes,tiers_id=tid,nature='client' if vente else 'fournisseur')
            db.add(od);db.flush();od_ids.append(od.id)
        if variante=='contrepassée':
            orig=db.get(models.Ecriture,od_ids[0])
            db.add(models.Ecriture(societe_id=sid,journal='OD',source='reglement',date=date.today(),
                exercice=date.today().year,reference='ANN-HISTORIQUE-FICTIF',libelle='Contrepassation historique fictive',
                contrepassation_de_id=orig.id,lignes=[models.LigneEcriture(compte=l.compte,debit=l.credit,credit=l.debit,tiers_id=l.tiers_id) for l in orig.lignes]))
        db.commit()
    if variante=='autres':
        paiement(api,f,500)
    for eid in od_ids:
        ok(api.post(f'/api/ecritures/{eid}/valider'))
    ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
    return f,r,sid,od_ids


def etat(app,fid,rid):
    with Session(app['engine']) as db:
        f=db.get(models.Facture,fid);r=db.get(models.Reglement,rid)
        return (tuple((c.name,getattr(f,c.name)) for c in f.__table__.columns),
                tuple((c.name,getattr(r,c.name)) for c in r.__table__.columns))


@pytest.mark.parametrize('variante',['absente','double','malformee','contrepassée'])
def test_annulation_historique_incertaine_refuse_sans_mutation(application,variante):
    with closing(client(application)[0]) as api:
        f,r,sid,_=preparer_historique(application,api,'vente',variante)
        avant=originaux(application,sid);avant_etat=etat(application,f['id'],r['id'])
        response=api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Recette historique fictive'})
        assert response.status_code==409,response.text
        assert originaux(application,sid)==avant
        assert etat(application,f['id'],r['id'])==avant_etat


@pytest.mark.parametrize('nature',['vente','achat'])
def test_annulation_historique_unique_conserve_originaux(application,nature):
    with closing(client(application)[0]) as api:
        f,r,sid,ids=preparer_historique(application,api,nature,'unique')
        avant=originaux(application,sid)
        resultat=ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Recette historique exacte'}))
        assert resultat['statut']=='annule'
        apres=originaux(application,sid)
        assert apres[:len(avant)]==avant and len(apres)==len(avant)+2
        with Session(application['engine']) as db:
            assert db.get(models.Facture,f['id']).ras_comptabilisee is False
            contre=db.query(models.Ecriture).filter_by(societe_id=sid,contrepassation_de_id=ids[0]).one()
            assert sum(Decimal(str(l.debit)) for l in contre.lignes)==Decimal('100')
            assert sum(Decimal(str(l.credit)) for l in contre.lignes)==Decimal('100')
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==1200
        ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Rejeu'}))
        assert originaux(application,sid)==apres


def test_autre_reglement_actif_conserve_ras_historique(application):
    with closing(client(application)[0]) as api:
        f,r,sid,ids=preparer_historique(application,api,'vente','autres')
        avant=originaux(application,sid)
        ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Autre paiement conservé'}))
        apres=originaux(application,sid)
        assert apres[:len(avant)]==avant and len(apres)==len(avant)+1
        with Session(application['engine']) as db:
            assert db.get(models.Facture,f['id']).ras_comptabilisee is True
            assert db.query(models.Ecriture).filter_by(societe_id=sid,contrepassation_de_id=ids[0]).count()==0
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==600
