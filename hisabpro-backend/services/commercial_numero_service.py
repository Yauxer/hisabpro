from sqlalchemy import text


def reserver_numero_commercial(db, societe_id: int, exercice: int, type_doc: str, prefixe: str):
    """Réserve atomiquement un numéro de document commercial dans PostgreSQL."""
    return db.execute(text("""
        SELECT hisabpro_reserver_numero_commercial(
            :societe_id, :exercice, :type_doc, :prefixe
        )
    """), {
        "societe_id": societe_id,
        "exercice": exercice,
        "type_doc": type_doc,
        "prefixe": prefixe,
    }).scalar_one()
