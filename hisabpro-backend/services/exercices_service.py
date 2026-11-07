# -*- coding: utf-8 -*-
"""Gestion des exercices et périodes comptables HisabPro."""
from datetime import date, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

import models

STATUTS_EXERCICE = {"a_venir", "ouvert", "cloture"}
STATUTS_PERIODE = {"a_venir", "ouverte", "fermee"}

from services.exercices_utils import (
    date_fin_max_douze_mois,
    generer_periodes_dates,
    statut_exercice_par_defaut,
    valider_duree_exercice,
)


def _statuts_periodes_par_defaut(exercice: models.ExerciceComptable, periodes: list[dict]):
    """Un exercice non clôturé laisse ses périodes libres pour la saisie.

    Ne jamais fermer automatiquement des mois simplement parce qu'ils sont
    anciens ou limiter artificiellement les périodes ouvertes à deux.
    """
    statut = "fermee" if getattr(exercice, "statut", None) == "cloture" else "ouverte"
    return [statut] * len(periodes)


def _creer_periodes_si_absentes(db: Session, exercice: models.ExerciceComptable):
    if db.query(models.PeriodeComptable).filter_by(exercice_id=exercice.id).count():
        return
    periodes = generer_periodes_dates(exercice.date_debut, exercice.date_fin)
    statuts = _statuts_periodes_par_defaut(exercice, periodes)
    for p, statut in zip(periodes, statuts):
        db.add(models.PeriodeComptable(
            exercice_id=exercice.id,
            numero=p["numero"],
            libelle=p["libelle"],
            date_debut=p["date_debut"],
            date_fin=p["date_fin"],
            statut=statut,
        ))
    # SessionLocal utilise autoflush=False. Les périodes doivent exister avant
    # le contrôle et le trigger d'une écriture, dans la même transaction.
    db.flush()


def activer_periodes_de_travail(db: Session, exercice: models.ExerciceComptable):
    """Autorise toutes les périodes non fermées d'un exercice non clôturé.

    Une fermeture manuelle historique demeure fermée jusqu'à décision explicite
    d'un administrateur ; la synchronisation n'efface pas la piste d'audit.
    """
    if exercice.statut == "cloture":
        return
    rows = db.query(models.PeriodeComptable).filter_by(exercice_id=exercice.id).all()
    for periode in rows:
        if periode.statut == "a_venir":
            periode.statut = "ouverte"
            periode.date_fermeture = None


def _fin_standard_12_mois(debut: date) -> date:
    """Dernier jour d'un exercice de douze mois commencé à ``debut``."""
    return date_fin_max_douze_mois(debut)


def ensure_exercice(
    db: Session,
    societe_id: int,
    annee: int,
    date_debut: date | None = None,
    date_fin: date | None = None,
    commit: bool = False,
):
    """Retourne l'exercice de référence ``annee`` et le prépare au besoin.

    Depuis le patch 055, ``annee`` désigne l'année de *clôture* servant de clé
    de compatibilité aux modules historiques. Cela autorise notamment un premier
    exercice court suivi d'un exercice décalé commencé dans la même année civile.
    """
    ex = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=annee
    ).first()
    if ex:
        _creer_periodes_si_absentes(db, ex)
        if commit:
            db.commit()
        return ex

    if date_fin is not None and date_fin.year != int(annee):
        raise ValueError("L'année de référence d'un exercice doit être l'année de sa date de clôture.")

    # Lorsqu'aucune date n'est fournie, prolonger la cadence de l'exercice
    # précédent évite de recréer artificiellement une année civile qui
    # chevaucherait un exercice décalé.
    if date_debut is None:
        precedent = db.query(models.ExerciceComptable).filter(
            models.ExerciceComptable.societe_id == societe_id,
            models.ExerciceComptable.annee < annee,
        ).order_by(models.ExerciceComptable.date_fin.desc()).first()
        if precedent and annee == precedent.annee + 1:
            date_debut = precedent.date_fin + timedelta(days=1)
            date_fin = _fin_standard_12_mois(date_debut)
        else:
            date_debut = date(annee, 1, 1)
            date_fin = date(annee, 12, 31)
    elif date_fin is None:
        date_fin = _fin_standard_12_mois(date_debut)

    if date_fin.year != int(annee):
        raise ValueError("L'année de référence doit correspondre à l'année de clôture de l'exercice.")
    valider_duree_exercice(date_debut, date_fin)

    chevauche = verifier_chevauchement(db, societe_id, date_debut, date_fin)
    if chevauche:
        raise ValueError(
            f"Les dates {date_debut.isoformat()}–{date_fin.isoformat()} chevauchent "
            f"l'exercice {chevauche.annee} ({chevauche.date_debut}–{chevauche.date_fin})."
        )

    clos = db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=annee
    ).first() is not None
    ex = models.ExerciceComptable(
        societe_id=societe_id,
        annee=annee,
        date_debut=date_debut,
        date_fin=date_fin,
        statut=statut_exercice_par_defaut(date_debut, date_fin, clos),
    )
    db.add(ex)
    db.flush()
    _creer_periodes_si_absentes(db, ex)
    if commit:
        db.commit()
        db.refresh(ex)
    return ex


