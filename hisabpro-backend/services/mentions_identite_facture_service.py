"""Mentions d'identification absentes : alertes informatives, jamais valeurs inventées.

Une absence n'empêche pas la recette/validation dans HisabPro. La personne
émettrice reste responsable de compléter les mentions légales avant envoi.
"""


def mentions_identite_manquantes(societe, tiers=None, *, est_vente=True):
    if not est_vente:
        return []
    manquants = []
    champs_societe = (
        ("raison_sociale", "raison sociale"),
        ("identifiant_fiscal", "IF"),
        ("ice", "ICE"),
        ("patente", "TP/patente"),
        ("adresse", "adresse"),
        ("ville", "ville"),
    )
    for champ, nom in champs_societe:
        if not str(getattr(societe, champ, None) or "").strip():
            manquants.append(f"Société : {nom}")
    if tiers is not None:
        if not str(getattr(tiers, "adresse", None) or "").strip():
            manquants.append("Client : adresse")
        categorie = (getattr(tiers, "categorie_fiscale", None) or "indetermine").lower()
        if categorie == "indetermine":
            manquants.append("Client : catégorie fiscale")
        if categorie == "professionnel" and not str(getattr(tiers, "ice", None) or "").strip():
            manquants.append("Client professionnel : ICE")
    return manquants
