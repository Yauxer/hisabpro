"""Bornes et calculs indépendants du barème général annuel ; pas une paie."""
from uuid import uuid4
from decimal import Decimal as D
import pytest
from pydantic import ValidationError
from services.paie_ir_annuel_schemas import Simulation
from services.paie_ir_annuel_moteur import calculer


def demande(**kw):return {'annee':2026,'revenu_net_imposable_annuel':'200000.00','personnes_charge':2,'cadre_general_confirme':True,'eligibilite_famille_confirmee':True,'reference_rni':'RNI-ANNUEL-FICTIF901','reference_famille':'FAMILLE-FICTIVE901','mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'Contrôle annuel FICTIF901',**kw}


@pytest.mark.parametrize('rni,impot',[
 ('0.00','0.0000'),('40000.00','0.0000'),('40000.01','0.0010'),('60000.00','2000.0000'),('60000.01','2000.0020'),
 ('80000.00','6000.0000'),('80000.01','6000.0030'),('100000.00','12000.0000'),('100000.01','12000.0034'),
 ('180000.00','39200.0000'),('180000.01','39200.0037'),('200000.00','46600.0000'),('1000000.00','342600.0000')])
def test_901_bornes_sans_trou_ni_arrondi_de_liquidation(rni,impot):
    r=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel=rni,personnes_charge=0)))
    assert r['ir_annuel_arithmetique']==impot and sum(D(t['impot_arithmetique']) for t in r['tranches'])==D(impot)
    assert r['ir_a_declarer'] is None and r['retenue_mensuelle'] is None and r['net_a_payer'] is None


def test_901_reduction_familiale_sans_credit_fictif_et_copie_sources():
    r=calculer(Simulation.model_validate(demande()));assert r['ir_annuel_arithmetique']=='45400.0000' and r['reduction_theorique']=='1200.00'
    q=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel='41000.00',personnes_charge=6)))
    assert q['ir_avant_reduction']=='100.0000' and q['reduction_theorique']=='3600.00' and q['reduction_appliquee']=='100.0000' and q['ir_annuel_arithmetique']=='0.0000'
    r['referentiel']['tranches'][0]['borne']='999999'
    assert calculer(Simulation.model_validate(demande()))['referentiel']['tranches'][0]['borne']=='40000.00'


@pytest.mark.parametrize('kw',[{'revenu_net_imposable_annuel':None},{'cadre_general_confirme':False},{'reference_rni':None},{'personnes_charge':None},{'eligibilite_famille_confirmee':False},{'reference_famille':None}])
def test_901_information_inconnue_pas_de_zero_ou_de_repli(kw):
    r=calculer(Simulation.model_validate(demande(**kw)));assert r['ir_annuel_arithmetique'] is None and r['anomalies']


@pytest.mark.parametrize('kw',[
 {'revenu_net_imposable_annuel':'NaN'},{'revenu_net_imposable_annuel':'Infinity'},{'revenu_net_imposable_annuel':'-1'},
 {'revenu_net_imposable_annuel':'1.001'},{'revenu_net_imposable_annuel':12.3},{'revenu_net_imposable_annuel':True},
 {'personnes_charge':True},{'personnes_charge':1.5},{'personnes_charge':7},{'personnes_charge':-1},
 {'annee':2025},{'annee':2027},{'annee':2026.0},{'annee':'2026'},
 {'mode_pedagogique_confirme':1},{'mode_pedagogique_confirme':False},{'net_a_payer':'1.00'},{'situation_familiale':'marie'}])
def test_901_entree_ambigue_non_finie_ou_annee_non_qualifiee_refusee(kw):
    with pytest.raises(ValidationError):Simulation.model_validate(demande(**kw))
