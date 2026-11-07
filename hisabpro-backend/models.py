from sqlalchemy import Column, Integer, String, Float, Numeric, Date, DateTime, ForeignKey, ForeignKeyConstraint, Boolean, Text, Enum, UniqueConstraint, CheckConstraint, JSON, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


class LiasseBalancePreparation(Base):
    """Version de préparation externe ; distincte du grand livre et archive fiscale."""
    __tablename__ = 'liasse_balances_preparation'
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer, ForeignKey('societes.id'), nullable=False, index=True)
    exercice = Column(Integer, nullable=False, index=True)
    exercice_id = Column(Integer, ForeignKey('exercices_comptables.id'), nullable=False)
    version = Column(Integer, nullable=False)
    contenu = Column(JSON, nullable=False)
    empreinte_sha256 = Column(String(64), nullable=False)
    created_by = Column(Integer, ForeignKey('utilisateurs.id'), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint('societe_id', 'exercice', 'version', name='uq_liasse_balance_version'),
        CheckConstraint('version > 0', name='ck_liasse_balance_version'),
    )


# ── Énumérations ──────────────────────────────────────────────────────────────

class JournalEnum(str, enum.Enum):
    # Journaux standards
    AC = "AC"  # Achats
    VT = "VT"  # Ventes
    BQ = "BQ"  # Banque
    CA = "CA"  # Caisse
    OD = "OD"  # Opérations diverses
    CL = "CL"  # Clôture — réservé au moteur de clôture
    # Journaux spéciaux
    AN = "AN"  # À nouveau
    EN = "EN"  # Encours
    AE = "AE"  # À encaisser
    AV = "AV"  # Avoirs
    AM = "AM"  # Amortissements
    TV = "TV"  # TVA
    PR = "PR"  # Provisions
    SA = "SA"  # Salaires (paie du personnel)

class TypeFactureEnum(str, enum.Enum):
    achat  = "achat"
    vente  = "vente"

class StatutFactureEnum(str, enum.Enum):
    en_attente          = "en_attente"
    payee               = "payee"
    partiellement_payee = "partiellement_payee"
    retard              = "retard"
    annulee             = "annulee"
    comptabilisee       = "comptabilisee"


# ── Société ───────────────────────────────────────────────────────────────────

class Societe(Base):
    __tablename__ = "societes"

    id                  = Column(Integer, primary_key=True, index=True)
    raison_sociale      = Column(String(200), nullable=False)
    identifiant_fiscal  = Column(String(50))
    ice                 = Column(String(20))
    rc                  = Column(String(50))
    patente             = Column(String(50))
    cnss_numero         = Column(String(50))
    adresse             = Column(Text)
    ville               = Column(String(100))
    pays                = Column(String(50), default="Maroc")
    telephone           = Column(String(20))
    fax                 = Column(String(20))
    email               = Column(String(100))
    site_web            = Column(String(200))
    # Banque
    banque              = Column(String(100))
    agence              = Column(String(100))
    rib                 = Column(String(50))
    # Paramètres comptables
    exercice_debut      = Column(Integer, default=2026)
    periodicite_tva     = Column(String(20), default="mensuelle")  # mensuelle | trimestrielle
    # Identité fiscale et sectorielle
    devise              = Column(String(10), default="MAD")        # devise de tenue de comptabilité
    regime_fiscal       = Column(String(30), default="is")         # is | ir | auto_entrepreneur | exonere
    regime_tva          = Column(String(30), default="encaissement")  # encaissement | debit | exonere | hors_champ
    secteur             = Column(String(80), nullable=True)        # activité principale
    forme_juridique     = Column(String(50), nullable=True)        # SARL, SA, SNC...
    capital_social      = Column(Float, default=0.0)
    # Préfixes de numérotation des documents
    prefixe_facture     = Column(String(10), default="FA")
    prefixe_devis       = Column(String(10), default="DV")
    prefixe_bc          = Column(String(10), default="BC")
    prefixe_bl          = Column(String(10), default="BL")
    prefixe_avoir       = Column(String(10), default="AV")
    # Déclenchement des mouvements de stock : 'facture' (défaut) | 'bl' (vente) | 'br' (achat)
    stock_declencheur_vente = Column(String(10), default="facture")
    stock_declencheur_achat = Column(String(10), default="facture")
    # Format des libellés d'écritures — variables : {numero} {tiers} {ref} {date}
    format_libelle_vente  = Column(String(120), default="Facture {numero} {tiers}")
    format_libelle_achat  = Column(String(120), default="Facture d'achat {numero} {tiers}")
    format_libelle_avoir  = Column(String(120), default="Avoir {numero} {tiers}")
    format_libelle_banque = Column(String(120), default="Règlement {tiers} {ref}")
    # Logo (chemin ou base64)
    logo_url            = Column(Text)
    created_at          = Column(DateTime, server_default=func.now())

    utilisateurs        = relationship("Utilisateur", back_populates="societe")
    ecritures           = relationship("Ecriture",    back_populates="societe")
    factures            = relationship("Facture",     back_populates="societe")
    employes            = relationship("Employe",     back_populates="societe")
    modules             = relationship("ModuleActif", foreign_keys="ModuleActif.societe_id",
                                       primaryjoin="Societe.id == ModuleActif.societe_id")


class CompteCGNCReference(Base):
    """Référentiel CGNC livré avec HisabPro.

    Cette table est un modèle de référence : chaque société possède ensuite son
    propre plan dans ``comptes_societe``. Le référentiel n'est jamais utilisé
    comme substitut silencieux au plan de la société lors de la saisie.
    """
    __tablename__ = "plan_comptable_cgnc_reference"

    numero      = Column(String(10), primary_key=True)
    libelle     = Column(String(300), nullable=False)
    classe      = Column(Integer, nullable=False)
    type_compte = Column(String(10), nullable=True)


class CompteSociete(Base):
    """Compte effectivement utilisable par une société.

    ``origine`` distingue les comptes issus du référentiel CGNC des subdivisions
    créées par l'entreprise. La désactivation interdit les nouvelles saisies sans
    effacer l'historique comptable.
    """
    __tablename__ = "comptes_societe"

    id          = Column(Integer, primary_key=True, index=True)
    societe_id  = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    numero      = Column(String(10), nullable=False)
    libelle     = Column(String(300), nullable=False)
    classe      = Column(Integer, nullable=False)
    type_compte = Column(String(10), nullable=True)
    origine     = Column(String(20), nullable=False, default="cgnc")  # cgnc | personnalise | historique
    actif       = Column(Boolean, nullable=False, default=True, index=True)
    created_at  = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "numero", name="uq_compte_societe_numero"),
        CheckConstraint("LENGTH(numero) BETWEEN 4 AND 10", name="ck_compte_societe_numero_longueur"),
        CheckConstraint("classe BETWEEN 0 AND 9", name="ck_compte_societe_classe"),
        CheckConstraint("origine IN ('cgnc','personnalise','historique')", name="ck_compte_societe_origine"),
    )



class TVAParametreExercice(Base):
    """Paramètres TVA propres à une société et un exercice.

    ``credit_ouverture`` correspond au crédit reportable existant avant la
    première période de l'exercice. ``prorata_deduction_pct`` est le prorata
    annuel appliqué aux dépenses ouvrant par ailleurs droit à déduction.
    """
    __tablename__ = "tva_parametres_exercice"

    id                    = Column(Integer, primary_key=True, index=True)
    societe_id            = Column(Integer, ForeignKey("societes.id"), nullable=False)
    exercice              = Column(Integer, nullable=False, index=True)
    credit_ouverture      = Column(Numeric(18, 2), nullable=False, default=0)
    prorata_deduction_pct = Column(Numeric(5, 2), nullable=False, default=100)
    updated_at            = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", name="uq_tva_param_societe_exercice"),
        CheckConstraint("credit_ouverture >= 0", name="ck_tva_credit_ouverture_non_negatif"),
        CheckConstraint("prorata_deduction_pct >= 0 AND prorata_deduction_pct <= 100", name="ck_tva_prorata_pct"),
    )


class ETICSectionExercice(Base):
    """Compléments ETIC saisis pour une société et un exercice.

    Les tableaux calculables restent produits dynamiquement depuis la comptabilité.
    Cette table ne stocke que les informations extra-comptables / commentaires
    nécessaires aux états A1-A3, B8-B10, C1-C5 et aux compléments des états
    assistés. Le contenu JSON est volontairement générique afin de conserver
    le format officiel de chaque section sans multiplier les tables métier.
    """
    __tablename__ = "etic_sections_exercice"

    id          = Column(Integer, primary_key=True, index=True)
    societe_id  = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    exercice    = Column(Integer, nullable=False, index=True)
    code        = Column(String(10), nullable=False)
    contenu     = Column(JSON, nullable=False, default=dict)
    updated_by  = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", "code", name="uq_etic_section_societe_exercice_code"),
    )


class LiasseFiscaleArchive(Base):
    """Photographie immuable d'une liasse fiscale finalisée.

    Le contenu JSON canonique regroupe les états de synthèse, le passage au
    résultat fiscal, les contrôles et l'ETIC tels qu'ils existaient au moment
    de la finalisation. Une nouvelle correction future devra créer une nouvelle
    version plutôt que réécrire l'archive existante.
    """
    __tablename__ = "liasses_fiscales_archives"

    id                  = Column(Integer, primary_key=True, index=True)
    societe_id          = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    exercice            = Column(Integer, nullable=False, index=True)
    version             = Column(Integer, nullable=False, default=1)
    contenu_json        = Column(Text, nullable=False)
    empreinte_sha256    = Column(String(64), nullable=False)
    date_finalisation   = Column(DateTime, nullable=False, server_default=func.now())
    finalisee_par       = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", "version", name="uq_liasse_archive_societe_exercice_version"),
        CheckConstraint("version > 0", name="ck_liasse_archive_version_positive"),
    )


class FiscalParametreExercice(Base):
    """Paramètres IS propres à une société et un exercice.

    Le régime est historisé par exercice : un changement futur de statut CFC,
    d'activité industrielle ou de régime particulier ne doit jamais réécrire le
    calcul fiscal d'un exercice antérieur.
    """
    __tablename__ = "fiscal_parametres_exercice"

    id                  = Column(Integer, primary_key=True, index=True)
    societe_id          = Column(Integer, ForeignKey("societes.id"), nullable=False)
    exercice            = Column(Integer, nullable=False, index=True)
    categorie_is        = Column(String(40), nullable=False, default="droit_commun")
    justification_regime = Column(Text, nullable=True)
    maintien_taux_35_transition = Column(Boolean, nullable=False, default=False)
    deficit_reportable_disponible = Column(Numeric(18, 2), nullable=False, default=0)
    taux_is_force       = Column(Numeric(6, 3), nullable=True)
    justification_taux_force = Column(Text, nullable=True)
    # Cotisation minimale — Patch 08.4
    cm_base_exclue      = Column(Numeric(18, 2), nullable=False, default=0)
    cm_justification_base_exclue = Column(Text, nullable=True)
    cm_base_taux_reduit_015 = Column(Numeric(18, 2), nullable=False, default=0)
    cm_justification_taux_reduit = Column(Text, nullable=True)
    cm_exoneration_totale = Column(Boolean, nullable=False, default=False)
    cm_justification_exoneration = Column(Text, nullable=True)
    cm_minimum_3000_exonere = Column(Boolean, nullable=False, default=False)
    cm_justification_minimum_exonere = Column(Text, nullable=True)
    # Acomptes provisionnels — Patch 08.5. Une référence manuelle n'est
    # utilisée qu'en reprise de dossier / absence de liquidation N-1 confirmée.
    acomptes_reference_forcee = Column(Numeric(18, 2), nullable=True)
    acomptes_justification_reference_forcee = Column(Text, nullable=True)
    # Contribution sociale de solidarité — Patch 08.6
    css_benefice_reference_forcee = Column(Numeric(18, 2), nullable=True)
    css_justification_reference_forcee = Column(Text, nullable=True)
    css_exoneration_permanente = Column(Boolean, nullable=False, default=False)
    css_justification_exoneration = Column(Text, nullable=True)
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", name="uq_fiscal_param_societe_exercice"),
        CheckConstraint(
            "categorie_is IN ('droit_commun','industrielle','cfc_zai','convention_investissement','avantage_20_transition','financier_40','exonere')",
            name="ck_fiscal_categorie_is",
        ),
        CheckConstraint("deficit_reportable_disponible >= 0", name="ck_fiscal_deficit_non_negatif"),
        CheckConstraint(
            "categorie_is = 'droit_commun' OR NULLIF(TRIM(justification_regime), '') IS NOT NULL",
            name="ck_fiscal_regime_special_justifie",
        ),
        CheckConstraint("taux_is_force IS NULL OR (taux_is_force >= 0 AND taux_is_force <= 100)", name="ck_fiscal_taux_force"),
        CheckConstraint(
            "taux_is_force IS NULL OR NULLIF(TRIM(justification_taux_force), '') IS NOT NULL",
            name="ck_fiscal_taux_force_justifie",
        ),
        CheckConstraint("cm_base_exclue >= 0", name="ck_fiscal_cm_base_exclue_non_negative"),
        CheckConstraint("cm_base_taux_reduit_015 >= 0", name="ck_fiscal_cm_base_reduite_non_negative"),
        CheckConstraint(
            "cm_base_exclue = 0 OR NULLIF(TRIM(cm_justification_base_exclue), '') IS NOT NULL",
            name="ck_fiscal_cm_base_exclue_justifiee",
        ),
        CheckConstraint(
            "cm_base_taux_reduit_015 = 0 OR NULLIF(TRIM(cm_justification_taux_reduit), '') IS NOT NULL",
            name="ck_fiscal_cm_taux_reduit_justifie",
        ),
        CheckConstraint(
            "cm_exoneration_totale = FALSE OR NULLIF(TRIM(cm_justification_exoneration), '') IS NOT NULL",
            name="ck_fiscal_cm_exoneration_justifiee",
        ),
        CheckConstraint(
            "cm_minimum_3000_exonere = FALSE OR NULLIF(TRIM(cm_justification_minimum_exonere), '') IS NOT NULL",
            name="ck_fiscal_cm_minimum_exonere_justifie",
        ),
        CheckConstraint(
            "acomptes_reference_forcee IS NULL OR acomptes_reference_forcee >= 0",
            name="ck_fiscal_acomptes_reference_non_negative",
        ),
        CheckConstraint(
            "acomptes_reference_forcee IS NULL OR NULLIF(TRIM(acomptes_justification_reference_forcee), '') IS NOT NULL",
            name="ck_fiscal_acomptes_reference_justifiee",
        ),
        CheckConstraint(
            "css_benefice_reference_forcee IS NULL OR css_benefice_reference_forcee >= 0",
            name="ck_fiscal_css_reference_non_negative",
        ),
        CheckConstraint(
            "css_benefice_reference_forcee IS NULL OR NULLIF(TRIM(css_justification_reference_forcee), '') IS NOT NULL",
            name="ck_fiscal_css_reference_justifiee",
        ),
        CheckConstraint(
            "css_exoneration_permanente = FALSE OR NULLIF(TRIM(css_justification_exoneration), '') IS NOT NULL",
            name="ck_fiscal_css_exoneration_justifiee",
        ),
    )


