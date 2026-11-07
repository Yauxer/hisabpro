"""Oracle arithmétique de simulation ; taux du laboratoire, pas validation CNSS."""
from decimal import Decimal
from types import SimpleNamespace as N
import pytest
from pydantic import ValidationError
import schemas
from services.paie_service import simuler_salaire, verifier_parametres


def parametres_laboratoire():
    taux = [N(code=c, taux_sal=s, taux_pat=p, plafond=plafond) for c,s,p,plafond in [
        ('cnss_retraite', '.0448', '.0898', 72000),
        ('cnss_prest_fam', 0, '.064', None), ('amo', '.0226', '.0226', None),
        ('amo_participation', 0, '.0185', None), ('formation_prof', 0, '.016', None)]]
    bareme = [N(tranche_min=a, tranche_max=b, taux=t, deduction=d) for a,b,t,d in [
        (0,40000,0,0),(40000,60000,'.1',4000),(60000,80000,'.2',10000),
        (80000,100000,'.3',18000),(100000,180000,'.34',22000),(180000,None,'.37',27400)]]
    return taux, bareme, [N(code='enfant', montant_an=600, max_beneficiaires=6)]


def employe(brut=10000, personnes=0, situation='celiba', enfants=0):
    return N(salaire_brut=brut, personnes_charge_ir=personnes, situation_familiale=situation, nb_enfants=enfants)


@pytest.mark.parametrize('personnes,ir,net', [(0,'601.56','8903.64'),(2,'501.56','9003.64'),(6,'301.56','9203.64')])
def test_oracle_mensuel_complet(personnes, ir, net):
    result = simuler_salaire(employe(personnes=personnes), *parametres_laboratoire())
    assert result['cnss_retraite_sal'] == Decimal('268.80')
    assert result['amo_sal'] == Decimal('226.00')
    assert result['total_retenues_sal'] == Decimal('494.80')
    assert result['prestations_fam'] == Decimal('640.00')
    assert result['amo_pat'] == Decimal('411.00')
    assert result['total_charges_pat'] == Decimal('1749.80')
    assert result['cout_employeur'] == Decimal('11749.80')
    assert result['ir'] == Decimal(ir)
    assert result['salaire_net'] == Decimal(net)
    assert result['accidents'] is None


def test_aucune_charge_famille_deduite_du_mariage_ni_des_enfants():
    a = simuler_salaire(employe(situation='marie', enfants=9), *parametres_laboratoire())
    b = simuler_salaire(employe(), *parametres_laboratoire())
    assert a == b
    with pytest.raises(ValueError, match='confirmer'):
        simuler_salaire(employe(personnes=None), *parametres_laboratoire())


def test_reference_incomplete_bloquee_sans_taux_silencieux():
    taux, bareme, deductions = parametres_laboratoire()
    taux = [t for t in taux if t.code != 'amo_participation']
    with pytest.raises(ValueError, match='amo_participation'):
        simuler_salaire(employe(), taux, bareme, deductions)


@pytest.mark.parametrize('anomalie', ['doublon','nan','negatif','discontinu','ouvert','sans_bareme','sans_deduction'])
def test_referentiel_incoherent_refuse(anomalie):
    taux,bareme,deductions = parametres_laboratoire()
    if anomalie == 'doublon': taux.append(taux[0])
    elif anomalie == 'nan': taux[0].taux_sal = 'NaN'
    elif anomalie == 'negatif': taux[0].plafond = -1
    elif anomalie == 'discontinu': bareme[1].tranche_min = 41000
    elif anomalie == 'ouvert': bareme[0].tranche_max = None
    elif anomalie == 'sans_bareme': bareme = []
    elif anomalie == 'sans_deduction': deductions = []
    assert verifier_parametres(taux,bareme,deductions)


@pytest.mark.parametrize('valeur', ['NaN','Infinity',float('-inf'),True,False,-1,1e20,{},None])
def test_salaire_dossier_non_fini_ou_negatif_refuse(valeur):
    with pytest.raises(ValidationError):
        schemas.EmployeCreate(nom='Salarié fictif', salaire_brut=valeur)


@pytest.mark.parametrize('champ,valeur', [('nom','  '),('nom','a'*151),('numero_cnss','a'*51),('nb_enfants',True),('nb_enfants',-1),('personnes_charge_ir',7),('personnes_charge_ir',1.5),('situation_familiale','inconnue')])
def test_dossier_invalide_refuse(champ,valeur):
    with pytest.raises(ValidationError):
        schemas.EmployeCreate(**{'nom':'Salarié fictif', 'salaire_brut':3000,champ:valeur})


def test_dates_sortie_avant_entree_refusees():
    with pytest.raises(ValidationError):
        schemas.EmployeCreate(nom='Salarié fictif', salaire_brut=0, date_embauche='2026-02-01', date_sortie='2026-01-31')


def test_zero_et_dossier_optionnel_autorises():
    dossier = schemas.EmployeCreate(nom='  Nom fictif  ', salaire_brut=0)
    assert dossier.nom == 'Nom fictif'
    assert dossier.personnes_charge_ir is None
    assert dossier.type_contrat is None
    resultat = simuler_salaire(employe(brut=0), *parametres_laboratoire())
    assert resultat['salaire_net'] == resultat['cout_employeur'] == 0


@pytest.mark.parametrize('brut', ['NaN','Infinity',-1,'1e300'])
def test_salaire_historique_invalide_bloque_simulation(brut):
    with pytest.raises(ValueError):
        simuler_salaire(employe(brut=brut), *parametres_laboratoire())
