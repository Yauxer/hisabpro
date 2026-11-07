from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT=Path(__file__).resolve().parents[1]
NOM='UTILISATION_CONTREPASSATIONS_OUVERTURE_20261019'


def generer(nom=NOM):
    source=ROOT/'docs/guides'/f'{nom}.md'
    st=getSampleStyleSheet()
    font=Path('C:/Windows/Fonts/arial.ttf')
    if font.exists():
        if 'Guide601' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('Guide601',str(font)))
        for n in ('BodyText','Title'):st[n].fontName='Guide601'
    st['BodyText'].fontSize=10;st['BodyText'].leading=14
    story=[]
    for bloc in source.read_text(encoding='utf8').split('\n\n'):
        if not bloc.strip():continue
        if bloc.startswith('# '):story.append(Paragraph(escape(bloc[2:]),st['Title']));continue
        for paragraphe in re.split(r'\n(?=\d+\.)',bloc):
            texte=escape(' '.join(paragraphe.splitlines()))
            texte=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',texte)
            story.extend([Paragraph(texte,st['BodyText']),Spacer(1,7)])
    def pied(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(40,22,'HisabPro - Guide du 19/10/2026')
        canvas.drawRightString(A4[0]-40,22,str(doc.page))
    cible=source.with_suffix('.pdf')
    SimpleDocTemplate(str(cible),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=40).build(story,onFirstPage=pied,onLaterPages=pied)
    return cible


if __name__=='__main__':print(generer())
