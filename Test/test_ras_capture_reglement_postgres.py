"""Capture explicite et annulation reliée, API réelle sur PostgreSQL nonce."""
from contextlib import closing
from datetime import date
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import httpx
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux

SQL = Path(__file__).resolve().parents[1] / 'hisabpro-backend/083_ras_reglements.sql'


def appliquer(app):
    c = app['cluster']; verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    conn = app['engine'].raw_connection()
    try:
        cur = conn.cursor(); cur.execute(SQL.read_text(encoding='utf-8')); conn.commit()
    finally:
        conn.close()


def preparer(api, nature):
    tid = ok(api.post('/api/tiers', json={'nom': 'RAS capture fictif', 'type': 'les_deux'}), 201)['id']
    f = ok(api.post('/api/factures', json={'type': nature, 'date': date.today().isoformat(), 'reference': 'CAPTURE-FICTIVE',
        'tiers': 'RAS capture fictif', 'tiers_id': tid, 'ras_taux': 10,
        'lignes': [{'description': 'Service fictif', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    return f


def paiement(api, f, montant):
    return ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': f['tiers'],
        'date': date.today().isoformat(), 'montant': montant, 'mode': 'virement', 'comptabiliser': True}), 201)


def payload(montant, nature, reference='PIECE-RAS-FICTIVE'):
    return {'montant': montant, 'date_operation': date.today().isoformat(), 'reference': reference,
            'compte_destination': '3453' if nature == 'vente' else '4457'}


@pytest.mark.parametrize('nature', ['vente','achat'])
def test_capture_partielle_reglements_annulation_idempotence(application, nature):
    appliquer(application)
    with closing(client(application)[0]) as api:
        f = preparer(api, nature); rid1 = paiement(api,f,400)['id']
        p1 = payload(30,nature)
        c1 = ok(api.post(f'/api/reglements/{rid1}/ras', json=p1))
        s = ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert s['solde_restant'] == 770 and s['montant_ras_impute'] == 30 and s['montant_ras_estime'] == 100
        assert s['ras_origine'] == 'capture_reglement'
        eid=c1['ecriture_id']
        assert api.patch(f'/api/ecritures/{eid}',json={'libelle':'Interdit'}).status_code==409
        assert api.delete(f'/api/ecritures/{eid}').status_code==409
        assert api.post(f'/api/ecritures/{eid}/contrepasser',json={'motif':'Interdit'}).status_code==409
        ok(api.post(f'/api/ecritures/{eid}/valider'))
        assert ok(api.post(f'/api/reglements/{rid1}/ras', json=p1))['id'] == c1['id']
        assert api.post(f'/api/reglements/{rid1}/ras', json=payload(31,nature)).status_code == 409
        rid2 = paiement(api,f,700)['id']; c2 = ok(api.post(f'/api/reglements/{rid2}/ras', json=payload(70,nature,'PIECE-RAS-2')))
        s = ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert s['solde_restant'] == 0 and s['montant_ras_impute'] == 100 and s['est_solde']
        with Session(application['engine']) as db:
            ff = db.get(models.Facture,f['id']); sid=ff.societe_id
            assert ff.ras_comptabilisee is False
            for c in (c1,c2):
                ec = db.get(models.Ecriture,c['ecriture_id'])
                assert ec.est_validee is (c['id']==c1['id']) and ec.source == 'ras_reglement' and len(ec.lignes)==2
                assert sum(Decimal(str(l.debit)) for l in ec.lignes) == Decimal(str(c['montant']))
                assert sum(Decimal(str(l.credit)) for l in ec.lignes) == Decimal(str(c['montant']))
                assert any(l.tiers_id==ff.tiers_id and l.compte_auxiliaire_snapshot for l in ec.lignes)
            from services.delais_paiement_service import _evenements_reglement
            events = _evenements_reglement(db,sid,ff,Decimal('1000'))
            assert sum(x['montant'] for x in events if x['type']=='ras') == Decimal('100')
        avant=originaux(application,sid)
        ok(api.post(f"/api/ecritures/{c2['ecriture_id']}/valider"))
        avant=originaux(application,sid)
        resultat=ok(api.post(f'/api/reglements/{rid2}/annuler',json={'motif':'Erreur fictive', 'date_annulation':date.today().isoformat()}))
        assert resultat['statut']=='annule'
        apres=originaux(application,sid)
        assert apres[:len(avant)]==avant
        assert len(apres)==len(avant)+2
        s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert s['solde_restant']==770 and s['montant_ras_impute']==30
        caps=ok(api.get(f'/api/reglements/{rid2}/ras'))
        assert caps['disponible'] and caps['captures'][0]['annulation_id']
        ok(api.post(f'/api/reglements/{rid2}/annuler',json={'motif':'Rejeu fictif'}))
        assert originaux(application,sid)==apres


@pytest.mark.parametrize('valeur',[True,False,'NaN','Infinity','-Infinity',0,-1,'1e1000000','0.001','1e16'])
def test_schema_capture_refuse_montants_non_admissibles(valeur):
    from routers.ras_reglements import CaptureIn
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CaptureIn(**payload(valeur,'vente'))


def test_capture_concurrente_solde_et_permissions(application):
    appliquer(application)
    with closing(client(application)[0]) as api:
        f=preparer(api,'vente')
        regs=[paiement(api,f,400), paiement(api,f,700)]
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,f['id']).societe_id
        def envoyer(r):
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as concurrent:
                return concurrent.post(f"/api/reglements/{r['id']}/ras",json=payload(80,'vente', 'CONCURRENT-' + str(r['id'])))
        with ThreadPoolExecutor(max_workers=2) as pool:
            reponses=list(pool.map(envoyer,regs))
        assert sorted(r.status_code for r in reponses)==[200,409],[(r.status_code,r.text) for r in reponses]
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==20
        gagnant=regs[next(i for i,r in enumerate(reponses) if r.status_code==200)]
        avant=originaux(application,sid)
        with closing(client(application)[0]) as autre:
            assert autre.get(f"/api/reglements/{gagnant['id']}/ras").status_code==404
            assert autre.post(f"/api/reglements/{gagnant['id']}/ras",json=payload(1,'vente')).status_code==404
        for mauvais in [payload(True,'vente'),payload('NaN','vente'),payload(100,'vente'),
                        {**payload(1,'vente'),'compte_destination':'9999999999'}]:
            r=api.post(f"/api/reglements/{regs[1-next(i for i,r in enumerate(reponses) if r.status_code==200)]['id']}/ras",json=mauvais)
            assert r.status_code in (422,409),r.text
        assert originaux(application,sid)==avant


def test_capture_controles_reels_et_centimes(application):
    appliquer(application)
    with closing(client(application)[0]) as api:
        f=preparer(api,'vente'); r=paiement(api,f,400)
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,f['id']).societe_id
        avant=originaux(application,sid)
        for invalide in [payload('1e16','vente'),payload('0.001','vente'),
                        {**payload(30,'vente'),'compte_destination':'4411'},
                        {**payload(30,'vente'),'date_operation':(date.today()+timedelta(days=1)).isoformat()},
                        {**payload(30,'vente'),'reference':' '},
                        {**payload(30,'vente'),'taux':10}]:
            refus=api.post(f"/api/reglements/{r['id']}/ras",json=invalide)
            assert refus.status_code==422,refus.text
        assert originaux(application,sid)==avant
        email='ras-lecture-'+uuid.uuid4().hex[:8]+'@example.com'; password='RasLecteurFictif2026!'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            login=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))
            lecteur.headers['Authorization']='Bearer '+login['access_token']
            detail=ok(lecteur.get(f"/api/reglements/{r['id']}/ras"))
            assert detail['disponible'] and not detail['peut_capturer']
            assert lecteur.post(f"/api/reglements/{r['id']}/ras",json=payload(30,'vente')).status_code==403
        assert originaux(application,sid)==avant
        capture=ok(api.post(f"/api/reglements/{r['id']}/ras",json=payload('0.29','vente')))
        with Session(application['engine']) as db:
            ec=db.get(models.Ecriture,capture['ecriture_id'])
            assert sum(l.debit for l in ec.lignes)==Decimal('0.29')
            assert sum(l.credit for l in ec.lignes)==Decimal('0.29')
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==799.71
        # Appartenance multi-société accordée et token changé par les vraies API.
        with closing(client(application)[0]) as invite:
            me=ok(invite.get('/api/auth/me'))
            ok(api.post(f'/api/societes/{sid}/inviter',params={'email':me['email'],'role':'comptable'}))
            token=ok(invite.post(f'/api/societes/switcher/{sid}'))
            invite.headers['Authorization']='Bearer '+token['access_token']
            second=paiement(invite,f,100)
            c=ok(invite.post(f"/api/reglements/{second['id']}/ras",json=payload(1,'vente','INVITE-FICTIF')))
            assert c['created_by']==me['id']
        historique=ok(api.post('/api/factures',json={'type':'vente','date':date.today().isoformat(),
            'tiers':f['tiers'],'tiers_id':f['tiers_id'],'ras_taux':10,
            'lignes':[{'description':'Historique fictif','quantite':1,'prix_unitaire':1000,'tva':20}]}),201)
        with Session(application['engine']) as db:
            db.get(models.Facture,historique['id']).ras_comptabilisee=True;db.commit()
        ok(api.post(f"/api/factures/{historique['id']}/valider"))
        reg=paiement(api,historique,400)
        avant=originaux(application,sid)
        assert api.post(f"/api/reglements/{reg['id']}/ras",json=payload(30,'vente')).status_code==409
        assert originaux(application,sid)==avant
