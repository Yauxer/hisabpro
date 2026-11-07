from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import Field,field_validator,field_serializer
from services.paie_catalogue_schemas import Base
from services.paie_ir_annuel_schemas import Simulation as Annuel
from services.personnel_dossiers_service import montant_exact


class Simulation(Base):
    annee:Literal[2026]
    employe_id:int=Field(strict=True,gt=0)
    preparation_ids:list[int]=Field(min_length=1,max_length=12)
    cadre_frais_general_confirme:bool=Field(default=False,strict=True)
    correspondance_revenus_annee_confirmee:bool=Field(default=False,strict=True)
    reference_controle_annuel:str|None=Field(default=None,min_length=1,max_length=300)
    autres_deductions_annuelles:Decimal|None=None
    autres_deductions_confirmees:bool=Field(default=False,strict=True)
    reference_autres_deductions:str|None=Field(default=None,min_length=1,max_length=300)
    mode_pedagogique_confirme:Literal[True]
    cle_idempotence:UUID
    motif:str=Field(min_length=1,max_length=500)

    @field_validator('annee',mode='before')
    @classmethod
    def exercice(cls,v):return Annuel.exercice(v)

    @field_validator('preparation_ids',mode='before')
    @classmethod
    def identifiants(cls,v):
        if not isinstance(v,list) or any(type(x) is not int or x<=0 for x in v) or len(set(v))!=len(v):
            raise ValueError('Identifiants entiers positifs uniques requis.')
        return sorted(v)

    @field_validator('autres_deductions_annuelles',mode='before')
    @classmethod
    def exact(cls,v):return None if v is None else montant_exact(v)

    @field_serializer('autres_deductions_annuelles')
    def monnaie(self,v):return None if v is None else format(v,'.2f')

    @field_validator('mode_pedagogique_confirme',mode='before')
    @classmethod
    def confirmer(cls,v):return Annuel.confirmer(v)
