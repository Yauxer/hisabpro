"""Recette humaine des droits du registre ; aucun résultat humain présumé."""
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
JEU={
 'Environnement':'Copie isolée restaurable,code929 sur frontend et backend de la copie. Société fictive du cahier principal ;exercices2025 et2026 et leurs périodes ouverts. Ne jamais utiliser le dossier réel pour ces essais.',
 'Bien actif':'Reprendre le jeu JEU_APERCU_SORTIES_927.json corrigé :Immobilisation FICTIVE927,24000HT,acquisition/mise en service01/01/2025,linéaire5ans,résiduelle0,TVA hypothétique20% récupérable100%,fournisseur FICTIF927,comptes2355/28355/61935,TVA34551,dette4411 explicitement choisie. Acquisition et dotation2025 4800 validées ;bien actif non payé. Ne pas comptabiliser sa sortie avant les essais de consultation.',
 'Utilisateurs':'Depuis Paramètres → Utilisateurs,créer sur la société fictive :Lecteur FICTIF929,lecteur929@example.test,rôle Consultation seule ;Comptable FICTIF929,comptable929@example.test,rôle Comptable ;Administrateur FICTIF929,admin929@example.test,rôle Administrateur. Mot de passe de laboratoire pour chacun :RecetteFictive929! ;ne pas le réutiliser dans un compte réel. Utiliser trois navigateurs privés ou se déconnecter entre les comptes.',
 'Historique facultatif préparé':'Pour la branche de reconstitution administrative,le responsable prépare sur le laboratoire un bien HISTORIQUE FICTIF929 de24000HT,acquisition/mise en service01/01/2025,linéaire5ans,résiduelle0,sans écriture d’acquisition ni paiement. Ce prérequis technique ne s’invente pas dans le dossier réel. S’il manque,noter cette branche Bloquée et conserver le reste du résultat.',
 'Contrôles communs':'Choisir exercice2026. Ouvrir Immobilisations,lire le registre et déployer le plan en cliquant la ligne. Ouvrir Réconciliation historique,consulter les diagnostics,puis Fermer. Comparer Journal et registre avant/après. Largeurs de recette1440px et390px. Aucune consultation ne crée d’écriture ;trace d’audit HTTP distincte possible.',
 'Réserves':'Droits API existants conservés. Diagnostic historique accessible au lecteur et au comptable,corrections réservées à administrateur. Convention de prorata/TVA de cession toujours à qualifier ;aucune paie définitive ou production approuvée par ces essais.'}
CAS=[
 ('IMM929-01','Consulter comme lecteur','Compte lecteur du jeu,bien actif préparé,exercice2026.',
  'lecteur929@example.test ;mot de passe de laboratoire du jeu.',
  'Se connecter,ouvrir Immobilisations. Vérifier Nouvelle immobilisation et Dotations2026 désactivés. Déployer le plan et ouvrir Réconciliation historique. Lire le statut de consultation,les montants et alertes. Vérifier les champs de correction désactivés et les commandes administratives absentes. Fermer. Vérifier aussi les autres lignes présentes :pas de commandes Modifier,Payer,Cession,Encaisser ou Archiver.',
  'Registre,plan et diagnostic lisibles. Aucun formulaire de mutation proposé au lecteur. Aucun bouton Générer dans le plan. Journal et biens inchangés. Les appels directs d’écriture restent403 (preuve technique distincte).',
  'Aucune écriture nouvelle.'),
 ('IMM929-02','Distinguer comptabilité courante et correction historique','Compte comptable du jeu,bien actif préparé,exercice2026.',
  'comptable929@example.test ;mot de passe de laboratoire du jeu.',
  'Se connecter,ouvrir Immobilisations. Ouvrir Nouvelle immobilisation,puis Annuler. Ouvrir Modifier sur le bien actif,puis Annuler. Vérifier les commandes de paiement/sortie et Générer dans le plan. Ouvrir Réconciliation historique :lire le diagnostic,contrôler le message administrateur et l’absence des trois commandes de correction. Fermer sans saisie comptable.',
  'Actions courantes conservées pour Comptable. Réconciliation historique en consultation :aucune reconstitution,reclassement ou correction d’amortissement proposée. Annuler les formulaires ne crée rien.',
  'Aucune écriture par les consultations et annulations de ce cas.'),
 ('IMM929-03','Conserver les corrections autorisées à administrateur','Compte administrateur,exercice2026 ouvert ;bien historique préparé pour la branche de reconstitution,sinon branche Bloquée.',
  'admin929@example.test ;bien HISTORIQUE FICTIF929 ;contrepartie4481 explicitement confirmée.',
  'Vérifier les commandes courantes puis ouvrir Réconciliation historique. Les trois commandes administratives sont présentes et restent conditionnées au diagnostic. Pour la branche préparée,saisir4481 comme compte d’ouverture,cocher uniquement ce bien,puis Reconstituer acquisitions et confirmer. Contrôler le Journal et le diagnostic actualisé. Ne pas valider définitivement la reprise dans ce cas.',
  'Une seule reprise d’ouverture2026 en brouillon,diagnostic actualisé et originaux inchangés. Les alertes et les conditions de période/exercice restent appliquées ;l’administrateur ne contourne pas les contrôles métier.',
  'Branche préparée :AN au01/01/2026,débit2355 24000,crédit28355 4800,crédit4481 19200. Pas de TVA historique recréée ni paiement ;écriture à contrôler avant validation.')]

