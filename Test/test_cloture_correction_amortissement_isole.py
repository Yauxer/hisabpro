"""Clôture après correction seule : oracles comptables et API/PG nonce réels."""
from contextlib import closing
import pytest
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,reconcilier,
)
from test_tva_calcul_cloture_isole import dossier
from test_immobilisations_mutations_concurrentes_isole import autre_immo
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from recette_restauration_consolidee_084 import empreintes_tables
from sqlalchemy import text


@pytest.mark.parametrize('montant',[2000,1000,3000])
def test_cloture_reconnait_correction_exacte_et_conserve_refus_des_ecarts(application,montant):
    with closing(client(application)[0]) as api:
        p,_=dossier(api);immo=autre_immo(api,p['a']);iid=immo['id']
        ok(api.post(f"/api/ecritures/{immo['ecriture_acquisition_id']}/valider"))
        correction=ok(reconcilier(api,'corriger',p['a'],iid))['generees'][0]['ecriture_id']
        if montant!=2000:
            # Cas négatif préparé sur brouillon fictif, avant son unique validation.
            ok(api.patch(f'/api/ecritures/{correction}',json={'lignes':[{'compte':'61935','debit':montant},{'compte':'28355','credit':montant}]}))
        ok(api.post(f'/api/ecritures/{correction}/valider'))
        avant=originaux(application,p['s']);tables_avant=empreintes_tables(application['engine'])
        r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
        if montant==2000:
            assert r.status_code==200,r.text
            assert r.json()['resultat_net']==-5000 and r.json()['a_nouveaux_sur']==p['a']+1
            assert api.get('/api/fec/export',params={'exercice':p['a']}).status_code==200
            apres=originaux(application,p['s'])
            for t,lignes in avant.items():assert all(l in apres[t] for l in lignes)
        else:
            assert r.status_code==400 and 'dotation' in r.text.lower(),r.text
            assert originaux(application,p['s'])==avant
            tables_apres=empreintes_tables(application['engine'])
            assert {k:v for k,v in tables_apres.items() if k!='audit_actions'}=={k:v for k,v in tables_avant.items() if k!='audit_actions'}
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':p['s'],'r':f"AM-{p['a']}-{iid}"})==0
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':p['s'],'r':f"RECON-AMORT-{p['a']}-{iid}"})==1


@pytest.mark.parametrize('perimetre',['societe','exercice'])
def test_correction_dun_autre_perimetre_ne_fait_pas_disparaitre_la_dotation_manquante(application,perimetre):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        p,_=dossier(api);immo=autre_immo(api,p['a']);iid=immo['id']
        ok(api.post(f"/api/ecritures/{immo['ecriture_acquisition_id']}/valider"))
        if perimetre=='societe':dossier(autre);cible=autre;annee=p['a']
        else:cible=api;annee=p['a']+1
        ok(cible.post('/api/ecritures',json={'date':f'{annee}-01-01','journal':'AM','reference':f"RECON-AMORT-{p['a']}-{iid}",
            'libelle':'Référence incohérente fictive501','est_validee':True,
            'lignes':[{'compte':'61935','debit':2000},{'compte':'28355','credit':2000}]}),201)
        avant=originaux(application,p['s'])
        r=api.post(f"/api/cloture/cloturer?exercice={p['a']}")
        assert r.status_code==400 and 'dotation' in r.text.lower(),r.text
        assert originaux(application,p['s'])==avant
