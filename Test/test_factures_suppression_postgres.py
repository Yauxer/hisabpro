"""Suppression SQL du parent facture : immutabilité en PG éphémère."""
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from test_permissions_cycle_facturation_postgres import cible, ok


@pytest.fixture(scope='module')
def dossier(cible):
    client = cible['client']
    inscription = ok(client.post('/api/auth/register', json={'nom': 'Admin fictif078',
        'email': 'delete078@example.invalid', 'password': 'Suppression078!Sure',
        'raison_sociale': 'Factures fictives078'}))
    client.headers['Authorization'] = 'Bearer ' + inscription['access_token']
    tier = ok(client.post('/api/tiers', json={'type': 'client', 'nom': 'Client fictif078',
        'categorie_fiscale': 'particulier', 'delai_paiement': 30}), 201)
    payload = {'type': 'vente', 'date': date.today().isoformat(), 'tiers': tier['nom'],
        'tiers_id': tier['id'], 'lignes': [{'description': 'Service fictif078', 'quantite': 1,
            'prix_unitaire': 100, 'tva': 20}]}
    fid = ok(client.post('/api/factures', json=payload), 201)['id']
    ok(client.post(f'/api/factures/{fid}/valider'))
    avant = instantane(cible['owner'])
    for _ in range(2):
        cible['migration']('078_factures_definitives_suppression.sql')
        assert instantane(cible['owner']) == avant
    return {'cible': cible, 'payload': payload, 'fid': fid}


def instantane(engine):
    with engine.connect() as db:
        return tuple(db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).all()
            for table in ('factures', 'lignes_facture', 'reglements', 'ecritures', 'lignes_ecriture'))


@pytest.mark.parametrize('role', ['owner', 'runtime'])
def test078_facture_definitive_non_reglee_et_lignes_preservees(dossier, role):
    cible = dossier['cible']
    cible['garde']()
    avant = instantane(cible['owner'])
    with cible[role].connect() as db:
        try:
            with pytest.raises(DBAPIError) as erreur:
                db.execute(text('DELETE FROM factures WHERE id=:id'), {'id': dossier['fid']})
            assert erreur.value.orig.pgcode == '23514'
        finally:
            db.rollback()
    assert instantane(cible['owner']) == avant
    assert cible['client'].delete(f"/api/factures/{dossier['fid']}").status_code == 409


@pytest.mark.parametrize('role', ['owner', 'runtime'])
@pytest.mark.parametrize('proforma', [False, True])
def test078_brouillon_ou_proforma_reste_supprimable(dossier, role, proforma):
    cible = dossier['cible']
    cible['garde']()
    fid = ok(cible['client'].post('/api/factures', json={**dossier['payload'], 'est_proforma': proforma}), 201)['id']
    if proforma:
        assert cible['client'].post(f'/api/factures/{fid}/valider').status_code == 400
    with cible[role].begin() as db:
        # SQL direct ORM sans cascade DB : lignes supprimées explicitement.
        db.execute(text('DELETE FROM lignes_facture WHERE facture_id=:id'), {'id': fid})
        assert db.execute(text('DELETE FROM factures WHERE id=:id'), {'id': fid}).rowcount == 1
    with cible['owner'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM factures WHERE id=:id'), {'id': fid}) == 0


def test078_rejeu_apres_donnees_preserve_documents(dossier):
    cible = dossier['cible']
    avant = instantane(cible['owner'])
    cible['migration']('078_factures_definitives_suppression.sql')
    assert instantane(cible['owner']) == avant
