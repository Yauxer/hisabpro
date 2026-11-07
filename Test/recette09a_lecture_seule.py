"""Diagnostic 09A sur PostgreSQL, sans migration ni réparation de données.

Usage : python Test/recette09a_lecture_seule.py --societe 3 --exercice 2026
La connexion force la lecture seule par défaut, y compris après un rollback.
Le rapport contient des constats de recette, jamais un dump de base.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import argparse
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hisabpro-backend"))

READ_ONLY_OPTIONS = "-c default_transaction_read_only=on -c statement_timeout=20000 -c idle_in_transaction_session_timeout=30000"


@contextmanager
def session_lecture_seule(url):
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
    from sqlalchemy.engine import make_url
    if make_url(url).get_backend_name() != "postgresql":
        raise ValueError("Cette recette exige PostgreSQL réel.")
    engine = create_engine(url, isolation_level="REPEATABLE READ",
                           connect_args={"connect_timeout": 5, "options": READ_ONLY_OPTIONS})
    try:
        with engine.connect() as connection:
            with Session(bind=connection, autoflush=False) as db:
                flags = [db.execute(text("SHOW default_transaction_read_only")).scalar(),
                         db.execute(text("SHOW transaction_read_only")).scalar()]
                if flags != ["on", "on"]:
                    raise RuntimeError("Lecture seule PostgreSQL non effective ; recette interrompue.")
                try:
                    yield db
                finally:
                    db.rollback()
    finally:
        engine.dispose()


def montant(value):
    return "À compléter" if value is None else f"{float(value):.2f}"


def rapport_references_exactes(db, societe_id, exercice, fin):
    from services.etic_service import _factures_eligibles_etic
    lignes = ["", "## Rapprochement des références 02 et 002", "",
              "Les références sont comparées littéralement ; aucun zéro initial supprimé.", "",
              "| Type | Facture | Référence | Écriture(s) principale(s) recoupée(s) |",
              "| --- | ---: | --- | --- |"]
    for type_ in ('vente', 'achat'):
        factures, _, preuves = _factures_eligibles_etic(
            db, societe_id, exercice, type_, fin, avec_preuves=True)
        for f in factures:
            if f.numero in {'02', '002'}:
                ids = ', '.join(str(e.id) for e in preuves['principales'].get(f.id, [])) or 'Aucune preuve unique'
                lignes.append(f'| {type_} | {f.id} | {f.numero} | {ids} |')
    return '\n'.join(lignes) + '\n'


def rapport_liasse(data, societe_id):
    rows = ["# Recette 09A — PostgreSQL en lecture seule", "",
            f"Contrôle du {datetime.now(timezone.utc).isoformat(timespec='seconds')}, société {societe_id}, exercice {data['exercice']}.", "",
            "Connexion protégée par `default_transaction_read_only=on` ; transactions annulées et connexions fermées.",
            "Aucune migration, réparation, confirmation ou mutation comptable exécutée.", "",
            "## Contrôles de la liasse", "",
            f"Prête à finaliser : {data['controles']['pret_a_finaliser']} ; bloquants : {data['controles']['nb_bloquants']}.", "",
            "| Contrôle | Résultat | Détail |", "| --- | --- | --- |"]
    for c in data["controles"]["items"]:
        rows.append(f"| {c['code']} | {'OK' if c['ok'] else 'À vérifier'} | {str(c.get('details') or '').replace('|', '/')} |")
    fec = data.get("fec") or {}
    rows += ["", f"FEC : {fec.get('nb_bloquants')} anomalies bloquantes ; {fec.get('nb_avertissements')} avertissements.",
             f"ETIC : {data['etic']['progression']['completes']}/{data['etic']['progression']['total']} sections complètes."]
    rows += ["", "### Détail des anomalies FEC", ""]
    for categorie in ("bloquants", "avertissements"):
        for a in fec.get(categorie) or []:
            rows.append(f"- {categorie} / {a['code']} / écriture {a.get('ecriture_id', 'globale')} : {a['message']}")
    for sec in data["etic"]["sections"]:
        if sec["code"] not in {"B6", "B7"}:
            continue
        rows += ["", f"## {sec['code']} — {sec['titre']}", "",
                 f"Section complète : {sec['complete']}.", "",
                 "| Compte | Solde | Source factures | Échéances documentées et recoupées | Source non qualifiée | Préremplissage |",
                 "| --- | ---: | ---: | ---: | ---: | --- |"]
        lignes = (sec.get("automatique") or {}).get("lignes") or []
        for ligne in lignes:
            diag = ligne.get("echeance_auto_diagnostic")
            qualifie = sum(diag.values()) if diag else None
            mode = "Complet" if ligne.get("echeance_auto") else "Partiel" if ligne.get("echeance_auto_partiel") else "Aucun"
            rows.append(f"| {ligne['compte']} | {montant(ligne.get('montant'))} | {montant(ligne.get('echeance_auto_total'))} | {montant(qualifie)} | {montant(ligne.get('echeance_auto_non_qualifie'))} | {mode} |")
        rows += ["", "Sources à vérifier (les montants ci-dessus ne justifient aucune reclassification) :", ""]
        for ligne in lignes:
            sources = [{"compte": ligne["compte"], "anomalies_sources": ligne.get("echeance_auto_anomalies_sources") or []},
                       *(ligne.get("echeance_auto_sources_hors_solde") or [])]
            for source in sources:
                if "total_source" in source:
                    rows.append(f"- Compte source {source['compte']} absent des soldes affichés : {montant(source['total_source'])} MAD.")
                for a in source["anomalies_sources"]:
                    rows.append(f"- {source['compte']} / facture {a['facture_id']} ({a.get('numero') or 'sans numéro'}) : {' '.join(a['motifs'])}")
        rows += ["", "Contrôles de ventilation :", ""]
        rows.extend(f"- {e}" for e in sec.get("erreurs_ventilation") or [])
    rows += ["", "## Limites et prochaine étape", "",
             "Ces constats ne valident ni les pièces historiques ni les saisies extra-comptables.",
             "Les incohérences réelles nécessitent les justificatifs et une décision comptable avant toute réparation tracée.",
             "Vérifier dans le navigateur connecté la conservation des saisies et les exports ; les tests React synthétiques ne remplacent pas ce parcours.",
             "09A reste ouverte tant que les contrôles bloquants ne sont pas levés. Ne pas démarrer 09B/EDI sur une recette non validée.", ""]
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--societe", type=int, required=True)
    parser.add_argument("--exercice", type=int, required=True)
    parser.add_argument("--rapport", type=Path)
    parser.add_argument("--exports", action="store_true", help="Vérifier PDF et XLSX en mémoire, sans les sauvegarder.")
    args = parser.parse_args()
    from dotenv import dotenv_values
    url = os.getenv("HISABPRO_READONLY_DATABASE_URL") or dotenv_values(ROOT / "hisabpro-backend/.env").get("DATABASE_URL")
    if not url:
        raise SystemExit("Connexion PostgreSQL locale non configurée.")
    # Charger les modèles n'établit aucune connexion. Le service utilise
    # uniquement la Session protégée passée explicitement ci-dessous.
    os.environ["DATABASE_URL"] = url
    from services.liasse_service import construire_liasse
    with session_lecture_seule(url) as db:
        data = construire_liasse(db, args.societe, args.exercice)
        contenu = rapport_liasse(data, args.societe)
        contenu += rapport_references_exactes(db, args.societe, args.exercice, data['exercice_comptable']['date_fin'])
    if args.exports:
        from exports09a import verifier_exports
        exports = verifier_exports(data)
        contenu += (f"\n## Exports vérifiés en mémoire\n\nPDF généré et relu : {exports['pdf_pages']} pages ; "
                    f"XLSX écrit/relu : {exports['feuilles']} feuilles et {exports['ventilations']} lignes de ventilation B6/B7 vérifiées.\n"
                    "Source inchangée ; aucun PDF/XLSX sauvegardé ni archive comptable créée.\n")
    target = args.rapport or ROOT / "Test" / f"rapport_session09a_societe{args.societe}_{args.exercice}.md"
    target.write_text(contenu, encoding="utf-8")
    print(f"Rapport écrit : {target.name}")
    print(f"Liasse : {data['controles']['nb_bloquants']} contrôle(s) bloquant(s). Aucune donnée modifiée.")


if __name__ == "__main__":
    main()
