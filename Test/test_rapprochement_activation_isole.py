"""Sans084 : aucun DDL au démarrage, anciens liens utilisables, groupe503."""
from contextlib import closing
from datetime import date
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_rapprochement_ventilation_isole import preparer,situation,rapprocher
from test_ras_lecture_conservation import client
from test_lecture_reglements_historiques import photo

def test_084_absente_ne_cree_pas_table_et_preserve_lien_simple(application):
    with closing(client(application)[0]) as api:
        payload,_,rid,lids=preparer(application,api)
        avant=photo(application)
        data=situation(api)
        assert data['ventilations_activees'] is False and data['ventilations']==[]
        assert rapprocher(api,rid,payload).status_code==503
        with application['engine'].connect() as c:
            assert c.execute(text("SELECT to_regclass('rapprochement_ventilations')")).scalar() is None
        r=api.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),
            'libelle':'Ancien lien simple fictif sans084','montant':120,'sens':'credit'})
        assert r.status_code==201,r.text
        simple=r.json()['id']
        r=api.post(f'/api/rapprochement/{simple}/rapprocher',json={'ecriture_ligne_id':lids[0]})
        assert r.status_code==200,r.text
        assert api.post(f'/api/rapprochement/{simple}/derapprocher',json={}).status_code==200
        assert photo(application)==avant
