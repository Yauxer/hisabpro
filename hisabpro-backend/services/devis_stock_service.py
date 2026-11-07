"""Stock physique indicatif pour préparer un devis, sans réservation ni mutation."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import math
import models


def _nombre_json(nombre, diagnostics):
    try:
        flottant = float(nombre)
    except (OverflowError, ValueError):
        flottant = math.inf
    if math.isfinite(flottant) and (flottant != 0 or nombre == 0):
        return flottant
    diagnostics.append('Quantité hors représentation numérique JSON : valeur Decimal conservée en texte.')
    return str(nombre)


def diagnostic_stock_devis(db, societe_id, lignes):
    groupes = {}
    libres = []
    for index, ligne in enumerate(lignes):
        if ligne.article_id is None:
            libres.append(index)
            continue
        groupe = groupes.setdefault(ligne.article_id, {'indices': [], 'quantites': []})
        groupe['indices'].append(index)
        groupe['quantites'].append(Decimal(str(ligne.quantite)))
    articles = db.query(models.Article).filter(
        models.Article.societe_id == societe_id, models.Article.actif.is_(True),
        models.Article.id.in_(list(groupes))).all() if groupes else []
    connus = {a.id: a for a in articles}
    resultats = []
    for aid, groupe in groupes.items():
        quantites = groupe['quantites']
        article = connus.get(aid)
        stock = (Decimal(str(article.stock_actuel)) if article is not None
                 and article.stock_actuel is not None and not isinstance(article.stock_actuel, bool) else None)
        # Précision suffisante pour additionner exactement les décimaux reçus,
        # y compris des exposants différents et une retenue de cumul.
        non_nuls = [q for q in quantites if q]
        if stock is not None and stock.is_finite():
            non_nuls.append(stock)
        precision = max(28, max((q.adjusted() for q in non_nuls), default=0)
                        - min((q.as_tuple().exponent for q in non_nuls), default=0)
                        + len(str(len(quantites))) + 2)
        with localcontext() as contexte:
            contexte.prec = precision
            demande = sum(quantites, Decimal(0))
            diagnostics = []
            sortie = {'article_id': aid, 'indices_lignes': groupe['indices'],
                'designation': article.designation if article else None,
                'unite': article.unite if article else None,
                'is_stockable': article.is_stockable if article else None,
                'quantite_demandee': _nombre_json(demande, diagnostics),
                'stock_disponible': None, 'quantite_manquante': None,
                'statut': 'inconnu', 'diagnostics': diagnostics}
            if article is None:
                diagnostics.append('Article introuvable ou inactif dans cette société : stock non déterminable.')
            elif article.is_stockable is False:
                sortie['statut'] = 'non_stockable'
            elif article.is_stockable is not True:
                diagnostics.append('Caractère stockable non renseigné : stock non déterminable.')
            elif article.stock_actuel is None or isinstance(article.stock_actuel, bool):
                diagnostics.append('Stock physique non renseigné ou invalide : à vérifier.')
            else:
                if not stock.is_finite() or stock < 0:
                    diagnostics.append('Stock physique non fini ou négatif : à vérifier, sans correction automatique.')
                else:
                    sortie['stock_disponible'] = float(stock)
                    sortie['quantite_manquante'] = _nombre_json(max(Decimal(0), demande-stock), diagnostics)
                    sortie['statut'] = 'a_approvisionner' if demande > stock else 'disponible'
            resultats.append(sortie)
    return {'devis_autorise': True, 'source': 'Article.stock_actuel',
        'perimetre': 'stock_physique_societe', 'constate_le': datetime.now(timezone.utc).isoformat(),
        'articles': resultats, 'lignes_non_rattachees': libres}
