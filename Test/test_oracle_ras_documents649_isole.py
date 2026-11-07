"""Jeu humain649 confronté aux vraies API/Journal/FEC/états, PostgreSQL102 nonce."""
from contextlib import closing
from decimal import Decimal
from io import StringIO
import csv,json
import httpx
from sqlalchemy import text
from test_ras_documents647_isole import (
    application,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,
    application089,application087,migration,
)
from test_multi_societes_runtime_isole import ok
from test_e2e_prorata_inventaire_isole import ecriture,photo
from test_permissions_tva_runtime_isole import donnees_metier
from generer_annexe_ras_documents649 import jeu,OUT,PREUVE


def test_649_capital_achat_ras_documents_annulation_oracle_independant(application,tmp_path):
    d=jeu();o=d['oracle'];ids={}
    with httpx.Client(base_url=application['api_url']) as api:
        u=d['administrateur'];auth=ok(api.post('/api/auth/register',json={'nom':'Administrateur recette649','email':u['email'],'password':u['mot_de_passe'],'raison_sociale':d['societe']['nom']}))
        api.headers['Authorization']='Bearer '+auth['access_token'];sid=ok(api.get('/api/auth/me'))['societe_id']
        ok(api.patch('/api/societe/moi',json={'raison_sociale':d['societe']['nom'],**{k:v for k,v in d['societe'].items() if k!='nom'}}))
        if not any(x['annee']==2026 for x in ok(api.get('/api/exercices'))):ok(api.post('/api/exercices',json=d['exercice']),201)
        ok(api.put('/api/tva/parametres/2026',json={'credit_ouverture':0,'prorata_deduction_pct':100}))
        for cle,role in [('comptable','comptable'),('lecteur','lecture')]:
            x=d[cle];ok(api.post('/api/utilisateurs',json={'nom':cle+' fictif649','email':x['email'],'mot_de_passe':x['mot_de_passe'],'role':role}),201)
        tiers=ok(api.post('/api/tiers',json={'nom':d['fournisseur'],'type':'fournisseur'}),201)
        capital=int(d['societe']['capital_social'])
        ids['Capital']=ecriture(api,'2026-01-02',[('5141',capital,0),('1111',0,capital)],d['references']['capital'])
        f=ok(api.post('/api/factures',json={**d['facture'],'tiers':tiers['nom'],'tiers_id':tiers['id']}),201)
        assert ok(api.post(f"/api/factures/{f['id']}/valider"))['numero']=='DOC649-2026-001'
        ids['Achat']=ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))['ecriture_id'];ok(api.post(f"/api/ecritures/{ids['Achat']}/valider"))
        r=ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers_id':tiers['id'],'tiers':tiers['nom'],'date':d['date_operation'],'montant':o['tresorerie'],'mode':'virement','reference':d['references']['virement'],'comptabiliser':True}),201)
        with application['engine'].connect() as db:ids['Règlement']=db.scalar(text('SELECT ecriture_id FROM reglements WHERE id=:r'),{'r':r['id']})
        ok(api.post(f"/api/ecritures/{ids['Règlement']}/valider"))
        corps={'simulation':d['simulation'],'justification_quote_part':d['justification_quote_part']}
        p=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=corps))
        capture=ok(api.post(f"/api/reglements/{r['id']}/ras-tva",json={**corps,'reference':d['references']['ras'],'compte_destination':d['comptes']['capture_choisie'],'empreinte_apercu':p['empreinte_apercu'],'pieces_verifiees':True}))
        ids['Capture RAS']=capture['capture']['ecriture_id'];cid=capture['capture']['id'];ok(api.post(f"/api/ecritures/{ids['Capture RAS']}/valider"))
        assert capture['dossier']['simulation']['retenue_tva']==o['ras']
        resultats={}
        def verifier(phase):
            attendu=o[phase]
            with application['engine'].connect() as db:
                soldes=db.execute(text('SELECT l.compte,sum(l.debit-l.credit) AS solde FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s GROUP BY l.compte'),{'s':sid}).all()
                assert {c:int(v*100) for c,v in soldes}==attendu['soldes_cents']
                assert db.execute(text('SELECT count(*),bool_and(est_validee) FROM ecritures WHERE societe_id=:s'),{'s':sid}).one()==(attendu['pieces'],True)
                for p in o['pieces'][:attendu['pieces']]:
                    lignes=db.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:e'),{'e':ids[p['phase']]}).all()
                    assert sorted(lignes)==sorted((l['compte'],Decimal(l['debit_cents'])/100,Decimal(l['credit_cents'])/100) for l in p['lignes'])
                assert db.scalar(text('SELECT count(*) FROM mouvements_stock WHERE societe_id=:s'),{'s':sid})==0
            etats=ok(api.get('/api/etats/liasse/2026'))['etats'];assert etats['bilan']['equilibre']
            assert Decimal(str(etats['bilan']['actif']['total']['net']))==Decimal(attendu['actif'])
            assert Decimal(str(etats['bilan']['passif']['total']))==Decimal(attendu['passif'])
            assert Decimal(str(etats['cpc']['resultat_net']))==Decimal(attendu['resultat_avant_impot'])
            fec=api.get('/api/fec/export',params={'exercice':2026});assert fec.status_code==200,fec.text
            rows=list(csv.DictReader(StringIO(fec.content.decode('utf-8-sig')),delimiter='\t'));assert len(rows)==attendu['lignes']
            assert sum(Decimal(x['Montant_Debit'].replace(',','.')) for x in rows)==sum(Decimal(x['Montant_Credit'].replace(',','.')) for x in rows)==Decimal(attendu['debit'])
            assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==float(attendu['fournisseur'])
            resultats[phase]={'oracle':attendu,'fec_lignes':len(rows),'bilan':etats['bilan'],'resultat_comptable':etats['cpc']['resultat_net']}
            (tmp_path/(phase+'_FEC_FICTIF649.txt')).write_bytes(fec.content)
        verifier('avant_annulation')
        avant=photo(application,list(ids.values()));pdf=(OUT/PREUVE).read_bytes();fichiers=[]
        for _ in range(2):fichiers.append(ok(api.post(f"/api/attachments/ecriture/{ids['Capture RAS']}",files={'file':(PREUVE,pdf,'application/pdf')})))
        assert fichiers[0]['nom']!=fichiers[1]['nom']
        ok(api.post(f"/api/ecritures/{ids['Capture RAS']}/justificatifs",json={'reference':d['references']['complement'],'date_piece':d['date_operation'],'motif':'Complément documentaire fictif DOC649'}),201)
        assert photo(application,list(ids.values()))==avant
        assert ok(api.get(f"/api/reglements/{r['id']}/ras-tva"))['dossier']==capture['dossier']
        ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'date_annulation':d['date_operation'],'motif':d['motif_annulation']}))
        with application['engine'].connect() as db:
            ids['Annulation règlement']=db.scalar(text('SELECT ecriture_annulation_id FROM reglements WHERE id=:r'),{'r':r['id']})
            ids['Annulation RAS']=db.scalar(text('SELECT ecriture_id FROM ras_reglement_annulations WHERE capture_id=:c'),{'c':cid})
        for phase in ('Annulation règlement','Annulation RAS'):ok(api.post(f"/api/ecritures/{ids[phase]}/valider"))
        avant=photo(application,list(ids.values()))
        fich_ann=ok(api.post(f"/api/attachments/ecriture/{ids['Annulation RAS']}",files={'file':(PREUVE,pdf,'application/pdf')}))
        assert photo(application,list(ids.values()))==avant
        verifier('apres_annulation')
        avant=donnees_metier(application)
        for path in ('/api/tva/ras/registre/2026','/api/tva/ras/preparation/2026/11'):
            data=ok(api.get(path));l=next(x for x in data['lignes'] if x['capture_id']==cid)
            assert len(l['documents_od'])==3 and len(l['documents_annulation'])==1
            assert l['reference_attestation']==d['simulation']['reference_attestation']
            for fmt in ('csv','xlsx','pdf'):assert api.get(path+'/export/'+fmt,params={'empreinte':data['empreinte_sha256']}).status_code==200
        assert api.get(fich_ann['url']).content==pdf and donnees_metier(application)==avant
        assert api.post('/api/reglements',json={'facture_id':f['id'],'tiers':tiers['nom'],'date':d['date_operation'],'montant':'0.005','mode':'virement','reference':'REFUS-DOC649'}).status_code==422
        assert donnees_metier(application)==avant
        (tmp_path/'oracle649_preuve.json').write_text(json.dumps(resultats,ensure_ascii=False,indent=2),encoding='utf8')
