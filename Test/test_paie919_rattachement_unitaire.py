import pytest
from pydantic import ValidationError
from services.paie_variables_schemas import Creation,RattachementRevenus

def declaration(**kw):return {'reference_debut':'2025-01-01','reference_fin':'2025-12-31','reference_justification':'PRIME-ANNUELLE-FICTIVE919','versement_date':'2026-12-05','versement_reference':'VERSEMENT-DECLARE-FICTIF919',**kw}

@pytest.mark.parametrize('kw',[{}, {'reference_debut':None,'reference_fin':None,'reference_justification':None},{'versement_date':None,'versement_reference':None},{'reference_debut':'2024-01-01'}])
def test_919_faits_independants_periode_longue_sans_prorata(kw):
    q=RattachementRevenus.model_validate(declaration(**kw));assert q.model_dump(mode='json')['reference_fin']==kw.get('reference_fin','2025-12-31')

@pytest.mark.parametrize('kw',[{'reference_debut':None},{'reference_fin':None},{'reference_justification':None},{'reference_debut':'2026-01-01'},{'reference_debut':'2025-02-30'},{'reference_debut':True},{'reference_debut':1735689600},{'versement_date':'Infinity'},{'versement_reference':None},{'versement_reference':' '},{'versement_date':None},{'qualification_fiscale':'VALIDE'},{'reference_fin':'2025-12-31T00:00:00'}])
def test_919_dates_et_references_strictes(kw):
    with pytest.raises(ValidationError):RattachementRevenus.model_validate(declaration(**kw))

def test_919_objet_vide_refuse_absence_historique_preservee():
    with pytest.raises(ValidationError):RattachementRevenus.model_validate({})
    q=Creation.model_validate({'employe_id':1,'rubrique_id':1,'periode':'2026-11-01','date_effet':'2026-11-15','mode':'MONTANT','montant':'800.01','source_reference':'FICTIF919','justificatifs':{},'motif':'FICTIF919'})
    assert q.rattachement_revenus is None and q.total().as_tuple().exponent==-2
