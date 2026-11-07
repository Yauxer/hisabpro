from datetime import date
from typing import Annotated,Literal
from uuid import UUID
from pydantic import Field,field_validator
from services.paie_catalogue_schemas import Base
from services.personnel_dossiers_service import RemunerationVersion

class Simulation(Base):
    periode:date
    type_campagne:Literal['NORMALE']='NORMALE'
    employe_ids:list[Annotated[int,Field(strict=True,gt=0)]]=Field(min_length=1,max_length=50)
    mois_complets_confirmes:Literal[True]
    cle_idempotence:UUID
    motif:str=Field(min_length=1,max_length=500)
    @field_validator('periode',mode='before')
    @classmethod
    def mois(cls,v):return RemunerationVersion.valider_date(v)
    @field_validator('mois_complets_confirmes',mode='before')
    @classmethod
    def confirme(cls,v):
        if v is not True:raise ValueError('Confirmation explicite de mois complets requise.')
        return v
    @field_validator('periode')
    @classmethod
    def premier(cls,v):
        if v.day!=1:raise ValueError('Période au premier du mois requise.')
        return v
    @field_validator('employe_ids')
    @classmethod
    def uniques(cls,v):
        if len(v)!=len(set(v)):raise ValueError('Chaque salarié ne doit apparaître qu’une fois.')
        return sorted(v)
