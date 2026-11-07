"""Guide PDF depuis le Markdown, sans application ni base de données."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph

ROOT=Path(__file__).resolve().parents[1]
NOM='UTILISATION_CALCUL_CCA_PCA_20261018'


def generer():
    dossier=ROOT/'docs/guides';lignes=(dossier/(NOM+'.md')).read_text(encoding='utf-8').splitlines()
    titre=lignes.pop(0).lstrip('# ');styles=getSampleStyleSheet()
    styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=9
    font=Path('C:/Windows/Fonts/arial.ttf')
    if font.is_file():
        if 'GuideProrata595' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('GuideProrata595',str(font)))
        styles['BodyText'].fontName=styles['Heading1'].fontName='GuideProrata595'
    story=[Paragraph('HisabPro',styles['Title']),Paragraph(escape(titre),styles['Heading1'])]
    for bloc in re.split(r'\n\s*\n','\n'.join(lignes).strip()):story.append(Paragraph(escape(' '.join(bloc.split())),styles['BodyText']))
    def pied(c,doc):
        c.setFont('Helvetica',8);c.drawString(42,24,'HisabPro · Guide du calcul documentaire CCA / PCA · 18/10/2026')
        c.drawRightString(A4[0]-42,24,str(doc.page))
    cible=dossier/(NOM+'.pdf')
    SimpleDocTemplate(str(cible),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=40,
        title='HisabPro — Calcul documentaire facultatif CCA / PCA').build(story,onFirstPage=pied,onLaterPages=pied)
    return cible


if __name__=='__main__':print(generer())
