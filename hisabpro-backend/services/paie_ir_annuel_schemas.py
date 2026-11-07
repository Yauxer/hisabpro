"""Contrôle arithmétique annuel ; aucune retenue mensuelle déduite d'un mois."""
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import Field,field_validator,field_serializer
from services.paie_catalogue_schemas import Base
from services.personnel_dossiers_service import montant_exact


class Simulation(Base):
    annee:Literal[2026]
    revenu_net_imposable_annuel:Decimal|None=None
    personnes_charge:int|None=Field(default=None,strict=True,ge=0,le=6)
    cadre_general_confirme:bool=Field(default=False,strict=True)
    eligibilite_famille_confirmee:bool=Field(default=False,strict=True)
    reference_rni:str|None=Field(default=None,min_length=1,max_length=300)
    reference_famille:str|None=Field(default=None,min_length=1,max_length=300)
    mode_pedagogique_confirme:Literal[True]
    cle_idempotence:UUID
    motif:str=Field(min_length=1,max_length=500)
    @field_validator('annee',mode='before')
    @classmethod
    def exercice(cls,v):
        if type(v) is not int:raise ValueError('Année entière explicite requise.')
        return v
    @field_validator('revenu_net_imposable_annuel',mode='before')
    @classmethod
    def exact(cls,v):return None if v is None else montant_exact(v)
    @field_serializer('revenu_net_imposable_annuel')
    def monnaie(self,v):return None if v is None else format(v,'.2f')
    @field_validator('mode_pedagogique_confirme',mode='before')
    @classmethod
    def confirmer(cls,v):
        if v is not True:raise ValueError('Confirmer explicitement le contrôle pédagogique.')
        return v
