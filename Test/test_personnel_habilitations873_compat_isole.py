"""Déploiement sans105 et installation partielle : aucun repli permissif silencieux."""
from contextlib import closing
from pathlib import Path
import httpx
import pytest
from sqlalchemy import text
from test_paie_grh_postgres import app_paie, application, compte, dossier
from postgres_isole import verifier_cible_isolee

P='/api/employes/securite'


def test_873_sans_migration_acces_historique_et_administration_indisponible(app_paie):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api);e=api.post('/api/employes',json=dossier());assert e.status_code==201
        r=api.get(P+'/acces');assert r.status_code==200 and r.json()['mode']=='historique' and not r.json()['schema_installe']
        assert api.get('/api/employes').json()[0]['salaire_brut']==e.json()['salaire_brut']
        assert api.get(P+'/habilitations').status_code==503
        assert api.post(P+'/activation',json={'confirmation':'PROTEGER_PERSONNEL','motif':'Refus sans installation'}).status_code==503
        assert api.get('/api/employes').json()[0]['id']==e.json()['id']
        assert api.patch('/api/societe/modules',json={'module':'paie_grh','actif':False}).status_code==200
        assert api.get(P+'/acces').json()['module_actif'] is False
        # Le basculement de sécurité reste explicite ; cette lecture demeure historique.
        assert api.get('/api/employes').status_code==200


def test_873_installation_partielle_refuse_lecture_et_mutation(app_paie):
    c=app_paie['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api);e=api.post('/api/employes',json=dossier());assert e.status_code==201
        with app_paie['engine'].begin() as db:db.execute(text('CREATE TABLE personnel_acces_societes(societe_id integer PRIMARY KEY)'))
        try:
            assert api.get(P+'/acces').status_code==503
            assert api.get('/api/employes').status_code==503
            assert api.post('/api/employes',json=dossier()).status_code==503
        finally:
            # Seule la table vide créée par ce test, dans son cluster marqué.
            assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
            with app_paie['engine'].begin() as db:db.execute(text('DROP TABLE personnel_acces_societes'))
        assert len(api.get('/api/employes').json())==1
