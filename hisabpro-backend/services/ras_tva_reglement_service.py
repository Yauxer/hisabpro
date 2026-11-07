"""Raccordement explicite559/083 ; aucun compte ou fait fiscal présumé."""
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy import text
import models
import schemas
from services.ras_tva_simulation_service import SimulationRasTvaIn, simuler
from services.ras_reglement_service import captures_facture


class ApercuIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    simulation: SimulationRasTvaIn
    justification_quote_part: str = Field(min_length=1, max_length=200)

    @field_validator('justification_quote_part')
    @classmethod
    def reference_non_vide(cls, v):
        if not v.strip():
            raise ValueError('Référence justifiant la quote-part de TVA requise.')
        return v.strip()


class CaptureTvaIn(ApercuIn):
    reference: str = Field(min_length=1, max_length=100)
    compte_destination: str = Field(min_length=4, max_length=10)
    empreinte_apercu: str = Field(pattern=r'^[a-f0-9]{64}$')
    pieces_verifiees: StrictBool

    @field_validator('reference', 'compte_destination')
    @classmethod
    def non_vide(cls, v):
        if not v.strip():
            raise ValueError('Valeur explicite requise.')
        return v.strip()


def disponible(db):
    return hasattr(db, 'get_bind') and db.get_bind().dialect.name == 'postgresql' and bool(db.scalar(text(
        "SELECT to_regclass('public.ras_tva_reglement_details') IS NOT NULL")))


def details(db, sid, rid):
    if not disponible(db):
        return None
    return db.execute(text('''SELECT d.dossier FROM public.ras_tva_reglement_details d
        JOIN public.ras_reglement_captures c ON c.id=d.capture_id AND c.societe_id=d.societe_id
        WHERE d.societe_id=:s AND c.reglement_id=:r'''), {'s': sid, 'r': rid}).scalar()


def exiger_disponible(db):
    if not disponible(db):
        raise HTTPException(409, 'Raccordement RAS TVA indisponible : migration099 manuelle requise. Aucune migration automatique.')


def verifier_declaration_automatique(db, sid, fin):
    """Ne pas assimiler le seul cash à la base d'une opération avec RAS TVA.

    Le calcul de déclaration courant n'intègre pas encore le traitement des
    retenues opérées/subies et de leur reversement. Aucun solde fictif renvoyé.
    """
    if disponible(db) and db.scalar(text('''SELECT EXISTS(
        SELECT 1 FROM public.ras_tva_reglement_details d
        JOIN public.ras_reglement_captures c ON c.id=d.capture_id AND c.societe_id=d.societe_id
        LEFT JOIN public.ras_reglement_annulations a ON a.capture_id=c.id
        WHERE d.societe_id=:s AND c.date_operation<=:fin
        AND (a.id IS NULL OR a.date_operation>:fin))'''), {'s': sid, 'fin': fin}):
        raise HTTPException(409, 'Déclaration TVA automatique à compléter : des retenues TVA tracées concernent cette période ou son report. Leur imputation et leur reversement doivent être qualifiés ; le seul montant de trésorerie ne permet pas de calculer un solde fiable. Consultez les dossiers RAS dans les règlements.')


def montant(v):
    try:
        d = Decimal(str(v))
        if not d.is_finite() or d < 0 or d >= Decimal('1e16'):
            raise ValueError
        return d.quantize(Decimal('.01'))
    except (ValueError, TypeError, InvalidOperation):
        raise HTTPException(422, 'Montant source non fini ou non représentable ; vérifier le document.')


def faits_serialises(simulation):
    faits = simulation.model_dump(mode='json')
    for cle in ('montant_paiement_ttc', 'tva_paiement'):
        valeur = getattr(simulation, cle)
        if valeur is not None:
            faits[cle] = format(valeur, '.2f')
    return faits


