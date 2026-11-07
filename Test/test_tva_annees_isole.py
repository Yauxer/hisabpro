"""Années calendaires TVA : erreurs422 sans mutation et bornes représentables."""
from contextlib import closing
from datetime import date
import json
import pytest
from fastapi import HTTPException
from routers.tva import _bornes
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from recette_restauration_consolidee_084 import empreintes_tables
from test_permissions_tva_runtime_isole import audit


@pytest.mark.parametrize('annee', [0,-1,10000,2147483648])
@pytest.mark.parametrize('periode', [{},{'mois':1},{'trimestre':1}])
def test_declaration_annee_invalide_422_sans_mutation(application,annee,periode):
    with closing(client(application)[0]) as api:
        avant=empreintes_tables(application['engine'])
        r=api.get('/api/tva/declaration',params={'exercice':annee,**periode})
        assert r.status_code==422,r.text
        erreurs=r.json()['detail']; assert any(e['loc']==['query','exercice'] for e in erreurs)
        assert empreintes_tables(application['engine'])==avant


@pytest.mark.parametrize('annee', [0,-1,10000,2147483648])
@pytest.mark.parametrize('methode', ['get','put'])
def test_parametre_annee_invalide_422_sans_mutation(application,annee,methode):
    with closing(client(application)[0]) as api:
        avant=empreintes_tables(application['engine']); journal_avant=audit(application)
        kwargs={'json':{'credit_ouverture':20,'prorata_deduction_pct':80}} if methode=='put' else {}
        r=getattr(api,methode)(f'/api/tva/parametres/{annee}',**kwargs)
        assert r.status_code==422,r.text
        assert any(e['loc']==['path','exercice'] for e in r.json()['detail'])
        apres=empreintes_tables(application['engine'])
        assert {k:v for k,v in apres.items() if k!='audit_actions'}=={k:v for k,v in avant.items() if k!='audit_actions'}
        journal_apres=audit(application)
        if methode=='put':
            assert journal_apres[:-1]==journal_avant and len(journal_apres)==len(journal_avant)+1
            evenement=json.loads(journal_apres[-1])
            assert evenement['methode']=='PUT' and evenement['chemin']==f'/api/tva/parametres/{annee}'
            assert evenement['statut_http']==422 and evenement['succes'] is False
            assert evenement['request_id']==r.headers['X-Request-ID']
        else: assert journal_apres==journal_avant and apres==avant


@pytest.mark.parametrize('annee', [1,9999])
@pytest.mark.parametrize('periode', [{},{'mois':1},{'mois':12},{'trimestre':1},{'trimestre':4}])
def test_limites_calendaires_valides_sans_faux_calcul(application,annee,periode):
    with closing(client(application)[0]) as api:
        # Paramètre déclaré, sans génération d'exercice ni données comptables.
        ok(api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':20,'prorata_deduction_pct':80}))
        assert ok(api.get(f'/api/tva/parametres/{annee}'))['exercice']==annee
        avant=empreintes_tables(application['engine'])
        r=ok(api.get('/api/tva/declaration',params={'exercice':annee,**periode}))
        assert r['tva_due']==0 and r['credit_tva']==20 and r['credit_tva_anterieur']==20
        assert r['collectee']['total']==0 and r['recuperable']['total']==0
        assert date.fromisoformat(r['periode']['date_debut']).year==annee
        assert date.fromisoformat(r['periode']['date_fin']).year==annee
        assert empreintes_tables(application['engine'])==avant


@pytest.mark.parametrize('annee', [0,-1,10000])
def test_fonction_bornes_invalide_refuse_clairement(annee):
    with pytest.raises(HTTPException) as exc: _bornes(annee,None,None)
    assert exc.value.status_code==400
