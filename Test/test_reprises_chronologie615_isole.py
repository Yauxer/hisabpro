"""Une annulation datée plus tard ne finance pas une nouvelle reprise antérieure."""
from contextlib import closing
from copy import deepcopy
from uuid import uuid4
import json
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_journal_cloture_concurrente_isole import moteur
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,dotation,corps,demande,PATH)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier


def test_615_annulation_future_ne_libere_pas_capacite_a_date_anterieure(application):
    with closing(client(application)[0]) as api:
        a=dotation(api);aid=a['id'];c=corps(api,aid,demande('1000'))
        s=ok(api.post(f'{PATH}/{aid}',json=c));r=s['reprises'][0]
        ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
        s=ok(api.post(f"{PATH}/{aid}/{r['id']}/annuler",json={'date':'2026-06-01','motif':'Risque fictif rétabli en juin'}))
        ok(api.post(f"/api/ecritures/{s['reprises'][0]['inverse_id']}/valider"))
        assert ok(api.get(f'{PATH}/{aid}'))['disponible']=='1000.00'
        avant=donnees_metier(application)
        refus=api.post(f'{PATH}/{aid}/apercu',json=demande('600',date='2026-03-01'))
        assert refus.status_code==409,refus.text
        assert donnees_metier(application)==avant
        # Vérification distincte du dernier rempart SQL sous LOGIN applicatif.
        # Aucun appel métier remplacé : tentative directe entièrement annulée.
        engine=moteur(application)
        try:
            with engine.connect() as db:
                tx=db.begin()
                try:
                    sid=ok(api.get('/api/societe/moi'))['id']
                    uid=ok(api.get('/api/auth/me'))['id']
                    eid=db.scalar(text("INSERT INTO ecritures(societe_id,exercice,date,journal,libelle,source,est_validee) VALUES(:s,2026,'2026-03-01','OD','Tentative fictive615','reprise_provision',false) RETURNING id"),{'s':sid})
                    db.execute(text("INSERT INTO lignes_ecriture(ecriture_id,compte,debit,credit) VALUES(:e,'1518',600,0),(:e,'7195',0,600)"),{'e':eid})
                    doc=deepcopy(r['faits']);doc['faits'].update(date='2026-03-01',montant='600.00')
                    with pytest.raises(DBAPIError) as exc:
                        db.execute(text('''INSERT INTO reprises_provisions(societe_id,ajustement_id,ecriture_id,cle,montant,faits,created_by)
                            VALUES(:s,:a,:e,:k,600,CAST(:f AS jsonb),:u)'''),
                            {'s':sid,'a':aid,'e':eid,'k':str(uuid4()),'f':json.dumps(doc),'u':uid})
                    assert exc.value.orig.pgcode=='23514'
                finally:tx.rollback()
        finally:engine.dispose()
        assert donnees_metier(application)==avant
        s=ok(api.post(f'{PATH}/{aid}/apercu',json=demande('600',date='2026-07-01')))
        assert s['capacite']['disponible_pour_date']=='1000.00'
