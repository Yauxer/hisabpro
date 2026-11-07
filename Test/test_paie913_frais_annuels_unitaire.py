from decimal import Decimal as D
from uuid import uuid4
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from services.paie_frais_annuels_schemas import Simulation
from services.paie_frais_annuels_moteur import calculer
from services.personnel_profil_service import exiger_chemin_personnel


def demande(**kw):return {'annee':2026,'employe_id':1,'preparation_ids':list(range(1,13)),'cadre_frais_general_confirme':True,'correspondance_revenus_annee_confirmee':True,'reference_controle_annuel':'ANNEE-FICTIVE913','autres_deductions_annuelles':'0.00','autres_deductions_confirmees':True,'reference_autres_deductions':'AUCUNE-AUTRE-FICTIVE913','mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'Frais annuels FICTIFS913',**kw}


def sources(brut='111601.32',base='108001.20',ded='720.00'):
    result=[]
    for m in range(1,13):
        # Onze zéros explicites puis le reliquat : oracle de somme, aucune projection.
        b=D(brut) if m==12 else D(0);f=D(base) if m==12 else D(0);d=D(ded) if m==12 else D(0)
        result.append({'periode':f'2026-{m:02d}-01','employe':{'brut_imposable':str(b),'base_frais_professionnels':str(f),'cotisations_salariales_deductibles':str(d),'cotisations_salariales_non_deductibles':'0.00','revenu_avant_frais_autres_deductions':str(b-d),'anomalies':[]}})
    return result


@pytest.mark.parametrize('brut,base,taux,frais',[
    ('78000.00','60000.00','35','21000.0000'),('78000.01','60000.00','25','15000.0000'),
    ('240000.00','200000.00','25','35000.0000'),('111601.32','108001.20','25','27000.3000'),
    ('0.00','0.00','35','0.0000')])
def test_913_seuil_sur_brut_base_hors_avantages_plafond_et_zero(brut,base,taux,frais):
    r=calculer(Simulation.model_validate(demande()),sources(brut,base,'0.00'))
    assert not r['anomalies'] and r['taux_frais_pourcent']==taux and r['frais_professionnels_annuels_arithmetiques']==frais
    assert all(r[k] is None for k in ['ir','retenue_mensuelle','net_a_payer','versement']) and not r['paie_definitive_autorisee']


def test_913_rni_independant_exact_sans_arrondi_et_autres_deductions():
    r=calculer(Simulation.model_validate(demande()),sources())
    assert r['cumuls']['brut_imposable']=='111601.32' and r['cumuls']['cotisations_salariales_deductibles']=='720.00'
    assert r['rni_annuel_arithmetique_avant_arrondis']=='83881.0200'
    q=calculer(Simulation.model_validate(demande(autres_deductions_annuelles='123.45')),sources())
    assert q['rni_annuel_arithmetique_avant_arrondis']=='83757.5700'


@pytest.mark.parametrize('mutation',[{'cadre_frais_general_confirme':False},{'correspondance_revenus_annee_confirmee':False},{'reference_controle_annuel':None}])
def test_913_cadre_et_revenus_non_confirmes_bloquants(mutation):
    r=calculer(Simulation.model_validate(demande(**mutation)),sources());assert r['frais_professionnels_annuels_arithmetiques'] is None and r['anomalies']


@pytest.mark.parametrize('mutation',[{'autres_deductions_annuelles':None},{'autres_deductions_confirmees':False},{'reference_autres_deductions':None},{'autres_deductions_annuelles':'999999.00'}])
def test_913_autres_deductions_inconnues_ne_sont_pas_zero(mutation):
    r=calculer(Simulation.model_validate(demande(**mutation)),sources())
    assert r['frais_professionnels_annuels_arithmetiques']=='27000.3000' and r['rni_annuel_arithmetique_avant_arrondis'] is None and r['anomalies']


def test_913_annee_partielle_pas_de_mois_multiplie_et_anomalie_source():
    s=sources();r=calculer(Simulation.model_validate(demande()),s[-1:])
    assert r['nombre_mois']==1 and r['cumuls']['brut_imposable']=='111601.32' and r['frais_professionnels_annuels_arithmetiques'] is None
    s[0]['employe']['brut_imposable']=None
    assert calculer(Simulation.model_validate(demande()),s)['cumuls']['brut_imposable'] is None


@pytest.mark.parametrize('mutation',[{'annee':2027},{'annee':2026.0},{'employe_id':True},{'preparation_ids':[True]}, {'preparation_ids':[1,1]},{'preparation_ids':[]},{'preparation_ids':list(range(1,14))},
    {'autres_deductions_annuelles':'NaN'},{'autres_deductions_annuelles':'Infinity'},{'autres_deductions_annuelles':True},{'autres_deductions_annuelles':1.25},{'autres_deductions_annuelles':'-1'},{'autres_deductions_annuelles':'0.001'},{'mode_pedagogique_confirme':1}])
def test_913_entree_ambigue_non_finie_ou_selection_invalide(mutation):
    with pytest.raises(ValidationError):Simulation.model_validate(demande(**mutation))


@pytest.mark.parametrize('method,suffixe,ok',[('GET','',True),('GET','/options',True),('GET','/1',True),('POST','',True),('DELETE','/1',False),('GET','/1/autre',False),('POST','/options',False),('GET','-autre',False)])
def test_913_chemins_personnel_fermes(method,suffixe,ok):
    request=SimpleNamespace(method=method,url=SimpleNamespace(path='/api/employes/personnel/fiscalite/frais-annuels'+suffixe))
    if ok:exiger_chemin_personnel('personnel',request)
    else:
        with pytest.raises(HTTPException):exiger_chemin_personnel('personnel',request)
