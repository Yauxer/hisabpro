"""Oracles indépendants exclusivement fictifs, sans barème réglementaire."""
from decimal import Decimal as D
from uuid import uuid4
import copy
import pytest
from pydantic import ValidationError
from services.paie_social_moteur import assiettes,branche
from services.paie_social_calcul_schemas import Simulation
from test_paie897_social_unitaire import contenu


def variable(m='800.01',cnss='PLAFOND_MONTANT',amo='SOUMIS',unite='operation',**kw):
    def r(tr):return {'traitement':tr,'statut_reglementaire':'A_VERIFIER','plafond':'300.00' if tr=='PLAFOND_MONTANT' else None,'unite':unite}
    return {'id':1,'code':'GAIN_FICTIF','montant':m,'rubrique_id':1,'rubrique_version_id':1,'regles':{'CNSS':r(cnss),'AMO':r(amo)},**kw}


def test_899_oracle_assiettes_et_deux_branches():
    b=assiettes({'CNSS':D('9000.10'),'AMO':D('9000.10')},D('9800.11'),[variable()])
    assert b['CNSS']['montant']==D('9500.11') and b['AMO']['montant']==D('9800.11')
    a=branche(contenu(taux_salarial='1',taux_patronal='2',plafond='6000.00'),b)
    c=branche(contenu(assiette='AMO',taux_salarial='3',taux_patronal='4',plafond_mode='SANS',plafond=None),b)
    assert (a['salarial'],a['patronal'],a['assiette_retenue'])==('60.00','120.00','6000.00')
    assert (c['salarial'],c['patronal'])==('294.00','392.00')
    assert D(a['salarial'])+D(c['salarial'])==D('354.00') and D(a['patronal'])+D(c['patronal'])==D('512.00')


@pytest.mark.parametrize('base,attendu',[('0.00','0.00'),('4999.99','50.00'),('5000.00','50.00'),('5000.01','50.00')])
def test_899_frontiere_plafond_et_arrondi_par_ligne(base,attendu):
    b={'CNSS':{'montant':D(base),'anomalies':[]}}
    assert branche(contenu(taux_salarial='1',plafond='5000.00'),b)['salarial']==attendu


def test_899_plafond_mensuel_exoneration_n_est_pas_multiplie_par_variable():
    b=assiettes({'CNSS':D('100'),'AMO':D('100')},D('900'),[variable('400',unite='mensuel'),variable('400',unite='mensuel',id=2)])
    assert b['CNSS']['montant']==D('600') #100+800-300, pas100+2*(400-300)
    assert b['AMO']['montant']==D('900')


def test_899_inconnue_cnss_ne_devient_ni_zero_ni_assiette_amo():
    b=assiettes({'CNSS':None,'AMO':D('100')},D('900'),[variable('800',cnss='A_VERIFIER')])
    assert b['CNSS']['montant'] is None and b['AMO']['montant']==D('900')
    assert branche(contenu(),b)['salarial'] is None


@pytest.mark.parametrize('unite',['annuel','journalier'])
def test_899_cumul_absent_pas_de_division_implicite(unite):
    b=assiettes({'CNSS':D('100'),'AMO':D('100')},D('900'),[variable('800',unite=unite)])
    assert b['CNSS']['montant'] is None
    assert branche(contenu(unite=unite),{'CNSS':{'montant':D('100'),'anomalies':[]}})['salarial'] is None


def test_899_plusieurs_versions_meme_plafond_mensuel_bloque():
    q=assiettes({'CNSS':D('100'),'AMO':D('100')},D('900'),[variable('400',unite='mensuel'),variable('400',unite='mensuel',rubrique_version_id=2)])
    assert q['CNSS']['montant'] is None


@pytest.mark.parametrize('kw,code',[
    ({'applicabilite':'A_VERIFIER'},'APPLICABILITE_INCONNUE'),({'statut_reglementaire':'OBSOLETE'},'BRANCHE_OBSOLETE'),
    ({'plafond_mode':'A_VERIFIER','plafond':None},'PLAFOND_INCONNU'),({'calcul_mode':'A_QUALIFIER'},'MODE_INCONNU'),
    ({'assiette':'A_QUALIFIER'},'ASSIETTE_INCONNUE'),({'taux_salarial':None},'TAUX_INCONNU')])
def test_899_parametre_inconnu_ne_donne_pas_zero(kw,code):
    q=branche(contenu(**kw),{'CNSS':{'montant':D('100'),'anomalies':[]}})
    assert q['salarial'] is None and code in {x['code'] for x in q['anomalies']}


def test_899_zero_explicite_non_applicabilite_et_forfait_distincts():
    b={'CNSS':{'montant':D('100'),'anomalies':[]}}
    assert branche(contenu(taux_salarial='0'),b)['salarial']=='0.00'
    assert branche(contenu(applicabilite='NON_APPLICABLE'),b)['salarial']=='0.00'
    q=branche(contenu(calcul_mode='FORFAIT',forfait_salarial='25.00',forfait_patronal='50.00'),{})
    assert (q['salarial'],q['patronal'],q['assiette_retenue'])==('25.00','50.00',None)


def demande(**kw):return {'brut_id':1,'regime':'FICTIF','declarations':[{'employe_id':1,'base_cnss':'9000.10','base_amo':'9000.10','conditions_confirmees':True,'reference_controle':'FICTIF'}],'mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'Test FICTIF899',**kw}


@pytest.mark.parametrize('valeur',['NaN','Infinity','-1','0.001',True,12.3])
def test_899_base_invalide_rejetee(valeur):
    q=demande();q['declarations'][0]['base_cnss']=valeur
    with pytest.raises(ValidationError):Simulation.model_validate(q)


@pytest.mark.parametrize('kw',[{'brut_id':True},{'brut_id':1.1},{'mode_pedagogique_confirme':1},{'mode_pedagogique_confirme':False},{'regime':'fictif'},{'declarations':[]},{'validation_definitive':True}])
def test_899_demande_ambigue_ou_definitive_rejetee(kw):
    with pytest.raises(ValidationError):Simulation.model_validate(demande(**kw))


def test_899_salarie_double_refuse_et_montants_sans_float():
    q=demande();q['declarations']*=2
    with pytest.raises(ValidationError):Simulation.model_validate(q)
    assert Simulation.model_validate(demande()).model_dump(mode='json')['declarations'][0]['base_cnss']=='9000.10'
