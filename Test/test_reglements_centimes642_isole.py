"""Régression sous-centime : POST/PATCH refusés avant facture/Journal/registres."""
from datetime import date
from decimal import Decimal
from sqlalchemy import text
from test_factures_liees635_isole import (
    application,application101,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,vente)
from test_suivi_correspondances641_isole import payer
from test_permissions_tva_runtime_isole import donnees_metier
from test_multi_societes_runtime_isole import ok


def test_642_creation_refuse_sous_centime_sans_mutation(application):
    a,b,ids=vente(application)
    try:
        f=next(x for x in ok(a.get('/api/factures',params={'exercice':date.today().year})) if x['id']==ids['fid'])
        avant=donnees_metier(application)
        r=a.post('/api/reglements',json={'facture_id':ids['fid'],'tiers':f['tiers'],'date':date.today().isoformat(),'montant':0.005,'mode':'virement','reference':'REPRO-FICTIF642','comptabiliser':True})
        if r.status_code!=422:
            with application['engine'].connect() as db:
                print('Reproduction native:',db.execute(text('SELECT r.montant,(SELECT sum(debit) FROM lignes_ecriture WHERE ecriture_id=r.ecriture_id),(SELECT sum(credit) FROM lignes_ecriture WHERE ecriture_id=r.ecriture_id) FROM reglements r WHERE facture_id=:f'),{'f':ids['fid']}).all())
        assert r.status_code==422,r.text
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_642_patch_refuse_sous_centime_sans_mutation(application):
    a,b,ids=vente(application)
    try:
        r=payer(a,ids['fid'],100);avant=donnees_metier(application)
        res=a.patch(f'/api/reglements/{r["id"]}',json={'montant':0.005,'notes':'Ne doit pas persister'})
        assert res.status_code==422,res.text
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_642_centime_comptabilise_identique_a_la_source(application):
    a,b,ids=vente(application)
    try:
        r=payer(a,ids['fid'],0.01,comptabiliser=True)
        with application['engine'].connect() as db:
            montant,debit,credit=db.execute(text('SELECT r.montant,(SELECT sum(debit) FROM lignes_ecriture WHERE ecriture_id=r.ecriture_id),(SELECT sum(credit) FROM lignes_ecriture WHERE ecriture_id=r.ecriture_id) FROM reglements r WHERE id=:id'),{'id':r['id']}).one()
            assert Decimal(str(montant))==debit==credit==Decimal('0.01')
    finally:a.close();b.close()
