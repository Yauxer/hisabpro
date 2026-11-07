from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from services.paie_catalogue_schemas import Regle,Contenu
from services.paie_catalogue_service import ventiler
from services.personnel_profil_service import exiger_chemin_personnel

def regle(**kw):return {'traitement':'A_VERIFIER','conditions':'Hypothèse fictive de test',**kw}
def contenu(**kw):return dict(libelle='Test fictif',nature='GAIN',periodicite='mensuelle',formule='MONTANT',date_debut='2026-01-01',justificatifs=[],incompatibilites=[],regles={k:regle() for k in ['IR','CNSS','AMO']},**kw)

@pytest.mark.parametrize('url',['http://www.finances.gov.ma/a','https://finances.gov.ma.evil.example/x','https://127.0.0.1/','https://user@www.finances.gov.ma/','https://www.finances.gov.ma:8443/x','javascript:alert(1)'])
def test_889_sources_non_officielles_refusees(url):
    with pytest.raises(ValidationError):Regle.model_validate(regle(url_source=url))

@pytest.mark.parametrize('mutation',[{'formule':'eval(1)'},{'date_debut':True},{'date_fin':'2025-12-31'},{'justificatifs':['X','X']},{'incompatibilites':['']},{'regles':{'IR':regle(),'CNSS':regle()}}])
def test_889_contenus_ambigus_ou_formules_libres_refuses(mutation):
    c=contenu();c.update(mutation)
    with pytest.raises(ValidationError):Contenu.model_validate(c)

@pytest.mark.parametrize('methode,chemin',[('GET','/api/employes/personnel/elements/autre'),('GET','/api/employes/personnel/elements/1/autre'),('POST','/api/employes/personnel/elements/1'),('PUT','/api/employes/personnel/elements/1'),('POST','/api/employes/personnel/elements/versions/1/approuver/autre'),('DELETE','/api/employes/personnel/elements')])
def test_889_whitelist_exacte(methode,chemin):
    with pytest.raises(HTTPException) as e:exiger_chemin_personnel('personnel',SimpleNamespace(method=methode,url=SimpleNamespace(path=chemin)))
    assert e.value.status_code==403

def test_889_inconnues_ne_deviennent_pas_soumises_ou_exonerees():
    c=Contenu.model_validate(contenu());r=ventiler(c,Decimal('100.01'))
    assert all(v['soumis'] is None and v['exonere'] is None for v in r.values())

def test_889_plafond_exact_separe_et_serie_sans_arrondi_implicite():
    c=contenu();c['regles']['IR']=regle(traitement='PLAFOND_MONTANT',plafond='0.01',unite='operation')
    # La fonction d'aide fixe une seule valeur par champ,comme le formulaire.
    q=Contenu.model_validate(c);assert q.regles.IR.plafond==Decimal('0.01')
    assert q.model_dump(mode='json')['regles']['IR']['plafond']=='0.01'
    r=ventiler(q,Decimal('0.02'));assert r['IR']['soumis']=='0.01' and r['IR']['exonere']=='0.01'
