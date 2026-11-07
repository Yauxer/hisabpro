"""Fermeture des limites de chemin :pas de préfixe ou de méthode permissifs."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from services.personnel_profil_service import exiger_chemin_personnel

@pytest.mark.parametrize('methode,chemin',[
 ('GET','/api/employes/personnel-extra'),('GET','/api/employes/personnel/1/historique-extra'),
 ('POST','/api/employes/personnel/contexte'),('GET','/api/employes/securite/acces-extra'),
 ('PUT','/api/employes/personnel/1'),('DELETE','/api/employes/personnel/1'),
 ('PATCH','/api/auth/me'),('POST','/api/societes/switcher/1/autre'),
 ('GET','/api/employes/personnel//options'),('GET','/api/futur-module'),
 ('POST','/api/employes/personnel/demandes/1/approuver/autre')])
def test_881_chemins_proches_ou_futurs_refuses(methode,chemin):
    with pytest.raises(HTTPException) as e:
        exiger_chemin_personnel('personnel',SimpleNamespace(method=methode,url=SimpleNamespace(path=chemin)))
    assert e.value.status_code==403

def test_881_contexte_request_absent_refuse_personnel():
    with pytest.raises(HTTPException):exiger_chemin_personnel('personnel',None)

@pytest.mark.parametrize('role',['admin','comptable','lecture'])
def test_881_roles_existants_non_restreints_par_cette_garde(role):
    exiger_chemin_personnel(role,SimpleNamespace(method='GET',url=SimpleNamespace(path='/api/factures')))