def synchroniser_exercices(db: Session, societe_id: int):
    """Synchronise les exercices sans casser une cadence de clôture décalée."""
    exercices = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id
    ).order_by(models.ExerciceComptable.date_debut.asc()).all()

    if not exercices:
        societe = db.query(models.Societe).filter_by(id=societe_id).first()
        annee_initiale = int(getattr(societe, "exercice_debut", 0) or date.today().year)
        ensure_exercice(db, societe_id, annee_initiale)
        exercices = db.query(models.ExerciceComptable).filter_by(
            societe_id=societe_id
        ).order_by(models.ExerciceComptable.date_debut.asc()).all()

    # Reprendre les références historiques réellement présentes lorsque cela ne
    # crée pas de chevauchement. Après 055, ces valeurs sont des années de
    # référence et non nécessairement l'année civile de la date de pièce.
    sources: Iterable[tuple[object, object]] = (
        (models.Ecriture, models.Ecriture.exercice),
        (models.Facture, models.Facture.exercice),
        (models.ClotureExercice, models.ClotureExercice.exercice),
        (models.AjustementInventaire, models.AjustementInventaire.exercice),
        (models.InventaireStock, models.InventaireStock.exercice),
    )
    refs = {ex.annee for ex in exercices}
    for model, col in sources:
        for (annee,) in db.query(col).filter(model.societe_id == societe_id).distinct().all():
            if annee and int(annee) not in refs:
                try:
                    ensure_exercice(db, societe_id, int(annee))
                    refs.add(int(annee))
                except ValueError:
                    # Une ancienne valeur calendaire peut tomber dans un exercice
                    # décalé déjà défini : ne jamais créer un doublon qui chevauche.
                    pass

    exercices = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id
    ).order_by(models.ExerciceComptable.date_debut.asc()).all()

    clotures = {
        int(x[0]) for x in db.query(models.ClotureExercice.exercice)
        .filter(models.ClotureExercice.societe_id == societe_id).all()
    }
    for ex in exercices:
        # Un statut définitif reste définitif, même si une ancienne base manque
        # d'un enregistrement de synthèse ClotureExercice. La synchronisation
        # du calendrier ne constitue jamais une procédure de réouverture.
        if ex.statut == "cloture":
            continue
        attendu = statut_exercice_par_defaut(ex.date_debut, ex.date_fin, ex.annee in clotures)
        if ex.statut != attendu and not (ex.statut == "ouvert" and attendu == "a_venir"):
            ex.statut = attendu

    # Si le dernier exercice est clôturé (ou si la date courante dépasse sa fin),
    # préparer la période suivante avec la même continuité chronologique.
    exercices = sorted(exercices, key=lambda x: x.date_debut)
    if exercices:
        dernier = exercices[-1]
        if dernier.statut == "cloture" or date.today() > dernier.date_fin:
            try:
                preparer_exercice_suivant(db, societe_id, dernier)
            except ValueError:
                pass

    exercices = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id
    ).order_by(models.ExerciceComptable.date_debut.asc()).all()
    for ex in exercices:
        if ex.statut != "cloture":
            precedent = next((p for p in exercices if p.date_fin < ex.date_debut and p.statut == "cloture"), None)
            if precedent and precedent.date_fin + timedelta(days=1) == ex.date_debut:
                ex.statut = "ouvert"
                activer_periodes_de_travail(db, ex)

    db.commit()
    return db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id
    ).order_by(models.ExerciceComptable.date_debut.asc()).all()


def verifier_chevauchement(db: Session, societe_id: int, debut: date, fin: date, exclure_id: int | None = None):
    q = db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.date_debut <= fin,
        models.ExerciceComptable.date_fin >= debut,
    )
    if exclure_id:
        q = q.filter(models.ExerciceComptable.id != exclure_id)
    return q.first()


