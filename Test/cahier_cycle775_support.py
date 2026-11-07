"""Premier sous-parcours du cahier : opérations réellement produites par les formulaires."""
from pathlib import Path
from decimal import Decimal
from collections import defaultdict
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import text
from playwright.sync_api import expect
from pypdf import PdfReader
import models
from cahier_formulaires773_support import DATA,ROOT,ok,champ,ouvrir_avance
OPS={o['reference_recette']:o for o in DATA['operations']}
D=Decimal

def identifiants(app,sid):
 with Session(app['engine']) as db:return {e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)}

def nouvelle_ecriture(app,sid,avant,reference,preuve):
 o=OPS[reference]
 with Session(app['engine']) as db:
  nouvelles=[e for e in db.query(models.Ecriture).filter_by(societe_id=sid) if e.id not in avant];assert len(nouvelles)==1,(reference,len(nouvelles));e=nouvelles[0]
  attendu=defaultdict(lambda:[D(0),D(0)]);reel=defaultdict(lambda:[D(0),D(0)])
  for l in o['lignes']:attendu[l['compte']][0]+=D(l['debit']);attendu[l['compte']][1]+=D(l['credit'])
  for l in e.lignes:
   reel[l.compte][0]+=D(str(l.debit));reel[l.compte][1]+=D(str(l.credit))
   if l.compte in ['3421','4411','3411']:assert l.tiers_id and l.compte_auxiliaire_snapshot
  assert dict(reel)==dict(attendu),(reference,dict(reel),dict(attendu));assert str(e.date)==o['date'] and e.journal==o['journal']
  preuve.setdefault('operations',[]).append({'reference':reference,'id':e.id,'date':str(e.date),'journal':e.journal,'lignes':{k:[str(v[0]),str(v[1])] for k,v in reel.items()}})

def stock(app,aid,qte,cmup):
 with Session(app['engine']) as db:
  a=db.get(models.Article,aid);assert D(str(a.stock_actuel))==D(str(qte)) and D(str(a.cmup))==D(str(cmup)),(a.stock_actuel,a.cmup)

def valider_journal(page,app,nb):
 page.goto(app['web_url']+'/journal');expect(page.get_by_role('button',name='Valider',exact=True)).to_have_count(nb)
 with page.expect_response(lambda r:r.url.endswith('/api/ecritures/valider-lot') and r.request.method=='POST') as r:page.get_by_role('button',name='Valider les brouillons',exact=True).click()
 assert ok(r.value)['nb_validees']==nb

