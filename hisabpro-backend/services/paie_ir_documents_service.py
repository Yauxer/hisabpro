"""Documents privés d'un contrôle annuel existant ; aucun recalcul de paie."""
from io import BytesIO
from pathlib import Path
from html import escape
from fastapi import HTTPException
from sqlalchemy import text
from services import paie_ir_annuel_service as ir,paie_frais_annuels_service as frais,personnel_workflow_service as w
from services.logo_export_service import ajouter_logo_pdf,ajouter_logo_xlsx

NOTE='Contrôle annuel arithmétique interne — pas un bulletin, une déclaration ou une paie définitive. Retenue mensuelle, imputations, montant à déclarer ou verser et net non déterminés. Les données historiques ne sont pas recalculées ; leur applicabilité actuelle reste à examiner.'


def sections(controle,source,societe):
    c=controle['contenu'];f=source['contenu'];q=c['source_frais_annuels'];d=c['declaration']
    valeur=lambda v:'À compléter' if v is None else str(v)
    return {
      'Identite':[['Champ','Valeur'],['Document','Contrôle IR annuel sourcé'],['Société (identité actuelle)',societe['raison_sociale']],['ICE',valeur(societe.get('ice'))],['IF',valeur(societe.get('identifiant_fiscal'))],['Salarié (snapshot)',q['nom']],['Matricule',q['matricule']],['Année',str(c['annee'])],['Contrôle IR',str(controle['id'])],['Empreinte IR SHA256',controle['empreinte']],['Contrôle des frais source',str(source['id'])],['Empreinte frais SHA256',source['empreinte']],['Portée',NOTE]],
      'IR annuel':[['Indicateur','Valeur exacte (MAD sauf personnes)'],['RNI source avant arrondis',q['rni_avant_arrondis']],['Base annuelle arrondie',q['base_annuelle_utilisee']],['IR avant réduction',valeur(c['ir_avant_reduction'])],['Personnes à charge déclarées',valeur(d['personnes_charge'])],['Éligibilité familiale confirmée','Oui' if d['eligibilite_famille_confirmee'] else 'Non'],['Réduction théorique',valeur(c['reduction_theorique'])],['Réduction appliquée',valeur(c['reduction_appliquee'])],['IR annuel arithmétique',valeur(c['ir_annuel_arithmetique'])],['Référence famille',valeur(d['reference_famille'])],['Retenue mensuelle','Non calculée'],['Montant à déclarer ou verser','Non déterminé'],['Net à payer','Non calculé']],
      'Frais annuels':[['Indicateur','Valeur exacte (MAD sauf périodes)'],['Périodes préparées',str(f['nombre_mois'])],['Cumul brut imposable',valeur(f['cumuls']['brut_imposable'])],['Cumul base des frais',valeur(f['cumuls']['base_frais_professionnels'])],['Cotisations salariales déductibles',valeur(f['cumuls']['cotisations_salariales_deductibles'])],['Frais professionnels annuels',valeur(f['frais_professionnels_annuels_arithmetiques'])],['Autres déductions déclarées',valeur(f['autres_deductions_annuelles'])],['Référence du contrôle annuel',f['declaration']['reference_controle_annuel']],['Référence autres déductions',valeur(f['declaration']['reference_autres_deductions'])]],
      'Tranches':[['De (MAD)','À (MAD)','Taux %','Base (MAD)','Impôt arithmétique (MAD)']]+[[t['de'],t['a'] or 'Sans limite',t['taux_pourcent'],t['base'],t['impot_arithmetique']] for t in c['tranches']],
      'Sources mensuelles':[['Période','Préparation fiscale','Simulation sociale','Simulation brute','Empreinte préparation SHA256']]+[[x['periode'],str(x['preparation_id']),str(x['social_id']),str(x['brut_id']),x['empreinte']] for x in f['sources']],
      'Regles et anomalies':[['Objet','Référence'],['Référentiel IR',c['referentiel']['version_interne']],['Empreinte référentiel IR',c['referentiel_sha256']],['Référentiel frais',f['referentiel']['version_interne']],['Empreinte référentiel frais',f['referentiel_sha256']],['Arrondi de base',q['regle_arrondi']['reference']],['Source de l’arrondi',q['regle_arrondi']['url']],['Document SHA256',q['regle_arrondi']['document_sha256']]]+[[x['titre'],x['url']] for x in c['referentiel']['sources']]+[[a['code'],a['message']] for a in c['anomalies']]
    }


