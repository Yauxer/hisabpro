"""BC/BL : représentation finie avant mutation, API/JWT/PG nonce réels."""
from datetime import date
import pytest
from sqlalchemy.orm import Session
import models
from test_devis_stock_diagnostic import application, dossier


def ligne(q=1, prix=10, tva=20, **remises):
    return {'description': 'Ligne fictive BC/BL', 'quantite': q, 'prix_unitaire': prix, 'tva': tva, **remises}


INVALIDE = [[ligne(1e308, 10)], [ligne(1e308, 1), ligne(1e308, 1)],
            [ligne(1.6e308, 1)], [ligne(1e308, 10, remise=100)],
            [ligne(10, 1, rabais=1e308)]]


def lignes_bl(lignes):
    return [{**{k: v for k, v in l.items() if k != 'quantite'},
             'quantite_prevue': l['quantite'], 'quantite_livree': l['quantite']} for l in lignes]


def snapshot(application):
    with Session(application['engine']) as db:
        tables = (models.BonCommande, models.LigneBonCommande, models.BonLivraison,
                  models.LigneBonLivraison, models.Article, models.MouvementStock,
                  models.Ecriture, models.LigneEcriture)
        return {m.__tablename__: [tuple(getattr(o, c.name) for c in m.__table__.columns)
            for o in db.query(m).order_by(m.id).all()] for m in tables}


@pytest.mark.parametrize('type_doc', ['vente', 'achat'])
@pytest.mark.parametrize('methode', ['bc_create', 'bc_patch', 'bl_create'])
@pytest.mark.parametrize('lignes', INVALIDE)
def test_totaux_non_finis_refuses_sans_mutation(application, dossier, type_doc, methode, lignes):
    api = dossier[0]
    base = {'date': date.today().isoformat(), 'tiers': 'Tiers fictif limites', 'type': type_doc}
    if methode == 'bc_patch':
        r = api.post('/api/bons-commande', json={**base, 'lignes': [ligne()]})
        assert r.status_code == 201, r.text
        url = '/api/bons-commande/' + str(r.json()['id'])
    avant = snapshot(application)
    if methode == 'bc_create':
        r = api.post('/api/bons-commande', json={**base, 'lignes': lignes})
    elif methode == 'bc_patch':
        r = api.patch(url, json={'lignes': lignes, 'notes': 'Ne doit pas persister'})
    else:
        r = api.post('/api/bons-livraison', json={**base, 'lignes': lignes_bl(lignes)})
    lecture = (api.get('/api/bons-livraison', params={'exercice': date.today().year}).status_code
               if methode == 'bl_create' and r.status_code == 201 else None)
    assert r.status_code == 422, (r.text, 'sources_modifiees', snapshot(application) != avant, 'lecture_bl', lecture)
    assert snapshot(application) == avant


@pytest.mark.parametrize('type_doc', ['vente', 'achat'])
def test_remises_rabais_gratuit_et_quantites_physiques_reelles(dossier, type_doc):
    api = dossier[0]
    base = {'date': date.today().isoformat(), 'tiers': 'Fictif remises', 'type': type_doc}
    # 2 × 100 × 0,9 × 0,8 − 5 × 2 = 134 ; TVA26,8 ; TTC160,8.
    l = ligne(2, 100, remise=10, remise2=20, rabais=5)
    r = api.post('/api/bons-commande', json={**base, 'lignes': [l]})
    assert r.status_code == 201, r.text
    assert r.json()['total_ht'] == pytest.approx(134)
    assert r.json()['total_ttc'] == pytest.approx(160.8)
    url = '/api/bons-commande/' + str(r.json()['id'])
    p = api.patch(url, json={'lignes': [ligne(.5, 0)], 'notes': 'Gratuit'})
    assert p.status_code == 200 and p.json()['total_ttc'] == 0, p.text
    assert api.patch(url, json={'notes': 'Sans lignes', 'lignes': None}).status_code == 200
    for livree, attendu in ((0, 0), (1, 67)):
        bl = lignes_bl([l])[0]
        bl['quantite_livree'] = livree
        r = api.post('/api/bons-livraison', json={**base, 'lignes': [bl]})
        assert r.status_code == 201, r.text
        liste = api.get('/api/bons-livraison', params={'exercice': date.today().year, 'type': type_doc})
        assert liste.status_code == 200, liste.text
        item = next(x for x in liste.json() if x['id'] == r.json()['id'])
        assert item['montant_a_facturer_ht'] == pytest.approx(attendu)


def test_bornes_representatives_sans_durcir_lecture_historique():
    import schemas
    from pydantic import ValidationError
    base = {'date': date.today(), 'tiers': 'Fictif'}
    assert schemas.BonCommandeCreate(**base, lignes=[ligne(1e308, 1)]).lignes[0].quantite == 1e308
    assert schemas.BonCommandeCreate(**base, lignes=[ligne(1, 10, rabais=20)]).lignes[0].rabais == 20
    assert schemas.BonCommandeUpdate(notes='Sans lignes').lignes is None
    assert schemas.LigneBCOut(id=1, montant_ht=float('inf'), **ligne(1e308, 10)).quantite == 1e308
    assert schemas.LigneBLOut(id=1, **lignes_bl([ligne(1e308, 10)])[0]).quantite_prevue == 1e308
    for quantites in ((1e308, 0), (1, 1e308)):
        bl = lignes_bl([ligne(1, 10)])[0]
        bl['quantite_prevue'], bl['quantite_livree'] = quantites
        with pytest.raises(ValidationError):
            schemas.BonLivraisonCreate(**base, lignes=[bl])
