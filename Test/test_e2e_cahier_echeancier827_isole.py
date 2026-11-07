"""FAC015 : échéancier contractuel 50/50 et règlement partiel, copie indépendante."""
from decimal import Decimal as D
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_cycle775_support import officialiser,valider_journal,payer
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_cahier_avant_is823_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def echeancier(api,fid,jour):return ok(api.get(f'/api/factures/{fid}/echeancier',params={'date_reference':jour}))

@pytest.mark.parametrize('largeur',[1440,390])
def test_827_echeancier_contractuel_paiement_et_etic(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'echeancier827') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='C-SERVICE');tiers=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201)
  a=next(a for a in DATA['articles'] if a['code']=='S-VTE');article=ok(api.post('/api/articles',json={'code':a['code'],'designation':a['designation'],'is_stockable':False,'stock_actuel':0,'prix_vente_ht':1000,'tva':20,'compte_vente':'7124'}),201)
  b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  page.goto(application['web_url']+'/factures');page.get_by_role('button',name='Nouvelle facture',exact=True).click();m=page.get_by_role('dialog',name='Nouvelle facture',exact=True);champ(m,'Date *').fill('2025-04-01');m.get_by_placeholder('Rechercher un',exact=False).fill(tiers['nom']);m.get_by_text(tiers['nom'],exact=True).click();m.get_by_placeholder('N° BC, bon de commande...').fill('VAR-ECHEANCIER-827');m.get_by_placeholder('Description ou article...').fill(article['designation']);m.locator('li').filter(has_text=article['designation']).click();ed=m.locator('.hp-invoice-line-editor');ed.locator('input[type=number]').nth(0).fill('1');ed.locator('input[type=number]').nth(1).fill('1000')
  m.get_by_role('button',name='Échéancier',exact=True).click();m.get_by_role('button',name='50 / 50',exact=True).click();rows=m.locator('[class*="echeancierRows"] > div');expect(rows).to_have_count(2)
  for i,jour in enumerate(['2025-04-30','2025-05-31']):rows.nth(i).locator('input[type=date]').fill(jour);expect(rows.nth(i).locator('input[type=number]')).to_have_value('50')
  m.get_by_role('button',name='Enregistrer en brouillon',exact=False).click()
  with page.expect_response(lambda r:r.url.endswith('/api/factures') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer le brouillon',exact=True).click()
  f=ok(r.value,201);fid=f['id'];m.wait_for(state='hidden');assert D(str(f['total_ttc']))==1200
  initial=echeancier(api,fid,'2025-04-01');assert initial['personnalise'] and [(e['date_echeance'],D(str(e['montant']))) for e in initial['echeances']]==[('2025-04-30',D(600)),('2025-05-31',D(600))]
  f,_=officialiser(page,application,f,tiers);valider_journal(page,application,1);payer(page,application,f,tiers,600,'2025-04-30','VAR-ECHEANCIER-PAY-827',banque);valider_journal(page,application,1)
  es=ok(api.get('/api/ecritures',params={'exercice':2025}));assert len(es)==2 and all(e['est_validee'] for e in es)
  for journal,jour,attendu in [('VT','2025-04-01',{'3421':(1200,0),'7124':(0,1000),'4455':(0,200)}),('BQ','2025-04-30',{'5141':(600,0),'3421':(0,600)})]:
   e=next(e for e in es if e['journal']==journal);assert e['date']==jour and {l['compte']:(D(str(l['debit'])),D(str(l['credit']))) for l in e['lignes']}=={k:tuple(map(D,v)) for k,v in attendu.items()}
  avant=core(application,sid);controle={}
  for jour,retard in [('2025-05-30',0),('2025-05-31',0),('2025-06-01',1)]:
   s=echeancier(api,fid,jour);controle[jour]=s;assert D(str(s['reste_du']))==600 and s['nb_ouvertes']==1 and s['echeances'][0]['reste_du']==0 and s['echeances'][1]['reste_du']==600 and s['prochaine_echeance']['date_echeance']=='2025-05-31' and s['echeances'][1]['jours_retard']==retard
  f=next(f for f in ok(api.get('/api/factures',params={'exercice':2025})) if f['id']==fid);assert f['statut']=='partiellement_payee' and f['date_echeance']=='2025-04-30' and f['date_prochaine_echeance']=='2025-05-31'
  page.goto(application['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=f['numero']);expect(row.locator('td').nth(9)).to_contain_text('31/05/25');row.click();expect(page.get_by_text('Échéancier de paiement',exact=True)).to_be_visible();expect(page.get_by_text('30/04/25',exact=True).first).to_be_visible();expect(page.get_by_text('31/05/25',exact=True).first).to_be_visible();expect(page.get_by_text('Réglée',exact=True)).to_be_visible();page.reload();page.locator('tbody tr').filter(has_text=f['numero']).click();expect(page.get_by_text('Échéancier de paiement',exact=True)).to_be_visible()
  etic=ok(api.get('/api/etats/etic/2025'));b6=next(s for s in etic['sections'] if s['code']=='B6');ligne=next(l for l in b6['automatique']['lignes'] if l['compte']=='3421');assert D(str(ligne['echeance_auto_total']))==600 and not ligne['echeance_auto_anomalies_sources'] and D(str(ligne['echeance_auto']['echues']))==600;assert core(application,sid)==avant
  refus=api.put(f'/api/factures/{fid}/echeancier',json={'echeances':[{'date_echeance':'2025-04-30','montant':600},{'date_echeance':'2025-05-31','montant':600}]});assert refus.status_code==409 and core(application,sid)==avant
  preuve['echeancier827']={'facture':f,'initial':initial,'controles_dates':controle,'etic_b6':b6,'ecritures':es,'refus_modification_apres_paiement':refus.json(),'journal_inchange_pendant_controles':True};preuve['cas'].append({'id':'HP-FAC-015','statut':'Réussi'})
