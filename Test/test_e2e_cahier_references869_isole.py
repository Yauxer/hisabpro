"""NEG009 : conserver02 et002 comme deux références textuelles distinctes."""
import csv,hashlib
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from cahier_etats803_support import telecharger,nombre,ENTETES
from navigation823_support import navigations_completes823
from test_e2e_cahier_plafonds843_isole import valider843
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_869_references_textuelles_sources_fec_etic(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'references869') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='F-CONTROLE');t=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'fournisseur','compte_fournisseur':'4411'}),201);a=next(a for a in DATA['articles'] if a['code']=='S-ACH');a=ok(api.post('/api/articles',json={'code':a['code'],'designation':a['designation'],'is_stockable':False,'prix_achat_ht':200,'prix_vente_ht':0,'tva':20,'compte_achat':'6125'}),201);fs=[]
  for ref in ['02','002']:
   f=ok(api.post('/api/factures',json={'type':'achat','date':'2025-12-02','date_echeance':'2025-12-31','tiers':t['nom'],'tiers_id':t['id'],'reference':ref,'lignes':[{'article_id':a['id'],'description':a['designation'],'quantite':1,'prix_unitaire':200,'tva':20}]}),201);ok(api.post(f'/api/factures/{f["id"]}/valider'));ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'));fs.append(f)
  valider843(api);avant=core(application,sid);assert len(avant)==2 and {e[4] for e in avant}=={'02','002'} and all(any(l[1]=='6125' and D(str(l[2]))==200 for l in e[8]) for e in avant);factures=ok(api.get('/api/factures',params={'exercice':2025}));assert len(factures)==2 and {f['reference'] for f in factures}=={'02','002'} and all(f['total_ttc']==240 for f in factures);ids={f['id'] for f in factures};assert len(ids)==2
  page.goto(application['web_url']+'/journal');expect(page.get_by_text('02',exact=True).first).to_be_visible();expect(page.get_by_text('002',exact=True).first).to_be_visible();post=[];page.on('request',lambda r:post.append(r.url.split('?')[0]) if r.method in ['POST','PUT','PATCH','DELETE'] else None);p=telecharger(page,'Export FEC',tmp_path,'references869.txt');reader=csv.DictReader(p.read_text(encoding='utf-8-sig').splitlines(),delimiter='\t');assert reader.fieldnames==ENTETES;rows=list(reader);assert len(rows)==6;groupes={}
  for ref in ['02','002']:
   g=[r for r in rows if r['Ref_Piece']==ref];assert len(g)==3 and sum(nombre(r['Montant_Debit']) for r in g)==240==sum(nombre(r['Montant_Credit']) for r in g);groupes[ref]={'nombre_lignes':len(g),'numero_ecriture':sorted({r['Num_Ecriture'] for r in g}),'debit':'240','credit':'240'}
  assert groupes['02']['numero_ecriture']!=groupes['002']['numero_ecriture']
  etic=ok(api.get('/api/etats/etic/2025'));b7=next(s for s in etic['sections'] if s['code']=='B7');l=next(l for l in b7['automatique']['lignes'] if l['compte']=='4411');assert l['echeance_auto_nb_factures']==2 and l['echeance_auto_nb_factures_historiques']==0 and D(str(l['echeance_auto_total']))==480 and D(str(l['echeance_auto_ecart']))==0 and D(str(l['echeance_auto_non_qualifie']))==0 and not l['echeance_auto_anomalies_sources'];assert D(str(l['echeance_auto']['echues']))==480
  page.goto(application['web_url']+'/etic');page.get_by_role('button',name='B — Compléments au Bilan et au CPC',exact=True).click();section=page.locator('#etic-B7');expect(section).to_be_visible();expect(section).to_contain_text('4411');assert not post and core(application,sid)==avant and ok(api.get('/api/factures',params={'exercice':2025}))==factures
  preuve['references869']={'sources':[{'id':f['id'],'reference':f['reference'],'ttc':f['total_ttc']} for f in factures],'fec':{'groupes':groupes,'lignes':6,'debit':'480','credit':'480','sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'etic_B7_4411':l,'aucune_mutation_http':True,'journal_et_factures_conserves':True,'limite':'Préconditions par API,lecture Journal,téléchargement FEC et ETIC dans Edge réel. Deux factures avec liens techniques d’origine ;aucun tiers/identifiant historique effacé ni réparation automatique.'};preuve['cas'].append({'id':'HP-NEG-009','statut':'Réussi'})
