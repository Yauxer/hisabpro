"""Complément de recette FAC013 ; aucun résultat humain prérempli comme réussi."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/recette'
DATA=json.loads((D/'jeu_donnees_recette.json').read_text(encoding='utf8'))
JEU={'installation':'Copie isolée et restaurable, code923, migration125 appliquée après les prérequis de l’installation existante. Société de recette vierge ; jamais la base habituelle.',
 'societe':DATA['societe'],'article':next(a for a in DATA['articles'] if a['code']=='S-VTE'),'client':next(t for t in DATA['tiers'] if t['code']=='C-SERVICE'),'banque':DATA['banque'],
 'exercice':'2025-01-01 au2025-12-31, ouvert ; ne pas utiliser l’exercice2026 par défaut.',
 'facture':'Vente,20/01/2025,client C-SERVICE,référence CONSERVATION-FICTIVE923,article S-VTE du jeu,description Prestation fictive923,quantité1,prixHT1000.00,TVA20%,aucune remise/transport/emballage/RAS.',
 'comptabilite':'Créer l’article S-VTE avec son compte de vente fourni dans ce jeu, puis le sélectionner dans la facture. Vente : D3421=1200,Ccompte_vente_article=1000,C4455=200. Validation définitive dans le Journal séparée de la validation de facture.',
 'reglement':'Virement1200.00 au21/01/2025,banque du jeu,compte5141,référence SOLDE-COPIE-FICTIF923. Écriture D5141=1200,C3421=1200 ; aucun deuxième règlement.',
 'motif':'Conservation FICTIVE923 <copie> & partenaire',
 'logo':'Utiliser un logo de recette PNG/JPEG dans Paramètres avant validation de facture. La modification ultérieure du logo courant ne réécrit pas cette copie.',
 'attendu':'FactureHT1000,TVA200,TTC1200,solde0. Après conservation :PDF figé,IDauteur,date,motif,taille,empreinte64caractères ; mêmes octets après rechargement et changement de paramètres.',
 'attention':'Copie interne seulement ; pas de signature ou certification légale, aucun statut commercial supplémentaire et aucune écriture nouvelle. L’empreinte est relevée après capture ; ne pas en inventer une.'}
CAS=[
 ('FAC923-01','Conserver la facture validée et soldée','Code/migration125 sur copie, société/client/banque/exercice du jeu, logo de recette installé.',
  'Toutes les valeurs du jeu,notamment facture1000HT+200TVA,paiement1200,motif exact.',
  'Créer et valider la facture,comptabiliser puis valider ses écritures. Enregistrer le virement unique1200 et valider son écriture. Ouvrir le détail de facture,déplier Conserver une copie figée,saisir motif et confirmation,puis Conserver ce PDF.',
  'Solde0 avant et après,PDF figé conservé une fois,date/auteur/motif/taille/SHA visibles sans F5 ; aucun nouveau statut ou mouvement comptable.'),
 ('FAC923-02','Télécharger et retrouver exactement le PDF','FAC923-01 ; relever son empreinte réelle.',
  'Même facture et bouton Télécharger la copie conservée ; conserver deux fichiers locaux sous des noms distincts.',
  'Télécharger,ouvrir le PDF et vérifier identité/logo/lignes/TTC. Recharger la page,rouvrir la facture et retélécharger. Faire comparer les octets ou SHA256 des deux fichiers par le responsable technique.',
  'Même empreinte et mêmes octets ; document ouvrable,logo présent. Un nouvel appel de conservation restitue la copie existante sans remplacer son motif.'),
 ('FAC923-03','Préserver la copie malgré les opérations ultérieures','FAC923-02 ; copie fictive uniquement.',
  'Nouvelle raison sociale SOCIETE COURANTE FICTIVE923 et autre logo de recette ; ne pas modifier une pièce validée.',
  'Changer seulement les paramètres courants,puis télécharger à nouveau la copie. Vérifier que Créer un avoir reste disponible selon droits,et comparer les journaux avant/après conservation.',
  'PDF conservé inchangé ; facture et écritures non modifiées par la conservation. Les opérations commerciales restent indépendantes ; ne pas émettre un avoir inutile pour ce test.'),
 ('FAC923-04','Contrôler consultation et cloisonnement','Deux comptes de recette,deux sociétés distinctes ; invitation du second compte en lecture dans la première.',
  'Facture et copie de FAC923-01 ; rôle Consultation seule,ensuite accès révoqué.',
  'Depuis l’autre société vérifier l’absence de facture. Dans la société partagée,consulter et télécharger la copie ; vérifier absence de formulaire de création. Révoquer l’accès depuis l’administrateur puis recharger.',
  'Lecture/téléchargement autorisés au lecteur actif ; création refusée403 par API. Autre société sans accès404,accès révoqué403 ; aucune exposition de PDF.'),
 ('FAC923-05','Vérifier les exclusions et les erreurs','Nouvelles pièces fictives indépendantes,aucune suppression de facture validée.',
  'Brouillon vente1000HT,proforma1000HT,facture achat1000HT. Essayer aussi une conservation avec motif vide ou confirmation absente.',
  'Consulter les pièces :aucun parcours de conservation de vente définitive pour ces exclusions. Responsable technique :vérifier refus409/422 sans copie créée. Sur une installation de recette sans125 vérifier que le PDF habituel reste disponible.',
  'Aucune copie trompeuse ; PDF habituel conservé selon ses droits et conditions antérieurs. Absence125 signalée,création refusée503,sans panne du détail de facture.'),
 ('FAC923-06','Restaurer et contrôler sur petit écran','Responsable technique,source de recette et seconde cible isolée neuve ; ne jamais écraser la base habituelle.',
  'Sauvegarde PostgreSQL de la copie avec sa table factures_copies_conservees ; identifiant de facture et empreinte de FAC923-01.',
  'Sauvegarder puis restaurer dans une cible distincte. Relire et télécharger sous rôle limité ; comparer PDF,métadonnées,droits et écritures. Rejouer l’écran à390px et1440px,contrôler texte,boutons et défilement.',
  'Octets/empreintes/métadonnées conservés ; source intacte. Aucune suppression/remplacement permis par le runtime. Recette visuelle humaine et configuration réelle à consigner séparément.'),
 ('JRN923-01','Lire le résultat de validation dans le Journal','Exercice2025 ouvert de cette copie de recette,compte administrateur/comptable.',
  'Écriture brouillon au15/01/2025,journal BQ,référence VALIDATION-FICTIVE923-1,libellé Validation fictive923 numéro1,deux lignes :5141 débit10.00 et1111 crédit10.00.',
  'Créer ce brouillon. Dans le Journal choisir Valider les brouillons et confirmer. Attendre le résultat dans la page,le lire puis utiliser Fermer le résultat de validation.',
  'Une écriture définitive équilibrée10MAD ;confirmation préalable conservée,résultat1écriture validée dans la page,sans alerte JavaScript supplémentaire. Bouton indisponible pendant le traitement.'),
 ('JRN923-02','Naviguer juste après la validation','JRN923-01 terminé ;aucun autre brouillon dans la sélection.',
  'Second brouillon au16/01/2025,journal BQ,référence VALIDATION-FICTIVE923-2,libellé Validation fictive923 numéro2,5141 débit20.00 et1111 crédit20.00.',
  'Créer ce brouillon. Valider les brouillons,confirmer,puis ouvrir immédiatement Factures. Revenir au Journal. Refaire le parcours à390px et1440px.',
  'Factures s’ouvre sans fenêtre tardive de succès. Deux écritures définitives uniques,montants10et20inchangés,aucun ancien message affiché sur le nouvel écran ou après une bascule de contexte.')]

def generer():
 (D/'JEU_CONSERVATION_FACTURES_923.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
 styles=getSampleStyleSheet()
 if Path('C:/Windows/Fonts/arial.ttf').exists():
  pdfmetrics.registerFont(TTFont('Arial923','C:/Windows/Fonts/arial.ttf'))
  for st in styles.byName.values():st.fontName='Arial923'
 styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;p=lambda t,st='BodyText':Paragraph(escape(str(t)),styles[st])
 story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Conservation des factures et validation du Journal923','Heading1'),p('Complément FAC013 et navigation après validation :huit cas humains Non testé. Les preuves automatisées sont distinctes ;aucune conformité ou production validée automatiquement.')]
 for k,v in JEU.items():
  story.append(p(k,'Heading2'))
  if isinstance(v,dict):
   for cle,val in v.items():story.append(p(cle+' : '+str(val)))
  else:story.append(p(v))
 story.append(PageBreak());w=Workbook();sy=w.active;sy.title='Synthese';s=w.create_sheet('Factures');journal=w.create_sheet('Journal');entetes=['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuves/captures'];s.append(entetes);journal.append(entetes)
 for ident,obj,pre,data,actions,att in CAS:
  ec='Aucune écriture créée par la conservation. Les écritures de vente/règlement du jeu existent déjà.' if ident.startswith('FAC') else 'Écritures du cas uniquement :D5141/C1111 pour10ou20MAD ;validation sans changer leurs montants.';fi='Aucune incidence fiscale directe ;pas de dépôt ni de certification légale.';co='ID facture/société,auteur,motif,date,octets,SHA,logo,droits et journal avant/après.' if ident.startswith('FAC') else 'Confirmation avant mutation,résultat visible,montants/IDs conservés,navigation sans alerte tardive.'
  bloc=[p(ident+' — '+obj,'Heading2')]
  for cle,val in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Statut','Non testé'),('Preuves','Capture du détail avant/après et deux PDF/empreintes ;preuve de refus ou rapport de restauration selon le cas.')]:bloc.append(p(cle+' : '+val))
  story.append(KeepTogether(bloc+[Spacer(1,12)]));cible=s if ident.startswith('FAC') else journal;cible.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures,IDs,PDF et empreintes à conserver'])
 pdf=D/'RECETTE_CONSERVATION_FACTURES_923.pdf';SimpleDocTemplate(str(pdf),title='HisabPro — conservation des factures923').build(story)
 for row in [['HISABPRO — CONSERVATION FACTURES923'],['Production','Non validée'],['Statut','Nombre']]:sy.append(row)
 for statut in ['Non testé','Réussi','Échoué','Bloqué']:sy.append([statut,f'=COUNTIF(Factures!J2:J7,"{statut}")+COUNTIF(Journal!J2:J3,"{statut}")'])
 sy.append(['Cas',len(CAS)]);sy.append(['Progression','=IFERROR(B5/B8,0)']);sy['B9'].number_format='0%'
 d=w.create_sheet('Donnees');d.append(['Champ','Valeur exacte fictive'])
 for k,v in JEU.items():
  if isinstance(v,dict):
   for cle,val in v.items():d.append([k+' / '+cle,str(val)])
  else:d.append([k,v])
 for feuille in w:
  feuille.freeze_panes='B2';feuille.auto_filter.ref=feuille.dimensions
  for col in feuille.columns:feuille.column_dimensions[col[0].column_letter].width=42
  for row in feuille:
   feuille.row_dimensions[row[0].row].height=210 if feuille in [s,journal] and row[0].row>1 else 60
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
  for c in feuille[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24589C')
 d.column_dimensions['B'].width=95
 for feuille in [s,journal]:
  dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');feuille.add_data_validation(dv);dv.add(f'J2:J{feuille.max_row}')
 x=D/'SUIVI_CONSERVATION_FACTURES_923.xlsx';w.save(x)
 texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
 wb=load_workbook(x);assert all(feuille.cell(i,10).value=='Non testé' for feuille in [wb['Factures'],wb['Journal']] for i in range(2,feuille.max_row+1));wb.close()
 print(json.dumps({'cas_humains':len(CAS),'statut':'Tous Non testé','pages':len(PdfReader(pdf).pages),'feuilles':w.sheetnames},ensure_ascii=False))

if __name__=='__main__':generer()