class FiscalRetraitement(Base):
    """Réintégration ou déduction extra-comptable d'un exercice fiscal."""
    __tablename__ = "fiscal_retraitements"

    id          = Column(Integer, primary_key=True, index=True)
    societe_id  = Column(Integer, ForeignKey("societes.id"), nullable=False)
    exercice    = Column(Integer, nullable=False, index=True)
    type        = Column(String(20), nullable=False)  # reintegration | deduction
    categorie   = Column(String(50), nullable=False, default="autre")
    libelle     = Column(String(250), nullable=False)
    montant     = Column(Numeric(18, 2), nullable=False)
    compte_source = Column(String(120), nullable=True)
    reference   = Column(String(120), nullable=True)
    commentaire = Column(Text, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('reintegration','deduction')", name="ck_fiscal_retraitement_type"),
        CheckConstraint("montant > 0", name="ck_fiscal_retraitement_montant_positif"),
    )


class FiscalDeficit(Base):
    """Déficit fiscal reportable ventilé par exercice d'origine (Patch 08.3)."""
    __tablename__ = "fiscal_deficits"

    id                     = Column(Integer, primary_key=True, index=True)
    societe_id             = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False)
    exercice_origine       = Column(Integer, nullable=False, index=True)
    montant_ordinaire      = Column(Numeric(18, 2), nullable=False, default=0)
    montant_amortissements = Column(Numeric(18, 2), nullable=False, default=0)
    source                 = Column(String(30), nullable=False, default="manuel")  # manuel | calcul
    commentaire            = Column(Text, nullable=True)
    created_at             = Column(DateTime, server_default=func.now())
    updated_at             = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice_origine", name="uq_fiscal_deficit_societe_origine"),
        CheckConstraint("montant_ordinaire >= 0", name="ck_fiscal_deficit_ordinaire_non_negatif"),
        CheckConstraint("montant_amortissements >= 0", name="ck_fiscal_deficit_amort_non_negatif"),
        CheckConstraint("montant_ordinaire + montant_amortissements > 0", name="ck_fiscal_deficit_total_positif"),
        CheckConstraint("source IN ('manuel','calcul')", name="ck_fiscal_deficit_source"),
    )


class FiscalDeficitImputation(Base):
    """Consommation historisée d'un déficit fiscal sur un exercice bénéficiaire."""
    __tablename__ = "fiscal_deficit_imputations"

    id                     = Column(Integer, primary_key=True, index=True)
    societe_id             = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False)
    deficit_id             = Column(Integer, ForeignKey("fiscal_deficits.id", ondelete="RESTRICT"), nullable=False, index=True)
    exercice_cible         = Column(Integer, nullable=False, index=True)
    montant_ordinaire      = Column(Numeric(18, 2), nullable=False, default=0)
    montant_amortissements = Column(Numeric(18, 2), nullable=False, default=0)
    created_at             = Column(DateTime, server_default=func.now())
    updated_at             = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("deficit_id", "exercice_cible", name="uq_fiscal_deficit_imputation_cible"),
        CheckConstraint("montant_ordinaire >= 0", name="ck_fiscal_imputation_ordinaire_non_negatif"),
        CheckConstraint("montant_amortissements >= 0", name="ck_fiscal_imputation_amort_non_negatif"),
        CheckConstraint("montant_ordinaire + montant_amortissements > 0", name="ck_fiscal_imputation_total_positif"),
    )


class FiscalLiquidationIS(Base):
    """Photographie fiscale confirmée d'un exercice (Patch 08.5).

    Elle fige les montants servant notamment de référence aux acomptes de N+1.
    Les calculs live restent modifiables tant que la liquidation n'est pas confirmée.
    """
    __tablename__ = "fiscal_liquidations_is"

    id                        = Column(Integer, primary_key=True, index=True)
    societe_id                = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False)
    exercice                  = Column(Integer, nullable=False, index=True)
    benefice_fiscal_imposable = Column(Numeric(18, 2), nullable=False, default=0)
    is_theorique              = Column(Numeric(18, 2), nullable=False, default=0)
    cm_exigible               = Column(Numeric(18, 2), nullable=False, default=0)
    impot_du                  = Column(Numeric(18, 2), nullable=False, default=0)
    nature_impot              = Column(String(10), nullable=False)
    acomptes_imputables       = Column(Numeric(18, 2), nullable=False, default=0)
    credits_is_imputables     = Column(Numeric(18, 2), nullable=False, default=0)
    solde_a_payer             = Column(Numeric(18, 2), nullable=False, default=0)
    excedent_acomptes         = Column(Numeric(18, 2), nullable=False, default=0)
    excedent_credits_is       = Column(Numeric(18, 2), nullable=False, default=0)
    excedent_total            = Column(Numeric(18, 2), nullable=False, default=0)
    snapshot_detail           = Column(JSON, nullable=True)
    confirmee_par             = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    date_confirmation         = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", name="uq_fiscal_liquidation_societe_exercice"),
        CheckConstraint("benefice_fiscal_imposable >= 0", name="ck_fiscal_liq_benefice_non_negatif"),
        CheckConstraint("is_theorique >= 0 AND cm_exigible >= 0 AND impot_du >= 0", name="ck_fiscal_liq_impots_non_negatifs"),
        CheckConstraint("acomptes_imputables >= 0 AND credits_is_imputables >= 0 AND solde_a_payer >= 0 AND excedent_acomptes >= 0 AND excedent_credits_is >= 0 AND excedent_total >= 0", name="ck_fiscal_liq_soldes_non_negatifs"),
        CheckConstraint("nature_impot IN ('IS','CM')", name="ck_fiscal_liq_nature_impot"),
    )


class FiscalAcompteIS(Base):
    """Paiement ou dispense d'un acompte provisionnel IS (Patch 08.5)."""
    __tablename__ = "fiscal_acomptes_is"

    id                 = Column(Integer, primary_key=True, index=True)
    societe_id         = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False)
    exercice           = Column(Integer, nullable=False, index=True)
    numero             = Column(Integer, nullable=False)
    montant_verse      = Column(Numeric(18, 2), nullable=False, default=0)
    date_versement     = Column(Date, nullable=True)
    reference_paiement = Column(String(120), nullable=True)
    dispense           = Column(Boolean, nullable=False, default=False)
    reference_dispense = Column(String(200), nullable=True)
    commentaire        = Column(Text, nullable=True)
    created_at         = Column(DateTime, server_default=func.now())
    updated_at         = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", "numero", name="uq_fiscal_acompte_societe_exercice_numero"),
        CheckConstraint("numero BETWEEN 1 AND 4", name="ck_fiscal_acompte_numero"),
        CheckConstraint("montant_verse >= 0", name="ck_fiscal_acompte_montant_non_negatif"),
        CheckConstraint(
            "(montant_verse > 0 AND date_versement IS NOT NULL) OR dispense = TRUE",
            name="ck_fiscal_acompte_paiement_ou_dispense",
        ),
        CheckConstraint(
            "dispense = FALSE OR NULLIF(TRIM(reference_dispense), '') IS NOT NULL",
            name="ck_fiscal_acompte_dispense_justifiee",
        ),
    )


class FiscalCreditIS(Base):
    """Retenue/crédit d'impôt imputable sur l'IS (Patch 08.6)."""
    __tablename__ = "fiscal_credits_is"

    id                           = Column(Integer, primary_key=True, index=True)
    societe_id                   = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False)
    exercice                     = Column(Integer, nullable=False, index=True)
    type                         = Column(String(30), nullable=False)  # pprf | retenue_tiers | autre
    montant                      = Column(Numeric(18, 2), nullable=False)
    montant_deja_impute_acomptes = Column(Numeric(18, 2), nullable=False, default=0)
    date_retenue                 = Column(Date, nullable=True)
    reference                    = Column(String(160), nullable=False)
    commentaire                  = Column(Text, nullable=True)
    created_at                   = Column(DateTime, server_default=func.now())
    updated_at                   = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('pprf','retenue_tiers','autre')", name="ck_fiscal_credit_is_type"),
        CheckConstraint("montant > 0", name="ck_fiscal_credit_is_montant_positif"),
        CheckConstraint("montant_deja_impute_acomptes >= 0 AND montant_deja_impute_acomptes <= montant", name="ck_fiscal_credit_is_imputation_acomptes"),
        CheckConstraint("NULLIF(TRIM(reference), '') IS NOT NULL", name="ck_fiscal_credit_is_reference"),
        CheckConstraint("type <> 'autre' OR NULLIF(TRIM(commentaire), '') IS NOT NULL", name="ck_fiscal_credit_is_autre_justifie"),
    )


class FiscalCSSPaiement(Base):
    """Paiement de la contribution sociale de solidarité d'une année (Patch 08.6)."""
    __tablename__ = "fiscal_css_paiements"

    id                 = Column(Integer, primary_key=True, index=True)
    societe_id         = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False)
    annee              = Column(Integer, nullable=False, index=True)
    montant_verse      = Column(Numeric(18, 2), nullable=False)
    date_versement     = Column(Date, nullable=False)
    reference_paiement = Column(String(160), nullable=False)
    commentaire        = Column(Text, nullable=True)
    created_at         = Column(DateTime, server_default=func.now())
    updated_at         = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "annee", name="uq_fiscal_css_paiement_societe_annee"),
        CheckConstraint("montant_verse > 0", name="ck_fiscal_css_paiement_montant_positif"),
        CheckConstraint("NULLIF(TRIM(reference_paiement), '') IS NOT NULL", name="ck_fiscal_css_paiement_reference"),
    )


# ── Utilisateurs ──────────────────────────────────────────────────────────────

class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id"), nullable=False)
    nom           = Column(String(100), nullable=False)
    email         = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role          = Column(String(20), default="comptable")  # admin | comptable | lecture
    actif         = Column(Boolean, default=True)
    created_at    = Column(DateTime, server_default=func.now())

    societe       = relationship("Societe", back_populates="utilisateurs")

    __table_args__ = (
        CheckConstraint("role IN ('admin','comptable','lecture','personnel')", name="ck_utilisateurs_role_hisabpro"),
    )


