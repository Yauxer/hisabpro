"""Traduction ciblée du conflit097, sans connexion à une base."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError
import database


class SessionFictive:
    def __init__(self):self.annulations=0;self.fermetures=0
    def rollback(self):self.annulations+=1
    def close(self):self.fermetures+=1


def erreur(code,contrainte):
    origine=RuntimeError('donnee-privee')
    origine.pgcode=code;origine.diag=SimpleNamespace(constraint_name=contrainte)
    return DBAPIError('SQL-prive',{'valeur':'donnee-privee'},origine)


@pytest.mark.parametrize('code,contrainte',[('40001','ck_tva_cloture_concurrence'),('23514','ck_tva_parametres_exercice_ouvert'),('23514','ck_journal_exercice_ouvert')])
def test_conflit_tva_annule_et_retourne409_sans_donnee_privee(monkeypatch,code,contrainte):
    session=SessionFictive();monkeypatch.setattr(database,'SessionLocal',lambda:session)
    dep=database.get_db();assert next(dep) is session
    with pytest.raises(HTTPException) as e:dep.throw(erreur(code,contrainte))
    assert e.value.status_code==409 and 'prive' not in str(e.value.detail)
    assert session.annulations==1 and session.fermetures==1


@pytest.mark.parametrize('code,contrainte',[('40001',None),('23514','autre_controle'),('42501',None)])
def test_autre_erreur_db_reste_visible_sans_requalification(monkeypatch,code,contrainte):
    session=SessionFictive();monkeypatch.setattr(database,'SessionLocal',lambda:session)
    dep=database.get_db();next(dep);original=erreur(code,contrainte)
    with pytest.raises(DBAPIError) as e:dep.throw(original)
    assert e.value is original and session.annulations==0 and session.fermetures==1


def test_session_normale_fermee_sans_annulation_explicite(monkeypatch):
    session=SessionFictive();monkeypatch.setattr(database,'SessionLocal',lambda:session)
    dep=database.get_db();assert next(dep) is session
    with pytest.raises(StopIteration):next(dep)
    assert session.annulations==0 and session.fermetures==1
