"""Dates de demandes et transitions de droits, sans solde légal calculé."""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from routers.grh import DemandeAbsence,DecisionAbsence,transition_absence


@pytest.mark.parametrize('source,cible', [('demande','approuve'),('demande','refuse'),('demande','annule'),('approuve','annule')])
def test_admin_transitions_autorisees(source,cible):
    transition_absence(source,cible,'admin',1,2)


@pytest.mark.parametrize('source,cible', [('refuse','approuve'),('annule','approuve'),('approuve','refuse'),('approuve','approuve'),('refuse','annule'),('annule','annule')])
def test_transition_deja_traitee_refusee(source,cible):
    with pytest.raises(HTTPException) as error:
        transition_absence(source,cible,'admin',1,2)
    assert error.value.status_code == 409


@pytest.mark.parametrize('cible',['approuve','refuse'])
def test_comptable_ne_decide_pas_meme_auteur(cible):
    with pytest.raises(HTTPException) as error:
        transition_absence('demande',cible,'comptable',1,1)
    assert error.value.status_code == 403


def test_annulation_seul_auteur_ou_admin():
    transition_absence('demande','annule','comptable',1,1)
    with pytest.raises(HTTPException) as error:
        transition_absence('demande','annule','comptable',1,2)
    assert error.value.status_code == 403


@pytest.mark.parametrize('valeurs', [
    {'employe_id':True},{'employe_id':1.5},{'employe_id':0},
    {'date_fin':'2026-01-01','date_debut':'2026-01-02'},
    {'type_absence':'maladie-exoneree-inventee'},{'motif':'x'*1001},
])
def test_demande_invalide_refusee(valeurs):
    with pytest.raises(ValidationError):
        DemandeAbsence(**{'employe_id':1,'date_debut':'2026-01-01','date_fin':'2026-01-03',**valeurs})


def test_un_jour_et_motif_facultatif():
    assert DemandeAbsence(employe_id=1,date_debut='2026-01-01',date_fin='2026-01-01').motif is None
    with pytest.raises(ValidationError):
        DecisionAbsence(statut='demande')
