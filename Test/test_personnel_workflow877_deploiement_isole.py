"""Avant107 :pas de fallback des nouvelles capacités et pas d'activation cachée."""
from contextlib import closing
import pytest
from test_personnel_workflow877_isole import (
    application875,application873,application093,application092,application091,
    application090,application089,application087,migration,appliquer,client,ok,P,W,CAPS,creation)


def test_877_sans107_workflow_et_caps_mutation_indisponibles(application875):
    app=application875
    with closing(client(app)[0]) as api:
        me=ok(api.get('/api/auth/me'))
        assert api.get(W).status_code==503
        assert api.post(W,json=creation()).status_code==503
        assert api.post(P+'/habilitations',json={'utilisateur_id':me['id'],'capacite':'personnel.proposer','motif':'Refus avant107'}).status_code==503
        assert api.get('/api/employes').status_code==200


def test_877_installe_sans_activation_et_sans_droits_implicites(application875):
    app=application875;appliquer(app)
    with closing(client(app)[0]) as api:
        me=ok(api.get('/api/auth/me'))
        assert api.get(W).status_code==409
        assert api.post(W,json=creation()).status_code==409
        assert api.post(P+'/activation',json={'confirmation':'PROTEGER_PERSONNEL','motif':'Activation fictive'}).status_code==201
        assert api.get(W).status_code==403 and api.post(W,json=creation()).status_code==403
        assert ok(api.get(P+'/acces'))['capacites']==[]
