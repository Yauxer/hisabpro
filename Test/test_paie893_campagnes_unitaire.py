from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError
from services.paie_campagnes_schemas import Simulation
from services.paie_campagnes_service import canonique,empreinte

def body(**kw):return {'periode':'2026-11-01','employe_ids':[2,1],'mois_complets_confirmes':True,'cle_idempotence':str(uuid4()),'motif':'Test fictif893',**kw}

def test_893_canonique_exact_sans_float_ni_date_ambigue():
    assert '9007199254740993.01' in canonique({'montant':Decimal('9007199254740993.01')})
    assert empreinte({'d':date(2026,11,1),'a':'1.01'})==empreinte({'a':'1.01','d':'2026-11-01'})
    assert Simulation.model_validate(body()).employe_ids==[1,2]

@pytest.mark.parametrize('kw',[{'employe_ids':[1,1]},{'employe_ids':[True]},{'employe_ids':[]},{'employe_ids':list(range(1,52))},{'mois_complets_confirmes':1},{'mois_complets_confirmes':False},{'periode':'2026-11-02'},{'periode':True},{'type_campagne':'AUTOMATIQUE'},{'net_a_payer':'9000.00'}])
def test_893_entrees_imprecises_ou_validation_forcee_refusees(kw):
    with pytest.raises(ValidationError):Simulation.model_validate(body(**kw))

@pytest.mark.parametrize('methode,chemin',[('POST','/api/employes/personnel/traitement/simulations/autre'),('GET','/api/employes/personnel/traitement/options-extra'),('DELETE','/api/employes/personnel/traitement/simulations/1'),('POST','/api/employes/personnel/traitement/campagnes/1/approuver')])
def test_893_chemins_futurs_ou_validations_definitives_fermes(methode,chemin):
    from types import SimpleNamespace
    from fastapi import HTTPException
    from services.personnel_profil_service import exiger_chemin_personnel
    with pytest.raises(HTTPException) as e:exiger_chemin_personnel('personnel',SimpleNamespace(method=methode,url=SimpleNamespace(path=chemin)))
    assert e.value.status_code==403
