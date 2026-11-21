"""Lot 981 : paiements en espèces aux fournisseurs (CGI 2026, art. 11-II et 106-II).

Texte vérifié dans le CGI 2026 (copie locale .codex-tests/CGI2026_CRI.pdf) :

- art. 11-II (IS) : les charges dont le règlement n'est pas justifié par chèque
  barré non endossable, effet de commerce, moyen magnétique de paiement,
  virement, procédé électronique ou compensation ne sont déductibles « que dans
  la limite de 5 000 DH par jour et par fournisseur sans dépasser 50 000 DH par
  mois et par fournisseur » ; exception : animaux vivants et produits agricoles
  non transformés, hors transactions entre commerçants ;
- art. 106-II (TVA) : n'est pas déductible la taxe des achats « dont le montant
  dépasse 5 000 DH par jour et par fournisseur, dans la limite de 50 000 DH par
  mois et par fournisseur » réglés hors de ces moyens.

Payer en espèces reste possible : HisabPro avertit et chiffre, sans bloquer ni
retraiter d'office. La base exacte (HT ou TTC, excédent seul ou totalité, cas
d'exception) reste à confirmer par l'utilisateur : rien n'est réintégré ni
retiré de la TVA automatiquement.

Sources prises en compte, déterministes : règlements en espèces de factures
d'achat (ou sans facture, à un tiers fournisseur) et acomptes fournisseurs en
espèces, hors annulés et rejetés. Les écritures saisies à la main ne sont pas
attribuées à un fournisseur ici (le formulaire d'écriture affiche son propre
avertissement).
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from services.tresorerie_service import _dh

SEUIL_JOUR = Decimal("5000.00")
SEUIL_MOIS = Decimal("50000.00")
REFERENCE = "CGI 2026 art. 11-II (IS) et 106-II (TVA)"
CENT = Decimal("0.01")


def _d(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(CENT)


def cle_fournisseur(tiers_id, tiers) -> str:
    """Un fournisseur = son identifiant ; à défaut, son nom normalisé."""
    if tiers_id:
        return f"id:{int(tiers_id)}"
    return "nom:" + " ".join(str(tiers or "").lower().split())


def _debut_mois(jour: date) -> date:
    return jour.replace(day=1)


def _fin_mois(jour: date) -> date:
    suivant = date(jour.year + (jour.month == 12), jour.month % 12 + 1, 1)
    return date.fromordinal(suivant.toordinal() - 1)


def paiements_especes(db, societe_id: int, debut: date, fin: date, *, exclure_reglement_id=None):
    rows = db.execute(text("""
        SELECT 'reglement' AS origine, r.id, r.date, r.montant, COALESCE(r.tiers_id, f.tiers_id) AS tiers_id,
               COALESCE(NULLIF(trim(r.tiers), ''), f.tiers) AS tiers, r.facture_id, f.numero AS facture,
               COALESCE(f.reference, '') AS reference_facture
          FROM reglements r
          LEFT JOIN factures f ON f.id = r.facture_id AND f.societe_id = r.societe_id
          LEFT JOIN tiers t ON t.id = COALESCE(r.tiers_id, f.tiers_id)
         WHERE r.societe_id = :s AND lower(coalesce(r.mode, '')) = 'especes'
           AND lower(coalesce(r.statut, '')) NOT IN ('annule', 'rejete')
           AND r.date BETWEEN :d AND :f AND r.montant > 0
           AND (CAST(:x AS integer) IS NULL OR r.id <> CAST(:x AS integer))
           AND (CAST(f.type AS text) = 'achat' OR (r.facture_id IS NULL AND t.type = 'fournisseur'))
        UNION ALL
        SELECT 'acompte', a.id, a.date, a.montant, a.tiers_id, a.tiers, a.facture_id, NULL, ''
          FROM acomptes a
         WHERE a.societe_id = :s AND a.type = 'fournisseur' AND lower(coalesce(a.mode, '')) = 'especes'
           AND coalesce(a.statut, '') <> 'annule' AND coalesce(a.statut_paiement, 'encaisse') <> 'rejete'
           AND a.date BETWEEN :d AND :f AND a.montant > 0
         ORDER BY 3, 1, 2"""), {"s": societe_id, "d": debut, "f": fin, "x": exclure_reglement_id}).mappings().all()
    return [{**r, "montant": _d(r["montant"]), "cle": cle_fournisseur(r["tiers_id"], r["tiers"])} for r in rows]


def cumuls(db, societe_id: int, *, tiers_id=None, tiers=None, jour: date, montant=0, exclure_reglement_id=None) -> dict:
    """Cumul des espèces versées à un fournisseur le jour et le mois de `jour`, avec un nouveau montant éventuel."""
    cle = cle_fournisseur(tiers_id, tiers)
    mois = [p for p in paiements_especes(db, societe_id, _debut_mois(jour), _fin_mois(jour),
                                         exclure_reglement_id=exclure_reglement_id) if p["cle"] == cle]
    nouveau = _d(montant)
    jour_avant = sum((p["montant"] for p in mois if p["date"] == jour), Decimal("0.00"))
    mois_avant = sum((p["montant"] for p in mois), Decimal("0.00"))
    total_jour, total_mois = jour_avant + nouveau, mois_avant + nouveau
    alertes = []
    if total_jour > SEUIL_JOUR:
        alertes.append(f"Espèces versées à ce fournisseur le {jour:%d/%m/%Y} : {_dh(total_jour)} DH, au-delà de 5 000 DH par jour.")
    if total_mois > SEUIL_MOIS:
        alertes.append(f"Espèces versées à ce fournisseur en {jour:%m/%Y} : {_dh(total_mois)} DH, au-delà de 50 000 DH par mois.")
    return {
        "jour_deja_paye": float(jour_avant), "mois_deja_paye": float(mois_avant),
        "total_jour": float(total_jour), "total_mois": float(total_mois),
        "seuil_jour": float(SEUIL_JOUR), "seuil_mois": float(SEUIL_MOIS),
        "depassement": bool(alertes),
        "alertes": alertes,
        "consequence": ("Le paiement reste possible. Au-delà de ces limites, la charge n'est pas entièrement déductible "
                        "du résultat fiscal et la TVA de l'achat n'est pas récupérable. Préférez un chèque barré, "
                        "un virement ou une carte.") if alertes else None,
        "reference": REFERENCE,
    }


def analyser(db, societe_id: int, debut: date, fin: date) -> list[dict]:
    """Dépassements par fournisseur et par mois sur la période.

    `montant_au_dela` suit la lecture littérale de l'art. 11-II : par mois, la
    part admise est la somme des paiements journaliers retenus dans la limite de
    5 000 DH, elle-même plafonnée à 50 000 DH ; le reste est au-delà. C'est un
    montant détecté, à confirmer avant toute réintégration.
    """
    groupes = defaultdict(list)
    for p in paiements_especes(db, societe_id, debut, fin):
        groupes[(p["cle"], p["date"].year, p["date"].month)].append(p)
    resultat = []
    for (cle, annee, mois), paiements in sorted(groupes.items(), key=lambda x: (x[0][1], x[0][2], x[0][0])):
        par_jour = defaultdict(lambda: Decimal("0.00"))
        for p in paiements:
            par_jour[p["date"]] += p["montant"]
        total = sum(par_jour.values(), Decimal("0.00"))
        admis = min(sum((min(v, SEUIL_JOUR) for v in par_jour.values()), Decimal("0.00")), SEUIL_MOIS)
        jours = [{"date": j.isoformat(), "total": float(v)} for j, v in sorted(par_jour.items()) if v > SEUIL_JOUR]
        if total - admis <= 0:
            continue
        resultat.append({
            "fournisseur": next((p["tiers"] for p in paiements if p["tiers"]), cle),
            "tiers_id": next((p["tiers_id"] for p in paiements if p["tiers_id"]), None),
            "mois": f"{annee}-{mois:02d}",
            "total_especes": float(total),
            "montant_admis": float(admis),
            "montant_au_dela": float(total - admis),
            "jours_au_dela": jours,
            "mois_au_dela": total > SEUIL_MOIS,
            "paiements": [{"origine": p["origine"], "id": p["id"], "date": p["date"].isoformat(), "montant": float(p["montant"]),
                           "facture_id": p["facture_id"], "facture": p["facture"] or p["reference_facture"] or None} for p in paiements],
        })
    return resultat
