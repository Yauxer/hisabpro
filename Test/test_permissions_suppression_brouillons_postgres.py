"""ACL de colonnes pour la suppression API des brouillons, PG isolé."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from test_factures_suppression_postgres import cible, dossier, instantane, ok


@pytest.fixture(scope='module')
def permissions(dossier):
    cible = dossier['cible']
    avant = instantane(cible['owner'])
    with cible['runtime'].connect() as db:
        droits_globaux = {table: db.scalar(text("SELECT has_table_privilege(current_user,:table,'UPDATE')"), {'table': table})
            for table in ('bons_commande', 'bons_livraison', 'devis', 'mouvements_stock')}
    for _ in range(2):
        cible['migration']('079_permissions_suppression_brouillons.sql')
        assert instantane(cible['owner']) == avant
    return {**dossier, 'droits_globaux_avant': droits_globaux}


@pytest.mark.parametrize('proforma', [False, True])
def test079_api_supprime_brouillon_ou_proforma_sans_privileges_globaux(permissions, proforma):
    cible = permissions['cible']
    fid = ok(cible['client'].post('/api/factures', json={**permissions['payload'], 'est_proforma': proforma}), 201)['id']
    assert cible['client'].delete(f'/api/factures/{fid}').status_code == 204
    with cible['owner'].connect() as db:
        assert db.scalar(text('SELECT count(*) FROM factures WHERE id=:id'), {'id': fid}) == 0
        assert db.scalar(text('SELECT count(*) FROM lignes_facture WHERE facture_id=:id'), {'id': fid}) == 0


@pytest.mark.parametrize('table,interdit', [('bons_commande', 'date'), ('bons_livraison', 'date'),
    ('devis', 'date'), ('mouvements_stock', 'quantite')])
def test079_colonnes_hors_detachement_restent_interdites(permissions, table, interdit):
    cible = permissions['cible']
    cible['garde']()
    with cible['runtime'].connect() as db:
        assert db.scalar(text("SELECT has_column_privilege(current_user,:table,'facture_id','UPDATE')"), {'table': table})
        assert db.scalar(text("SELECT has_table_privilege(current_user,:table,'UPDATE')"), {'table': table}) == permissions['droits_globaux_avant'][table]
        if permissions['droits_globaux_avant'][table]:
            # 012 donne déjà UPDATE global sur mouvements_stock. Ce lot ne
            # normalise pas cette ACL historique et n'en ajoute aucune.
            assert table == 'mouvements_stock'
            return
        try:
            with pytest.raises(DBAPIError) as erreur:
                db.execute(text(f'UPDATE {table} SET {interdit}={interdit}'))
            assert erreur.value.orig.pgcode == '42501'
        finally:
            db.rollback()


def test079_ne_contourne_pas_garde_facture_definitive(permissions):
    assert permissions['cible']['client'].delete(f"/api/factures/{permissions['fid']}").status_code == 409