class AuditAction(Base):
    """Journal applicatif append-only des actions HTTP modifiantes (FACT.11)."""
    __tablename__ = "audit_actions"

    id          = Column(Integer, primary_key=True, index=True)
    societe_id  = Column(Integer, nullable=True, index=True)
    acteur_id   = Column(Integer, nullable=True, index=True)
    acteur_nom  = Column(String(200), nullable=True)
    acteur_email = Column(String(200), nullable=True)
    acteur_role = Column(String(40), nullable=True)
    methode     = Column(String(10), nullable=False)
    chemin      = Column(String(300), nullable=False)
    statut_http = Column(Integer, nullable=False)
    succes      = Column(Boolean, nullable=False, default=True)
    ip          = Column(String(80), nullable=True)
    request_id  = Column(String(64), nullable=True, index=True)
    created_at  = Column(DateTime, server_default=func.now(), nullable=False)


# ── Écritures comptables ──────────────────────────────────────────────────────

class Ecriture(Base):
    __tablename__ = "ecritures"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id"), nullable=False)
    date          = Column(Date, nullable=False, index=True)
    journal       = Column(Enum(JournalEnum), nullable=False)
    libelle       = Column(String(300), nullable=False)
    # Métadonnées de pièce / chemin de révision (Patch 07B)
    # ``numero_ecriture`` est un identifiant interne immuable attribué
    # automatiquement par PostgreSQL lors de la validation définitive, par
    # société / exercice / journal. Un brouillon conserve NULL.
    # ``reference`` reste la référence du justificatif externe (facture,
    # relevé bancaire, chèque, contrat...) et ne doit pas être confondue
    # avec le numéro interne.
    numero_ecriture = Column(String(40), nullable=True, index=True)
    reference       = Column(String(100))
    date_piece      = Column(Date, nullable=True)
    exercice      = Column(Integer, nullable=False, index=True)  # année
    source        = Column(String(20), default="manuel")  # manuel | ia | import
    # Validation : une écriture validée est définitive (non modifiable, non supprimable).
    # Tant qu'elle est en brouillon, elle reste corrigeable librement.
    est_validee   = Column(Boolean, default=False, index=True)
    date_validation = Column(DateTime, nullable=True)
    validee_par   = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    # COMPTA.3 : une correction d'écriture définitive se fait par une nouvelle
    # contrepassation liée à l'original ; l'original n'est jamais réécrit.
    contrepassation_de_id = Column(Integer, ForeignKey("ecritures.id", ondelete="RESTRICT"), nullable=True, index=True)
    motif_correction = Column(String(500), nullable=True)
    created_at    = Column(DateTime, server_default=func.now())

    societe       = relationship("Societe",      back_populates="ecritures")
    lignes        = relationship("LigneEcriture", back_populates="ecriture",
                                 cascade="all, delete-orphan")
    # COMPTA.4 : les références documentaires ajoutées après validation vivent
    # dans une table séparée. L'écriture définitive reste donc strictement
    # intangible, tout en pouvant être reliée ultérieurement à son justificatif.
    justificatifs = relationship(
        "EcritureJustificatif",
        back_populates="ecriture",
        cascade="all, delete-orphan",
        order_by="EcritureJustificatif.id",
    )

    @property
    def reference_fec(self):
        overrides = [j for j in (self.justificatifs or []) if getattr(j, "prioritaire", False)]
        if overrides:
            return overrides[-1].reference
        if (self.reference or "").strip():
            return self.reference
        refs = [j for j in (self.justificatifs or []) if (getattr(j, "reference", None) or "").strip()]
        return refs[-1].reference if refs else None

    @property
    def date_piece_fec(self):
        overrides = [j for j in (self.justificatifs or []) if getattr(j, "prioritaire", False)]
        if overrides:
            return overrides[-1].date_piece or self.date_piece or self.date
        if (self.reference or "").strip():
            return self.date_piece or self.date
        refs = [j for j in (self.justificatifs or []) if (getattr(j, "reference", None) or "").strip()]
        if refs:
            return refs[-1].date_piece or self.date_piece or self.date
        return self.date_piece or self.date

    @property
    def nb_justificatifs(self):
        return len(self.justificatifs or [])


@event.listens_for(Ecriture, "before_insert")
def _completer_date_piece_ecriture(_mapper, _connection, target):
    # Avis n°24 §2.3.e : à défaut d'une date documentaire distincte, la date
    # de saisie/comptabilisation couvre le champ Date_Piece. Cela évite de
    # demander une saisie supplémentaire à l'utilisateur.
    if target.date_piece is None:
        target.date_piece = target.date


class LigneEcriture(Base):
    __tablename__ = "lignes_ecriture"

    id            = Column(Integer, primary_key=True, index=True)
    ecriture_id   = Column(Integer, ForeignKey("ecritures.id", ondelete="CASCADE"), nullable=False)
    compte        = Column(String(10), nullable=False, index=True)
    libelle       = Column(String(300))
    # Montants comptables : NUMERIC/Decimal, jamais FLOAT.
    # 18 chiffres dont 2 décimales couvre largement les montants en MAD tout en
    # évitant les erreurs binaires de type 0.1 + 0.2 != 0.3.
    debit         = Column(Numeric(18, 2), nullable=False, default=0)
    credit        = Column(Numeric(18, 2), nullable=False, default=0)
    # COMPTA-AUX / Avis n°24 : rattachement natif et snapshot de l'auxiliaire.
    # Le nom/code du tiers au jour de la comptabilisation ne dépend jamais de
    # la fiche tiers courante lors d'un export FEC ultérieur.
    tiers_id      = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    nature_auxiliaire = Column(String(20), nullable=True)  # client | fournisseur
    compte_auxiliaire_snapshot = Column(String(20), nullable=True)
    libelle_auxiliaire_snapshot = Column(String(200), nullable=True)
    # Champ prévu pour l'IA (score de confiance si rempli par IA)
    confidence    = Column(Float, nullable=True)

    __table_args__ = (
        CheckConstraint("debit >= 0", name="ck_ligne_ecriture_debit_non_negatif"),
        CheckConstraint("credit >= 0", name="ck_ligne_ecriture_credit_non_negatif"),
        CheckConstraint(
            "NOT (debit > 0 AND credit > 0)",
            name="ck_ligne_ecriture_un_seul_sens",
        ),
    )

    ecriture      = relationship("Ecriture", back_populates="lignes")
    tiers          = relationship("Tiers", foreign_keys=[tiers_id])
    # PATCH 097 — les anciennes lignes déjà définitives ne sont jamais réécrites
    # pour compléter un auxiliaire FEC. Un complément append-only peut porter
    # l'identité auxiliaire manquante, de la même manière que
    # ``ecriture_justificatifs`` complète une référence documentaire historique.
    auxiliaire_complements = relationship(
        "LigneAuxiliaireComplement",
        back_populates="ligne",
        order_by="LigneAuxiliaireComplement.id",
    )
    # COMPTA-FINAL : le lettrage est une métadonnée séparée de la ligne comptable
    # afin de préserver l'immutabilité des écritures définitives.
    lettrages      = relationship("LettrageComptable", back_populates="ligne", cascade="all, delete-orphan", order_by="LettrageComptable.id")

    @property
    def lettrage_actif(self):
        actifs = [x for x in (self.lettrages or []) if getattr(x, "actif", False)]
        return actifs[-1] if actifs else None

    @property
    def code_lettrage(self):
        x = self.lettrage_actif
        return x.code if x else None

    @property
    def date_lettrage(self):
        x = self.lettrage_actif
        return x.date_lettrage if x else None


class LigneAuxiliaireComplement(Base):
    """Complément auxiliaire append-only d'une ligne comptable historique.

    Les écritures définitives restent strictement immuables. Cette table sert
    uniquement à documenter, après coup et avec piste d'audit, un auxiliaire
    déterminé sans ambiguïté pour les historiques antérieurs à COMPTA-AUX.
    """
    __tablename__ = "ligne_auxiliaire_complements"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    ligne_ecriture_id = Column(Integer, ForeignKey("lignes_ecriture.id", ondelete="RESTRICT"), nullable=False, index=True)
    tiers_id      = Column(Integer, ForeignKey("tiers.id", ondelete="RESTRICT"), nullable=False, index=True)
    nature_auxiliaire = Column(String(20), nullable=False)
    compte_auxiliaire_snapshot = Column(String(20), nullable=False)
    libelle_auxiliaire_snapshot = Column(String(200), nullable=False)
    source_type   = Column(String(30), nullable=False, default="reparation_historique")
    source_id     = Column(Integer, nullable=True)
    motif         = Column(String(500), nullable=True)
    created_by    = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    created_at    = Column(DateTime, server_default=func.now(), nullable=False)

    ligne         = relationship("LigneEcriture", back_populates="auxiliaire_complements")
    tiers         = relationship("Tiers", foreign_keys=[tiers_id])

    __table_args__ = (
        CheckConstraint(
            "nature_auxiliaire IN ('client','fournisseur')",
            name="ck_ligne_aux_complement_nature",
        ),
        CheckConstraint(
            "length(trim(compte_auxiliaire_snapshot)) > 0",
            name="ck_ligne_aux_complement_compte_non_vide",
        ),
        CheckConstraint(
            "length(trim(libelle_auxiliaire_snapshot)) > 0",
            name="ck_ligne_aux_complement_libelle_non_vide",
        ),
    )


class LettrageComptable(Base):
    __tablename__ = "lettrages_comptables"

    id                = Column(Integer, primary_key=True, index=True)
    societe_id        = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    ligne_ecriture_id = Column(Integer, ForeignKey("lignes_ecriture.id", ondelete="CASCADE"), nullable=False, index=True)
    code              = Column(String(10), nullable=False, index=True)
    date_lettrage     = Column(DateTime, server_default=func.now(), nullable=False)
    created_by        = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    actif             = Column(Boolean, nullable=False, default=True, index=True)
    date_delettrage   = Column(DateTime, nullable=True)
    delettre_par      = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    created_at        = Column(DateTime, server_default=func.now(), nullable=False)
    # Lettrage partiel déclaré à la création (migration 130) ; jamais modifié ensuite.
    partiel           = Column(Boolean, nullable=False, default=False, server_default="false")

    ligne             = relationship("LigneEcriture", back_populates="lettrages")


class EcritureJustificatif(Base):
    __tablename__ = "ecriture_justificatifs"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    ecriture_id   = Column(Integer, ForeignKey("ecritures.id", ondelete="CASCADE"), nullable=False, index=True)
    reference     = Column(String(100), nullable=False)
    date_piece    = Column(Date, nullable=False)
    source_type   = Column(String(30), nullable=False, default="manuel")
    source_id     = Column(Integer, nullable=True)
    fichier_nom   = Column(String(255), nullable=True)
    prioritaire   = Column(Boolean, nullable=False, default=False)
    motif         = Column(String(500), nullable=True)
    created_by    = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    created_at    = Column(DateTime, server_default=func.now(), nullable=False)

    ecriture      = relationship("Ecriture", back_populates="justificatifs")

    __table_args__ = (
        CheckConstraint("length(trim(reference)) > 0", name="ck_ecriture_justificatif_reference_non_vide"),
    )


# ── Factures ──────────────────────────────────────────────────────────────────

