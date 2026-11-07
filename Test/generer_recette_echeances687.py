"""Complément de recette687, données fictives et résultats humains vierges."""
from pathlib import Path
import csv,importlib.util,json
from openpyxl import Workbook
from openpyxl.styles import Alignment,Font,PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/recette'
NOM='RECETTE_ECHEANCES_BALANCES_687'
COLONNES=['Identifiant','Objectif','Prérequis','Données exactes','Actions dans l’interface',
          'Résultat attendu','Écritures attendues','Impact fiscal','Contrôles','Statut humain',
          'Résultat réel','Anomalies','Preuve attendue','Preuve réelle','Observations']


def jeu():
    return {'societe':'RECETTE ECHEANCES 687 SARL','devise':'MAD','exercice':2026,
        'lignes':[{'compte':'1111','debit':'0.00','credit':'6000.00'},
                  {'compte':'3421','debit':'8000.00','credit':'0.00'},
                  {'compte':'4411','debit':'0.00','credit':'3000.00'},
                  {'compte':'5141','debit':'1000.00','credit':'0.00'}],
        'oracle':{'debit':'9000.00','credit':'9000.00','actif':'9000.00','passif':'9000.00','cpc':'0.00',
                  'v2_B6_ventile':'3000.00','v2_B6_reliquat':'5000.00',
                  'v3_B7_ventile':'3000.00','v3_B7_reliquat':'0.00','ecritures_creees':0}}


def cas():
    donnees=jeu();societe=donnees['societe'];res=[]
    def add(n,objectif,data,actions,attendu):
        res.append([f'BAL687-{n:02}',objectif,'Base isolée fictive, administrateur et application fournis par le technicien ; cas précédents terminés.',
            data,actions,attendu,'Aucune écriture ; le Journal de cette société reste vide.',
            'Aucune liquidation, déclaration ou preuve de dépôt créée.',
            'Comparer les montants et les versions ; conserver la capture/export indiqué.',
            'Non testé','','','Capture d’écran et fichiers exportés lorsqu’indiqués.','',''])
    add(1,'Créer la préparation de base',societe+' ; MAD ; exercice2026 ouvert, du01/01 au31/12 ; BALANCE_FICTIVE_ECHEANCES687.csv.',
        'Créer cette société distincte et vérifier les quatre comptes du CSV dans son plan. Comptabilité → Liasse fiscale → Importer N / N-1 : joindre le CSV en Balance N, sans N-1 ; Contrôler et préparer puis Conserver une nouvelle version. Relever version1 et empreinte.',
        '4 comptes ; D=C 9000 MAD ; actif/passif 9000 ; CPC 0 ; N-1 indisponible. Version 1 créée sans écriture.')
    add(2,'Vérifier les inconnus initiaux','Version1 ; créance3421=8000 ; dette4411=3000.',
        'Ouvrir Compléter les échéances documentaires des balances. Choisir B6 ·3421 puis B7 ·4411 dans Compte à documenter. Examiner les sept champs.',
        'Champs vides/Inconnu ; reliquats 8000 et 3000. Aucun classement automatique en échues ; aucun tiers ni calendrier supposé.')
    add(3,'Conserver la partie certaine des créances','B6/3421 : Plus d’un an2000 ; Échues1000 ; justification ETAT CLIENTS FICTIF687 ; autres champs laissés vides.',
        'Sélectionner B6 ·3421, saisir les deux montants et la justification. Confirmer les données documentaires puis Conserver les compléments dans une nouvelle version. Ouvrir à nouveau le panneau après sélection automatique de version2.',
        'Version2 liée à version1 par empreinte. Total8000, ventilé3000, reliquat5000. Moins d’un an et analyses complémentaires restent inconnus. Bilan/CPC et sources inchangés.')
    add(4,'Ajouter les échéances des dettes','B7/4411 : Plus d’un an1000 ; Moins d’un an1000 ; Échues1000 ; État/organismes publics0 ; justification ETAT FOURNISSEURS FICTIF687.',
        'Depuis version2, ouvrir le panneau et choisir B7 ·4411. Saisir les quatre montants indiqués sans remplir les autres analyses ; confirmer puis conserver une nouvelle version.',
        'Version 3 ; B7 ventilé 3000/reliquat 0, analyse État=0 explicite ; devises/entreprises liées/effets inconnus. B6 conserve 2000/1000 et reliquat 5000.')
    add(5,'Refuser un dépassement sans perdre la saisie','Depuis version3, B6/3421 : remplacer Échues1000par7000 ; conserver Plus d’un an2000.',
        'Saisir7000, confirmer puis tenter de conserver. Lire l’alerte. Revenir à1000sans enregistrer une nouvelle version.',
        'Rejet : 9000 ventilés dépasseraient le solde 8000. Les champs restent visibles pour correction ; version 3 et le Journal sont inchangés.')
    add(6,'Exporter et vérifier la version3','Version3 ; logo fictif si fourni par le technicien.',
        'Fermer le panneau si nécessaire, puis Exporter la préparation Excel et PDF. Ouvrir les fichiers. Comparer les rubriques, sources, version/empreinte, échéances, reliquats, justification et analyses complémentaires.',
        'PDF/XLSX cohérents : B6 reliquat 5000, B7 reliquat 0, champs inconnus identifiés. Parent version 2 et son empreinte présents. Aucun document présenté comme ETIC officielle complète ou prêt à déposer. Logo actuel si configuré.')
    add(7,'Préserver les anciennes versions et le rôle Lecture','Compte fictif lecture687@example.com, rôleLecture, mot de passe de laboratoire Recette687!2026.',
        'En administrateur, rouvrir version 1 et vérifier ses champs inconnus, puis version 2 avec B7 encore inconnu. Créer le lecteur indiqué depuis Administration → Utilisateurs. Se connecter avec ce lecteur, choisir version 3, ouvrir le panneau et télécharger les exports.',
        'Anciennes versions inchangées. Lecture peut consulter/exporter ; champs désactivés et aucune commande de conservation. Bilan 9000/CPC 0 et Journal vide. Recette humaine toujours à renseigner dans ce classeur.')
    return res


