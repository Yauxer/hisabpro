from sqlalchemy import text


def prefixe_facture(societe, est_proforma=False):
    if est_proforma:
        return "PF"
    return (getattr(societe, "prefixe_facture", None) or "FA").strip() or "FA"


def prochain_numero_preview(db, societe_id: int, exercice: int, type_doc: str, prefixe: str):
    """Aperçu non réservé du prochain numéro.

    La réservation définitive est faite exclusivement par ``reserver_numero``.
    """
    row = db.execute(text("""
        SELECT derniere_sequence
        FROM facturation_sequences
        WHERE societe_id = :societe_id
          AND exercice = :exercice
          AND type_doc = :type_doc
    """), {
        "societe_id": societe_id,
        "exercice": exercice,
        "type_doc": type_doc,
    }).first()
    seq = int(row[0] if row else 0) + 1
    seq_txt = str(seq).zfill(3) if seq < 1000 else str(seq)
    return f"{prefixe}-{exercice}-{seq_txt}", seq


def reserver_numero(db, societe_id: int, exercice: int, type_doc: str, prefixe: str):
    """Réserve atomiquement un numéro dans PostgreSQL."""
    numero = db.execute(text("""
        SELECT hisabpro_reserver_numero_facture(
            :societe_id, :exercice, :type_doc, :prefixe
        )
    """), {
        "societe_id": societe_id,
        "exercice": exercice,
        "type_doc": type_doc,
        "prefixe": prefixe,
    }).scalar_one()
    return numero