def preparer(db, sid, r, f, demande):
    """Lecture de préparation ; l'écriture refait cette lecture sous verrous."""
    from routers.factures import _calc_totaux, _situation_paiement_facture
    from routers.commercial import _verifier_date_operation_ouverte
    from services.tva_service import ventilation_facture, total_ventilation
    exiger_disponible(db)
    if not f or not f.est_validee or not f.est_comptabilisee or f.est_proforma or str(getattr(f.statut, 'value', f.statut)) == 'annulee':
        raise HTTPException(409, 'Facture définitive et comptabilisée requise pour ce raccordement.')
    if r.mode not in ('virement', 'especes') or r.statut != 'complet' or not r.est_comptabilisee or not r.ecriture_id:
        raise HTTPException(409, 'Règlement immédiat comptabilisé par virement ou espèces requis.')
    if r.date > date.today() or demande.simulation.date_paiement != r.date:
        raise HTTPException(422, 'La simulation doit utiliser la date réelle du règlement source.')
    _verifier_date_operation_ouverte(db, sid, r.date, 'capture RAS TVA')
    try:
        taux_ht = Decimal(str(schemas._taux_ras_fini(f.ras_taux or 0)))
    except (ValueError, InvalidOperation):
        raise HTTPException(422, 'Taux RAS HT source invalide ; vérifier la facture.')
    # Un pourcentage ne doit pas être arrondi comme un montant au centime.
    if taux_ht != 0 or f.ras_comptabilisee:
        raise HTTPException(409, 'RAS HT ou historique présente : combinaison non couverte par ce raccordement TVA.')
    _calc_totaux(f)  # garde commune des sources historiques invalides
    totaux = total_ventilation(ventilation_facture(f, appliquer_escompte=True))
    ttc, tva = montant(totaux['ttc']), montant(totaux['tva'])
    situation = _situation_paiement_facture(db, sid, f)
    if any(situation.get(k, 0) for k in ('total_avoirs', 'total_acomptes', 'total_avoirs_imputes')):
        raise HTTPException(409, 'Avoir ou acompte affecté : ventilation spécifique à traiter séparément.')
    calcul = simuler(demande.simulation)
    if calcul['statut'] != 'calcule' or montant(calcul['retenue_tva']) <= 0:
        raise HTTPException(422, 'Une simulation positive complète du périmètre117-V-b est requise : ' + ' '.join(calcul['motifs']))
    cash = montant(r.montant)
    if montant(calcul['net_apres_cette_ras_tva']) != cash:
        raise HTTPException(409, 'Le net après cette seule RAS TVA ne correspond pas au montant réel du règlement.')
    if f.tiers_id is None:
        raise HTTPException(409, 'Tiers source explicite requis.')
    caps = {c['reglement_id']: c for c in captures_facture(db, sid, f.id) if c['annulation_id'] is None}
    if r.id in caps:
        raise HTTPException(409, 'Ce règlement possède déjà une capture immuable.')
    quote = demande.simulation.montant_paiement_ttc
    base = demande.simulation.tva_paiement
    sources = []
    autres = db.query(models.Reglement).filter_by(societe_id=sid, facture_id=f.id).filter(
        models.Reglement.id != r.id, models.Reglement.statut.notin_(['annule', 'rejete'])).order_by(models.Reglement.id).all()
    for autre in autres:
        dossier = details(db, sid, autre.id)
        if autre.id not in caps or not dossier:
            raise HTTPException(409, 'Autre règlement sans ventilation RAS TVA tracée : quote-part historique à qualifier séparément.')
        quote += montant(dossier['faits']['montant_paiement_ttc'])
        base += montant(dossier['faits']['tva_paiement'])
        sources.append({'capture_id': caps[autre.id]['id'], 'reglement_id': autre.id,
            'quote_part_ttc': dossier['faits']['montant_paiement_ttc'],
            'quote_part_tva': dossier['faits']['tva_paiement'], 'montant_reglement': format(montant(autre.montant), '.2f'),
            'montant_capture': str(caps[autre.id]['montant'])})
    if quote > ttc or base > tva:
        raise HTTPException(409, 'Cumul des quotes-parts supérieur au TTC ou à la TVA de la facture source.')
    # Le contrôle ne répartit pas automatiquement une TVA entre plusieurs taux.
    # La référence de ventilation et les faits confirmés restent indispensables.
    source = {'societe_id': sid, 'facture_id': f.id, 'numero_facture': f.numero,
        'tiers_id': f.tiers_id, 'reglement_id': r.id, 'date_paiement': r.date.isoformat(),
        'montant_reglement': format(cash, '.2f'), 'facture_ttc': format(ttc, '.2f'),
        'facture_tva': format(tva, '.2f'), 'ecriture_reglement_id': r.ecriture_id,
        'autres_captures': sources, 'solde_avant_capture': str(situation['solde_restant'])}
    dossier = {'version_regle': calcul['version_regle'], 'faits': faits_serialises(demande.simulation),
        'justification_quote_part': demande.justification_quote_part, 'simulation': calcul, 'source': source}
    empreinte = hashlib.sha256(json.dumps(dossier, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return {'empreinte_apercu': empreinte, 'dossier': dossier,
        'limite': 'Faits et ventilation déclarés sur justificatifs. Compte explicitement choisi. OD à contrôler et valider ; aucun reversement ni dépôt généré.'}
