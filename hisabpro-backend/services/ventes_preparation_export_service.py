"""Exports internes de la préparation documentaire ; montants issus du serveur."""
from decimal import Decimal
from math import ceil
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from services.logo_export_service import ajouter_logo_pdf, ajouter_logo_xlsx


def _montant(v):
    return 'À vérifier' if v is None else v.replace('.', ',')


def _cell(ws, valeur, ligne, colonne, montant=False):
    cell=ws.cell(ligne,colonne)
    if montant and valeur is not None:
        d=Decimal(valeur)
        # Excel conserve quinze chiffres significatifs ; sinon garder le texte exact.
        if len(d.normalize().as_tuple().digits)<=15 and Decimal(str(float(d)))==d:
            cell.value=float(d);cell.number_format='0.00';return
    cell.value='À vérifier' if montant and valeur is None else '' if valeur is None else str(valeur)
    cell.data_type='s'


def xlsx(data, societe=None):
    w=Workbook();s=w.active;s.title='Synthèse';p=w.create_sheet('Sources')
    infos=[('Préparation interne des ventes',data['exercice']),('Société',data['societe']['raison_sociale']),
        ('ICE société',data['societe']['ice']),('IF société',data['societe']['identifiant_fiscal']),
        ('Période',data['date_debut']+' → '+data['date_fin']),('Empreinte',data['empreinte_sha256']),
        ('Périmètre',data['note']),('Pièces retenues',len(data['documents'])),
        ('Sources aux montants inconnus',data['nb_montants_inconnus'])]
    for i,(label,v) in enumerate(infos,1):_cell(s,label,i,1);_cell(s,v,i,2)
    _cell(s,'Total complet',11,1);_cell(s,'HT commercial signé',12,1);_cell(s,'TVA signée',13,1);_cell(s,'TTC signé',14,1)
    for i,k in enumerate(('ht','tva','ttc'),12):_cell(s,data['totaux'][k] if data['totaux'] is not None else None,i,2,montant=True)
    _cell(s,'Partie connue uniquement',16,1)
    for i,k in enumerate(('ht','tva','ttc'),17):_cell(s,k.upper(),i,1);_cell(s,data['totaux_partie_connue'][k],i,2,montant=True)
    for i,(k,v) in enumerate(data['exclusions'].items(),21):_cell(s,'Exclus : '+k,i,1);_cell(s,v,i,2)
    headers=['Nature','ID source','Numéro','Date','Client figé','ICE figé','IF figé','HT commercial signé','TVA signée','TTC signé','Comptabilisée','Diagnostics']
    for j,label in enumerate(headers,1):_cell(p,label,1,j)
    for i,r in enumerate(data['documents'],2):
        for j,k in enumerate(('nature','id','numero','date','tiers','ice','identifiant_fiscal','ht','tva','ttc'),1):
            _cell(p,r[k],i,j,montant=k in {'ht','tva','ttc'})
        _cell(p,'Oui' if r['comptabilisee'] else 'Non',i,11);_cell(p,' '.join(r['diagnostics']),i,12)
    compta = data.get('comptabilite')
    if compta:
        _cell(s, 'Raccordement comptable', 25, 1); _cell(s, compta['note'], 25, 2)
        for i, label, v in [(26, 'CA comptes711/712 validés', compta['ca_net']),
                            (27, 'HT documentaire signé', data['totaux']['ht'] if data['totaux'] else None),
                            (28, 'Écart CA moins HT documentaire', compta['ecart_ca_moins_ht'])]:
            _cell(s, label, i, 1); _cell(s, v, i, 2, montant=True)
        _cell(s, 'Brouillons exclus du CA', 29, 1); _cell(s, compta['brouillons_exclus'], 29, 2)
        _cell(s, 'Contrôles', 30, 1); _cell(s, ' '.join(compta['avertissements']), 30, 2)
        j = w.create_sheet('Comptabilité')
        for col, label in enumerate(['Écriture', 'Ligne', 'Date', 'Journal', 'Référence', 'Origine technique', 'Compte', 'Débit', 'Crédit', 'CA net'], 1):
            _cell(j, label, 1, col)
        for i, m in enumerate(compta['mouvements'], 2):
            for col, k in enumerate(('ecriture_id', 'ligne_id', 'date', 'journal', 'reference', 'source', 'compte', 'debit', 'credit', 'ca_net'), 1):
                _cell(j, m[k], i, col, montant=k in ('debit', 'credit', 'ca_net'))
        j.auto_filter.ref=j.dimensions
        s.row_dimensions[25].height=80
    for ws in w:
        ws.freeze_panes='A2'
        for cellule in ws[1]:cellule.font=Font(bold=True,color='FFFFFF');cellule.fill=PatternFill('solid',fgColor='185FA5')
        for row in ws:
            for cellule in row:cellule.alignment=Alignment(vertical='top',wrap_text=True)
        for colonne in ws.columns:ws.column_dimensions[colonne[0].column_letter].width=22
    s.column_dimensions['A'].width=30;s.column_dimensions['B'].width=100;s.row_dimensions[7].height=80
    p.column_dimensions['E'].width=36;p.column_dimensions['L'].width=65;p.auto_filter.ref=p.dimensions
    for i in range(2,p.max_row+1):p.row_dimensions[i].height=65
    if compta:
        j.column_dimensions['E'].width=36
        for row in j.iter_rows(min_row=2):
            lignes = max(sum(max(1, ceil(len(partie) / max(8, int(j.column_dimensions[c.column_letter].width) - 3)))
                for partie in str(c.value or '').split('\n')) for c in row)
            j.row_dimensions[row[0].row].height=max(30, 15*lignes+8)
    ajouter_logo_xlsx(w, societe if societe is not None else data['societe'])
    out=BytesIO();w.save(out);return out.getvalue()


