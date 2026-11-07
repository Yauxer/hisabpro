"""Recette humaine de l'aperçu de sortie ; aucun statut humain automatisé."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from pypdf import PdfReader

R = Path(__file__).resolve().parents[1]
D = R/'docs/recette'
JEU = {
 'Environnement': 'Copie isolée restaurable, backend et frontend927 installés ensemble. Aucun essai sur le dossier réel. Administrateur ou comptable de la société fictive ; exercices2025 et2026 ouverts avec leurs périodes. Si le paramétrage préalable manque, classer Bloqué et le faire préparer par le responsable.',
 'Fournisseur': 'Créer Fournisseur FICTIF927, type Fournisseur. Autres champs facultatifs laissés vides ;aucun identifiant fiscal réel inventé.',
 'Immobilisation': 'Créer Immobilisation FICTIVE927, catégorie Matériel informatique, acquisition et mise en service01/01/2025, prix HT24000MAD, TVA taxable20% selon hypothèse de recette, récupération100%, durée5ans, méthode linéaire, valeur résiduelle0, amortissable oui, fournisseur ci-dessus, comptes2355/28355/61935, TVA34551 et dette fournisseur4411 (à choisir explicitement dans les paramètres comptables avancés ;le formulaire propose4481 par défaut). Ne pas enregistrer de paiement. Valider son acquisition dans le Journal, puis générer et valider sa dotation2025 de4800MAD. Ne pas générer celle de2026 avant le premier aperçu. Relever les références réellement générées ;ne pas deviner les IDs.',
 'Acquisition attendue': 'Débit2355 :24000 ;débit34551 :4800 ;crédit4411 :28800MAD. Dotation2025 :débit61935 et crédit28355 :4800. Vérifier les comptes de TVA effectivement paramétrés ;un écart doit être documenté.',
 'Sortie': 'Depuis Immobilisations, ouvrir Cession sur ce bien ;nature Cession,date01/01/2026,prix HT20000MAD,traitement TVA Taxable,taux20%,Encaissement immédiat décoché. Cliquer Calculer avant comptabilisation. Les dates d’exercice et périodes doivent être déjà préparées.',
 'Oracle indépendant': 'Convention interne existante linéaire30/360 avec bornes inclusives :24000/5=4800/an ;01/01/2026 compte un jour,4800/360=13,333... arrondi13,33. Cumul4800+13,33=4813,33 ;VNC24000−4813,33=19186,67 ;résultat20000−19186,67=813,33 ;TVA hypothétique20000×20%=4000 ;TTC24000. Ce calcul ne qualifie pas la convention ou la TVA comme règle fiscale obligatoire.',
 'Écritures attendues de sortie': 'Trois écritures nouvelles, sans banque :AM débit61935/crédit28355 :13,33 ;OD débit28355 :4813,33 et débit6513 :19186,67 contre crédit2355 :24000 ;VT débit3481 :24000 contre crédit7513 :20000 et crédit4455 :4000. La validation définitive des nouvelles écritures reste une action distincte du responsable. Ne pas modifier les écritures2025.',
 'Réserves': 'IMM004 reste Partiel :ancien cahier attendait VNC19200 et résultat800,alors que le prorata interne actuel donne19186,67 et813,33. TVA de cession/régularisation et convention à qualifier par le responsable avec les sources applicables. Pas de déclaration de conformité ni de régularisation automatique. Paie inchangée.'}
CAS = [
 ('IMM927-01','Lire les montants avant toute écriture','Bien linéaire préparé selon le jeu ;2025 et2026 ouverts.',
  'Sortie du jeu :01/01/2026,20000HT,20%,sans encaissement.',
  'Photographier le Journal et le registre avant. Ouvrir Cession et saisir les paramètres. Cliquer Calculer avant comptabilisation. Lire les six montants,la convention et les deux lignes de dotation. Fermer avec Annuler puis comparer le Journal.',
  'Brut24000,cumul4813,33,VNC19186,67,résultat813,33,TVA4000,TTC24000. Dotation2025 déjà comptabilisée et2026 de13,33 à comptabiliser. Bien actif,aucune nouvelle écriture,aucune période créée.',
  'Aucune écriture créée par l’aperçu. La trace technique de consultation peut être conservée.'),
 ('IMM927-02','Écarter un aperçu après modification','Même bien encore actif ;aperçu IMM927-01 recalculé.',
  'Passer le prix HT de20000 à21000,puis revenir à20000.',
  'Changer le prix et vérifier la disparition immédiate de l’aperçu. Revenir à20000 :l’ancien aperçu ne doit pas réapparaître. Recalculer puis vérifier les montants du jeu. Faire aussi un essai à390px de largeur.',
  'Aucun affichage ancien réutilisé,aucune écriture ;montants et actions accessibles par défilement vertical à390px.',
  'Aucune écriture ;recalcul purement préparatoire.'),
 ('IMM927-03','Comptabiliser la cession annoncée','IMM927-02 terminé,aperçu courant visible ;pas de dotation2026 ajoutée ailleurs.',
  'Paramètres inchangés :01/01/2026,20000HT,20%,sans encaissement.',
  'Noter l’aperçu puis utiliser le bouton de comptabilisation existant. Vérifier le registre actualisé et les trois écritures du Journal. Comparer les montants avec l’aperçu et vérifier la conservation des écritures2025. Ne pas cliquer une seconde fois pour recréer une sortie.',
  'Bien Cédé ;montants identiques à l’aperçu,trois écritures nouvelles équilibrées,aucun encaissement bancaire créé. Une seconde sortie de ce bien est refusée.',
  JEU['Écritures attendues de sortie']),
 ('IMM927-04','Préparer une mise au rebut','Créer un deuxième bien Immobilisation REBUT FICTIVE927 avec les mêmes données et sa dotation2025 validée ;ne pas réutiliser le bien cédé.',
  'Nature Mise au rebut,date01/01/2026 ;ne pas saisir un prix de vente ou un encaissement.',
  'Ouvrir la sortie de ce deuxième bien,choisir Mise au rebut et calculer. Vérifier les montants puis comptabiliser. Contrôler le Journal et le registre.',
  'Cumul4813,33,VNC19186,67,résultat−19186,67,prix/TVA/TTC0. Bien au rebut ;deux écritures nouvelles,pas de VT ou banque. La qualification fiscale reste hors de cet essai.',
  'AM13,33 puis OD :débit28355 4813,33 et6513 19186,67/crédit2355 24000.'),
 ('IMM927-05','Refuser les sources devenues différentes','Cas technique sur un troisième bien préparé identiquement,avec accès au banc isolé du technicien ;sinon Bloqué.',
  'Aperçu courant puis dotation2026 indépendante de13,33 sur le même bien,référence AM-2026-ID réel ;aucune donnée réelle.',
  'Le technicien rejoue test_927_changement_demande_ou_dotation_rend_apercu_perime dans le test fourni. Après l’aperçu,comptabiliser et valider la dotation exacte par un autre flux. Soumettre l’ancienne empreinte. Recalculer puis enregistrer la sortie.',
  'Ancienne empreinte refusée409 avant ajout d’écriture. Nouvel aperçu :2026 déjà comptabilisée ;enregistrement avec seulement OD etVT,sans doublon de dotation.',
  'Dotation indépendante13,33 conservée ;deux écritures de sortie seulement après recalcul.'),
 ('IMM927-06','Vérifier droits et lecture seule','Technicien disposant du banc PostgreSQL nonce,second compte invité Consultation seule et société distincte ;sinon Bloqué.',
  'Un bien actif du jeu ;aucun jeton,secret ou identifiant réel à joindre aux preuves.',
  'Rejouer les tests927 de lecture seule SQL et rôles/sociétés/dates/montants non finis. La consultation API de l’aperçu est permise au lecteur ;le formulaire de mutation n’est pas garanti accessible à ce rôle. Vérifier le refus d’enregistrement et l’isolation de société.',
  'Aperçu200 pour le lecteur,enregistrement403,autre société404,NaN/Infinity422 ;calcul métier exécutable en transaction SQL READ ONLY,comptabilité/calendrier/séquences métier inchangés. Audit HTTP distinct possible.',
  'Aucune mutation comptable par ces refus et consultations.')]

def generer():
 (D/'JEU_APERCU_SORTIES_927.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
 styles=getSampleStyleSheet()
 font=Path('C:/Windows/Fonts/arial.ttf')
 if font.exists():
  pdfmetrics.registerFont(TTFont('Arial927',str(font)))
  for s in styles.byName.values():s.fontName='Arial927'
 styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
 p=lambda t,s='BodyText':Paragraph(escape(str(t)),styles[s])
 story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Aperçu des sorties d’immobilisations927','Heading1'),p('Six cas humains Non testé. Recette pilote et mise en production restent distinctes des tests automatiques.')]
 for k,v in JEU.items():story.append(KeepTogether([p(k,'Heading2'),p(v),Spacer(1,8)]))
 story.append(PageBreak());w=Workbook();sy=w.active;sy.title='Synthese';s=w.create_sheet('Immobilisations')
 s.append(['ID','Objectif','Prérequis','Données exactes','Actions détaillées','Attendu','Écritures attendues','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuves/captures'])
 for ident,obj,pre,data,actions,att,ec in CAS:
  fi='TVA20% hypothétique ;convention et régularisation à qualifier. Aucune conformité fiscale validée.'
  co='Montants,équilibre et nombre d’écritures,absence de doublon,ancien historique inchangé,statut du bien.'
  preuve='Captures aperçu/registre/Journal,références effectivement générées ;pour cas technique,rapport pytest du banc isolé.'
  bloc=[p(ident+' — '+obj,'Heading2')]
  for k,v in [('Module','Immobilisations / comptabilité'),('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Statut','Non testé ;Bloqué si prérequis absent.'),('Preuves',preuve)]:bloc.append(p(k+' : '+v))
  story.append(KeepTogether(bloc+[Spacer(1,12)]));s.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','',preuve])
 pdf=D/'RECETTE_APERCU_SORTIES_927.pdf';SimpleDocTemplate(str(pdf),title='HisabPro — aperçu de sortie927').build(story)
 for row in [['HISABPRO — APERÇU SORTIE927'],['Production','Non validée'],['Statut','Nombre']]:sy.append(row)
 for statut in ['Non testé','Réussi','Échoué','Bloqué']:sy.append([statut,f'=COUNTIF(Immobilisations!J2:J7,"{statut}")'])
 sy.append(['Cas',len(CAS)]);sy.append(['Progression','=IFERROR(B5/B8,0)']);sy['B9'].number_format='0%'
 d=w.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
 for k,v in JEU.items():d.append([k,v])
 for sh in w:
  sh.freeze_panes='B2';sh.auto_filter.ref=sh.dimensions
  for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=42
  for row in sh:
   sh.row_dimensions[row[0].row].height=245 if sh==s and row[0].row>1 else 80
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
  for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24589C')
 d.column_dimensions['B'].width=100;dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');s.add_data_validation(dv);dv.add('J2:J7')
 x=D/'SUIVI_APERCU_SORTIES_927.xlsx';w.save(x)
 texte='\n'.join(page.extract_text() or '' for page in PdfReader(pdf).pages)
 assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
 wb=load_workbook(x);assert all(wb['Immobilisations'].cell(i,10).value=='Non testé' for i in range(2,8));wb.close()
 print(json.dumps({'cas_humains':len(CAS),'statut':'Tous Non testé','pages':len(PdfReader(pdf).pages),'feuilles':w.sheetnames},ensure_ascii=False))

if __name__=='__main__':generer()
