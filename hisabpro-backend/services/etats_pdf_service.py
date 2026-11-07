# -*- coding: utf-8 -*-
"""Construction serveur des états financiers PDF officiels HisabPro.

Les montants imprimés sont toujours recalculés depuis la comptabilité en base via
``construire_liasse``. Le navigateur ne peut donc pas injecter des chiffres dans
un PDF portant l'identité HisabPro.
"""
from __future__ import annotations

from typing import Any, Dict

from services.liasse_service import construire_liasse


ETATS_AUTORISES = {
    "bilan_actif",
    "bilan_passif",
    "cpc",
    "esg",
    "tableau_financement",
}


def _n(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _total_actif(rows):
    return {
        "brut": sum(_n(r.get("brut")) for r in rows),
        "amort_prov": sum(_n(r.get("amort_prov")) for r in rows),
        "net": sum(_n(r.get("net")) for r in rows),
        "net_n1": sum(_n(r.get("net_n1")) for r in rows),
    }


def _total_passif(rows):
    return {
        "montant": sum(_n(r.get("montant")) for r in rows),
        "n1": sum(_n(r.get("n1")) for r in rows),
    }


def construire_etat_pdf_officiel(db, societe_id: int, exercice: int, etat: str,
                                  comparatif: bool = False) -> Dict[str, Any]:
    etat = str(etat or "").strip().lower()
    if etat not in ETATS_AUTORISES:
        raise ValueError("État financier PDF inconnu.")

    li = construire_liasse(db, societe_id, int(exercice))
    ex = li.get("exercice_comptable", {})
    base = {
        "exercice": int(exercice),
        "periode_debut": ex.get("date_debut"),
        "periode_fin": ex.get("date_fin"),
    }
    bilan = li.get("etats", {}).get("bilan", {})

    if etat in ("bilan_actif", "bilan_passif"):
        from services.bilan_presentation import lignes_bilan_detaille
        cote = "actif" if etat == "bilan_actif" else "passif"
        precedent_disponible = bool(li.get("source", {}).get("n1", {}).get("disponible"))
        soldes = li.get("source", {}).get("n", {}).get("soldes", {})
        soldes_n1 = li.get("source", {}).get("n1", {}).get("soldes", {})
        # Reprend le moteur de liasse existant ; aucun calcul comptable ajouté
        # par le format PDF. N-1 reste vide lorsque la source manque.
        from services.liasse_service import calculer_bilan, calculer_cpc
        bilan_n1 = calculer_bilan(soldes_n1, calculer_cpc(soldes_n1)["resultat_net"])
        lignes = lignes_bilan_detaille(bilan, soldes, bilan_n1, soldes_n1, cote, precedent_disponible)
        colonnes = ([f"Brut {exercice}", "Amort. & prov.", f"Net {exercice}", f"Net {exercice - 1}"]
                    if cote == "actif" else [str(exercice), str(exercice - 1)])
        return {**base, "titre": f"BILAN — {cote.upper()}",
                "sous_titre": "Présentation détaillée · État de consultation non certifié",
                "colonnes": colonnes, "lignes": lignes,
                "nom_fichier": f"bilan_{cote}_{exercice}.pdf", "paysage": False}

    if etat == "cpc":
        cpc = li.get("etats", {}).get("cpc", {})
        colonnes = [str(exercice)] + ([str(int(exercice)-1)] if comparatif else [])
        lignes = []
        for r in cpc.get("lignes", []) or []:
            vals = [None if r.get("montant") is None else _n(r.get("montant"))]
            if comparatif:
                vals.append(None if r.get("n1") is None else _n(r.get("n1")))
            lignes.append({
                "type": r.get("type") or "ligne", "numero": r.get("code"),
                "label": r.get("libelle", ""), "valeurs": vals,
                "niveau": 0 if r.get("type") == "total" else 1,
            })
        return {**base, "titre": "COMPTE DE PRODUITS ET CHARGES", "sous_titre": "Modèle Normal — CGNC",
                "colonnes": colonnes, "lignes": lignes, "nom_fichier": f"cpc_{exercice}.pdf"}

    if etat == "esg":
        esg = li.get("etats", {}).get("esg", {})
        colonnes = [str(exercice)] + ([str(int(exercice)-1)] if comparatif else [])
        lignes = []
        for r in esg.get("lignes", []) or []:
            vals = [_n(r.get("montant"))] + ([_n(r.get("n1"))] if comparatif else [])
            lignes.append({"type": "total", "numero": r.get("code"), "label": r.get("libelle", ""), "valeurs": vals})
        return {**base, "titre": "ÉTAT DES SOLDES DE GESTION", "sous_titre": "TFR et capacité d'autofinancement — CGNC",
                "colonnes": colonnes, "lignes": lignes, "nom_fichier": f"esg_{exercice}.pdf"}

    tf = li.get("etats", {}).get("tableau_financement", {})
    colonnes = [str(exercice), str(int(exercice)-1), "Emplois", "Ressources"]
    lignes = [{"type": "titre", "label": "I — SYNTHÈSE DES MASSES DU BILAN", "valeurs": []}]
    for r in tf.get("synthese", []) or []:
        lignes.append({
            "type": "total" if r.get("total") else "ligne", "label": r.get("libelle", ""),
            "valeurs": [_n(r.get("n")), _n(r.get("n1")), _n(r.get("emploi")) or None, _n(r.get("ressource")) or None],
            "niveau": 0 if r.get("total") else 1,
        })
    lignes += [
        {"type": "titre", "label": "II — EMPLOIS ET RESSOURCES STABLES", "valeurs": []},
        {"type": "titre", "label": "Ressources stables", "valeurs": []},
    ]
    for r in tf.get("ressources", []) or []:
        lignes.append({"type": "total" if r.get("total") else "ligne", "numero": r.get("code"),
                       "label": r.get("libelle", ""), "valeurs": [_n(r.get("montant")), _n(r.get("n1")), None, _n(r.get("montant"))],
                       "niveau": r.get("niveau", 0)})
    lignes.append({"type": "total", "label": "Total des ressources stables", "valeurs": [None, None, None, _n(tf.get("total_ressources"))]})
    lignes.append({"type": "titre", "label": "Emplois stables", "valeurs": []})
    for r in tf.get("emplois", []) or []:
        lignes.append({"type": "total" if r.get("total") else "ligne", "numero": r.get("code"),
                       "label": r.get("libelle", ""), "valeurs": [_n(r.get("montant")), _n(r.get("n1")), _n(r.get("montant")), None],
                       "niveau": r.get("niveau", 0)})
    lignes.append({"type": "total", "label": "Total des emplois stables", "valeurs": [None, None, _n(tf.get("total_emplois")), None]})
    return {**base, "titre": "TABLEAU DE FINANCEMENT", "sous_titre": "Modèle Normal — CGNC",
            "colonnes": colonnes, "lignes": lignes, "nom_fichier": f"tableau_financement_{exercice}.pdf"}


def etat_depuis_titre(titre: str) -> str:
    t = " ".join(str(titre or "").upper().replace("—", "-").split())
    if "BILAN" in t and "ACTIF" in t:
        return "bilan_actif"
    if "BILAN" in t and "PASSIF" in t:
        return "bilan_passif"
    if "PRODUITS ET CHARGES" in t or t == "CPC":
        return "cpc"
    if "SOLDES DE GESTION" in t or t == "ESG":
        return "esg"
    if "TABLEAU DE FINANCEMENT" in t:
        return "tableau_financement"
    raise ValueError("Titre d'état financier non reconnu.")
