"""Orchestration janvier-juin : aucun résultat attendu injecté comme écriture automatique."""
from collections import defaultdict
from decimal import Decimal as D
from sqlalchemy.orm import Session
from playwright.sync_api import expect
import models
from cahier_formulaires773_support import DATA,ok,champ,ouvrir_avance
from cahier_cycle775_support import OPS,identifiants,nouvelle_ecriture,valider_journal,officialiser,payer,cycle,stock
from cahier_suite777_support import core,suite


def manuelle(page,app,sid,ref,preuve):
 o=OPS[ref];avant=identifiants(app,sid);page.goto(app['web_url']+'/journal');page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog');champ(m,'Date comptable *').fill(o['date']);champ(m,'Journal *','select').select_option(o['journal']);champ(m,'Référence du justificatif').fill(ref);champ(m,"Libellé de l'écriture *").fill(o['description'])
 rows=m.locator('tbody tr')
 for _ in range(max(0,len(o['lignes'])-rows.count())):m.get_by_role('button',name='Ajouter une ligne',exact=True).click()
 expect(rows).to_have_count(max(3,len(o['lignes'])))
 for i,l in enumerate(o['lignes']):
  assert not l.get('tiers'),'Les lignes manuelles avec tiers doivent passer par un flux auxiliaire explicite.'
  rows.nth(i).get_by_placeholder('Ex: 6111',exact=True).fill(l['compte'])
  for k,col in [('debit','Débit (MAD)'),('credit','Crédit (MAD)')]:
   if D(l[k]):rows.nth(i).locator(f'td[data-label="{col}"] input').fill(l[k])
 m.get_by_label('Valider immédiatement',exact=False).uncheck()
 with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as r:m.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
 ok(r.value,201);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,ref,preuve);valider_journal(page,app,1)
 for c in DATA['cas_recette']:
  if c['module']=='Fiscalité' and c['objectif']=='Comptabiliser '+o['description']:preuve['cas'].append({'id':c['id'],'statut':'Réussi'})