class Facture(Base):
    __tablename__ = "factures"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id"), nullable=False)
    numero        = Column(String(50), nullable=True)
    type          = Column(Enum(TypeFactureEnum), nullable=False)
    date          = Column(Date, nullable=False, index=True)
    exercice      = Column(Integer, nullable=False, index=True)
    tiers         = Column(String(200), nullable=False)
    # FACT.1 — lien technique vers le tiers + snapshot légal de la pièce.
    # Le libellé ``tiers`` reste le nom figé affiché sur la facture.
    tiers_id      = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    # COMPTA.1 — compte tiers figé lors de la validation de la facture.
    compte_tiers_snapshot = Column(String(10), nullable=True)
    tiers_ice_snapshot = Column(String(20), nullable=True)
    tiers_if_snapshot = Column(String(50), nullable=True)
    tiers_rc_snapshot = Column(String(50), nullable=True)
    tiers_adresse_snapshot = Column(Text, nullable=True)
    tiers_ville_snapshot = Column(String(100), nullable=True)
    tiers_telephone_snapshot = Column(String(20), nullable=True)
    tiers_email_snapshot = Column(String(100), nullable=True)
    tiers_categorie_snapshot = Column(String(20), nullable=True)
    # FACT-B — photographie de l'émetteur au moment où la facture devient définitive.
    # Le PDF historique ne doit jamais dépendre de la fiche société courante.
    societe_snapshot_json = Column(Text, nullable=True)
    # FACT-B — contenu imprimé figé à validation ; les notes internes peuvent
    # ensuite évoluer sans modifier le PDF historique.
    notes_snapshot = Column(Text, nullable=True)
    reference     = Column(String(100))
    statut        = Column(Enum(StatutFactureEnum), default=StatutFactureEnum.en_attente)
    notes         = Column(Text)
    delai_paiement    = Column(Integer, default=60)
    # FACT.4 — cycle de validation de la facture. Le numéro interne et
    # l'échéance contractuelle deviennent définitifs à la validation.
    est_validee      = Column(Boolean, default=False, nullable=False)
    date_validation  = Column(DateTime, nullable=True)
    validee_par      = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    date_echeance    = Column(Date, nullable=True, index=True)
    # FACT-D — conditions de règlement convenues, figées avec la facture définitive.
    mode_reglement_prevu = Column(String(20), nullable=True)
    reference_reglement_prevue = Column(String(100), nullable=True)
    # FACT-F — métadonnées déclaratives loi 69-21. Elles peuvent être complétées
    # après validation sans réécrire les données économiques de la facture.
    date_livraison_service = Column(Date, nullable=True)
    litige_judiciaire = Column(Boolean, default=False, nullable=False)
    reference_litige = Column(String(200), nullable=True)
    delais_paiement_hors_champ = Column(Boolean, default=False, nullable=False)
    delais_paiement_motif_hors_champ = Column(String(300), nullable=True)
    est_comptabilisee = Column(Boolean, default=False)
    # Régime TVA figé à la date de la facture : évite qu’un changement futur
    # de paramétrage société ne réécrive l’historique fiscal.
    regime_tva      = Column(String(30), default="encaissement")
    qualification_tva = Column(String(40), default="taxable", nullable=False)
    # Achats : qualification fiscale explicite. On ne déduit jamais une règle TVA
    # depuis le libellé du compte ou de la facture.
    nature_tva_achat = Column(String(30), default="charge")  # charge | immobilisation | non_deductible
    tva_deductible_pct = Column(Numeric(5, 2), default=100)   # 0..100 avant prorata global
    code_lettrage     = Column(String(10), nullable=True, index=True)
    remise_globale    = Column(Float, default=0.0)   # remise commerciale en % sur le pied
    ristourne         = Column(Float, default=0.0)   # ristourne en % (volume d'affaires), pied de facture
    escompte          = Column(Float, default=0.0)
    # Frais accessoires facturés
    frais_transport_ht  = Column(Float, default=0.0)
    frais_transport_tva = Column(Float, default=20.0)
    frais_transport_mode = Column(String(30), default="accessoire", nullable=False)
    frais_transport_qualification_tva = Column(String(40), default="taxable", nullable=False)
    frais_emballage_ht  = Column(Float, default=0.0)
    frais_emballage_tva = Column(Float, default=20.0)
    frais_emballage_mode = Column(String(30), default="perdu", nullable=False)
    frais_emballage_qualification_tva = Column(String(40), default="taxable", nullable=False)
    # Retenue à la source
    ras_taux          = Column(Float, default=0.0)      # 0 | 5 | 10 | 15 | 20 (%)
    ras_comptabilisee = Column(Boolean, default=False)
    # Facture proforma : aucun effet stock ni comptable
    est_proforma      = Column(Boolean, default=False)
    created_at        = Column(DateTime, server_default=func.now())

    societe       = relationship("Societe",      back_populates="factures")
    lignes        = relationship("LigneFacture",  back_populates="facture",
                                 cascade="all, delete-orphan")
    echeances     = relationship("EcheanceFacture", back_populates="facture",
                                 cascade="all, delete-orphan", order_by="EcheanceFacture.ordre")


class LigneFacture(Base):
    __tablename__ = "lignes_facture"

    id            = Column(Integer, primary_key=True, index=True)
    facture_id    = Column(Integer, ForeignKey("factures.id", ondelete="CASCADE"), nullable=False)
    article_id    = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    # COMPTA.1 — comptes figés à la validation (article > famille > défaut).
    compte_vente_snapshot = Column(String(10), nullable=True)
    compte_achat_snapshot = Column(String(10), nullable=True)
    # Traçabilité du cycle commercial : la ligne d'origine reste identifiable
    # même si sa désignation est modifiée ultérieurement.
    source_ligne_devis_id = Column(Integer, ForeignKey("lignes_devis.id", ondelete="SET NULL"), nullable=True, index=True)
    source_ligne_bc_id = Column(Integer, ForeignKey("lignes_bon_commande.id", ondelete="SET NULL"), nullable=True, index=True)
    source_ligne_bl_id = Column(Integer, ForeignKey("lignes_bon_livraison.id", ondelete="SET NULL"), nullable=True, index=True)
    description   = Column(String(300), nullable=False)
    quantite      = Column(Float, default=1.0)
    prix_unitaire = Column(Float, nullable=False)
    tva           = Column(Float, default=20.0)  # taux TVA en %
    qualification_tva = Column(String(40), default="taxable", nullable=False)
    remise        = Column(Float, default=0.0)   # remise 1 en % (liée à la quantité / accord commercial)
    remise2       = Column(Float, default=0.0)   # remise 2 en %, appliquée EN CASCADE sur le net après remise 1
    rabais        = Column(Float, default=0.0)   # rabais exceptionnel, en MONTANT par unité (défaut qualité, retard)

    facture       = relationship("Facture", back_populates="lignes")

    @property
    def montant_ht(self):
        return self.quantite * self.prix_unitaire

    @property
    def montant_tva(self):
        return self.montant_ht * (self.tva / 100)

    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva


# ── Avoir (note de crédit) ─────────────────────────────────────────────────────

class StatutAvoirEnum(str, enum.Enum):
    emis      = "emis"       # émis, pas encore utilisé
    utilise   = "utilise"    # imputé sur une facture future
    rembourse = "rembourse"  # remboursé au tiers
    annule    = "annule"

class Avoir(Base):
    __tablename__ = "avoirs"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id"), nullable=False)
    facture_id    = Column(Integer, ForeignKey("factures.id"), nullable=False)
    numero        = Column(String(50), nullable=False)
    type          = Column(Enum(TypeFactureEnum), nullable=False)  # vente | achat — hérité de la facture
    date          = Column(Date, nullable=False, index=True)
    exercice      = Column(Integer, nullable=False, index=True)
    tiers         = Column(String(200), nullable=False)
    motif         = Column(String(300), nullable=True)   # ex: retour marchandise, erreur facturation
    statut        = Column(Enum(StatutAvoirEnum), default=StatutAvoirEnum.emis)
    notes         = Column(Text)
    est_comptabilisee = Column(Boolean, default=False)
    # FACT.6 — snapshots nécessaires pour qu'un avoir inverse fidèlement la facture
    # même si les paramètres de la facture ou de la société changent ensuite.
    retour_stock = Column(Boolean, default=False, nullable=False)
    remise_globale_snapshot = Column(Float, default=0.0, nullable=False)
    ristourne_snapshot = Column(Float, default=0.0, nullable=False)
    escompte_snapshot = Column(Float, default=0.0, nullable=False)
    nature_tva_achat_snapshot = Column(String(30), nullable=True)
    nature_avoir = Column(String(30), default="retour_annulation", nullable=False)
    tva_deductible_pct_snapshot = Column(Numeric(5, 2), nullable=True)
    # FACT-H — identité légale figée de l'avoir : un PDF historique ne doit
    # jamais changer lorsque la fiche société/tiers est modifiée après émission.
    societe_snapshot_json = Column(Text, nullable=True)
    tiers_ice_snapshot = Column(String(20), nullable=True)
    tiers_if_snapshot = Column(String(50), nullable=True)
    tiers_rc_snapshot = Column(String(50), nullable=True)
    tiers_adresse_snapshot = Column(Text, nullable=True)
    tiers_ville_snapshot = Column(String(100), nullable=True)
    tiers_telephone_snapshot = Column(String(20), nullable=True)
    tiers_email_snapshot = Column(String(100), nullable=True)
    tiers_categorie_snapshot = Column(String(20), nullable=True)
    notes_snapshot = Column(Text, nullable=True)
    date_annulation = Column(DateTime, nullable=True)
    annulee_par = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    ecriture_annulation_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    created_at    = Column(DateTime, server_default=func.now())

    societe       = relationship("Societe")
    facture       = relationship("Facture")
    lignes        = relationship("LigneAvoir", back_populates="avoir",
                                 cascade="all, delete-orphan")


class LigneAvoir(Base):
    __tablename__ = "lignes_avoir"

    id            = Column(Integer, primary_key=True, index=True)
    avoir_id      = Column(Integer, ForeignKey("avoirs.id", ondelete="CASCADE"), nullable=False)
    # FACT.6 — lien technique vers la ligne de facture : plus aucun rapprochement
    # métier par simple description.
    facture_ligne_id = Column(Integer, ForeignKey("lignes_facture.id", ondelete="SET NULL"), nullable=True, index=True)
    article_id    = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    description   = Column(String(300), nullable=False)
    quantite      = Column(Float, default=1.0)
    prix_unitaire = Column(Float, nullable=False)
    tva           = Column(Float, default=20.0)
    qualification_tva = Column(String(40), default="taxable", nullable=False)
    remise        = Column(Float, default=0.0)
    remise2       = Column(Float, default=0.0)
    rabais        = Column(Float, default=0.0)
    montant_ht_force = Column(Numeric(18, 2), nullable=True)
    mode_calcul       = Column(String(30), default="quantite", nullable=False)
    taux_rrr          = Column(Numeric(7, 4), nullable=True)
    nouveau_prix_unitaire = Column(Numeric(18, 4), nullable=True)

    avoir         = relationship("Avoir", back_populates="lignes")

    @property
    def montant_ht(self):
        if self.montant_ht_force is not None:
            return max(float(self.montant_ht_force or 0), 0)
        net = self.quantite * self.prix_unitaire
        net *= (1 - (self.remise or 0) / 100)
        net *= (1 - (self.remise2 or 0) / 100)
        net -= (self.rabais or 0) * self.quantite
        return max(net, 0)

    @property
    def montant_tva(self):
        return self.montant_ht * (self.tva / 100)

    @property
    def montant_ttc(self):
        return self.montant_ht + self.montant_tva


# ── Employés / CNSS ───────────────────────────────────────────────────────────

class Employe(Base):
    __tablename__ = "employes"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id"), nullable=False)
    nom           = Column(String(150), nullable=False)
    poste         = Column(String(150))
    salaire_brut  = Column(Float, nullable=True)  # Brouillon Personnel sans montant attesté ;migration107.
    situation_familiale = Column(String(20), default="celiba")  # celiba|marie|veuf|divorce
    nb_enfants    = Column(Integer, default=0)
    date_embauche = Column(Date)
    matricule = Column(String(50))
    numero_cnss = Column(String(50))
    type_contrat = Column(String(20), nullable=True)
    date_sortie = Column(Date)
    email = Column(String(254))
    telephone = Column(String(50))
    personnes_charge_ir = Column(Integer, nullable=True)
    actif         = Column(Boolean, default=True)
    created_at    = Column(DateTime, server_default=func.now())

    societe       = relationship("Societe", back_populates="employes")

    __table_args__ = (UniqueConstraint('id', 'societe_id', name='uq_employes_id_societe'),)


class AbsenceRH(Base):
    __tablename__ = 'grh_absences'
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer, ForeignKey('societes.id'), nullable=False, index=True)
    employe_id = Column(Integer, nullable=False, index=True)
    type_absence = Column(String(20), nullable=False)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    motif = Column(String(1000))
    statut = Column(String(20), nullable=False, default='demande')
    commentaire_decision = Column(String(1000))
    created_by = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    decided_by = Column(Integer, ForeignKey('utilisateurs.id'))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    decided_at = Column(DateTime)
    __table_args__ = (
        UniqueConstraint('id','societe_id',name='uq_grh_absences_id_societe'),
        ForeignKeyConstraint(['employe_id','societe_id'],['employes.id','employes.societe_id']),
        CheckConstraint("date_fin >= date_debut", name='ck_grh_absences_dates'),
        CheckConstraint("type_absence IN ('conge','absence','autre')",name='ck_grh_absences_type'),
        CheckConstraint("statut IN ('demande','approuve','refuse','annule')",name='ck_grh_absences_statut'),
    )


