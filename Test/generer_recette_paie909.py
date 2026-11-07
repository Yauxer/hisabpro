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
JEU={'societe': 'RECETTE PERSONNEL879 — FICTIF, copie isolée restaurable', 'menu': '05 · Fiscalité salariale → Bases fiscales', 'installation': '120 après113–119 ; module Personnel actif/protégé ; droits identité/rémunération/proposer', 'sources': 'Un salarié P909, contrat mensuel approuvé, rémunération9000.10 applicable tout novembre2026 ; variable ponctuelle800.01 approuvée ; brut9800.11 et social complets', 'rubrique_fictive': 'GAIN_FICTIF909, Gain, Ponctuelle, Montant exact, début2026-01-01, fin vide, compte vide, justificatif ATTESTATION_FICTIVE, aucune incompatibilité', 'regles_rubrique': 'IR : plafond500.00/par opération ; CNSS : plafond300.00/par opération ; AMO : soumis. Conditions Hypothèse FICTIVE909 sans portée légale. IR qualifié seulement dans le jeu de test isolé ; frais Exclue / qualifiée dans ce même jeu.', 'branches_fictives': 'Régime REGIME_FISC909. B1_FICTIF909 : CNSS, salarial1%, patronal2%, plafond6000.00/mensuel, composantB1, déductibilité intégrale fictive. B2_FICTIF909 : AMO, salarial3%, patronal4%, sans plafond, composantB2, non déductible fictivement. Organisme Organisme fictif, début2026-01-01, conditions Hypothèse FICTIVE909 sans portée légale.', 'qualification_test': 'Pour la recette isolée exclusivement, le technicien peut constituer les états synthétiques qualifiés comme les fixtures test_paie909_bases_isole.py : texte/article/référence FICTIF909, URL https://www.finances.gov.ma/, SHA a répété64fois, consultation2026-01-01 ; approbateur distinct habilité valider_regles_paie. Ces références fictives ne justifient aucune véritable règle et sont interdites pour une paie réelle.', 'sources_reelles': 'En exploitation, utiliser uniquement des preuves véritables de l’éligibilité du salarié et de chaque règle, contrôlées par le décideur. Ne pas copier les taux ou preuves fictifs du cahier.', 'declarations_sociales': 'BaseCNSS9000.10 etbaseAMO9000.10 ; conditions confirmées, référenceCTRL-FICTIF909 ; motif Social FICTIF909 ; conserverIDsocial après calcul354.00 salarial/512.00 patronal.', 'part_base_imposable': '9000.10', 'part_base_frais': '9000.10', 'reference_controle': 'CTRL-FICTIF909', 'motif': 'Préparation FICTIVE909', 'confirmations': 'Conditions fiscales ; déductibilité intégrale des cotisations éligibles ; compréhension du résultat intermédiaire. Uniquement si justifiées dans le scénario.', 'attendus': 'Gain imposable300.01 ; brut imposable9300.11 ; basefrais9000.10 ; déductible60.00 ; non déductible294.00 ; revenu avantfrais9240.11. Frais déduits/RNI/IR/net non déterminés.', 'attention': 'Aucun montant du scénario n’est une règle réglementaire. Aucun prélèvement, bulletin, paiement ou écriture. Période des variables distincte d’une date réelle de paiement.'}
CAS=[('PA-BASE01', 'Ouvrir depuis une simulation sociale', 'Copie isolée et sources fictives complètes préparées selon le jeu ; technicien et deux acteurs indépendants.', 'IDsocial retourné, novembre2026, P909, brut9800.11, salarial354.00.', 'Depuis04 > Simulations sociales, consulter la simulation puis Préparer les bases fiscales. Ouvrir Nouvelle préparation fiscale et Charger le social.', 'Onglet Bases fiscales actif, IDsocial prérempli ; société, mois, base9000.10 et brut9800.11 visibles. Aucune saisie de revenu annuel de substitution.'), ('PA-BASE02', 'Calculer les cinq montants distincts', 'PA-BASE01, utilisateur habilité proposer.', 'Baseimposable9000.10, basefrais9000.10, référenceCTRL-FICTIF909, motif Préparation FICTIVE909 ; trois confirmations justifiées.', 'Saisir les seules fractions de base, sans rajouter800.01. Calculer et conserver. Déplier Variables et cotisations fiscales puis Qualifications conservées.', 'Brutimposable9300.11, basefrais9000.10, cotisations déductibles60.00, non déductibles294.00, revenu avant frais9240.11. Versions/IDs/empreintes conservés ; ni RNI définitif ni IR/net calculés.'), ('PA-BASE03', 'Garder une inconnue et un montant certain', 'PA-BASE02 ; créer une nouvelle préparation.', 'MêmeIDsocial et données, basefrais laissée vide ; référence/motif suffixe INCONNU, autres confirmations inchangées.', 'Calculer et lire les anomalies. Ne pas saisir0 pour obtenir un résultat complet. Réouvrir ensuite la première préparation.', 'Basefrais À compléter, brutimposable9300.11 reste connu ; montant intermédiaire ne devient pas un RNI définitif. Premier résultat reste9000.10 pour sa basefrais et conserve son empreinte.'), ('PA-BASE04', 'Bloquer une déduction intégrale non justifiée', 'Sources du jeu, nouvelles préparations distinctes.', 'Essai1 : ne pas confirmer déductibilité intégrale. Essai2 : baseimposable9800.11 alors que la base salariale n’est que9000.10. Autres champs commePA-BASE02.', 'Calculer séparément les deux essais. Lire les anomalies et l’état des totaux. Pour une véritable déduction partielle, ne pas confirmer intégrale pour contourner le contrôle.', 'Essai1 : cotisations déductibles et revenu intermédiaire À compléter. Essai2 : base fiscale incohérente, brut imposable non calculé. Aucun zéro ou montant négatif de secours.'), ('PA-BASE05', 'Détecter un changement des sources', 'PA-BASE02 conservé ; préparateur et décideur.', 'Nouvelle variable ponctuelle100.00 de GAIN_FICTIF909, même novembre, référenceEXTRA-FICTIF909 ; justificatifATTESTATION_FICTIVE=PIECE-FICTIVE909 ; motifs Proposition/Soumission/Contrôle FICTIF909.', 'Créer, soumettre puis faire approuver la variable indépendamment. Tenter une nouvelle préparation fiscale depuis l’ancienIDsocial. Lire l’alerte, puis refaire le brut et le social avant une nouvelle préparation.', 'Ancienne source refusée pour un nouveau calcul complet, SOURCE_SOCIALE_CHANGEE visible ; ancien snapshot fiscal inchangé. Le logiciel ne modifie pas rétroactivement le brut/social ni les écritures.'), ('PA-BASE06', 'Vérifier historique, accès et séparation du contrôle annuel', 'Deux sociétés fictives, administrateur d’habilitations ; journal/soldes relevés avant recette.', 'IDsdes préparations, motif révocation Fin accès fictif909.', 'Passer au Contrôle annuel IR puis revenir aux Bases fiscales. Changer de société. Révoquer rémunération et Actualiser. Vérifier ordinateur et mobile, puis comparer le journal avant/après.', 'Contrôle annuel reste séparé et ne reçoit aucun revenu intermédiaire automatiquement. Isolation, révocation et lecture verticale conservées. Aucun bulletin, paiement, retenue mensuelle ou écriture ; production non validée.')]


