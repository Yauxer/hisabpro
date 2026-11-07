from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List, Literal
from datetime import date, datetime
DateType = date
ModeReglement = Literal["virement", "cheque", "especes", "effet", "carte", "prelevement", "autre"]
from enum import Enum
from decimal import Decimal
from decimal import InvalidOperation
from uuid import UUID
import math


def _nombre_fini(v):
    if isinstance(v, bool):
        raise ValueError("Une valeur numérique ne peut pas être un booléen")
    try:
        nombre = float(v)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Une valeur numérique est requise") from exc
    if not math.isfinite(nombre):
        raise ValueError("La valeur numérique doit être finie")
    return v


def _taux_ras_fini(v):
    _nombre_fini(v)
    if not 0 <= float(v) <= 100:
        raise ValueError("Le taux RAS doit être un pourcentage compris entre 0 et 100")
    return v


# ── Énumérations ──────────────────────────────────────────────────────────────

class JournalEnum(str, Enum):
    # Standards
    AC = "AC"
    VT = "VT"
    BQ = "BQ"
    CA = "CA"
    OD = "OD"
    # Spéciaux
    AN = "AN"
    EN = "EN"
    AE = "AE"
    AV = "AV"
    AM = "AM"
    TV = "TV"
    PR = "PR"
    SA = "SA"

class TypeFactureEnum(str, Enum):
    achat = "achat"
    vente = "vente"

class StatutFactureEnum(str, Enum):
    en_attente          = "en_attente"
    payee               = "payee"
    partiellement_payee = "partiellement_payee"
    retard              = "retard"
    annulee             = "annulee"


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    str
    password: str

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    # Rôle courant renvoyé dès l’authentification pour que l’interface
    # applique immédiatement les droits (admin | comptable | lecture).
    role:         str

class UtilisateurCreate(BaseModel):
    nom:       str
    email:     str
    password:  str
    role:      str = "comptable"

class UtilisateurOut(BaseModel):
    id:         int
    nom:        str
    email:      str
    role:       str
    societe_id: int

    class Config:
        from_attributes = True


# ── Société ───────────────────────────────────────────────────────────────────

class SocieteCreate(BaseModel):
    raison_sociale:     str
    identifiant_fiscal: Optional[str] = None
    ice:                Optional[str] = None
    rc:                 Optional[str] = None
    adresse:            Optional[str] = None
    ville:              Optional[str] = None
    telephone:          Optional[str] = None
    email:              Optional[str] = None

class SocieteOut(SocieteCreate):
    id:         int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Écritures ─────────────────────────────────────────────────────────────────

class LigneEcritureCreate(BaseModel):
    compte:  str
    libelle: Optional[str] = ""
    debit:   float = 0.0
    credit:  float = 0.0
    # COMPTA-AUX : sélection explicite du tiers sur une ligne collective.
    tiers_id: Optional[int] = None

    @field_validator("debit", "credit", mode="before")
    @classmethod
    def montant_numerique(cls, v):
        if isinstance(v, bool):
            raise ValueError("Débit et crédit doivent être des montants, pas des booléens")
        return v

    @field_validator("debit", "credit")
    @classmethod
    def montant_fini(cls, v):
        if not math.isfinite(v):
            raise ValueError("Débit et crédit doivent être des montants finis")
        return v

    @field_validator("compte")
    @classmethod
    def compte_valide(cls, v):
        if not v.isdigit() or len(v) < 3:
            raise ValueError("Numéro de compte invalide")
        return v

    @model_validator(mode="after")
    def sens_comptable_valide(self):
        """Une ligne est soit au débit, soit au crédit, jamais les deux."""
        debit = float(self.debit or 0)
        credit = float(self.credit or 0)
        if debit < 0 or credit < 0:
            raise ValueError("Débit et crédit doivent être positifs ou nuls")
        if debit > 0 and credit > 0:
            raise ValueError("Une ligne ne peut pas être simultanément au débit et au crédit")
        if debit == 0 and credit == 0:
            raise ValueError("Une ligne comptable doit porter un montant au débit ou au crédit")
        return self

class LigneEcritureOut(LigneEcritureCreate):
    id:             int
    confidence:     Optional[float] = None
    nature_auxiliaire: Optional[str] = None
    compte_auxiliaire_snapshot: Optional[str] = None
    libelle_auxiliaire_snapshot: Optional[str] = None
    code_lettrage: Optional[str] = None
    date_lettrage: Optional[datetime] = None

    class Config:
        from_attributes = True

class EcritureUpdate(BaseModel):
    journal:    Optional[str]               = None
    date:       Optional[str]               = None
    date_piece: Optional[str]               = None
    libelle:    Optional[str]               = None
    reference:  Optional[str]               = None
    lignes:     Optional[List[LigneEcritureCreate]] = None


class EcritureCreate(BaseModel):
    date:       date
    date_piece: Optional[date] = None
    journal:    JournalEnum
    libelle:    str
    # Référence du justificatif externe. Le numéro interne de l'écriture
    # est attribué automatiquement en base et n'est jamais fourni par le client.
    reference:  Optional[str] = None
    # Valider dès la création : l'écriture devient définitive immédiatement
    est_validee: bool = False
    lignes:     List[LigneEcritureCreate]

    @field_validator("lignes")
    @classmethod
    def equilibre(cls, lignes):
        total_debit  = sum(l.debit  for l in lignes)
        total_credit = sum(l.credit for l in lignes)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Écriture non équilibrée : débit={total_debit}, crédit={total_credit}")
        return lignes

class EcritureOut(BaseModel):
    id:               int
    numero_ecriture:  Optional[str] = None
    date:             date
    date_piece:       Optional[date] = None
    journal:          str
    libelle:          str
    reference:        Optional[str]
    # COMPTA.4 : référence/date effectivement utilisées par le FEC. Elles
    # peuvent provenir d'un complément documentaire append-only sans modifier
    # l'écriture définitive.
    reference_fec:    Optional[str] = None
    date_piece_fec:   Optional[date] = None
    nb_justificatifs: int = 0
    exercice:         int
    source:           str
    est_validee:      bool = False
    date_validation:  Optional[datetime] = None
    validee_par:      Optional[int] = None
    contrepassation_de_id: Optional[int] = None
    motif_correction: Optional[str] = None
    lignes:           List[LigneEcritureOut]
    created_at:       datetime

    class Config:
        from_attributes = True