class EvenementAbsenceRH(Base):
    __tablename__ = 'grh_absence_evenements'
    id = Column(Integer, primary_key=True)
    absence_id = Column(Integer, nullable=False, index=True)
    societe_id = Column(Integer, ForeignKey('societes.id'), nullable=False, index=True)
    acteur_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    ancien_statut = Column(String(20))
    nouveau_statut = Column(String(20), nullable=False)
    commentaire = Column(String(1000))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (
        ForeignKeyConstraint(['absence_id','societe_id'],['grh_absences.id','grh_absences.societe_id']),
        CheckConstraint("nouveau_statut IN ('demande','approuve','refuse','annule')",name='ck_grh_absence_evenements_statut'),
    )


# ── Barème IR et taux cotisations ─────────────────────────────────────────────

class PaieReferentielVersion(Base):
    """Consignation des preuves partielles, sans activer une règle de paie."""
    __tablename__ = 'paie_referentiel_versions'
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer, ForeignKey('societes.id'), nullable=False, index=True)
    annee = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False)
    empreinte = Column(String(64), nullable=False)
    parametres = Column(JSON, nullable=False)
    sources = Column(JSON, nullable=False)
    regime = Column(String(200), nullable=True)
    commentaire = Column(String(2000), nullable=True)
    qualification = Column(String(30), nullable=False)
    created_by = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint('societe_id', 'annee', 'version', name='uq_paie_referentiel_version'),
        CheckConstraint('version > 0', name='ck_paie_referentiel_version'),
        CheckConstraint('annee BETWEEN 2025 AND 2100', name='ck_paie_referentiel_annee'),
        CheckConstraint("qualification IN ('non_verifie','preuves_partielles')", name='ck_paie_referentiel_qualification'),
    )


class BaremeIR(Base):
    __tablename__ = "bareme_ir"

    id           = Column(Integer, primary_key=True, index=True)
    annee        = Column(Integer, nullable=False, index=True)
    tranche_min  = Column(Float, nullable=False)   # revenu annuel min (MAD)
    tranche_max  = Column(Float, nullable=True)    # null = pas de plafond
    taux         = Column(Float, nullable=False)   # ex: 0.10 pour 10%
    deduction    = Column(Float, default=0.0)      # déduction fixe MAD/an


class TauxCotisation(Base):
    __tablename__ = "taux_cotisations"

    id           = Column(Integer, primary_key=True, index=True)
    annee        = Column(Integer, nullable=False, index=True)
    code         = Column(String(50), nullable=False)   # ex: cnss_retraite_sal
    libelle      = Column(String(200))
    taux_sal     = Column(Float, default=0.0)   # part salariale
    taux_pat     = Column(Float, default=0.0)   # part patronale
    plafond      = Column(Float, nullable=True) # plafond annuel (null = pas de plafond)


class DeductionIR(Base):
    __tablename__ = "deductions_ir"

    id           = Column(Integer, primary_key=True, index=True)
    annee        = Column(Integer, nullable=False, index=True)
    code         = Column(String(50), nullable=False)  # conjoint | enfant | retraite
    libelle      = Column(String(200))
    montant_an   = Column(Float, nullable=False)       # montant annuel MAD
    max_beneficiaires = Column(Integer, nullable=True) # ex: 6 pour les enfants


# ── Modules et société étendue ────────────────────────────────────────────────

class ModuleActif(Base):
    __tablename__ = "modules_actifs"

    id         = Column(Integer, primary_key=True, index=True)
    societe_id = Column(Integer, ForeignKey("societes.id"), nullable=False)
    module     = Column(String(50), nullable=False)  # facturation | comptabilite | paie_grh
    actif      = Column(Boolean, default=True)
    date_activation = Column(DateTime, server_default=func.now())

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('societe_id', 'module'),
    )


# ── Tiers (Clients / Fournisseurs) ────────────────────────────────────────────

class Tiers(Base):
    __tablename__ = "tiers"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    type            = Column(String(20), nullable=False)  # client | fournisseur | les_deux
    nom             = Column(String(200), nullable=False, index=True)
    ice             = Column(String(20))
    identifiant_fiscal = Column(String(50))
    rc              = Column(String(50))
    adresse         = Column(Text)
    ville           = Column(String(100))
    telephone       = Column(String(20))
    email           = Column(String(100))
    # FACT-B — permet de distinguer les mentions attendues pour un client B2B
    # de celles d'un particulier sans imposer un ICE aux ventes B2C.
    categorie_fiscale = Column(String(20), default="professionnel", nullable=False)  # professionnel | autoentrepreneur | particulier | indetermine
    # Comptable
    compte_client      = Column(String(10), default="3421")
    compte_fournisseur = Column(String(10), default="4411")
    # COMPTA-AUX : identifiants auxiliaires stables, distincts du compte collectif.
    # Ils sont générés automatiquement et figés sur les lignes comptables/FEC.
    code_aux_client      = Column(String(20), nullable=True)
    code_aux_fournisseur = Column(String(20), nullable=True)
    # TVA / RAS
    assujetti_tva   = Column(Boolean, default=True)
    taux_ras        = Column(Float, nullable=True)  # ex: 0.10 pour 10%
    # Délai de paiement (jours)
    delai_paiement  = Column(Integer, default=60)
    plafond_credit  = Column(Float, default=0.0)   # encours maximum autorisé (0 = illimité)
    actif           = Column(Boolean, default=True)
    created_at      = Column(DateTime, server_default=func.now())


# ── Modèles d'écritures (contreparties automatiques) ──────────────────────────

class ModeleEcriture(Base):
    __tablename__ = "modeles_ecritures"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(50), unique=True, nullable=False)  # ex: achat_marchandises
    libelle     = Column(String(200), nullable=False)
    journal             = Column(String(5), default="AC")
    description         = Column(Text)
    compte_declencheur  = Column(String(10), nullable=True, index=True)
    libelle_auto        = Column(String(255), nullable=True)
    actif               = Column(Boolean, default=True)

    lignes      = relationship("LigneModele", back_populates="modele",
                               cascade="all, delete-orphan",
                               order_by="LigneModele.ordre")


class LigneModele(Base):
    __tablename__ = "lignes_modele"

    id          = Column(Integer, primary_key=True, index=True)
    modele_id   = Column(Integer, ForeignKey("modeles_ecritures.id", ondelete="CASCADE"))
    ordre       = Column(Integer, default=0)
    compte      = Column(String(10), nullable=False)
    libelle     = Column(String(200))
    # Rôle de la ligne : charge | tva_recup | tva_collect | contrepartie | libre
    role        = Column(String(20), default="libre")
    # Sens par défaut : debit | credit
    sens        = Column(String(6), default="debit")
    # Formule : montant_ht | montant_tva | montant_ttc | saisie
    formule     = Column(String(30), default="saisie")
    # Taux TVA si applicable
    taux_tva       = Column(Float, nullable=True)
    est_principal  = Column(Boolean, default=False, nullable=False)
    est_tva        = Column(Boolean, default=False, nullable=False)

    modele      = relationship("ModeleEcriture", back_populates="lignes")


# ── Modèles d'écritures (contreparties automatiques) ─────────────────────────



class UtilisateurSociete(Base):
    __tablename__ = "utilisateurs_societes"

    id              = Column(Integer, primary_key=True, index=True)
    utilisateur_id  = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    role            = Column(String(20), default="comptable")
    actif           = Column(Boolean, default=True)
    created_at      = Column(DateTime, server_default=func.now())

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('utilisateur_id', 'societe_id'),
        CheckConstraint("role IN ('admin','comptable','lecture','personnel')", name="ck_utilisateurs_societes_role_hisabpro"),
    )


# ── Familles d'articles ───────────────────────────────────────────────────────

class FamilleArticle(Base):
    __tablename__ = "familles_articles"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    code            = Column(String(20), nullable=False)
    libelle         = Column(String(200), nullable=False)
    tva_defaut      = Column(Float, default=20.0)      # taux TVA par défaut
    compte_vente    = Column(String(10), default="7111") # compte CA
    compte_achat    = Column(String(10), default="6111") # compte charge
    # Comptabilité des stocks en inventaire intermittent (CGNC).
    # Le stock final est rapproché du compte 31xx ; l'écart transite par 6114.
    compte_stock    = Column(String(10), default="3111")
    compte_variation_stock = Column(String(10), default="6114")
    actif           = Column(Boolean, default=True)
    created_at      = Column(DateTime, server_default=func.now())

    articles        = relationship("Article", back_populates="famille",
                                   cascade="all, delete-orphan")


# ── Articles ──────────────────────────────────────────────────────────────────

class Article(Base):
    __tablename__ = "articles"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    famille_id      = Column(Integer, ForeignKey("familles_articles.id"), nullable=True)
    code            = Column(String(50), nullable=False, index=True)
    designation     = Column(String(300), nullable=False)
    description     = Column(Text, nullable=True)
    prix_vente_ht   = Column(Float, default=0.0)
    prix_achat_ht   = Column(Float, default=0.0)
    tva             = Column(Float, default=20.0)      # taux TVA en %
    unite           = Column(String(20), default="unité") # unité, kg, m², heure...
    code_barre      = Column(String(100), nullable=True, index=True)
    stock_actuel    = Column(Float, default=0.0)
    emplacement     = Column(String(200), nullable=True)  # ex: Magasin central, Entrepôt B
    is_stockable    = Column(Boolean, default=True)       # False = service, logiciel, frais...
    stock_min       = Column(Float, default=0.0)          # seuil de réapprovisionnement (alerte)
    cmup            = Column(Float, default=0.0)          # coût moyen unitaire pondéré (valorisation du stock)
    frais_emballage = Column(Float, default=0.0)          # frais d'emballage par unité
    frais_transport = Column(Float, default=0.0)          # frais de transport par unité
    # COMPTA.1 — surcharge facultative des comptes de la famille.
    compte_vente    = Column(String(10), nullable=True)
    compte_achat    = Column(String(10), nullable=True)
    actif           = Column(Boolean, default=True)
    created_at      = Column(DateTime, server_default=func.now())

    famille         = relationship("FamilleArticle", back_populates="articles")


# ── Mouvements de stock ───────────────────────────────────────────────────────

class MouvementStock(Base):
    __tablename__ = "mouvements_stock"

    id          = Column(Integer, primary_key=True, index=True)
    societe_id  = Column(Integer, ForeignKey("societes.id"), nullable=False)
    article_id  = Column(Integer, ForeignKey("articles.id"), nullable=False)
    type        = Column(String(20), nullable=False)  # entree | sortie | correction
    quantite    = Column(Float, nullable=False)        # toujours positif
    stock_avant = Column(Float, nullable=False)
    stock_apres = Column(Float, nullable=False)
    reference   = Column(String(100), nullable=True)

    # Valorisation figée au moment du mouvement.
    cout_unitaire = Column(Float, default=0.0)
    cmup_avant    = Column(Float, nullable=True)
    cmup_apres    = Column(Float, default=0.0)

    # Date métier + origine. ``created_at`` reste la date technique d'insertion.
    date_mouvement   = Column(Date, nullable=False, server_default=func.current_date(), index=True)
    source_type      = Column(String(40), nullable=True, index=True)
    source_id        = Column(Integer, nullable=True, index=True)
    source_ligne_id  = Column(Integer, nullable=True)
    cle_idempotence  = Column(String(180), nullable=True)
    cree_par         = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)

    # Une annulation ne détruit jamais le mouvement d'origine : elle crée un
    # mouvement compensatoire qui pointe vers lui.
    annule_mouvement_id = Column(Integer, ForeignKey("mouvements_stock.id"), nullable=True, index=True)

    facture_id  = Column(Integer, ForeignKey("factures.id"), nullable=True)
    note        = Column(String(300), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())

    article     = relationship("Article")


# ── Inventaires physiques de stock ───────────────────────────────────────────

class InventaireStock(Base):
    """Photographie validée d'un comptage physique.

    Contrairement à ``Article.stock_actuel`` qui représente l'état courant, cette
    table conserve la situation réellement constatée à une date donnée. Elle sert
    de base à la comptabilisation du stock final et au Livre d'inventaire.
    """
    __tablename__ = "inventaires_stock"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False, index=True)
    exercice        = Column(Integer, nullable=False, index=True)
    date_inventaire = Column(Date, nullable=False, index=True)
    reference       = Column(String(100), nullable=False)
    note            = Column(String(500), nullable=True)
    total_valeur    = Column(Numeric(18, 2), nullable=False, default=0)
    total_perte     = Column(Numeric(18, 2), nullable=False, default=0)
    total_excedent  = Column(Numeric(18, 2), nullable=False, default=0)
    ecriture_stock_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    cree_par        = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    validee_le      = Column(DateTime, server_default=func.now(), nullable=False)

    lignes = relationship("InventaireStockLigne", back_populates="inventaire", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("societe_id", "reference", name="uq_inventaire_stock_societe_reference"),
    )


