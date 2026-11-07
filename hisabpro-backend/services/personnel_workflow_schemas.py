"""Contrats API Personnel ;aucun paramètre comptable ni donnée bancaire."""
from datetime import date
from typing import Annotated,Literal,Union
from pydantic import BaseModel,ConfigDict,Field,StringConstraints,field_validator,model_validator,EmailStr,SecretStr
from services.personnel_dossiers_service import RemunerationVersion,normaliser_matricule

class Base(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class Motif(Base):
    motif: str=Field(min_length=1,max_length=500)

class DonneesPersonnelles(Base):
    date_embauche: date|None=None
    email: EmailStr|None=None
    telephone: str|None=Field(default=None,max_length=50)
    numero_cnss: str|None=Field(default=None,max_length=50)
    situation_familiale: Literal['celiba','marie','veuf','divorce']|None=None
    nb_enfants: int|None=Field(default=None,ge=0,le=2147483647,strict=True)
    # Même borne technique que la colonne080 existante ;aucun calcul IR ici.
    personnes_charge_ir: int|None=Field(default=None,ge=0,le=6,strict=True)

    @field_validator('date_embauche',mode='before')
    @classmethod
    def date_connue(cls,v):
        return None if v is None else RemunerationVersion.valider_date(v)

class Beneficiaire(Base):
    utilisateur_beneficiaire_id: int|None=Field(default=None,gt=0,strict=True)
    beneficiaire_sans_compte_confirme: bool=Field(default=False,strict=True)
    reference_beneficiaire: str=Field(min_length=1,max_length=200)

    @model_validator(mode='after')
    def lien_explicite(self):
        if (self.utilisateur_beneficiaire_id is not None)==self.beneficiaire_sans_compte_confirme:
            raise ValueError('Indiquer un utilisateur bénéficiaire OU attester explicitement son absence de compte.')
        return self

class Creation(Beneficiaire,Motif,DonneesPersonnelles):
    matricule: Annotated[str,StringConstraints(strip_whitespace=False,min_length=1,max_length=50)]
    nom: str=Field(min_length=1,max_length=150)
    poste: str|None=Field(default=None,max_length=150)

    @field_validator('matricule',mode='before')
    @classmethod
    def matricule_texte(cls,v):
        v=normaliser_matricule(v)
        if v is None:raise ValueError('Matricule textuel requis.')
        return v

class Reprise(Beneficiaire,Motif):
    employe_id: int=Field(gt=0,strict=True)

class Revision(Motif):
    revision_attendue: int=Field(ge=0,strict=True)

class Identite(DonneesPersonnelles):
    nom: str=Field(min_length=1,max_length=150)
    poste: str|None=Field(default=None,max_length=150)

class Contrat(Base):
    regime_amo: str|None=Field(default=None,min_length=1,max_length=120)
    regime_retraite: str|None=Field(default=None,min_length=1,max_length=120)
    regime_mutuelle: str|None=Field(default=None,min_length=1,max_length=120)
    date_effet: date
    type_contrat: str=Field(min_length=1,max_length=40)
    date_debut: date
    date_fin: date|None=None
    reference_justificatif: str=Field(min_length=1,max_length=200)
    @field_validator('date_effet','date_debut','date_fin',mode='before')
    @classmethod
    def date_exacte(cls,v):
        return None if v is None else RemunerationVersion.valider_date(v)

    @model_validator(mode='after')
    def dates(self):
        if self.date_effet<self.date_debut or self.date_fin and (self.date_fin<self.date_debut or self.date_effet>self.date_fin):
            raise ValueError('Dates du contrat incohérentes.')
        return self

class Salaire(RemunerationVersion):
    contrat_version_id: int=Field(gt=0,strict=True)

class Sortie(Base):
    date_sortie: date
    reference_justificatif: str=Field(min_length=1,max_length=200)
    @field_validator('date_sortie',mode='before')
    @classmethod
    def date_exacte(cls,v):
        return RemunerationVersion.valider_date(v)

class DemandeIdentite(Revision):
    nature: Literal['DOSSIER']
    contenu: Identite

class DemandeContrat(Revision):
    nature: Literal['CONTRAT']
    contenu: Contrat

class DemandeSalaire(Revision):
    nature: Literal['REMUNERATION']
    contenu: Salaire

class DemandeSortie(Revision):
    nature: Literal['SORTIE']
    contenu: Sortie

class Banque(Base):
    date_effet:date
    rib_iban:SecretStr
    banque:str|None=Field(default=None,max_length=120)
    titulaire:str|None=Field(default=None,max_length=150)
    piece_id:int|None=Field(default=None,gt=0,strict=True)
    reference_justificatif:str=Field(min_length=1,max_length=200)

    @field_validator('date_effet',mode='before')
    @classmethod
    def date_bancaire(cls,v):return RemunerationVersion.valider_date(v)

    @field_validator('rib_iban',mode='before')
    @classmethod
    def identifiant_atteste(cls,v):
        if not isinstance(v,str) or not 1<=len(v.strip())<=120 or any(ord(c)<32 or ord(c)==127 or c in '*•' for c in v):
            raise ValueError('Coordonnées attestées requises,en texte borné,sans caractères de contrôle ni valeur masquée.')
        return v.strip()

class DemandeBanque(Revision):
    nature:Literal['BANQUE']
    contenu:Banque

Proposition=Annotated[Union[DemandeIdentite,DemandeContrat,DemandeSalaire,DemandeSortie,DemandeBanque],Field(discriminator='nature')]

class Decision(Revision):
    verification_bancaire_confirmee:bool=Field(default=False,strict=True)
    independance_confirmee: Literal[True]
    reference_independance: str=Field(min_length=1,max_length=200)

    @field_validator('independance_confirmee',mode='before')
    @classmethod
    def confirmation_explicite(cls,v):
        if type(v) is not bool or not v:raise ValueError('Confirmer explicitement l’indépendance de la décision.')
        return v
