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
JEU={'societe': 'RECETTE PERSONNEL879 — FICTIF, copie restaurable uniquement', 'menu': '05 · Fiscalité salariale → Cumuls et frais annuels', 'annee': '2026', 'salarie': 'P909 — fiche/contrat/rémunération du jeu909', 'installation': '121 après120 ; Personnel actif/protégé et habilitations identité/rémunération/proposer', 'sources_mensuelles': 'Reprendre le jeu909 (base9000.10, gain800.01, IRplafond500/par opération, gainexclu basefrais, social60déductibles/294non) dans chaque mois2026, en environnement synthétique seulement. Les règles et preuves FICTIVES restent interdites pour toute vraie paie.', 'periodes_exactes': [{'periode': '2026-01-01', 'date_effet_variable': '2026-01-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-01', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-02-01', 'date_effet_variable': '2026-02-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-02', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-03-01', 'date_effet_variable': '2026-03-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-03', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-04-01', 'date_effet_variable': '2026-04-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-04', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-05-01', 'date_effet_variable': '2026-05-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-05', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-06-01', 'date_effet_variable': '2026-06-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-06', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-07-01', 'date_effet_variable': '2026-07-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-07', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-08-01', 'date_effet_variable': '2026-08-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-08', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-09-01', 'date_effet_variable': '2026-09-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-09', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-10-01', 'date_effet_variable': '2026-10-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-10', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-11-01', 'date_effet_variable': '2026-11-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-11', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}, {'periode': '2026-12-01', 'date_effet_variable': '2026-12-15', 'reference_variable': 'GAIN-ANNUEL-FICTIF913-12', 'brut': '9800.11', 'social_salarial': '354.00', 'brut_imposable': '9300.11', 'base_frais': '9000.10', 'deductible': '60.00', 'non_deductible': '294.00'}], 'choix': 'Une préparation fiscale parmois pourP909 ; si plusieurs versions, choisir explicitementcellejustifiée ; aucun ID universel préinventé, noterlesIDs retournés.', 'cadre': 'Confirmer59-I-A horsB/C et autres revenus/cas nontraités, uniquement si justifié danslejeu.', 'correspondance': 'Confirmer exhaustivité et correspondance desrevenus2026 ; paiement vérifié séparément, aucune date déduite.', 'reference_annuelle': 'ANNEE-FICTIVE913', 'autres_deductions': '0.00', 'reference_autres': 'AUCUNE-AUTRE-FICTIVE913', 'motif': 'Contrôle annuel FICTIF913', 'confirmation_autres': 'Cocher après vérification du zéro dujeu ;nepasprésumer0 en exploitation.', 'attendus': 'Cumul brutimposable111601.32 ;basefrais108001.20 ;déductible720.00 ;taux25% ;frais27000.3000 ;RNIarithmétique83881.0200 avantarrondis.', 'attention': 'Contrôle annuel uniquement, sans retenue mensuelle,versement,net,paiement ouécriture. Toutes les opérations etpreuves de cejeu sont fictives.'}
CAS=[('PA-FRAIS01', 'Préparer les douze mois et choisir les versions', 'Copie isolée restaurable ; jeu909 avec règles et preuves entièrement fictives, acteurs distincts et droits requis.', 'P909, base9000.10 et gain800.01 par mois. Utiliser les périodes, dates et références de la feuille Periodes.', 'Pour chacun des douze mois, créer puis faire approuver la variable, simuler le brut, le social et les bases comme dans le guide909. Ouvrir Cumuls et frais annuels, créer un contrôle, choisir P909 et Charger les préparations. Cliquer Choisir les mois à version unique, puis inspecter chaque choix.', 'Douze sources réelles de test. Un mois comportant plusieurs versions reste à choisir explicitement. Aucun identifiant inventé ni addition de versions.'), ('PA-FRAIS02', 'Calculer le contrôle annuel complet', 'PA-FRAIS01 ; exhaustivité et cadre général vérifiés dans le jeu fictif.', 'Référence ANNEE-FICTIVE913 ; autres déductions0.00, référence AUCUNE-AUTRE-FICTIVE913 ; motif Contrôle annuel FICTIF913. Confirmer cadre général, revenus, autres déductions et périmètre arithmétique.', 'Calculer et conserver. Déplier Périodes et sources conservées. Comparer les douze identifiants, versions et empreintes aux préparations sélectionnées.', 'Cumul du brut imposable111601.32, base des frais108001.20, cotisations déductibles720.00, taux25%, frais27000.3000 et RNI arithmétique83881.0200. Aucun versement ou retenue mensuelle déterminé.'), ('PA-FRAIS03', 'Garder un cumul partiel sans extrapolation', 'Premier contrôle complet conservé ; créer de nouveaux contrôles.', 'Essai1 : mêmes choix sauf janvier laissé Non choisi. Essai2 : novembre seul. Autres champs identiques au cas02.', 'Enregistrer séparément les deux contrôles. Lire le nombre de mois et les anomalies. Ne pas remplacer les mois absents par des zéros.', 'Onze puis une période, frais annuels et RNI inconnus. Le cumul de novembre reste9300.11 ; aucun facteur douze appliqué.'), ('PA-FRAIS04', 'Distinguer autres déductions inconnues et zéro', 'Douze préparations choisies, cadre général et revenus confirmés.', 'Autres déductions laissées vides, confirmation correspondante non cochée. Référence annuelle et motif identiques au cas02.', 'Calculer. Lire les frais et le RNI, puis consulter à nouveau le premier contrôle complet.', 'Frais27000.3000 connus mais RNI À compléter. Zéro n’est pas présumé. Le premier contrôle, ses sources et son empreinte restent inchangés.'), ('PA-FRAIS05', 'Refuser une source devenue périmée', 'Ancien contrôle conservé, préparateur et décideur indépendants.', 'Nouvelle variable ponctuelle100.00 sur GAIN_FICTIF909, novembre2026, date2026-11-15, référence EXTRA-ANNUEL-FICTIF913, justificatif ATTESTATION_FICTIVE=PIECE-FICTIVE913.', 'Créer, soumettre et faire approuver la variable. Tenter un nouveau contrôle annuel avec les anciennes préparations. Refaire le brut, le social et les bases pour recalculer.', 'Ancienne source refusée pour un nouveau calcul ; contrôle historique consultable. Les nouvelles versions doivent être sélectionnées explicitement, sans réécrire les anciens snapshots.'), ('PA-FRAIS06', 'Vérifier les droits et la séparation de la paie', 'Deux sociétés fictives, administrateur des habilitations ; journal relevé avant recette.', 'Identifiants des contrôles et motif Fin accès fictif913.', 'Changer de société, puis révoquer rémunération et Actualiser. Vérifier ordinateur et mobile, liens de sources, onglets Bases fiscales et Contrôle annuel IR. Comparer les soldes comptables avant et après.', 'Données isolées puis masquées après révocation. Lecture verticale et sources conservées. Aucun bulletin, paiement, écriture ou paie définitive ; production non validée.')]

def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_FRAIS_ANNUELS_PAIE_913.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_FRAIS_ANNUELS_PAIE_913.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial913','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial913'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Cumuls et frais professionnels annuels913','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Cumuls sourcés et frais annuels ; RNI avant arrondis, sans retenue mensuelle, versement ou paie définitive.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():
        if k=='periodes_exactes':
            story.append(p('Douze périodes et références exactes','Heading2'))
            for m in v:story.append(p(m['periode']+' — Date variable '+m['date_effet_variable']+' — Référence '+m['reference_variable']))
        else:story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('IRAnnuel');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Contrôle arithmétique annuel uniquement ; montant à déclarer, retenue mensuelle et net non déterminés.';co='Société, droits, année, RNI déclaré, éligibilité, exactitude par tranche, inconnues et intégrité des snapshots.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_FRAIS_ANNUELS_PAIE_913.pdf';SimpleDocTemplate(str(pdf),title='HisabPro frais annuels913').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — IR ANNUEL913'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(IRAnnuel!J2:J7,"{statut}")'])
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
    x=D/'SUIVI_FRAIS_ANNUELS_PAIE_913.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['IRAnnuel'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
