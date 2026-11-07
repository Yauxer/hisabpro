from decimal import Decimal
import pytest
from pydantic import ValidationError
from services.reprises_provisions_service import RepriseIn,compte_reprise,capacite,capacite_a_date
from datetime import date


@pytest.mark.parametrize('v',[True,None,'NaN','Infinity','-Infinity','0','-1','1.001','10000000000000000','1e999999'])
def test_montants_refuses(v):
    with pytest.raises(ValidationError):
        RepriseIn(date='2026-01-01',montant=v,justification='Fictif')


@pytest.mark.parametrize('type_,charge,produit',[
    ('provision_risque','6195','7195'),('provision_risque','619510','7195'),
    ('provision_risque','6393','7393'),('provision_risque','6595','7595'),
    ('depreciation_client','61964','7196'),('depreciation_client','65963','7596'),
    ('depreciation_stock','61961','7196'),('depreciation_stock','6196','7196')])
def test_comptes_cgnc(type_,charge,produit):
    assert compte_reprise(type_,charge)==produit


@pytest.mark.parametrize('type_,charge',[('provision_risque','6125'),('depreciation_stock','61964'),
    ('depreciation_client','61961'),('depreciation_stock','6596'),('cca','6195')])
def test_nature_ambigue_refusee(type_,charge):
    with pytest.raises(ValueError):compte_reprise(type_,charge)


def test_reservations_et_annulation_incomplete_ne_liberent_pas():
    r={'montant':Decimal('400'),'annulation_id':None,'est_validee':False,'inverse_validee':None}
    assert capacite(Decimal('1000'),[r])['reservations_brouillons']=='400.00'
    for valide,inverse in [(False,False),(True,False),(False,True)]:
        assert capacite(Decimal('1000'),[{**r,'annulation_id':1,'est_validee':valide,'inverse_validee':inverse}])['disponible']=='600.00'
    assert capacite(Decimal('1000'),[{**r,'annulation_id':1,'est_validee':True,'inverse_validee':True}])['disponible']=='1000.00'


@pytest.mark.parametrize('v',['NaN','Infinity','-Infinity','0','-1'])
def test_montant_source_inexploitable_pas_de_capacite_inventee(v):
    with pytest.raises(ValueError):capacite(Decimal(v),[])


def mouvement(m='400',date_reprise='2026-02-01',annulation='2026-06-01',validee=True,inverse=True):
    return {'montant':Decimal(m),'date':date.fromisoformat(date_reprise),
        'annulation_id':1 if annulation else None,'est_validee':validee,'inverse_validee':inverse,
        'inverse_date':date.fromisoformat(annulation) if annulation else None}


@pytest.mark.parametrize('jour,attendu',[('2026-01-01','600'),('2026-03-01','600'),('2026-06-01','1000'),('2026-07-01','1000')])
def test_capacite_respecte_la_date_de_l_inverse(jour,attendu):
    assert capacite_a_date(Decimal(1000),[mouvement()],date.fromisoformat(jour))==Decimal(attendu)


def test_reprises_futures_deja_reservees_sont_preservees():
    rows=[mouvement(),mouvement('700','2026-07-01',annulation=None,validee=False)]
    assert capacite_a_date(Decimal(1000),rows,date(2026,3,1))==Decimal(300)
    assert capacite_a_date(Decimal(1000),rows,date(2026,6,2))==Decimal(300)


def test_inverse_brouillon_et_mouvements_du_meme_jour():
    assert capacite_a_date(Decimal(1000),[mouvement(inverse=False)],date(2026,7,1))==Decimal(600)
    assert capacite_a_date(Decimal(1000),[mouvement(date_reprise='2026-06-01')],date(2026,6,1))==Decimal(1000)
