"""Protocole transactionnel du registre avec la clôture, sans migration."""
from fastapi import HTTPException
from sqlalchemy import text


def verrouiller_registre(db, societe_id: int, *, exclusif: bool = False):
    # Un même plan couvre plusieurs exercices ; la création doit aussi être
    # protégée, même si aucune ligne d'immobilisation n'existe encore.
    fonction = "pg_try_advisory_xact_lock" if exclusif else "pg_try_advisory_xact_lock_shared"
    cle = f"hisabpro:registre-immobilisations:{societe_id}"
    if not db.scalar(text(f"SELECT {fonction}(hashtextextended(:cle,0))"), {"cle": cle}):
        raise HTTPException(409, "Une opération de clôture ou d'immobilisations est en cours. Réessayez.")
