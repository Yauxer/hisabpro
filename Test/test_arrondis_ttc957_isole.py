"""TTC = HT arrondi + TVA arrondie : écritures facture/avoir équilibrées. PG nonce, données fictives."""
from contextlib import closing
from decimal import Decimal as D

import pytest
from sqlalchemy import text

from test_compensations_tva953_isole import (  # noqa: F401
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, dossier, ok,
)

B = {'description': 'B957', 'quantite': 7, 'prix_unitaire': 13.4567, 'tva': 18}
C = {'description': 'C957', 'quantite': 1.333, 'prix_unitaire': 99.995, 'tva': 10, 'remise': 3.3, 'remise2': 1.1}
DL = {'description': 'D957', 'quantite': 11, 'prix_unitaire': 0.015, 'tva': 9}


def _totaux(app, ecriture_id):
    with app['engine'].connect() as db:
        return db.execute(text('SELECT sum(debit), sum(credit) FROM lignes_ecriture WHERE ecriture_id=:i'),
                          {'i': ecriture_id}).one()


@pytest.mark.parametrize('nature,lignes,remise', [
    ('vente', [B], 0), ('vente', [B, C], 0), ('vente', [DL], 2.5), ('achat', [B, C], 0), ('achat', [C, DL], 2.5),
])
def test_957_facture_et_avoir_equilibres_au_centime(application, nature, lignes, remise):
    with closing(client(application)[0]) as api:
        _, tiers, banque = dossier(api, application, 'debit', 'client' if nature == 'vente' else 'fournisseur')
        f = ok(api.post('/api/factures', json={'type': nature, 'tiers': tiers['nom'], 'tiers_id': tiers['id'],
            'date': '2025-01-10', 'reference': 'ARR957', 'remise_globale': remise, 'lignes': lignes}), 201)
        ok(api.post(f'/api/factures/{f["id"]}/valider'))
        e = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
        debit, credit = _totaux(application, e['ecriture_id'])
        assert debit == credit
        ok(api.post(f'/api/ecritures/{e["ecriture_id"]}/valider'))
        situation = ok(api.get(f'/api/factures/{f["id"]}/reglements'))
        assert D(str(situation['total_ttc'])) == D(str(debit))
        decl = ok(api.get('/api/tva/declaration', params={'exercice': 2025, 'mois': 1}))
        cle = 'collectee' if nature == 'vente' else 'recuperable'
        with application['engine'].connect() as db:
            compte = '4455' if nature == 'vente' else '3455%'
            tva_ecr = db.scalar(text("SELECT abs(sum(debit-credit)) FROM lignes_ecriture WHERE ecriture_id=:i AND compte LIKE :c"),
                                {'i': e['ecriture_id'], 'c': compte})
        if nature == 'vente':  # achat : récupérable au paiement (CGI art. 101)
            assert D(str(decl[cle]['total'])) == D(str(tva_ecr))
        # Avoir total de la facture : même arrondi, écriture validable.
        a = ok(api.post('/api/avoirs', json={'facture_id': f['id'], 'date': '2025-01-20', 'motif': 'Retour ARR957',
            'lignes': [{'facture_ligne_id': l['id'], 'quantite': l['quantite']} for l in f['lignes']]}), 201)
        ea = ok(api.post(f'/api/avoirs/{a["id"]}/comptabiliser'))
        ea_id = ea.get('ecriture_id') or ea.get('ecriture', {}).get('id')
        da, ca = _totaux(application, ea_id)
        assert da == ca == debit
        ok(api.post(f'/api/ecritures/{ea_id}/valider'))
        assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant'] == 0
