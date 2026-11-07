"""Entrées exactes des variables ;aucune formule libre ni taux réglementaire."""
from datetime import date
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from typing import Literal
from pydantic import Field,field_validator,field_serializer,model_validator
from services.paie_catalogue_schemas import Base
from services.personnel_dossiers_service import montant_exact,RemunerationVersion

def decimal_six(v):
    if isinstance(v,bool) or not isinstance(v,(str,int,Decimal)):raise ValueError('Décimal exact en texte requis,sans flottant.')
    try:d=Decimal(v)
    except InvalidOperation:raise ValueError('Décimal invalide.') from None
    if not d.is_finite() or d<0 or d>=Decimal('1000000000000') or d.as_tuple().exponent < -6:raise ValueError('Valeur finie positive ou nulle,12chiffres entiers et6décimales maximum.')
    return d

class Motif(Base):
    motif:str=Field(min_length=1,max_length=500)

class RattachementRevenus(Base):
    reference_debut:date|None=None
    reference_fin:date|None=None
    reference_justification:str|None=Field(default=None,min_length=1,max_length=200)
    versement_date:date|None=None
    versement_reference:str|None=Field(default=None,min_length=1,max_length=200)
    @field_validator('reference_debut','reference_fin','versement_date',mode='before')
    @classmethod
    def dates(cls,v):return None if v is None else RemunerationVersion.valider_date(v)
    @model_validator(mode='after')
    def documente(self):
        if self.reference_debut is None:
            if self.reference_fin is not None or self.reference_justification is not None:raise ValueError('Début, fin et justification de la période de référence requis ensemble.')
        elif self.reference_fin is None or not self.reference_justification or self.reference_fin<self.reference_debut:raise ValueError('Période de référence ordonnée et justifiée requise.')
        if (self.versement_date is None)!=(self.versement_reference is None):raise ValueError('Date et référence du versement déclaré requises ensemble.')
        if self.reference_debut is None and self.versement_date is None:raise ValueError('Renseigner une période de référence ou un versement déclaré ; sinon laisser le rattachement absent.')
        return self

class Creation(Motif):
    employe_id:int=Field(strict=True,gt=0)
    rubrique_id:int=Field(strict=True,gt=0)
    periode:date
    date_effet:date
    mode:Literal['MONTANT','QUANTITE_TAUX']
    montant:Decimal|None=None
    quantite:Decimal|None=None
    taux:Decimal|None=None
    source_reference:str=Field(min_length=1,max_length=200)
    justificatifs:dict[str,str]=Field(max_length=20)
    rattachement_revenus:RattachementRevenus|None=None
    @field_validator('periode','date_effet',mode='before')
    @classmethod
    def dates(cls,v):return RemunerationVersion.valider_date(v)
    @field_validator('montant',mode='before')
    @classmethod
    def argent(cls,v):return None if v is None else montant_exact(v)
    @field_validator('quantite','taux',mode='before')
    @classmethod
    def decimaux(cls,v):return None if v is None else decimal_six(v)
    @field_validator('justificatifs')
    @classmethod
    def pieces(cls,v):
        if any(not k.strip() or len(k)>120 or not ref.strip() or len(ref)>200 for k,ref in v.items()):raise ValueError('Types et références de justificatifs non vides requis.')
        return {k.strip():ref.strip() for k,ref in v.items()}
    @model_validator(mode='after')
    def coherent(self):
        if self.periode.day!=1 or (self.date_effet.year,self.date_effet.month)!=(self.periode.year,self.periode.month):raise ValueError('Période au premier du mois et date d’effet dans ce mois requises.')
        if self.mode=='MONTANT':
            if self.montant is None or self.quantite is not None or self.taux is not None:raise ValueError('Saisir uniquement un montant pour ce mode.')
        elif self.montant is not None or self.quantite is None or self.taux is None:raise ValueError('Quantité et taux requis,sans montant forcé.')
        self.total()
        return self
    def total(self):
        return self.montant if self.mode=='MONTANT' else montant_exact((self.quantite*self.taux).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
    @field_serializer('montant')
    def argent_json(self,v):return None if v is None else format(v,'.2f')
    @field_serializer('quantite','taux')
    def decimal_json(self,v):return None if v is None else format(v,'f')

class Decision(Motif):
    independance_confirmee:bool=Field(default=False,strict=True)
    justificatifs_verifies:bool=Field(default=False,strict=True)
    reference_controle:str=Field(min_length=1,max_length=200)
