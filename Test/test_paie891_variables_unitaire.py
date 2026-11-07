from decimal import Decimal
import pytest
from pydantic import ValidationError
from services.paie_variables_schemas import Creation,decimal_six

def donnees(**kw):return {'employe_id':1,'rubrique_id':1,'periode':'2026-11-01','date_effet':'2026-11-15','mode':'QUANTITE_TAUX','quantite':'3','taux':'0.335','source_reference':'SOURCE-FICTIVE891','justificatifs':{},'motif':'Test fictif',**kw}

def test_891_arrondi_ligne_independant_et_decimal_exact():
    d=Creation.model_validate(donnees());assert d.total()==Decimal('1.01') and d.model_dump(mode='json')['taux']=='0.335'
    d=Creation.model_validate(donnees(quantite='7.5',taux='12.345678'));assert d.total()==Decimal('92.59')

@pytest.mark.parametrize('v',[True,0.1,'NaN','Infinity','-1','0.0000001','1000000000000'])
def test_891_quantites_taux_non_exacts_refuses(v):
    with pytest.raises(ValueError):decimal_six(v)

@pytest.mark.parametrize('changement',[{'montant':'1.00'},{'quantite':None},{'mode':'MONTANT','montant':None},{'justificatifs':{'PIECE':''}},{'periode':'2026-11-02'},{'date_effet':'2026-12-01'},{'taux':'999999999999','quantite':'999999999999'}])
def test_891_combinaisons_ambigues_ou_hors_bornes_refusees(changement):
    with pytest.raises(ValidationError):Creation.model_validate(donnees(**changement))

@pytest.mark.parametrize('methode,chemin',[('POST','/api/employes/personnel/elements/variables/1'),('GET','/api/employes/personnel/elements/variables/options-extra'),('POST','/api/employes/personnel/elements/variables/1/approuver/autre'),('DELETE','/api/employes/personnel/elements/variables/1')])
def test_891_chemins_variables_non_elargis(methode,chemin):
    from types import SimpleNamespace
    from fastapi import HTTPException
    from services.personnel_profil_service import exiger_chemin_personnel
    with pytest.raises(HTTPException) as e:exiger_chemin_personnel('personnel',SimpleNamespace(method=methode,url=SimpleNamespace(path=chemin)))
    assert e.value.status_code==403
