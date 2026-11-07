"""Valeurs exactes du contrat1A.2 ;aucune règle sociale/fiscale."""
from datetime import date, datetime
from decimal import Decimal
import pytest
from pydantic import ValidationError
from services.personnel_dossiers_service import normaliser_matricule, montant_exact, RemunerationVersion


@pytest.mark.parametrize('source,attendu',[(None,None),('',None),(' \t\n ',None),
    (' 002\t','002'),('02','02'),('2','2'),('ab  cd','ab  cd'),('Ab','Ab'),('\u00a002\u00a0','\u00a002\u00a0')])
def test_875_matricule_textuel(source,attendu):
    assert normaliser_matricule(source)==attendu


@pytest.mark.parametrize('source',[2,True,False,1.2])
def test_875_matricule_pas_de_coercition(source):
    with pytest.raises(ValueError):normaliser_matricule(source)


@pytest.mark.parametrize('source',[True,False,1.25,float('inf'),float('nan'),None,'NaN','sNaN','Infinity','-Infinity',
    '-1','1.001',Decimal('1.000'),'10000000000000000','1e1000','1e-1000','non-montant'])
def test_875_montant_non_exact_refuse(source):
    with pytest.raises(ValueError):montant_exact(source)


@pytest.mark.parametrize('source,attendu',[('0','0.00'),(0,'0.00'),('0.01','0.01'),
    ('12345.67','12345.67'),(Decimal('9000.10'),'9000.10'),('9999999999999999.99','9999999999999999.99')])
def test_875_montant_exact_et_serialisation(source,attendu):
    v=RemunerationVersion(montant=source,date_effet='2027-01-01',periodicite='mensuelle',reference_justificatif='Contrat fictif')
    assert v.montant==Decimal(attendu) and v.model_dump(mode='json')['montant']==attendu


@pytest.mark.parametrize('champs',[{'date_effet':True},{'date_effet':1798761600},{'date_effet':'2027-01-01T00:00:00'},
    {'date_effet':datetime(2027,1,1)},{'date_effet':'2027-02-30'},{'periodicite':'annuelle'},
    {'devise':'EUR'},{'reference_justificatif':' '},{'societe_id':2},{'montant':1.23}])
def test_875_contrat_valeur_strict(champs):
    with pytest.raises(ValidationError):
        RemunerationVersion(**dict({'montant':'9000.00','date_effet':'2027-01-01',
            'periodicite':'mensuelle','reference_justificatif':'Document fictif'},**champs))
