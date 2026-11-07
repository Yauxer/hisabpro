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
JEU={'societe': 'RECETTE PAIE921 — société entièrement fictive, copie isolée uniquement', 'menu': '05 · Fiscalité salariale → Bases fiscales → Préparer le RNI mensuel de P909', 'installation': 'Code921 ; migrations123 puis124 sur copie après120 ; prérequis Personnel, brut et social déjà installés. Ne jamais lancer cette recette sur les données habituelles.', 'sources': 'Créer une nouvelle fiche P909 et des sources approuvées dans la société vierge : contrat CDI dès2026-01-01, rémunération mensuelle9000.10, tout novembre2026. Gain mensuel800.01 approuvé indépendamment. Préparer brut, social puis bases fiscales via les guides893,899,909.', 'rubrique_fictive': 'GAIN_FICTIF909, Gain, Mensuelle (et non Ponctuelle), Montant exact, début2026-01-01, fin et compte vides, justificatif ATTESTATION_FICTIVE. Créer cette périodicité avant approbation ; ne jamais modifier une rubrique historique approuvée.', 'regles_rubrique': 'IR : plafond500.00/par opération ; CNSS : plafond300.00/par opération ; AMO : soumis. Conditions Hypothèse FICTIVE909 sans portée légale. IR qualifié seulement dans le jeu de test isolé ; frais Exclue / qualifiée dans ce même jeu.', 'branches_fictives': 'Régime REGIME_FISC909. B1_FICTIF909 : CNSS, salarial1%, patronal2%, plafond6000.00/mensuel, composantB1, déductibilité intégrale fictive. B2_FICTIF909 : AMO, salarial3%, patronal4%, sans plafond, composantB2, non déductible fictivement. Organisme Organisme fictif, début2026-01-01, conditions Hypothèse FICTIVE909 sans portée légale.', 'qualification_test': 'Pour la recette isolée exclusivement, le technicien peut constituer les états synthétiques qualifiés comme les fixtures test_paie909_bases_isole.py : texte/article/référence FICTIF909, URL https://www.finances.gov.ma/, SHA a répété64fois, consultation2026-01-01 ; approbateur distinct habilité valider_regles_paie. Ces références fictives ne justifient aucune véritable règle et sont interdites pour une paie réelle.', 'sources_reelles': 'En exploitation, utiliser uniquement des preuves véritables de l’éligibilité du salarié et de chaque règle, contrôlées par le décideur. Ne pas copier les taux ou preuves fictifs du cahier.', 'declarations_sociales': 'BaseCNSS9000.10 etbaseAMO9000.10 ; conditions confirmées, référenceCTRL-FICTIF909 ; motif Social FICTIF909 ; conserverIDsocial après calcul354.00 salarial/512.00 patronal.', 'part_base_imposable': '9000.10', 'part_base_frais': '9000.10', 'reference_controle': 'CTRL-FICTIF909', 'motif': 'Préparation FICTIVE909', 'confirmations': 'Conditions fiscales ; déductibilité intégrale des cotisations éligibles ; compréhension du résultat intermédiaire. Uniquement si justifiées dans le scénario.', 'attendus': 'Gain imposable300.01 ; brut imposable9300.11 ; basefrais9000.10 ; déductible60.00 ; non déductible294.00 ; revenu avantfrais9240.11. Frais déduits/RNI/IR/net non déterminés.', 'attention': 'Les règles sociales et qualifications FISC909 sont fictives et ne sont pas les taux CNSS/AMO applicables. Annualiser par12 ici est une transformation mathématique, pas une estimation des revenus futurs ni une règle de retenue liquidée. Ne pas utiliser497.0240 pour payer ou déclarer.', 'frais_declares': '2250.03 ; référence FRAIS-DECLARES-FICTIFS921. Hypothèse arithmétique déclarée, pas un forfait mensuel réglementaire calculé par HisabPro.', 'autres_deductions': '0.00 explicite ; référence AUCUNE-AUTRE-FICTIVE921. Ne pas saisir zéro pour une donnée inconnue.', 'cadre_mensuel': 'Cocher déductions confirmées et mois complet du cas général ; référence MOIS-FICTIF921. Ces confirmations concernent seulement le scénario fictif.', 'famille': '2 personnes ; confirmer éligibilité uniquement dans ce scénario ; référence FAMILLE-FICTIVE921. Nombre civil seul insuffisant.', 'versement': 'Laisser date et référence de versement vides : date inconnue, aucune date déduite du mois ou de la date d’effet.', 'motif_mensuel': 'Contrôle mensuel entièrement FICTIF921 ; cocher la compréhension du mode préparatoire pédagogique.', 'attendu_mensuel': '9300.11 - 60.00 - 2250.03 - 0.00 = RNI6990.08. Équivalence mathématique annuelle83880.96 ; IR annuel mathématique7164.288 /12 =597.0240. Réduction mathématique2×600/12=100.0000 ; après réduction497.0240, fraction exacte62128/125.', 'indisponibles': 'Retenue à opérer, montant à déclarer, versement et net à payer : non déterminés. Aucun bulletin ni OD de paie. Statut NON_VALIDE_JURIDIQUEMENT.', 'periodes_exactes': [{'periode': '2026-11-01', 'date_effet_variable': '2026-11-15', 'reference_variable': 'SOURCE-FICTIVE921'}]}
CAS=[('PA-M921-01', 'Calculer depuis les sources approuvées', 'Société vierge et prérequis exacts du jeu ; acteurs distincts pour les approbations.', 'Toutes les données du jeu, notamment rubrique mensuelle avant approbation, FP2250.03, autres0.00, famille2, références et confirmations.', 'Préparer brut9800.11, social puis bases fiscales. Depuis le résultat de P909 ouvrir Préparer le RNI mensuel. Vérifier identité et novembre2026, saisir le jeu, conserver le contrôle. Déplier bases, variables et fractions ; revenir à la préparation source.', 'RNI6990.08 ; équivalence avant597.0240, réduction100.0000 et après497.0240 (62128/125). Les déductions et sources sont lisibles. Retenue/net/versement restent indisponibles ; aucune déclaration autorisée.'), ('PA-M921-02', 'Conserver les inconnues', 'PA-M921-01, nouvelle simulation avec clé automatiquement renouvelée.', 'Premier essai : famille vide et non confirmée, autres données identiques. Second essai : frais et référence des frais vides.', 'Conserver les deux contrôles successifs et consulter les anomalies. Ne pas remplacer les champs vides par zéro.', 'Famille inconnue : RNI6990.08 et avant597.0240 connus, après réduction indéterminé. Frais inconnus : RNI et équivalence indéterminés. Ancien contrôle inchangé.'), ('PA-M921-03', 'Isoler primes, rappels et versements hors année', 'Nouvelle source approuvée dans une période distincte ; suivre le guide919 pour documenter les dates.', 'Référence du gain2025-01-01au2025-12-31 et preuve RAPPEL-FICTIF921 ; ou rubrique Ponctuelle ; autre cas : versement source2025-12-05 et preuve VERSEMENT-FICTIF921, date globale laissée vide.', 'Créer ces nouvelles sources avant le brut/social/bases. Ouvrir le contrôle mensuel et saisir les déclarations de PA-M921-01, sans retirer le rattachement ni changer les confirmations pour contourner le contrôle.', 'RATTACHEMENT_SPECIFIQUE ou VERSEMENT_SOURCE_AUTRE_ANNEE ; RNI et équivalence indisponibles même si mois complet confirmé. Aucune assimilation au mois courant ni recalcul automatique des périodes2025.'), ('PA-M921-04', 'Refuser déductions excessives et données invalides', 'Nouvelle simulation sur la source initiale.', 'Essai1 : frais9000.11 > base de frais9000.10. Essai2 : frais2250.03 et autres8000.00. Références fictives explicites pour chaque déclaration.', 'Saisir chaque combinaison et lire les anomalies. Essayer aussi montant négatif, non numérique ou trois décimales ; corriger dans le formulaire.', 'Déductions excessives : RNI indéterminé, aucune réduction arbitraire à zéro. Formats invalides refusés sans conserver un calcul trompeur. Pas de modification comptable.'), ('PA-M921-05', 'Détecter les sources devenues anciennes', 'PA-M921-01 conservé ; nouvelle rubrique distincte, ne pas réécrire les anciennes sources.', 'EXTRA_MENSUEL_FICTIF921, Gain, Ponctuelle, Montant exact,100.00 pour novembre2026 ; justificatif et source FICTIF921, approbation indépendante.', 'Approuver cette nouvelle variable. Depuis l’ancienne préparation fiscale tenter un nouveau contrôle ; relire le contrôle déjà conservé. Repréparer les bases pour inclure la nouvelle source avant tout autre calcul.', 'Nouvelle création depuis sources périmées refusée409 ; ancien contrôle et empreinte conservés lisibles. Rejeu identique par clé idempotente restitué sans recalcul (contrôle technique API).'), ('PA-M921-06', 'Vérifier accès, petit écran et restauration', 'Deux sociétés fictives, rôle Personnel seul habilité identité/rémunération ; responsable de sauvegarde sur copie.', 'Contrôle de PA-M921-01 ; largeurs1440px et390px. Accès successifs utilisateur habilité, autre société et droit révoqué.', 'Consulter le contrôle et ses sources ; changer de société ; révoquer les droits puis Actualiser. Sauvegarder/restaurer uniquement l’environnement isolé puis relire sous rôle limité.', 'Aucune fuite inter-société ; accès refusé et état effacé après révocation. Formulaire et résultat lisibles sans débordement horizontal.100tables, source, montants, fractions, empreintes et droits restaurés ; journal comptable inchangé.')]

