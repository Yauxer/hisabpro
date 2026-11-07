"""Guide consolidé ETIC697–701 et suivi humain, sans connexion à la base."""
from pathlib import Path
from copy import copy
import importlib.util,re,csv,json,hashlib
from decimal import Decimal
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from openpyxl.formatting.rule import DataBarRule

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STEM=HERE/'GUIDE_RECETTE_ETIC_697_701'
MODULES=[('B8-B9','Sûretés et engagements',ROOT/'docs/LIASSE_BALANCES_TABLEAUX_ETIC_697.md','MODE_EMPLOI_TABLEAUX_ETIC_697'),
         ('Annexes','Autres annexes manuelles',ROOT/'docs/LIASSE_BALANCES_ANNEXES_ETIC_699.md','MODE_EMPLOI_ANNEXES_ETIC_699'),
         ('Capital','Contrôles arithmétiques du capital',ROOT/'docs/LIASSE_BALANCES_CONTROLES_CAPITAL_701.md','MODE_EMPLOI_CONTROLES_CAPITAL_701')]



def verifier_donnees():
    data=json.loads((HERE/'DONNEES_ETIC_SESSION701.json').read_text(encoding='utf8'))
    def lire(cle):
        with (HERE/data['balances'][cle]).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
    n,n1=lire('n'),lire('n1')
    for rows,attendu in [(n,Decimal('17000')),(n1,Decimal('6000'))]:
        assert sum(Decimal(r['debit']) for r in rows)==sum(Decimal(r['credit']) for r in rows)==attendu
    assert {r['compte'] for r in n}=={'1111','1481','2332','3421','5141','6132','7111'}
    lignes={r['compte']:r for r in n}
    produits=Decimal(lignes['7111']['credit'])-Decimal(lignes['7111']['debit'])
    charges=Decimal(lignes['6132']['debit'])-Decimal(lignes['6132']['credit'])
    capital=Decimal(lignes['1111']['credit'])-Decimal(lignes['1111']['debit'])
    actif=sum(Decimal(lignes[k]['debit'])-Decimal(lignes[k]['credit']) for k in ('2332','3421','5141'))
    dettes=Decimal(lignes['1481']['credit'])-Decimal(lignes['1481']['debit'])
    assert produits-charges==Decimal('800') and actif==capital+dettes+produits-charges==Decimal('15800')
    assert capital==Decimal('10000') and produits==Decimal('2000') and charges==Decimal('1200')
    tableaux={r['code']:r for r in data['annexes']}
    c=tableaux['C1']['lignes'][0]
    assert Decimal(c['titres'])*Decimal(c['nominal'])==Decimal(c['capital'])==capital and Decimal(c['pourcentage'])==100
    assert Decimal(tableaux['B10']['lignes'][0]['redevances_exercice'])==charges
    assert Decimal(tableaux['C4']['lignes'][0]['ventes'])==produits
    for nom,preuve in data['fichiers'].items():
        raw=(HERE/nom).read_bytes();assert len(raw)==preuve['taille'] and hashlib.sha256(raw).hexdigest()==preuve['sha256']


