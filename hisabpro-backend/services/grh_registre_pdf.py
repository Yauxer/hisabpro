"""Registre interne des périodes déclarées ; aucun calcul de droits ou de paie."""
from datetime import datetime,timezone
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from services.logo_export_service import ajouter_logo_pdf

TYPES={'conge':'Congé','absence':'Absence','autre':'Autre'}
STATUTS={'demande':'Demandée','approuve':'Approuvée','refuse':'Refusée','annule':'Annulée'}


def generer_registre_absences_pdf(societe,demandes,statut=None):
    buffer=BytesIO()
    styles=getSampleStyleSheet()
    petit=ParagraphStyle('grh_cell',parent=styles['BodyText'],fontSize=8,leading=10,spaceAfter=0)
    def p(value,style=None,sauts=False):
        texte=escape(str(value if value is not None else 'Non renseigné'))
        return Paragraph(texte.replace('\n','<br/>') if sauts else texte,style or petit)
    edition=datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
    def pied(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(12*mm,8*mm,'HisabPro — Registre interne GRH')
        canvas.drawRightString(A4[0]-12*mm,8*mm,f'Page {doc.page}');canvas.restoreState()
    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=12*mm,rightMargin=12*mm,
        topMargin=12*mm,bottomMargin=18*mm,title='Registre des congés et absences')
    story=[p('Registre des congés et absences',styles['Title']),
        p(societe.raison_sociale,styles['Heading2']),p('Sélection : '+(STATUTS.get(statut,statut) if statut else 'Toutes les demandes')),
        p('Édition : '+edition),Spacer(1,3*mm),
        p('Périodes et décisions déclarées. Les durées sont des jours calendaires, début et fin inclus. '
          'Ce registre ne calcule ni solde de congés acquis ni retenue sur salaire.'),Spacer(1,4*mm)]
    ajouter_logo_pdf(story,societe)
    if not demandes:
        story.append(p('Aucune demande dans cette sélection.'))
    else:
        data=[[p(x) for x in ['Réf. interne','Salarié','Type','Début','Fin','Jours calendaires','Statut']]]
        for a in demandes:
            data.append([p(x) for x in [f"#{a['id']}",a['nom_employe'],
                TYPES.get(a['type_absence'],a['type_absence']),a['date_debut'],a['date_fin'],
                a['jours_calendaires'],STATUTS.get(a['statut'],a['statut'])]])
        table=Table(data,colWidths=[17*mm,45*mm,20*mm,25*mm,25*mm,22*mm,32*mm],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6F1FB')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.7,colors.HexColor('#185FA5')),
            ('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#DDDDDD')),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.extend([table,Spacer(1,5*mm),p('Motifs, décisions et historique',styles['Heading2'])])
        for a in demandes:
            story.append(p(f"Demande #{a['id']} — {a['nom_employe']} — {a['date_debut']} au {a['date_fin']}",styles['Heading3']))
            story.append(p('Motif : '+(a.get('motif') or 'Non renseigné'),sauts=True))
            story.append(p('Commentaire de décision : '+(a.get('commentaire_decision') or 'Non renseigné'),sauts=True))
            if not a['historique']:
                story.append(p('Historique non renseigné.'))
            for ev in a['historique']:
                ancien=STATUTS.get(ev['ancien_statut'],ev['ancien_statut'] or 'Non renseigné')
                nouveau=STATUTS.get(ev['nouveau_statut'],ev['nouveau_statut'])
                story.append(p(f"{ev['created_at']} — {ancien} vers {nouveau} — Acteur (réf. interne) #{ev['acteur_id']}"))
                if ev.get('commentaire'):story.append(p(ev['commentaire'],sauts=True))
            story.append(Spacer(1,3*mm))
    doc.build(story,onFirstPage=pied,onLaterPages=pied)
    return buffer.getvalue()
