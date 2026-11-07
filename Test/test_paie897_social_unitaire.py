"""Précision et qualification des paramètres ; chiffres exclusivement fictifs."""
from datetime import date,timedelta
import copy
import pytest
from pydantic import ValidationError
from services.paie_social_schemas import Contenu


def contenu(**kw):
    return {'libelle':'Branche FICTIVE897','organisme':'Organisme fictif','applicabilite':'APPLICABLE','calcul_mode':'TAUX','assiette':'CNSS',
      'taux_salarial':'1.234567','taux_patronal':'2.5','plafond_mode':'MONTANT','plafond':'5000.00','unite':'mensuel',
      'composants':['GARANTIE_FICTIVE'],'conditions':'Hypothèse de test, ne représente aucun taux légal.',
      'date_debut':'2026-01-01','source_nature':'REGLEMENTAIRE','statut_reglementaire':'A_VERIFIER',**kw}


@pytest.mark.parametrize('valeur',['NaN','Infinity','-Infinity','-0.01','100.000001','0.0000001',True,False,1.25,{},[]])
def test_897_taux_invalide_rejete(valeur):
    with pytest.raises(ValidationError):Contenu.model_validate(contenu(taux_salarial=valeur))


@pytest.mark.parametrize('valeur',['0','100','0.000001','2.26'])
def test_897_pourcentage_exact_sans_float(valeur):
    c=Contenu.model_validate(contenu(taux_salarial=valeur));assert c.model_dump(mode='json')['taux_salarial']==valeur


@pytest.mark.parametrize('kw',[
    {'plafond':None},{'plafond':'0.00'},{'plafond':'-1'},{'plafond':'1.001'},{'plafond':True},{'plafond':12.3},
    {'plafond_mode':'SANS'},{'date_fin':'2025-12-31'},{'date_debut':'infinity'},
    {'composants':['IPE','IPE']},{'composants':['ipe']},{'composants':[]},
    {'calcul_mode':'FORFAIT'},{'calcul_mode':'A_QUALIFIER'},
    {'applicabilite':'NON_APPLICABLE'}, {'url_source':'http://www.cnss.ma/taux'},
    {'url_source':'https://cnss.ma.attacker.invalid/taux'}, {'url_source':'https://www.cnss.ma/t aux'},
    {'url_source':'https://user@www.cnss.ma/taux'}, {'date_consultation':(date.today()+timedelta(days=1)).isoformat()},
    {'statut_reglementaire':'VALIDE'}, {'assiette':'IR'}, {'taux_global':'8.00'},
])
def test_897_incoherence_ou_source_invalide(kw):
    with pytest.raises(ValidationError):Contenu.model_validate(contenu(**kw))


def qualifie(**kw):
    return contenu(statut_reglementaire='VALIDE',source_reference='FICTIF897',texte_reference='Texte FICTIF, sans portée légale',article='FICTIF',
      url_source='https://www.cnss.ma/',empreinte_preuve='a'*64,date_consultation=date.today().isoformat(),**kw)


@pytest.mark.parametrize('champ',['source_reference','texte_reference','article','url_source','empreinte_preuve','date_consultation','taux_salarial','taux_patronal'])
def test_897_qualification_incomplete_bloquee(champ):
    c=qualifie();c[champ]=None
    with pytest.raises(ValidationError):Contenu.model_validate(c)


def test_897_convention_forfait_et_non_applicabilite_explicites():
    c=qualifie();c.update(source_nature='CONTRACTUELLE',article=None,url_source=None,calcul_mode='FORFAIT',assiette='A_QUALIFIER',plafond_mode='SANS',plafond=None,taux_salarial=None,taux_patronal=None,forfait_salarial='0.00',forfait_patronal='123.45')
    assert Contenu.model_validate(c).model_dump(mode='json')['forfait_patronal']=='123.45'
    c.update(applicabilite='NON_APPLICABLE',calcul_mode='A_QUALIFIER',forfait_salarial=None,forfait_patronal=None,composants=[])
    assert Contenu.model_validate(c).applicabilite=='NON_APPLICABLE'


def test_897_inconnu_reste_inconnu_sans_defaut_reglementaire():
    c=contenu(applicabilite='A_VERIFIER',calcul_mode='A_QUALIFIER',assiette='A_QUALIFIER',taux_salarial=None,taux_patronal=None,plafond_mode='A_VERIFIER',plafond=None,composants=[])
    r=Contenu.model_validate(c).model_dump(mode='json')
    assert r['taux_salarial'] is None and r['taux_patronal'] is None and r['plafond'] is None and r['statut_reglementaire']=='A_VERIFIER'
