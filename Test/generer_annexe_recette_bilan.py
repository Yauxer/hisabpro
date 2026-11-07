"""Annexe de recette bilan : documents seuls, aucun accès à la base."""
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

DEST = Path(__file__).resolve().parents[1] / 'docs/recette'
NOM = 'ANNEXE_RECETTE_BILAN_DETAILLE'
TITRE = 'CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
INTRO = ('Annexe bilan détaillé : quatre cas Non testé. Aucun résultat utilisateur prévalidé. '
         'Les preuves automatisées du lot 256 sont distinctes de cette recette à effectuer. '
         'Utiliser uniquement des sociétés fictives isolées ; aucune réparation de dossier réel. '
         'La présentation ne constitue pas une certification comptable ou fiscale.')
COMPTES = [('2311', 1000), ('2321', 2000), ('2331', 3000), ('2340', 4000),
           ('2351', 5000), ('2380', 6000), ('3111', 7000), ('3421', 8000), ('5141', 9000)]
JEU = {
    'Société A': 'BILAN DETAIL RECETTE A ; dossier fictif vierge, début du premier exercice 2026 ; administrateur ; exercice ouvert du 01/01/2026 au 31/12/2026.',
    'Client': 'CLIENT BILAN RECETTE ; type Client ; rattacher explicitement ce tiers à la ligne 3421.',
    'Reprise N': 'Écriture OD au 01/01/2026, référence BILAN-REC-N, libellé Reprise fictive pour recette de présentation. Débits : ' + '; '.join(f'{c} = {v},00 MAD' for c, v in COMPTES) + '. Crédits : 28321 = 300,00 ; 1111 = 44 700,00 MAD. Total débit = crédit = 45 000,00 MAD. Aucun compte 6/7.',
    'Nature des données': 'Reprise fictive de soldes de bilan, pas une acquisition ou une dotation fiscale. Aucune TVA ou déclaration n’est générée. Ne pas créer aussi des factures, immobilisations ou stocks correspondant à ces mêmes montants : cela doublerait les écritures.',
    'Société B': 'BILAN DETAIL RECETTE B ; société fictive séparée, début du premier exercice 2025 ; exercices 2025 et 2026 ouverts. Client CLIENT BILAN RECETTE B.',
    'Comparatif B N-1': 'Écriture OD au 01/01/2025, référence BILAN-B-N1 : débit 5141 = 75,00 ; crédit 1111 = 75,00 MAD. Valider. Ne pas clôturer ni générer d’à-nouveaux automatiquement pendant cette recette isolée de présentation.',
    'Ouverture B N': 'Écriture OD au 01/01/2026, référence BILAN-B-OUVERTURE : débit 5141 = 75,00 ; crédit 1111 = 75,00 MAD. Valider. Puis seconde écriture OD BILAN-B-N avec les débits de Reprise N sauf 5141 = 8 925,00 ; crédits 28321 = 300,00 et 1111 = 44 625,00 MAD. Débit = crédit = 44 925,00 ; total annuel identique à A. Rattacher le client B à 3421. Aucun doublon d’ouverture.',
    'Archive ancienne': 'Dossier fictif précédemment finalisé avant livraison du détail (lot 256), issu du cahier annuel. Relever société, exercice, version, empreinte et ancien export. Si aucun dossier de recette ne satisfait ce prérequis, classer BILAN-DET-04 Bloqué ; ne pas modifier ni fabriquer un snapshot.',
}


def oracle():
    brut = sum((Decimal(v) for _, v in COMPTES), Decimal(0))
    amort = Decimal(300)
    return {'brut': str(brut), 'amort': str(amort), 'net': str(brut-amort),
            'immobilisations_brut': '21000', 'immobilisations_net': '20700', 'n1_net': '75'}


