"""Projection en lecture seule : un nombre inconnu ne devient jamais zéro."""
import math
from decimal import Decimal, localcontext, ROUND_HALF_UP


def nombre(value, champ, diagnostics, *, negatif=False, decimales=None):
    try:
        if value is None or isinstance(value, bool):
            raise ValueError
        result = float(value)
        if not math.isfinite(result) or (result < 0 and not negatif):
            raise ValueError
        if decimales is not None:
            with localcontext() as ctx:
                ctx.prec = 1000
                result = float(Decimal(str(result)).quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP))
        return result
    except (ValueError, TypeError, OverflowError):
        diagnostics[champ] = "Nombre historique absent, non fini ou invalide : à vérifier."
        return None


def produit(quantite, cout, champ, diagnostics):
    if quantite is None or cout is None:
        diagnostics[champ] = "Valorisation indéterminable : quantité ou coût à vérifier."
        return None
    with localcontext() as ctx:
        ctx.prec = 1000
        valeur = (Decimal(str(quantite)) * Decimal(str(cout))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return nombre(valeur, champ, diagnostics, negatif=True)


def somme(valeurs, champ, diagnostics):
    if any(v is None for v in valeurs):
        diagnostics[champ] = "Total incomplet : des nombres sources sont à vérifier."
        return None
    with localcontext() as ctx:
        ctx.prec = 1000
        total = sum((Decimal(str(v)) for v in valeurs), Decimal('0'))
    return nombre(total, champ, diagnostics, negatif=True, decimales=2)


def projection_article(article):
    diagnostics = {}
    stock = nombre(article.stock_actuel, "stock_actuel", diagnostics, negatif=True, decimales=4)
    cmup_source = nombre(article.cmup, "cmup", diagnostics)
    cmup = nombre(article.cmup, "cmup", diagnostics, decimales=4)
    valeur = produit(stock, cmup_source, "valeur", diagnostics)
    return {"stock": stock, "cmup": cmup, "valeur": valeur,
            "nombres_diagnostics": diagnostics}


def projection_snapshot_ligne(ligne):
    diagnostics = {}
    return {"quantite": nombre(ligne.quantite_reelle, "quantite_reelle", diagnostics, negatif=True, decimales=4),
            "cmup": nombre(ligne.cmup, "cmup", diagnostics, decimales=4),
            "valeur": nombre(ligne.valeur_stock, "valeur_stock", diagnostics, negatif=True, decimales=2),
            "nombres_diagnostics": diagnostics}


def diagnostics_lignes(lignes):
    return [{"article_id": l.get("article_id"), "code": l.get("code"), "champ": c, "message": m}
            for l in lignes for c, m in l.get("nombres_diagnostics", {}).items()]