def generer():
 (D/'JEU_DROITS_IMMOBILISATIONS_929.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
 st=getSampleStyleSheet();font=Path('C:/Windows/Fonts/arial.ttf')
 if font.exists():
  pdfmetrics.registerFont(TTFont('Arial929',str(font)))
  for s in st.byName.values():s.fontName='Arial929'
 st['BodyText'].fontSize=9;st['BodyText'].leading=13;p=lambda t,s='BodyText':Paragraph(escape(str(t)),st[s])
 story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Droits des immobilisations929','Heading1'),p('Trois cas humains Non testé. Les tests automatiques ne renseignent pas la recette humaine.')]
 for k,v in JEU.items():story.append(KeepTogether([p(k,'Heading2'),p(v),Spacer(1,8)]))
 story.append(PageBreak());w=Workbook();sy=w.active;sy.title='Synthese';s=w.create_sheet('Droits immobilisations')
 s.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures attendues','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuves/captures'])
 for ident,obj,pre,data,actions,att,ec in CAS:
  fi='Aucune nouvelle règle fiscale ;convention/TVA de cession non qualifiées par ce cas.';co='Rôle,société,commandes,lisibilité,Journal inchangé hors reprise explicitement demandée.';preuve='Captures registre/plan/diagnostic,référence de reprise réelle si applicable ;aucun secret dans les preuves.'
  bloc=[p(ident+' — '+obj,'Heading2')]
  for k,v in [('Module','Immobilisations / permissions'),('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Statut','Non testé ;documenter tout prérequis bloquant.'),('Preuves',preuve)]:bloc.append(p(k+' : '+v))
  story.append(KeepTogether(bloc+[Spacer(1,12)]));s.append([ident,'Immobilisations',obj,pre,data,actions,att,ec,fi,co,'Non testé','','','',preuve])
 pdf=D/'RECETTE_DROITS_IMMOBILISATIONS_929.pdf';SimpleDocTemplate(str(pdf),title='HisabPro — droits des immobilisations929').build(story)
 for row in [['HISABPRO — DROITS IMMOBILISATIONS929'],['Production','Non validée'],['Statut','Nombre']]:sy.append(row)
 for statut in ['Non testé','Réussi','Échoué','Bloqué']:sy.append([statut,f'=COUNTIF(\'Droits immobilisations\'!K2:K4,"{statut}")'])
 sy.append(['Cas',3]);sy.append(['Progression','=IFERROR(B5/B8,0)']);sy['B9'].number_format='0%'
 d=w.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
 for k,v in JEU.items():d.append([k,v])
 for sh in w:
  sh.freeze_panes='B2';sh.auto_filter.ref=sh.dimensions
  for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=43
  for row in sh:
   sh.row_dimensions[row[0].row].height=245 if sh==s and row[0].row>1 else 80
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
  for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24589C')
 d.column_dimensions['B'].width=100;dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');s.add_data_validation(dv);dv.add('K2:K4')
 x=D/'SUIVI_DROITS_IMMOBILISATIONS_929.xlsx';w.save(x)
 texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
 wb=load_workbook(x);assert all(wb['Droits immobilisations'].cell(i,11).value=='Non testé' for i in range(2,5));wb.close()
 print(json.dumps({'cas_humains':3,'statut':'Tous Non testé','pages':len(PdfReader(pdf).pages),'feuilles':w.sheetnames},ensure_ascii=False))

if __name__=='__main__':generer()
