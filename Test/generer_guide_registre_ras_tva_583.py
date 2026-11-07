"""Guide PDF du registre, depuis le Markdown livré, sans application ni base."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
NOM = 'UTILISATION_REGISTRE_RAS_TVA_20261018'


def generer():
    dossier = ROOT / 'docs/guides'
    source = (dossier / (NOM + '.md')).read_text(encoding='utf-8')
    styles = getSampleStyleSheet()
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 9
    styles['Heading1'].textColor = colors.HexColor('#183D35')
    fonts = Path('C:/Windows/Fonts')
    if (fonts / 'arial.ttf').is_file():
        if 'GuideRegistre583' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('GuideRegistre583', str(fonts / 'arial.ttf')))
        styles['BodyText'].fontName = styles['Heading1'].fontName = 'GuideRegistre583'
    lignes = source.splitlines()
    titre = lignes.pop(0).lstrip('# ')
    story = [Paragraph('HisabPro', styles['Title']), Paragraph(escape(titre), styles['Heading1'])]
    # Conserver les six étapes et les paragraphes du Markdown comme source unique.
    blocs = re.split(r'\n\s*\n|\n(?=\d+\. )', '\n'.join(lignes).strip())
    for bloc in blocs:
        texte = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', bloc.replace('**', ''))
        story.append(Paragraph(escape(' '.join(texte.split())), styles['BodyText']))
    image = dossier / 'images/REGISTRE_RAS_TVA_583_FICTIF.png'
    if image.is_file():
        story += [PageBreak(), Paragraph('Exemple entièrement fictif', styles['Heading1']),
            Paragraph('Capture réelle d’un test Edge sur société de laboratoire. Les montants achats et ventes sont séparés ; une capture annulée reste visible. Aucune donnée comptable utilisateur.', styles['BodyText']),
            Image(str(image), width=195, height=500)]
    def pied(canvas, doc):
        canvas.saveState(); canvas.setFont('Helvetica', 8)
        canvas.drawString(42, 24, 'HisabPro · Guide du registre interne RAS TVA · 18/10/2026')
        canvas.drawRightString(A4[0]-42, 24, str(doc.page)); canvas.restoreState()
    cible = dossier / (NOM + '.pdf')
    SimpleDocTemplate(str(cible), pagesize=A4, leftMargin=42, rightMargin=42,
        topMargin=35, bottomMargin=40, title='HisabPro — Consulter le registre des retenues TVA').build(
            story, onFirstPage=pied, onLaterPages=pied)
    return cible


if __name__ == '__main__':
    print(generer())