def trouver_exercice_pour_date(db: Session, societe_id: int, d: date, creer_si_absent: bool = True):
    ex = db.query(models.ExerciceComptable).filter(
        models.ExerciceComptable.societe_id == societe_id,
        models.ExerciceComptable.date_debut <= d,
        models.ExerciceComptable.date_fin >= d,
    ).order_by(models.ExerciceComptable.date_debut.desc()).first()
    if ex or not creer_si_absent:
        return ex

    rows = db.query(models.ExerciceComptable).filter_by(societe_id=societe_id).order_by(
        models.ExerciceComptable.date_debut.asc()
    ).all()
    if not rows:
        return ensure_exercice(db, societe_id, d.year)

    # Compatibilité historique : si la date précède le premier exercice connu,
    # on peut matérialiser automatiquement un exercice antérieur qui ne chevauche
    # pas le premier. Cela conserve le comportement des bases existantes tout en
    # respectant les exercices décalés. Un trou *au milieu* de l'historique reste
    # volontairement à paramétrer explicitement.
    premier = rows[0]
    if d < premier.date_debut:
        if d.year < premier.date_debut.year:
            return ensure_exercice(
                db, societe_id, d.year, date(d.year, 1, 1), date(d.year, 12, 31)
            )
        fin_historique = premier.date_debut - timedelta(days=1)
        debut_historique = date(fin_historique.year, 1, 1)
        if debut_historique <= d <= fin_historique:
            return ensure_exercice(
                db, societe_id, fin_historique.year, debut_historique, fin_historique
            )

    dernier = rows[-1]
    if d > dernier.date_fin:
        courant = dernier
        for _ in range(20):
            suivant = preparer_exercice_suivant(db, societe_id, courant)
            if suivant.date_debut <= d <= suivant.date_fin:
                return suivant
            if d < suivant.date_debut:
                break
            courant = suivant
    raise ValueError(
        f"Aucun exercice comptable ne couvre la date {d.isoformat()}. "
        "Paramétrez d'abord les dates de l'exercice."
    )


def verifier_date_ecriture(db: Session, societe_id: int, d: date, action: str = "enregistrer"):
    ex = trouver_exercice_pour_date(db, societe_id, d)
    if ex.statut == "cloture" or db.query(models.ClotureExercice).filter_by(
        societe_id=societe_id, exercice=ex.annee
    ).first():
        raise ValueError(f"Exercice {ex.annee} clôturé : impossible d'y {action} une écriture.")

    # Un exercice historique sans aucune période est préparé comme ensure_exercice.
    # Un calendrier partiel existant reste intact ; aucune période fermée n'est rouverte.
    _creer_periodes_si_absentes(db, ex)

    periode = db.query(models.PeriodeComptable).filter(
        models.PeriodeComptable.exercice_id == ex.id,
        models.PeriodeComptable.date_debut <= d,
        models.PeriodeComptable.date_fin >= d,
    ).first()
    if periode is None:
        raise ValueError(
            f"Aucune période comptable ne couvre la date {d.isoformat()} de l'exercice {ex.annee}. "
            "Paramétrez d'abord les périodes de l'exercice."
        )
    if periode.statut != "ouverte":
        etat = "fermée" if periode.statut == "fermee" else "non encore ouverte"
        raise ValueError(
            f"Période {periode.libelle} {etat} : impossible d'y {action} une écriture."
        )
    return ex


def preparer_exercice_suivant(db: Session, societe_id: int, exercice: models.ExerciceComptable):
    debut = exercice.date_fin + timedelta(days=1)
    fin = _fin_standard_12_mois(debut)
    annee = fin.year
    existant = db.query(models.ExerciceComptable).filter_by(
        societe_id=societe_id, annee=annee
    ).first()
    if existant:
        if existant.date_debut != debut:
            raise ValueError(
                f"Continuité des exercices : l'exercice suivant {annee} commence le {existant.date_debut.isoformat()}, "
                f"au lieu du {debut.isoformat()}. Vérifiez son calendrier avant de poursuivre."
            )
        return existant
    return ensure_exercice(db, societe_id, annee, debut, fin)


def marquer_exercice_cloture(db: Session, societe_id: int, annee: int, cloture: bool):
    ex = ensure_exercice(db, societe_id, annee)
    if not cloture:
        raise ValueError(
            "COMPTA.3 : une clôture comptable est définitive. "
            "Passez les corrections sur une période ouverte ultérieure."
        )
    ex.statut = "cloture"
    for p in db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id).all():
        p.statut = "fermee"
        if p.date_fermeture is None:
            from datetime import datetime
            p.date_fermeture = datetime.now()
    return ex