def generer():
    D.mkdir(exist_ok=True)
    (D/'JEU_RNI_MENSUEL_PAIE_921.json').write_text(json.dumps(JEU,ensure_ascii=False,indent=2),encoding='utf8')
    (D/'CAS_RNI_MENSUEL_PAIE_921.json').write_text(json.dumps(CAS,ensure_ascii=False,indent=2),encoding='utf8')
    styles=getSampleStyleSheet()
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('Arial921','C:/Windows/Fonts/arial.ttf'))
        for st in styles.byName.values():st.fontName='Arial921'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda t,style='BodyText':Paragraph(escape(str(t)),styles[style])
    story=[p('CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Title'),p('RNI mensuel préparatoire921','Heading1'),p('Complément de6 cas. Tous les résultats humains sont Non testé. Contrôle mathématique préparatoire ; aucun prélèvement, déclaration, net ou paiement autorisé.'),p('Données exactes à saisir','Heading1')]
    for k,v in JEU.items():
        if k=='periodes_exactes':
            story.append(p('Période du jeu de recette','Heading2'))
            for m in v:story.append(p(m['periode']+' — Date variable '+m['date_effet_variable']+' — Référence '+m['reference_variable']))
        else:story.append(p(k+' : '+str(v)))
    story.append(PageBreak());wb=Workbook();s=wb.active;s.title='Synthese';w=wb.create_sheet('RNIMensuel');w.append(['ID','Objectif','Prérequis','Données exactes','Actions','Attendu','Écritures','Fiscalité','Contrôles','Statut','Résultat réel','Anomalies','Observations','Preuve/capture'])
    for ident,obj,pre,data,actions,att in CAS:
        ec='Aucune écriture ni paiement ; comparer le journal avant/après.';fi='RNI sur déductions déclarées et équivalence mathématique annuelle/12 ; retenue liquidée et net indisponibles.';co='Société, droits, exactitude des déductions, inconnues, dates de référence, fraîcheur et intégrité des sources.'
        story.append(p(ident+' — '+obj,'Heading2'))
        for label,t in [('Prérequis',pre),('Données',data),('Actions',actions),('Attendu',att),('Écritures',ec),('Fiscalité',fi),('Contrôles',co),('Preuve','Captures fiche/version/décision ou refus ; ID branche et version, société et acteurs.'),('Statut','Non testé ; renseigner le classeur et conserver les preuves.')]:story.append(p(label+' : '+t))
        story.append(Spacer(1,12));w.append([ident,obj,pre,data,actions,att,ec,fi,co,'Non testé','','','','Captures/ID/version à conserver'])
    pdf=D/'RECETTE_RNI_MENSUEL_PAIE_921.pdf';SimpleDocTemplate(str(pdf),title='HisabPro RNI mensuel préparatoire921').build(story)
    w.freeze_panes='C2';w.auto_filter.ref=w.dimensions
    for col in w.columns:w.column_dimensions[col[0].column_letter].width=38
    for row in w:
        for ce in row:ce.alignment=Alignment(wrap_text=True,vertical='top')
    for ce in w[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
    from math import ceil
    for i in range(2,8):w.row_dimensions[i].height=min(409,max(170,(max(ceil(len(str(c.value or ''))/30) for c in w[i])+2)*15))
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');w.add_data_validation(dv);dv.add('J2:J7')
    for row in [['HISABPRO — RNI_MENSUEL921'],['Production','Non validée'],['Statut','Nombre']]:s.append(row)
    for statut in ['Non testé','Réussi','Échoué','Bloqué']:s.append([statut,f'=COUNTIF(RNIMensuel!J2:J7,"{statut}")'])
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
    x=D/'SUIVI_RNI_MENSUEL_PAIE_921.xlsx';wb.save(x)
    texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert all(c[0] in texte for c in CAS) and '\u25a0' not in texte
    assert all(load_workbook(x)['RNIMensuel'].cell(i,10).value=='Non testé' for i in range(2,8))
    print(json.dumps({'cas':6,'pages':len(PdfReader(pdf).pages),'feuilles':wb.sheetnames,'humain':'Tous Non testé'},ensure_ascii=False))


if __name__=='__main__':generer()
