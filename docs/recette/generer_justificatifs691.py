"""Mode d'emploi691 et sources exclusivement fictives, sans connexion de base."""
from pathlib import Path
import hashlib,importlib.util,json
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STEM=HERE/'MODE_EMPLOI_JUSTIFICATIFS_BALANCES_691'


def generer():
    source=HERE/'ETAT_CREANCES_FICTIF691.pdf'
    c=canvas.Canvas(str(source),pagesize=A4)
    c.setTitle('État de créances strictement fictif691')
    c.setFillColorRGB(.09,.37,.65);c.setFont('Helvetica-Bold',16)
    c.drawString(42,790,'HISABPRO — LABORATOIRE FICTIF691')
    c.setFillColorRGB(0,0,0);c.setFont('Helvetica',11)
    textes=[
        'RECETTE ECHEANCES 687 SARL — exercice 2026 — devise MAD',
        'Compte 3421 : créances du jeu de recette, aucune opération réelle.',
        'Solde de la balance : 8 000,00 MAD.',
        'Part à plus d’un an : 2 000,00 MAD.',
        'Part échue : 1 000,00 MAD.',
        'Part à moins d’un an : inconnue, aucune valeur supposée.',
        'Reliquat non qualifié : 8 000 - 2 000 - 1 000 = 5 000,00 MAD.',
        'Ce reliquat n’est pas classé en échues.',
        'Aucune ventilation de devise, d’entreprise liée ou d’effet présumée.',
        'Document pédagogique, sans attestation ou validité fiscale.',
    ]
    for i,t in enumerate(textes):c.drawString(42,750-i*28,t)
    c.save()
    (HERE/'FICHIER_REFUSE_FICTIF691.txt').write_text('Fichier de laboratoire691 pour tester un format refusé. Aucune donnée réelle.\n',encoding='utf8')
    raw=source.read_bytes()
    d={'societe':'RECETTE ECHEANCES 687 SARL','exercice':2026,'devise':'MAD',
       'compte':'3421','solde':'8000.00','plus_un_an':'2000.00','echues':'1000.00',
       'moins_un_an':None,'reliquat_non_qualifie':'5000.00','ecritures_creees':0,
       'source':{'fichier':source.name,'taille':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
       'cas_humains_non_testes':[f'PJD691-{i:02}' for i in range(1,6)]}
    (HERE/'DONNEES_JUSTIFICATIFS691.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    spec=importlib.util.spec_from_file_location('guide691',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=ROOT/'docs/LIASSE_BALANCES_JUSTIFICATIFS_691.md';guide.STEM=STEM
    blocs=guide.blocs();guide.docx(blocs);guide.pdf(blocs)
    wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
    ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
    for i,st in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([st,f'=COUNTIF(Recette!D2:D6,A{i})'])
    ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws=wb.create_sheet('Recette');ws.append(['Identifiant','Module','Objectif','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations'])
    objectifs=['Joindre le PDF fictif et vérifier sa trace sans changer la préparation',
               'Télécharger la pièce et le ZIP, vérifier octets/métadonnées/manifeste',
               'Lecture/mobile et séparation des sociétés',
               'Refuser le TXT sans changer les pièces déjà conservées',
               'Vérifier les pièces associées explicitement à chaque version']
    for i,o in enumerate(objectifs,1):ws.append([f'PJD691-{i:02}','Liasse / justificatifs',o,'Non testé','','','',''])
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(dv);dv.add('D2:D6')
    ws=wb.create_sheet('Données');ws.append(['Objet','Valeur exacte'])
    for k,v in d.items():ws.append([k,json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v])
    ws=wb.create_sheet('Preuves');ws.append(['Identifiant','Fichier / capture réelle','Observations'])
    for i in range(1,6):ws.append([f'PJD691-{i:02}','',''])
    ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
    for ws in wb:
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=50
        for row in ws:
            for cell in row:cell.alignment=Alignment(vertical='top',wrap_text=True)
        if ws.title=='Recette':
            for i in range(2,7):ws.row_dimensions[i].height=75
    wb.save(STEM.with_suffix('.xlsx'))
    return d


if __name__=='__main__':
    generer();print('Documents691 générés : cinq cas humains Non testé, sources fictives uniquement.')
