"""Calcul et feuille PDF sans mutation métier, sur un snapshot RO/RR."""
from typing import Annotated
from io import BytesIO
from pathlib import Path
import hashlib
import json
from xml.sax.saxutils import escape
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import Field
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from database import get_db
from auth import get_current_user
import models
from services.ventes_preparation_service import preparer_lecture
from services.logo_export_service import ajouter_logo_pdf
from services.prorata_inventaire_service import ProrataIn, calculer

router=APIRouter()


class ExportIn(ProrataIn):
    empreinte: str = Field(pattern=r'^[a-f0-9]{64}$')


def lecture(db:Session=Depends(get_db)):
    return preparer_lecture(db)


def preparer(db,sid,exercice,faits):
    ex=db.query(models.ExerciceComptable).filter_by(societe_id=sid,annee=exercice).first()
    if not ex:raise HTTPException(404,'Exercice introuvable. Préparez son calendrier avant ce calcul.')
    s=db.get(models.Societe,sid)
    try:data=calculer(faits,ex.date_fin)
    except ValueError as exc:raise HTTPException(400,str(exc)) from exc
    data.update(societe_id=sid,exercice=exercice,societe={'raison_sociale':s.raison_sociale or '',
        'ice':s.ice or '', 'identifiant_fiscal':s.identifiant_fiscal or '',
        'logo_sha256':hashlib.sha256((s.logo_url or '').encode()).hexdigest()})
    data['empreinte_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return data,s


@router.post('/ajustements/calcul-prorata')
def consulter(data:ProrataIn,exercice:Annotated[int,Query(ge=1,le=9999)],
    db:Session=Depends(lecture),user=Depends(get_current_user)):
    return preparer(db,user['societe_id'],exercice,data)[0]


def pdf_bytes(data,societe):
    styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=14
    font=Path('C:/Windows/Fonts/arial.ttf')
    if font.is_file():
        if 'ProrataInventaire' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('ProrataInventaire',str(font)))
        styles['BodyText'].fontName=styles['Title'].fontName='ProrataInventaire'
    p=lambda v:Paragraph(escape(str(v)),styles['BodyText'])
    f=data['faits'];s=data['societe']
    story=[Paragraph('Feuille de calcul documentaire CCA / PCA',styles['Title']),p(s['raison_sociale']),
        p('ICE : '+(s['ice'] or 'à compléter')+' · IF : '+(s['identifiant_fiscal'] or 'à compléter')),
        Spacer(1,12)]
    for label,v in [('Exercice',data['exercice']),('Date de clôture du calendrier',data['date_fin_exercice']),
        ('Type',f['type'].upper()),('Référence déclarée',f['reference']),('Montant déjà comptabilisé',f['montant']+' MAD'),
        ('Base déclarée',{'ht':'HT','ttc':'TTC','autre':'Autre'}[f['base']]),
        ('Période inclusive',f['date_debut']+' au '+f['date_fin']),('Convention choisie','Jours calendaires inclusifs'),
        ('Jours après la clôture / jours totaux',str(data['jours_apres_cloture'])+' / '+str(data['jours_total'])),
        ('Part à reporter',data['montant_reporte']+' MAD'),('Part non reportée par ce calcul',data['montant_non_reporte']+' MAD'),
        ('Arrondi',data['arrondi']),('Libellé proposé',data['libelle_propose']),
        ('Empreinte des données SHA-256',data['empreinte_sha256'])]:
        story += [p(label+' : '+str(v)),Spacer(1,7)]
    story += [Spacer(1,10),p(data['note']),p('Cette empreinte identifie les données ; elle ne constitue ni une signature ni le hash du fichier PDF.')]
    ajouter_logo_pdf(story,societe)
    out=BytesIO()
    def pied(c,doc):c.setFont('Helvetica',8);c.drawString(40,22,'HisabPro · Calcul documentaire interne · Page '+str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=40,
        title='HisabPro — Calcul documentaire CCA / PCA').build(story,onFirstPage=pied,onLaterPages=pied)
    return out.getvalue()


@router.post('/ajustements/calcul-prorata/pdf')
def exporter(data:ExportIn,exercice:Annotated[int,Query(ge=1,le=9999)],
    db:Session=Depends(lecture),user=Depends(get_current_user)):
    faits=ProrataIn.model_validate(data.model_dump(exclude={'empreinte'}))
    doc,s=preparer(db,user['societe_id'],exercice,faits)
    if data.empreinte!=doc['empreinte_sha256']:
        raise HTTPException(409,'Le calendrier ou les données ont changé. Recalculez avant de télécharger.')
    return Response(pdf_bytes(doc,s),media_type='application/pdf',headers={
        'Content-Disposition':f'attachment; filename="calcul_prorata_{exercice}_{faits.type}.pdf"',
        'Access-Control-Expose-Headers':'Content-Disposition'})
