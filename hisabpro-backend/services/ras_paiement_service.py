"""Séparation de l'estimation documentaire et de l'imputation historique."""
import math
from decimal import Decimal


def lecture_ras_paiement(montant_estime, ras_comptabilisee=False, montant_capture=0):
    if montant_estime is None or not math.isfinite(float(montant_estime)):
        estime = impute = None
    else:
        estime = float(montant_estime)
        impute = estime if ras_comptabilisee is True else (float(montant_capture) if montant_capture is not None else None)
    return {'montant_ras_estime': estime, 'montant_ras_impute': impute,
            'montant_ras': impute,
            'ras_origine': 'historique_comptabilisee' if ras_comptabilisee is True else ('capture_reglement' if montant_capture is None or montant_capture > 0 else 'aucune')}


def resoudre_od_ras_historique(db, societe_id, facture, montant):
    """OD exacte unique non contrepassée ; None signale une piste incertaine."""
    import models
    from services.compta_mapping_service import compte_tiers_facture
    from sqlalchemy.orm import joinedload
    if montant is None or montant <= 0 or getattr(facture, 'ras_comptabilisee', False) is not True:
        return None
    vente = getattr(getattr(facture, 'type', None), 'value', facture.type) == 'vente'
    ref = facture.numero if vente else (facture.reference or facture.numero)
    rows = db.query(models.Ecriture).options(joinedload(models.Ecriture.lignes)).filter_by(
        societe_id=societe_id, source='reglement', journal='OD', reference=ref,
        libelle=f'Retenue à la source — {facture.numero} {facture.tiers}').all()
    if len(rows) != 1:
        return None
    e = rows[0]
    if db.query(models.Ecriture.id).filter_by(societe_id=societe_id, contrepassation_de_id=e.id).first():
        return None
    etat = '3453' if vente else '4457'
    tiers_id = getattr(facture, 'tiers_id', None)
    if tiers_id is None or len(e.lignes) != 2:
        return None
    m = Decimal(str(montant))
    collectif = compte_tiers_facture(db, societe_id, facture)
    contre = [l for l in e.lignes if l.compte == etat and
              Decimal(str(l.debit)) == (m if vente else 0) and Decimal(str(l.credit)) == (0 if vente else m)]
    tiers = [l for l in e.lignes if l.tiers_id == tiers_id and l.compte == collectif and
             Decimal(str(l.debit)) == (0 if vente else m) and Decimal(str(l.credit)) == (m if vente else 0)]
    return e if len(contre) == len(tiers) == 1 else None


def date_od_ras_historique(db, societe_id, facture, montant):
    """Date comptable de l'OD résolue, jamais une date fiscale devinée."""
    e = resoudre_od_ras_historique(db, societe_id, facture, montant)
    return e.date if e is not None else None
