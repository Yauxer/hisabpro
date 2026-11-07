from contextlib import closing
import pytest
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import exercice, donnees
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_prorata_inventaire_isole import ecriture, photo


@pytest.mark.parametrize('type_,compte',[
    ('depreciation_stock','3942'),('depreciation_stock','1518'),('depreciation_stock','3950'),
    ('depreciation_client','3911'),('depreciation_client','3941'),('depreciation_client','3943'),
    ('provision_risque','3942'),('provision_risque','3911'),
])
def test_603_api_refuse_apercu_et_creation_sans_mutation(application,type_,compte):
    with closing(client(application)[0]) as api:
        exercice(api)
        eid=ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'SOURCE-FIGEE603')
        source=photo(application,[eid]);avant=donnees_metier(application)
        data=donnees(type_=type_,montant='123.45',contrepartie=compte)
        for chemin in ('ajustements/apercu','ajustements'):
            r=api.post('/api/cloture/'+chemin+'?exercice=2025',json=data)
            assert r.status_code==400,r.text
            assert 'provision' in r.json()['detail'].lower()
        assert donnees_metier(application)==avant and photo(application,[eid])==source


@pytest.mark.parametrize('type_,activite,compte',[
    ('depreciation_stock','61961','3915'),('depreciation_client','61964','3942'),('provision_risque','6195','4508'),
])
def test_603_famille_correcte_apercu_creation_et_validation(application,type_,activite,compte):
    with closing(client(application)[0]) as api:
        exercice(api)
        types={t['type']:t for t in ok(api.get('/api/cloture/types-ajustements'))}
        assert types[type_]['prefixes_contrepartie']==({'provision_risque':['15','45'],'depreciation_client':['3942'],'depreciation_stock':['391']}[type_])
        data=donnees(type_=type_,activite=activite,contrepartie=compte,montant='123.45')
        apercu=ok(api.post('/api/cloture/ajustements/apercu?exercice=2025',json=data))
        assert apercu['compte_contrepartie']==compte and apercu['contrepassation_date'] is None
        a=ok(api.post('/api/cloture/ajustements?exercice=2025',json=data))
        assert a['contrepassation_id'] is None
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        assert ok(api.get('/api/cloture/ajustements?exercice=2025'))[0]['est_validee']