class InventaireStockLigne(Base):
    __tablename__ = "inventaires_stock_lignes"

    id                = Column(Integer, primary_key=True, index=True)
    inventaire_id     = Column(Integer, ForeignKey("inventaires_stock.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id        = Column(Integer, ForeignKey("articles.id"), nullable=False)
    code              = Column(String(50), nullable=False)
    designation       = Column(String(300), nullable=False)
    quantite_theorique = Column(Numeric(18, 4), nullable=False, default=0)
    quantite_reelle    = Column(Numeric(18, 4), nullable=False, default=0)
    ecart_quantite     = Column(Numeric(18, 4), nullable=False, default=0)
    cmup               = Column(Numeric(18, 4), nullable=False, default=0)
    valeur_stock       = Column(Numeric(18, 2), nullable=False, default=0)
    valeur_ecart       = Column(Numeric(18, 2), nullable=False, default=0)
    compte_stock       = Column(String(10), nullable=False, default="3111")
    compte_variation   = Column(String(10), nullable=False, default="6114")

    inventaire = relationship("InventaireStock", back_populates="lignes")
    article = relationship("Article")

    __table_args__ = (
        UniqueConstraint("inventaire_id", "article_id", name="uq_inventaire_stock_ligne_article"),
        CheckConstraint("quantite_reelle >= 0", name="ck_inventaire_stock_qte_reelle_non_negative"),
    )


# ── Cycle commercial ──────────────────────────────────────────────────────────

class StatutDevisEnum(str, enum.Enum):
    brouillon = "brouillon"
    envoye    = "envoye"
    accepte   = "accepte"
    refuse    = "refuse"
    expire    = "expire"

class StatutBCEnum(str, enum.Enum):
    en_attente  = "en_attente"
    confirme    = "confirme"
    livre       = "livre"
    annule      = "annule"

class StatutBLEnum(str, enum.Enum):
    en_preparation = "en_preparation"
    expedie        = "expedie"
    livre          = "livre"
    retourne       = "retourne"

class StatutReglementEnum(str, enum.Enum):
    en_attente = "en_attente"
    partiel    = "partiel"
    complet    = "complet"
    annule     = "annule"

class ModeReglementEnum(str, enum.Enum):
    virement  = "virement"
    cheque    = "cheque"
    especes   = "especes"
    effet     = "effet"
    autre     = "autre"


# ── Devis ─────────────────────────────────────────────────────────────────────

class Devis(Base):
    __tablename__ = "devis"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    numero          = Column(String(50), nullable=False)
    date            = Column(Date, nullable=False, index=True)
    exercice        = Column(Integer, nullable=False, index=True)
    tiers           = Column(String(200), nullable=False)
    tiers_id        = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    reference       = Column(String(100))
    validite_jours  = Column(Integer, default=30)
    statut          = Column(String(20), default="brouillon")
    notes           = Column(Text)
    societe_snapshot_json = Column(Text, nullable=True)
    tiers_snapshot_json = Column(Text, nullable=True)
    notes_snapshot = Column(Text, nullable=True)
    facture_id      = Column(Integer, ForeignKey("factures.id"), nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    lignes          = relationship("LigneDevis", back_populates="devis",
                                   cascade="all, delete-orphan")
    bons_commande   = relationship("BonCommande", back_populates="devis")


class LigneDevis(Base):
    __tablename__ = "lignes_devis"

    id            = Column(Integer, primary_key=True, index=True)
    devis_id      = Column(Integer, ForeignKey("devis.id", ondelete="CASCADE"), nullable=False)
    article_id    = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    description   = Column(String(300), nullable=False)
    quantite      = Column(Float, default=1.0)
    prix_unitaire = Column(Float, nullable=False, default=0.0)
    tva           = Column(Float, default=20.0)
    qualification_tva = Column(String(40), default="taxable", nullable=False)

    devis         = relationship("Devis", back_populates="lignes")

    @property
    def montant_ht(self):  return self.quantite * self.prix_unitaire
    @property
    def montant_tva(self): return self.montant_ht * (self.tva / 100)
    @property
    def montant_ttc(self): return self.montant_ht + self.montant_tva


# ── Bon de commande ───────────────────────────────────────────────────────────

class BonCommande(Base):
    __tablename__ = "bons_commande"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    devis_id        = Column(Integer, ForeignKey("devis.id"), nullable=True)
    facture_id      = Column(Integer, ForeignKey("factures.id"), nullable=True)
    numero          = Column(String(50), nullable=False)
    type            = Column(String(10), default="vente")  # vente | achat
    date            = Column(Date, nullable=False, index=True)
    exercice        = Column(Integer, nullable=False, index=True)
    tiers           = Column(String(200), nullable=False)
    tiers_id        = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    reference       = Column(String(100))
    date_livraison  = Column(Date, nullable=True)
    statut          = Column(String(20), default="en_attente")
    notes           = Column(Text)
    societe_snapshot_json = Column(Text, nullable=True)
    tiers_snapshot_json = Column(Text, nullable=True)
    notes_snapshot = Column(Text, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    lignes          = relationship("LigneBonCommande", back_populates="bon_commande",
                                   cascade="all, delete-orphan")
    devis           = relationship("Devis", back_populates="bons_commande")
    bons_livraison  = relationship("BonLivraison", back_populates="bon_commande")


class LigneBonCommande(Base):
    __tablename__ = "lignes_bon_commande"

    id              = Column(Integer, primary_key=True, index=True)
    bon_commande_id = Column(Integer, ForeignKey("bons_commande.id", ondelete="CASCADE"), nullable=False)
    article_id      = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    source_ligne_devis_id = Column(Integer, ForeignKey("lignes_devis.id", ondelete="SET NULL"), nullable=True, index=True)
    description     = Column(String(300), nullable=False)
    quantite        = Column(Float, default=1.0)
    prix_unitaire   = Column(Float, nullable=False, default=0.0)
    # Les conditions commerciales suivent la ligne jusqu'à la facture.
    tva             = Column(Float, nullable=False, default=20.0)
    qualification_tva = Column(String(40), default="taxable", nullable=False)
    remise          = Column(Float, nullable=False, default=0.0)
    remise2         = Column(Float, nullable=False, default=0.0)
    rabais          = Column(Float, nullable=False, default=0.0)

    bon_commande    = relationship("BonCommande", back_populates="lignes")

    @property
    def montant_ht(self): return self.quantite * self.prix_unitaire


# ── Bon de livraison ──────────────────────────────────────────────────────────

class BonLivraison(Base):
    __tablename__ = "bons_livraison"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    bon_commande_id = Column(Integer, ForeignKey("bons_commande.id"), nullable=True)
    facture_id      = Column(Integer, ForeignKey("factures.id"), nullable=True)
    numero          = Column(String(50), nullable=False)
    type            = Column(String(10), default="vente")  # vente (livraison) | achat (réception)
    date            = Column(Date, nullable=False, index=True)
    exercice        = Column(Integer, nullable=False, index=True)
    tiers           = Column(String(200), nullable=False)
    tiers_id        = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    transporteur    = Column(String(200), nullable=True)
    statut          = Column(String(30), default="en_preparation")
    notes           = Column(Text)
    societe_snapshot_json = Column(Text, nullable=True)
    tiers_snapshot_json = Column(Text, nullable=True)
    notes_snapshot = Column(Text, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    lignes          = relationship("LigneBonLivraison", back_populates="bon_livraison",
                                   cascade="all, delete-orphan")
    bon_commande    = relationship("BonCommande", back_populates="bons_livraison")


class LigneBonLivraison(Base):
    __tablename__ = "lignes_bon_livraison"

    id                = Column(Integer, primary_key=True, index=True)
    bon_livraison_id  = Column(Integer, ForeignKey("bons_livraison.id", ondelete="CASCADE"), nullable=False)
    article_id        = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    source_ligne_bc_id = Column(Integer, ForeignKey("lignes_bon_commande.id", ondelete="SET NULL"), nullable=True, index=True)
    description       = Column(String(300), nullable=False)
    quantite_prevue   = Column(Float, default=1.0)
    quantite_livree   = Column(Float, default=1.0)
    # Snapshot commercial nécessaire si la facture est générée après le BL/BR.
    prix_unitaire     = Column(Float, nullable=False, default=0.0)
    tva               = Column(Float, nullable=False, default=20.0)
    qualification_tva = Column(String(40), default="taxable", nullable=False)
    remise            = Column(Float, nullable=False, default=0.0)
    remise2           = Column(Float, nullable=False, default=0.0)
    rabais            = Column(Float, nullable=False, default=0.0)

    bon_livraison     = relationship("BonLivraison", back_populates="lignes")


# ── Règlement ─────────────────────────────────────────────────────────────────

class Reglement(Base):
    __tablename__ = "reglements"
    __table_args__ = (
        CheckConstraint(
            "statut NOT IN ('encaisse', 'paye') OR date_encaissement IS NOT NULL",
            name="ck_reglements_statut_date_effective",
        ),
    )

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id"), nullable=False)
    facture_id    = Column(Integer, ForeignKey("factures.id"), nullable=True)
    tiers_id      = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    numero        = Column(String(50), nullable=True)
    date          = Column(Date, nullable=False, index=True)
    tiers         = Column(String(200), nullable=False)
    montant       = Column(Float, nullable=False)
    mode          = Column(String(20), default="virement")  # virement|cheque|especes|effet|autre
    reference     = Column(String(100), nullable=True)      # N° chèque, virement...
    banque        = Column(String(100), nullable=True)
    date_echeance = Column(Date, nullable=True)             # échéance (effets et chèques post-datés)
    # Date de paiement/encaissement fiscal effectif. Pour un chèque/effet client,
    # elle est renseignée lors de la transition « encaisser ».
    date_encaissement = Column(Date, nullable=True, index=True)
    statut        = Column(String(20), default="complet")
    est_comptabilisee = Column(Boolean, default=False)      # écriture d'encaissement générée
    # FACT-H — lien explicite vers l'écriture source et sa contrepassation.
    # Il permet de corriger un règlement erroné sans supprimer l'historique.
    ecriture_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    ecriture_annulation_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    date_annulation = Column(DateTime, nullable=True)
    # Date comptable de l'annulation (migration 127) : la TVA sur encaissements
    # des périodes antérieures n'est pas réécrite.
    date_annulation_effective = Column(Date, nullable=True)
    # Date de l'impayé (127). Un rejet après encaissement garde date_encaissement.
    date_rejet_effective = Column(Date, nullable=True)
    annulee_par = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    notes         = Column(Text, nullable=True)
    code_lettrage  = Column(String(10), nullable=True, index=True)
    created_at    = Column(DateTime, server_default=func.now())

    facture       = relationship("Facture")


# ── Comptes bancaires ─────────────────────────────────────────────────────────

class CompteBancaire(Base):
    __tablename__ = "comptes_bancaires"

    id              = Column(Integer, primary_key=True, index=True)
    societe_id      = Column(Integer, ForeignKey("societes.id"), nullable=False)
    banque          = Column(String(100), nullable=False)   # ex: Banque Populaire
    agence          = Column(String(100), nullable=True)    # ex: Agence Hay Riad
    rib             = Column(String(50), nullable=True)
    iban            = Column(String(50), nullable=True)
    devise          = Column(String(10), default="MAD")
    compte_comptable = Column(String(10), default="5141")  # compte CGNC banque
    actif           = Column(Boolean, default=True)
    created_at      = Column(DateTime, server_default=func.now())

    societe         = relationship("Societe")


# ── Rapprochement bancaire ────────────────────────────────────────────────────

class RapprochementLigne(Base):
    __tablename__ = "rapprochement_lignes"

    id                 = Column(Integer, primary_key=True, index=True)
    societe_id         = Column(Integer, ForeignKey("societes.id"), nullable=False, index=True)
    compte             = Column(String(10), nullable=False, index=True)
    date               = Column(Date, nullable=False)
    libelle            = Column(String(300), nullable=True)
    montant            = Column(Float, nullable=False)
    sens               = Column(String(10), default="debit")   # débit/crédit du relevé bancaire
    rapprochee         = Column(Boolean, default=False)
    # Legacy : conservé pour compatibilité avec les anciennes lignes importées.
    reglement_id       = Column(Integer, ForeignKey("reglements.id"), nullable=True)
    # COMPTA-FINAL : rapprochement persistant avec la ligne du compte bancaire.
    ecriture_ligne_id  = Column(Integer, ForeignKey("lignes_ecriture.id", ondelete="SET NULL"), nullable=True, index=True)
    date_rapprochement = Column(DateTime, nullable=True)
    rapproche_par      = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    created_at         = Column(DateTime, server_default=func.now())


class RapprochementEtat(Base):
    __tablename__ = "rapprochement_etats"

    id            = Column(Integer, primary_key=True, index=True)
    societe_id    = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    compte        = Column(String(10), nullable=False, index=True)
    date_debut    = Column(Date, nullable=False)
    date_fin      = Column(Date, nullable=False)
    # 048 : soldes du relevé explicités. ``solde_releve`` reste la colonne
    # historique, synchronisée avec ``solde_final`` pour compatibilité.
    solde_releve  = Column(Numeric(18, 2), nullable=True)
    solde_initial = Column(Numeric(18, 2), nullable=True)
    solde_final   = Column(Numeric(18, 2), nullable=True)
    updated_by    = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("societe_id", "compte", "date_debut", "date_fin", name="uq_rapprochement_etat_periode"),
    )


# ── Immobilisations ───────────────────────────────────────────────────────────

class MethodeAmortEnum(str, enum.Enum):
    lineaire   = "lineaire"
    degressif  = "degressif"

class Immobilisation(Base):
    __tablename__ = "immobilisations"

    id                  = Column(Integer, primary_key=True, index=True)
    societe_id          = Column(Integer, ForeignKey("societes.id"), nullable=False)
    designation         = Column(String(300), nullable=False)
    reference           = Column(String(100), nullable=True)
    categorie           = Column(String(100), nullable=True)   # Matériel, Véhicule, Logiciel...

    # Acquisition / mise en service
    date_acquisition    = Column(Date, nullable=False)
    date_mise_en_service = Column(Date, nullable=False)
    prix_acquisition_ht = Column(Numeric(18, 2), nullable=False)
    taux_tva            = Column(Numeric(5, 2), nullable=False, default=20)
    qualification_tva   = Column(String(40), nullable=False, default="taxable")
    tva_recuperable_pct = Column(Numeric(5, 2), nullable=False, default=100)
    # Valeur brute comptable = HT + part de TVA non récupérable capitalisée.
    valeur_brute        = Column(Numeric(18, 2), nullable=False)
    valeur_residuelle   = Column(Numeric(18, 2), nullable=False, default=0)
    fournisseur         = Column(String(200), nullable=True)
    # Lien métier optionnel vers le référentiel tiers. Le nom reste figé sur
    # l'immobilisation pour conserver une trace lisible même si le tiers change.
    fournisseur_tiers_id = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    date_paiement       = Column(Date, nullable=True)  # fait générateur de la déduction TVA en saisie directe
    tva_suivie_directement = Column(Boolean, nullable=False, default=True)

    # Amortissement
    amortissable        = Column(Boolean, nullable=False, default=True)
    duree_amort         = Column(Integer, nullable=True)       # années ; NULL si non amortissable
    methode             = Column(String(20), nullable=False, default="lineaire")
    taux_degressif      = Column(Numeric(8, 4), nullable=True) # coefficient 1.5 / 2 / 3
    vehicule_tourisme   = Column(Boolean, nullable=False, default=False)

    # Comptes CGNC
    compte_immo         = Column(String(10), default="2332")
    compte_amort        = Column(String(10), default="28332")
    compte_dotation     = Column(String(10), default="61933")
    compte_tva          = Column(String(10), default="34551")
    compte_fournisseur  = Column(String(10), default="4481")
    compte_reglement    = Column(String(10), default="5141")

    # Traçabilité des écritures générées
    ecriture_acquisition_id = Column(Integer, ForeignKey("ecritures.id"), nullable=True)
    ecriture_paiement_id    = Column(Integer, ForeignKey("ecritures.id"), nullable=True)

    # Sortie / cession / rebut
    date_sortie             = Column(Date, nullable=True)
    type_sortie             = Column(String(20), nullable=True)  # cession | rebut
    prix_cession_ht         = Column(Numeric(18, 2), nullable=True)
    taux_tva_cession        = Column(Numeric(5, 2), nullable=True)
    qualification_tva_cession = Column(String(40), nullable=False, default="taxable")
    regime_tva_cession      = Column(String(30), nullable=True)
    date_encaissement_cession = Column(Date, nullable=True)
    compte_produit_cession  = Column(String(10), default="7513")
    compte_vna_cession      = Column(String(10), default="6513")
    compte_creance_cession  = Column(String(10), default="3481")
    compte_tva_cession      = Column(String(10), default="4455")
    ecriture_cession_id     = Column(Integer, ForeignKey("ecritures.id"), nullable=True)
    ecriture_sortie_id      = Column(Integer, ForeignKey("ecritures.id"), nullable=True)
    ecriture_encaissement_cession_id = Column(Integer, ForeignKey("ecritures.id"), nullable=True)

    actif               = Column(Boolean, default=True)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("prix_acquisition_ht >= 0", name="ck_immo_prix_ht_non_negatif"),
        CheckConstraint("valeur_brute >= 0", name="ck_immo_valeur_brute_non_negative"),
        CheckConstraint("valeur_residuelle >= 0 AND valeur_residuelle <= valeur_brute", name="ck_immo_valeur_residuelle"),
        CheckConstraint("taux_tva >= 0 AND taux_tva <= 100", name="ck_immo_taux_tva"),
        CheckConstraint("qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')", name="ck_immo_qualification_tva_enum"),
        CheckConstraint("qualification_tva = 'taxable' OR (taux_tva = 0 AND tva_recuperable_pct = 0)", name="ck_immo_qualification_tva_coherence"),
        CheckConstraint("tva_recuperable_pct >= 0 AND tva_recuperable_pct <= 100", name="ck_immo_tva_recuperable_pct"),
        CheckConstraint("taux_tva_cession IS NULL OR (taux_tva_cession >= 0 AND taux_tva_cession <= 100)", name="ck_immo_taux_tva_cession"),
        CheckConstraint("qualification_tva_cession IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')", name="ck_immo_qualification_tva_cession_enum"),
        CheckConstraint("duree_amort IS NULL OR duree_amort > 0", name="ck_immo_duree_amort"),
        CheckConstraint("date_mise_en_service >= date_acquisition", name="ck_immo_mise_service_apres_acquisition"),
        CheckConstraint("date_paiement IS NULL OR date_paiement >= date_acquisition", name="ck_immo_paiement_apres_acquisition"),
        CheckConstraint("date_sortie IS NULL OR date_sortie >= date_mise_en_service", name="ck_immo_sortie_apres_service"),
        CheckConstraint("type_sortie IS NULL OR type_sortie IN ('cession','rebut')", name="ck_immo_type_sortie"),
        CheckConstraint("NOT amortissable OR duree_amort IS NOT NULL", name="ck_immo_amortissable_duree"),
        CheckConstraint("methode IN ('lineaire','degressif')", name="ck_immo_methode"),
        CheckConstraint("date_encaissement_cession IS NULL OR (date_sortie IS NOT NULL AND date_encaissement_cession >= date_sortie)", name="ck_immo_encaissement_cession"),
    )

    societe             = relationship("Societe")
    fournisseur_tiers   = relationship("Tiers", foreign_keys=[fournisseur_tiers_id])


# ── Acomptes / avances ────────────────────────────────────────────────────────

class Acompte(Base):
    """Acompte reçu d'un client ou versé à un fournisseur, imputable sur une facture."""
    __tablename__ = "acomptes"

    id                 = Column(Integer, primary_key=True, index=True)
    societe_id         = Column(Integer, ForeignKey("societes.id"), nullable=False)
    numero             = Column(String(50), nullable=False)
    type               = Column(String(20), default="client")      # client | fournisseur
    tiers              = Column(String(200), nullable=False)
    tiers_id           = Column(Integer, ForeignKey("tiers.id", ondelete="SET NULL"), nullable=True, index=True)
    compte_tiers_snapshot = Column(String(10), nullable=True)
    date               = Column(Date, nullable=False, index=True)
    exercice           = Column(Integer, nullable=False, index=True)
    montant            = Column(Float, default=0.0)  # montant TTC encaissé/versé
    # Un acompte client est un encaissement taxable lorsqu'il se rattache à une
    # opération soumise à TVA. Le taux est figé sur l'acompte. Pour les acomptes
    # fournisseurs, la déduction n'est prise qu'une fois l'acompte imputé sur une
    # facture justificative.
    tva_applicable     = Column(Boolean, default=True)
    taux_tva           = Column(Numeric(5, 2), default=20)
    qualification_tva  = Column(String(40), nullable=False, default="taxable")
    mode               = Column(String(20), default="virement")    # virement | cheque | especes | effet | carte | prelevement | autre
    banque             = Column(String(100), nullable=True)
    compte_bancaire_id = Column(Integer, ForeignKey("comptes_bancaires.id", ondelete="SET NULL"), nullable=True, index=True)
    reference          = Column(String(100), nullable=True)
    date_echeance      = Column(Date, nullable=True)
    statut_paiement    = Column(String(20), default="encaisse", nullable=False)  # en_attente | encaisse | rejete
    date_encaissement  = Column(Date, nullable=True)
    statut             = Column(String(20), default="disponible")  # disponible | partiellement_impute | impute | annule
    facture_id         = Column(Integer, ForeignKey("factures.id"), nullable=True)
    date_imputation    = Column(Date, nullable=True)
    est_comptabilisee  = Column(Boolean, default=False)            # écriture d'encaissement générée
    est_imputee_compta = Column(Boolean, default=False)            # écriture d'imputation générée
    notes              = Column(Text, nullable=True)
    # FACT-C — annulation métier traçable. Une avance comptabilisée n'est jamais
    # supprimée : elle est compensée par une écriture inverse sur une période ouverte.
    date_annulation    = Column(DateTime, nullable=True)
    annule_par         = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    ecriture_annulation_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    created_at         = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("qualification_tva IN ('taxable','exonere_droit_deduction','exonere_sans_deduction','hors_champ','suspension')", name="ck_acomptes_qualification_tva_enum"),
        CheckConstraint("(qualification_tva = 'taxable' AND taux_tva > 0 AND tva_applicable) OR (qualification_tva <> 'taxable' AND taux_tva = 0 AND NOT tva_applicable)", name="ck_acomptes_tva_coherence"),
    )

    societe            = relationship("Societe")
    facture            = relationship("Facture")
    compte_bancaire    = relationship("CompteBancaire", foreign_keys=[compte_bancaire_id])
    imputations        = relationship("ImputationAcompte", back_populates="acompte", cascade="all, delete-orphan")


class EcheanceFacture(Base):
    """Tranche contractuelle d'un échéancier de facture (FACT.8)."""
    __tablename__ = "echeances_facture"

    id             = Column(Integer, primary_key=True, index=True)
    societe_id     = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    facture_id     = Column(Integer, ForeignKey("factures.id", ondelete="CASCADE"), nullable=False, index=True)
    ordre          = Column(Integer, nullable=False)
    date_echeance  = Column(Date, nullable=False, index=True)
    montant        = Column(Numeric(18, 2), nullable=False)
    libelle        = Column(String(120), nullable=True)
    created_at     = Column(DateTime, server_default=func.now(), nullable=False)

    facture = relationship("Facture", back_populates="echeances")

    __table_args__ = (
        CheckConstraint("ordre > 0", name="ck_echeance_facture_ordre"),
        CheckConstraint("montant > 0", name="ck_echeance_facture_montant"),
        UniqueConstraint("facture_id", "ordre", name="uq_echeance_facture_ordre"),
    )


class ImputationAcompte(Base):
    """Imputation partielle d'un acompte sur une facture (FACT.8)."""
    __tablename__ = "imputations_acomptes"

    id                 = Column(Integer, primary_key=True, index=True)
    societe_id         = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    acompte_id         = Column(Integer, ForeignKey("acomptes.id", ondelete="RESTRICT"), nullable=False, index=True)
    facture_id         = Column(Integer, ForeignKey("factures.id", ondelete="RESTRICT"), nullable=False, index=True)
    date_imputation    = Column(Date, nullable=False, default=func.current_date(), index=True)
    montant            = Column(Numeric(18, 2), nullable=False)
    est_comptabilisee  = Column(Boolean, nullable=False, default=False)
    statut             = Column(String(20), nullable=False, default="active")
    date_annulation    = Column(DateTime, nullable=True)
    annulee_par        = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    ecriture_id        = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    ecriture_annulation_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    created_at         = Column(DateTime, server_default=func.now(), nullable=False)

    acompte = relationship("Acompte", back_populates="imputations")
    facture = relationship("Facture")

    __table_args__ = (
        CheckConstraint("montant > 0", name="ck_imputation_acompte_montant"),
    )


class UtilisationAvoir(Base):
    """Affectation du crédit excédentaire d'un avoir (FACT-G)."""
    __tablename__ = "utilisations_avoirs"

    id                     = Column(Integer, primary_key=True, index=True)
    societe_id             = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    avoir_id               = Column(Integer, ForeignKey("avoirs.id", ondelete="RESTRICT"), nullable=False, index=True)
    type_utilisation       = Column(String(20), nullable=False)
    facture_id             = Column(Integer, ForeignKey("factures.id", ondelete="RESTRICT"), nullable=True, index=True)
    date_utilisation       = Column(Date, nullable=False, index=True)
    date_acceptation_compensation = Column(Date, nullable=True)
    date_annulation_effective = Column(Date, nullable=True)
    montant                = Column(Numeric(18, 2), nullable=False)
    mode                   = Column(String(20), nullable=True)
    compte_bancaire_id     = Column(Integer, ForeignKey("comptes_bancaires.id", ondelete="SET NULL"), nullable=True)
    banque                 = Column(String(100), nullable=True)
    reference              = Column(String(100), nullable=True)
    ecriture_id            = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    statut                 = Column(String(20), nullable=False, default="active")
    date_annulation        = Column(DateTime, nullable=True)
    annulee_par            = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    ecriture_annulation_id = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    created_at             = Column(DateTime, server_default=func.now(), nullable=False)

    avoir                  = relationship("Avoir")
    facture                = relationship("Facture")
    compte_bancaire        = relationship("CompteBancaire")

    __table_args__ = (
        CheckConstraint("type_utilisation IN ('imputation','remboursement')", name="ck_utilisations_avoirs_type_factg"),
        CheckConstraint("statut IN ('active','annulee')", name="ck_utilisations_avoirs_statut_factg"),
        CheckConstraint("montant > 0", name="ck_utilisations_avoirs_montant_factg"),
        CheckConstraint("date_acceptation_compensation IS NULL OR (type_utilisation='imputation' AND date_acceptation_compensation=date_utilisation AND reference IS NOT NULL AND length(trim(reference))>0)", name="ck_utilisations_compensation126"),
        CheckConstraint("(type_utilisation = 'imputation' AND facture_id IS NOT NULL) OR type_utilisation = 'remboursement'", name="ck_utilisations_avoirs_facture_factg"),
    )


class RelanceRecouvrement(Base):
    """Historique des relances clients liées à une facture (FACT.7)."""
    __tablename__ = "relances_recouvrement"

    id                       = Column(Integer, primary_key=True, index=True)
    societe_id               = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    facture_id               = Column(Integer, ForeignKey("factures.id", ondelete="RESTRICT"), nullable=False, index=True)
    niveau                   = Column(Integer, nullable=False, default=1)
    date_relance             = Column(Date, nullable=False, default=func.current_date())
    canal                    = Column(String(20), nullable=False, default="email")
    commentaire              = Column(Text, nullable=True)
    date_promesse_reglement  = Column(Date, nullable=True)
    montant_promis           = Column(Numeric(18, 2), nullable=True)
    prochaine_relance        = Column(Date, nullable=True, index=True)
    statut                   = Column(String(20), nullable=False, default="effectuee")
    created_by               = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    created_at               = Column(DateTime, server_default=func.now(), nullable=False)

    facture = relationship("Facture")

    __table_args__ = (
        CheckConstraint("niveau BETWEEN 1 AND 3", name="ck_relance_niveau"),
        CheckConstraint("canal IN ('email','telephone','courrier','whatsapp','autre')", name="ck_relance_canal"),
        CheckConstraint("montant_promis IS NULL OR montant_promis > 0", name="ck_relance_montant_promis"),
        CheckConstraint("statut IN ('effectuee','annulee')", name="ck_relance_statut"),
        CheckConstraint("date_promesse_reglement IS NULL OR date_promesse_reglement >= date_relance", name="ck_relance_promesse_date"),
        CheckConstraint("prochaine_relance IS NULL OR prochaine_relance > date_relance", name="ck_relance_prochaine_date"),
    )


# ── Exercices et périodes comptables ─────────────────────────────────────────

class ExerciceComptable(Base):
    """Exercice comptable d'une société.

    ``annee`` reste la clé de compatibilité utilisée par les modules historiques
    de HisabPro et désigne l'année de clôture de l'exercice. Les dates réelles
    restent la source de vérité pour l'affichage et les contrôles de période.
    """
    __tablename__ = "exercices_comptables"

    id          = Column(Integer, primary_key=True, index=True)
    societe_id  = Column(Integer, ForeignKey("societes.id"), nullable=False, index=True)
    annee       = Column(Integer, nullable=False, index=True)
    date_debut  = Column(Date, nullable=False)
    date_fin    = Column(Date, nullable=False)
    statut      = Column(String(20), nullable=False, default="ouvert")  # a_venir | ouvert | cloture
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "annee", name="uq_exercice_societe_annee"),
        CheckConstraint("date_fin >= date_debut", name="ck_exercice_dates"),
        CheckConstraint(
            "date_fin <= ((date_debut + INTERVAL '1 year')::date - "
            "CASE WHEN EXTRACT(MONTH FROM date_debut) = 2 AND EXTRACT(DAY FROM date_debut) = 29 THEN 0 ELSE 1 END)",
            name="ck_exercice_duree_max",
        ),
        CheckConstraint("EXTRACT(YEAR FROM date_fin)::int = annee", name="ck_exercice_annee_reference_fin"),
        CheckConstraint("statut IN ('a_venir','ouvert','cloture')", name="ck_exercice_statut"),
    )

    societe     = relationship("Societe")
    periodes    = relationship("PeriodeComptable", back_populates="exercice", cascade="all, delete-orphan")


