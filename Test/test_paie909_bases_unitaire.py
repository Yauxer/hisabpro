"""Oracles indépendants : chiffres fictifs, jamais des taux réglementaires."""
import copy
from decimal import Decimal
from types import SimpleNamespace
from fastapi import HTTPException
from uuid import uuid4
import pytest
from pydantic import ValidationError
from services.paie_bases_fiscales_schemas import Declaration,Simulation
from services.paie_bases_fiscales_moteur import calculer,variables_fiscales
from test_paie907_qualification_ir_unitaire import preuve
from services.personnel_profil_service import exiger_chemin_personnel


def variable(ident=1,**kw):
    return {'id':ident,'code':'GAIN_FICTIF909','montant':'800.01','rubrique_id':1,'rubrique_version_id':1,
      'regle_ir':{'traitement':'PLAFOND_MONTANT','statut_reglementaire':'VALIDE','plafond':'500.00','unite':'operation'},
      'frais_professionnels':preuve('EXCLUS'),**kw}


def branches():return [{'branche_id':1,'version_id':1,'code':'B1_FICTIF','salarial':'60.00','deductibilite_ir':preuve()},
    {'branche_id':2,'version_id':2,'code':'B2_FICTIF','salarial':'294.00','deductibilite_ir':preuve('NON_DEDUCTIBLE')}]


def declaration(**kw):return Declaration.model_validate({'employe_id':1,'base_imposable':'9000.10','base_frais':'9000.10','conditions_confirmees':True,'deductibilite_integrale_confirmee':True,'reference_controle':'FICTIF909',**kw})


def test_909_bases_distinctes_oracle_exact_sans_rni_ou_net_fictif():
    r=calculer('9000.10',declaration(),[variable()],branches())
    assert r['brut_imposable']=='9300.11' and r['base_frais_professionnels']=='9000.10'
    assert r['cotisations_salariales_deductibles']=='60.00' and r['cotisations_salariales_non_deductibles']=='294.00'
    assert r['revenu_avant_frais_autres_deductions']=='9240.11' and not r['anomalies']
    assert all(r[k] is None for k in ['revenu_net_imposable','ir','net_a_payer','frais_professionnels'])


@pytest.mark.parametrize('unite,imposable',[('operation','0.00'),('mensuel','300.00')])
def test_909_plafond_mensuel_groupe_et_par_operation(unite,imposable):
    a=variable(montant='400.00');a['regle_ir']['unite']=unite;b=copy.deepcopy(a);b['id']=2
    q=variables_fiscales([a,b]);assert len(q)==1 and q[0]['imposable']==imposable and q[0]['variable_ids']==[1,2]


@pytest.mark.parametrize('traitement,imposable,frais',[('SOUMIS','800.01','800.01'),('EXONERE','0.00','0.00')])
def test_909_frais_portent_sur_fraction_imposable(traitement,imposable,frais):
    v=variable(frais_professionnels=preuve('INCLUS'));v['regle_ir']['traitement']=traitement
    q=variables_fiscales([v])[0];assert q['imposable']==imposable and q['base_frais']==frais


@pytest.mark.parametrize('mutation',[{'frais_professionnels':None},{'frais_professionnels':preuve('INCLUS',statut_reglementaire='OBSOLETE')},
    {'regle_ir':{'traitement':'SOUMIS','statut_reglementaire':'A_VERIFIER'}},
    {'regle_ir':{'traitement':'PLAFOND_MONTANT','statut_reglementaire':'VALIDE','plafond':'500.00','unite':'annuel'}},
    {'regle_ir':{'traitement':'PLAFOND_MONTANT','statut_reglementaire':'VALIDE','plafond':'500.00','unite':'journalier'}}])
def test_909_inconnues_obsolescence_cumuls_restent_bloquants(mutation):
    r=calculer('9000.10',declaration(),[variable(**mutation)],branches());assert r['anomalies']
    assert r['revenu_net_imposable'] is None and (r['brut_imposable'] is None or r['base_frais_professionnels'] is None)


