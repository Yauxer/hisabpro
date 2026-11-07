"""Catalogue de paie : règles déclarées, aucune valeur réglementaire implicite."""
from datetime import date
from decimal import Decimal
from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator,field_serializer
from services.personnel_dossiers_service import montant_exact,RemunerationVersion

class Base(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class Regle(Base):
    traitement:Literal['A_VERIFIER','SOUMIS','EXONERE','PLAFOND_MONTANT']
    statut_reglementaire:Literal['A_VERIFIER','VALIDE','OBSOLETE']='A_VERIFIER'
    plafond:Decimal|None=None
    unite:Literal['mensuel','journalier','annuel','operation']='mensuel'
    conditions:str=Field(min_length=1,max_length=2000)
    texte_reference:str|None=Field(default=None,min_length=1,max_length=300)
    article:str|None=Field(default=None,min_length=1,max_length=150)
    url_source:str|None=Field(default=None,max_length=2000)
    empreinte_preuve:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    @field_validator('plafond',mode='before')
    @classmethod
    def exact(cls,v):return None if v is None else montant_exact(v)
    @field_serializer('plafond')
    def decimal(self,v):return None if v is None else format(v,'.2f')
    @field_validator('url_source')
    @classmethod
    def source(cls,v):
        if v is None:return v
        u=urlsplit(v)
        domaines=('finances.gov.ma','tax.gov.ma','cnss.ma','sgg.gov.ma','justice.gov.ma','acaps.ma')
        if u.scheme!='https' or u.username or u.password or u.port not in (None,443) or not any(u.hostname==d or (u.hostname or '').endswith('.'+d) for d in domaines):
            raise ValueError('Référence HTTPS sur un domaine officiel requis ;aucun téléchargement serveur automatique.')
        return v
    @model_validator(mode='after')
    def coherente(self):
        if (self.traitement=='PLAFOND_MONTANT')!=(self.plafond is not None):raise ValueError('Un plafond est requis uniquement pour le traitement plafonné.')
        if self.statut_reglementaire=='VALIDE' and (self.traitement=='A_VERIFIER' or not all([self.texte_reference,self.article,self.url_source,self.empreinte_preuve])):
            raise ValueError('Une règle validée nécessite traitement,texte,article,URL officielle et empreinte de preuve.')
        return self

class Regles(Base):
    IR:Regle
    CNSS:Regle
    AMO:Regle

class QualificationIR(Base):
    traitement:Literal['A_VERIFIER','INCLUS','EXCLUS','DEDUCTIBLE','NON_DEDUCTIBLE']='A_VERIFIER'
    statut_reglementaire:Literal['A_VERIFIER','VALIDE','OBSOLETE']='A_VERIFIER'
    conditions:str=Field(min_length=1,max_length=2000)
    source_reference:str|None=Field(default=None,min_length=1,max_length=300)
    texte_reference:str|None=Field(default=None,min_length=1,max_length=300)
    article:str|None=Field(default=None,min_length=1,max_length=150)
    url_source:str|None=Field(default=None,max_length=2000)
    empreinte_preuve:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    date_consultation:date|None=None
    @field_validator('url_source')
    @classmethod
    def source(cls,v):
        if v is not None and any(c.isspace() for c in v):raise ValueError('URL officielle sans espace requise.')
        return Regle.source(v)
    @field_validator('date_consultation',mode='before')
    @classmethod
    def date_source(cls,v):return None if v is None else RemunerationVersion.valider_date(v)
    @model_validator(mode='after')
    def qualification(self):
        if self.date_consultation and self.date_consultation>date.today():raise ValueError('Consultation future interdite.')
        if self.statut_reglementaire=='VALIDE' and (self.traitement=='A_VERIFIER' or not all([self.source_reference,self.texte_reference,self.article,self.url_source,self.empreinte_preuve,self.date_consultation])):
            raise ValueError('Traitement, conditions, référence, texte, article, URL officielle, empreinte et consultation requis pour qualifier la règle IR.')
        return self

class InclusionFrais(QualificationIR):
    traitement:Literal['A_VERIFIER','INCLUS','EXCLUS']='A_VERIFIER'

class DeductibiliteIR(QualificationIR):
    traitement:Literal['A_VERIFIER','DEDUCTIBLE','NON_DEDUCTIBLE']='A_VERIFIER'

class Contenu(Base):
    libelle:str=Field(min_length=1,max_length=150)
    nature:Literal['GAIN','RETENUE','REMBOURSEMENT']
    periodicite:Literal['mensuelle','ponctuelle','annuelle']
    formule:Literal['MONTANT','QUANTITE_TAUX']
    date_debut:date
    date_fin:date|None=None
    compte_charge:str|None=Field(default=None,pattern=r'^[0-9]{4,10}$')
    justificatifs:list[str]=Field(max_length=20)
    incompatibilites:list[str]=Field(max_length=30)
    regles:Regles
    frais_professionnels:InclusionFrais|None=None
    @field_validator('date_debut','date_fin',mode='before')
    @classmethod
    def dates(cls,v):return None if v is None else RemunerationVersion.valider_date(v)
    @field_validator('justificatifs','incompatibilites')
    @classmethod
    def liste(cls,v):
        if any(not x or len(x)>120 for x in v) or len(set(v))!=len(v):raise ValueError('Valeurs uniques non vides,120 caractères maximum.')
        return v
    @model_validator(mode='after')
    def intervalle(self):
        if self.date_fin and self.date_fin<self.date_debut:raise ValueError('Fin antérieure au début.')
        return self

class Creation(Base):
    code:str=Field(pattern=r'^[A-Z][A-Z0-9_]{1,39}$')
    contenu:Contenu
    motif:str=Field(min_length=1,max_length=500)

class Version(Base):
    version_attendue:int=Field(strict=True,ge=1)
    contenu:Contenu
    motif:str=Field(min_length=1,max_length=500)

class Decision(Base):
    motif:str=Field(min_length=1,max_length=500)
    independance_confirmee:bool=Field(strict=True)
    verification_reglementaire_confirmee:bool=Field(default=False,strict=True)
    reference_controle:str=Field(min_length=1,max_length=200)

class Apercu(Base):
    montant:Decimal
    @field_validator('montant',mode='before')
    @classmethod
    def exact(cls,v):return montant_exact(v)
