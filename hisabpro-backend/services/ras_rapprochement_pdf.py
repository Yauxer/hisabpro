"""État documentaire interne des rapprochements, jamais un bordereau DGI."""
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from services.logo_export_service import ajouter_logo_pdf


def generer(data,societe):
    styles=getSampleStyleSheet()
    p=lambda v:Paragraph(escape(str(v)),styles['BodyText'])
    argent=lambda v:'Indisponible' if v is None else f'{Decimal(v):,.2f}'.replace(',',' ').replace('.',',')+' MAD'
    story=[Paragraph('Rapprochement comptable documentaire RAS',styles['Title']),
        p(societe.raison_sociale),p(f"Capture #{data['capture_id']} · Compte {data['compte_destination']}"),
        p(data['note']),p('État courant. Identité et logo actuels hors empreintes des rapprochements.'),
        Spacer(1,5*mm),p('Capture : '+argent(data['montant_capture'])),
        p('Montant rapproché : '+argent(data['total_rapproche'])),
        p('Capacité documentaire non rapprochée : '+argent(data['capacite_documentaire']))]
    ajouter_logo_pdf(story,societe)
    if data['capture_annulee']:story.append(p('Capture annulée : les rapprochements sont à revoir, sans retrait automatique.'))
    for r in data['items']:
        e=r['faits']['piece']
        story.extend([Spacer(1,5*mm),p(f"Rapprochement #{r['id']} · {'Retiré' if r['retire_le'] else 'Actif'} · {argent(r['montant'])}"),
            p(f"Pièce #{e['id']} · {e['numero_ecriture'] or ''} · {e['reference'] or 'Sans référence'}"),
            p(f"Date comptable {e['date']} · Journal {e['journal']}"),
            p(f"Créé le {r['created_at']} par l’utilisateur #{r['created_by']}"),
            p('Empreinte des faits conservés : '+r['empreinte_sha256'])])
        for diagnostic in r['diagnostics']:story.append(p(diagnostic))
        if r['retire_le']:story.append(p(f"Retrait du {r['retire_le']} par l’utilisateur #{r['retire_par']} : {r['motif_retrait']}"))
    if not data['items']:story.append(p('Aucun rapprochement documentaire enregistré.'))
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=14*mm,bottomMargin=16*mm,
        title='HisabPro — rapprochement documentaire RAS')
    def pied(canvas,doc):
        canvas.setFont('Helvetica',8)
        canvas.drawString(16*mm,8*mm,'HisabPro · Document interne · Ne vaut pas preuve de versement fiscal')
        canvas.drawRightString(194*mm,8*mm,str(doc.page))
    doc.build(story,onFirstPage=pied,onLaterPages=pied)
    return out.getvalue()
