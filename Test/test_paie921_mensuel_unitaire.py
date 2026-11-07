from uuid import uuid4
from copy import deepcopy
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from services.paie_ir_mensuel_schemas import Simulation
from services.paie_ir_mensuel_moteur import calculer
from services.personnel_profil_service import exiger_chemin_personnel

def demande(p=1,e=1,**kw):return {'preparation_id':p,'employe_id':e,'frais_professionnels_declares':'2250.03','reference_frais':'FRAIS-DECLARES-FICTIFS921','autres_deductions_declarees':'0.00','reference_autres_deductions':'AUCUNE-AUTRE-FICTIVE921','deductions_confirmees':True,'cadre_mensuel_general_confirme':True,'reference_controle_mensuel':'MOIS-FICTIF921','personnes_charge':2,'eligibilite_famille_confirmee':True,'reference_famille':'FAMILLE-FICTIVE921','mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'Contrôle mensuel entièrement FICTIF921',**kw}

def salarie(**kw):return {'employe_id':1,'nom':'FICTIF921','matricule':'P921','brut_imposable':'9300.11','base_frais_professionnels':'9000.10','cotisations_salariales_deductibles':'60.00','cotisations_salariales_non_deductibles':'294.00','anomalies':[],**kw}

def test_921_rni_exact_equivalence_et_invariants_sans_retenue():
    e=salarie();avant=deepcopy(e);r=calculer(e,'2026-11-01',Simulation.model_validate(demande()),[{'id':1,'periodicite':'mensuelle'}])
    assert r['rni_arithmetique']=='6990.08' and r['ir_avant_reduction_arithmetique']=='597.0240' and r['reduction_appliquee_arithmetique']=='100.0000' and r['ir_mensuel_arithmetique']=='497.0240'
    assert all(r[k] is None for k in ['retenue_a_operer','montant_a_declarer','versement','net_a_payer']) and not r['paie_definitive_autorisee'] and e==avant

@pytest.mark.parametrize('rni,impot',[('0.00','0.0000'),('3333.33','0.0000'),('3333.34','0.0007'),('5000.00','166.6667'),('6666.67','500.0010'),('15000.00','3266.6667'),('15000.01','3266.6704')])
def test_921_bornes_equivalence_sans_arrondir_les_seuils_mensuels(rni,impot):
    r=calculer(salarie(brut_imposable=rni,base_frais_professionnels=rni,cotisations_salariales_deductibles='0.00'),'2026-11-01',Simulation.model_validate(demande(frais_professionnels_declares='0.00',personnes_charge=0)),[])
    assert r['ir_mensuel_arithmetique']==impot
    if rni=='3333.34':assert r['fractions_exactes']['ir_apres_reduction']=={'numerateur':'1','denominateur':'1500'}

@pytest.mark.parametrize('kw',[{'frais_professionnels_declares':None},{'reference_frais':None},{'autres_deductions_declarees':None},{'reference_autres_deductions':None},{'deductions_confirmees':False},{'cadre_mensuel_general_confirme':False},{'reference_controle_mensuel':None},{'frais_professionnels_declares':'9001.00'},{'autres_deductions_declarees':'99999.00'},{'date_versement_declaree':'2027-01-05','reference_versement':'FICTIF'}])
def test_921_inconnues_et_deductions_excessives_pas_de_zero(kw):
    r=calculer(salarie(),'2026-11-01',Simulation.model_validate(demande(**kw)),[]);assert r['rni_arithmetique'] is None and r['ir_mensuel_arithmetique'] is None and r['anomalies']

@pytest.mark.parametrize('kw',[{'personnes_charge':None},{'eligibilite_famille_confirmee':False},{'reference_famille':None}])
def test_921_famille_inconnue_ne_change_pas_rni(kw):
    r=calculer(salarie(),'2026-11-01',Simulation.model_validate(demande(**kw)),[]);assert r['rni_arithmetique']=='6990.08' and r['ir_avant_reduction_arithmetique']=='597.0240' and r['ir_mensuel_arithmetique'] is None

@pytest.mark.parametrize('v',[{'id':1,'periodicite':'annuelle'},{'id':1,'periodicite':'ponctuelle'},{'id':1,'periodicite':'mensuelle','rattachement_revenus':{'reference_debut':'2025-01-01','reference_fin':'2025-12-31'}}])
def test_921_rappels_identifies_refuses_meme_cadre_confirme(v):
    r=calculer(salarie(),'2026-11-01',Simulation.model_validate(demande()),[v]);assert r['rni_arithmetique'] is None and any(x['code']=='RATTACHEMENT_SPECIFIQUE' for x in r['anomalies'])

def test_921_versement_source_autre_annee_pas_ignore_si_date_globale_inconnue():
    r=calculer(salarie(),'2026-11-01',Simulation.model_validate(demande()),[{'id':1,'periodicite':'mensuelle','rattachement_revenus':{'versement_date':'2025-12-05'}}])
    assert r['rni_arithmetique'] is None and any(x['code']=='VERSEMENT_SOURCE_AUTRE_ANNEE' for x in r['anomalies'])

@pytest.mark.parametrize('kw',[{'frais_professionnels_declares':'NaN'},{'frais_professionnels_declares':'Infinity'},{'frais_professionnels_declares':True},{'frais_professionnels_declares':1.5},{'frais_professionnels_declares':'-1'},{'frais_professionnels_declares':'1.001'},{'preparation_id':True},{'employe_id':False},{'personnes_charge':7},{'mode_pedagogique_confirme':1},{'date_versement_declaree':'2026-11-30'},{'revenu_net_imposable_annuel':'1.00'},{'taux':'20'},{'annee':2027}])
def test_921_entrees_strictes_sans_montant_imposable_force(kw):
    with pytest.raises(ValidationError):Simulation.model_validate(demande(**kw))

@pytest.mark.parametrize('method,suffix,ok',[('GET','',True),('GET','/1',True),('POST','',True),('POST','/1',False),('GET','/referentiel',False),('DELETE','/1',False)])
def test_921_personnel_chemins_fermes(method,suffix,ok):
    q=SimpleNamespace(method=method,url=SimpleNamespace(path='/api/employes/personnel/fiscalite/mensuel'+suffix))
    if ok:exiger_chemin_personnel('personnel',q)
    else:
        with pytest.raises(HTTPException):exiger_chemin_personnel('personnel',q)
