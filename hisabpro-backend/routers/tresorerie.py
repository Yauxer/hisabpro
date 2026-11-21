"""Lot 980 : volet Trésorerie.

- ``GET /api/tresorerie/situation`` : soldes comptables des banques, caisses,
  valeurs à encaisser et crédits de trésorerie à une date, et derniers mouvements.
- ``POST /api/tresorerie/virements`` : virement de fonds entre deux comptes de
  disponibilités (retrait banque → caisse, versement caisse → banque, banque →
  banque). Il passe par le compte de liaison 5115 « Virements de fonds » :
  une écriture dans le journal du compte qui donne, une dans celui du compte
  qui reçoit. Chaque journal reste ainsi complet et le 5115 revient à zéro.

Les soldes viennent uniquement des écritures : aucune donnée n'est déduite.
"""
import secrets
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import schemas
from auth import get_current_user, requiert_ecriture
from database import get_db
from routers.ecritures import inserer_ecriture
from services.plan_comptable import libelle_compte
from services.tresorerie_service import SANS_AN_CLOTURE, est_caisse
from services import especes_fournisseurs_service as especes

router = APIRouter(prefix="/api/tresorerie", tags=["tresorerie"])

COMPTE_VIREMENT = "5115"
CENT = Decimal("0.01")

# (clé, titre, préfixes, côté du bilan) — l'ordre compte : 5115 avant 511.
CATEGORIES = [
    ("virements", "Virements de fonds en cours", ("5115",), "actif"),
    ("valeurs", "Chèques et effets à encaisser", ("511",), "actif"),
    ("banques", "Banques", ("514",), "actif"),
    ("caisses", "Caisses", ("516",), "actif"),
    ("credits", "Crédits de trésorerie et banques créditrices", ("55",), "passif"),
]


def _categorie(compte: str):
    for cle, _, prefixes, _ in CATEGORIES:
        if compte.startswith(prefixes):
            return cle
    return None


def est_disponibilite(compte: str) -> bool:
    """Comptes entre lesquels un virement de fonds est possible : banques (514) et caisses (516)."""
    c = str(compte or "").strip()
    return c.startswith(("514", "516")) and c.isdigit()


