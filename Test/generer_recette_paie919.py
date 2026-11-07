"""Recette du référentiel social ; aucune hypothèse fictive n'est un taux légal."""
from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
JEU={'societe':'RECETTE PERSONNEL919 — société fictive sur copie isolée',
 'installation':'Code919 et migration123 après114 ; prérequis du workflowPersonnel et des campagnes déjà installés. Aucun taux ou salarié créé automatiquement.',
 'menu':'02 · Éléments de paie → Variables mensuelles',
 'preparation':'Suivre le guide891 pour créer et faire approuver une ficheRATT919, un contratCDI à partir du2026-01-01 et une rémunération mensuelle9000.10. Catalogue : rubriqueRATTACHEMENT_FICTIF919,GAIN,MONTANT,mensuelle, applicable2026-01-01, avec justificatif ATTESTATION_FICTIVE. Reprendre les paramètres de recette891 ; ne pas qualifier ces hypothèses comme règles légales.',
 'periode_traitement':'2026-11-01','date_effet':'2026-11-15','montant':'800.01',
 'justificatif_variable':'ATTESTATION_FICTIVE : PIECE-FICTIVE919','source_variable':'SOURCE-FICTIVE919','motif':'Rattachement documentaire entièrement FICTIF919',
 'reference_debut':'2025-01-01','reference_fin':'2025-12-31','reference_justification':'PRIME-ANNUELLE-FICTIVE919',
 'versement_date':'2026-12-05','versement_reference':'VERSEMENT-DECLARE-FICTIF919',
 'decision':'Second acteur indépendant ; motif Approbation fictive919 ; référence CTRL-FICTIF919 ; confirmer indépendance et contrôle des justificatifs.',
 'attendu':'Variable approuvée800.01 ; période2026-11, effet2026-11-15, référence2025-01-01au2025-12-31, versement déclaré2026-12-05. Brut purement arithmétique9000.10+800.01=9800.11, sans nouveau traitementIR/social/régularisation ou paiement confirmé.',
 'periodes_exactes':[{'periode':'2026-11-01','date_effet_variable':'2026-11-15','reference_variable':'SOURCE-FICTIVE919'}],
 'attention':'La présence de dates et références ne confirme ni un paiement bancaire ni une méthode fiscale. Les champs restent facultatifs quand les faits ne sont pas connus.'}
CAS=[
 ('PA-RAT01','Conserver les trois dimensions de dates','Copie isolée, migration123 ; fiche et rubrique du jeu approuvées.',
  'Toutes les valeurs du jeu : traitement2026-11, effet15/11/2026, référence01/01/2025au31/12/2025, versement déclaré05/12/2026 ; montant800.01.',
  'Créer une variable. Déplier Période de référence et versement déclaré (facultatif), remplir les cinq nouveaux champs. Enregistrer puis consulter le détail.',
  'Les dates restent différentes et les références sont conservées ; aucun rattachement automatique au mois de traitement ni paiement confirmé.'),
 ('PA-RAT02','Soumettre et contrôler indépendamment','PA-RAT01 ; second acteur habilité, indépendant du préparateur et bénéficiaire.',
  'Motif Approbation fictive919, référence CTRL-FICTIF919 ; cocher indépendance et justificatifs après examen.',
  'Soumettre la variable. Le second acteur ouvre le détail, compare dates et références, puis approuve. Le préparateur Actualise et consulte de nouveau.',
  'Même rattachement dans la variable approuvée et historique ; aucune auto-approbation ou édition de données approuvées.'),
 ('PA-RAT03','Propager les faits sans modifier le brut','PA-RAT02 ; salaire9000.10 en vigueur sur tout novembre2026.',
  'Campagne pédagogique de novembre2026 pourRATT919, mois complet confirmé uniquement dans le jeu fictif.',
  'Simuler le brut selon le guide893. Vérifier le montant et la variable source ; relire le rattachement par la variable.',
  'Brut9800.11 ; dates conservées dans le snapshot technique, preuves textuelles absentes de cette synthèse. Aucun prorata ouIR pour le rappel déduit de ces dates.'),
 ('PA-RAT04','Refuser les renseignements incomplets','Nouvelle variable sur autre période ou après annulation d’un brouillon erroné.',
  'Début2025-01-01 avec fin vide, puis fin2024-12-31 ; date de versement2026-12-05 sans référence.',
  'Tenter successivement chaque saisie. Corriger les champs dans le formulaire et vérifier le message.',
  'Enregistrement refusé pour paire incomplète ou période inversée ; aucune date de substitution ni donnée comptable créée.'),
 ('PA-RAT05','Préserver l’historique sans dates inventées','Variable ancienne ou nouvelle saisie en laissant le panneau facultatif vide.',
  'Aucun rattachement renseigné ; source et justificatifs normaux du guide891.',
  'Créer, soumettre et approuver normalement. Consulter la variable et une ancienne simulation.',
  'Ancien parcours fonctionnel ; dates Non renseignée, aucune copie automatique de la date d’effet. Anciennes simulations et empreintes inchangées.'),
 ('PA-RAT06','Vérifier droits, mobile et restauration','Deux sociétés fictives ; lecteur de rémunération sans droit audit/approbation ; responsable de sauvegarde.',
  'Même variable, références PRlME/VERSEMENT du jeu ; vues390pxet1440px.',
  'Lire avec le lecteur puis depuis l’autre société ; révoquer le droit et Actualiser. Faire restaurer la copie dans une seconde cible et relire la variable et son snapshot.',
  'Justifications masquées au lecteur non habilité, aucune fuite inter-société, accès retiré après révocation. Métadonnées, empreintes et garde123 restitués. Recette utilisateur à renseigner avec preuves.')]

def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_RATTACHEMENT_PAIE_919.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_RATTACHEMENT_PAIE_919.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial919','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial919'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Rattachement documentaire des revenus919','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Dates et références des variables ; aucun paiement confirmé, nouvelle règle fiscale ou recalcul historique.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():
        if k=='periodes_exactes':
            story.append(p('Période du jeu de recette','Heading2'))
            for m in v:story.append(p(m['periode']+' — Date variable '+m['date_effet_variable']+' — Référence '+m['reference_variable']))
        else:story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('Variables');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Rattachement documentaire seulement ; aucun nouveau calculIR/social, net ou paiement.';co='Société, droits, dates indépendantes, justificatifs, masquage et intégrité des variables et snapshots.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_RATTACHEMENT_PAIE_919.pdf';SimpleDocTemplate(str(pdf),title='HisabPro IR annuel sourcé919').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — RATTACHEMENT919'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(Variables!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,'Voir feuille Periodes et tableau du PDF' if isinstance(v,list) else v])
    per=wb.create_sheet('Periodes');per.append(list(JEU['periodes_exactes'][0]))
    for m in JEU['periodes_exactes']:per.append(list(m.values()))
    per.freeze_panes='C2';per.auto_filter.ref=per.dimensions
    for col in per.columns:per.column_dimensions[col[0].column_letter].width=30
    for row in per:
        per.row_dimensions[row[0].row].height=40
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for row in d:
        d.row_dimensions[row[0].row].height=min(409,max(30,((len(str(row[1].value or ''))+84)//85)*15+10))
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_RATTACHEMENT_PAIE_919.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['Variables'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
