"""Jeu humain639 réellement exécuté via API native, calculs indépendants externes."""
from contextlib import closing
from datetime import date
from decimal import Decimal
from io import StringIO
import csv,json
import httpx
from sqlalchemy import text
from test_factures_liees635_isole import (
    application,application101,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,PATH)
from test_multi_societes_runtime_isole import ok
from test_e2e_prorata_inventaire_isole import ecriture,photo
from generer_annexe_societes639 import jeu


def test_639_deux_capitaux_factures_reglements_lettrages_oracle(application,tmp_path):
    d=jeu();oracle=d['oracle'];apis={};ids={};fids={};arts={};tiers={}
    try:
        a=httpx.Client(base_url=application['api_url']);apis['A']=a
        auth=ok(a.post('/api/auth/register',json={'nom':'Administrateur recette639','email':d['administrateur']['email'],'password':d['administrateur']['mot_de_passe'],'raison_sociale':d['societes']['A']['nom']}))
        a.headers['Authorization']='Bearer '+auth['access_token'];ids['A']=ok(a.get('/api/auth/me'))['societe_id']
        ids['B']=ok(a.post('/api/societes/nouvelle',json={'raison_sociale':d['societes']['B']['nom']}),201)['id']
        b=httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+ok(a.post(f'/api/societes/switcher/{ids["B"]}'))['access_token']});apis['B']=b
        eids=[]
        for soc,api in apis.items():
            ok(api.patch('/api/societe/moi',json={'raison_sociale':d['societes'][soc]['nom'],'prefixe_facture':d['societes'][soc]['prefixe'],'devise':'MAD','forme_juridique':'SARL','capital_social':10000,'regime_fiscal':'is','regime_tva':'encaissement'}))
            if not any(x['annee']==2026 for x in ok(api.get('/api/exercices'))):ok(api.post('/api/exercices',json={'annee':2026,'date_debut':'2026-01-01','date_fin':'2026-12-31'}),201)
            ok(api.put('/api/tva/parametres/2026',json={'credit_ouverture':0,'prorata_deduction_pct':100}))
            art=d['articles'][soc];arts[soc]=ok(api.post('/api/articles',json={**art,'prix_vente_ht':100,'prix_achat_ht':100,'tva':20}),201)['id']
            tiers[soc]=ok(api.post('/api/tiers',json={'type':'client' if soc=='A' else 'fournisseur','nom':d['tiers']['client_A' if soc=='A' else 'fournisseur_B']}),201)['id']
            eids.append(ecriture(api,'2026-01-02',[('5141',10000,0),('1111',0,10000)],'CAP-'+soc+'-639'))
        cap=photo(application,eids)
        l=ok(a.post(PATH,json={'acheteur_id':ids['B'],'client_id':tiers['A'],'fournisseur_id':tiers['B'],'cle':'63900000-0000-4000-8000-000000000001','justification':d['justification_liaison'],'association_verifiee':True}),201)
        f=ok(a.post('/api/factures',json={'type':'vente','date':d['facture']['date'],'tiers_id':tiers['A'],'tiers':d['tiers']['client_A'],'delai_paiement':60,'lignes':[{**x,'article_id':arts['A']} for x in d['facture']['lignes']]}),201);fids['A']=f['id']
        assert ok(a.post(f'/api/factures/{f["id"]}/valider'))['numero']=='ATLAS-2026-001'
        p=f'{PATH}/{l["id"]}/factures/{f["id"]}'
        corps={'nature_tva_achat':'charge','tva_deductible_pct':'100','lignes':[{'source_ligne_id':x['id'],'article_id':arts['B']} for x in f['lignes']]}
        preparation=ok(a.post(p+'/apercu',json=corps));s=ok(a.post(p,json={**corps,'cle':'63900000-0000-4000-8000-000000000002','empreinte':preparation['empreinte'],'correspondance_verifiee':True}),201)
        fids['B']=s['facture_achat_id'];assert ok(b.post(f'/api/factures/{fids["B"]}/valider'))['numero']=='RIF-2026-001'
        for soc,api in apis.items():
            eid=ok(api.post(f'/api/factures/{fids[soc]}/comptabiliser'))['ecriture_id'];ok(api.post(f'/api/ecritures/{eid}/valider'));eids.append(eid)
        # PayerB d'abord : aucun encaissement n'apparaît chezA automatiquement.
        for soc in ('B','A'):
            api=apis[soc];r=ok(api.post('/api/reglements',json={'facture_id':fids[soc],'tiers_id':tiers[soc],'tiers':d['tiers']['client_A' if soc=='A' else 'fournisseur_B'],'date':'2026-10-19','montant':600,'mode':'virement','reference':'VIR-'+soc+'-639','comptabiliser':True}),201)
            with application['engine'].connect() as db:eid=db.scalar(text('SELECT ecriture_id FROM reglements WHERE id=:id'),{'id':r['id']})
            ok(api.post(f'/api/ecritures/{eid}/valider'));eids.append(eid)
            if soc=='B':assert ok(a.get(f'/api/factures/{fids["A"]}/reglements'))['solde_restant']==600
        avant=photo(application,eids)
        for soc,api in apis.items():
            compte='3421' if soc=='A' else '4411'
            with application['engine'].connect() as db:ls=db.execute(text('SELECT l.id FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s AND l.compte=:c ORDER BY l.id'),{'s':ids[soc],'c':compte}).scalars().all()
            r=ok(api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':ls,'code':'AAA'}));assert r['nb']==2 and r['code']=='AAA'
        assert photo(application,eids)==avant and photo(application,eids[:2])==cap
        resultat={}
        for soc,api in apis.items():
            o=oracle['societes'][soc]
            with application['engine'].connect() as db:
                rows=db.execute(text('SELECT l.compte,sum(l.debit-l.credit) solde FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s AND e.exercice=2026 GROUP BY l.compte'),{'s':ids[soc]}).all()
                assert {x.compte:int(x.solde*100) for x in rows}==o['soldes_cents']
                assert db.execute(text('SELECT count(*),bool_and(est_validee) FROM ecritures WHERE societe_id=:s AND exercice=2026'),{'s':ids[soc]}).one()==(3,True)
                assert db.scalar(text('SELECT count(*) FROM mouvements_stock WHERE societe_id=:s'),{'s':ids[soc]})==0
                lignes=db.execute(text('SELECT e.reference,l.compte,l.debit,l.credit FROM ecritures e JOIN lignes_ecriture l ON l.ecriture_id=e.id WHERE e.societe_id=:s ORDER BY 1,2'),{'s':ids[soc]}).all()
                attendu=[(p['reference'],x['compte'],Decimal(x['debit_cents'])/100,Decimal(x['credit_cents'])/100) for p in oracle['pieces'] if p['societe']==soc for x in p['lignes']]
                assert sorted(lignes)==sorted(attendu)
            etats=ok(api.get('/api/etats/liasse/2026'))['etats'];assert etats['bilan']['equilibre']
            assert Decimal(str(etats['bilan']['actif']['total']['net']))==Decimal(o['actif'])
            assert Decimal(str(etats['bilan']['passif']['total']))==Decimal(o['passif'])
            assert Decimal(str(etats['cpc']['resultat_net']))==Decimal(o['resultat_avant_impot'])
            fec=api.get('/api/fec/export',params={'exercice':2026});assert fec.status_code==200,fec.text
            ls=list(csv.DictReader(StringIO(fec.content.decode('utf-8-sig')),delimiter='\t'));assert len(ls)==7
            assert sum(Decimal(x['Montant_Debit'].replace(',','.')) for x in ls)==sum(Decimal(x['Montant_Credit'].replace(',','.')) for x in ls)==Decimal(o['debit'])
            (tmp_path/f'FEC639_{soc}_FICTIF.txt').write_bytes(fec.content)
            assert ok(api.get(f'/api/factures/{fids[soc]}/reglements'))['solde_restant']==0
            resultat[soc]={'oracle':o,'etats':etats['bilan'],'fec_lignes':len(ls)}
        assert ok(a.get(f'{PATH}/factures/{fids["A"]}/correspondance'))['ecarts']==[]
        vue=ok(a.get(f'{PATH}/{l["id"]}/correspondances'));assert vue['total']==1
        for cote in ('vente','achat'):
            f=vue['items'][0][cote]['finances']
            assert (f['total_ttc'],f['solde_restant'],f['total_encaisse'],f['total_reglement_en_cours'])==('600.00','0.00','600.00','0.00')
        (tmp_path/'oracle639_preuve.json').write_text(json.dumps(resultat,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        for api in apis.values():api.close()
