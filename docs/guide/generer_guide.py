"""Génère le Word OOXML et le PDF depuis le guide Markdown, sans connexion DB."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
import re
import xml.etree.ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
)

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'GUIDE_UTILISATION_VERIFICATION_HISABPRO.md'
STEM = SOURCE.with_suffix('')
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def date_document():
    version = re.search(r'Version \d+ du (\d+) (\w+) (\d{4})', SOURCE.read_text(encoding='utf-8-sig'))
    if not version:
        raise ValueError('Date de version du guide manquante')
    mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    jour, nom_mois, annee = version.groups()
    return f'{int(jour):02d}/{mois.index(nom_mois.lower()) + 1:02d}/{annee}'


def blocs():
    lines = SOURCE.read_text(encoding='utf-8-sig').splitlines()
    result, table = [], []
    for line in lines + ['']:
        if line.startswith('|'):
            if not re.fullmatch(r'[|\-\s:]+', line):
                table.append([s.strip() for s in line.strip('|').split('|')])
            continue
        if table:
            result.append(('table', table))
            table = []
        if not line.strip():
            continue
        if line.startswith('# '):
            result.append(('title', line[2:]))
        elif line.startswith('## '):
            result.append(('h1', line[3:]))
        elif line.startswith('### '):
            result.append(('h2', line[4:]))
        else:
            result.append(('body', line))
    return result


def para(text, style='Normal'):
    return ('<w:p><w:pPr><w:pStyle w:val="' + style + '"/></w:pPr>'
            '<w:r><w:t xml:space="preserve">' + escape(text) + '</w:t></w:r></w:p>')


def word_table(rows):
    widths = [650, 3000, 1250, 3400]
    content = '<w:tbl><w:tblPr><w:tblStyle w:val="GuideTable"/>'
    content += '<w:tblW w:w="8300" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr>'
    content += '<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>'
    for i, row in enumerate(rows):
        content += '<w:tr><w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if i == 0 else '') + '</w:trPr>'
        for width, cell in zip(widths, row):
            shade = '<w:shd w:fill="E8EFF7"/>' if i == 0 else ''
            content += f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>'
            content += para(cell, 'TableText') + '</w:tc>'
        content += '</w:tr>'
    return content + '</w:tbl>'


def docx(items):
    body = ''.join(word_table(value) if kind == 'table' else para(value, {
        'title': 'Title', 'h1': 'Heading1', 'h2': 'Heading2', 'body': 'Normal',
    }[kind]) for kind, value in items)
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>{body}
<w:sectPr><w:headerReference w:type="default" r:id="rId2"/><w:footerReference w:type="default" r:id="rId3"/>
<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="500" w:footer="500"/></w:sectPr></w:body></w:document>'''
    styles = f'''<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="21"/><w:lang w:val="fr-FR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="270" w:lineRule="auto"/><w:widowControl/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="1200" w:after="500"/></w:pPr><w:rPr><w:b/><w:color w:val="185FA5"/><w:sz w:val="42"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:pageBreakBefore/><w:keepNext/><w:spacing w:after="240"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="185FA5"/><w:sz w:val="30"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:color w:val="263D55"/><w:sz w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="50"/></w:pPr><w:rPr><w:sz w:val="18"/></w:rPr></w:style>
<w:style w:type="table" w:styleId="GuideTable"><w:name w:val="Guide table"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:color="CDD8E5"/><w:left w:val="single" w:sz="4" w:color="CDD8E5"/><w:bottom w:val="single" w:sz="4" w:color="CDD8E5"/><w:right w:val="single" w:sz="4" w:color="CDD8E5"/><w:insideH w:val="single" w:sz="4" w:color="CDD8E5"/><w:insideV w:val="single" w:sz="4" w:color="CDD8E5"/></w:tblBorders><w:tblCellMar><w:top w:w="75" w:type="dxa"/><w:left w:w="75" w:type="dxa"/><w:bottom w:w="75" w:type="dxa"/><w:right w:w="75" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style></w:styles>'''
    types = '''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'''
    for name, type_ in [('document','document.main'),('styles','styles'),('settings','settings'),('header1','header'),('footer1','footer')]:
        types += f'<Override PartName="/word/{name}.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.{type_}+xml"/>'
    types += '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>'
    ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
    relns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    rootrels = f'<Relationships xmlns="{ns}"><Relationship Id="rId1" Type="{relns}officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>'
    rels = f'<Relationships xmlns="{ns}">' + ''.join(
        f'<Relationship Id="{id_}" Type="{relns}{type_}" Target="{path}"/>'
        for id_,type_,path in [('rId1','styles','styles.xml'),('rId2','header','header1.xml'),('rId3','footer','footer1.xml'),('rId4','settings','settings.xml')]) + '</Relationships>'
    header = f'<w:hdr xmlns:w="{W}">{para("HISABPRO | Guide utilisateur — Démonstration et vérification")}</w:hdr>'
    footer = f'''<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:t>Recette fictive · {date_document()} · Page </w:t></w:r><w:fldSimple w:instr="PAGE"><w:r><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>'''
    core = '''<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>HisabPro — Mode d’emploi et vérification des avancées</dc:title><dc:creator>HisabPro</dc:creator><dc:description>Parcours utilisateur, exemples fictifs, contrôles et limites.</dc:description><dc:language>fr-FR</dc:language></cp:coreProperties>'''
    files = {'[Content_Types].xml':types, '_rels/.rels':rootrels,
        'word/document.xml':document, 'word/styles.xml':styles,
        'word/settings.xml':f'<w:settings xmlns:w="{W}"><w:updateFields w:val="true"/></w:settings>',
        'word/_rels/document.xml.rels':rels, 'word/header1.xml':header,
        'word/footer1.xml':footer, 'docProps/core.xml':core}
    for xml in files.values():
        ET.fromstring(xml)
    with ZipFile(STEM.with_suffix('.docx'), 'w', ZIP_DEFLATED) as z:
        for name,data in files.items():
            z.writestr(name, data.encode('utf-8'))


def pdf(items):
    fontdir = Path('C:/Windows/Fonts')
    if (fontdir / 'arial.ttf').is_file():
        pdfmetrics.registerFont(TTFont('Guide', str(fontdir / 'arial.ttf')))
        pdfmetrics.registerFont(TTFont('GuideBold', str(fontdir / 'arialbd.ttf')))
    else:
        raise RuntimeError('Fonte Unicode Arial requise pour le PDF français.')
    styles = {
        'title': ParagraphStyle('title', fontName='GuideBold', fontSize=23, leading=29, textColor=colors.HexColor('#185FA5'), spaceBefore=40, spaceAfter=22),
        'h1': ParagraphStyle('h1',fontName='GuideBold',fontSize=16,leading=21,textColor=colors.HexColor('#185FA5'),spaceAfter=14,keepWithNext=True),
        'h2': ParagraphStyle('h2',fontName='GuideBold',fontSize=11,leading=15,textColor=colors.HexColor('#263D55'),spaceBefore=10,spaceAfter=7,keepWithNext=True),
        'body': ParagraphStyle('body',fontName='Guide',fontSize=10,leading=14,spaceAfter=7,alignment=TA_LEFT,splitLongWords=True),
        'table': ParagraphStyle('table',fontName='Guide',fontSize=8,leading=11,spaceAfter=1),
    }
    story = []
    for kind,value in items:
        if kind == 'table':
            rows = [[Paragraph(escape(cell),styles['table']) for cell in row] for row in value]
            table = Table(rows, colWidths=[13*mm,65*mm,27*mm,65*mm],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF7')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CDD8E5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([table,Spacer(1,10)])
        else:
            if kind == 'h1':
                story.append(PageBreak())
            story.append(Paragraph(escape(value),styles[kind]))
    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setFont('Guide',8)
        canvas.setFillColor(colors.HexColor('#52687F'))
        canvas.drawString(20*mm, A4[1]-13*mm, 'HISABPRO | Mode d’emploi et vérification')
        canvas.drawRightString(A4[0]-20*mm,12*mm,f'Recette fictive · {date_document()} · {doc.page}')
        canvas.restoreState()
    document = SimpleDocTemplate(str(STEM.with_suffix('.pdf')),pagesize=A4,
        leftMargin=20*mm,rightMargin=20*mm,topMargin=22*mm,bottomMargin=22*mm,
        title='HisabPro — Mode d’emploi et vérification des avancées',author='HisabPro')
    document.build(story,onFirstPage=decorate,onLaterPages=decorate)


if __name__ == '__main__':
    items = blocs()
    docx(items)
    pdf(items)
    print('Word/PDF générés depuis', SOURCE.name, ':', len(items), 'blocs')
