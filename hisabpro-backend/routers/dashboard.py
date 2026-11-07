from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from services.dashboard_service import construire_dashboard_commercial

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/commercial")
def dashboard_commercial(
    exercice: int = Query(...),
    date_reference: Optional[date] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return construire_dashboard_commercial(
        db,
        current_user["societe_id"],
        exercice,
        date_reference=date_reference,
    )
