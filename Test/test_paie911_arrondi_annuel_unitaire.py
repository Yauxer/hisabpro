from decimal import Decimal
import pytest
from services.paie_ir_annuel_schemas import Simulation
from services.paie_ir_annuel_moteur import calculer
from test_paie901_ir_annuel_unitaire import demande


@pytest.mark.parametrize('revenu,base,impot',[
    ('0.00','0.00','0.0000'),('0.01','10.00','0.0000'),('10.00','10.00','0.0000'),
    ('39999.99','40000.00','0.0000'),('40000.00','40000.00','0.0000'),('40000.01','40010.00','1.0000'),
    ('40009.99','40010.00','1.0000'),('40010.00','40010.00','1.0000'),('50000.01','50010.00','1001.0000'),
    ('60000.01','60010.00','2002.0000'),('80000.01','80010.00','6003.0000'),
    ('100000.01','100010.00','12003.4000'),('180000.01','180010.00','39203.7000'),('200000.00','200000.00','46600.0000')])
def test_911_oracles_independants_arrondi_base_vers_dizaine_superieure(revenu,base,impot):
    r=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel=revenu,personnes_charge=0)));c=r['controle_arrondi_base']
    assert c['base_arrondie']==base and c['ir_apres_reduction']==impot
    assert sum(Decimal(t['impot_arithmetique']) for t in c['tranches'])==Decimal(impot)
    assert c['versement'] is None and r['ir_a_declarer'] is None and r['retenue_mensuelle'] is None and r['net_a_payer'] is None


def test_911_comparaison_exacte_distincte_et_sources_conservees():
    r=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel='40000.01',personnes_charge=0)))
    assert r['ir_annuel_arithmetique']=='0.0010' and r['controle_arrondi_base']['ecart_sans_arrondi']=='0.9990'
    q=r['referentiel']['arrondi_base_annuelle'];assert q['unite']=='10.00' and q['document_sha256']=='fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1'
    q['unite']='1.00'
    assert calculer(Simulation.model_validate(demande()))['referentiel']['arrondi_base_annuelle']['unite']=='10.00'


@pytest.mark.parametrize('kw',[{'revenu_net_imposable_annuel':None},{'cadre_general_confirme':False},{'reference_rni':None}])
def test_911_base_non_confirmee_pas_de_zero(kw):
    c=calculer(Simulation.model_validate(demande(**kw)))['controle_arrondi_base']
    assert c['base_arrondie'] is None and c['ir_apres_reduction'] is None


def test_911_famille_inconnue_et_reduction_plafonnee():
    c=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel='40000.01',personnes_charge=None)))['controle_arrondi_base']
    assert c['base_arrondie']=='40010.00' and c['ir_avant_reduction']=='1.0000' and c['ir_apres_reduction'] is None
    c=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel='40000.01',personnes_charge=6)))['controle_arrondi_base']
    assert c['reduction_appliquee']=='1.0000' and c['ir_apres_reduction']=='0.0000' and c['versement'] is None
