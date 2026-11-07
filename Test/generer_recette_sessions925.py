"""Recette de reconnexion ; ne contient aucun jeton ou clé, même de test."""
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
JEU={'environnement':'Copie isolée restaurable. Code925 sur toutes les instances de ce laboratoire ;aucune migration925. Aucune manipulation de la base habituelle.',
 'societe_A':'RECETTE SESSIONS925 A — FICTIVE','societe_B':'RECETTE SESSIONS925 B — FICTIVE',
 'administrateur':'Admin fictif925 ;email admin.fictif925@example.test ;mot de passe initial AncienSecretFictif925!',
 'nouveau_mot_de_passe':'NouveauSecretFictif925!',
 'lecteur':'Lecteur fictif925 ;email lecteur.fictif925@example.test ;mot de passe LecteurSecretFictif925! ;compte propre puis invitation Consultation seule dansA.',
 'ancien_navigateur':'Prérequis spécifique :session sans version dans un navigateur de recette ou banc synthétique isolé préparé par le technicien. Sans prérequis,casSES925-02 Bloqué ;aucun jeton réel à copier dans un document.',
 'ecran':'Ouvrir Factures ou Clôture avant expiration. La connexion apparaît sur la route courante et reprend cet écran après succès.',
 'controles':'Aucune facture,écriture,règlement ou solde créé/modifié par les opérations de session. Conserver les captures de connexion/refus et les IDs de société,mais aucun secret ou jeton.'}
CAS=[
 ('SES925-01','Vérifier la connexion courante','Code925 sur copie,sociétéA et administrateur fictif du jeu créés par inscription.',
  'Email admin.fictif925@example.test et mot de passe AncienSecretFictif925!.',
  'Se déconnecter puis se reconnecter. Ouvrir Factures,Journal et Paramètres. Recharger une page protégée. Le technicien vérifie que la session nouvellement émise porte sa version,sans conserver le jeton dans les preuves.',
  'Connexion et lectures autorisées selon le rôle ;aucune reconnexion répétée ou donnée comptable modifiée.'),
 ('SES925-02','Reprendre une ancienne session','Navigateur de recette déjà muni d’une vraie ancienne session sans version,ou banc synthétique isolé du technicien. Sinon classer Bloqué.',
  'Compte fictif du jeu et ancien navigateur ;ne pas modifier un jeton courant ou utiliser une clé réelle pour préparer ce cas.',
  'Après installation925,ouvrir/recharger l’écran protégé. Vérifier le retour au formulaire de connexion. Saisir les identifiants habituels de ce compte,ouvrir de nouveau Factures et contrôler les écritures avant/après.',
  'Ancienne session refusée401,jeton/rôle local effacés. Une connexion normale rétablit l’accès et reprend l’écran courant,sans changement de mot de passe ni perte de données.'),
 ('SES925-03','Invalider les sessions après changement de secret','Administrateur disposant des sociétés fictivesAetB ;deux navigateurs connectés au même compte.',
  'Premier navigateur dansA,second dansB. Mot de passe initial AncienSecretFictif925!,nouveau NouveauSecretFictif925!.',
  'Dans Paramètres → Mon compte,remplir ancien,nouveau et confirmation,puis modifier le mot de passe. Reconnecter le premier navigateur avec le nouveau secret. Dans le second,lancer une lecture protégée,puis se reconnecter également. Tester que l’ancien secret ne permet plus la connexion.',
  'Les anciennes sessions des deux sociétés sont refusées ;nouveau secret utilisable,ancien refusé. Sociétés,comptes et données comptables conservés. Aucun mot de passe ou jeton joint aux captures.'),
 ('SES925-04','Préserver les droits de société et la révocation','AdministrateurA et lecteur du jeu,compte du lecteur créé dans sa propre sociétéB avant invitation dansA.',
  'Inviter lecteur.fictif925@example.test dansA avec Consultation seule ;largeurs1440pxet390px.',
  'Le lecteur se connecte et bascule dansA :vérifier consultation et absence d’actions de création. L’administrateur révoque cet accès. Le lecteur actualiseA,puis vérifie que son compte propre dansB reste utilisable. Le technicien rejoue aussi la connexion d’un compte fictif à hash bcrypt historique inchangé.',
  'Créations interdites au lecteur,accèsA refusé après révocation,compteB préservé. Connexion sur ancien hash bcrypt possible sans réécriture silencieuse. Aucun effet comptable.')]

def generer():
 (D/'JEU_SESSIONS_925.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8');styles=getSampleStyleSheet()
 if Path('C:/Windows/Fonts/arial.ttf').exists():
  pdfmetrics.registerFont(TTFont('Arial925','C:/Windows/Fonts/arial.ttf'))
  for st in styles.byName.values():st.fontName='Arial925'
 styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;p=lambda t,st='BodyText':Paragraph(escape(str(t)),styles[st]);story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Sessions et reconnexion925','Heading1'),p('Quatre cas humains Non testé. Les tests automatiques et la décision de production sont distincts.')]
 for k,v in JEU.items():story.extend([p(k,'Heading2'),p(v)])
 story.append(PageBreak());w=Workbook();sy=w.active;sy.title='Synthese';s=w.create_sheet('Sessions');s.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuves/captures'])
 for ident,obj,pre,data,actions,att in CAS:
  ec='Aucune écriture ou mutation comptable.';fi='Aucune incidence fiscale directe.';co='Connexion,version de session,compte/société,rôle,révocation et intégrité des données. Aucun secret dans les preuves.';bloc=[p(ident+' — '+obj,'Heading2')]
  for cle,val in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Statut','Non testé ;Bloqué si le prérequis d’ancienne session est absent.'),('Preuves','Captures du formulaire et de l’écran repris,statuts de refus et IDs fictifs ;sans mot de passe ou jeton.')]:bloc.append(p(cle+' : '+val))
  story.append(KeepTogether(bloc+[Spacer(1,12)]));s.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures et IDs seulement'])
 pdf=D/'RECETTE_SESSIONS_925.pdf';SimpleDocTemplate(str(pdf),title='HisabPro — sessions925').build(story)
 for row in [['HISABPRO — SESSIONS925'],['Production','Non validée'],['Statut','Nombre']]:sy.append(row)
 for statut in ['Non testé','Réussi','Échoué','Bloqué']:sy.append([statut,f'=COUNTIF(Sessions!J2:J5,"{statut}")'])
 sy.append(['Cas',4]);sy.append(['Progression','=IFERROR(B5/B8,0)']);sy['B9'].number_format='0%';d=w.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
 for k,v in JEU.items():d.append([k,v])
 for sh in w:
  sh.freeze_panes='B2';sh.auto_filter.ref=sh.dimensions
  for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=42
  for row in sh:
   sh.row_dimensions[row[0].row].height=240 if sh==s and row[0].row>1 else 70
   for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
  for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='24589C')
 d.column_dimensions['B'].width=95;dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');s.add_data_validation(dv);dv.add('J2:J5');x=D/'SUIVI_SESSIONS_925.xlsx';w.save(x)
 texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte;wb=load_workbook(x);assert all(wb['Sessions'].cell(i,10).value=='Non testé' for i in range(2,6));wb.close()
 print(json.dumps({'cas_humains':4,'statut':'Tous Non testé','pages':len(PdfReader(pdf).pages),'feuilles':w.sheetnames},ensure_ascii=False))

if __name__=='__main__':generer()
