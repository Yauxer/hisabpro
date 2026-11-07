"""Une RAS estimée n'est ni un règlement ni une preuve de retenue opérée."""
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client, lire
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux


@pytest.mark.parametrize('type_doc', ['vente', 'achat'])
def test_estimation_sans_paiement_ne_solde_pas(application, type_doc):
    with closing(client(application)[0]) as api:
        tid = ok(api.post('/api/tiers', json={'nom': 'Tiers RAS fictif', 'type': 'les_deux'}), 201)['id']
        f = ok(api.post('/api/factures', json={'type': type_doc, 'date': date.today().isoformat(),
            'tiers': 'Tiers RAS fictif', 'tiers_id': tid, 'reference': 'FR-RAS-FICTIF', 'ras_taux': 10,
            'lignes': [{'description': 'Service fictif', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        fid = f['id']
        ok(api.post(f'/api/factures/{fid}/valider'))
        situation = ok(api.get(f'/api/factures/{fid}/reglements'))
        assert situation['solde_restant'] == 1200
        assert situation['montant_ras_estime'] == 100 and situation['montant_ras_impute'] == situation['montant_ras'] == 0
        assert lire(api, fid)['montant_ras'] == 100
        rec = ok(api.get('/api/recouvrement/situation', params={'exercice': date.today().year}))
        row = next(x for x in rec['factures'] if x['id'] == fid)
        assert row['reste_du'] == 1200 and row['statut_paiement'] == 'non_reglee'
        partiel = ok(api.post('/api/reglements', json={'facture_id': fid, 'date': date.today().isoformat(),
            'tiers': f['tiers'], 'montant': 300, 'mode': 'virement', 'comptabiliser': False}), 201)
        assert ok(api.get(f'/api/factures/{fid}/reglements'))['solde_restant'] == 900
        suppression = api.delete(f"/api/reglements/{partiel['id']}")
        assert suppression.status_code == 204, suppression.text
        r = ok(api.post('/api/reglements', json={'facture_id': fid, 'date': date.today().isoformat(),
            'tiers': f['tiers'], 'montant': 1100, 'mode': 'virement', 'comptabiliser': True}), 201)
        assert r['est_comptabilisee']
        s = ok(api.get(f'/api/factures/{fid}/reglements'))
        assert s['solde_restant'] == 100 and not s['est_solde']
        with Session(application['engine']) as db:
            ff = db.get(models.Facture, fid); sid = ff.societe_id
            assert ff.ras_comptabilisee is False
            assert not db.query(models.Ecriture).filter_by(societe_id=sid, journal='OD').count()
            from services.delais_paiement_service import _evenements_reglement
            assert not any(x['type'] == 'ras' for x in _evenements_reglement(db, sid, ff, Decimal('1000')))
        # L'historique est construit exclusivement dans le cluster de cette fixture.
        legacy_doc = ok(api.post('/api/factures', json={'type': type_doc, 'date': date.today().isoformat(),
            'tiers': f['tiers'], 'tiers_id': tid, 'reference': 'LEGACY-RAS-VALIDE', 'ras_taux': 10,
            'lignes': [{'description': 'Historique fictif', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        fid = legacy_doc['id']
        with Session(application['engine']) as db:
            ff = db.get(models.Facture, fid); ff.ras_comptabilisee = True
            db.commit()
        ok(api.post(f'/api/factures/{fid}/valider'))
        ok(api.post('/api/reglements', json={'facture_id': fid, 'date': date.today().isoformat(),
            'tiers': f['tiers'], 'montant': 1100, 'mode': 'virement', 'comptabiliser': True}), 201)
        with Session(application['engine']) as db:
            ff = db.get(models.Facture, fid)
            collective, etat = ('3421', '3453') if type_doc == 'vente' else ('4411', '4457')
            debit_tiers = type_doc == 'achat'
            od = models.Ecriture(societe_id=sid, journal='OD', date=date.today(), exercice=date.today().year,
                source='reglement', reference=ff.numero if type_doc == 'vente' else ff.reference,
                libelle=f'Retenue à la source — {ff.numero} {ff.tiers}', lignes=[
                    models.LigneEcriture(compte=collective, tiers_id=tid, debit=100 if debit_tiers else 0, credit=0 if debit_tiers else 100),
                    models.LigneEcriture(compte=etat, debit=0 if debit_tiers else 100, credit=100 if debit_tiers else 0)])
            db.add(od); db.commit()
        avant = originaux(application, sid)
        s = ok(api.get(f'/api/factures/{fid}/reglements'))
        assert s['solde_restant'] == 0 and s['montant_ras_impute'] == 100
        assert s['ras_origine'] == 'historique_comptabilisee'
        assert originaux(application, sid) == avant
        from services.ras_paiement_service import date_od_ras_historique
        with Session(application['engine']) as db:
            ff = db.get(models.Facture, fid)
            assert date_od_ras_historique(db, sid, ff, 100) == date.today()
            diagnostics = []
            events = _evenements_reglement(db, sid, ff, Decimal('1000'), diagnostics)
            assert [x['date'] for x in events if x['type'] == 'ras'] == [date.today()]
            assert not diagnostics
            od = db.query(models.Ecriture).filter_by(societe_id=sid, journal='OD').one()
            od.lignes[0].compte = '5141'
            db.commit()
            assert date_od_ras_historique(db, sid, ff, 100) is None
            diagnostics = []
            assert not any(x['type'] == 'ras' for x in _evenements_reglement(db, sid, ff, Decimal('1000'), diagnostics))
            assert diagnostics
        # Une pièce historique invalide est construite AVANT sa validation,
        # sans désactiver la protection des factures définitives.
        historique = ok(api.post('/api/factures', json={'type': type_doc, 'date': date.today().isoformat(),
            'tiers': f['tiers'], 'tiers_id': tid, 'reference': 'LEGACY-RAS-NAN', 'ras_taux': 10,
            'lignes': [{'description': 'Historique fictif', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        hid = historique['id']
        with Session(application['engine']) as db:
            legacy = db.get(models.Facture, hid)
            legacy.ras_taux = float('nan')
            legacy.numero = f'LEGACY-NAN-{hid}'
            legacy.est_validee = True
            db.commit()
            if type_doc == 'vente':
                relance = models.RelanceRecouvrement(societe_id=sid, facture_id=hid, niveau=1,
                    date_relance=date.today(), canal='email', montant_promis=10, commentaire='Historique fictif')
                db.add(relance); db.commit(); relance_id = relance.id
        avant = originaux(application, sid)
        s = ok(api.get(f'/api/factures/{hid}/reglements'))
        assert s['solde_restant'] is None and s['ras_anomalie']
        rec = ok(api.get('/api/recouvrement/situation', params={'exercice': date.today().year}))
        row = next(x for x in rec['factures'] if x['id'] == hid)
        assert row['reste_du'] is None and row['ras_anomalie']
        assert rec['resume'][type_doc]['calcul_incomplet'] and rec['resume'][type_doc]['reste'] is None
        assert rec['resume']['position_nette'] is None
        assert originaux(application, sid) == avant
        if type_doc == 'vente':
            with Session(application['engine']) as db:
                nombre = db.query(models.RelanceRecouvrement).filter_by(societe_id=sid).count()
            refus = api.post('/api/recouvrement/relances', json={'facture_id': hid, 'montant_promis': 10})
            assert refus.status_code == 409 and 'RAS' in refus.json()['detail']
            refus = api.patch(f'/api/recouvrement/relances/{relance_id}', json={'montant_promis': 20})
            assert refus.status_code == 409 and 'RAS' in refus.json()['detail']
            with Session(application['engine']) as db:
                assert db.query(models.RelanceRecouvrement).filter_by(societe_id=sid).count() == nombre
                assert db.get(models.RelanceRecouvrement, relance_id).montant_promis == 10