def _dec(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(CENT)


@router.get("/situation")
def situation_tresorerie(
    au: Optional[date] = Query(None, description="Date de situation (par défaut : aujourd'hui)"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    jour = au or date.today()
    rows = db.execute(text(f"""
        SELECT l.compte,
               sum(CASE WHEN e.est_validee THEN l.debit - l.credit ELSE 0 END) AS solde_valide,
               sum(l.debit - l.credit) AS solde_total,
               max(e.date) AS dernier
          FROM lignes_ecriture l JOIN ecritures e ON e.id = l.ecriture_id
         WHERE e.societe_id = :s AND e.date <= :j AND l.compte LIKE '5%' AND l.compte NOT LIKE '59%'
           AND {SANS_AN_CLOTURE}
         GROUP BY l.compte"""), {"s": sid, "j": jour}).all()
    soldes = {r.compte: r for r in rows}

    banques_par_compte = {}
    for b in db.execute(text("""SELECT banque, agence, compte_comptable FROM comptes_bancaires
                                 WHERE societe_id = :s AND actif ORDER BY banque, id"""), {"s": sid}).all():
        compte = (b.compte_comptable or "5141").strip()
        banques_par_compte.setdefault(compte, []).append(b.banque + (f" — {b.agence}" if b.agence else ""))

    comptes = set(soldes) | set(banques_par_compte) | {"5161"}
    categories = {cle: {"cle": cle, "titre": titre, "cote": cote, "comptes": [], "solde": Decimal("0.00"),
                        "brouillons": Decimal("0.00")} for cle, titre, _, cote in CATEGORIES}
    for compte in sorted(comptes):
        cle = _categorie(compte)
        if not cle:
            continue
        r = soldes.get(compte)
        valide, total = _dec(r.solde_valide if r else 0), _dec(r.solde_total if r else 0)
        banques = banques_par_compte.get(compte, [])
        ligne = {
            "compte": compte,
            "libelle": libelle_compte(compte, db, sid) or compte,
            "banques": banques,
            "solde": float(valide),
            "brouillons": float(total - valide),
            "dernier_mouvement": r.dernier.isoformat() if r and r.dernier else None,
            "alerte": None,
        }
        if len(banques) > 1:
            ligne["alerte"] = "Plusieurs banques partagent ce compte : leur solde n'est pas séparable."
        if est_caisse(compte) and valide < 0:
            ligne["alerte"] = "Caisse créditrice : une caisse ne peut pas avoir moins que zéro, une entrée manque."
        if compte == COMPTE_VIREMENT and total != 0:
            ligne["alerte"] = "Virement sans sa contrepartie : le 5115 doit revenir à zéro."
        if cle == "banques" and valide < 0:
            ligne["alerte"] = "Banque à découvert : présentée au passif (554) dans le bilan."
        cat = categories[cle]
        cat["comptes"].append(ligne)
        cat["solde"] += valide
        cat["brouillons"] += total - valide

    actif = sum((c["solde"] for c in categories.values() if c["cote"] == "actif"), Decimal("0.00"))
    passif = -categories["credits"]["solde"]  # solde créditeur des 55xx
    mouvements = db.execute(text(f"""
        SELECT e.id AS ecriture_id, e.date, e.journal, e.numero_ecriture, e.libelle, e.est_validee,
               l.compte, l.debit, l.credit
          FROM lignes_ecriture l JOIN ecritures e ON e.id = l.ecriture_id
         WHERE e.societe_id = :s AND e.date <= :j AND (l.compte LIKE '514%' OR l.compte LIKE '516%')
           AND {SANS_AN_CLOTURE}
         ORDER BY e.date DESC, e.id DESC, l.id
         LIMIT 20"""), {"s": sid, "j": jour}).mappings().all()
    return {
        "date": jour.isoformat(),
        "categories": [{**c, "solde": float(c["solde"]), "brouillons": float(c["brouillons"])} for c in categories.values()],
        "disponibilites": float(categories["banques"]["solde"] + categories["caisses"]["solde"]),
        "tresorerie_nette": float(actif - passif),
        "mouvements": [{**m, "date": m["date"].isoformat(), "debit": float(m["debit"] or 0), "credit": float(m["credit"] or 0)}
                       for m in mouvements],
    }


@router.get("/especes-fournisseur")
def especes_fournisseur(
    jour: date = Query(..., alias="date"),
    tiers_id: Optional[int] = Query(None),
    tiers: Optional[str] = Query(None, max_length=200),
    montant: Decimal = Query(Decimal("0"), ge=0),
    exclure_reglement_id: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lot 981 : cumul des espèces versées à un fournisseur (jour, mois), avec le paiement en préparation."""
    if not tiers_id and not (tiers or "").strip():
        raise HTTPException(422, "Indiquez le fournisseur.")
    return especes.cumuls(db, current_user["societe_id"], tiers_id=tiers_id, tiers=tiers, jour=jour,
                          montant=montant, exclure_reglement_id=exclure_reglement_id)


@router.get("/especes-fournisseurs")
def especes_fournisseurs(
    debut: date = Query(...), fin: date = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lot 981 : fournisseurs payés en espèces au-delà de 5 000 DH/jour ou 50 000 DH/mois sur la période."""
    if fin < debut:
        raise HTTPException(422, "La date de fin précède la date de début.")
    return {"reference": especes.REFERENCE, "depassements": especes.analyser(db, current_user["societe_id"], debut, fin)}


class VirementFondsIn(BaseModel):
    date: date
    montant: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    compte_source: str = Field(min_length=3, max_length=10)
    compte_destination: str = Field(min_length=3, max_length=10)
    libelle: Optional[str] = Field(default=None, max_length=200)
    reference: Optional[str] = Field(default=None, max_length=50)
    valider: bool = True


def _journal(compte: str) -> str:
    return "CA" if est_caisse(compte) else "BQ"


def _nom(compte: str, db, sid) -> str:
    return "caisse" if est_caisse(compte) else (libelle_compte(compte, db, sid) or "banque").lower()


@router.post("/virements", status_code=201)
def virement_fonds(data: VirementFondsIn, current_user=Depends(requiert_ecriture), db: Session = Depends(get_db)):
    sid = current_user["societe_id"]
    src, dst = data.compte_source.strip(), data.compte_destination.strip()
    if not est_disponibilite(src) or not est_disponibilite(dst):
        raise HTTPException(422, "Un virement de fonds se fait entre deux comptes de banque (514…) ou de caisse (516…).")
    if src == dst:
        raise HTTPException(422, "Choisissez deux comptes différents.")
    if est_caisse(src) and est_caisse(dst):
        sens = "Transfert entre caisses"
    elif est_caisse(dst):
        sens = "Retrait d'espèces pour la caisse"
    elif est_caisse(src):
        sens = "Versement d'espèces en banque"
    else:
        sens = "Virement entre banques"
    libelle = (data.libelle or "").strip() or f"{sens} ({src} → {dst})"
    # Même référence sur les deux pièces, pour les relier (Avis n° 24).
    reference = (data.reference or "").strip() or f"VF-{data.date:%Y%m%d}-{secrets.token_hex(3).upper()}"

    def ecrire(journal, debit, credit, cote):
        lignes = [
            schemas.LigneEcritureCreate(compte=debit, libelle=f"{libelle} — {cote}", debit=float(data.montant), credit=0),
            schemas.LigneEcritureCreate(compte=credit, libelle=f"{libelle} — {cote}", debit=0, credit=float(data.montant)),
        ]
        e = schemas.EcritureCreate(date=data.date, journal=journal, libelle=libelle, reference=reference,
                                   est_validee=data.valider, lignes=lignes)
        return inserer_ecriture(db, current_user, e, source="virement_fonds", action_audit="virement_fonds")

    # Sortie d'abord : la caisse qui donne est contrôlée (lot 977) avant toute entrée.
    sortie = ecrire(_journal(src), COMPTE_VIREMENT, src, f"sortie {_nom(src, db, sid)}")
    entree = ecrire(_journal(dst), dst, COMPTE_VIREMENT, f"entrée {_nom(dst, db, sid)}")
    db.commit()
    return {
        "sens": sens,
        "montant": float(data.montant),
        "valide": data.valider,
        "ecritures": [
            {"id": e.id, "journal": getattr(e.journal, "value", e.journal), "numero_ecriture": e.numero_ecriture, "reference": e.reference,
             "lignes": [{"compte": l.compte, "debit": float(l.debit or 0), "credit": float(l.credit or 0)} for l in e.lignes]}
            for e in (sortie, entree)
        ],
    }
