from uuid import uuid4
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from services.paie_ir_source_annuelle_service import arrondir_source
from services.paie_ir_source_annuelle_schemas import Creation
from services.personnel_profil_service import exiger_chemin_personnel


def demande(ident=1,**kw):return {'frais_annuels_id':ident,'source_annuelle_confirmee':True,'cadre_general_confirme':True,'personnes_charge':2,'eligibilite_famille_confirmee':True,'reference_famille':'FAMILLE-FICTIVE915','mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'IR annuel sourcé FICTIF915',**kw}


@pytest.mark.parametrize('rni,base',[('83881.0200','83890.00'),('40000.0001','40010.00'),('40000.0000','40000.00'),('0.0000','0.00'),('59999.9999','60000.00')])
def test_915_arrondi_avant_modele_deux_decimales_sans_troncature(rni,base):assert arrondir_source(rni)==base


@pytest.mark.parametrize('v',['NaN','Infinity','-Infinity','-1','0.00001',True,False,83881.02,None,{}])
def test_915_source_invalide_refusee(v):
    with pytest.raises(ValueError):arrondir_source(v)


@pytest.mark.parametrize('kw',[{'frais_annuels_id':True},{'frais_annuels_id':0},{'source_annuelle_confirmee':'true'},{'personnes_charge':True},{'personnes_charge':7},{'mode_pedagogique_confirme':1},{'revenu_net_imposable_annuel':'1.00'},{'taux':'10'},{'reference_rni':'Inventée'}])
def test_915_source_et_famille_strictes_pas_de_montant_reaisi(kw):
    with pytest.raises(ValidationError):Creation.model_validate(demande(**kw))


@pytest.mark.parametrize('methode,suffixe,ok',[('POST','',True),('GET','',False),('POST','/1',False),('POST','-autre',False),('DELETE','',False)])
def test_915_chemin_personnel_ferme(methode,suffixe,ok):
    q=SimpleNamespace(method=methode,url=SimpleNamespace(path='/api/employes/personnel/fiscalite/depuis-frais-annuels'+suffixe))
    if ok:exiger_chemin_personnel('personnel',q)
    else:
        with pytest.raises(HTTPException):exiger_chemin_personnel('personnel',q)