def generer():
    verifier_donnees()
    texte='''# MODE D’EMPLOI ET RECETTE — AVANCÉES ETIC HISABPRO

Version 1 du 21 octobre 2026 — lots 697/699/701, hors RH et paie.

Ce guide réunit les trois modes d’emploi de cette session. Il couvre les huit
schémas de tableaux manuels déjà définis dans le catalogue HisabPro et les
contrôles arithmétiques du capital déclaré. Ce n’est pas le cahier de recette
complet de toute l’application ; les autres domaines conservent leurs cahiers.
La liasse indépendante complète et les formalités officielles restent partielles.

## Parcours conseillé

Utiliser une société fictive en MAD et un exercice 2026 dans une base de test
autorisée. Ne pas effectuer ces essais dans un dossier comptable réel.
Importer BALANCE_FICTIVE_ETIC701_N.csv et BALANCE_FICTIVE_ETIC701_N1.csv,
puis conserver une préparation. Les fichiers existent dans ce même dossier.

Compléter d’abord B8/B9 et conserver. Compléter ensuite les six autres annexes
et conserver : les blocs précédents sont repris depuis la version sélectionnée.
La version courante calcule alors les contrôles C1 à sa conservation ; consulter
ces contrôles avant de télécharger le dossier. Conserver chaque formulaire
avant de passer à une modification dans un autre formulaire ou de relire une
ancienne version. Le nombre exact de versions dépend de vos conservations.

Les montants et sources ci-dessous sont exclusivement fictifs. Les inconnus
ne deviennent pas zéro ; un néant est une déclaration explicite et justifiée.
Une version conservée n’est jamais modifiée par ces formulaires. Une pièce
jointe reste propre à sa version et n’est pas copiée automatiquement.

Les PDF/Excel/ZIP utilisent l’identité et le logo actuels, hors empreinte
historique. Le ZIP contient les sources et un manifeste SHA-256. Aucun export
ne crée d’écriture, de liquidation, de preuve de dépôt ou de certification.

## Suivre la recette dans Excel

Le classeur associé comporte une synthèse, une feuille par domaine, les sources,
les preuves et les anomalies. Pour chaque cas, renseigner statut humain,
résultat réel, anomalie et preuve. Les seize cas sont initialement Non testé.
Les formules et barres de progression sont recalculées à l’ouverture dans Excel.
Les réussites des tests automatisés sont documentées séparément dans Test et
ne remplissent pas les résultats de votre propre recette.

'''
    wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True)
    ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
    bornes={}
    for nom,titre,source,stem in MODULES:
        corps=source.read_text(encoding='utf8').splitlines()
        texte+='\n## '+titre+'\n\n'
        for line in corps:
            if line.startswith('# ') or line.startswith('Version '):continue
            if line.startswith('## '):line='#'+line
            texte+=line+'\n'
        src=load_workbook(HERE/(stem+'.xlsx'))['Recette'];dest=wb.create_sheet(nom)
        for row in src:
            for c in row:
                d=dest.cell(c.row,c.column,c.value)
                d.font=copy(c.font);d.fill=copy(c.fill);d.border=copy(c.border)
                d.alignment=copy(c.alignment);d.protection=copy(c.protection);d.number_format=c.number_format
        n=dest.max_row;bornes[nom]=n
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');dest.add_data_validation(dv);dv.add(f'D2:D{n}')
        for i in range(2,n+1):
            assert dest.cell(i,4).value=='Non testé'
            assert all(dest.cell(i,j).value is None for j in range(5,8))
            dest.row_dimensions[i].height=150
    texte=texte.replace('BALANCE_FICTIVE_FINANCEMENT695_N.csv','BALANCE_FICTIVE_ETIC701_N.csv').replace('BALANCE_FICTIVE_FINANCEMENT695_N1.csv','BALANCE_FICTIVE_ETIC701_N1.csv')
    texte=texte.replace('Utiliser la société fictive en MAD et les balances 695 décrites dans le guide 699.', 'Utiliser la société fictive en MAD et les deux balances du présent guide consolidé.')
    texte=texte.replace('## Parcours conseillé', 'Les chiffres du parcours consolidé sont regroupés dans DONNEES_ETIC_SESSION701.json. La balance N comporte la charge de crédit-bail de 1 200 MAD, déjà prévue dans B10, et une banque de 6 800 MAD. Résultat et CAF N attendus : 800 MAD. Les guides unitaires conservent leurs jeux de saisie propres ; pour ce parcours suivre les deux CSV ETIC701.\n\n## Parcours conseillé')
    STEM.with_suffix('.md').write_text(texte,encoding='utf8')
    ws=wb['Synthèse']
    for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):
        terms=','.join(f'COUNTIF(\'{nom}\'!D2:D{n},A{i})' for nom,n in bornes.items())
        ws.append([statut,'=SUM('+terms+')'])
    ws.append(['Avancement','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws.append(['Cas prévus',16]);ws.append(['Portée','Recette humaine, aucune conformité officielle présumée'])
    ws.append(['Domaine','Total','Non testé','Réussi','Échoué','Bloqué','Avancement'])
    for i,(nom,n) in enumerate(bornes.items(),10):
        ws.append([nom,f'=COUNTA(\'{nom}\'!A2:A{n})',
            *[f'=COUNTIF(\'{nom}\'!D2:D{n},"{statut}")' for statut in ['Non testé','Réussi','Échoué','Bloqué']],
            f'=IF(B{i}=0,0,D{i}/B{i})'])
        ws[f'G{i}'].number_format='0%'
    ws.conditional_formatting.add('G10:G12',DataBarRule(start_type='num',start_value=0,end_type='num',end_value=1,color='185FA5'))
    ws=wb.create_sheet('Sources');ws.append(['Fichier / information','Usage'])
    for f,usage in [('BALANCE_FICTIVE_ETIC701_N.csv','Débit = crédit 17 000 MAD ; capital 10 000 MAD ; produits 2 000 MAD ; charges 1 200 MAD ; résultat/CAF 800 MAD ; banque 6 800 MAD'),
                    ('BALANCE_FICTIVE_ETIC701_N1.csv','Débit = crédit 6 000 MAD'),
                    ('DONNEES_ETIC_SESSION701.json','Référence consolidée : tableaux, charges, résultats et contrôles indépendants'),
                    ('DONNEES_TABLEAUX_ETIC697.json','Jeu unitaire B8/B9'),
                    ('DONNEES_ANNEXES_ETIC699.json','Six annexes, capital : 100 titres × 100 MAD = 10 000 MAD, 100 %'),
                    ('DONNEES_CONTROLES_CAPITAL701.json','Trois variantes de contrôles et attendus indépendants'),
                    ('Logo','Configurer une image fictive dans les paramètres de la société de test'),
                    ('Statut','Seize cas Non testé ; aucun résultat humain déduit des automatismes')]:ws.append([f,usage])
    ws=wb.create_sheet('Preuves');ws.append(['ID','Domaine','Fichier / capture réelle','Observations'])
    for nom,n in bornes.items():
        for i in range(2,n+1):ws.append([wb[nom].cell(i,1).value,nom,'',''])
    ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
    for ws in wb:
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=48
        for row in ws:
            for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
    for col,width in {'A':42,'B':16,'C':14,'D':14,'E':14,'F':14,'G':18}.items():
        wb['Synthèse'].column_dimensions[col].width=width
    for c in wb['Synthèse'][9]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
    for nom in bornes:
        wb[nom].freeze_panes='B2'
        for col,width in {'A':14,'B':60,'C':60,'D':18,'E':42,'F':42,'G':42,'H':45}.items():wb[nom].column_dimensions[col].width=width
    for nom,widths in [('Sources',{'A':58,'B':90}),('Preuves',{'A':14,'B':16,'C':85,'D':70}),('Anomalies',{'A':12,'B':14,'C':70,'D':70,'E':16})]:
        for col,width in widths.items():wb[nom].column_dimensions[col].width=width
    wb.save(STEM.with_suffix('.xlsx'))
    spec=importlib.util.spec_from_file_location('guide_session_etic',ROOT/'docs/guide/generer_guide.py')
    guide=importlib.util.module_from_spec(spec);spec.loader.exec_module(guide)
    guide.SOURCE=STEM.with_suffix('.md');guide.STEM=STEM;blocs=guide.blocs()
    word_orig=guide.word_table;largeurs={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    guide.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+largeurs[m[1]]+'"',word_orig(rows))
    guide.docx(blocs);table_orig=guide.Table
    guide.Table=lambda rows,**kw:table_orig(rows,**{**kw,'colWidths':[24*guide.mm,64*guide.mm,63*guide.mm,19*guide.mm]})
    guide.pdf(blocs)


if __name__=='__main__':
    generer();print('Guide consolidé Word/PDF et Excel7feuilles/seize cas humains Non testé générés.')
