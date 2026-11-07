"""Préparation indépendante depuis des balances, sans création d'écritures.

Le moteur des états existants est partagé. Une balance ne justifie ni les
échéances ETIC, ni les flux du financement, ni les données fiscales.
"""
from decimal import Decimal, InvalidOperation
import re
import hashlib
import hmac
import json
from sqlalchemy import func
import models

from services.liasse_service import calculer_bilan, calculer_cpc, calculer_esg


def montant_import(value, contexte):
    if value is None or value == "":
        return Decimal("0.00")
    if isinstance(value, bool):
        raise ValueError(f"{contexte} : montant invalide.")
    try:
        raw = str(value).strip().replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
        if "," in raw and "." in raw:
            raise ValueError("séparateurs ambigus")
        n = Decimal(raw.replace(",", "."))
        if not n.is_finite() or n < 0 or n > Decimal("9999999999999.99"):
            raise ValueError("montant hors limites")
        if n != n.quantize(Decimal("0.01")):
            raise ValueError("plus de deux décimales")
        return n.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{contexte} : montant positif ou nul, fini, à deux décimales requis.") from exc


def normaliser_balance(lignes, comptes_autorises, periode):
    if not isinstance(lignes, list) or not 1 <= len(lignes) <= 10000:
        raise ValueError(f"Balance {periode} : entre 1 et 10 000 lignes requises.")
    soldes = {}
    total_d = total_c = Decimal("0.00")
    for index, ligne in enumerate(lignes, 2):
        if not isinstance(ligne, dict):
            raise ValueError(f"Balance {periode}, ligne {index} : ligne invalide.")
        compte = str(ligne.get("compte", "")).strip()
        contexte = f"Balance {periode}, ligne {index} ({compte or 'compte manquant'})"
        if not re.fullmatch(r"[1-7][0-9]{3,9}", compte):
            raise ValueError(f"{contexte} : compte CGNC de classes 1 à 7 requis.")
        if compte not in comptes_autorises:
            raise ValueError(f"{contexte} : compte absent du plan de la société ; le créer explicitement avant import.")
        if compte in soldes:
            raise ValueError(f"{contexte} : compte en doublon ; fournir une balance agrégée par compte.")
        debit = montant_import(ligne.get("debit"), contexte + " débit")
        credit = montant_import(ligne.get("credit"), contexte + " crédit")
        soldes[compte] = {"debit": debit, "credit": credit}
        total_d += debit
        total_c += credit
    if total_d != total_c:
        raise ValueError(f"Balance {periode} déséquilibrée : débit {total_d}, crédit {total_c}, écart {total_d-total_c} MAD.")
    # Le résultat technique de clôture et les charges/produits ne doivent pas
    # être additionnés : exiger la balance avant leur solde dans ce cas.
    resultat = sum((v["credit"] - v["debit"] for c, v in soldes.items() if c.startswith("119")), Decimal(0))
    activite = any(v["debit"] != v["credit"] for c, v in soldes.items() if c.startswith(("6", "7")))
    if resultat and activite:
        raise ValueError(f"Balance {periode} : résultat 119 et classes 6/7 simultanés ; fournir la balance avant clôture technique ou clarifier l'affectation antérieure.")
    return soldes, {"nb_comptes": len(soldes), "total_debit": float(total_d), "total_credit": float(total_c)}


