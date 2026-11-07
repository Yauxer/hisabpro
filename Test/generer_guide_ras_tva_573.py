"""Guide d'utilisation PDF/Markdown, sans connexion ni dépendance à l'application."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape
import argparse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
NOM = 'UTILISATION_RAS_TVA_GUIDEE_20261018'
INTRO = (
    'Cette fonction rapproche une RAS TVA déclarée d’un règlement réel et prépare une OD. '
    'Elle conserve les faits renseignés et la référence des pièces. Elle ne valide pas la '
    'qualification fiscale, ne choisit pas le compte et ne génère aucun reversement ou dépôt. '
    'La déclaration TVA automatique des périodes et reports concernés reste indisponible '
    'jusqu’à qualification de l’imputation et du reversement des retenues.'
)
SECTIONS = [
    ('Avant de commencer', [
        'Utilisez la bonne société et le bon exercice. La facture doit être définitive et comptabilisée, avec son tiers réel. Le règlement doit déjà représenter le montant de trésorerie effectivement payé ou reçu.',
        'Le premier périmètre couvre 2026, article 117-V-b / liste B : les parties, la prestation, les exclusions et l’attestation doivent être vérifiées sur pièces. Les services ne sont jamais classés automatiquement.',
        'Un administrateur doit avoir appliqué la migration 099 après la chaîne existante jusqu’à 098, notamment 083. Cet écran n’exécute aucune migration. L’installation cible doit suivre votre procédure de sauvegarde et de mise à jour.',
        'Les règlements immédiats comptabilisés par virement ou espèces sont couverts. RAS HT/historique, avoirs/acomptes affectés et autres paiements actifs sans ventilation RAS TVA tracée restent hors de ce raccordement.',
    ]),
    ('Préparer la capture depuis l’interface', [
        'Ouvrez Cycle commercial → Vente ou Achat → Règlements. Sur le règlement concerné, utilisez l’icône « Consulter ou déclarer la RAS ». Choisissez « RAS TVA guidée ».',
        'Dépliez « Assistant RAS TVA · 2026 ». La date vient du règlement. Renseignez les situations réelles des parties, la listeB, les exclusions, l’attestation et la quote-part TTC avant retenue avec sa TVA correspondante. Cliquez sur « Simuler la RAS TVA ».',
        'Renseignez le justificatif de ventilation, une référence RAS TVA et le compte destination explicitement justifié par le comptable. Aucune valeur de compte n’est proposée comme obligation fiscale.',
        'Cliquez sur « Vérifier le règlement et afficher l’aperçu ». Le net doit égaler le règlement et les cumuls doivent rester dans le TTC et la TVA de la facture. Tout changement de saisie impose un nouvel aperçu.',
        'Contrôlez les pièces et le rapprochement, cochez la confirmation puis cliquez sur « Préparer la capture RAS TVA et son OD ». Attendez la fin de l’enregistrement : la facture et le règlement se rafraîchissent automatiquement.',
    ]),
    ('Contrôler, valider et consulter', [
        'Rouvrez l’icône RAS du règlement : le dossier conserve les montants, la ventilation et les références déclarées. Le rôle lecture peut consulter ce dossier ; il ne peut pas préparer de capture.',
        'Dans le Journal, contrôlez l’OD et son vrai tiers, puis validez-la avec le rôle autorisé. L’écriture de trésorerie existante n’est pas créée une seconde fois. La capture et ses lignes restent protégées.',
        'Après paiement complet, le lettrage est une action distincte : validez les pièces nécessaires, sélectionnez le compte et le tiers réels, puis rapprochez les débits et crédits équilibrés.',
        'Pour corriger, délettrez si nécessaire puis utilisez l’annulation du règlement. Le dossier et les OD originales sont conservés, avec leur contrepassation. Ne remplacez pas les faits d’une ancienne capture pour la requalifier.',
    ]),
    ('Comprendre les refus', [
        '« Migration 099 » : l’administrateur doit qualifier l’installation ; aucun clic ne crée les tables.',
        'Net différent du règlement : vérifiez la trésorerie réellement versée et la quote-part avant retenue. Un règlement déjà comptabilisé se corrige par annulation, pas par changement silencieux de son montant.',
        'Autre paiement non ventilé, avoir, acompte ou RAS HT : ce cas n’est pas encore pris en charge. Conservez les justificatifs et faites qualifier le traitement ; ne choisissez pas une autre situation pour contourner le contrôle.',
        'Aperçu périmé ou période fermée : refaites l’aperçu ou faites examiner la période par le rôle autorisé. Un exercice définitivement clôturé reste verrouillé.',
        'Déclaration TVA à compléter : le logiciel ne présente ni ancien montant ni zéro comme un solde calculé. Les règles et justificatifs d’imputation/reversement restent à qualifier avec le comptable.',
    ]),
]


def oracle():
    lignes = []
    for quote, tva in [('400.00', '66.67'), ('800.00', '133.33')]:
        t, v = Decimal(quote), Decimal(tva)
        ras = (v * Decimal('.75')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        lignes.append((t, v, ras, t - ras))
    assert sum(x[0] for x in lignes) == Decimal('1200.00')
    assert sum(x[1] for x in lignes) == Decimal('200.00')
    assert sum(x[2] for x in lignes) == Decimal('150.00')
    assert sum(x[3] for x in lignes) == Decimal('1050.00')
    return lignes


def generer(destination=None):
    dest = Path(destination) if destination else ROOT / 'docs/guides'
    dest.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 8
    styles['Heading2'].textColor = colors.HexColor('#183D35')
    styles.add(ParagraphStyle(name='Petit573', parent=styles['BodyText'], fontSize=9, leading=12))
    p = lambda texte: Paragraph(escape(texte), styles['BodyText'])
    story = [Paragraph('HisabPro', styles['Title']), Paragraph('Utiliser la RAS TVA guidée', styles['Heading1']), p(INTRO)]
    for titre, textes in SECTIONS[:2]:
        story.append(Paragraph(titre, styles['Heading2']))
        for n, texte in enumerate(textes, 1):
            story.append(p(f'{n}. {texte}'))
    story += [PageBreak(), Paragraph('Exemple chiffré entièrement fictif', styles['Heading1'])]
    story.append(p('Exclusivement dans une société de test isolée. Facture de service : HT 1000,00 MAD, TVA 200,00 MAD, TTC 1200,00 MAD. Date 18/10/2026. Attestation présentée, datée du 01/09/2026. Les conditions 117-V-b et l’absence d’exclusion, y compris le cumul mensuel, sont supposées justifiées par des pièces fictives : elles ne se déduisent pas de ces montants.'))
    entete = ['Paiement', 'Quote-part TTC', 'TVA', 'RAS 75 %', 'Trésorerie']
    lignes = [[str(i), *[format(v, '.2f').replace('.', ',') for v in valeurs]] for i, valeurs in enumerate(oracle(), 1)]
    tableau = Table([entete, *lignes, ['Total', '1200,00', '200,00', '150,00', '1050,00']], colWidths=[60, 116, 85, 95, 110])
    tableau.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#183D35')), ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CAD5D0')), ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),9), ('TOPPADDING',(0,0),(-1,-1),8), ('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    story += [tableau, Spacer(1,12), p('Le premier règlement réel est 350,00 MAD, pas 400,00 MAD. Après sa capture de 50,00 MAD, le reste dû est 800,00 MAD. Le second règlement de 700,00 MAD et sa capture de 100,00 MAD soldent la facture. Le compte destination reste à choisir et justifier ; ces chiffres n’en imposent aucun.')]
    for titre, textes in SECTIONS[2:]:
        story.append(Paragraph(titre, styles['Heading2']))
        story.extend(p(texte) for texte in textes)
    image = dest/'images/RAS_TVA_573_FICTIF.png'
    if image.exists():
        story += [PageBreak(), Paragraph('Exemple de dossier conservé', styles['Heading1']), p('Capture réelle d’un test automatisé sur société fictive, écran mobile. Aucune donnée utilisateur réelle.'), Image(str(image), width=195, height=500)]
    story.append(p('Ce guide décrit un usage. Il ne valide ni la recette utilisateur, ni une déclaration déposée, ni une conformité officielle.'))
    def pied(canvas, doc):
        canvas.saveState(); canvas.setFont('Helvetica',8)
        canvas.drawString(42,25,'HisabPro — Guide RAS TVA573 — Exemple fictif')
        canvas.drawRightString(A4[0]-42,25,str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(str(dest/(NOM+'.pdf')), pagesize=A4, leftMargin=42, rightMargin=42,
        topMargin=35, bottomMargin=40, title='HisabPro — Utiliser la RAS TVA guidée').build(story,onFirstPage=pied,onLaterPages=pied)
    md = ['# HisabPro — Utiliser la RAS TVA guidée', '', INTRO, '']
    for titre, textes in SECTIONS:
        md += ['## '+titre, ''] + [f'{i}. {t}' for i,t in enumerate(textes,1)] + ['']
    md += ['## Exemple fictif', '', 'Facture HT1000,00 / TVA200,00 / TTC 1200,00 MAD. Toutes les qualifications et exclusions doivent être justifiées sur pièces.', '', '|Quote-partTTC|TVA|RAS 75 %|Trésorerie|', '|---|---|---|---|']
    md += ['|'+'|'.join(format(v,'.2f') for v in row)+'|' for row in oracle()]
    md += ['', 'Aucun compte destination imposé. Ce guide ne vaut ni recette utilisateur ni validation réglementaire.', '']
    (dest/(NOM+'.md')).write_text('\n'.join(md),encoding='utf-8')
    return dest/(NOM+'.pdf')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path)
    print(generer(parser.parse_args().destination))
