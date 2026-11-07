"""Paramètres sociaux déclarés et versionnés ; aucun taux légal implicite."""
from datetime import date
from decimal import Decimal
from pydantic import Field, field_validator, field_serializer, model_validator
from services.paie_catalogue_schemas import Base, Regle, Decision, DeductibiliteIR
from services.personnel_dossiers_service import montant_exact, RemunerationVersion
from services.paie_variables_schemas import decimal_six


class Contenu(Base):
    libelle: str = Field(min_length=1, max_length=150)
    organisme: str = Field(min_length=1, max_length=150)
    applicabilite: str = Field(pattern=r'^(A_VERIFIER|APPLICABLE|NON_APPLICABLE)$')
    calcul_mode: str = Field(pattern=r'^(A_QUALIFIER|TAUX|FORFAIT)$')
    assiette: str = Field(pattern=r'^(A_QUALIFIER|CNSS|AMO|BRUT)$')
    taux_salarial: Decimal | None = None
    taux_patronal: Decimal | None = None
    forfait_salarial: Decimal | None = None
    forfait_patronal: Decimal | None = None
    plafond_mode: str = Field(pattern=r'^(A_VERIFIER|SANS|MONTANT)$')
    plafond: Decimal | None = None
    unite: str = Field(pattern=r'^(mensuel|annuel|journalier)$')
    composants: list[str] = Field(max_length=30)
    conditions: str = Field(min_length=1, max_length=2000)
    date_debut: date
    date_fin: date | None = None
    source_nature: str = Field(pattern=r'^(REGLEMENTAIRE|CONTRACTUELLE)$')
    statut_reglementaire: str = Field(default='A_VERIFIER', pattern=r'^(A_VERIFIER|VALIDE|OBSOLETE)$')
    source_reference: str | None = Field(default=None, min_length=1, max_length=300)
    texte_reference: str | None = Field(default=None, min_length=1, max_length=300)
    article: str | None = Field(default=None, min_length=1, max_length=150)
    url_source: str | None = Field(default=None, max_length=2000)
    empreinte_preuve: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    date_consultation: date | None = None
    deductibilite_ir: DeductibiliteIR | None = None

    @field_validator('taux_salarial', 'taux_patronal', mode='before')
    @classmethod
    def taux(cls, v):
        if v is None: return None
        n = decimal_six(v)
        if n > 100: raise ValueError('Taux compris entre 0 et 100 pour cent.')
        return n

    @field_validator('plafond', 'forfait_salarial', 'forfait_patronal', mode='before')
    @classmethod
    def argent(cls, v): return None if v is None else montant_exact(v)

    @field_serializer('plafond', 'forfait_salarial', 'forfait_patronal')
    def monnaie(self, v): return None if v is None else format(v, '.2f')

    @field_serializer('taux_salarial', 'taux_patronal')
    def pourcentage(self, v): return None if v is None else format(v, 'f')

    @field_validator('date_debut', 'date_fin', 'date_consultation', mode='before')
    @classmethod
    def dates(cls, v): return None if v is None else RemunerationVersion.valider_date(v)

    @field_validator('url_source')
    @classmethod
    def source(cls, v):
        if v is not None and any(x.isspace() for x in v): raise ValueError('URL sans espace requise.')
        return Regle.source(v)

    @field_validator('composants')
    @classmethod
    def composition(cls, v):
        import re
        if len(v) != len(set(v)) or any(not re.fullmatch(r'[A-Z][A-Z0-9_]{1,39}', x) for x in v):
            raise ValueError('Codes de composants uniques, majuscules, de 2 à 40 caractères.')
        return v

    @model_validator(mode='after')
    def coherente(self):
        if self.date_fin and self.date_fin < self.date_debut: raise ValueError('Fin antérieure au début.')
        if self.date_consultation and self.date_consultation > date.today(): raise ValueError('Consultation future interdite.')
        if (self.plafond_mode == 'MONTANT') != (self.plafond is not None): raise ValueError('Montant requis uniquement pour un plafond en montant.')
        if self.plafond is not None and self.plafond <= 0: raise ValueError('Plafond strictement positif requis.')
        if self.calcul_mode != 'TAUX' and any(x is not None for x in [self.taux_salarial, self.taux_patronal]): raise ValueError('Taux réservés au mode taux.')
        if self.calcul_mode != 'FORFAIT' and any(x is not None for x in [self.forfait_salarial, self.forfait_patronal]): raise ValueError('Forfaits réservés au mode forfait.')
        if self.calcul_mode == 'FORFAIT' and (self.assiette != 'A_QUALIFIER' or self.plafond_mode != 'SANS'): raise ValueError('Un forfait ne combine ni assiette ni plafond.')
        if self.applicabilite == 'NON_APPLICABLE' and any(x is not None for x in [self.taux_salarial, self.taux_patronal, self.forfait_salarial, self.forfait_patronal, self.plafond]):
            raise ValueError('Une branche non applicable ne porte aucun taux, forfait ou plafond.')
        if self.applicabilite == 'APPLICABLE' and not self.composants: raise ValueError('Déclarer les composants couverts pour prévenir le double comptage.')
        if self.statut_reglementaire == 'VALIDE':
            if not all([self.source_reference, self.texte_reference, self.empreinte_preuve, self.date_consultation]): raise ValueError('Référence, texte, empreinte et date de consultation requis.')
            if self.source_nature == 'REGLEMENTAIRE' and not all([self.article, self.url_source]): raise ValueError('Article et source officielle requis.')
            if self.applicabilite == 'A_VERIFIER': raise ValueError('Applicabilité à qualifier.')
            if self.applicabilite == 'APPLICABLE':
                if self.calcul_mode == 'TAUX' and (self.assiette == 'A_QUALIFIER' or self.plafond_mode == 'A_VERIFIER' or self.taux_salarial is None or self.taux_patronal is None): raise ValueError('Assiette, plafond et deux taux explicites requis.')
                if self.calcul_mode == 'FORFAIT' and (self.forfait_salarial is None or self.forfait_patronal is None): raise ValueError('Deux forfaits explicites requis.')
                if self.calcul_mode == 'A_QUALIFIER': raise ValueError('Mode de calcul à qualifier.')
        return self


class Creation(Base):
    code: str = Field(pattern=r'^[A-Z][A-Z0-9_]{1,39}$')
    regime: str = Field(pattern=r'^[A-Z][A-Z0-9_]{1,79}$')
    contenu: Contenu
    motif: str = Field(min_length=1, max_length=500)


class Version(Base):
    version_attendue: int = Field(strict=True, ge=1)
    contenu: Contenu
    motif: str = Field(min_length=1, max_length=500)
