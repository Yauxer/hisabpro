"""Qualification séparée, sans présumer l'éligibilité fiscale d'une cotisation."""
from datetime import date,timedelta
import pytest
from pydantic import ValidationError
from services.paie_catalogue_schemas import InclusionFrais,DeductibiliteIR,Contenu as Rubrique
from services.paie_social_schemas import Contenu as Branche
from test_paie889_catalogue_isole import contenu as rubrique
from test_paie897_social_unitaire import contenu as branche


def preuve(traitement='DEDUCTIBLE',**kw):
    return {'traitement':traitement,'statut_reglementaire':'VALIDE','conditions':'Hypothèse FICTIVE907, aucune portée légale.',
      'source_reference':'PREUVE-FICTIVE907','texte_reference':'Texte FICTIF907','article':'FICTIF907',
      'url_source':'https://www.finances.gov.ma/','empreinte_preuve':'a'*64,'date_consultation':date.today().isoformat(),**kw}


@pytest.mark.parametrize('champ',['source_reference','texte_reference','article','url_source','empreinte_preuve','date_consultation'])
def test_907_qualification_incomplete_refusee(champ):
    c=preuve();c[champ]=None
    with pytest.raises(ValidationError):DeductibiliteIR.model_validate(c)


@pytest.mark.parametrize('kw',[{'traitement':'INCLUS'},{'traitement':'A_VERIFIER'}, {'conditions':' '},
    {'url_source':'https://finances.gov.ma.attacker.invalid/'},{'url_source':'https://user@www.finances.gov.ma/'},
    {'url_source':'http://www.finances.gov.ma/'},{'url_source':'https://www.finances.gov.ma/t aux'},
    {'url_source':'https://www.finances.gov.ma/\npreuve'}, {'date_consultation':'infinity'},
    {'date_consultation':(date.today()+timedelta(days=1)).isoformat()},{'taux':'35'}])
def test_907_preuve_invalide_rejetee(kw):
    with pytest.raises(ValidationError):DeductibiliteIR.model_validate(preuve(**kw))


def test_907_anciens_contenus_inconnus_sans_deduction_automatique():
    assert Rubrique.model_validate(rubrique()).frais_professionnels is None
    assert Branche.model_validate(branche()).deductibilite_ir is None
    assert InclusionFrais.model_validate({'conditions':'À documenter'}).traitement=='A_VERIFIER'
    assert DeductibiliteIR.model_validate(preuve()).traitement=='DEDUCTIBLE'
    assert InclusionFrais.model_validate(preuve('EXCLUS')).traitement=='EXCLUS'
    with pytest.raises(ValidationError):InclusionFrais.model_validate(preuve())