def test_909_versions_multiples_non_ambigues_et_pas_de_deduction_par_defaut():
    a=variable();b=variable(2,rubrique_version_id=2)
    assert 'VERSIONS_FISCALES_MULTIPLES' in {a['code'] for a in variables_fiscales([a,b])[0]['anomalies']}
    b=branches();b[0]['deductibilite_ir']=None;r=calculer('9000.10',declaration(),[variable()],b)
    assert r['cotisations_salariales_deductibles'] is None and r['revenu_avant_frais_autres_deductions'] is None
    assert r['brut_imposable']=='9300.11' # partie certaine conservée


def test_909_vrai_zero_et_absence_de_cotisation_distincts():
    d=Declaration(employe_id=1,base_imposable='0.00',base_frais='0.00',conditions_confirmees=True,deductibilite_integrale_confirmee=True,reference_controle='ZERO FICTIF')
    b=branches()
    for x in b:x['salarial']='0.00'
    r=calculer('0.00',d,[],b);assert r['brut_imposable']=='0.00' and r['revenu_avant_frais_autres_deductions']=='0.00' and not r['anomalies']
    assert calculer('0.00',d,[],[])['cotisations_salariales_deductibles'] is None


def test_909_base_frais_inconnue_preserve_brut_connu():
    d=declaration().model_copy(update={'base_frais':None});r=calculer('9000.10',d,[variable()],branches())
    assert r['brut_imposable']=='9300.11' and r['base_frais_professionnels'] is None and r['anomalies']


@pytest.mark.parametrize('mutation',[{'base_imposable':'9500.00'},{'base_frais':'9500.00'},{'conditions_confirmees':False},{'reference_controle':None},{'base_imposable':None}])
def test_909_bases_incoherentes_et_conditions_non_confirmees(mutation):
    d=Declaration.model_validate({**declaration().model_dump(mode='json'),**mutation});r=calculer('9000.10',d,[variable()],branches())
    assert r['brut_imposable'] is None and r['anomalies']


def test_909_deduction_superieure_revenu_pas_de_zero_de_secours():
    d=declaration().model_copy(update={'base_imposable':Decimal('1'),'base_frais':Decimal('1')})
    r=calculer('9000.10',d,[],branches());assert r['revenu_avant_frais_autres_deductions'] is None and r['anomalies']


@pytest.mark.parametrize('valeur',['NaN','Infinity','-Infinity',True,False,1.25,'-1','0.001',{},[]])
def test_909_montants_non_finis_negatifs_flottants_refuses(valeur):
    with pytest.raises(ValidationError):Declaration.model_validate({**declaration().model_dump(mode='json'),'base_imposable':valeur})


def test_909_selection_et_confirmations_strictes():
    d={'social_id':1,'declarations':[declaration().model_dump(mode='json')],'mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'FICTIF909'}
    Simulation.model_validate(d)
    for mutation in [{'mode_pedagogique_confirme':1},{'social_id':True},{'declarations':d['declarations']*2},{'rni':'1000'}]:
        with pytest.raises(ValidationError):Simulation.model_validate({**d,**mutation})


def test_909_deductibilite_partielle_non_transformee_en_deduction_totale():
    r=calculer('9000.10',declaration(deductibilite_integrale_confirmee=False),[variable()],branches())
    assert r['cotisations_salariales_deductibles'] is None and r['brut_imposable']=='9300.11'
    assert 'DEDUCTION_INTEGRALE_NON_CONFIRMEE' in {a['code'] for a in r['anomalies']}


@pytest.mark.parametrize('methode,suffixe,autorise',[('GET','',True),('GET','/options',True),('GET','/12',True),('POST','',True),
    ('POST','/12',False),('GET','/12/autre',False),('GET','-autre',False),('DELETE','/12',False),('GET','//options',False),('PUT','',False)])
def test_909_profil_personnel_chemins_fermes(methode,suffixe,autorise):
    request=SimpleNamespace(method=methode,url=SimpleNamespace(path='/api/employes/personnel/fiscalite/preparations'+suffixe))
    if autorise:exiger_chemin_personnel('personnel',request)
    else:
        with pytest.raises(HTTPException) as erreur:exiger_chemin_personnel('personnel',request)
        assert erreur.value.status_code==403
