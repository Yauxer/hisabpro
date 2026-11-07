"""Consultation des liens d'inventaire existants dans l'exercice de destination."""
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, aliased, joinedload
from database import get_db
from auth import get_current_user
import models
from services.ventes_preparation_service import preparer_lecture

router = APIRouter()


def lecture(db: Session = Depends(get_db)):
    return preparer_lecture(db)


@router.get('/contrepassations')
def consulter(exercice: int = Query(..., ge=1, le=9999), page: int = Query(1, ge=1, le=1000000),
              db: Session = Depends(lecture), user=Depends(get_current_user)):
    sid = user['societe_id']
    a = models.AjustementInventaire
    source = aliased(models.Ecriture)
    cp = models.Ecriture
    q = db.query(a, cp, source).join(cp, cp.id == a.contrepassation_id).join(source, source.id == a.ecriture_id).filter(
        a.societe_id == sid, cp.societe_id == sid, source.societe_id == sid, cp.exercice == exercice)
    total = q.count()
    validees = q.filter(cp.est_validee.is_(True)).count()
    rows = q.options(joinedload(cp.lignes)).order_by(cp.date.desc(), cp.id.desc()).offset((page-1)*20).limit(20).all()
    items = []
    for ajustement, ecriture, origine in rows:
        sommes = [sum((getattr(l, nom) for l in ecriture.lignes), Decimal('0.00')) for nom in ('debit', 'credit')]
        finies = all(v.is_finite() for v in sommes)
        items.append(dict(id=ecriture.id, numero=ecriture.numero_ecriture, reference=ecriture.reference,
            date=ecriture.date.isoformat(), journal=ecriture.journal, libelle=ecriture.libelle,
            est_validee=bool(ecriture.est_validee), type=ajustement.type,
            source_id=origine.id, source_numero=origine.numero_ecriture, source_reference=origine.reference,
            source_exercice=origine.exercice, source_date=origine.date.isoformat(), source_validee=bool(origine.est_validee),
            debit=format(sommes[0], '.2f') if finies else None, credit=format(sommes[1], '.2f') if finies else None,
            equilibree=finies and sommes[0] == sommes[1]))
    return dict(exercice=exercice, page=page, taille_page=20, total=total,
                a_valider=total-validees, validees=validees, items=items)