def generer(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);d=jeu();rows=cas()
    with (out/'BALANCE_FICTIVE_ECHEANCES687.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['compte','debit','credit'],delimiter=';');w.writeheader();w.writerows(d['lignes'])
    (out/'DONNEES_RECETTE_ECHEANCES687.json').write_text(json.dumps({**d,'cas':rows},ensure_ascii=False,indent=2),encoding='utf8')
    paragraphs=['# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO','Version 1 du 21 octobre 2026',
        'Complément687 — échéances documentaires des balances importées',
        'Mode d’emploi pour les fonctions disponibles. Sept cas humains Non testé ; aucun résultat humain prérempli. RH/paie et recette utilisateur différées. Production non validée.',
        '## Préparation du laboratoire',
        'Un technicien fournit une base isolée et un compte administrateur fictif. Ne pas utiliser une société ou une base comptable réelle. Aucun SQL supplémentaire requis : la chaîne071 des préparations immuables doit déjà être présente. Les tests techniques récents utilisent un schéma103 isolé.',
        'La ventilation est documentée à la date de fin de la période conservée ; la personne chargée de la recette choisit les montants du jeu, sans transformer une date de facture en échéance. Les champs vides restent inconnus ; zéro n’est conservé que s’il est saisi. Les analyses complémentaires peuvent se recouper : ne pas les additionner.',
        '## Calculs attendus indépendants',
        'Balance fictive : 8000 de créances 3421 + 1000 en banque 5141 = 9000 actif ; 6000 capital 1111 + 3000 dettes 4411 = 9000 passif ; aucun compte de résultat, CPC 0. Après la première ventilation : 2000 + 1000 = 3000 qualifiés sur 8000, reliquat 5000. Dette : 1000 + 1000 + 1000 = 3000, reliquat 0. Chaque complément crée une version documentaire, zéro écriture.']
    for row in rows:
        paragraphs += ['## '+row[0]+' — '+row[1]]+[k+' : '+str(v or 'À renseigner par la personne chargée de la recette.') for k,v in zip(COLONNES[2:],row[2:])]
    paragraphs += ['## Limites','Le panneau ne constitue pas une ETIC officielle complète. Il ne renseigne ni liquidation, ni tableau de financement, ni modèle DGI, ni annexe EDI. Les soldes de sens inverse restent visibles et non ventilables dans cette préparation. Les sources absentes des anciennes versions ne sont pas reconstituées. Les états et les balances conservés ne sont pas recalculés.']
    import re
    prose='\n\n'.join(paragraphs)+'\n'
    prose=prose.replace('Complément687', 'Complément 687').replace('chaîne071', 'chaîne 071').replace('schéma103', 'schéma 103')
    prose=prose.replace('du01/01 au31/12', 'du 01/01 au 31/12').replace('par7000', 'par 7000').replace('à1000', 'à 1000')
    prose=re.sub(r'(?<=\d)(MAD|et\b|de\b|en\b|actif|passif|capital|dettes|qualifiés|par\b|sans\b|explicite)',r' \1',prose)
    prose=re.sub(r'\b(année|exercice|cas|compte|créance|dette|capital|actif|passif|CPC|B6|B7|reliquat|ventilés|sur|Échues|État|an|version)(?=\d)',r'\1 ',prose,flags=re.I)
    md=out/(NOM+'.md');md.write_text(prose,encoding='utf8')
    spec=importlib.util.spec_from_file_location('guide687',ROOT/'docs/guide/generer_guide.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    g.SOURCE=md;g.STEM=out/NOM;blocs=g.blocs();g.docx(blocs);g.pdf(blocs)
    wb=Workbook();ws=wb.active;ws.title='Synthèse';wb.calculation=CalcProperties(fullCalcOnLoad=True)
    ws.append(['Statut humain','Nombre']);
    for i,st in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([st,f'=COUNTIF(Recette!J2:J8,A{i})'])
    ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws=wb.create_sheet('Recette');ws.append(COLONNES)
    for row in rows:ws.append(row)
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(dv);dv.add('J2:J8')
    ws=wb.create_sheet('Oracle');ws.append(['Contrôle','Valeur exacte'])
    for k,v in d['oracle'].items():ws.append([k,str(v)])
    ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
    ws=wb.create_sheet('Preuves');ws.append(['Cas','Preuve réelle','Observations'])
    for row in rows:ws.append([row[0],'',''])
    for ws in wb:
        ws.freeze_panes='C2' if ws.title=='Recette' else 'A2';ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=75 if ws.title=='Recette' else 40
        for row in ws:
            for c in row:
                c.alignment=Alignment(wrap_text=True,vertical='top')
                if isinstance(c.value,str) and not c.value.startswith(('=COUNTIF','=IF')):c.data_type='s'
        if ws.title=='Recette':
            for i in range(2,9):ws.row_dimensions[i].height=150
    wb.save(out/(NOM+'.xlsx'))
    return d,rows


if __name__=='__main__':
    generer();print('Recette687 generee :7cas humains Non teste.')
