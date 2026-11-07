"""Saisie sérialisée avec le calcul de clôture, pour un exercice précis."""
from fastapi import HTTPException
from sqlalchemy import text


def verrouiller_saisie_exercice(db, societe_id: int, exercice: int):
    # Même clé transactionnelle que le verrou exclusif de clôture/097/098.
    cle = f"hisabpro:tva-cloture:{societe_id}:{exercice}"
    acquis = db.scalar(text(
        "SELECT pg_try_advisory_xact_lock_shared(hashtextextended(:cle,0))"), {"cle":cle})
    if not acquis:
        raise HTTPException(409, "Une clôture est en cours pour cet exercice. Réessayez après sa fin.")


def verrouiller_operation_stock(db, societe_id: int, exercice: int, *, partage: bool = False):
    """Photographies exclusives ; mouvements ordinaires sérialisés par article."""
    verrouiller_saisie_exercice(db, societe_id, exercice)
    cle = f"hisabpro:inventaire-stock:{societe_id}:{exercice}"
    fonction = "pg_try_advisory_xact_lock_shared" if partage else "pg_try_advisory_xact_lock"
    acquis = db.scalar(text(
        f"SELECT {fonction}(hashtextextended(:cle,0))"), {"cle":cle})
    if not acquis:
        raise HTTPException(409,
            "Une opération de stock est en cours pour cet exercice. Réessayez après sa fin.")


def verrouiller_mutation_fiscale(db, societe_id: int, exercice: int):
    """Garder le calcul courant et sa confirmation sur les mêmes sources."""
    verrouiller_deficits_fiscaux(db, societe_id)
    verrouiller_saisie_exercice(db, societe_id, exercice)
    cle = f"hisabpro:fiscalite-is:{societe_id}:{exercice}"
    acquis = db.scalar(text(
        "SELECT pg_try_advisory_xact_lock(hashtextextended(:cle,0))"), {"cle":cle})
    if not acquis:
        raise HTTPException(409,
            "Une modification ou une confirmation fiscale est en cours pour cet exercice. Réessayez après sa fin.")


def verrouiller_deficits_fiscaux(db, societe_id: int, *, ecriture: bool = False):
    """Le stock de déficits est partagé entre tous les exercices d'une société."""
    fonction = "pg_try_advisory_xact_lock" if ecriture else "pg_try_advisory_xact_lock_shared"
    cle = f"hisabpro:deficits-fiscaux:{societe_id}"
    acquis = db.scalar(text(f"SELECT {fonction}(hashtextextended(:cle,0))"), {"cle": cle})
    if not acquis:
        raise HTTPException(409,
            "Un calcul ou une modification des déficits fiscaux est en cours pour cette société. Réessayez après sa fin.")
