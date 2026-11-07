"""Bornes de stockage des montants entrants, aucun plafond fiscal nouveau."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import pytest
from fastapi import HTTPException
from sqlalchemy import text
from routers.ecritures import _montant_decimal
from test_justificatifs_modeles_runtime_isole import (
    application, application090, application089, application087, migration,
    ecriture, original,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_complements_structure_postgres import refuser


@pytest.mark.parametrize('montant',[1e16,1e20])
@pytest.mark.parametrize('operation',['creation','modification'])
def test_depassement_fini_retourne422_et_preserve_journal(application,montant,operation):
    with closing(client(application)[0]) as api:
        sid=ok(api.get('/api/auth/me'))['societe_id']
        eid=ecriture(api,validee=False)
        avant=original(application,eid)
        payload={'date':date.today().isoformat(),'journal':'BQ','reference':'CAPACITE-FICTIVE458',
            'libelle':'Ne doit pas remplacer le brouillon fictif',
            'lignes':[{'compte':'5141','debit':montant},{'compte':'1111','credit':montant}]}
        r=(api.post('/api/ecritures',json=payload) if operation=='creation' else
           api.patch(f'/api/ecritures/{eid}',json=payload))
        assert original(application,eid)==avant
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid'),{'sid':sid})==1
        assert r.status_code==422,r.text
        assert 'montant' in str(r.json()['detail']).lower()


@pytest.mark.parametrize('valeur',['10000000000000000','9999999999999999.995','-10000000000000000'])
def test_helper_refuse_depassement_apres_arrondi_existant(valeur):
    with pytest.raises(HTTPException) as exc:_montant_decimal(Decimal(valeur))
    assert exc.value.status_code==422


@pytest.mark.parametrize('valeur,attendu',[
    ('9999999999999999.99','9999999999999999.99'),
    ('9999999999999999.994','9999999999999999.99'),
    ('100.105','100.11'),
])
def test_helper_conserve_limites_decimal_valides_et_arrondi(valeur,attendu):
    assert _montant_decimal(Decimal(valeur))==Decimal(attendu)


def test_pg_confirme_precision_et_limite_valide_api(application):
    with application['engine'].connect() as db:
        cols=db.execute(text("SELECT column_name,numeric_precision,numeric_scale FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='lignes_ecriture' AND column_name IN ('debit','credit') ORDER BY column_name")).all()
        assert cols==[('credit',18,2),('debit',18,2)]
        assert db.scalar(text("SELECT '9999999999999999.994'::numeric(18,2)"))==Decimal('9999999999999999.99')
    refuser(application['engine'],"SELECT '10000000000000000'::numeric(18,2)",'22003')
    refuser(application['engine'],"SELECT '9999999999999999.995'::numeric(18,2)",'22003')
    with closing(client(application)[0]) as api:
        # Plus grand float représentable avant10^16 ; aucune conversion de
        # l'API existante vers un nouveau type Decimal n'est introduite ici.
        montant=9999999999999998
        r=api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ',
            'reference':'LIMITE-FICTIVE458','libelle':'Borne technique fictive',
            'est_validee':True,'lignes':[{'compte':'5141','debit':montant},{'compte':'1111','credit':montant}]})
        eid=ok(r,201)['id']
        for route in ('balance','grand-livre'):
            lecture=api.get('/api/ecritures/reporting/'+route,params={'exercice':date.today().year})
            assert lecture.status_code==200,lecture.text
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT est_validee FROM ecritures WHERE id=:id'),{'id':eid}) is True
            assert db.execute(text('SELECT debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':eid}).all()==[(0,montant),(montant,0)]
