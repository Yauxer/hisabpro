"""Recette chiffrée des campagnes brutes ;aucun résultat fiscal inventé."""
from pathlib import Path
from html import escape
from decimal import Decimal
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
JEU={'societe':'RECETTE PERSONNEL879 — FICTIF','periode':'2026-11','salarie':'P001 — Salma FICTIVE','date_entree_connue':'2025-12-15','base_mensuelle':'9000.10','gain_PRIME_FICTIVE889':'800.01','gain_QUANT_FICTIVE891':'1.01','total_gains':'801.02','brut_initial':'9801.12','motif_premiere_simulation':'Simulation fictive novembre893','variable_ponctuelle_supplementaire_code':'QUANT_FICTIVE891','variable_supplementaire_quantite':'1','variable_supplementaire_taux':'1.00','variable_supplementaire_effet':'2026-11-15','variable_supplementaire_source':'VAR-CAMP893-ATTENTE','variable_supplementaire_justificatif':'ATTEST-CAMP893-ATTENTE','variable_supplementaire_motif':'Gain complémentaire fictif893','gain_supplementaire':'1.00','brut_apres_gain_supplementaire':'9802.12','cotisations_salariales':None,'cotisations_patronales':None,'IR':None,'net_a_payer':None,'attention':'Données entièrement fictives ;brut pédagogique uniquement,aucune paie définitive.'}
CAS=[
 ('PA-CAMP01','Préparer la campagne sans inventer la date d’entrée','Cahiers887/889/891 effectués sur copie restaurable ;technicien et préparateur habilités.','Migration115 après114. P001 :entrée connue2025-12-15,base9000.10 mensuelle,contrat couvrant novembre2026.','Appliquer115 sur copie. Si entrée inconnue,fiche P001 >Proposer une modification >Identité >Coordonnées et informations personnelles >Date d’entrée connue. Saisir15/12/2025,motif Entrée fictive P001 pour recette893,conserver le nom,enregistrer,soumettre etfaire approuver indépendamment.','La date est déclarée etapprouvée,non déduite ducontrat. Aucun salaire oubarème automatiquement modifié ;03 · Traitement de la paie devient accessible.'),
 ('PA-CAMP02','Simuler le brut exact de la sélection','P001 actif avec conditions mensuelles complètes ;deux gains du cahier891 approuvés.','Mois2026-11,sélectionP001 seulement,motif Simulation fictive novembre893 ;confirmer mois complets etvariables préparées.','03 · Traitement de la paie >Nouvelle simulation du brut. Choisir le mois,rechercher P001,cocher la ligne,saisir le motif etla confirmation,puis Simuler et conserver.','Base9000.10,gains801.02,brut9801.12. Cotisations,IR,net etcoût employeur Non calculés. Snapshot version1,auteur etempreinte conservés ;aucune validation de paie.'),
 ('PA-CAMP03','Refuser d’ignorer une variable en attente','Scénario P001 de PA-CAMP02 ;continuer sur la même copie en ajoutant le gain explicite ci-dessous.','Nouvelle variable QUANT_FICTIVE891,novembre,effet15/11/2026,quantité1,taux1.00,source VAR-CAMP893-ATTENTE,justificatif ATTEST-CAMP893-ATTENTE,motif Gain complémentaire fictif893.','Créer ce brouillon sans le soumettre. Revenir aux campagnes etsimuler de nouveau P001,motif Contrôle attente fictif893.','Anomalie variables en attente ;brut global À compléter,aucun total qui ignore1.00MAD. Ancienne version1 reste9801.12.'),
 ('PA-CAMP04','Recalculer et conserver les anciennes versions','Variable supplémentaire de PA-CAMP03 en brouillon.','Soumission motif Soumission complémentaire893 ;approbation motif Contrôle indépendant893,référence CTRL-CAMP893 ;simulation motif Recalcul après variable893.','Soumettre puis faire approuver la variable indépendamment. Simuler de nouveau P001. Ouvrir Historique de la campagne puis les trois versions.','Nouvelle version complète :gains802.02,brut9802.12. Première version reste9801.12,deuxième reste incomplète. Une campagne normale unique pour le mois ;pas d’écrasement.'),
 ('PA-CAMP05','Distinguer un montant inconnu d’un zéro','P004 du cahier887 sans salaire confirmé ;P001 complet du scénario principal.','Même mois,sélectionP001 etP004,motif Contrôle dossier incomplet893.','Créer une nouvelle simulation de la même campagne avec les deux salariés ;consulter les anomalies etles lignes. Ne renseigner aucun faux salaire pour P004.','P001 garde son brut connu ;P004 est À compléter. Les totaux globaux concernés sont inconnus,aucun zéro artificiel ni exclusion silencieuse du salarié incomplet.'),
 ('PA-CAMP06','Contrôler reprise,droits et séparation comptable','Comptable légitime,deux sociétés etdeux sessions de recette.','Preuves dujournal etsoldes avant les simulations ;motif révocation Fin accès campagne893.','Vérifier qu’un double clic pendant une même requête ne duplique pas sa simulation. Contrôler historique,absence de bouton Valider une paie définitive,bulletin,paiement ouOD. Révoquer rémunération du préparateur,puis Actualiser ;vérifier seconde société.','Une reprise identique est idempotente. Nouvelle simulation volontaire crée une version distincte. Révocation/isolation effectives ;journal et soldes inchangés. Les validations SQL natives sont documentées,ne lancer aucun UPDATE sur une base réelle.')
]

def generer():
    assert Decimal(JEU['base_mensuelle'])+Decimal(JEU['gain_PRIME_FICTIVE889'])+Decimal(JEU['gain_QUANT_FICTIVE891'])==Decimal(JEU['brut_initial'])
    assert Decimal(JEU['brut_initial'])+Decimal(JEU['gain_supplementaire'])==Decimal(JEU['brut_apres_gain_supplementaire'])
    (D/'JEU_CAMPAGNES_PAIE_893.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_CAMPAGNES_PAIE_893.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial893','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial893'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Campagnes et simulation du brut893','Heading1'),p('Complément6cas à effectuer après les cahiers887,889 et891. Statuts humains Non testé. Cette recette ne valide aucune paie définitive ;cotisations,IR,net etbulletins ne sont pas livrés par cette étape.'),p('Données exactes et calculs indépendants','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+('Non calculé' if v is None else v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('Campagnes');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ;comparer le journal avant/après.';fi='Cotisations,IR etnet non calculés ;pas de valeur zéro supposée.';co='Société,droits,dates,sources,exactitude,versions etintégrité du snapshot.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Capture de sélection/résultat/anomalies ;IDcampagne,version,empreinte etacteur.'),('Statut','Non testé ;renseigner le classeur etconserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Capture/ID/version à conserver'])
    pdf=D/'RECETTE_CAMPAGNES_PAIE_893.pdf';SimpleDocTemplate(str(pdf),leftMargin=1.7*cm,rightMargin=1.7*cm,title='HisabPro campagnes893').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    for i in range(2,8):w.row_dimensions[i].height=155
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO —CAMPAGNES893'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(Campagnes!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,'Non calculé' if v is None else v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for i in range(2,d.max_row+1):d.row_dimensions[i].height=38
    x=D/'SUIVI_CAMPAGNES_PAIE_893.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['Campagnes'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))

if __name__=='__main__':generer()