def facture_service(api,page,app,sid,tiers,article,ref,pu,date,echeance,preuve,cas,reference_piece=None):
 avant=identifiants(app,sid);achat=tiers['type']=='fournisseur';page.goto(app['web_url']+'/factures');page.get_by_role('button',name='Nouvelle facture',exact=True).click();m=page.get_by_role('dialog',name='Nouvelle facture',exact=True)
 if achat:m.get_by_role('button',name='Achat',exact=True).click()
 champ(m,'Date *').fill(date);m.get_by_placeholder('Rechercher un',exact=False).fill(tiers['nom']);m.get_by_text(tiers['nom'],exact=True).click();m.get_by_placeholder('N° porté sur la facture du fournisseur' if achat else 'N° BC, bon de commande...').fill(reference_piece or ref);m.get_by_label('Échéance de la nouvelle facture',exact=True).fill(echeance);m.get_by_placeholder('Description ou article...').fill(article['designation']);m.locator('li').filter(has_text=article['designation']).click();ed=m.locator('.hp-invoice-line-editor');ed.locator('input[type="number"]').nth(0).fill('1');ed.locator('input[type="number"]').nth(1).fill(str(pu));m.get_by_role('button',name='Enregistrer en brouillon',exact=False).click()
 with page.expect_response(lambda r:r.url.endswith('/api/factures') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer le brouillon',exact=True).click()
 f=ok(r.value,201);assert D(str(f['total_ttc']))==D(str(pu))*D('1.2');m.wait_for(state='hidden');f,_=officialiser(page,app,f,tiers);nouvelle_ecriture(app,sid,avant,ref,preuve);valider_journal(page,app,1);preuve['cas'].append({'id':cas,'statut':'Réussi'});return f


def effet(api,page,app,sid,f,tiers,banque,montant,date,echeance,ref,preuve,cas):
 avant=identifiants(app,sid);page.goto(app['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=f['numero']);row.get_by_title('Payer le fournisseur' if f['type']=='achat' else 'Encaisser le client',exact=True).click();m=page.get_by_role('dialog');champ(m,'Montant *').fill(str(montant));champ(m,'Date *').fill(date);champ(m,'Mode','select').select_option('effet');champ(m,'Banque','select').select_option(banque['banque']);champ(m,'Échéance').fill(echeance);m.get_by_placeholder('N° chèque, virement...').fill(ref)
 with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer',exact=True).click()
 reg=ok(r.value,201);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,ref,preuve);valider_journal(page,app,1);preuve['cas'].append({'id':cas,'statut':'Réussi'});return reg


def transition(api,page,app,sid,reg,action,date,frais,ref,preuve,cas):
 avant=identifiants(app,sid);page.goto(app['web_url']+'/effets');champ(page,'Statut','select').select_option('tous');row=page.locator('tbody tr').filter(has_text=reg['reference']);titre={'payer':"Payer l'effet",'remettre':"Remettre à l'encaissement",'encaisser':"Confirmer l'encaissement"}[action];row.get_by_title(titre,exact=True).click();m=page.get_by_role('dialog');m.locator('input[type="date"]').fill(date)
 if m.get_by_placeholder('0.00',exact=True).count():m.get_by_placeholder('0.00',exact=True).fill(str(frais))
 bouton={'payer':'Confirmer le paiement','remettre':"Remettre à l'encaissement",'encaisser':"Confirmer l'encaissement"}[action]
 with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{reg["id"]}/transition') and r.request.method=='POST') as r:m.get_by_role('button',name=bouton,exact=True).click()
 ok(r.value);assert r.value.request.post_data_json['date_effective']==date;m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,ref,preuve);valider_journal(page,app,1);preuve['cas'].append({'id':cas,'statut':'Réussi'})


def semestre(api,page,app,sid,tiers,articles,banque,preuve,tmp_path,apres_effet_client=None,accord_compensation=None):
 cycle(api,page,app,sid,tiers,articles,preuve,tmp_path,banque=banque);services={};effets={}
 def intercaler(etape):
  if etape=='apres_cheque':manuelle(page,app,sid,'TVA-01',preuve)
  elif etape=='avant_avoir':services['achat']=facture_service(api,page,app,sid,tiers['F-SERVICE'],articles['S-ACH'],'ACH-SERVICE',12000,'2025-02-10','2025-02-15',preuve,'HP-FAC-005')
  elif etape=='apres_avoir':
   avant=identifiants(app,sid);payer(page,app,services['achat'],tiers['F-SERVICE'],14400,'2025-02-15','ACH-SERVICE-PAY',banque);nouvelle_ecriture(app,sid,avant,'ACH-SERVICE-PAY',preuve);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-PAY-008','statut':'Réussi'});manuelle(page,app,sid,'TVA-02',preuve)
  elif etape=='apres_vente2':
   f=next(f for f in ok(api.get('/api/factures',params={'exercice':2025})) if f['id']==preuve['cycle']['factures'][1]);effets['fournisseur']=effet(api,page,app,sid,f,tiers['F-MARCH'],banque,14400,'2025-03-01','2025-03-20','EFF-F01',preuve,'HP-PAY-009')
 suite(api,page,app,sid,tiers,articles,preuve,intercaler=intercaler,accord_compensation=accord_compensation)
 transition(api,page,app,sid,effets['fournisseur'],'payer','2025-03-20',0,'EFF-F01-PAY',preuve,'HP-PAY-011');manuelle(page,app,sid,'TVA-03',preuve)
 v2=next(f for f in ok(api.get('/api/factures',params={'exercice':2025})) if f['id']==preuve['suite777']['facture2']);reg=effet(api,page,app,sid,v2,tiers['C-MARCH'],banque,10000,'2025-04-01','2025-05-15','EFF-C01',preuve,'HP-PAY-012');transition(api,page,app,sid,reg,'remettre','2025-05-15',0,'EFF-C01-REM',preuve,'HP-PAY-013');transition(api,page,app,sid,reg,'encaisser','2025-05-16',10,'EFF-C01-ENC',preuve,'HP-PAY-014')
 if apres_effet_client is not None:apres_effet_client()
 avant=identifiants(app,sid);page.goto(app['web_url']+'/acomptes');page.get_by_role('button',name='Nouvel acompte',exact=True).click();m=page.get_by_role('dialog',name='Nouvel acompte',exact=True);m.get_by_role('button',name='Acompte client reçu',exact=False).click();champ(m,'Date').fill('2025-06-01');m.locator('input[role="combobox"]').fill(tiers['C-SERVICE']['nom']);m.get_by_role('option').filter(has_text=tiers['C-SERVICE']['nom']).click();champ(m,'Montant (MAD)').fill('24000');champ(m,'Compte bancaire','select').select_option(str(banque['id']));m.get_by_placeholder('N° chèque, virement...').fill('AC-C01');ouvrir_avance(m,'TVA, comptabilisation & notes');expect(champ(m,'Taux TVA','select')).to_have_value('20')
 with page.expect_response(lambda r:r.url.endswith('/api/acomptes') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer l’acompte',exact=True).click()
 ac=ok(r.value,201);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'AC-C01',preuve);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-PAY-015','statut':'Réussi'})
 vente=facture_service(api,page,app,sid,tiers['C-SERVICE'],articles['S-VTE'],'VENTE-SERVICE',120000,'2025-06-15','2025-06-30',preuve,'HP-FAC-008')
 avant=identifiants(app,sid);page.goto(app['web_url']+'/acomptes');page.locator('tbody tr').filter(has_text=tiers['C-SERVICE']['nom']).get_by_title('Imputer sur une facture',exact=True).click();m=page.get_by_role('dialog');m.locator('select').select_option(str(vente['id']));champ(m,'Montant à imputer (MAD)').fill('24000');champ(m,'Date d’imputation').fill('2025-06-15')
 with page.expect_response(lambda r:r.url.endswith(f'/api/acomptes/{ac["id"]}/imputer')) as r:m.get_by_role('button',name='Imputer l’acompte',exact=True).click()
 assert ok(r.value)['montant_disponible']==0;m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'AC-C01-IMP',preuve);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-PAY-016','statut':'Réussi'})
 avant=identifiants(app,sid);payer(page,app,vente,tiers['C-SERVICE'],120000,'2025-06-30','VENTE-SERVICE-PAY',banque);nouvelle_ecriture(app,sid,avant,'VENTE-SERVICE-PAY',preuve);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-PAY-017','statut':'Réussi'});manuelle(page,app,sid,'TVA-06',preuve)
 for f in [vente,services['achat'],v2]:assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant']==0
 stock(app,articles['M-01']['id'],60,110)
 for a in [articles['S-ACH'],articles['S-VTE']]:
  with Session(app['engine']) as db:assert db.query(models.MouvementStock).filter_by(societe_id=sid,article_id=a['id']).count()==0
 expected=[o for o in DATA['operations'] if o['date']<='2025-06-30'];refs=[o['reference'] for o in preuve['operations']];assert len(refs)==len(set(refs))==len(expected) and set(refs)=={o['reference_recette'] for o in expected};assert [o['date'] for o in preuve['operations']]==sorted(o['date'] for o in preuve['operations'])
 attendu=defaultdict(lambda:D(0));reel=defaultdict(lambda:D(0))
 for o in expected:
  for l in o['lignes']:attendu[l['compte']]+=D(l['debit'])-D(l['credit'])
 with Session(app['engine']) as db:
  es=db.query(models.Ecriture).filter_by(societe_id=sid).all();assert len(es)==len(expected) and all(e.est_validee for e in es);ls=[l for e in es for l in e.lignes];assert len(ls)==sum(len(o['lignes']) for o in expected)
  for l in ls:reel[l.compte]+=D(str(l.debit))-D(str(l.credit))
  assert {k:v for k,v in reel.items() if v}=={k:v for k,v in attendu.items() if v};total=sum(D(str(l.debit)) for l in ls);assert total==sum(D(str(l.credit)) for l in ls)==sum(D(l['debit']) for o in expected for l in o['lignes'])
 preuve['semestre789']={'ecritures':len(expected),'lignes':len(ls),'debit_credit':str(total),'soldes':{k:str(v) for k,v in sorted(reel.items()) if v},'references':refs,'stock':60,'cmup':110,'frais_effet':'10.00','ordre_chronologique':True,'limite':'Arrêt30/06/2025 ;les écritures TVA sont saisies manuellement conformément aux fichesFIS015/016/017/018, pas des déclarations automatiques. Pas de clôture ni de dotation annuelle anticipée.'}