def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_BASES_FISCALES_PAIE_909.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_BASES_FISCALES_PAIE_909.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial909','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial909'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('Bases fiscales connectées909','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Bases reliées aux sources ; aucun RNI définitif, taux de frais ou montant de retenue mensuelle.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('BasesFiscales');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='Bases arithmétiques avant frais et autres déductions ; aucune retenue, déclaration ou paie définitive.';co='Société, droits, indépendance, dates, composition, sources et intégrité des versions.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_BASES_FISCALES_PAIE_909.pdf';SimpleDocTemplate(str(pdf),title='HisabPro bases fiscales909').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — SOCIAL909'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(BasesFiscales!J2:J7,"{statut}")'])
    s.append(['Cas',6]);s.append(['Progression','=IFERROR(B5/B8,0)']);s['B9'].number_format='0%';s.column_dimensions['A'].width=48;s.column_dimensions['B'].width=22
    ch=BarChart();ch.add_data(Reference(s,min_col=2,min_row=3,max_row=7),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=7));s.add_chart(ch,'A12')
    d=wb.create_sheet('Donnees');d.append(['Champ','Valeur fictive'])
    for k,v in JEU.items():d.append([k,v])
    d.column_dimensions['A'].width=46;d.column_dimensions['B'].width=95
    for row in d:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    x=D/'SUIVI_BASES_FISCALES_PAIE_909.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['BasesFiscales'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