class PeriodeComptable(Base):
    """Sous-période de saisie d'un exercice, généralement mensuelle."""
    __tablename__ = "periodes_comptables"

    id             = Column(Integer, primary_key=True, index=True)
    exercice_id    = Column(Integer, ForeignKey("exercices_comptables.id", ondelete="CASCADE"), nullable=False, index=True)
    numero         = Column(Integer, nullable=False)
    libelle        = Column(String(40), nullable=False)
    date_debut     = Column(Date, nullable=False)
    date_fin       = Column(Date, nullable=False)
    statut         = Column(String(20), nullable=False, default="a_venir")  # a_venir | ouverte | fermee
    date_fermeture = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("exercice_id", "numero", name="uq_periode_exercice_numero"),
        CheckConstraint("date_fin >= date_debut", name="ck_periode_dates"),
        CheckConstraint("statut IN ('a_venir','ouverte','fermee')", name="ck_periode_statut"),
    )

    exercice       = relationship("ExerciceComptable", back_populates="periodes")


# ── Écritures d'inventaire / cut-off ─────────────────────────────────────────

class AjustementInventaire(Base):
    """Ajustement de fin d'exercice généré depuis l'assistant de clôture.

    Les CCA/PCA/FNP/FAE peuvent générer une contrepassation au 01/01/N+1.
    Les provisions et dépréciations restent au bilan jusqu'à une reprise explicite.
    """
    __tablename__ = "ajustements_inventaire"

    id                  = Column(Integer, primary_key=True, index=True)
    societe_id          = Column(Integer, ForeignKey("societes.id"), nullable=False, index=True)
    exercice            = Column(Integer, nullable=False, index=True)
    type                = Column(String(30), nullable=False)
    libelle             = Column(String(300), nullable=False)
    montant             = Column(Numeric(18, 2), nullable=False)
    compte_activite     = Column(String(10), nullable=False)
    compte_contrepartie = Column(String(10), nullable=False)
    ecriture_id         = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    contrepassation_id  = Column(Integer, ForeignKey("ecritures.id", ondelete="SET NULL"), nullable=True)
    created_at          = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("montant > 0", name="ck_ajustement_inventaire_montant_positif"),
    )

    societe             = relationship("Societe")


