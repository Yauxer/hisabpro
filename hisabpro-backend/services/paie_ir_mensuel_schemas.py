from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import Literal
from pydantic import Field,field_validator,field_serializer,model_validator
from services.paie_catalogue_schemas import Base
from services.personnel_dossiers_service import montant_exact,RemunerationVersion

class Simulation(Base):
    preparation_id:int=Field(strict=True,gt=0)
    employe_id:int=Field(strict=True,gt=0)
    frais_professionnels_declares:Decimal|None=None
    reference_frais:str|None=Field(default=None,min_length=1,max_length=300)
    autres_deductions_declarees:Decimal|None=None
    reference_autres_deductions:str|None=Field(default=None,min_length=1,max_length=300)
    deductions_confirmees:bool=Field(default=False,strict=True)
    cadre_mensuel_general_confirme:bool=Field(default=False,strict=True)
    reference_controle_mensuel:str|None=Field(default=None,min_length=1,max_length=300)
    personnes_charge:int|None=Field(default=None,strict=True,ge=0,le=6)
    eligibilite_famille_confirmee:bool=Field(default=False,strict=True)
    reference_famille:str|None=Field(default=None,min_length=1,max_length=300)
    date_versement_declaree:date|None=None
    reference_versement:str|None=Field(default=None,min_length=1,max_length=300)
    mode_pedagogique_confirme:Literal[True]
    cle_idempotence:UUID
    motif:str=Field(min_length=1,max_length=500)
    @field_validator('frais_professionnels_declares','autres_deductions_declarees',mode='before')
    @classmethod
    def argent(cls,v):return None if v is None else montant_exact(v)
    @field_validator('date_versement_declaree',mode='before')
    @classmethod
    def date_iso(cls,v):return None if v is None else RemunerationVersion.valider_date(v)
    @field_validator('mode_pedagogique_confirme',mode='before')
    @classmethod
    def pedagogique(cls,v):
        if v is not True:raise ValueError('Mode pédagogique explicitement confirmé requis.')
        return v
    @field_serializer('frais_professionnels_declares','autres_deductions_declarees')
    def monnaie(self,v):return None if v is None else format(v,'.2f')
    @model_validator(mode='after')
    def versement(self):
        if (self.date_versement_declaree is None)!=(self.reference_versement is None):raise ValueError('Date et référence du versement déclaré requises ensemble ; sinon laisser les deux absentes.')
        return self
