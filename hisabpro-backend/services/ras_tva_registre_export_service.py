"""Exports internes du registre099, mêmes sources exactes et logos partagés."""
import csv
from math import ceil
from pathlib import Path
from io import StringIO, BytesIO
from xml.sax.saxutils import escape
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate, Spacer
from services.logo_export_service import ajouter_logo_pdf, ajouter_logo_xlsx
from services.ventes_preparation_export_service import _cell
from services.ras_tva_documents_service import lignes_documents, NOTE_DOCUMENTS

COLONNES = [('capture_id','Capture'),('nature','Nature'),('date_paiement','Date paiement'),('numero_facture','Facture'),
    ('tiers','Tiers figé'),('quote_part_ttc','Quote-part TTC'),('quote_part_tva','TVA quote-part'),
    ('retenue_tva','Retenue déclarée'),('net_reglement','Trésorerie'),('reference','Référence RAS'),
    ('compte_destination','Compte choisi'),('numero_ecriture','N° OD'),('od_validee','OD validée'),
    ('date_annulation','Date annulation'),('mois_reversement_prevu','Mois prévu chez le payeur, versement non suivi ici'),
    ('justification_quote_part','Justificatif ventilation'),('reference_attestation','Attestation déclarée'),('diagnostics','Points à vérifier'),
    ('ecriture_id','ID OD'),('od_annulation_id','ID OD annulation'),('reglement_id','ID règlement'),('facture_id','ID facture')]
MONTANTS = {'quote_part_ttc','quote_part_tva','retenue_tva','net_reglement'}
COLONNES_DOCUMENTS = [('capture_id','Capture'),('nature','Nature'),('phase','OD concernée'),
    ('ecriture_id','ID OD'),('reference','Référence documentaire'),('date_piece','Date pièce'),
    ('source_type','Source'),('fichier_nom','Fichier déclaré'),('created_at','Ajouté le'),
    ('prioritaire','Référence prioritaire FEC')]


def presentation(data):
    return data.get('presentation') or {'titre':'Registre interne des retenues TVA', 'periode':data['annee'],
        'natures':[('achat','Opérées sur achats'),('vente','Subies sur ventes')],
        'groupes':[('declarees','Saisies dans l’année'),('actives','Actives'),
            ('actives_validees','Actives, OD validées'),('annulees','Annulées, paiements de l’année'),
            ('annulations_annee','Annulations de l’année')]}


def texte(v):
    if isinstance(v,list):v=' · '.join(v)
    if isinstance(v,bool):v='Oui' if v else 'Non'
    s = '' if v is None else str(v)
    return "'"+s if s.lstrip().startswith(('=','+','-','@')) or s.startswith(('\t','\r','\n')) else s


def csv_bytes(data):
    out=StringIO(newline='');w=csv.writer(out,delimiter=';')
    p=presentation(data)
    for label,v in [(p['titre'],p['periode']),('Société',data['societe']['raison_sociale']),
        ('ICE',data['societe']['ice']),('IF',data['societe']['identifiant_fiscal']),('Périmètre',data['note']),
        ('Empreinte des données SHA-256',data.get('empreinte_sha256') or 'Indisponible')]:w.writerow([label,texte(v)])
    for nature,_ in p['natures']:
        for cle,label in p['groupes']:
            t=data['totaux'][nature][cle]
            w.writerow(['Total '+nature+' — '+label, t['montant'] if t['montant'] is not None else 'À vérifier'])
    w.writerow([v for _,v in COLONNES])
    for r in data['lignes']:w.writerow([texte('À vérifier' if k in MONTANTS and r[k] is None else r[k]) for k,_ in COLONNES])
    documents=list(lignes_documents(data))
    if documents:
        w.writerow([]);w.writerow(['Documents liés',texte(NOTE_DOCUMENTS)])
        w.writerow([label for _,label in COLONNES_DOCUMENTS])
        for r in documents:w.writerow([texte(r[k]) for k,_ in COLONNES_DOCUMENTS])
    return ('\ufeff'+out.getvalue()).encode('utf-8')


def xlsx_bytes(data,societe):
    w=Workbook();s=w.active;s.title='Synthèse';p=w.create_sheet('Captures')
    meta=presentation(data)
    for i,(label,v) in enumerate([(meta['titre'],meta['periode']),('Société',data['societe']['raison_sociale']),
        ('ICE',data['societe']['ice']),('IF',data['societe']['identifiant_fiscal']),('Périmètre',data['note']),
        ('Empreinte des données SHA-256',data.get('empreinte_sha256') or 'Indisponible')],1):
        _cell(s,label,i,1);_cell(s,v,i,2)
    for j,label in enumerate(['Nature']+[label for _,label in meta['groupes']],1):_cell(s,label,7,j)
    for i,(nature,label) in enumerate(meta['natures'],8):
        _cell(s,label,i,1)
        for j,(cle,_) in enumerate(meta['groupes'],2):_cell(s,data['totaux'][nature][cle]['montant'],i,j,montant=True)
    for j,(_,label) in enumerate(COLONNES,1):_cell(p,label,1,j)
    for i,r in enumerate(data['lignes'],2):
        for j,(k,_) in enumerate(COLONNES,1):
            v=' · '.join(r[k]) if isinstance(r[k],list) else 'Oui' if r[k] is True else 'Non' if r[k] is False else r[k]
            _cell(p,v,i,j,montant=k in MONTANTS)
    documents=list(lignes_documents(data))
    if documents:
        d=w.create_sheet('Documents liés')
        for j,(_,label) in enumerate(COLONNES_DOCUMENTS,1):_cell(d,label,1,j)
        for i,r in enumerate(documents,2):
            for j,(k,_) in enumerate(COLONNES_DOCUMENTS,1):
                v='Oui' if r[k] is True else 'Non' if r[k] is False else r[k]
                _cell(d,'' if v is None else v,i,j)
        d.auto_filter.ref=d.dimensions
    note_ligne=None
    if documents:
        note_ligne=s.max_row+2
        _cell(s,'Documents liés',note_ligne,1);_cell(s,NOTE_DOCUMENTS,note_ligne,2)
    for ws in w:
        ws.freeze_panes='A2'
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='183D35')
        for row in ws:
            for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=24
        ws.row_dimensions[1].height=65
        for n in range(2,ws.max_row+1):
            lignes=max(sum(max(1,ceil(len(t)/22)) for t in str(c.value or '').split('\n')) for c in ws[n])
            ws.row_dimensions[n].height=min(409,max(25,lignes*12+10))
    s.merge_cells('B5:F5');s.row_dimensions[5].height=95
    if note_ligne:
        s.merge_cells(start_row=note_ligne,start_column=2,end_row=note_ligne,end_column=6)
        s.row_dimensions[note_ligne].height=85
    p.auto_filter.ref=p.dimensions
    ajouter_logo_xlsx(w,societe)
    out=BytesIO();w.save(out);return out.getvalue()