def pdf(data, societe=None):
    dossier=Path('C:/Windows/Fonts')
    if (dossier/'arial.ttf').is_file():
        for nom,f in [('VentesInterne','arial.ttf'),('VentesInterneBold','arialbd.ttf')]:
            if nom not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(nom,str(dossier/f)))
        normal,bold='VentesInterne','VentesInterneBold'
    else:normal,bold='Helvetica','Helvetica-Bold'
    body=ParagraphStyle('texte',fontName=normal,fontSize=8,leading=11)
    titre=ParagraphStyle('titre',fontName=bold,fontSize=15,leading=19,textColor=colors.HexColor('#185FA5'))
    cellule=ParagraphStyle('cellule',fontName=normal,fontSize=7,leading=10)
    para=lambda v:Paragraph(escape(str(v)),cellule)
    story=[Paragraph('PRÉPARATION INTERNE DES VENTES',titre),Spacer(1,5*mm),
        Paragraph(escape(str(data['societe']['raison_sociale'] or f"Société #{data['societe_id']}")),body),
        Paragraph(f"Exercice {data['exercice']} · {data['date_debut']} → {data['date_fin']}",body),
        Paragraph(escape(data['note']),body),Spacer(1,4*mm)]
    ajouter_logo_pdf(story, societe if societe is not None else data['societe'])
    total=data['totaux']
    story.append(Paragraph('Total complet : HT '+_montant(total['ht'] if total else None)+' ; TVA '+_montant(total['tva'] if total else None)+' ; TTC '+_montant(total['ttc'] if total else None),body))
    if total is None:story.append(Paragraph('Partie connue uniquement : HT '+_montant(data['totaux_partie_connue']['ht'])+' ; TVA '+_montant(data['totaux_partie_connue']['tva'])+' ; TTC '+_montant(data['totaux_partie_connue']['ttc']),body))
    story.append(Spacer(1,4*mm))
    rows=[[para(v) for v in ('Pièce / source','Date','Client figé','ICE / IF figés','HT commercial signé','TVA signée','TTC signé','Contrôles')]]
    for r in data['documents']:
        values=[f"{r['nature']} {r['numero'] or '#'+str(r['id'])} · ID {r['id']}",r['date'],r['tiers'],
            f"{r['ice'] or 'À compléter'} / {r['identifiant_fiscal'] or 'À compléter'}",
            _montant(r['ht']),_montant(r['tva']),_montant(r['ttc']),' '.join(r['diagnostics']) or 'Source disponible']
        rows.append([para(v) for v in values])
    if len(rows)>1:
        table=Table(rows,colWidths=[25*mm,23*mm,42*mm,33*mm,27*mm,23*mm,25*mm,69*mm],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF7')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CDD8E5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(table)
    else:story.append(Paragraph('Aucune pièce de vente définitive dans cette période.',body))
    compta = data.get('comptabilite')
    if compta:
        story.extend([Spacer(1, 5*mm), Paragraph('RACCORDEMENT COMPTABLE', titre),
            Paragraph(escape(compta['note']), body), Spacer(1, 2*mm),
            Paragraph('CA comptes711/712 : '+_montant(compta['ca_net'])+' ; HT documentaire : '+_montant(total['ht'] if total else None)
                +' ; écart CA moins HT : '+_montant(compta['ecart_ca_moins_ht']), body)])
        for c in compta['comptes']:
            story.append(Paragraph(escape(c['compte'])+' · Débit '+_montant(c['debit'])+' · Crédit '+_montant(c['credit'])+' · CA net '+_montant(c['ca_net']), body))
        for o in compta['origines']:
            story.append(Paragraph('Origine '+escape(o['source'])+' · '+str(o['nb_lignes'])+' ligne(s) · '+_montant(o['ca_net']), body))
        for alerte in compta['avertissements']: story.append(Paragraph(escape(alerte), body))
        story.append(Paragraph('Brouillons exclus du CA : '+str(compta['brouillons_exclus'])+'. Détail des mouvements dans les exports Excel et CSV.', body))
    story.extend([Spacer(1,4*mm),Paragraph('Exclusions : '+escape(', '.join(f'{k} {v}' for k,v in data['exclusions'].items())),body),
                  Paragraph('Empreinte : '+data['empreinte_sha256'],body)])
    out=BytesIO();doc=SimpleDocTemplate(out,pagesize=landscape(A4),leftMargin=15*mm,rightMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm,title='HisabPro — préparation interne des ventes')
    def footer(canvas,doc):canvas.setFont(normal,7);canvas.drawString(15*mm,8*mm,'HisabPro · Document interne · Page '+str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer);return out.getvalue()
