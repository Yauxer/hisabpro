from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError
from services.prorata_inventaire_service import ProrataIn, calculer


def faits(**kw):
    return {'type':'cca','reference':'CONTRAT-FICTIF595','montant':'12000','base':'ht',
        'date_debut':'2025-10-01','date_fin':'2026-03-31','convention':'jours_calendaires_inclusifs',**kw}


@pytest.mark.parametrize('type_',['cca','pca'])
def test_90_jours_sur182_calcul_independant_et_complement_exact(type_):
    d=calculer(ProrataIn.model_validate(faits(type=type_)),date(2025,12,31))
    assert (d['jours_total'],d['jours_apres_cloture'],d['montant_reporte'],d['montant_non_reporte'])==(182,90,'5934.07','6065.93')
    assert Decimal(d['montant_reporte'])+Decimal(d['montant_non_reporte'])==12000
    assert len(d['libelle_propose'])<=300 and d['libelle_propose'].startswith(type_.upper())


@pytest.mark.parametrize('debut,fin,cloture,montant,jours,total,report',[
    ('2027-12-01','2028-02-29','2027-12-31','12000',60,91,'7912.09'),
    ('2028-02-01','2028-03-01','2028-02-28','30',2,30,'2.00'),
    ('2026-01-01','2026-01-01','2025-12-31','12000',1,1,'12000.00'),
    ('2025-01-01','2025-12-31','2025-12-31','12000',0,365,'0.00'),
    ('2024-07-01','2025-06-30','2025-06-30','12000',0,365,'0.00'),
    ('2026-12-31','2027-01-01','2026-12-31','0.01',1,2,'0.01'),
    ('2026-12-31','2027-01-01','2026-12-31','0.03',1,2,'0.02'),
    ('9999-12-31','9999-12-31','9999-12-31','12000',0,1,'0.00'),
    ('2026-12-31','2027-01-01','2026-12-31','9999999999999999.99',1,2,'5000000000000000.00'),
])
def test_calendrier_inclusif_bissextile_bornes_et_arrondi(debut,fin,cloture,montant,jours,total,report):
    d=calculer(ProrataIn.model_validate(faits(date_debut=debut,date_fin=fin,montant=montant)),date.fromisoformat(cloture))
    assert (d['jours_apres_cloture'],d['jours_total'],d['montant_reporte'])==(jours,total,report)
    assert Decimal(d['montant_non_reporte'])+Decimal(report)==Decimal(montant)


@pytest.mark.parametrize('kw',[{'montant':x} for x in ('NaN','Infinity','-Infinity','1e1000',True,0,-1,'0.001','10000000000000000')]+[
    {'reference':'   '},{'reference':'x'*81},{'base':'a_deviner'}, {'convention':'obligatoire'},
    {'type':'provision_risque'},{'date_debut':True},{'date_fin':'2026-02-30'}, {'societe_id':2}])
def test_entrees_inconnues_non_finies_ou_ambiguite_refusees(kw):
    with pytest.raises(ValidationError):ProrataIn.model_validate(faits(**kw))


def test_periode_inversee_refusee_et_libelle_long_representable():
    with pytest.raises(ValueError):calculer(ProrataIn.model_validate(faits(date_debut='2027-01-01')),date(2025,12,31))
    d=calculer(ProrataIn.model_validate(faits(reference='X'*80,montant='9999999999999999.99',base='autre')),date(2025,12,31))
    assert len(d['libelle_propose'])<=300