def pdf_bytes(data,societe):
    styles=getSampleStyleSheet();styles['BodyText'].fontSize=8;styles['BodyText'].leading=11
    fonts=Path('C:/Windows/Fonts')
    if (fonts/'arial.ttf').is_file() and (fonts/'arialbd.ttf').is_file():
        for nom, fichier in [('RegistreRasTva','arial.ttf'),('RegistreRasTvaBold','arialbd.ttf')]:
            if nom not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(nom,str(fonts/fichier)))
        styles['BodyText'].fontName='RegistreRasTva';styles['Title'].fontName='RegistreRasTvaBold'
    cell=lambda v:Paragraph(escape('À vérifier' if v is None else str(v)),styles['BodyText'])
    montant=lambda v:'À vérifier' if v is None else str(v).replace('.',',')
    meta=presentation(data)
    story=[Paragraph(escape(meta['titre']),styles['Title']),cell(str(meta['periode'])+' · '+data['societe']['raison_sociale']),
        cell('ICE : '+data['societe']['ice']+' · IF : '+data['societe']['identifiant_fiscal']),cell(data['note']),
        cell('Empreinte des données SHA-256 : '+(data.get('empreinte_sha256') or 'Indisponible')),Spacer(1,10)]
    for nature,label in meta['natures']:
        t=data['totaux'][nature]
        story.append(cell(label+' — '+' ; '.join(libelle+' : '+montant(t[cle]['montant']) for cle,libelle in meta['groupes'])+' MAD'))
    rows=[[cell(v) for v in ('Date / nature','Facture / tiers','Quote TTC / TVA','RAS / trésorerie','OD / état','Références déclarées')]]
    for r in data['lignes']:
        rows.append([cell(r['date_paiement']+' / '+r['nature']),cell(str(r['numero_facture'])+' / '+r['tiers']),
            cell(montant(r['quote_part_ttc'])+' / '+montant(r['quote_part_tva'])),cell(montant(r['retenue_tva'])+' / '+montant(r['net_reglement'])),
            cell(str(r['numero_ecriture'] or '#'+str(r['ecriture_id']))+' / '+('Annulée '+r['date_annulation'] if r['annulation_id'] else 'Validée' if r['od_validee'] else 'Brouillon')+
                ' / Compte '+str(r['compte_destination'])+(' / Contrep. #'+str(r['od_annulation_id']) if r['annulation_id'] else '')),
            cell(r['reference']+' / '+r['justification_quote_part']+' / Attestation : '+(r['reference_attestation'] or 'référence non renseignée')+
                ' / Mois prévu : '+(r['mois_reversement_prevu'] or 'à vérifier')+' '+ ' · '.join(r['diagnostics']))])
    table=Table(rows,colWidths=[85,140,95,95,90,250],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9F1EC')),
        ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#CAD5D0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story += [Spacer(1,10),table]
    documents=list(lignes_documents(data))
    if documents:
        story += [Spacer(1,12),cell('Documents liés aux OD'),cell(NOTE_DOCUMENTS),Spacer(1,8)]
        docrows=[[cell(v) for v in ('Capture','Nature / OD','Date pièce','Référence documentaire','Fichier déclaré','Ajout / priorité FEC')]]
        for r in documents:
            docrows.append([cell(r['capture_id']),cell(r['nature']+' / '+r['phase']+' #'+str(r['ecriture_id'])),
                cell(r['date_piece'] or 'Non renseignée'),cell(r['reference'] or 'Non renseignée'),
                cell(r['fichier_nom'] or 'Référence sans fichier'),
                cell((r['created_at'] or 'Date non renseignée')+' / '+('Prioritaire FEC' if r['prioritaire'] else 'Complément'))])
        doc_table=Table(docrows,colWidths=[45,100,65,200,225,120],repeatRows=1)
        doc_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9F1EC')),
            ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#CAD5D0')),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.append(doc_table)
    ajouter_logo_pdf(story,societe)
    out=BytesIO()
    def pied(c,doc):c.setFont('Helvetica',8);c.drawString(30,18,'HisabPro · Préparation interne RAS TVA · Page '+str(doc.page))
    SimpleDocTemplate(out,pagesize=landscape(A4),leftMargin=30,rightMargin=30,topMargin=28,bottomMargin=30,title=meta['titre']).build(story,onFirstPage=pied,onLaterPages=pied)
    return out.getvalue()
