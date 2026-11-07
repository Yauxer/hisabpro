"""Du cahier annuel à la clôture et au snapshot fiscal, en PostgreSQL temporaire."""
import pytest
from cahier_formulaires773_support import laboratoire,referentiels,DATA,ok
from test_e2e_cahier_immobilisation785_isole import capital,acquisition
from cahier_semestre789_support import semestre
from cahier_annuel791_support import annuel
from cahier_cloture793_support import cloturer_cahier
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

from pathlib import Path
from decimal import Decimal as D
import hashlib,csv,io
from sqlalchemy import text
from openpyxl import load_workbook
from playwright.sync_api import expect
from test_e2e_balances_exports_isole import telecharger,pdf_texte,cellules
from cahier_suite777_support import core


def verifier_exports(api,page,app,sid,preuve,tmp_path,tiers):
 avant=core(app,sid);fige=ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'];exports=[]
 page.goto(app['web_url']+'/journal');ligne=page.locator('tr').filter(has=page.get_by_text('CAP-01',exact=True)).filter(has=page.get_by_role('button',name='Justificatifs',exact=True));expect(ligne).to_have_count(1);ligne.get_by_role('button',name='Justificatifs',exact=True).click()
 modal=page.locator('div[class*="auditModal"]').filter(has=page.get_by_text('Pièces jointes',exact=False));expect(modal).to_have_count(1);expect(modal.get_by_role('button',name='Joindre un fichier',exact=True)).to_be_enabled()
 source=Path('docs/recette/justificatifs/CAP-01.pdf').resolve()
 with page.expect_response(lambda r:'/api/attachments/ecriture/' in r.url and r.request.method=='POST') as r:modal.locator('input[type=file]').set_input_files(str(source))
 fiche=ok(r.value);nom=fiche['nom'];expect(modal.get_by_text(nom,exact=True)).to_be_visible();expect(modal.get_by_role('button',name='Supprimer',exact=True)).to_have_count(0)

 with app['engine'].connect() as db:
  traces=db.execute(text('SELECT reference,date_piece,source_type,created_by FROM ecriture_justificatifs WHERE societe_id=:sid AND fichier_nom=:nom'),{'sid':sid,'nom':nom}).all()
  assert len(traces)==1 and traces[0][0]=='CAP-01' and str(traces[0][1])=='2025-01-01' and traces[0][2]=='fichier' and traces[0][3]
 preuve['justificatif797']={'nom_serveur':nom,'reference':'CAP-01','date_piece':'2025-01-01','trace_documentaire_verifiee':True,'suppression_non_proposee':True}
 with page.expect_download() as sortie:modal.get_by_role('button',name='Télécharger',exact=True).click()
 fichier=tmp_path/'CAP-01_telecharge.pdf';sortie.value.save_as(fichier);assert fichier.read_bytes()==source.read_bytes();exports.append({'nom':'Justificatif CAP-01','chemin':str(fichier),'sha256':hashlib.sha256(fichier.read_bytes()).hexdigest()})
 modal.get_by_role('button',name='Fermer',exact=True).click();page.reload();ligne=page.locator('tr').filter(has=page.get_by_text('CAP-01',exact=True)).filter(has=page.get_by_role('button',name='Justificatifs',exact=True));ligne.get_by_role('button',name='Justificatifs',exact=True).click();expect(page.get_by_text(nom,exact=True)).to_be_visible();page.get_by_role('button',name='Fermer',exact=True).click();preuve['cas'].append({'id':'HP-CPT-005','statut':'Réussi'})

 exercice=[e for e in avant if str(e[1]).startswith('2025')];nb_lignes=sum(len(e[-1]) for e in exercice);total_attendu=sum(D(str(l[2])) for e in exercice for l in e[-1])
 for route,nom_export,ref_col in [('/journal','journal','Référence pièce'),('/grand-livre','grand_livre','Référence')]:
  page.goto(app['web_url']+route);bouton=page.get_by_role('button',name='Exporter CSV',exact=True);expect(bouton).to_be_enabled()
  with page.expect_download() as sortie:bouton.click()
  fichier=tmp_path/(nom_export+'.csv');sortie.value.save_as(fichier);rows=list(csv.DictReader(io.StringIO(fichier.read_text(encoding='utf-8-sig')),delimiter=';'));assert len(rows)==nb_lignes,(nom_export,len(rows),nb_lignes)
  assert {'02','002'} <= {r[ref_col] for r in rows};debit=sum(D(r['Débit'].replace(',','.')) for r in rows);credit=sum(D(r['Crédit'].replace(',','.')) for r in rows);assert debit==credit==total_attendu
  banque=sum(D(r['Débit'].replace(',','.'))-D(r['Crédit'].replace(',','.')) for r in rows if r['Compte']=='5141');assert banque==D('287730')
  exports.append({'nom':nom_export,'chemin':str(fichier),'sha256':hashlib.sha256(fichier.read_bytes()).hexdigest(),'lignes':len(rows),'debit':str(debit),'credit':str(credit)})
  if route=='/journal':
   page.evaluate('() => { window.__recetteImpressions797=0;window.print=()=>{window.__recetteImpressions797+=1}; }');assert page.evaluate('window.__recetteImpressions797')==0
   page.get_by_role('button',name='Imprimer',exact=True).click();assert page.evaluate('window.__recetteImpressions797')==1
   fichier=tmp_path/'journal_imprime.pdf';page.pdf(path=str(fichier),format='A4',print_background=True);texte=pdf_texte(fichier);assert 'CAP-01' in texte and '2025' in texte
   exports.append({'nom':'journal_imprime','chemin':str(fichier),'sha256':hashlib.sha256(fichier.read_bytes()).hexdigest()})
 page.goto(app['web_url']+'/balances');expect(page.get_by_text('Balance équilibrée',exact=False)).to_be_visible()
 for genre,identifiant,montant in [('generale','5141',D('287730')),('clients',tiers['C-IMPAYE']['nom'],D('14400')),('fournisseurs',tiers['F-CONTROLE']['nom'],D('-480'))]:
  if genre=='clients':page.get_by_role('button',name='Balance Auxiliaire',exact=False).click()
  if genre=='fournisseurs':page.get_by_role('button',name='Fournisseurs (4411)',exact=True).click()
  expect(page.get_by_text(identifiant,exact=True).first).to_be_visible()
  excel=telecharger(page,'Excel',tmp_path,genre);rows=cellules(load_workbook(excel,data_only=True));row=next(r for r in rows[7:] if r[0]==identifiant);assert D(str(row[-2] or 0))-D(str(row[-1] or 0))==montant,(genre,row)
  pdf=telecharger(page,'PDF',tmp_path,genre);texte=pdf_texte(pdf);assert identifiant in texte and '2025' in texte;assert f'{abs(montant):,.2f}'.replace(',',' ').replace('.',',') in texte,(genre,texte)
  for path in [excel,pdf]:exports.append({'nom':genre,'chemin':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 assert core(app,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==fige
 preuve['cas'].append({'id':'HP-CPT-006','statut':'Réussi'});preuve['exports797']={'fichiers':exports,'nombre':10,'ecritures_et_snapshot_inchanges':True,'soldes_controles':{'5141':'287730','3421':'14400','4411':'-480'},'archive_fiscale':'Non réalisée dans ce lot ; notes ETIC à compléter sans inventer.'}


@pytest.mark.parametrize('largeur',[1440,390])
def test_797_exports_et_justificatif_cahier_cloture(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'exports797rr') as (api,page,sid,preuve):
  tiers,articles=referentiels(api,page,application,sid,preuve);b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,tiers['F-IMMO'],preuve);semestre(api,page,application,sid,tiers,articles,banque,preuve,tmp_path);annuel(api,page,application,sid,tiers,articles,banque,immo,preuve);cloturer_cahier(api,page,application,sid,preuve)

  verifier_exports(api,page,application,sid,preuve,tmp_path,tiers)