def cas():
    def item(i, domaine, objectif, prerequis, donnees, actions, attendu, preuves):
        return dict(id=f'BILAN-DET-{i:02}', module=domaine, objectif=objectif, prerequis=prerequis,
            donnees=donnees, actions=actions, attendu=attendu,
            ecritures=('Créer et valider uniquement les écritures fictives précisées dans ce cas. '
                      'La consultation et les exports ne créent aucune écriture supplémentaire.' if i in (1, 2)
                      else 'Aucune nouvelle écriture : consultation et exports uniquement.'),
            fiscal='Aucun calcul fiscal nouveau attendu ; cette reprise fictive ne justifie aucune TVA, amortissement fiscal ou liquidation.',
            controles='Vérifier société et exercice actifs ; comparer balance validée et total bilan ; les sous-postes sont pour mémoire, sans double addition.',
            statut='Non testé', resultat_reel='', anomalies='', preuves=preuves, observations='')
    return [
        item(1, 'Bilan', 'Bilan détaillé sans comparatif',
             'Créer la société A et le client du Jeu de données ; aucun autre mouvement. Vérifier que les comptes indiqués sont actifs.',
             JEU['Reprise N'],
             'Sélectionner A / 2026. Journal → Nouvelle écriture : saisir date, journal OD, référence, libellé et les onze lignes exactes ; sélectionner le client sur 3421. Contrôler débit/crédit 45 000,00 puis enregistrer et Valider. Ouvrir Comptabilité → Liasse fiscale → T1 · Bilan. Lire les six immobilisations sous la rubrique Immobilisations corporelles, les stocks, clients et banque.',
             'Brut immobilisé 21 000,00 ; amortissements 300,00 ; net 20 700,00. Brut général 45 000,00 ; net actif = passif 44 700,00. Sous-postes bruts 1 000/2 000/3 000/4 000/5 000/6 000 ; amortissement et net des sous-postes « — », sans ventilation arbitraire. N-1 absent, jamais transformé en zéro.',
             'Capture de l’écriture validée, balance et T1 incluant sous-postes, notice, totaux et absence de N-1.'),
        item(2, 'Comparatif', 'Bilan détaillé avec N-1 disponible',
             'Utiliser exclusivement la société B distincte, exercices 2025 et 2026 ouverts ; aucun autre mouvement, aucune clôture ou à-nouveaux automatique.',
             JEU['Comparatif B N-1'] + ' ' + JEU['Ouverture B N'],
             'En B/2025, saisir puis valider BILAN-B-N1. Passer à B/2026, saisir puis valider BILAN-B-OUVERTURE et BILAN-B-N selon le Jeu. Vérifier les montants et le tiers. Ouvrir Liasse fiscale → T1 · Bilan. Comparer la colonne N-1 avec le bilan B/2025.',
             'Total brut N 45 000,00 ; amortissements 300,00 ; net N 44 700,00. N-1 : banque et capital 75,00 ; total net actif/passif 75,00. Les autres rubriques N-1 connues sont nulles en montant, pas absentes. Aucun amortissement ou net de détail N n’est inventé.',
             'Écritures validées des deux exercices ; T1 B/2025 et B/2026 montrant 75,00 en comparatif.'),
        item(3, 'Exports', 'Retrouver le détail dans Excel et PDF',
             'BILAN-DET-01 effectué sur A/2026 ; aucune autre mutation après la capture du bilan.',
             'A/2026 ; mêmes soldes et montants que BILAN-DET-01.',
             'Dans la liasse A/2026, cliquer Excel et ouvrir T1 Bilan Actif puis T1 Bilan Passif. Cliquer PDF et l’ouvrir. Rechercher Constructions, Matériel de transport et TOTAL GÉNÉRAL. Comparer les lignes, chiffres et N-1 avec l’écran ; comparer à nouveau le journal.',
             'Les six sous-postes figurent dans les deux exports. Construction brute 2 000,00, amortissement/net détaillés absents. Total brut 45 000,00, amortissements 300,00 et net 44 700,00 identiques ; Excel garde de vraies cellules numériques et des cellules vides pour montants indéterminés. Journal inchangé.',
             'Fichiers PDF/XLSX téléchargés, captures des six sous-postes et totaux ; journal avant/après.'),
        item(4, 'Archives', 'Préserver une archive de l’ancien format',
             JEU['Archive ancienne'], 'Identifiants et montants effectivement relevés dans cette archive fictive ; aucune valeur arbitraire imposée.',
             'Sélectionner la société/exercice du prérequis et ouvrir Liasse fiscale. Relever version et empreinte de l’archive. Ouvrir T1 · Bilan, exporter Excel et PDF puis recharger. Comparer avec l’ancien snapshot/export disponible. Sans prérequis, inscrire Bloqué et expliquer quelle archive manque.',
             'Version, empreinte et montants figés restent identiques. Les anciennes rubriques agrégées restent lisibles ; aucun détail n’est reconstitué depuis les écritures actuelles. La présence de détails ne doit pas être exigée sur cette archive ancienne.',
             'Référence du dossier fictif, capture version/empreinte avant/après, anciens et nouveaux exports comparés.'),
    ]


