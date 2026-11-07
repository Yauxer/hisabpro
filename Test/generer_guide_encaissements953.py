"""Guide953 Word/PDF ; ne modifie pas le cahier ou ses résultats humains."""
from pathlib import Path
from html import escape
import re
import sys

from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'docs/recette'
NOM = 'MODE_EMPLOI_TVA_ENCAISSEMENTS_953'
SOURCES = ['TVA_ENCAISSEMENTS_953.md']


def texte(ligne):
    ligne = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'\1 (\2)', ligne)
    return ligne.replace('**', '').replace('`', '')


def generer(remplacer=False):
    word, pdf = DEST/(NOM+'.docx'), DEST/(NOM+'.pdf')
    assert remplacer or (not word.exists() and not pdf.exists()), 'Annexe déjà présente ; ne pas écraser une copie annotée.'
    elements = []
    def paragraphe(val, style='Normal'):
        elements.append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{escape(val)}</w:t></w:r></w:p>')
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 9
    styles['Normal'].leading = 12
    styles['BodyText'].fontSize = 8
    styles['BodyText'].leading = 10
    contenu = []
    titre = 'HISABPRO — MODE D’EMPLOI ET ANNEXE DE RECETTE'
    paragraphe(titre, 'Title')
    contenu.append(Paragraph(escape(titre), styles['Title']))
    intro = ('Complément953 — scénario annuel TVA sur encaissements, données fictives et bases isolées. '
             'Le classeur JEU_RECETTE_ENCAISSEMENTS_953.xlsx contient les saisies et résultats attendus. '
             'Les résultats humains restent à renseigner ; la migration126 est à vérifier sur copie avant utilisation. '
             'Ce document ne constitue pas une certification fiscale.')
    paragraphe(intro)
    contenu.extend([Paragraph(escape(intro), styles['Normal']), Spacer(1, 16)])
    for source in SOURCES:
        elements.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        contenu.append(PageBreak())
        lignes = (DEST/source).read_text(encoding='utf8').splitlines()
        i = 0
        while i < len(lignes):
            ligne = lignes[i].strip()
            if ligne.startswith('|'):
                rows = []
                while i < len(lignes) and lignes[i].strip().startswith('|'):
                    cellules = [texte(c.strip()) for c in lignes[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'[:\- ]+', c or '-') for c in cellules):
                        rows.append(cellules)
                    i += 1
                if rows:
                    bordures = ''.join(f'<w:{c} w:val="single" w:sz="4" w:color="B0B0B0"/>' for c in ['top','left','bottom','right','insideH','insideV'])
                    largeur = 10206//len(rows[0])
                    grille = ''.join(f'<w:gridCol w:w="{largeur}"/>' for _ in rows[0])
                    tableau = f'<w:tbl><w:tblPr><w:tblBorders>{bordures}</w:tblBorders></w:tblPr><w:tblGrid>{grille}</w:tblGrid>'
                    for row in rows:
                        tableau += '<w:tr>' + ''.join(f'<w:tc><w:tcPr><w:tcW w:w="{largeur}" w:type="dxa"/></w:tcPr><w:p><w:r><w:t xml:space="preserve">'+escape(val)+'</w:t></w:r></w:p></w:tc>' for val in row) + '</w:tr>'
                    elements.append(tableau+'</w:tbl>')
                    donnees = [[Paragraph(escape(c), styles['BodyText']) for c in row] for row in rows]
                    t = Table(donnees, colWidths=[510/len(rows[0])]*len(rows[0]), repeatRows=1)
                    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8EEF6')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
                    contenu.extend([t, Spacer(1, 10)])
                continue
            if ligne:
                niveau = len(ligne)-len(ligne.lstrip('#')) if ligne.startswith('#') else 0
                val = texte(ligne.lstrip('#').strip())
                if niveau:
                    paragraphe(val, 'Heading'+str(min(niveau, 3)))
                    contenu.append(Paragraph(escape(val), styles['Heading'+str(min(niveau, 3))]))
                else:
                    paragraphe(val)
                    contenu.extend([Paragraph(escape(val), styles['Normal']), Spacer(1, 6)])
            i += 1
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    xml = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{ns}"><w:body>'+''.join(elements)+'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="850" w:bottom="850" w:left="850" w:right="850"/></w:sectPr></w:body></w:document>'
    styles_xml = f'<w:styles xmlns:w="{ns}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:after="100"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="20"/></w:rPr></w:style>'
    for ident, taille in [('Title',36),('Heading1',30),('Heading2',25),('Heading3',22)]:
        styles_xml += f'<w:style w:type="paragraph" w:styleId="{ident}"><w:name w:val="{ident}"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="100"/></w:pPr><w:rPr><w:b/><w:color w:val="24589C"/><w:sz w:val="{taille}"/></w:rPr></w:style>'
    styles_xml += '</w:styles>'
    with ZipFile(word, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', xml)
        z.writestr('word/styles.xml', styles_xml)
        z.writestr('word/_rels/document.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
    with ZipFile(word) as z:
        assert z.testzip() is None
        for n in z.namelist():ElementTree.fromstring(z.read(n))
        assert len(ElementTree.fromstring(z.read('word/document.xml')).findall('.//{'+ns+'}p')) > 30
    def pied(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(42, 24, 'HisabPro — recette humaine à effectuer — 29/10/2026')
        canvas.drawRightString(A4[0]-42, 24, str(document.page))
    SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=42, rightMargin=42,
                      topMargin=42, bottomMargin=40).build(contenu, onFirstPage=pied, onLaterPages=pied)
    reader = PdfReader(pdf)
    extrait = '\n'.join(p.extract_text() or '' for p in reader.pages)
    assert len(reader.pages) >= 2 and all(t in extrait for t in ['REC-COMP01', '126', '2026', '19 900'])
    print(f'Annexe vérifiée : Word et PDF {len(reader.pages)} pages ;cahier humain inchangé.')


if __name__ == '__main__':
    generer('--remplacer' in sys.argv)
