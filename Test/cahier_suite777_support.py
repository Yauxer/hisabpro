"""Suite des vrais formulaires du cahier :chèque,retour,vente etcrédit client."""
from decimal import Decimal
from sqlalchemy.orm import Session
from playwright.sync_api import expect
import models
from cahier_formulaires773_support import DATA,ok,champ
from cahier_cycle775_support import identifiants,nouvelle_ecriture,stock,valider_journal,officialiser,payer,OPS
D=Decimal

def core(app,sid):
 with Session(app['engine']) as db:
  return tuple((e.id,e.date,e.date_piece,e.journal,e.reference,e.libelle,e.numero_ecriture,e.est_validee,tuple((l.id,l.compte,l.debit,l.credit,l.tiers_id,l.compte_auxiliaire_snapshot) for l in sorted(e.lignes,key=lambda l:l.id))) for e in db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id))

def suite(api,page,app,sid,tiers,articles,preuve,intercaler=None,accord_compensation=None):
 c=tiers['C-MARCH'];a=articles['M-01'];initial=core(app,sid);assert len(initial)>=7
 ventes=ok(api.get('/api/factures',params={'exercice':2025}));vente=next(f for f in ventes if f['id']==preuve['cycle']['factures'][2]);banque=ok(api.get('/api/banques'))[0]
 avant=identifiants(app,sid);page.goto(app['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=vente['numero']);row.get_by_title('Encaisser le client',exact=True).click();m=page.get_by_role('dialog');champ(m,'Date *').fill('2025-01-26');champ(m,'Montant *').fill('20000');champ(m,'Mode','select').select_option('cheque');champ(m,'Banque','select').select_option(banque['banque']);m.get_by_placeholder('N° chèque, virement...').fill('CHQ-01')
 with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer',exact=True).click()
 reg=ok(r.value,201);assert reg['statut']=='portefeuille';m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'CHQ-01',preuve);valider_journal(page,app,1);s=ok(api.get(f'/api/factures/{vente["id"]}/reglements'));assert s['solde_restant']==0 and s['total_encaisse']==10000 and s['total_reglement_en_cours']==20000;preuve['cas'].append({'id':'HP-PAY-005','statut':'Réussi'})
 if intercaler:intercaler('apres_cheque')
 for action,date,titre,bouton,reference,cas in [
  ('remettre','2025-02-01',"Remettre à l'encaissement","Remettre à l'encaissement",'CHQ-01-REM','HP-PAY-006'),
  ('encaisser','2025-02-05',"Confirmer l'encaissement","Confirmer l'encaissement",'CHQ-01-ENC','HP-PAY-007')]:
  avant=identifiants(app,sid);page.goto(app['web_url']+'/effets');champ(page,'Statut','select').select_option('tous');row=page.locator('tbody tr').filter(has_text='CHQ-01');row.get_by_title(titre,exact=True).click();m=page.get_by_role('dialog');m.locator('input[type="date"]').fill(date)
  if m.get_by_placeholder('0.00',exact=True).count():m.get_by_placeholder('0.00',exact=True).fill('0')
  with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{reg["id"]}/transition') and r.request.method=='POST') as r:m.get_by_role('button',name=bouton,exact=True).click()
  ok(r.value);assert r.value.request.post_data_json['date_effective']==date;m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,reference,preuve);valider_journal(page,app,1);preuve['cas'].append({'id':cas,'statut':'Réussi'})
 s=ok(api.get(f'/api/factures/{vente["id"]}/reglements'));assert s['total_encaisse']==30000 and s['solde_restant']==0
 if intercaler:intercaler('avant_avoir')
 avant=identifiants(app,sid);page.goto(app['web_url']+'/factures');page.locator('tbody tr').filter(has_text=vente['numero']).click();page.get_by_role('button',name='Créer un avoir',exact=True).click();m=page.get_by_role('dialog',name='Créer un avoir',exact=False);champ(m,"Date de l'avoir *").fill('2025-02-10');champ(m,"Nature de l'avoir",'select').select_option('retour_annulation');m.get_by_placeholder('Retour marchandise, remise après facture...').fill('AV-01 — retour fictif10unités');m.get_by_role('checkbox',name='Retour physique de marchandise',exact=False).check();line=m.locator('tbody tr').filter(has_text=a['designation']);line.get_by_role('checkbox').check();line.locator('input[type="number"]').fill('10')
 with page.expect_response(lambda r:r.url.endswith('/api/avoirs') and r.request.method=='POST') as r:m.get_by_role('button',name="Créer l'avoir",exact=False).click()
 av=ok(r.value,201);assert av['total_ttc']==3000 and av['retour_stock'];m.wait_for(state='hidden');stock(app,a['id'],100,110);page.goto(app['web_url']+'/avoirs');page.locator('tbody tr').filter(has_text=av['numero']).click()
 with page.expect_response(lambda r:r.url.endswith(f'/api/avoirs/{av["id"]}/comptabiliser')) as r:page.get_by_role('button',name='Comptabiliser',exact=True).last.click()
 ok(r.value);nouvelle_ecriture(app,sid,avant,'AV-01',preuve);stock(app,a['id'],110,110);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-FAC-006','statut':'Réussi'})
 if intercaler:intercaler('apres_avoir')
 avant=identifiants(app,sid);page.goto(app['web_url']+'/factures');page.get_by_role('button',name='Nouvelle facture',exact=True).click();m=page.get_by_role('dialog',name='Nouvelle facture',exact=True);champ(m,'Date *').fill('2025-03-01');m.get_by_placeholder('Rechercher un',exact=False).fill(c['nom']);m.get_by_text(c['nom'],exact=True).click();m.get_by_placeholder('N° BC, bon de commande...').fill('VENTE-02');m.get_by_label('Échéance de la nouvelle facture',exact=True).fill('2025-05-15');m.get_by_placeholder('Description ou article...').fill(a['designation']);m.locator('li').filter(has_text=a['designation']).click();ed=m.locator('.hp-invoice-line-editor');ed.locator('input[type="number"]').nth(0).fill('50');ed.locator('input[type="number"]').nth(1).fill('300');m.get_by_role('button',name='Enregistrer en brouillon',exact=False).click()
 with page.expect_response(lambda r:r.url.endswith('/api/factures') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer le brouillon',exact=True).click()
 v2=ok(r.value,201);assert v2['total_ttc']==18000;m.wait_for(state='hidden');v2,row=officialiser(page,app,v2,c);nouvelle_ecriture(app,sid,avant,'VENTE-02',preuve);stock(app,a['id'],60,110);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-FAC-007','statut':'Réussi'})
 if intercaler:intercaler('apres_vente2')
 avant=core(app,sid);page.goto(app['web_url']+'/avoirs');page.locator('tbody tr').filter(has_text=av['numero']).click();page.get_by_role('button',name='Imputer sur une facture',exact=True).click();m=page.get_by_role('dialog',name=f'Imputer le crédit — {av["numero"]}',exact=True);champ(m,'Facture cible','select').select_option(str(v2['id']));champ(m,'Montant (MAD)').fill('3000');champ(m,'Date').fill('2025-03-01')
 if accord_compensation:
  m.get_by_role('checkbox',name='Accord de compensation signé',exact=False).check();m.get_by_label('Référence de l’accord signé',exact=True).fill(accord_compensation)
 with page.expect_response(lambda r:r.url.endswith(f'/api/avoirs/{av["id"]}/utiliser') and r.request.method=='POST') as r:m.get_by_role('button',name='Imputer le crédit',exact=True).click()
 ok(r.value);m.wait_for(state='hidden');assert core(app,sid)==avant
 avant=identifiants(app,sid);payer(page,app,v2,c,5000,'2025-03-05','PAY-V02',banque);nouvelle_ecriture(app,sid,avant,'VENTE-02-PAY',preuve);valider_journal(page,app,1);assert ok(api.get(f'/api/factures/{v2["id"]}/reglements'))['solde_restant']==10000;preuve['cas'].append({'id':'HP-PAY-010','statut':'Réussi'})
 refs=[o['reference'] for o in preuve['operations']];assert len(refs)==len(set(refs))
 attendu_lignes=sum(len(OPS[r]['lignes']) for r in refs);attendu_debit=sum(D(l['debit']) for r in refs for l in OPS[r]['lignes'])
 with Session(app['engine']) as db:
  es=db.query(models.Ecriture).filter_by(societe_id=sid).all();assert len(es)==len(refs) and all(e.est_validee for e in es);assert sum(len(e.lignes) for e in es)==attendu_lignes
  debit=sum(D(str(l.debit)) for e in es for l in e.lignes);credit=sum(D(str(l.credit)) for e in es for l in e.lignes);assert debit==credit==attendu_debit
  assert db.query(models.MouvementStock).filter_by(societe_id=sid,article_id=a['id']).count()==5
 assert core(app,sid)[:len(initial)]==initial
 preuve['suite777']={'ecritures':len(refs),'lignes':attendu_lignes,'debit_credit':str(attendu_debit),'stock':60,'cmup':110,'reste_vente2':10000,'avoir':av['id'],'facture2':v2['id'],'prefixe_valide_inchange':True,'imputation_credit_sans_nouvelle_ecriture':True}
