"""Montants effectivement affectés, sans confondre acompte et imputation."""
from contextlib import closing
import pytest
from sqlalchemy.orm import Session
import models
from test_tva_acomptes945_isole import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, acompte, declaration, montant, core, ok,
)


def facture(api, tiers, nature, jour='2025-06-15', ht=10000, ref='F-FICTIF945'):
    f = ok(api.post('/api/factures', json={'type': nature, 'tiers': tiers['nom'],
        'tiers_id': tiers['id'], 'date': jour, 'reference': ref,
        'lignes': [{'description': 'Service FICTIF945', 'quantite': 1, 'prix_unitaire': ht, 'tva': 20}]}), 201)
    ok(api.post(f'/api/factures/{f["id"]}/valider'))
    return f


def imputer(api, ac, f, montant=6000, jour='2025-06-20'):
    return ok(api.post(f'/api/acomptes/{ac["id"]}/imputer', json={
        'facture_id': f['id'], 'montant': montant, 'date_imputation': jour}))


@pytest.mark.parametrize('nature,regime,avant,un,deux', [
    ('client', 'debit', 8000, 7000, 6000),
    ('client', 'encaissement', 4000, 4000, 4000),
    ('fournisseur', 'encaissement', 0, 1000, 2000),
])
def test_945_imputations_partielles_multiples_et_annulation(application, nature, regime, avant, un, deux):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application, regime, nature)
        ac = acompte(api, tiers, banque, mode='virement', nature=nature)
        type_facture = 'vente' if nature == 'client' else 'achat'
        f1 = facture(api, tiers, type_facture)
        f2 = facture(api, tiers, type_facture, '2025-06-16', ref='F2-FICTIF945')
        cle = 'collectee' if nature == 'client' else 'recuperable'
        assert montant(declaration(api, 6), cle) == avant
        imputer(api, ac, f1)
        assert montant(declaration(api, 6), cle) == un
        imputer(api, ac, f2)
        assert montant(declaration(api, 6), cle) == deux
        ac2 = next(a for a in ok(api.get('/api/acomptes', params={'exercice': 2025})) if a['id'] == ac['id'])
        assert ac2['facture_id'] is None and ac2['montant_impute'] == 12000
        premiere = next(i for i in ac2['imputations'] if i['facture_id'] == f1['id'])
        ok(api.post(f'/api/acomptes/{ac["id"]}/imputations/{premiere["id"]}/annuler',
                    params={'date_annulation': '2025-06-25'}))
        livre = core(application, sid)
        assert montant(declaration(api, 6), cle) == un
        assert core(application, sid) == livre


def test_945_encaissement_apres_facturation_debit_sans_double_tva(application):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application, 'debit')
        ac = acompte(api, tiers, banque, jour='2025-05-01')
        f = facture(api, tiers, 'vente', ht=20000)
        assert montant(declaration(api, 5)) == 0
        assert montant(declaration(api, 6)) == 4000
        ok(api.post(f'/api/acomptes/{ac["id"]}/statut-paiement',
                    json={'statut': 'encaisse', 'date_operation': '2025-07-05'}))
        imputer(api, ac, f, montant=24000, jour='2025-07-10')
        avant = core(application, sid)
        assert montant(declaration(api, 6)) == 4000
        assert montant(declaration(api, 7)) == 0
        assert montant(declaration(api)) == 4000 and core(application, sid) == avant


def test_945_variante_encaissement_impaye_et_acompte_du_cahier(application):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application, 'encaissement')
        ac = acompte(api, tiers, banque, mode='virement')
        assert montant(declaration(api, 6)) == 4000
        f = facture(api, tiers, 'vente', ht=120000, ref='VENTE-SERVICE')
        imputer(api, ac, f, montant=24000, jour='2025-06-15')
        ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'],
            'montant': 120000, 'date': '2025-06-30', 'mode': 'virement',
            'banque': banque['banque'], 'reference': 'VENTE-SERVICE-PAY', 'comptabiliser': True}), 201)
        assert montant(declaration(api, 6)) == 24000
        impayee = facture(api, tiers, 'vente', jour='2025-12-10', ht=12000, ref='VENTE-IMPAYEE')
        r = ok(api.post('/api/reglements', json={'facture_id': impayee['id'], 'tiers': tiers['nom'],
            'montant': 2000, 'date': '2025-12-12', 'mode': 'cheque',
            'banque': banque['banque'], 'reference': 'CHQ-REJET', 'comptabiliser': True}), 201)
        ok(api.post(f'/api/reglements/{r["id"]}/transition',
                    json={'action': 'rejeter', 'date_effective': '2025-12-15', 'frais': 0}))
        avant = core(application, sid)
        assert montant(declaration(api, 12)) == 0
        assert montant(declaration(api)) == 24000
        assert ok(api.get(f'/api/factures/{impayee["id"]}/reglements'))['solde_restant'] == 14400
        assert core(application, sid) == avant


def test_945_paiement_fournisseur_historique_sans_date_signale(application):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application, nature='fournisseur')
        ac = acompte(api, tiers, banque, nature='fournisseur')
        ok(api.post(f'/api/acomptes/{ac["id"]}/statut-paiement',
                    json={'statut': 'encaisse', 'date_operation': '2025-06-05'}))
        f = facture(api, tiers, 'achat', ht=20000)
        imputer(api, ac, f, montant=24000)
        assert montant(declaration(api, 6), 'recuperable') == 4000
        with Session(application['engine']) as db:
            db.get(models.Acompte, ac['id']).date_encaissement = None
            db.commit()
        avant = core(application, sid)
        vue = declaration(api, 6)
        assert montant(vue, 'recuperable') == 0
        assert any(ac['numero'] in a and 'paiement effective absente' in a for a in vue['alertes'])
        assert core(application, sid) == avant
