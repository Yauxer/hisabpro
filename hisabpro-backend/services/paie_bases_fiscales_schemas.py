"""Déclarations de base salariale seule ; aucune assiette fiscale de secours."""
from uuid import UUID
from decimal import Decimal
from typing import Literal
from pydantic import Field,field_validator,field_serializer
from services.paie_catalogue_schemas import Base
from services.personnel_dossiers_service import montant_exact


class Declaration(Base):
    employe_id:int=Field(strict=True,gt=0)
    base_imposable:Decimal|None=None
    base_frais:Decimal|None=None
    conditions_confirmees:bool=Field(default=False,strict=True)
    deductibilite_integrale_confirmee:bool=Field(default=False,strict=True)
    reference_controle:str|None=Field(default=None,min_length=1,max_length=300)

    @field_validator('base_imposable','base_frais',mode='before')
    @classmethod
    def montant(cls,v):return None if v is None else montant_exact(v)

    @field_serializer('base_imposable','base_frais')
    def exact(self,v):return None if v is None else format(v,'.2f')


class Simulation(Base):
    social_id:int=Field(strict=True,gt=0)
    declarations:list[Declaration]=Field(min_length=1,max_length=50)
    mode_pedagogique_confirme:Literal[True]
    cle_idempotence:UUID
    motif:str=Field(min_length=1,max_length=500)

    @field_validator('mode_pedagogique_confirme',mode='before')
    @classmethod
    def confirmer(cls,v):
        if v is not True:raise ValueError('Confirmation explicite du mode pédagogique requise.')
        return v

    @field_validator('declarations')
    @classmethod
    def uniques(cls,v):
        if len({x.employe_id for x in v})!=len(v):raise ValueError('Une déclaration par salarié requise.')
        return sorted(v,key=lambda x:x.employe_id)
