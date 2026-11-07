"""Totaux calculés de devis : rejets avant mutation, API/PG nonce réel."""
from datetime import date
import math
import pytest
from test_devis_stock_diagnostic import application, dossier, etat


def ligne(q=1, prix=10, tva=20, qualification='taxable'):
    return {'description': 'Ligne fictive limites', 'quantite': q, 'prix_unitaire': prix,
            'tva': tva, 'qualification_tva': qualification}


INVALIDE = [
    [ligne(1e308, 10)],
    [ligne(1e308, 1e308)],
    [ligne(1e308, 1, 20), ligne(1e308, 1, 20)],
    [ligne(1.6e308, 1, 20)],
    [ligne(1.7e308, 1, 10)],
]


@pytest.mark.parametrize('lignes', INVALIDE)
@pytest.mark.parametrize('methode', ['creation', 'modification'])
def test_totaux_non_finis_refuses_avant_mutation(application, dossier, lignes, methode):
    api, sid, article, service, ids = dossier
    if methode == 'modification':
        r = api.post('/api/devis', json={'date': date.today().isoformat(), 'tiers': 'Client fictif limites',
                                       'lignes': [ligne()]})
        assert r.status_code == 201, r.text
        url = '/api/devis/' + str(r.json()['id'])
    avant = etat(application)
    if methode == 'creation':
        r = api.post('/api/devis', json={'date': date.today().isoformat(), 'tiers': 'Client fictif limites',
                                       'lignes': lignes})
    else:
        r = api.patch(url, json={'notes': 'Ne doit pas persister', 'lignes': lignes})
    assert r.status_code == 422, (r.text, 'sources_modifiees', etat(application) != avant)
    assert etat(application) == avant


@pytest.mark.parametrize('lignes,ht,tva,ttc', [
    ([ligne(.5, 10)], 5, 1, 6),
    ([ligne(1e308, 1, 20)], 1e308, 2e307, 1.2e308),
    ([ligne(1, 0, 20)], 0, 0, 0),
])
def test_totaux_finis_creation_patch_et_notes_restent_possibles(dossier, lignes, ht, tva, ttc):
    api, sid, article, service, ids = dossier
    r = api.post('/api/devis', json={'date': date.today().isoformat(), 'tiers': 'Client fictif limites', 'lignes': lignes})
    assert r.status_code == 201, r.text
    d = r.json()
    assert d['total_ht'] == pytest.approx(ht) and d['total_tva'] == pytest.approx(tva)
    assert d['total_ttc'] == pytest.approx(ttc) and math.isfinite(d['total_ttc'])
    p = api.patch('/api/devis/' + str(d['id']), json={'lignes': lignes})
    assert p.status_code == 200, p.text
    p = api.patch('/api/devis/' + str(d['id']), json={'notes': 'Note indépendante'})
    assert p.status_code == 200 and p.json()['notes'] == 'Note indépendante', p.text


def test_validation_uniquement_requetes_pas_lecture_historique():
    import schemas
    historique = schemas.LigneDevisOut(id=1, **ligne(1e308, 10),
        montant_ht=math.inf, montant_tva=math.inf, montant_ttc=math.inf)
    assert historique.quantite == 1e308
    assert schemas.DevisUpdate(notes='Note sans lignes').lignes is None
    assert schemas.DevisUpdate(lignes=None).lignes is None


def test_qualification_non_taxable_conserve_le_taux_effectif_nul():
    import schemas
    from pydantic import ValidationError
    payload = {'date': date.today(), 'tiers': 'Fictif',
               'lignes': [ligne(1.6e308, 1, 20, 'exonere')]}
    assert schemas.DevisCreate(**payload).lignes[0].qualification_tva == 'exonere'
    assert schemas.DevisUpdate(lignes=payload['lignes']).lignes[0].quantite == 1.6e308
    payload['lignes'][0]['qualification_tva'] = 'taxable'
    with pytest.raises(ValidationError):
        schemas.DevisCreate(**payload)
