"""Même contenu FEC quand PostgreSQL charge les lignes dans un ordre différent."""
from itertools import permutations

import pytest
from services.fec_service import lignes_fec
from test_patch053_comptabilite_auxiliaire_fec_avis24 import _ligne, _ecriture


@pytest.mark.parametrize('ordre',list(permutations(range(3))))
def test_fec_trie_les_lignes_persistantes_par_id_sans_mutation(ordre):
    lignes=[_ligne('7111',credit=100,id=10),_ligne('3421',debit=120,id=20),
            _ligne('4455',credit=20,id=30)]
    entree=[lignes[i] for i in ordre]
    ecriture=_ecriture(entree)
    avant=[dict(l.__dict__) for l in entree]
    rows=list(lignes_fec([ecriture],2027))
    assert [r[4] for r in rows]==['7111','3421','4455']
    assert all(len(r)==18 for r in rows)
    assert ecriture.lignes==entree and [dict(l.__dict__) for l in entree]==avant


def test_fec_objets_sans_id_gardent_leur_ordre_de_fonction_pure():
    ec=_ecriture([_ligne('5141',debit=100),_ligne('1111',credit=100)])
    assert [r[4] for r in lignes_fec([ec],2027)]==['5141','1111']
