from uuid import UUID
from pydantic import Field,field_validator
from typing import Literal
from services.paie_catalogue_schemas import Base
from services.paie_ir_annuel_schemas import Simulation as Annuel


class Creation(Base):
    frais_annuels_id:int=Field(strict=True,gt=0)
    source_annuelle_confirmee:bool=Field(default=False,strict=True)
    cadre_general_confirme:bool=Field(default=False,strict=True)
    personnes_charge:int|None=Field(default=None,strict=True,ge=0,le=6)
    eligibilite_famille_confirmee:bool=Field(default=False,strict=True)
    reference_famille:str|None=Field(default=None,min_length=1,max_length=300)
    mode_pedagogique_confirme:Literal[True]
    cle_idempotence:UUID
    motif:str=Field(min_length=1,max_length=500)

    @field_validator('mode_pedagogique_confirme',mode='before')
    @classmethod
    def confirmer(cls,v):return Annuel.confirmer(v)