# ── Factures ──────────────────────────────────────────────────────────────────
class LigneFactureCreate(BaseModel):
    article_id:    Optional[int] = None
    source_ligne_devis_id: Optional[int] = None
    source_ligne_bc_id: Optional[int] = None
    source_ligne_bl_id: Optional[int] = None
    description:   str
    quantite:      float = 1.0
    prix_unitaire: float
    tva:           float = 20.0
    qualification_tva: str = "taxable"
    remise:        float = 0.0   # remise 1 en %
    remise2:       float = 0.0   # remise 2 en %, en cascade sur le net après remise 1
    rabais:        float = 0.0   # rabais exceptionnel, montant par unité

    @field_validator("quantite", "prix_unitaire", "tva", "remise", "remise2", "rabais", mode="before")
    @classmethod
    def nombres_finis(cls, v):
        return _nombre_fini(v)

    @field_validator("description")
    @classmethod
    def description_obligatoire(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("La description de ligne est obligatoire")
        return v

    @field_validator("quantite")
    @classmethod
    def quantite_positive(cls, v):
        if v <= 0:
            raise ValueError("La quantité doit être strictement positive")
        return v

    @field_validator("prix_unitaire", "rabais")
    @classmethod
    def montants_non_negatifs(cls, v):
        if v < 0:
            raise ValueError("Les montants ne peuvent pas être négatifs")
        return v

    @field_validator("tva", "remise", "remise2")
    @classmethod
    def pourcentages_valides(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Le pourcentage doit être compris entre 0 et 100")
        return v

class LigneFactureOut(LigneFactureCreate):
    id:           int
    montant_ht:   float
    montant_tva:  float
    montant_ttc:  float

    class Config:
        from_attributes = True

class EcheanceFactureCreate(BaseModel):
    date_echeance: date
    montant: float
    libelle: Optional[str] = None


class EcheanceFactureOut(EcheanceFactureCreate):
    id: Optional[int] = None
    ordre: int

    class Config:
        from_attributes = True


class FactureCreate(BaseModel):
    numero:         Optional[str] = None
    type:           TypeFactureEnum
    date:           date
    tiers:          str
    tiers_id:       Optional[int] = None
    reference:      Optional[str] = None
    statut:         StatutFactureEnum = StatutFactureEnum.en_attente
    notes:          Optional[str] = None
    delai_paiement: Optional[int] = 60
    date_echeance:  Optional[date] = None
    mode_reglement_prevu: Optional[ModeReglement] = None
    reference_reglement_prevue: Optional[str] = None
    echeances:       Optional[List[EcheanceFactureCreate]] = None
    remise_globale: float           = 0.0
    ristourne:      float           = 0.0   # ristourne en % (volume d'affaires), pied de facture
    escompte:       float           = 0.0
    # Frais accessoires facturés
    frais_transport_ht:  float      = 0.0
    frais_transport_tva: float      = 20.0
    frais_transport_mode: str       = "accessoire"
    frais_transport_qualification_tva: str = "taxable"
    frais_emballage_ht:  float      = 0.0
    frais_emballage_tva: float      = 20.0
    frais_emballage_mode: str       = "perdu"
    frais_emballage_qualification_tva: str = "taxable"
    # Retenue à la source (0, 5, 10, 15, 20 %)
    ras_taux:       float           = 0.0
    # TVA achats : qualification explicite pour la déclaration (Patch 02B)
    nature_tva_achat: str           = "charge"  # charge | immobilisation | non_deductible
    tva_deductible_pct: float       = 100.0
    # Facture proforma : aucun effet stock ni comptable
    est_proforma:   bool            = False
    lignes:         List[LigneFactureCreate]

    @field_validator("ras_taux", mode="before")
    @classmethod
    def ras_taux_valide(cls, v):
        return _taux_ras_fini(v)

    @field_validator("delai_paiement")
    @classmethod
    def delai_paiement_valide(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("Le délai de paiement ne peut pas être négatif")
        if v > 365:
            raise ValueError("Le délai de paiement ne peut pas dépasser 365 jours")
        return v

    @model_validator(mode="after")
    def echeance_coherente(self):
        if self.date_echeance and self.date_echeance < self.date:
            raise ValueError("L'échéance ne peut pas précéder la date de facture")
        return self

# ── Avoir ────────────────────────────────────────────────────────────────────

class LigneAvoirCreate(BaseModel):
    # FACT.6 : facture_ligne_id est la source de vérité. Les champs tarifaires
    # restent optionnels uniquement pour compatibilité avec d'anciens clients API ;
    # le backend les remplace systématiquement par les snapshots de la facture.
    facture_ligne_id: Optional[int] = None
    article_id:       Optional[int] = None
    description:      Optional[str] = None
    quantite:         float = 1.0
    prix_unitaire:    Optional[float] = None
    tva:              Optional[float] = None
    qualification_tva: Optional[str] = None
    remise:           Optional[float] = None
    remise2:          Optional[float] = None
    rabais:           Optional[float] = None
    # FACT-G : vrais RRR/corrections de prix. Les champs sont contrôlés et
    # recalculés côté backend à partir de la facture source.
    mode_calcul:       Optional[str] = None
    taux_rrr:          Optional[float] = None
    montant_ht_avoir:  Optional[float] = None
    nouveau_prix_unitaire: Optional[float] = None

class LigneAvoirOut(LigneAvoirCreate):
    id:           int
    montant_ht_force: Optional[float] = None
    montant_ht:   float
    montant_tva:  float
    montant_ttc:  float

    class Config:
        from_attributes = True

class AvoirCreate(BaseModel):
    facture_id: int
    date:       date
    motif:      Optional[str] = None
    notes:      Optional[str] = None
    retour_stock: bool = False
    nature_avoir: str = "retour_annulation"
    lignes:     List[LigneAvoirCreate]

class AvoirUpdate(BaseModel):
    statut: Optional[str] = None
    motif:  Optional[str] = None
    notes:  Optional[str] = None

class UtilisationAvoirOut(BaseModel):
    id: int
    type_utilisation: str
    facture_id: Optional[int] = None
    facture_numero: Optional[str] = None
    date_utilisation: date
    date_acceptation_compensation: Optional[date] = None
    date_annulation_effective: Optional[date] = None
    montant: float
    mode: Optional[str] = None
    banque: Optional[str] = None
    reference: Optional[str] = None
    statut: str = "active"
    est_comptabilisee: bool = False


class AvoirOut(BaseModel):
    id:                int
    numero:            str
    type:              str
    date:              date
    exercice:          int
    tiers:             str
    tiers_id:          Optional[int] = None
    facture_id:        int
    facture_numero:    Optional[str] = None
    motif:             Optional[str]
    statut:            str
    notes:             Optional[str]
    est_comptabilisee: Optional[bool] = False
    retour_stock:      Optional[bool] = False
    nature_avoir:       str = "retour_annulation"
    date_annulation:   Optional[datetime] = None
    ecriture_annulation_id: Optional[int] = None
    credit_excedentaire: float = 0.0
    montant_utilise: float = 0.0
    montant_disponible: float = 0.0
    utilisations: List[UtilisationAvoirOut] = []
    total_ht:          float
    total_tva:         float
    total_ttc:         float
    lignes:            List[LigneAvoirOut]
    created_at:        datetime

    class Config:
        from_attributes = True


class FactureOut(BaseModel):
    id:                int
    numero:            Optional[str] = None
    type:              str
    date:              date
    exercice:          int
    tiers:             str
    tiers_id:          Optional[int] = None
    tiers_ice_snapshot: Optional[str] = None
    tiers_if_snapshot: Optional[str] = None
    tiers_rc_snapshot: Optional[str] = None
    tiers_adresse_snapshot: Optional[str] = None
    tiers_ville_snapshot: Optional[str] = None
    reference:         Optional[str]
    statut:            str
    delai_paiement:    Optional[int] = 60
    date_echeance:    Optional[date] = None
    mode_reglement_prevu: Optional[str] = None
    reference_reglement_prevue: Optional[str] = None
    alerte_delai_paiement: Optional[str] = None
    total_encaisse: float = 0.0
    total_reglement_en_cours: float = 0.0
    echeances:         List[EcheanceFactureOut] = []
    est_validee:      Optional[bool] = False
    date_validation:  Optional[datetime] = None
    validee_par:      Optional[int] = None
    est_comptabilisee: Optional[bool] = False
    est_proforma:     Optional[bool] = False
    regime_tva:      Optional[str] = "encaissement"
    qualification_tva: Optional[str] = "taxable"
    nature_tva_achat: Optional[str] = "charge"
    tva_deductible_pct: Optional[float] = 100.0
    remise_globale:    Optional[float] = 0.0
    ristourne:         Optional[float] = 0.0
    escompte:          Optional[float] = 0.0
    frais_transport_ht: Optional[float] = 0.0
    frais_transport_tva: Optional[float] = 20.0
    frais_transport_mode: Optional[str] = "accessoire"
    frais_transport_qualification_tva: Optional[str] = "taxable"
    frais_emballage_ht: Optional[float] = 0.0
    frais_emballage_tva: Optional[float] = 20.0
    frais_emballage_mode: Optional[str] = "perdu"
    frais_emballage_qualification_tva: Optional[str] = "taxable"
    total_ht:          float
    total_tva:         float
    total_ttc:         float
    ras_taux:          Optional[float] = None
    montant_ras:       Optional[float] = None
    net_a_payer:       Optional[float] = None
    ras_anomalie:      Optional[str] = None
    total_avoirs:      float = 0.0
    statut_credit:     str = "aucun"
    lignes:            List[LigneFactureOut]
    created_at:        Optional[datetime]

    class Config:
        from_attributes = True

class LigneFactureLectureOut(BaseModel):
    """Lecture historique distincte des règles strictes de saisie."""
    id: int
    article_id: Optional[int] = None
    source_ligne_devis_id: Optional[int] = None
    source_ligne_bc_id: Optional[int] = None
    source_ligne_bl_id: Optional[int] = None
    description: str
    quantite: Optional[float] = None
    prix_unitaire: Optional[float] = None
    tva: Optional[float] = None
    qualification_tva: Optional[str] = None
    remise: Optional[float] = None
    remise2: Optional[float] = None
    rabais: Optional[float] = None
    montant_ht: Optional[float] = None
    montant_tva: Optional[float] = None
    montant_ttc: Optional[float] = None


class EcheanceFactureLectureOut(EcheanceFactureOut):
    montant: Optional[float] = None


class FactureLectureOut(FactureOut):
    # Lecture calculée : prochaine échéance encore ouverte, sans changer le contrat.
    date_prochaine_echeance: Optional[DateType] = None
    total_ht: Optional[float] = None
    total_tva: Optional[float] = None
    total_ttc: Optional[float] = None
    total_encaisse: Optional[float] = None
    total_reglement_en_cours: Optional[float] = None
    total_avoirs: Optional[float] = None
    statut_credit: Optional[str] = None
    lignes: List[LigneFactureLectureOut]
    echeances: List[EcheanceFactureLectureOut] = []
    montants_valides: bool = True
    anomalies_montants: List[str] = []


class FactureUpdate(BaseModel):
    numero:         Optional[str] = None
    type:           Optional[TypeFactureEnum] = None
    # Date en chaîne : Pydantic v2 ne coerce pas automatiquement vers Optional[date]
    date:           Optional[str] = None
    tiers:          Optional[str] = None
    tiers_id:       Optional[int] = None
    reference:      Optional[str] = None
    statut:         Optional[StatutFactureEnum] = None
    notes:          Optional[str] = None
    delai_paiement: Optional[int] = None
    date_echeance:  Optional[str] = None
    mode_reglement_prevu: Optional[ModeReglement] = None
    reference_reglement_prevue: Optional[str] = None
    echeances:       Optional[List[EcheanceFactureCreate]] = None
    remise_globale: Optional[float] = None
    ristourne:      Optional[float] = None
    escompte:       Optional[float] = None
    frais_transport_ht:  Optional[float] = None
    frais_transport_tva: Optional[float] = None
    frais_transport_mode: Optional[str] = None
    frais_transport_qualification_tva: Optional[str] = None
    frais_emballage_ht:  Optional[float] = None
    frais_emballage_tva: Optional[float] = None
    frais_emballage_mode: Optional[str] = None
    frais_emballage_qualification_tva: Optional[str] = None
    ras_taux:       Optional[float] = None
    nature_tva_achat: Optional[str] = None
    tva_deductible_pct: Optional[float] = None
    est_proforma:   Optional[bool] = None
    lignes:         Optional[List[LigneFactureCreate]] = None

    @field_validator("ras_taux", mode="before")
    @classmethod
    def ras_taux_valide(cls, v):
        return None if v is None else _taux_ras_fini(v)


# ── Employés ──────────────────────────────────────────────────────────────────

class EmployeCreate(BaseModel):
    nom:                str
    poste:              Optional[str] = None
    salaire_brut:       float
    situation_familiale: str = "celiba"
    nb_enfants:         int  = 0
    date_embauche:      Optional[date] = None
    matricule:          Optional[str] = None
    numero_cnss:        Optional[str] = None
    type_contrat:       Optional[Literal["CDI", "CDD", "autre"]] = None
    date_sortie:        Optional[date] = None
    email:              Optional[EmailStr] = None
    telephone:          Optional[str] = None
    personnes_charge_ir: Optional[int] = None
    actif:              bool = True

    @field_validator("salaire_brut", mode="before")
    @classmethod
    def salaire_fini(cls, value):
        _nombre_fini(value)
        if not 0 <= float(value) <= 9999999999.99:
            raise ValueError("Salaire brut hors limites")
        return value

    @field_validator("nb_enfants", "personnes_charge_ir", mode="before")
    @classmethod
    def personnes_valides(cls, value, info):
        if value is None and info.field_name == "personnes_charge_ir":
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Un nombre entier positif ou nul est requis")
        if info.field_name == "personnes_charge_ir" and value > 6:
            raise ValueError("Le nombre de personnes à charge IR ne peut dépasser 6")
        return value

    @field_validator("nom", "poste", "matricule", "numero_cnss", "telephone", mode="before")
    @classmethod
    def texte_dossier(cls, value, info):
        if value is None and info.field_name != "nom":
            return None
        if not isinstance(value, str):
            raise ValueError("Un texte est requis")
        value = value.strip()
        maximum = 150 if info.field_name in ("nom", "poste") else 50
        if not value and info.field_name == "nom":
            raise ValueError("Le nom est requis")
        if len(value) > maximum:
            raise ValueError("Le texte dépasse la longueur autorisée")
        return value or None

    @field_validator("situation_familiale")
    @classmethod
    def situation_valide(cls, value):
        if value not in {"celiba", "marie", "veuf", "divorce"}:
            raise ValueError("Situation familiale invalide")
        return value

    @model_validator(mode="after")
    def dates_coherentes(self):
        if self.date_embauche and self.date_sortie and self.date_sortie < self.date_embauche:
            raise ValueError("La date de sortie précède l'embauche")
        return self

class EmployeOut(BaseModel):
    # La lecture ne revalide pas l'historique comme une nouvelle saisie.
    nom: str
    poste: Optional[str] = None
    salaire_brut: Optional[float] = None
    situation_familiale: Optional[str] = None
    nb_enfants: Optional[int] = None
    date_embauche: Optional[date] = None
    matricule: Optional[str] = None
    numero_cnss: Optional[str] = None
    type_contrat: Optional[str] = None
    date_sortie: Optional[date] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    personnes_charge_ir: Optional[int] = None
    id:         int
    actif:      bool
    created_at: datetime

    @field_validator("salaire_brut", mode="before")
    @classmethod
    def salaire_historique_lisible(cls, value):
        if value is None:
            return None
        try:
            return float(value) if math.isfinite(float(value)) else None
        except (TypeError, ValueError, OverflowError):
            return None

    class Config:
        from_attributes = True


# ── Dashboard / Stats ─────────────────────────────────────────────────────────

class KPIDashboard(BaseModel):
    chiffre_affaires: float
    charges:          float
    resultat_net:     float
    tva_due:          float
    nb_ecritures:     int
    nb_factures_attente: int

class AlerteStock(BaseModel):
    article_id:    int
    code:          str
    designation:   str
    stock_actuel:  float
    unite:         Optional[str]
    emplacement:   Optional[str]

    class Config:
        from_attributes = True


# ── Articles / Familles ───────────────────────────────────────────────────────

class FamilleCreate(BaseModel):
    code:         str
    libelle:      str
    tva_defaut:   float = 20.0
    compte_vente: Optional[str] = "7111"
    compte_achat: Optional[str] = "6111"
    compte_stock: Optional[str] = "3111"
    compte_variation_stock: Optional[str] = "6114"

    @field_validator('tva_defaut', mode='before')
    @classmethod
    def tva_defaut_finie(cls, v):
        _nombre_fini(v)
        if not 0 <= float(v) <= 100:
            raise ValueError('Le taux de TVA doit être compris entre 0 et 100 %')
        return v

class FamilleOut(FamilleCreate):
    # Projection de sortie uniquement : la saisie nouvelle conserve son contrat.
    tva_defaut: Optional[float] = None
    nombres_diagnostics: dict[str, str] = Field(default_factory=dict)
    id:         int
    actif:      bool
    created_at: datetime

    @field_validator('tva_defaut', mode='before')
    @classmethod
    def tva_defaut_finie(cls, v):
        if v is None or isinstance(v, bool):
            return None
        try:
            taux = float(v)
        except (TypeError, ValueError, OverflowError):
            return None
        return taux if math.isfinite(taux) and 0 <= taux <= 100 else None

    @model_validator(mode='after')
    def qualifier_tva_historique(self):
        self.nombres_diagnostics = {
            'tva_defaut': 'TVA historique absente ou invalide : vérifier la source avant utilisation.'
        } if self.tva_defaut is None else {}
        return self

    class Config:
        from_attributes = True

class ArticleCreate(BaseModel):
    famille_id:      Optional[int]   = None
    code:            str
    designation:     str
    description:     Optional[str]   = None
    prix_vente_ht:   float           = 0.0
    prix_achat_ht:   float           = 0.0
    tva:             float           = 20.0
    unite:           Optional[str]   = "unité"
    code_barre:      Optional[str]   = None
    stock_actuel:    float           = 0.0
    emplacement:     Optional[str]   = None
    is_stockable:    bool            = True
    stock_min:       float           = 0.0
    frais_emballage: float           = 0.0
    frais_transport: float           = 0.0
    # COMPTA.1 — surcharge facultative des comptes de la famille.
    compte_vente:    Optional[str]   = None
    compte_achat:    Optional[str]   = None

    @field_validator("prix_vente_ht", "prix_achat_ht", "stock_actuel", "stock_min", "frais_emballage", "frais_transport", "tva", mode="before")
    @classmethod
    def nombres_finis_saisie(cls, v):
        return _nombre_fini(v)

    @field_validator("code", "designation")
    @classmethod
    def texte_obligatoire(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("Champ obligatoire")
        return v

    @field_validator("prix_vente_ht", "prix_achat_ht", "stock_actuel", "stock_min", "frais_emballage", "frais_transport")
    @classmethod
    def valeur_non_negative(cls, v):
        if v < 0:
            raise ValueError("La valeur ne peut pas être négative")
        return v

    @field_validator("tva")
    @classmethod
    def tva_valide(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Le taux de TVA doit être compris entre 0 et 100 %")
        return v

class ArticleOut(ArticleCreate):
    # Une donnée historique inconnue reste consultable, jamais remplacée par 0.
    # Ce contrat de sortie ne relâche pas le contrat des saisies ArticleCreate.
    stock_actuel: Optional[float] = None
    stock_diagnostic: Optional[str] = None
    prix_vente_ht: Optional[float] = None
    prix_achat_ht: Optional[float] = None
    frais_emballage: Optional[float] = None
    frais_transport: Optional[float] = None
    stock_min: Optional[float] = None
    tva: Optional[float] = None
    nombres_diagnostics: dict[str, str] = Field(default_factory=dict)
    id:           int
    actif:        bool
    created_at:   datetime
    cmup:         Optional[float] = None  # coût moyen unitaire pondéré (valorisation)
    famille:      Optional[FamilleOut] = None

    @field_validator("prix_vente_ht", "prix_achat_ht", "stock_actuel", "stock_min", "frais_emballage", "frais_transport", "tva", "cmup", mode="before")
    @classmethod
    def nombres_finis_saisie(cls, v, info):
        # Projection JSON seulement : aucun attribut de l'ORM n'est changé.
        if v is None or isinstance(v, bool):
            return None
        try:
            nombre = float(v)
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(nombre) or nombre < 0:
            return None
        if info.field_name == 'tva' and nombre > 100:
            return None
        return nombre

    @field_validator("stock_actuel", mode="before")
    @classmethod
    def lire_stock_historique(cls, v):
        import math
        if v is None or isinstance(v, bool):
            return None
        try:
            nombre = float(v)
        except (TypeError, ValueError, OverflowError):
            return None
        return nombre if math.isfinite(nombre) and nombre >= 0 else None

    @field_validator("prix_vente_ht", "prix_achat_ht", "stock_actuel", "stock_min", "frais_emballage", "frais_transport")
    @classmethod
    def valeur_non_negative(cls, v):
        # Remplace le validateur hérité pour accepter le stock de sortie NULL.
        if v is not None and v < 0:
            raise ValueError("La valeur ne peut pas être négative")
        return v

    @field_validator("tva")
    @classmethod
    def tva_valide(cls, v):
        # Remplace le validateur de saisie hérité : inconnu reste NULL.
        return v

    @model_validator(mode="after")
    def qualifier_stock_historique(self):
        self.stock_diagnostic = (
            "Stock physique inconnu ou invalide : vérifier la source historique."
            if self.stock_actuel is None else None
        )
        self.nombres_diagnostics = {
            champ: 'Valeur historique absente ou invalide : vérifier la source avant utilisation.'
            for champ in ('prix_vente_ht', 'prix_achat_ht', 'frais_emballage',
                          'frais_transport', 'stock_min', 'tva', 'cmup')
            if getattr(self, champ) is None
        }
        return self

    class Config:
        from_attributes = True

class ArticleUpdate(BaseModel):
    designation:     Optional[str]   = None
    description:     Optional[str]   = None
    prix_vente_ht:   Optional[float] = None
    prix_achat_ht:   Optional[float] = None
    tva:             Optional[float] = None
    unite:           Optional[str]   = None
    famille_id:      Optional[int]   = None
    actif:           Optional[bool]  = None
    code_barre:      Optional[str]   = None
    stock_actuel:    Optional[float] = None
    emplacement:     Optional[str]   = None
    is_stockable:    Optional[bool]  = None
    stock_min:       Optional[float] = None
    frais_emballage: Optional[float] = None
    frais_transport: Optional[float] = None
    compte_vente:    Optional[str]   = None
    compte_achat:    Optional[str]   = None

    @field_validator("prix_vente_ht", "prix_achat_ht", "stock_actuel", "stock_min", "frais_emballage", "frais_transport", "tva", mode="before")
    @classmethod
    def nombres_finis_saisie(cls, v):
        # Un champ omis préserve l'historique. Une correction explicitement
        # fournie doit être un nombre connu, même si la lecture accepte NULL.
        return _nombre_fini(v)

    @field_validator("prix_vente_ht", "prix_achat_ht", "stock_actuel", "stock_min", "frais_emballage", "frais_transport")
    @classmethod
    def valeur_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("La valeur ne peut pas être négative")
        return v

    @field_validator("tva")
    @classmethod
    def tva_valide(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Le taux de TVA doit être compris entre 0 et 100 %")
        return v


# ── Mouvements de stock ───────────────────────────────────────────────────────

class MouvementStockOut(BaseModel):
    id:          int
    type:        str
    quantite:    Optional[float] = None
    stock_avant: Optional[float] = None
    stock_apres: Optional[float] = None
    nombres_diagnostics: dict[str, str] = Field(default_factory=dict)
    reference:   Optional[str]
    note:        Optional[str]
    created_at:  datetime

    @field_validator('quantite', 'stock_avant', 'stock_apres', mode='before')
    @classmethod
    def quantites_historiques_connues(cls, v):
        if v is None or isinstance(v, bool):
            return None
        try:
            quantite = float(v)
        except (ValueError, TypeError, OverflowError):
            return None
        return quantite if math.isfinite(quantite) else None

    @model_validator(mode='after')
    def qualifier_quantites_historiques(self):
        self.nombres_diagnostics = {
            c: 'Quantité historique absente ou non finie : vérifier la source.'
            for c in ('quantite', 'stock_avant', 'stock_apres') if getattr(self, c) is None
        }
        return self

    class Config:
        from_attributes = True


# ── Cycle commercial ──────────────────────────────────────────────────────────

# ── Devis ──────────────────────────────────────────────────────────────────────

class LigneDevisCreate(BaseModel):
    article_id:    Optional[int] = None
    description:   str
    quantite:      float = 1.0
    prix_unitaire: float = 0.0
    tva:           float = 20.0
    qualification_tva: str = "taxable"

    @field_validator("quantite", "prix_unitaire", "tva", mode="before")
    @classmethod
    def nombres_finis(cls, v):
        return _nombre_fini(v)

    @field_validator("description")
    @classmethod
    def description_obligatoire(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("La description de ligne est obligatoire")
        return v

    @field_validator("quantite")
    @classmethod
    def quantite_positive(cls, v):
        if v <= 0:
            raise ValueError("La quantité doit être strictement positive")
        return v

    @field_validator("prix_unitaire")
    @classmethod
    def prix_non_negatif(cls, v):
        if v < 0:
            raise ValueError("Le prix unitaire ne peut pas être négatif")
        return v

    @field_validator("tva")
    @classmethod
    def tva_valide(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Le taux de TVA doit être compris entre 0 et 100")
        return v

class LigneDevisOut(LigneDevisCreate):
    id:           int
    montant_ht:   float
    montant_tva:  float
    montant_ttc:  float
    class Config: from_attributes = True

def _verifier_totaux_devis_finis(lignes):
    """Garde de représentation avant mutation, sans modifier les calculs métier."""
    ht = tva = 0.0
    for ligne in lignes or []:
        h = ligne.quantite * ligne.prix_unitaire
        # Reproduit la qualification effective déjà utilisée par commercial.py.
        taux = ligne.tva if ligne.qualification_tva == 'taxable' else 0.0
        tv = h * (taux / 100)
        ttc_ligne = h * (1 + taux / 100)
        ht += h
        tva += tv
        if not all(math.isfinite(n) for n in (h, tv, ttc_ligne, ht, tva, ht + tva)):
            raise ValueError('Les montants calculés du devis doivent rester des nombres finis')
    return lignes


class DevisCreate(BaseModel):
    numero:         Optional[str] = None
    date:           date
    tiers:          str
    tiers_id:       Optional[int] = None
    reference:      Optional[str] = None
    validite_jours: int = 30
    notes:          Optional[str] = None
    lignes:         List[LigneDevisCreate]

    @field_validator('lignes')
    @classmethod
    def totaux_finis(cls, lignes):
        return _verifier_totaux_devis_finis(lignes)

class DevisOut(BaseModel):
    id:             int
    numero:         str
    date:           date
    exercice:       int
    tiers:          str
    tiers_id:       Optional[int] = None
    reference:      Optional[str]
    validite_jours: int
    statut:         str
    notes:          Optional[str]
    facture_id:     Optional[int] = None
    facture_numero: Optional[str] = None
    bon_commande_id: Optional[int] = None
    bon_commande_numero: Optional[str] = None
    total_ht:       float
    total_tva:      float
    total_ttc:      float
    lignes:         List[LigneDevisOut]
    created_at:     Optional[datetime]
    class Config: from_attributes = True

class DevisUpdate(BaseModel):
    statut:         Optional[Literal["brouillon", "envoye", "accepte", "converti", "refuse", "expire"]] = None
    notes:          Optional[str]  = None
    reference:      Optional[str]  = None
    numero:         Optional[str]  = None
    date:           Optional[str]  = None
    tiers:          Optional[str]  = None
    tiers_id:       Optional[int]  = None
    validite_jours: Optional[int]  = None
    facture_id:     Optional[int]  = None
    lignes:         Optional[List[LigneDevisCreate]] = None

    @field_validator('lignes')
    @classmethod
    def totaux_finis(cls, lignes):
        return _verifier_totaux_devis_finis(lignes)


# ── Bon de commande ────────────────────────────────────────────────────────────

class LigneBCCreate(BaseModel):
    article_id:    Optional[int] = None
    source_ligne_devis_id: Optional[int] = None
    description:   str
    quantite:      float = 1.0
    prix_unitaire: float = 0.0
    tva:           float = 20.0
    qualification_tva: str = "taxable"
    remise:        float = 0.0
    remise2:       float = 0.0
    rabais:        float = 0.0

    @field_validator("quantite", "prix_unitaire", "tva", "remise", "remise2", "rabais", mode="before")
    @classmethod
    def nombres_finis(cls, v):
        return _nombre_fini(v)

    @field_validator("description")
    @classmethod
    def description_obligatoire(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("La description de ligne est obligatoire")
        return v

    @field_validator("quantite")
    @classmethod
    def quantite_positive(cls, v):
        if v <= 0:
            raise ValueError("La quantité doit être strictement positive")
        return v

    @field_validator("prix_unitaire", "rabais")
    @classmethod
    def montants_non_negatifs(cls, v):
        if v < 0:
            raise ValueError("Les montants ne peuvent pas être négatifs")
        return v

    @field_validator("tva", "remise", "remise2")
    @classmethod
    def pourcentages_valides(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Le pourcentage doit être compris entre 0 et 100")
        return v

class LigneBCOut(LigneBCCreate):
    id:         int
    montant_ht: float
    montant_tva: float = 0.0
    montant_ttc: float = 0.0
    # FACT.3 — situation ligne par ligne du cycle commercial.
    quantite_commandee: float = 0.0
    quantite_livree: float = 0.0
    quantite_facturee: float = 0.0
    quantite_brouillon: float = 0.0
    quantite_reservee_facturation: float = 0.0
    reste_a_livrer: float = 0.0
    reste_a_facturer: float = 0.0
    livre_non_facture: float = 0.0
    class Config: from_attributes = True

def _verifier_totaux_bons_finis(lignes, livraison=False):
    """Vérifie les opérations float du cycle, uniquement sur les requêtes."""
    champs_quantite = ('quantite_prevue', 'quantite_livree') if livraison else ('quantite',)
    for champ_quantite in champs_quantite:
        ht = tva = 0.0
        for ligne in lignes or []:
            qte = getattr(ligne, champ_quantite)
            brut = qte * ligne.prix_unitaire
            remise1 = brut * (1 - ligne.remise / 100)
            remise2 = remise1 * (1 - ligne.remise2 / 100)
            rabais = ligne.rabais * qte
            net = remise2 - rabais
            if not all(math.isfinite(n) for n in (brut, remise1, remise2, rabais, net)):
                raise ValueError('Les montants calculés du bon doivent rester des nombres finis')
            h = max(net, 0.0)
            taux = ligne.tva if ligne.qualification_tva == 'taxable' else 0.0
            tv = h * (taux / 100)
            ht += h
            tva += tv
            if not all(math.isfinite(n) for n in (h, tv, h + tv, ht, tva, ht + tva)):
                raise ValueError('Les montants calculés du bon doivent rester des nombres finis')
    return lignes


class BonCommandeCreate(BaseModel):
    numero:         Optional[str] = None
    type:           Literal["vente", "achat"] = "vente"
    date:           date
    tiers:          str
    tiers_id:       Optional[int] = None
    reference:      Optional[str] = None
    date_livraison: Optional[date] = None
    devis_id:       Optional[int] = None
    notes:          Optional[str] = None
    lignes:         List[LigneBCCreate]

    @field_validator('lignes')
    @classmethod
    def totaux_finis(cls, lignes):
        return _verifier_totaux_bons_finis(lignes)

class BonCommandeOut(BaseModel):
    id:             int
    numero:         str
    type:           str
    date:           date
    exercice:       int
    tiers:          str
    tiers_id:       Optional[int] = None
    reference:      Optional[str]
    date_livraison: Optional[date]
    devis_id:       Optional[int]
    facture_id:     Optional[int]
    statut:         str
    notes:          Optional[str]
    total_ht:       float
    total_tva:      float = 0.0
    total_ttc:      float = 0.0
    # FACT.2 — avancement dérivé du cycle, sans surcharger le statut historique du BC
    statut_cycle:            Optional[str] = None
    livraison_pct:           float = 0.0
    facturation_pct:         float = 0.0
    facturation_reservee_pct: float = 0.0
    montant_commande_ht:     float = 0.0
    montant_livre_ht:        float = 0.0
    montant_facture_ht:      float = 0.0
    montant_brouillon_ht:    float = 0.0
    reste_a_livrer_ht:       float = 0.0
    reste_a_facturer_ht:     float = 0.0
    nb_bons_logistiques:     int = 0
    nb_factures:             int = 0
    nb_brouillons:           int = 0
    lignes:         List[LigneBCOut]
    created_at:     Optional[datetime]
    class Config: from_attributes = True

class BonCommandeUpdate(BaseModel):
    statut:         Optional[Literal["en_attente", "confirme", "partiel", "livre", "facture", "annule"]] = None
    date_livraison: Optional[str] = None
    notes:          Optional[str] = None
    facture_id:     Optional[int] = None
    numero:         Optional[str] = None
    tiers:          Optional[str] = None
    tiers_id:       Optional[int] = None
    type:           Optional[Literal["vente", "achat"]] = None
    lignes:         Optional[List[LigneBCCreate]] = None

    @field_validator('lignes')
    @classmethod
    def totaux_finis(cls, lignes):
        return _verifier_totaux_bons_finis(lignes)


# ── Bon de livraison ───────────────────────────────────────────────────────────

class LigneBLCreate(BaseModel):
    article_id:       Optional[int] = None
    source_ligne_bc_id: Optional[int] = None
    description:      str
    quantite_prevue:  float = 1.0
    quantite_livree:  float = 1.0
    prix_unitaire:    float = 0.0
    tva:              float = 20.0
    qualification_tva: str = "taxable"
    remise:           float = 0.0
    remise2:          float = 0.0
    rabais:           float = 0.0

    @field_validator("quantite_prevue", "quantite_livree", "prix_unitaire", "tva", "remise", "remise2", "rabais", mode="before")
    @classmethod
    def nombres_finis(cls, v):
        return _nombre_fini(v)

    @field_validator("description")
    @classmethod
    def description_obligatoire(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("La description de ligne est obligatoire")
        return v

    @field_validator("quantite_prevue")
    @classmethod
    def quantite_prevue_positive(cls, v):
        if v <= 0:
            raise ValueError("La quantité prévue doit être strictement positive")
        return v

    @field_validator("quantite_livree", "prix_unitaire", "rabais")
    @classmethod
    def valeurs_non_negatives(cls, v):
        if v < 0:
            raise ValueError("La valeur ne peut pas être négative")
        return v

    @field_validator("tva", "remise", "remise2")
    @classmethod
    def pourcentages_valides(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Le pourcentage doit être compris entre 0 et 100")
        return v

class LigneBLOut(LigneBLCreate):
    id: int
    ligne_bl_id: Optional[int] = None
    quantite_facturee: float = 0.0
    quantite_brouillon: float = 0.0
    quantite_reservee_facturation: float = 0.0
    reste_a_facturer: float = 0.0
    class Config: from_attributes = True

class BonLivraisonCreate(BaseModel):
    numero:          Optional[str] = None
    type:            Literal["vente", "achat"] = "vente"
    date:            date
    tiers:           str
    tiers_id:        Optional[int] = None
    bon_commande_id: Optional[int] = None
    facture_id:      Optional[int] = None
    transporteur:    Optional[str] = None
    notes:           Optional[str] = None
    lignes:          List[LigneBLCreate]

    @field_validator('lignes')
    @classmethod
    def totaux_finis(cls, lignes):
        return _verifier_totaux_bons_finis(lignes, livraison=True)

class BonLivraisonOut(BaseModel):
    id:              int
    numero:          str
    type:            str
    date:            date
    exercice:        int
    tiers:           str
    tiers_id:        Optional[int] = None
    bon_commande_id: Optional[int]
    bon_commande_numero: Optional[str] = None
    facture_id:      Optional[int]
    transporteur:    Optional[str]
    statut:          str
    notes:           Optional[str]
    # FACT.3 — la facturation d'un BL/BR peut être partielle et multi-factures.
    facturation_pct: float = 0.0
    facturation_reservee_pct: float = 0.0
    montant_a_facturer_ht: float = 0.0
    montant_facture_ht: float = 0.0
    montant_brouillon_ht: float = 0.0
    reste_a_facturer_ht: float = 0.0
    nb_factures: int = 0
    nb_brouillons: int = 0
    facture_numeros: Optional[List[str]] = None
    lignes:          List[LigneBLOut]
    created_at:      Optional[datetime]
    class Config: from_attributes = True

class BonLivraisonUpdate(BaseModel):
    statut:      Optional[Literal["en_preparation", "expedie", "livre", "retourne"]] = None
    transporteur: Optional[str] = None
    notes:       Optional[str] = None


# ── Règlement ──────────────────────────────────────────────────────────────────

def _valider_montant_reglement(v):
    if v is None:
        return v
    if isinstance(v, bool):
        raise ValueError("Le montant du règlement ne peut pas être un booléen")
    try:
        montant = float(v)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Le montant du règlement doit être numérique") from exc
    if not math.isfinite(montant) or montant <= 0:
        raise ValueError("Le montant du règlement doit être fini et strictement positif")
    try:
        exact = Decimal(str(v))
        # Les colonnes historiques sont des doubles : préserver le seul bruit
        # de représentation machine (ex.0.1+0.2), pas un vrai sous-centime.
        tolerance = Decimal(str(min(1e-8, 4 * math.ulp(montant))))
        if abs(exact - exact.quantize(Decimal('0.01'))) > tolerance:
            raise ValueError("Le montant du règlement doit être exprimé au centime, sans arrondi implicite")
    except InvalidOperation as exc:
        raise ValueError("Le montant du règlement doit être représentable au centime") from exc
    return v


class ReglementUpdate(BaseModel):
    date:       Optional[str]  = None
    montant:    Optional[float] = None
    mode:       Optional[ModeReglement] = None
    reference:  Optional[str]   = None
    banque:     Optional[str]   = None
    # Échéance des effets et chèques post-datés : conditionne l'encaissement
    date_echeance: Optional[str] = None
    notes:      Optional[str]   = None

    @field_validator("montant", mode="before")
    @classmethod
    def montant_reglement_valide(cls, v):
        return _valider_montant_reglement(v)


class LigneQuantiteIn(BaseModel):
    """Quantité à livrer pour une ligne donnée (livraison partielle)."""
    ligne_bc_id: Optional[int] = None
    description: str
    quantite:    float

    @field_validator("quantite")
    @classmethod
    def quantite_positive(cls, v):
        if v is None or float(v) <= 0:
            raise ValueError("La quantité à livrer doit être strictement positive")
        return v


class ConvertirBLIn(BaseModel):
    """Paramètres de conversion BC → BL/BR.

    `lignes` permet une livraison PARTIELLE : on ne transmet que les quantités
    effectivement livrées. Sans `lignes`, le reste à livrer est pris en totalité.
    """
    date:   Optional[str] = None
    lignes: Optional[List[LigneQuantiteIn]] = None




class LigneQuantiteFactureIn(BaseModel):
    """Quantité à facturer d'une ligne physique BL/BR."""
    ligne_bl_id: int
    quantite: float


class ConvertirBCFactureIn(BaseModel):
    """Conversion BC -> facture. La date de la facture est indépendante de celle du BC."""
    date: Optional[DateType] = None


class ConvertirBLFactureIn(BaseModel):
    """Facturation partielle d'un BL/BR.

    Sans ``lignes``, tout le reliquat facturable du bon est facturé.
    La date de facture est indépendante de la date logistique.
    """
    date: Optional[DateType] = None
    lignes: Optional[List[LigneQuantiteFactureIn]] = None


class ConvertirProformaIn(BaseModel):
    """Conversion d'une proforma en facture définitive."""
    date: Optional[DateType] = None

class ReglementCreate(BaseModel):
    facture_id: Optional[int] = None
    tiers_id:   Optional[int] = None
    numero:     Optional[str] = None
    date:       date
    tiers:      str
    montant:    float
    mode:       ModeReglement = "virement"
    reference:  Optional[str] = None
    banque:     Optional[str] = None
    date_echeance: Optional[date] = None   # échéance des effets / chèques post-datés
    notes:      Optional[str] = None
    comptabiliser: bool = True             # génère l'écriture d'encaissement immédiatement

    @field_validator("montant", mode="before")
    @classmethod
    def montant_reglement_positif(cls, v):
        return _valider_montant_reglement(v)

    @model_validator(mode="after")
    def echeance_mode_reglement(self):
        if self.mode == "effet" and not self.date_echeance:
            raise ValueError("Une date d'échéance est obligatoire pour un effet de commerce")
        if self.date_echeance and self.date_echeance < self.date:
            raise ValueError("La date d'échéance ne peut pas précéder la date du règlement")
        return self

class VentilationReglementIn(BaseModel):
    facture_id: int = Field(gt=0, strict=True)
    montant: float

    @field_validator('montant', mode='before')
    @classmethod
    def montant_centimes(cls, v):
        _valider_montant_reglement(v)
        try:
            nombre = Decimal(str(v))
            if nombre != nombre.quantize(Decimal('0.01')):
                raise ValueError('Le montant doit être exprimé au centime.')
        except InvalidOperation as exc:
            raise ValueError('Montant non représentable au centime.') from exc
        return v


class ReglementParTiersCreate(BaseModel):
    operation_id: UUID
    tiers_id: int = Field(gt=0, strict=True)
    date: DateType
    montant: float
    mode: Literal['virement', 'especes', 'carte', 'prelevement', 'autre'] = 'virement'
    reference: Optional[str] = Field(default=None, max_length=100)
    banque: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    comptabiliser: bool = True
    ventilations: List[VentilationReglementIn] = Field(min_length=1, max_length=50)

    @field_validator('montant', mode='before')
    @classmethod
    def montant_centimes(cls, v):
        return VentilationReglementIn.montant_centimes(v)

    @model_validator(mode='after')
    def ventilation_exacte(self):
        ids = [v.facture_id for v in self.ventilations]
        if len(ids) != len(set(ids)):
            raise ValueError('Une facture ne peut figurer deux fois dans la ventilation.')
        if sum((Decimal(str(v.montant)) for v in self.ventilations), Decimal(0)) != Decimal(str(self.montant)):
            raise ValueError('Le total des ventilations doit être égal au montant du paiement.')
        return self


class ReglementOut(ReglementCreate):
    id:                int
    statut:            str
    date_encaissement: Optional[date] = None
    est_comptabilisee: bool = False
    date_annulation: Optional[datetime] = None
    ecriture_id: Optional[int] = None
    ecriture_annulation_id: Optional[int] = None
    created_at:        Optional[datetime]
    class Config: from_attributes = True


class ReglementLectureOut(BaseModel):
    """Projection de lecture : aucune validation de saisie ni réparation historique."""
    id: int
    facture_id: Optional[int] = None
    tiers_id: Optional[int] = None
    numero: Optional[str] = None
    date: date
    tiers: str
    montant: Optional[float]
    mode: str
    reference: Optional[str] = None
    banque: Optional[str] = None
    date_echeance: Optional[date] = None
    notes: Optional[str] = None
    comptabiliser: bool = True
    statut: str
    date_encaissement: Optional[date] = None
    est_comptabilisee: bool = False
    date_annulation: Optional[datetime] = None
    ecriture_id: Optional[int] = None
    ecriture_annulation_id: Optional[int] = None
    created_at: Optional[datetime] = None
    montant_valide: bool = True
    montant_anomalie: Optional[str] = None
    facture_type: Optional[str] = None
    facture_numero: Optional[str] = None
    facture_exercice: Optional[int] = None
    facture_statut: Optional[str] = None
    facture_montants_valides: Optional[bool] = None
    class Config: from_attributes = True


# ── Comptes bancaires ─────────────────────────────────────────────────────────

class CompteBancaireCreate(BaseModel):
    banque:           str
    agence:           Optional[str] = None
    rib:              Optional[str] = None
    iban:             Optional[str] = None
    devise:           str = "MAD"
    compte_comptable: str = "5141"

class CompteBancaireOut(CompteBancaireCreate):
    id:         int
    actif:      bool
    created_at: datetime

    class Config:
        from_attributes = True

class CompteBancaireUpdate(BaseModel):
    banque:           Optional[str] = None
    agence:           Optional[str] = None
    rib:              Optional[str] = None
    iban:             Optional[str] = None
    devise:           Optional[str] = None
    compte_comptable: Optional[str] = None
    actif:            Optional[bool] = None


# ── Rapprochement bancaire ────────────────────────────────────────────────────

class RapprochementLigneCreate(BaseModel):
    compte:    str
    date:      date
    libelle:   Optional[str] = None
    montant:   float
    sens:      str = "debit"

class RapprochementLigneOut(RapprochementLigneCreate):
    id:                 int
    rapprochee:         bool
    ecriture_ligne_id:  Optional[int] = None
    date_rapprochement: Optional[datetime] = None
    rapproche_par:      Optional[int] = None
    created_at:         datetime

    class Config:
        from_attributes = True

class RapprochementLigneUpdate(BaseModel):
    date:       Optional[date] = None
    libelle:    Optional[str] = None
    montant:    Optional[float] = None
    sens:       Optional[str] = None
    rapprochee: Optional[bool] = None


# ── Immobilisations ───────────────────────────────────────────────────────────

class ImmobilisationCreate(BaseModel):
    designation:          str
    reference:            Optional[str] = None
    categorie:            Optional[str] = None
    date_acquisition:     date
    date_mise_en_service: Optional[date] = None
    prix_acquisition_ht:  Decimal
    taux_tva:             Decimal = Decimal("20")
    qualification_tva:    str = "taxable"
    tva_recuperable_pct:  Decimal = Decimal("100")
    fournisseur:          Optional[str] = None
    fournisseur_tiers_id: Optional[int] = None
    date_paiement:        Optional[date] = None
    amortissable:         bool = True
    duree_amort:          Optional[int] = 5
    methode:              str = "lineaire"
    taux_degressif:       Optional[Decimal] = None
    vehicule_tourisme:    bool = False
    compte_immo:          str = "2332"
    compte_amort:         str = "28332"
    compte_dotation:      str = "61933"
    compte_tva:           str = "34551"
    compte_fournisseur:   str = "4481"
    compte_reglement:     str = "5141"
    valeur_residuelle:    Decimal = Decimal("0")
    notes:                Optional[str] = None

    @field_validator("prix_acquisition_ht", "valeur_residuelle")
    @classmethod
    def montant_non_negatif(cls, v):
        if v < 0:
            raise ValueError("Le montant ne peut pas être négatif")
        return v

    @field_validator("taux_tva", "tva_recuperable_pct")
    @classmethod
    def pourcentage_valide(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Le pourcentage doit être compris entre 0 et 100")
        return v

    @field_validator("methode")
    @classmethod
    def methode_valide(cls, v):
        v = (v or "lineaire").lower()
        if v not in {"lineaire", "degressif"}:
            raise ValueError("Méthode d'amortissement invalide")
        return v

    @model_validator(mode="after")
    def coherence_immo(self):
        if self.date_mise_en_service is None:
            self.date_mise_en_service = self.date_acquisition
        if self.date_mise_en_service < self.date_acquisition:
            raise ValueError("La mise en service ne peut pas précéder l'acquisition")
        if self.date_paiement and self.date_paiement < self.date_acquisition:
            raise ValueError("Le paiement ne peut pas précéder l'acquisition")
        if self.compte_immo in {"2311", "2312", "2313", "2318"} or (self.categorie or "").strip().lower() == "terrain":
            self.amortissable = False
            self.duree_amort = None
        if self.amortissable:
            if not self.duree_amort or self.duree_amort <= 0:
                raise ValueError("Une immobilisation amortissable doit avoir une durée positive")
            if self.methode == "degressif" and self.duree_amort < 3:
                raise ValueError("L'amortissement dégressif requiert une durée d'au moins 3 ans")
            if self.methode == "degressif" and self.vehicule_tourisme:
                raise ValueError("Le dégressif n'est pas autorisé pour un véhicule de transport de personnes")
            if self.methode == "degressif" and (self.compte_immo.startswith("232") or self.compte_immo in {"2311", "2312", "2313", "2318"}):
                raise ValueError("Le dégressif n'est pas autorisé pour les terrains ou immeubles")
        return self


class ImmobilisationOut(BaseModel):
    id:                    int
    designation:           str
    reference:             Optional[str] = None
    categorie:             Optional[str] = None
    date_acquisition:      date
    date_mise_en_service:  date
    prix_acquisition_ht:   Decimal
    taux_tva:              Decimal
    qualification_tva:     str = "taxable"
    tva_recuperable_pct:   Decimal
    valeur_brute:          Decimal
    valeur_residuelle:     Decimal
    fournisseur:           Optional[str] = None
    fournisseur_tiers_id:  Optional[int] = None
    date_paiement:         Optional[date] = None
    tva_suivie_directement: bool = True
    amortissable:          bool
    duree_amort:           Optional[int] = None
    methode:               str
    taux_degressif:        Optional[Decimal] = None
    vehicule_tourisme:     bool
    compte_immo:           str
    compte_amort:          str
    compte_dotation:       str
    compte_tva:            str
    compte_fournisseur:    str
    compte_reglement:      str
    ecriture_acquisition_id: Optional[int] = None
    ecriture_paiement_id:    Optional[int] = None
    date_sortie:             Optional[date] = None
    type_sortie:             Optional[str] = None
    prix_cession_ht:         Optional[Decimal] = None
    taux_tva_cession:        Optional[Decimal] = None
    qualification_tva_cession: Optional[str] = None
    regime_tva_cession:      Optional[str] = None
    date_encaissement_cession: Optional[date] = None
    ecriture_cession_id:     Optional[int] = None
    ecriture_sortie_id:      Optional[int] = None
    ecriture_encaissement_cession_id: Optional[int] = None
    actif:                 bool
    created_at:            datetime
    tva_acquisition:       Decimal = Decimal("0")
    tva_recuperable:       Decimal = Decimal("0")
    tva_non_recuperable:   Decimal = Decimal("0")
    total_ttc:             Decimal = Decimal("0")
    cumul_amortissement:   Decimal = Decimal("0")
    vnc_actuelle:          Decimal = Decimal("0")

    class Config:
        from_attributes = True


class ImmobilisationUpdate(BaseModel):
    designation:          Optional[str] = None
    reference:            Optional[str] = None
    categorie:            Optional[str] = None
    date_mise_en_service: Optional[date] = None
    prix_acquisition_ht:  Optional[Decimal] = None
    taux_tva:             Optional[Decimal] = None
    qualification_tva:    Optional[str] = None
    tva_recuperable_pct:  Optional[Decimal] = None
    fournisseur:          Optional[str] = None
    fournisseur_tiers_id: Optional[int] = None
    amortissable:         Optional[bool] = None
    duree_amort:          Optional[int] = None
    methode:              Optional[str] = None
    taux_degressif:       Optional[Decimal] = None
    vehicule_tourisme:    Optional[bool] = None
    compte_immo:          Optional[str] = None
    compte_amort:         Optional[str] = None
    compte_dotation:      Optional[str] = None
    compte_tva:           Optional[str] = None
    compte_fournisseur:   Optional[str] = None
    compte_reglement:     Optional[str] = None
    valeur_residuelle:    Optional[Decimal] = None
    notes:                Optional[str] = None


class ImmobilisationPaiementIn(BaseModel):
    date_paiement: date
    compte_reglement: str = "5141"
    reference: Optional[str] = None


class ImmobilisationSortieIn(BaseModel):
    type_sortie: Literal["cession", "rebut"]
    date_sortie: date
    prix_cession_ht: Decimal = Decimal("0")
    taux_tva_cession: Decimal = Decimal("20")
    qualification_tva_cession: str = "taxable"
    encaissement_immediat: bool = True
    date_encaissement: Optional[date] = None
    compte_tresorerie: str = "5141"
    reference: Optional[str] = None
    empreinte_apercu: Optional[str] = Field(default=None, pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode="after")
    def coherence_sortie(self):
        if self.prix_cession_ht < 0:
            raise ValueError("Le prix de cession ne peut pas être négatif")
        if self.taux_tva_cession < 0 or self.taux_tva_cession > 100:
            raise ValueError("Le taux de TVA de cession doit être compris entre 0 et 100")
        if self.type_sortie == "cession" and self.prix_cession_ht <= 0:
            raise ValueError("Une cession doit avoir un prix HT strictement positif")
        if self.type_sortie == "rebut":
            self.prix_cession_ht = Decimal("0")
            self.taux_tva_cession = Decimal("0")
            self.qualification_tva_cession = "hors_champ"
            self.encaissement_immediat = False
            self.date_encaissement = None
        if self.encaissement_immediat and self.type_sortie == "cession" and self.date_encaissement is None:
            self.date_encaissement = self.date_sortie
        if self.date_encaissement and self.date_encaissement < self.date_sortie:
            raise ValueError("L'encaissement de la cession ne peut pas précéder la cession")
        return self


class ImmobilisationEncaissementCessionIn(BaseModel):
    date_encaissement: date
    compte_tresorerie: str = "5141"
    reference: Optional[str] = None