def pdf(controle,source,societe):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    styles=getSampleStyleSheet();font=Path('C:/Windows/Fonts/arial.ttf')
    if font.is_file():
        if 'HisabProIR' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('HisabProIR',str(font)))
        for s in styles.byName.values():s.fontName='HisabProIR'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
    p=lambda v,style='BodyText':Paragraph(escape(str(v)),styles[style])
    story=[p('Contrôle IR annuel sourcé','Title'),p(NOTE)]
    for nom,lignes in sections(controle,source,societe).items():
        story.append(p(nom,'Heading2'))
        for ligne in lignes[1:]:
            texte=' · '.join(f'{label} : {v}' for label,v in zip(lignes[0],ligne)) if len(lignes[0])>2 else ' · '.join(str(v) for v in ligne)
            story.extend([p(texte),Spacer(1,4)])
    ajouter_logo_pdf(story,societe);out=BytesIO()
    def pied(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(40,20,'HisabPro - Confidentiel - Controle annuel interne - Page '+str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=40,title='HisabPro - Contrôle IR annuel sourcé',author='HisabPro').build(story,onFirstPage=pied,onLaterPages=pied)
    return out.getvalue()


def xlsx(controle,source,societe):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment,Font,PatternFill
    wb=Workbook();wb.remove(wb.active)
    for nom,lignes in sections(controle,source,societe).items():
        s=wb.create_sheet(nom)
        for ligne in lignes:
            s.append([str(v) for v in ligne])
            for ce in s[s.max_row]:
                ce.data_type='s' # Références et noms : jamais des formules Excel.
                ce.alignment=Alignment(wrap_text=True,vertical='top')
            caracteres=26 if len(lignes[0])>2 else 45
            s.row_dimensions[s.max_row].height=min(409,max(35,(max((len(str(v))+caracteres-1)//caracteres for v in ligne)+1)*16))
        for ce in s[1]:ce.font=Font(bold=True,color='FFFFFF');ce.fill=PatternFill('solid',fgColor='24589C')
        for col in s.columns:s.column_dimensions[col[0].column_letter].width=38 if len(lignes[0])>2 else 65
        s.freeze_panes='B2';s.auto_filter.ref=s.dimensions
    ajouter_logo_xlsx(wb,societe);out=BytesIO();wb.save(out);return out.getvalue()


@w.transaction
def exporter(db,user,ident,format):
    controle=ir.lire(db,user,ident);q=controle['contenu'].get('source_frais_annuels')
    if q is None:raise HTTPException(409,'Ce document exige un contrôle IR relié à son RNI annuel constitué.')
    source=frais.lire(db,user,q['id'])
    if source['empreinte']!=q['empreinte']:raise HTTPException(409,'Source du document incohérente.')
    societe=dict(db.execute(text('SELECT raison_sociale,ice,identifiant_fiscal,logo_url FROM societes WHERE id=:s'),{'s':user['societe_id']}).mappings().one())
    if format not in {'pdf','xlsx'}:raise HTTPException(422,'Format PDF ou Excel requis.')
    contenu=(pdf if format=='pdf' else xlsx)(controle,source,societe)
    dossier=w.dossier(db,user['societe_id'],q['employe_id'])
    w.evenement(db,user,dossier,'CONTROLE_IR_EXPORTE',f'Contrôle IR #{ident} ; source frais #{source["id"]} ; format {format} ; empreinte {controle["empreinte"]}')
    return contenu
