"""Lecture diagnostiquée des paramètres sociaux, sans correction des données."""
import math


def sortie_taux_cotisation(taux):
    resultat = {nom: getattr(taux, nom) for nom in ('id', 'annee', 'code', 'libelle')}
    anomalies = []
    for nom in ('taux_sal', 'taux_pat', 'plafond'):
        valeur = getattr(taux, nom)
        resultat[nom] = None
        if valeur is None:
            if nom != 'plafond':
                anomalies.append(f'{nom} : valeur absente')
            continue
        if isinstance(valeur, bool):
            anomalies.append(f'{nom} : booléen invalide')
            continue
        try:
            nombre = float(valeur)
        except (TypeError, ValueError, OverflowError):
            anomalies.append(f'{nom} : valeur non numérique')
            continue
        if not math.isfinite(nombre):
            marqueur = 'NaN' if math.isnan(nombre) else ('Infinity' if nombre > 0 else '-Infinity')
            anomalies.append(f'{nom} : {marqueur}, valeur non finie')
            continue
        resultat[nom] = nombre
        if nom == 'plafond' and nombre <= 0:
            anomalies.append(f'{nom} : valeur non strictement positive')
        elif nom != 'plafond' and not 0 <= nombre <= 1:
            anomalies.append(f'{nom} : ratio hors bornes [0, 1]')
    resultat['anomalies'] = anomalies
    return resultat