# ── Clôture d'exercice ────────────────────────────────────────────────────────

class ClotureExercice(Base):
    """Trace la clôture d'un exercice comptable.
    Une fois clos, l'exercice est verrouillé (plus de saisie ni de modification de
    pièces sur cette période) et les à-nouveaux sont générés sur l'exercice suivant."""
    __tablename__ = "clotures_exercice"

    id                   = Column(Integer, primary_key=True, index=True)
    societe_id           = Column(Integer, ForeignKey("societes.id"), nullable=False)
    exercice             = Column(Integer, nullable=False, index=True)  # année clôturée
    date_cloture         = Column(DateTime, server_default=func.now())
    resultat_net         = Column(Numeric(18, 2), default=0)   # bénéfice (+) ou perte (−)
    ecriture_an_id       = Column(Integer, nullable=True)  # écriture d'à-nouveaux sur N+1
    ecriture_resultat_id = Column(Integer, nullable=True)  # écriture de solde des comptes de gestion

    __table_args__ = (UniqueConstraint("societe_id", "exercice", name="uq_cloture_societe_exercice"),)

    societe              = relationship("Societe")


class DecisionAffectationResultat(Base):
    """Décision sociale immutable ayant conduit à l'affectation d'un résultat.

    La décision (AGO, associé unique ou autre organe compétent) est conservée
    séparément de l'écriture comptable afin de garder la preuve de la date, de
    la référence et des paramètres juridiques utilisés lors du contrôle.
    """
    __tablename__ = "decisions_affectation_resultat"

    id                         = Column(Integer, primary_key=True, index=True)
    societe_id                 = Column(Integer, ForeignKey("societes.id", ondelete="CASCADE"), nullable=False, index=True)
    exercice_origine           = Column(Integer, nullable=False, index=True)
    exercice_comptabilisation  = Column(Integer, nullable=False, index=True)
    date_decision              = Column(Date, nullable=False)
    date_comptabilisation      = Column(Date, nullable=False)
    reference_decision         = Column(String(120), nullable=False)
    organe_decision            = Column(String(120), nullable=False)
    forme_juridique_snapshot   = Column(String(50), nullable=True)
    capital_social_snapshot    = Column(Numeric(18, 2), nullable=False, default=0)
    resultat_origine           = Column(Numeric(18, 2), nullable=False)
    pertes_anterieures_imputees = Column(Numeric(18, 2), nullable=False, default=0)
    reserve_legale_avant       = Column(Numeric(18, 2), nullable=False, default=0)
    reserve_legale_minimale    = Column(Numeric(18, 2), nullable=False, default=0)
    reserve_legale_affectee    = Column(Numeric(18, 2), nullable=False, default=0)
    autres_reserves            = Column(Numeric(18, 2), nullable=False, default=0)
    report_a_nouveau           = Column(Numeric(18, 2), nullable=False, default=0)
    dividendes                 = Column(Numeric(18, 2), nullable=False, default=0)
    compte_source              = Column(String(10), nullable=False)
    ecriture_id                = Column(Integer, ForeignKey("ecritures.id", ondelete="RESTRICT"), nullable=False, unique=True)
    created_by                 = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    created_at                 = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice_origine", name="uq_decision_affectation_societe_exercice"),
        CheckConstraint("capital_social_snapshot >= 0", name="ck_decision_affectation_capital_non_negatif"),
        CheckConstraint("pertes_anterieures_imputees >= 0", name="ck_decision_affectation_pertes_non_negatif"),
        CheckConstraint("reserve_legale_avant >= 0 AND reserve_legale_minimale >= 0 AND reserve_legale_affectee >= 0", name="ck_decision_affectation_reserve_non_negative"),
        CheckConstraint("autres_reserves >= 0 AND report_a_nouveau >= 0 AND dividendes >= 0", name="ck_decision_affectation_ventilation_non_negative"),
    )

    societe = relationship("Societe")
    ecriture = relationship("Ecriture")


# ── Livre d'inventaire archivé ───────────────────────────────────────────────

class LivreInventaireArchive(Base):
    """Photographie immuable du livre d'inventaire d'un exercice.

    Le contenu est sérialisé en JSON canonique et accompagné d'une empreinte
    SHA-256. Une seule archive est autorisée par société/exercice.
    """
    __tablename__ = "livres_inventaire_archives"

    id                  = Column(Integer, primary_key=True, index=True)
    societe_id          = Column(Integer, ForeignKey("societes.id"), nullable=False, index=True)
    exercice            = Column(Integer, nullable=False, index=True)
    version             = Column(Integer, nullable=False, default=1)
    date_etablissement  = Column(DateTime, nullable=False, server_default=func.now())
    contenu_json        = Column(Text, nullable=False)
    empreinte_sha256    = Column(String(64), nullable=False)
    cree_par            = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    created_at          = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("societe_id", "exercice", "version", name="uq_livre_inventaire_societe_exercice_version"),
        CheckConstraint("version > 0", name="ck_livre_inventaire_version_positive"),
    )

    societe             = relationship("Societe")
