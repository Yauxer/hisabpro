"""Dossier interne courant, PDF/Excel sur les mêmes faits et la même identité."""
import hashlib
import json
from math import ceil
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
import models
from services.reprises_provisions_service import exiger_registre,lecture_source
from services.plan_comptable import libelle_compte
from services.logo_export_service import image_logo,ajouter_logo_pdf,ajouter_logo_xlsx
from services.ventes_preparation_export_service import _cell

TITRE='Suivi interne des reprises de provisions'
COLONNES=[('id','ID reprise'),('date','Date de reprise'),('montant','Montant MAD'),
    ('numero','Pièce de reprise'),('statut','Statut de reprise'),('justification','Justification déclarée'),
    ('reference','Référence déclarée à la création'),('date_piece','Date de pièce déclarée'),
    ('inverse','Pièce inverse'),('inverse_date','Date inverse'),('inverse_statut','Statut inverse'),
    ('motif','Motif d’annulation'),('capacite','Effet sur la capacité liée'),
    ('exercice','Exercice de reprise'),('inverse_exercice','Exercice de l’inverse')]


def preparer(db,sid,aid):
    exiger_registre(db)
    source=lecture_source(db,sid,aid)
    societe=db.get(models.Societe,sid)
    logo=image_logo(societe)
    identite={'id':sid,'raison_sociale':societe.raison_sociale or '', 'ice':societe.ice or '',
        'identifiant_fiscal':societe.identifiant_fiscal or '',
        'logo_sha256':hashlib.sha256(logo.getvalue()).hexdigest() if logo else None}
    data={'version':'suivi-reprises-617','societe':identite,'source':source,
        'comptes':{c:libelle_compte(c,db,sid) for c in
            (source['compte_dotation'],source['compte_provision'],source['compte_reprise']) if c},
        'note':source['note']+' Identité et logo courants de la société, pas une archive annuelle. '
            'Le disponible final ne permet pas de financer une reprise antérieure à un inverse. '
            'Ce document interne n’est ni une déclaration DGI ni une attestation de déductibilité.'}
    # Dates/UUID sont encodés de manière stable comme dans la réponse JSON.
    data=json.loads(json.dumps(data,default=str,ensure_ascii=False))
    data['empreinte_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return data,societe


def lignes(data):
    for r in data['source']['reprises']:
        annulee=bool(r['annulation_id'] and r['est_validee'] and r['inverse_validee'])
        f=r['faits']['faits']
        yield {'id':r['id'],'date':r['date'],'exercice':r['exercice'],'montant':r['montant'],
            'numero':r['numero_ecriture'] or '#'+str(r['ecriture_id']),
            'statut':'Validée' if r['est_validee'] else 'Brouillon',
            'justification':f['justification'],'reference':f['reference'],'date_piece':f['date_piece'],
            'inverse':r['inverse_numero'] or ('#'+str(r['inverse_id']) if r['inverse_id'] else None),
            'inverse_date':r['inverse_date'],'inverse_exercice':r['inverse_exercice'],
            'inverse_statut':('Validé' if r['inverse_validee'] else 'Brouillon') if r['annulation_id'] else None,
            'motif':r['motif'], 'capacite':'Libérée à la date de l’inverse' if annulee else
                'Consommée, reprise validée' if r['est_validee'] else 'Réservée, reprise en brouillon'}


def synthese(data):
    a=data['source'];s=data['societe']
    return [('Société',s['raison_sociale']),('ICE',s['ice']),('Identifiant fiscal',s['identifiant_fiscal']),
        ('Dotation source',str(a['id'])+' — '+a['libelle']),('Exercice source',a['exercice']),
        ('Pièce source',a['numero'] or ('#'+str(a['ecriture_id']) if a['ecriture_id'] else 'Absente')),
        ('Date source',a['date']),('Compte de dotation',a['compte_dotation']+' — '+str(data['comptes'].get(a['compte_dotation']) or 'À vérifier')),
        ('Compte de provision',a['compte_provision']+' — '+str(data['comptes'].get(a['compte_provision']) or 'À vérifier')),
        ('Diagnostic',a['diagnostic'] or 'Aucune incohérence de source détectée par ce contrôle'),
        ('Dotation initiale MAD',a['dotation']),('Reprises validées actives MAD',a['reprises_validees']),
        ('Réservations en brouillon MAD',a['reservations_brouillons']),('Disponible final du registre MAD',a['disponible']),
        ('Périmètre',data['note']),('Empreinte des données SHA-256',data['empreinte_sha256'])]


def xlsx_bytes(data,societe):
    w=Workbook();s=w.active;s.title='Synthèse';p=w.create_sheet('Reprises')
    _cell(s,TITRE,1,1)
    for i,(label,v) in enumerate(synthese(data),2):
        _cell(s,label,i,1);_cell(s,v,i,2,montant=12<=i<=15)
    for j,(_,label) in enumerate(COLONNES,1):_cell(p,label,1,j)
    for i,r in enumerate(lignes(data),2):
        for j,(cle,_) in enumerate(COLONNES,1):_cell(p,r[cle],i,j,montant=cle=='montant')
    for ws in (s,p):
        ws.freeze_panes='A2'
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='183D35')
        for row in ws:
            for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=27
    s.column_dimensions['B'].width=95
    p.column_dimensions['F'].width=60;p.column_dimensions['L'].width=60
    for ws in (s,p):
        for row in ws:
            hauteur=max(sum(max(1,ceil(len(t)/max(1,int(ws.column_dimensions[c.column_letter].width)-3)))
                for t in str(c.value or '').split('\n')) for c in row)
            ws.row_dimensions[row[0].row].height=min(409,max(28,hauteur*14+10))
    p.auto_filter.ref=p.dimensions
    ajouter_logo_xlsx(w,societe)
    out=BytesIO();w.save(out);return out.getvalue()


def pdf_bytes(data,societe):
    styles=getSampleStyleSheet();styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
    fonts=Path('C:/Windows/Fonts')
    if (fonts/'arial.ttf').is_file():
        if 'ReprisesProvisions' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('ReprisesProvisions',str(fonts/'arial.ttf')))
        styles['BodyText'].fontName=styles['Title'].fontName='ReprisesProvisions'
    p=lambda v:Paragraph(escape('À vérifier' if v is None else str(v)),styles['BodyText'])
    story=[Paragraph(TITRE,styles['Title']),Spacer(1,8)]
    table=Table([[p(label),p(v)] for label,v in synthese(data)],colWidths=[165,350])
    table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.25,colors.HexColor('#CAD5D0')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#E9F1EC')),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story += [table,Spacer(1,12),p('Historique des reprises — pièces d’origine et inverses conservés')]
    for r in lignes(data):
        story += [Spacer(1,12),p('Reprise '+str(r['id'])+' · '+r['date']+' · Exercice '+str(r['exercice'])+' · '+r['montant']+' MAD · '+r['numero']+' · '+r['statut'])]
        for cle,label in COLONNES[5:]:story += [p(label+' : '+('Non renseigné' if r[cle] is None else str(r[cle])))]
    if not data['source']['reprises']:story.append(p('Aucune reprise liée à cette source.'))
    story += [Spacer(1,12),p('L’empreinte identifie les données exportées ; ce n’est ni une signature ni l’empreinte du PDF.')]
    ajouter_logo_pdf(story,societe)
    out=BytesIO()
    def pied(c,doc):c.setFont('Helvetica',8);c.drawString(40,20,'HisabPro · Suivi interne des provisions · Page '+str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=35,
        title=TITRE).build(story,onFirstPage=pied,onLaterPages=pied)
    return out.getvalue()
