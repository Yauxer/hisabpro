"""Contrats stricts du workflow ;sans base et sans règle de paie."""
from datetime import datetime
import pytest
from pydantic import TypeAdapter,ValidationError
from services.personnel_workflow_schemas import Creation,Proposition,Decision,Revision

def creation(**champs):
    return dict({'nom':'Salariée fictive','matricule':'002','beneficiaire_sans_compte_confirme':True,
                 'reference_beneficiaire':'Pièce fictive877','motif':'Création fictive'},**champs)


@pytest.mark.parametrize('champs',[{'matricule':True},{'matricule':2},{'matricule':' '},{'nom':' '},
    {'beneficiaire_sans_compte_confirme':False},{'beneficiaire_sans_compte_confirme':1},
    {'utilisateur_beneficiaire_id':True},{'utilisateur_beneficiaire_id':1},
    {'reference_beneficiaire':' '},{'salaire_brut':0},{'societe_id':5},{'rib':'FAUX'}])
def test_877_creation_stricte(champs):
    with pytest.raises(ValidationError):Creation(**creation(**champs))


def test_877_pas_de_faux_salaire_et_lien_explicite():
    a=Creation(**creation(matricule=' 002\t'));assert a.matricule=='002' and 'salaire_brut' not in a.model_dump()
    b=Creation(**creation(utilisateur_beneficiaire_id=12,beneficiaire_sans_compte_confirme=False));assert b.utilisateur_beneficiaire_id==12
    assert Creation(**creation(matricule='\u00a0002\u00a0')).matricule=='\u00a0002\u00a0'


@pytest.mark.parametrize('valeur',[False,1,'true',None])
def test_877_decision_confirmation_booleenne(valeur):
    with pytest.raises(ValidationError):Decision(revision_attendue=0,motif='Fictif',independance_confirmee=valeur,reference_independance='Pièce')


@pytest.mark.parametrize('valeur',[True,-1,1.0,'0',None])
def test_877_revision_entier_strict(valeur):
    with pytest.raises(ValidationError):Revision(revision_attendue=valeur,motif='Fictif')


@pytest.mark.parametrize('contenu',[{'montant':True},{'montant':1.5},{'montant':'NaN'},{'montant':'1.001'},
    {'contrat_version_id':True},{'date_effet':datetime(2027,1,1)},{'date_effet':True},{'societe_id':5}])
def test_877_proposition_monetaires_strictes(contenu):
    c=dict({'montant':'9876.54','date_effet':'2027-01-01','periodicite':'mensuelle','reference_justificatif':'Fictif','contrat_version_id':1},**contenu)
    with pytest.raises(ValidationError):TypeAdapter(Proposition).validate_python({'nature':'REMUNERATION','revision_attendue':0,'motif':'Fictif','contenu':c})


def test_877_contrat_incoherent_et_changement_exact():
    t=TypeAdapter(Proposition)
    with pytest.raises(ValidationError):t.validate_python({'nature':'CONTRAT','revision_attendue':0,'motif':'Fictif','contenu':{
        'date_effet':'2027-01-01','date_debut':'2027-01-02','type_contrat':'CDI','reference_justificatif':'Fictif'}})
    d=t.validate_python({'nature':'REMUNERATION','revision_attendue':2,'motif':'Fictif','contenu':{
        'montant':'9876.54','date_effet':'2027-01-01','periodicite':'mensuelle','reference_justificatif':'Fictif','contrat_version_id':1}})
    assert d.model_dump(mode='json')['contenu']['montant']=='9876.54'
