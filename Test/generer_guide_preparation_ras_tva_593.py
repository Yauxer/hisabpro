"""Guide PDF depuis la source Markdown livrée, sans accès base."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph

ROOT=Path(__file__).resolve().parents[1]
NOM='UTILISATION_PREPARATION_RAS_TVA_20261018'


def generer():
    dossier=ROOT/'docs/guides';source=(dossier/(NOM+'.md')).read_text(encoding='utf-8')
    styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=9
    styles['Heading1'].textColor=colors.HexColor('#183D35')
    font=Path('C:/Windows/Fonts/arial.ttf')
    if font.is_file():
        if 'GuidePreparation593' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('GuidePreparation593',str(font)))
        styles['BodyText'].fontName=styles['Heading1'].fontName='GuidePreparation593'
    lignes=source.splitlines();titre=lignes.pop(0).lstrip('# ')
    story=[Paragraph('HisabPro',styles['Title']),Paragraph(escape(titre),styles['Heading1'])]
    for bloc in re.split(r'\n\s*\n','\n'.join(lignes).strip()):
        story.append(Paragraph(escape(' '.join(bloc.split())),styles['BodyText']))
    def pied(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8)
        canvas.drawString(42,24,'HisabPro · Préparation mensuelle RAS TVA · 18/10/2026')
        canvas.drawRightString(A4[0]-42,24,str(doc.page));canvas.restoreState()
    cible=dossier/(NOM+'.pdf')
    SimpleDocTemplate(str(cible),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=40,
        title='HisabPro — Préparation mensuelle des retenues TVA opérées').build(story,onFirstPage=pied,onLaterPages=pied)
    return cible


if __name__=='__main__':print(generer())
