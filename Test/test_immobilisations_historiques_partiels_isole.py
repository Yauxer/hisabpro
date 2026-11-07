"""Corrections de N et écarts antérieurs : pièces définitives conservées."""
from contextlib import closing
from datetime import date
from io import BytesIO
import re
import pytest
from pypdf import PdfReader
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration, reconcilier,
)
from test_registre_immobilisations_cloture_isole import acquisition
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from recette_restauration_consolidee_084 import empreintes_tables


@pytest.mark.parametrize('ouverture,dotation_initiale', [
    (4000,500), (4000,3000), (4000,2000), (3000,1000), (5000,1000),
])
def test_correction_annuelle_preserve_sources_et_reliquat_historique(
        application, ouverture, dotation_initiale):
    with closing(client(application)[0]) as api:
        annee = date.today().year-1
        ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
        payload=acquisition(annee-2);payload['designation']='Materiel fictif504'
        immo=ok(api.post('/api/immobilisations',params={'generer_ecriture':False},json=payload),201)
        iid=immo['id'];sid=ok(api.get('/api/societe/moi'))['id']
        ouv=ok(api.post('/api/immobilisations/reconciliation-historique/reconstituer-acquisitions',json={
            'exercice':annee,'items':[{'immo_id':iid,'mode':'reprise_anterieure','compte_contrepartie':'4481'}]}))['generees'][0]['ecriture_id']
        if ouverture!=4000:
            # Historique fictif incomplet préparé sur brouillon, jamais en
            # réécrivant une pièce définitive pour satisfaire un contrôle.
            ok(api.patch(f'/api/ecritures/{ouv}',json={'lignes':[
                {'compte':'2355','debit':10000},{'compte':'28355','credit':ouverture},
                {'compte':'4481','credit':10000-ouverture}]}))
        ok(api.post(f'/api/ecritures/{ouv}/valider'))
        ok(api.post('/api/ecritures',json={'date':f'{annee}-12-31','journal':'AM',
            'reference':f'AM-{annee}-{iid}','libelle':'Dotation historique fictive504',
            'est_validee':True,'lignes':[{'compte':'61935','debit':dotation_initiale},
                                       {'compte':'28355','credit':dotation_initiale}]}),201)
        sources=originaux(application,sid)
        correction=ok(reconcilier(api,'corriger',annee,iid))
        ecart=2000-dotation_initiale
        assert correction['nb_ecritures']==int(ecart!=0)
        if ecart:
            eid=correction['generees'][0]['ecriture_id']
            with application['engine'].connect() as c:
                lignes=c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'),{'id':eid}).all()
                attendu=[('28355',0,ecart),('61935',ecart,0)] if ecart>0 else [('28355',-ecart,0),('61935',0,-ecart)]
                assert lignes==attendu
            ok(api.post(f'/api/ecritures/{eid}/valider'))
        apres=originaux(application,sid)
        for table,lignes in sources.items():assert all(l in apres[table] for l in lignes)
        d=ok(api.get('/api/immobilisations/reconciliation-historique',params={'exercice':annee}))['items'][0]
        assert d['amortissement']['comptabilise_exercice']==2000
        assert d['amortissement']['attendu_exercice']==2000
        assert d['amortissement']['ecart_cumule']==4000-ouverture
        assert d['amortissement']['comptabilise_cumule']==ouverture+2000
        assert ok(reconcilier(api,'corriger',annee,iid))['nb_ecritures']==0
        assert originaux(application,sid)==apres
        livre=ok(api.get('/api/inventaire/livre',params={'exercice':annee}))['snapshot']['immobilisations']
        assert livre['amortissements_cumules']==6000 and livre['vnc']==4000
        assert livre['rapprochement']['ecart_amortissements']==4000-ouverture
        assert livre['rapprochement']['rapproche']==(ouverture==4000)
        tables_avant=empreintes_tables(application['engine'])
        r=api.post('/api/cloture/cloturer',params={'exercice':annee})
        if ouverture==4000:
            assert r.status_code==200 and r.json()['resultat_net']==-5000,r.text
            assert api.get('/api/fec/export',params={'exercice':annee}).status_code==200
            pdf=api.get('/api/inventaire/livre/pdf',params={'exercice':annee})
            assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-'),pdf.text[:300]
            doc=PdfReader(BytesIO(pdf.content));texte=re.sub(r'\s+',' ',' '.join(p.extract_text() for p in doc.pages))
            assert 'Materiel fictif504' in texte and '6 000,00' in texte and '4 000,00' in texte
        else:
            assert r.status_code==400 and 'Immobilisations non rapprochées' in r.text,r.text
            tables_apres=empreintes_tables(application['engine'])
            assert {k:v for k,v in tables_avant.items() if k!='audit_actions'}=={k:v for k,v in tables_apres.items() if k!='audit_actions'}
        fin=originaux(application,sid)
        for table,lignes in apres.items():assert all(l in fin[table] for l in lignes)
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':sid,'r':f'AM-{annee}-{iid}'})==1
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s AND reference=:r'),{'s':sid,'r':f'RECON-AMORT-{annee}-{iid}'})==int(ecart!=0)
