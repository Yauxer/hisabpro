"""Simulation117-V-b, CGI2026 TGR ; aucune qualification fiscale présumée.

Sources et périmètre : docs/audit/SOURCES_RAS_TVA_20261018.md.
Les exclusions sont justifiées par l'utilisateur, pas déduites du HT ou du nom.
Ce service pur ne génère ni pièce, ni écriture, ni déclaration déposée.
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

SOURCE = 'https://www.tgr.gov.ma/wps/wcm/connect/9856b6bb-dee8-4578-bfe8-ef1521dcc80f/CGI%2B2026%2BFR.pdf?MOD=AJPERES'
VERSION = 'CGI2026-117Vb-listeB-559'
CENT = Decimal('0.01')


class SimulationRasTvaIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date_paiement: date | None = None
    payeur: Literal['a_qualifier', 'pm_privee_assujettie', 'pp_rnr_rns_assujettie', 'autre'] = 'a_qualifier'
    prestataire: Literal['a_qualifier', 'pp_assujettie', 'autre'] = 'a_qualifier'
    prestation_liste_b: StrictBool | None = None
    exclusion: Literal['a_qualifier', 'aucune_apres_controle', 'energie_eau_reseaux',
        'assainissement_compteurs', 'telecommunications', 'courtier_assurances',
        'petites_prestations_justifiees'] = 'a_qualifier'
    reference_exclusion: str | None = Field(default=None, max_length=200)
    attestation: Literal['a_qualifier', 'presentee', 'absente'] = 'a_qualifier'
    date_attestation: date | None = None
    reference_attestation: str | None = Field(default=None, max_length=200)
    montant_paiement_ttc: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2, allow_inf_nan=False)
    tva_paiement: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2, allow_inf_nan=False)

    @field_validator('montant_paiement_ttc', 'tva_paiement', mode='before')
    @classmethod
    def montant_non_booleen(cls, v):
        if isinstance(v, bool):
            raise ValueError('Un montant ne peut pas être un booléen.')
        return v

    @model_validator(mode='after')
    def coherence_montants(self):
        if self.attestation == 'absente' and (self.date_attestation or (self.reference_attestation or '').strip()):
            raise ValueError('Une attestation déclarée absente ne peut pas avoir de date ou de référence.')
        if self.montant_paiement_ttc is not None and self.tva_paiement is not None:
            if self.tva_paiement > self.montant_paiement_ttc:
                raise ValueError('La TVA de la quote-part payée dépasse son montant TTC.')
        return self


def _six_mois_apres(d):
    mois = d.month + 6
    annee = d.year + (mois - 1) // 12
    mois = (mois - 1) % 12 + 1
    return date(annee, mois, min(d.day, monthrange(annee, mois)[1]))


def simuler(data: SimulationRasTvaIn):
    resultat = {
        'version_regle': VERSION, 'source': SOURCE,
        'statut': 'a_completer', 'motifs': [], 'taux_retenue_tva': None,
        'base_tva': None, 'retenue_tva': None, 'net_apres_cette_ras_tva': None,
        'mois_reversement': None,
        'limite': 'Simulation 2026, article117-V-b uniquement. Aucun règlement, écriture ou déclaration créé. Le net ne déduit aucune autre retenue.',
    }
    if not data.date_paiement:
        resultat['motifs'].append('Date réelle du paiement à renseigner.')
    elif data.date_paiement.year != 2026:
        resultat.update(statut='non_couvert', motifs=['Millésime hors2026 : règles à vérifier séparément.'])
        return resultat
    if data.payeur == 'autre' or data.prestataire == 'autre' or data.prestation_liste_b is False:
        resultat.update(statut='non_couvert', motifs=['Situation hors du périmètre117-V-b/listeB de cet assistant. Aucune absence de retenue ne peut en être déduite.'])
        return resultat
    if data.payeur == 'a_qualifier':
        resultat['motifs'].append('Situation du payeur à qualifier.')
    if data.prestataire == 'a_qualifier':
        resultat['motifs'].append('Prestataire personne physique assujettie à confirmer.')
    if data.prestation_liste_b is None:
        resultat['motifs'].append('Appartenance du service à la listeB à confirmer.')
    if data.exclusion == 'a_qualifier':
        resultat['motifs'].append('Exclusions de l’article117 à examiner sur justificatifs.')
    if resultat['motifs']:
        return resultat

    if data.exclusion != 'aucune_apres_controle':
        if not (data.reference_exclusion or '').strip():
            resultat['motifs'].append('Référence justifiant l’exclusion à renseigner ; aucun seuil présumé.')
        else:
            resultat.update(statut='exclu', motifs=['Exclusion déclarée et référencée ; justificatif à conserver.'],
                taux_retenue_tva='0', retenue_tva='0.00')
            if data.montant_paiement_ttc is not None:
                resultat['net_apres_cette_ras_tva'] = format(data.montant_paiement_ttc, '.2f')
        return resultat

    if data.attestation == 'a_qualifier':
        resultat['motifs'].append('Présentation de l’attestation à qualifier.')
    elif data.attestation == 'presentee':
        if not data.date_attestation or not (data.reference_attestation or '').strip():
            resultat['motifs'].append('Date et référence de l’attestation présentée à renseigner.')
        elif not (data.date_attestation <= data.date_paiement < _six_mois_apres(data.date_attestation)):
            resultat['motifs'].append('Attestation datée après le paiement ou ne datant plus de moins de six mois : revoir sa qualification.')
    if data.montant_paiement_ttc is None or data.tva_paiement is None:
        resultat['motifs'].append('Quote-part TTC payée et TVA correspondante à renseigner explicitement.')
    elif data.montant_paiement_ttc == 0:
        resultat['motifs'].append('Aucun paiement positif renseigné.')
    if resultat['motifs']:
        return resultat
    taux = Decimal('75') if data.attestation == 'presentee' else Decimal('100')
    retenue = (data.tva_paiement * taux / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    mois = data.date_paiement.month % 12 + 1
    annee = data.date_paiement.year + (data.date_paiement.month == 12)
    resultat.update(statut='calcule', taux_retenue_tva=str(taux),
        base_tva=format(data.tva_paiement, '.2f'), retenue_tva=format(retenue, '.2f'),
        net_apres_cette_ras_tva=format(data.montant_paiement_ttc - retenue, '.2f'),
        mois_reversement=f'{annee:04d}-{mois:02d}')
    return resultat
