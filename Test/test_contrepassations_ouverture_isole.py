from contextlib import closing
import httpx
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import exercice, donnees
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier

BASE='/api/cloture/contrepassations?exercice='


def creer(api, **kw):
    return ok(api.post('/api/cloture/ajustements?exercice=2025', json=donnees(montant='1200.13', **kw)))


def test_601_destination_reelle_source_statuts_et_non_mutation(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        exercice(api)
        a=creer(api)
        avant=donnees_metier(application)
        d=ok(api.get(BASE+'2026'))
        assert (d['total'],d['a_valider'],d['validees'])==(1,1,0)
        e=d['items'][0]
        assert (e['id'],e['source_id'],e['source_exercice'],e['date'],e['source_date'])==(a['contrepassation_id'],a['ecriture_id'],2025,'2026-01-01','2025-12-31')
        assert e['debit']==e['credit']=='1200.13' and e['equilibree']
        assert not e['source_validee'] and not e['est_validee']
        assert ok(api.get(BASE+'2025'))['total']==0
        assert ok(autre.get(BASE+'2026'))['total']==0
        assert ok(api.get(BASE+'2030'))['total']==0
        assert donnees_metier(application)==avant
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        ok(api.post(f"/api/ecritures/{a['contrepassation_id']}/valider"))
        d=ok(api.get(BASE+'2026'))
        assert (d['a_valider'],d['validees'])==(0,1)
        assert d['items'][0]['source_validee'] and d['items'][0]['numero']
        for url in (BASE+'0',BASE+'10000',BASE+'2026&page=0',BASE+'2026&page='+('9'*50)):
            assert api.get(url).status_code==422


def test_601_pagination_dates_decalees_et_suppression_brouillon(application):
    with closing(client(application)[0]) as api:
        exercice(api,'2024-07-01','2025-06-30')
        ok(api.patch('/api/exercices/2026',json={'date_debut':'2025-07-01','date_fin':'2026-06-30'}))
        ajustements=[creer(api,libelle=f'Contrat fictif601 {i}') for i in range(21)]
        avant=donnees_metier(application)
        a,b=ok(api.get(BASE+'2026')),ok(api.get(BASE+'2026&page=2'))
        assert len(a['items'])==20 and len(b['items'])==1 and a['total']==b['total']==21
        assert all(e['date']=='2025-07-01' and e['source_date']=='2025-06-30' for e in a['items']+b['items'])
        assert [e['id'] for e in a['items']+b['items']]==[x['contrepassation_id'] for x in reversed(ajustements)]
        assert donnees_metier(application)==avant
        ok(api.delete(f"/api/cloture/ajustements/{ajustements[-1]['id']}"))
        assert ok(api.get(BASE+'2026'))['total']==20


def test_601_lecture_autorisee_anonyme_refuse(application):
    with closing(client(application)[0]) as api:
        exercice(api);a=creer(api)
        # Réutiliser le suffixe unique du compte de laboratoire.
        me=ok(api.get('/api/auth/me'))
        email='lecteur601-'+str(me['id'])+'@example.com';password='Recette601!Lecture'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture601','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
            lecteur.headers['Authorization']='Bearer '+token
            avant=donnees_metier(application)
            assert ok(lecteur.get(BASE+'2026'))['total']==1
            assert lecteur.post(f"/api/ecritures/{a['contrepassation_id']}/valider").status_code==403
            assert donnees_metier(application)==avant
        with httpx.Client(base_url=application['api_url']) as anon:
            assert anon.get(BASE+'2026').status_code==401
