"""Calculs facture avant mutation : API authentifiée et PG nonce exclusivement."""
from datetime import date
import pytest
from sqlalchemy.orm import Session
import models
from test_devis_stock_diagnostic import application, dossier


def instantane(application):
    with Session(application['engine']) as db:
        return {m.__tablename__: [repr(tuple(getattr(r, c.name) for c in m.__table__.columns))
                for r in db.query(m).order_by(m.id).all()]
                for m in (models.Facture, models.LigneFacture, models.Ecriture,
                          models.LigneEcriture, models.Article, models.MouvementStock)}


def ligne(q=1, prix=10):
    return {'description': 'Service fictif limites facture', 'quantite': q,
            'prix_unitaire': prix, 'tva': 20}


@pytest.mark.parametrize('valeurs', [
    {'lignes': [ligne(1e308, 10)]},
    {'lignes': [ligne(1, 1e27)]},
    {'lignes': [ligne()], 'frais_transport_ht': 1e308},
    {'lignes': [ligne()], 'frais_emballage_ht': 1e308},
])
@pytest.mark.parametrize('mode', ['creation', 'modification'])
def test_calcul_non_representable_refuse_sans_mutation(application, dossier, valeurs, mode):
    api, *_ = dossier
    if mode == 'modification':
        r = api.post('/api/factures', json={'date': date.today().isoformat(),
            'tiers': 'Client fictif limites', 'type': 'vente', 'lignes': [ligne()]})
        assert r.status_code == 201, r.text
        url = '/api/factures/' + str(r.json()['id'])
    avant = instantane(application)
    if mode == 'creation':
        r = api.post('/api/factures', json={'date': date.today().isoformat(),
            'tiers': 'Client fictif limites', 'type': 'vente', **valeurs})
    else:
        r = api.patch(url, json={'notes': 'Cette note ne doit pas persister', **valeurs})
    assert r.status_code == 422, (r.text, 'sources_modifiees', avant != instantane(application))
    assert instantane(application) == avant


def test_calculs_commerciaux_normaux_et_gratuit_preserves(dossier):
    api, *_ = dossier
    payload = {'date': date.today().isoformat(), 'tiers': 'Client fictif limites',
        'type': 'vente', 'lignes': [ligne(.5, 100), ligne(1, 0)],
        'remise_globale': 10, 'escompte': 5,
        'frais_transport_ht': 10, 'frais_emballage_ht': 5}
    r = api.post('/api/factures', json=payload)
    assert r.status_code == 201, r.text
    # Net commercial 50 * .9 + 15 = 60 ; net financier 57, TVA11.4, TTC68.4.
    assert r.json()['total_ht'] == 60
    assert r.json()['total_tva'] == 11.4
    assert r.json()['total_ttc'] == 68.4
    fid = r.json()['id']
    assert api.patch('/api/factures/' + str(fid), json={'notes': 'Note seule'}).status_code == 200
    r = api.patch('/api/factures/' + str(fid), json={'lignes': [ligne(.5, 100), ligne(1, 0)]})
    assert r.status_code == 200, r.text
    r = api.get('/api/factures', params={'exercice': date.today().year})
    assert r.status_code == 200, r.text
    assert next(f for f in r.json() if f['id'] == fid)['total_ttc'] == 68.4


def test_note_historique_independante_sans_reparer_montants(application, dossier):
    api, *_ = dossier
    r = api.post('/api/factures', json={'date': date.today().isoformat(),
        'tiers': 'Client fictif limites', 'type': 'vente', 'lignes': [ligne()]})
    assert r.status_code == 201, r.text
    fid = r.json()['id']
    # Historique anormal exclusivement dans le laboratoire nonce.
    with Session(application['engine']) as db:
        f = db.get(models.Facture, fid)
        f.lignes[0].prix_unitaire = 1e27
        db.commit()
    avant = instantane(application)['lignes_facture']
    r = api.patch('/api/factures/' + str(fid), json={'notes': 'Note historique conservee'})
    assert r.status_code == 200, r.text
    assert instantane(application)['lignes_facture'] == avant
    with Session(application['engine']) as db:
        assert db.get(models.Facture, fid).notes == 'Note historique conservee'
