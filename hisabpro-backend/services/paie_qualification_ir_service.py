"""Qualification fiscale distincte, sans taux ni déduction implicites."""
from fastapi import HTTPException
from sqlalchemy import text

def exiger_installation(db,contenu,champ):
    if getattr(contenu,champ,None) is not None and not db.scalar(text("SELECT to_regprocedure('public.hisabpro_paie_qualification_ir119()') IS NOT NULL")):
        raise HTTPException(503,'Installer la migration 119 de qualification fiscale avant de proposer cette règle.')

def qualifie(contenu,champ):
    q=getattr(contenu,champ,None)
    return q is not None and q.statut_reglementaire=='VALIDE'