def generer(destination=DEST):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    items = cas(); colonnes = list(items[0])
    wb = Workbook(); synth = wb.active; synth.title = 'Synthèse'
    synth.append([TITRE]); synth.append([INTRO]); synth.append(['Domaine', 'Cas', 'Réussis', 'Échoués', 'Bloqués', 'Non testé'])
    for c in items:
        ws = wb.create_sheet(c['module']); ws.append(colonnes); ws.append([c[k] for k in colonnes])
        ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions
        dv = DataValidation(type='list', formula1='"Non testé,Réussi,Échoué,Bloqué"')
        ws.add_data_validation(dv); dv.add('K2')
        synth.append([c['module'], 1, *[f'=COUNTIF(\'{c["module"]}\'!K2,"{s}")' for s in ('Réussi', 'Échoué', 'Bloqué', 'Non testé')]])
    synth.append(['TOTAL', '=SUM(B4:B7)', *[f'=SUM({l}4:{l}7)' for l in 'CDEF']])
    jeu = wb.create_sheet('Jeu de données'); jeu.append(['Champ', 'Valeur fictive exacte'])
    for k, v in JEU.items(): jeu.append([k, v])
    for k, v in oracle().items(): jeu.append(['Oracle ' + k, v])
    for ws in wb:
        for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='183D35')
        for row in ws:
            for c in row: c.alignment = Alignment(vertical='top', wrap_text=True)
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 34
    wb.save(destination / (NOM + '.xlsx'))
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(TITRE), styles['Title']), Paragraph('Annexe bilan détaillé', styles['Heading1']), Paragraph(escape(INTRO), styles['BodyText'])]
    for k, v in JEU.items(): story.extend([Paragraph(escape(k), styles['Heading3']), Paragraph(escape(v), styles['BodyText'])])
    for item in items:
        story.extend([PageBreak(), Paragraph(item['id'] + ' — ' + escape(item['objectif']), styles['Heading1'])])
        for k, v in item.items():
            if k not in ('id', 'objectif'): story.extend([Paragraph(escape(k.replace('_', ' ')), styles['Heading3']), Paragraph(escape(str(v) or 'À renseigner pendant la recette.'), styles['BodyText'])])
    SimpleDocTemplate(str(destination / (NOM + '.pdf')), pagesize=A4, title=TITRE + ' — Annexe bilan détaillé').build(story)
    md = ['# ' + TITRE, '', '## Annexe bilan détaillé', '', INTRO, '', '## Jeu de données', '']
    md.extend(f'- **{k}** : {v}' for k, v in JEU.items())
    for c in items:
        md.extend(['', '## ' + c['id'] + ' — ' + c['objectif'], ''])
        md.extend(f'**{k.replace("_", " ")}** : {v or "À renseigner pendant la recette."}\n' for k, v in c.items() if k not in ('id', 'objectif'))
    (destination / (NOM + '.md')).write_text('\n'.join(md) + '\n', encoding='utf-8')
    return items


if __name__ == '__main__':
    generer()
    print('Annexe bilan détaillé : quatre cas Non testé, PDF/XLSX/MD générés.')