def facture_achat(api,page,app,tiers,article,reference,pu,date,echeance):
 page.goto(app['web_url']+'/factures');page.get_by_role('button',name='Nouvelle facture',exact=True).click();m=page.get_by_role('dialog',name='Nouvelle facture',exact=True);m.get_by_role('button',name='Achat',exact=True).click();champ(m,'Date *').fill(date);m.get_by_placeholder('Rechercher un',exact=False).fill(tiers['nom']);m.get_by_text(tiers['nom'],exact=True).click();m.get_by_placeholder('N° porté sur la facture du fournisseur').fill(reference);m.get_by_label('Échéance de la nouvelle facture',exact=True).fill(echeance)
 m.get_by_placeholder('Description ou article...').fill(article['designation']);m.locator('li').filter(has_text=article['designation']).click();ed=m.locator('.hp-invoice-line-editor');ed.locator('input[type="number"]').nth(0).fill('100');ed.locator('input[type="number"]').nth(1).fill(str(pu));m.get_by_role('button',name='Enregistrer en brouillon',exact=False).click()
 with page.expect_response(lambda r:r.url.endswith('/api/factures') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer le brouillon',exact=True).click()
 f=ok(r.value,201);m.wait_for(state='hidden');assert f['total_ttc']==100*pu*1.2;return f

def officialiser(page,app,f,tiers):
 row=page.locator('tbody tr').filter(has_text=tiers['nom']).filter(has=page.locator('button[title="Valider définitivement"]'))
 # Si plusieurs brouillons, l'identifiant visible évite toute sélection arbitraire.
 expect(row).to_have_count(1)
 with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{f["id"]}/valider')) as r:row.get_by_title('Valider définitivement',exact=True).click()
 f={**f,**ok(r.value)}
 row=page.locator('tbody tr').filter(has_text=f['numero'])
 with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{f["id"]}/comptabiliser')) as r:row.get_by_title("Générer l'écriture comptable de cette facture",exact=True).click()
 ok(r.value);return f,row

def payer(page,app,f,tiers,montant,date,ref,banque):
 page.goto(app['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=f['numero']);row.get_by_title('Payer le fournisseur' if f['type']=='achat' else 'Encaisser le client',exact=True).click();m=page.get_by_role('dialog');champ(m,'Montant *').fill(str(montant));champ(m,'Date *').fill(date);m.get_by_placeholder('N° chèque, virement...').fill(ref)
 champ(m,'Banque','select').select_option(banque['banque'])
 with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer',exact=True).click()
 ok(r.value,201);m.wait_for(state='hidden')

def cycle(api,page,app,sid,tiers,articles,preuve,tmp_path,banque=None):
 from cahier_suite777_support import core
 initial=core(app,sid);prefixe=len(initial);prefixe_lignes=sum(len(e[8]) for e in initial);prefixe_debit=sum(D(str(l[2])) for e in initial for l in e[8])
 page.on('requestfailed',lambda req:preuve.setdefault('requetes_echouees',[]).append({'url':req.url.split('?')[0],'erreur':req.failure}))
 f=tiers['F-MARCH'];c=tiers['C-MARCH'];a=articles['M-01'];b=DATA['banque'];banque=banque or ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
 preuve['limite_cycle']='Sous-parcours :capital etimmobilisation du début du cahier non rejoués ;solde banque contrôlé comme variation des seules opérations exécutées,non comme solde annuel. Banque préparée parAPI,formulaire validé771.'
 avant=identifiants(app,sid);page.goto(app['web_url']+'/acomptes');page.get_by_role('button',name='Nouvel acompte',exact=True).click();m=page.get_by_role('dialog',name='Nouvel acompte',exact=True);m.get_by_role('button',name='Acompte fournisseur versé',exact=False).click();champ(m,'Date').fill('2025-01-04');m.locator('input[role="combobox"]').fill(f['nom']);m.get_by_role('option').filter(has_text=f['nom']).click();champ(m,'Montant (MAD)').fill('6000');champ(m,'Compte bancaire','select').select_option(str(banque['id']));m.get_by_placeholder('N° chèque, virement...').fill('AC-F01')
 with page.expect_response(lambda r:r.url.endswith('/api/acomptes') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer l’acompte',exact=True).click()
 avance=ok(r.value,201);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'AC-F01',preuve);preuve['cas'].append({'id':'HP-PAY-001','statut':'Réussi'})
 avant=identifiants(app,sid);ach1=facture_achat(api,page,app,f,a,'ACH-01',100,'2025-01-05','2025-01-07');ach1,row=officialiser(page,app,ach1,f);nouvelle_ecriture(app,sid,avant,'ACH-01',preuve);stock(app,a['id'],100,100);preuve['cas'].append({'id':'HP-FAC-002','statut':'Réussi'})
 avant=identifiants(app,sid);page.goto(app['web_url']+'/acomptes');page.locator('tbody tr').filter(has_text=f['nom']).get_by_title('Imputer sur une facture',exact=True).click();m=page.get_by_role('dialog');m.locator('select').select_option(str(ach1['id']));champ(m,'Montant à imputer (MAD)').fill('6000');champ(m,'Date d’imputation').fill('2025-01-05')
 with page.expect_response(lambda r:r.url.endswith(f'/api/acomptes/{avance["id"]}/imputer')) as r:m.get_by_role('button',name='Imputer l’acompte',exact=True).click()
 assert ok(r.value)['montant_disponible']==0;m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'AC-F01-IMP',preuve);preuve['cas'].append({'id':'HP-PAY-002','statut':'Réussi'})
 avant=identifiants(app,sid);payer(page,app,ach1,f,6000,'2025-01-07','PAY-ACH01',banque);nouvelle_ecriture(app,sid,avant,'ACH-01-PAY',preuve);situation=ok(api.get(f'/api/factures/{ach1["id"]}/reglements'));assert situation['total_acomptes']==6000 and situation['solde_restant']==0;valider_journal(page,app,4);preuve['cas'].append({'id':'HP-PAY-003','statut':'Réussi'})
 page.goto(app['web_url']+'/lettrage');champ(page,'Compte','select').select_option('4411');champ(page,'Tiers','select').select_option(label=f['nom']);boxes=page.locator('tbody input[type=checkbox]');expect(boxes).to_have_count(3)
 for box in boxes.all():box.check()
 with page.expect_response(lambda r:'/api/lettrage' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Lettrer 3 lignes',exact=True).click()
 lettre=ok(r.value);assert len(lettre['code'])>=3;page.get_by_text('3 lettrée(s)',exact=True).wait_for();preuve['lettrage_fournisseur']=lettre['code'];page.reload(wait_until='domcontentloaded');champ(page,'Compte','select').select_option('4411');champ(page,'Tiers','select').select_option(label=f['nom']);page.get_by_text('3 lettrée(s)',exact=True).wait_for()
 avant=identifiants(app,sid);ach2=facture_achat(api,page,app,f,a,'ACH-02',120,'2025-01-10','2025-03-20');ach2,row=officialiser(page,app,ach2,f);nouvelle_ecriture(app,sid,avant,'ACH-02',preuve);stock(app,a['id'],200,110);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-FAC-003','statut':'Réussi'})
 page.goto(app['web_url']+'/commercial');page.get_by_role('button',name='Nouveau devis',exact=True).click();m=page.get_by_role('dialog',name='Nouveau devis',exact=True);champ(m,'Date').fill('2025-01-15');champ(m,'Validité (jours)').fill('30');m.get_by_placeholder('Nom du client...',exact=True).fill(c['nom']);m.get_by_role('option').filter(has_text=c['nom']).click();m.get_by_placeholder('Article ou description...',exact=True).fill(a['designation']);m.locator('li').filter(has_text=a['designation']).click();m.get_by_label('Quantité',exact=True).fill('100');ouvrir_avance(m,'Notes internes / commerciales');champ(m,'Notes','textarea').fill('REC-DV01')
 with page.expect_response(lambda r:r.url.endswith('/api/devis') and r.request.method=='POST') as r:m.get_by_role('button',name='Créer le devis',exact=True).click()
 devis=ok(r.value,201);did=devis['id'];assert devis['total_ttc']==30000;m.wait_for(state='hidden');row=page.locator('tbody tr').filter(has_text=c['nom'])
 with page.expect_download() as dl:row.get_by_title('Télécharger PDF',exact=True).click()
 pdf=Path(dl.value.path()).read_bytes();assert pdf.startswith(b'%PDF') and 'REC-DV01' in '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf)).pages)
 with page.expect_response(lambda r:r.url.endswith(f'/api/devis/{did}') and r.request.method=='PATCH') as r:row.get_by_title('Marquer accepté',exact=True).click()
 ok(r.value);row.get_by_role('button',name='Créer BC',exact=True).click();m=page.get_by_role('dialog',name='Nouveau bon de commande',exact=True);champ(m,'Date').fill('2025-01-18')
 # Le cahier demande une note de commande : vérifier le vrai champ, sans écrire directement en API.
 ouvrir_avance(m,'Notes de commande');champ(m,'Notes','textarea').fill('REC-BC01')
 with page.expect_response(lambda r:r.url.endswith('/api/bons-commande') and r.request.method=='POST') as r:m.get_by_role('button',name='Créer la commande',exact=True).click()
 bc=ok(r.value,201);assert bc['devis_id']==did and bc['notes']=='REC-BC01' and bc['date']=='2025-01-18';m.wait_for(state='hidden');preuve['cas'].append({'id':'HP-FAC-001','statut':'Réussi'})
 page.get_by_role('button',name='Bons de commande',exact=True).click();row=page.locator('tbody tr').filter(has_text=c['nom']);row.get_by_title('Créer un bon de livraison sur le reliquat',exact=True).click();m=page.get_by_role('dialog');champ(m,'Date de livraison').fill('2025-01-20')
 with page.expect_response(lambda r:r.url.endswith(f'/api/bons-commande/{bc["id"]}/convertir-bl')) as r:m.get_by_role('button',name='Créer le bon de livraison',exact=True).click()
 bl=ok(r.value);assert bl['date']=='2025-01-20';m.wait_for(state='hidden');page.get_by_role('button',name='Bons de livraison',exact=True).click();row=page.locator('tbody tr').filter(has_text=c['nom'])
 for title in ["Confirmer l'expédition ou la prestation réalisée",'Confirmer la remise au client']:
  with page.expect_response(lambda r:r.url.endswith(f'/api/bons-livraison/{bl["id"]}') and r.request.method=='PATCH') as r:row.get_by_title(title,exact=True).click()
  ok(r.value)
 stock(app,a['id'],200,110);row.get_by_role('button',name='Facturer',exact=True).click();m=page.get_by_role('dialog');m.get_by_label('Date de la facture',exact=True).fill('');expect(m.get_by_role('button',name='Créer la facture',exact=True)).to_be_disabled();m.get_by_label('Date de la facture',exact=True).fill('2025-01-20')
 with page.expect_response(lambda r:r.url.endswith(f'/api/bons-livraison/{bl["id"]}/convertir-facture')) as r:m.get_by_role('button',name='Créer la facture',exact=True).click()
 vente=ok(r.value);assert vente['date']=='2025-01-20' and vente['exercice']==2025 and vente['total_ttc']==30000;m.wait_for(state='hidden');page.goto(app['web_url']+'/factures');row=page.locator('tbody tr').filter(has_text=c['nom']);row.get_by_title('Modifier le brouillon',exact=True).click();m=page.get_by_role('dialog');champ(m,'Échéance').fill('2025-01-26')
 with page.expect_response(lambda r:r.url.endswith(f'/api/factures/{vente["id"]}') and r.request.method=='PATCH') as r:m.get_by_role('button',name='Enregistrer les modifications',exact=True).click()
 ok(r.value);m.wait_for(state='hidden');vente=next(f for f in ok(api.get('/api/factures',params={'exercice':2025})) if f['id']==vente['id']);assert vente['date_echeance']=='2025-01-26';avant=identifiants(app,sid);vente,row=officialiser(page,app,vente,c);nouvelle_ecriture(app,sid,avant,'VENTE-01',preuve);stock(app,a['id'],100,110);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-FAC-004','statut':'Réussi'})
 avant=identifiants(app,sid);payer(page,app,vente,c,10000,'2025-01-25','PAY-V01',banque);nouvelle_ecriture(app,sid,avant,'VENTE-01-PAY',preuve);valider_journal(page,app,1);assert ok(api.get(f'/api/factures/{vente["id"]}/reglements'))['solde_restant']==20000;preuve['cas'].append({'id':'HP-PAY-004','statut':'Réussi'})
 with Session(app['engine']) as db:
  es=db.query(models.Ecriture).filter_by(societe_id=sid).all();assert len(es)==7+prefixe and all(e.est_validee for e in es);assert sum(len(e.lignes) for e in es)==17+prefixe_lignes;assert db.get(models.Facture,vente['id']).statut.value=='partiellement_payee';assert sum(D(str(l.debit)) for e in es for l in e.lignes)==sum(D(str(l.credit)) for e in es for l in e.lignes)==D('84400')+prefixe_debit;assert db.query(models.MouvementStock).filter_by(societe_id=sid,article_id=a['id']).count()==3
 assert core(app,sid)[:prefixe]==initial
 if prefixe:preuve['limite_cycle']='Capital etacquisition présents danscette société ;autres opérations annuelles encoreàintercaler chronologiquement.'
 preuve['cycle']={'factures':[ach1['id'],ach2['id'],vente['id']],'devis':did,'bc':bc['id'],'bl':bl['id'],'ecritures':7+prefixe,'lignes':17+prefixe_lignes,'total_debit_credit':str(D('84400')+prefixe_debit),'stock':100,'cmup':110,'reste_vente':20000}