def preparer_balance_liasse(lignes_n, lignes_n1, comptes_autorises):
    soldes, total = normaliser_balance(lignes_n, comptes_autorises, "N")
    soldes_n1, total_n1 = normaliser_balance(lignes_n1, comptes_autorises, "N-1") if lignes_n1 is not None else ({}, None)
    def etats(source):
        cpc = calculer_cpc(source)
        bilan = calculer_bilan(source, cpc["resultat_net"])
        esg = calculer_esg(source)
        if abs(bilan["ecart"]) > 0.001 or esg["resultat_net"] != cpc["resultat_net"]:
            raise ValueError("Balance équilibrée mais états incohérents : vérifier les comptes non couverts ou leur classement ; aucune reclassification automatique.")
        technique = any(c.startswith('119') and v['debit'] != v['credit'] for c, v in source.items())
        activite = any(c.startswith(('6', '7')) and v['debit'] != v['credit'] for c, v in source.items())
        if technique and not activite:
            motif = 'Classes 6/7 soldées et résultat technique présent : fournir la balance avant clôture pour le CPC/ESG.'
            cpc = {'disponible': False, 'motif': motif, 'resultat_net': None, 'lignes': []}
            esg = {'disponible': False, 'motif': motif, 'resultat_net': None, 'caf': None, 'lignes': []}
        return {"bilan": bilan, "cpc": cpc, "esg": esg}
    courant = etats(soldes)
    precedent = etats(soldes_n1) if lignes_n1 is not None else None
    return {
        "mode": "balance_importee", "statut": "preparation", "pret_a_deposer": False,
        "balance_n": total, "balance_n1": total_n1, "etats": courant, "etats_n1": precedent,
        "soldes": {c: {k: float(v) for k, v in row.items()} for c, row in soldes.items()},
        "a_completer": ["ETIC et échéances sur justificatifs", "Flux du tableau de financement",
                        "Retraitements, liquidation et annexes fiscales", "Référentiel DGI et format EDI applicable"],
        "avertissements": ["Préparation indépendante : aucune écriture ni archive annuelle n'est créée.",
                            "Utiliser une balance avant solde technique des charges et produits pour établir le CPC."] +
                           ([] if precedent else ["Balance N-1 non fournie : comparatif indisponible, aucun zéro historique déduit."]),
    }


def empreinte_preparation(contenu):
    canon = json.dumps(contenu, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()


def lire_preparation(row):
    if not hmac.compare_digest(empreinte_preparation(row.contenu), row.empreinte_sha256):
        raise ValueError('Empreinte de préparation incohérente ; vérifier son intégrité avant utilisation.')
    return {'id': row.id, 'exercice': row.exercice, 'version': row.version,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'empreinte_sha256': row.empreinte_sha256, 'contenu': row.contenu}


def enregistrer_preparation(db, societe_id, exercice, lignes_n, lignes_n1, noms_sources, user_id):
    # Sérialise uniquement la numérotation de versions de cette société.
    if not db.query(models.Societe).filter_by(id=societe_id).with_for_update().first():
        raise ValueError('Société introuvable.')
    period = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id, annee=exercice).first()
    if not period:
        raise ValueError('Créer explicitement cet exercice avant de conserver une préparation.')
    comptes = {r.numero for r in db.query(models.CompteSociete).filter_by(societe_id=societe_id).all()}
    preview = preparer_balance_liasse(lignes_n, lignes_n1, comptes)
    def source(rows, name):
        if rows is None:
            return None
        balances, _ = normaliser_balance(rows, comptes, name)
        return [{'compte': c, 'debit': str(v['debit']), 'credit': str(v['credit'])}
                for c, v in sorted(balances.items())]
    contenu = {'schema_version': 1, 'exercice': exercice,
               'periode': {'debut': period.date_debut.isoformat(), 'fin': period.date_fin.isoformat()},
               'sources': {'n': source(lignes_n, 'N'), 'n1': source(lignes_n1, 'N-1'),
                           'noms_fichiers': noms_sources or {}}, 'preparation': preview}
    latest = db.query(func.max(models.LiasseBalancePreparation.version)).filter_by(
        societe_id=societe_id, exercice=exercice).scalar() or 0
    row = models.LiasseBalancePreparation(societe_id=societe_id, exercice=exercice,
        exercice_id=period.id, version=latest + 1, contenu=contenu,
        empreinte_sha256=empreinte_preparation(contenu), created_by=user_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return lire_preparation(row)
