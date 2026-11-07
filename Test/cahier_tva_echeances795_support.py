"""Préparations TVA et échéancesN+1 du cahier, sur dossier fictif clôturé."""
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path
from io import BytesIO
import hashlib,re
from pypdf import PdfReader
from sqlalchemy.orm import Session
from playwright.sync_api import expect
import models
from cahier_formulaires773_support import DATA,ok,champ
from cahier_cycle775_support import identifiants,valider_journal
from cahier_suite777_support import core
from urllib.parse import urlsplit,parse_qs

def choisir_mois(page,mois,verifier):
 with page.expect_response(lambda r:urlsplit(r.url).path=='/api/tva/declaration' and parse_qs(urlsplit(r.url).query).get('mois')==[str(mois)]) as r:page.get_by_text('Mois',exact=True).locator('..').locator('select').select_option(str(mois))
 verifier(ok(r.value));page.get_by_text('Calcul de la déclaration…',exact=True).wait_for(state='hidden')


def tva_mensuelle(api,page,app,sid,preuve,tmp_path):
 avant=core(app,sid);snapshot=ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'];page.goto(app['web_url']+'/declaration-tva');expect(page.get_by_role('heading',name='Déclaration TVA',exact=True)).to_be_visible();preuves=[]
 for attendu in DATA['tva_mois']:
  mois=int(attendu['mois']);recu={};page.get_by_role('button',name='Synthèse',exact=True).click()
  def verifier(data):
   for reel,cible in [(data['collectee']['total'],'collectee'),(data['recuperable']['total'],'recuperable'),(data['credit_tva_anterieur'],'credit_ouverture'),(data['credit_tva'],'credit_fin'),(data['tva_due'],'due')]:assert D(str(reel))==D(attendu[cible]),(mois,cible,reel,attendu[cible])
   assert data['periode']['date_debut']==f'2025-{mois:02d}-01' and data['regime_tva']==DATA['societe']['regime_tva'];recu.update(data)
  choisir_mois(page,mois,verifier);page.get_by_role('button',name='Détail par taux',exact=True).click();expect(page.get_by_text('Détail par taux de TVA',exact=True)).to_be_visible();page.get_by_role('button',name='Préparation DGI',exact=True).click()
  for label,cle in [('Raison sociale','raison_sociale'),('N° IF','identifiant_fiscal'),('N° ICE','ice')]:expect(page.get_by_label(label,exact=True)).to_have_value(DATA['societe'][cle])
  expect(page.get_by_text('Dépôt sur le portail DGI (hors HisabPro)',exact=True)).to_be_visible();assert page.get_by_title('Connexion directe DGI non encore implémentée',exact=True).count()==0;page.get_by_role('button',name='Imprimer',exact=True).click()
  pdf=page.pdf(format='A4',print_background=True);assert pdf.startswith(b'%PDF');texte='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf)).pages);assert 'ATLAS RECETTE HISABPRO' in texte and 'Brouillon de contrôle' in texte;normal=re.sub(r'[\s.\u00a0\u202f]','',texte);montant=format(D(attendu['due']),'.2f').replace('.',',');assert montant in normal,(mois,montant,normal[-600:])
  fichier=tmp_path/f'TVA_2025_{mois:02d}_{preuve["largeur"]}.pdf';fichier.write_bytes(pdf);preuves.append({'mois':mois,'attendu':attendu,'reel':recu,'pdf_temporaire':str(fichier),'pdf_sha256':hashlib.sha256(pdf).hexdigest(),'pdf_pages':len(PdfReader(BytesIO(pdf)).pages),'impression':'PDF rendu par moteur Edge ;aucune imprimante physique ni dépôtDGI.'});preuve['cas'].append({'id':f'HP-FIS-{mois+2:03d}','statut':'Réussi'})
 assert core(app,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==snapshot;preuve['tva795']=preuves


def ecriture_2026(page,app,sid,date_,ref,montant,compte,preuve):
 avant=identifiants(app,sid);page.goto(app['web_url']+'/journal');page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog');champ(m,'Date comptable *').fill(date_);champ(m,'Journal *','select').select_option('BQ');champ(m,'Référence du justificatif').fill(ref);champ(m,"Libellé de l'écriture *").fill(ref+' — règlement fiscal fictif');rows=m.locator('tbody tr')
 for i,c,col in [(0,compte,'Débit (MAD)'),(1,'5141','Crédit (MAD)')]:rows.nth(i).get_by_placeholder('Ex: 6111',exact=True).fill(c);rows.nth(i).locator(f'td[data-label="{col}"] input').fill(montant)
 m.get_by_label('Valider immédiatement',exact=False).uncheck()
 with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as r:m.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
 e=ok(r.value,201);m.wait_for(state='hidden');assert identifiants(app,sid)-avant=={e['id']}
 with Session(app['engine']) as db:
  entree=db.get(models.Ecriture,e['id']);assert str(entree.date)==str(entree.date_piece)==date_ and entree.reference==ref and entree.journal==models.JournalEnum.BQ and not entree.est_validee;assert {l.compte:(D(str(l.debit)),D(str(l.credit))) for l in entree.lignes}=={compte:(D(montant),D(0)),'5141':(D(0),D(montant))}
 valider_journal(page,app,1);preuve.setdefault('paiements2026_795',[]).append({'reference':ref,'date':date_,'debit':compte,'credit':'5141','montant':montant,'id':e['id']})


def soldes_2026(app,sid):
 r=defaultdict(lambda:D(0))
 with Session(app['engine']) as db:
  for e in db.query(models.Ecriture).filter_by(societe_id=sid,exercice=2026):
   assert e.est_validee
   for l in e.lignes:r[l.compte]+=D(str(l.debit))-D(str(l.credit))
 return r


def echeances_2026(api,page,app,sid,preuve):
 origine=[e for e in core(app,sid) if e[1].year==2025];snapshot=ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'];page.goto(app['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026')
 for args in [('2026-01-20','TVA-12-PAY','2400.00','4456'),('2026-03-31','IS-2025-PAY','23220.25','4453')]:ecriture_2026(page,app,sid,*args,preuve)
 soldes=soldes_2026(app,sid);assert soldes['4456']==soldes['4453']==0 and soldes['5141']==D('262109.75');preuve['cas'].append({'id':'HP-FIS-028','statut':'Réussi'})
 for args in [('2026-03-31','AP1-2026','6691.50','3453'),('2026-06-30','AP2-2026','2000.00','3453')]:ecriture_2026(page,app,sid,*args,preuve)
 banque_apres=soldes_2026(app,sid);assert banque_apres['3453']==D('8691.50') and banque_apres['5141']==D('253418.25');avant_metadata=core(app,sid);page.goto(app['web_url']+'/fiscalite-is');situation=ok(api.get('/api/fiscalite/is/2026'));ref=situation['acomptes']['reference'];assert ref['disponible'] and ref['exercice_reference']==2025 and ref['source']=='transition_2023_2026' and D(str(ref['benefice_reference']))==D('133830') and D(str(ref['taux_reference']))==D('20') and D(str(ref['montant_annuel']))==D('26766');expect(page.get_by_label('Référence annuelle forcée (optionnel)',exact=True)).to_have_value('')
 lignes=page.locator('tr').filter(has=page.get_by_placeholder('Réf. paiement',exact=True));expect(lignes).to_have_count(4)
 for idx,montant,date_,reference in [(0,'6691.50','2026-03-31','AP1-2026'),(1,'2000.00','2026-06-30','AP2-2026')]:
  row=lignes.nth(idx);row.get_by_placeholder('Montant',exact=True).fill(montant);row.locator('input[type="date"]').fill(date_);row.get_by_placeholder('Réf. paiement',exact=True).fill(reference)
  with page.expect_response(lambda r:r.url.endswith(f'/api/fiscalite/is/2026/acomptes/{idx+1}') and r.request.method=='PUT') as r:row.get_by_role('button',name='Enregistrer',exact=True).click()
  ok(r.value)
 page.reload();lignes.nth(1).wait_for();situation=ok(api.get('/api/fiscalite/is/2026'));acomptes=situation['acomptes']['acomptes'];assert [D(str(a['montant_du'])) for a in acomptes]==[D('6691.50')]*4;assert [D(str(a['montant_verse'])) for a in acomptes]==list(map(D,['6691.50','2000','0','0']));assert acomptes[0]['statut']=='solde' and D(str(acomptes[1]['reste_a_couvrir']))==D('4691.50')
 for idx,a in enumerate(acomptes):
  if idx==0:continue
  passe=date.today()>date.fromisoformat(a['date_echeance']);attendu=('partiel_en_retard' if passe else 'partiel') if idx==1 else ('en_retard' if passe else 'a_venir');assert a['statut']==attendu,(idx,a,attendu)
 if acomptes[1]['statut']=='partiel_en_retard':expect(lignes.nth(1)).to_contain_text('Partiel — en retard')
 assert core(app,sid)==avant_metadata;preuve['cas'].append({'id':'HP-FIS-029','statut':'Réussi'});css=situation['contribution_solidarite'];assert css['disponible'] and css['exercice_reference']==2025 and css['source']=='liquidation_n_1' and D(str(css['base']))==D('133830') and D(str(css['montant_du']))==0;assert page.get_by_placeholder('Référence paiement / déclaration',exact=True).count()==0;preuve['cas'].append({'id':'HP-FIS-030','statut':'Réussi'})
 assert all(e in core(app,sid) for e in origine) and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==snapshot
 preuve['echeances795']={'date_controle':date.today().isoformat(),'banque_apres_soldes2025':'262109.75','banque_apres_acomptes2026':'253418.25','reference_acomptes':ref,'acomptes':acomptes,'css':css,'metadonnees_fiscales_sans_double_ecriture':True,'cloture_et_snapshot2025_inchanges':True,'limite':'Montants du jeu fictif,statuts adaptés àdatecourante ;CSSmoteur0neprouvepasabsenceobligationdéclarative. Pasdedépôt niPGutilisateur.'}
