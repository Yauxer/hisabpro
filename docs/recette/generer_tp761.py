"""Jeu pédagogique et recette tp761 ; aucun accès DB ou calcul fiscal."""
from pathlib import Path
from decimal import Decimal as D
from copy import deepcopy
from uuid import uuid4
import ast,json,importlib.util,re
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.properties import CalcProperties
from reportlab.pdfgen import canvas
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

INTRO='# MODE D’EMPLOI ET RECETTE — TAXE PROFESSIONNELLE HISABPRO\n\nVersion 1 du 23 octobre 2026. Lot761 : préparation interne et simulation brute sur bases et classes fournies.\n\n## Fonction et limites\n\nLe formulaire conserve un profil annuel et des établissements avec valeurs locatives, classes et avis explicitement sourcés. Il calcule un brut arithmétique et compare les avis fournis, sans calculer une imposition, un montant dû, une échéance ou un paiement. Aucune écriture ni immobilisation n’est créée/modifiée. Les modèles administratifs ne sont pas intégrés.\n\nLes taux normaux C3=10%,C2=20%,C1=30% ont été lus dans les extraits officiels indexés du guideDGCT2024,page120,article9-I. Les noticesDGCT07-20/14-25 ont été consultées. Les PDF complets ont rencontré des timeouts/cachemiss ; aucune lecture intégrale ou empreinte binaire n’est revendiquée. Le référentiel applicable et la situation réelle doivent être revus sur pièces. Ni la VL ni la classe ne sont déduites d’un loyer, compte ou valeur nette amortie.\n\nLe brut n’applique pas automatiquement les règles de base de l’article7, exonérations/réductions, hôtel, prorata, droit minimum, franchise ou émission. Un brut inférieur à200MAD n’est pas rendu artificiellement nul ou présenté comme dû. Sans local ou sans ligne, aucune taxe nulle n’est déduite. Arrondi HALF_UP au centime par établissement : convention documentaire, pas arrondi légal validé ; le calcul exact est conservé.\n\n## Prérequis et accès\n\nInstaller les fichiers du ZIP différentiel sur environnement de test avec l’arborescence exacte et redémarrer les services habituels. Aucune migration nouvelle, conserver le socle des préparations104. Société fictive MAD, rôles admin/comptable ou lecture pour consultation. RH/paie restent hors périmètre.\n\nOuvrir Comptabilité → Liasse fiscale → mode Liasse seule, importer/conserver une balance fictive ou sélectionner une préparation existante. Les CSV755 peuvent servir de support technique. Les bases ci-dessous sont fictives et indépendantes de ces balances : aucune qualification TP réelle n’est attestée. Ouvrir « Préparer la taxe professionnelle » puis « Rubrique TP à documenter ».\n\nChoisir successivement TP-P et TP-E, codes internes. Dans chaque rubrique choisir Saisie documentée — à revoir, saisir justification puis lignes exactes ci-dessous. Les deux rubriques sont conservées ensemble. Une année TP2026 est explicitement saisie, distincte de la période comptable importée ; les références sont fictives.\n\n## Données exactes à saisir\n\nTous les noms, activités, classes, bases et avis sont pédagogiques. Aucune classe de métier réelle n’est affirmée. Les confirmations sont celles du jeu fictif, pas une validation d’un dossier fiscal réel.\n\n'
SUITE='## Conserver et vérifier\n\nCocher « Je confirme les données et déclarations saisies, sans valider une liasse complète » puis « Conserver la préparation TP dans une nouvelle version ». Rouvrir le formulaire : version actualisée sans F5, contrôles conservés.\n\nOracles indépendants : A30000×20%=6000 ; B12000×10%=1200 ; brut7200MAD. Avis fournis6200+1200=7400MAD. Écart brut−avis=−200MAD, visible sans modifier l’avis ni la comptabilité. L’avis reste une donnée déclarée, aucune émission ou imposition n’est confirmée.\n\nModifier seulement le brouillon ne modifie pas les contrôles conservés. Un champ VL vide laisse le brut indisponible, jamais zéro. Une classe, base, situation de janvier ou régime non revu laisse le brut qualifié global indisponible même si un calcul arithmétique existe. Hors2026 ou année différente de la préparation, aucune proposition globale qualifiée.\n\n## Erreurs, avis et situations particulières\n\nSaisir NaN/Infinity, négatif direct ou précision de plus de deux décimales : refus sans nouvelle version, brouillon gardé. Dupliquer un identifiant interne d’établissement : refus. Même avis référencé sur deux établissements : montants conservés, total global des avis inconnu, alerte contre double addition sans ventilation justifiée.\n\nVider la référence d’avis ou le rattachement à l’année : avis non comparable, aucune date d’échéance supposée. Une différence avec le brut n’est pas une erreur comptable à réparer automatiquement. Une situation particulière reste à qualifier sans perte de données.\n\nPour tester le brut faible, sur copie choisir C3 etVL100 pourA : brutA10 et total1210, sans montant dû ou exonération déduit. Pour l’arrondi documentaire, C3/VL0,05 donne exact0,005 et centime0,01 ; aucun arrondi fiscal officiel validé.\n\n## Exports et justificatifs\n\nTélécharger le dossier ZIP de la version. Contrôler JSON TP, PDF, Excel et manifeste SHA256. Feuilles TP-P/TP-E, Simulation brute TP et revue établissements ; valeurs7200/7400/−200 et sources concordantes ; logo dans PDF/Excel. Le calcul exact et les points à revoir restent exportés. Les autres compléments et versions historiques sont préservés.\n\nJoindre JUSTIFICATIFS_FICTIFS_TP761.pdf depuis les justificatifs complémentaires si souhaité. Il n’a aucune valeur fiscale réelle. Consulter la version précédente et conserver les captures/fichiers de preuve. Le suivi Excel reste vierge jusqu’à exécution humaine ; les formules Office doivent être recalculées dans Office.\n\n## Cas de recette utilisateur\n\n| ID | Actions | Résultat attendu et preuve | Statut |\n|---|---|---|---|\n|TP761-01|Ouvrir une préparation fictive MAD et les rubriques TP-P/TP-E.|Accès lisible et limites visibles, codes internes et source DGCT indiqués. Capture accès.|Non testé|\n|TP761-02|Saisir exactement profil et deux établissements, confirmer puis conserver.|Nouvelle version, VL42000, brut7200, avis7400, écart−200, aucun dû confirmé. Capture contrôles/version.|Non testé|\n|TP761-03|Sur copie, vider la VL puis retirer la revue de base ; conserver des versions séparées.|Brut inconnu si VL manque ; brut arithmétique connu mais proposition globale indisponible si revue manque. Captures des états.|Non testé|\n|TP761-04|Saisir NaN et Infinity dans la VL et tenter de conserver ; corriger ensuite30000.|Refus sans version parasite ou écriture ; brouillon gardé et reprise sans F5. Captures refus/reprise.|Non testé|\n|TP761-05|Sur copie, dupliquer l’identifiant établissement puis partager la référence d’avis entre deux lignes.|Doublon établissement refusé ; avis partagé signalé et total des avis inconnu sans double addition. Captures références.|Non testé|\n|TP761-06|Sur copie, testerA C3/VL100 puis C3/VL0,05 ; consulter l’ancien état.|BrutsA10 puis0,01 avec exact0,005 conservé ; aucun dû/exonération déduit. Ancienne version intacte. Captures/exports.|Non testé|\n|TP761-07|Tester lecture, comptable390px et accès d’une autre société.|Lecture ne conserve pas, comptable autorisé, autre société refusée ; écran lisible. Captures rôles/mobile.|Non testé|\n|TP761-08|Télécharger ZIP et vérifier PDF/Excel/JSON/manifeste/logo ; joindre pièce fictive puis consulter l’ancienne version.|Sources et montants concordants, pièce traçable ; autres compléments et version antérieure intacts. Conserver fichiers/preuves.|Non testé|\n\n## Limites et suite\n\nHuit cas Non testé humainement. La simulation brute normale est disponible ; taxation complète, régime particulier, base réglementaire calculée, modèle administratif et dépôt restent à qualifier. Recette cible/Office et imposition réelle non validées. Aucun PostgreSQL réel utilisé ; RH/paie etpoint6 différés.\n'

def generer():
    # Extraire uniquement les fonctions pures évite tout import de fixtures/DB.
    t=ast.parse((R/'Test/tp761_support.py').read_text(encoding='utf8'))
    fn=next(a for a in t.body if isinstance(a,ast.FunctionDef) and a.name=='body')
    ns={'uuid4':uuid4,'NORMAL':'Établissement avec local — hors régime particulier, exonération et réduction'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'jeu_fictif','exec'),ns)
    b=ns['body']({'empreinte_sha256':'a'*64})
    data={'societe':'DOSSIER PEDAGOGIQUE TP761','exercice':2026,'tables':b['tables'],'attendus':{'valeur_locative':'42000.00','brut':'7200.00','avis':'7400.00','ecart':'-200.00'},'imposition_confirmee':False,'fictif':True,'statut_humain':'Non testé'}
    assert data['tables'][1]['lignes'][0]['classe']=='C2' and data['tables'][1]['lignes'][1]['classe']=='C3'
    assert D('30000')*D('20')/100+D('12000')*D('10')/100==D('7200')
    assert D('6200')+D('1200')==D('7400') and D('7200')-D('7400')==D('-200')
    (HERE/'DONNEES_TP761.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    t=ast.parse((R/'hisabpro-backend/services/balance_taxe_professionnelle_service.py').read_text(encoding='utf8'))
    fn=next(a for a in t.body if isinstance(a,ast.FunctionDef) and a.name=='catalogue')
    ns={'deepcopy':deepcopy,'BLOC':'taxe_professionnelle_documentaire'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'labels','exec'),ns)
    catalogue=ns['catalogue']({'contenu':{}})
    pdf=canvas.Canvas(str(HERE/'JUSTIFICATIFS_FICTIFS_TP761.pdf'),invariant=1)
    texte=INTRO
    for t,cat in zip(data['tables'],catalogue):
        texte+='### '+t['code']+' — '+cat['titre']+'\n\nJustification du tableau : '+t['justification']+'\n\n'
        pdf.setFont('Helvetica-Bold',13);pdf.drawString(35,805,'HISABPRO - SOURCES FICTIVES TP761')
        pdf.setFont('Helvetica',9);pdf.drawString(35,785,'Aucune valeur fiscale reelle - aucun paiement ou depot valide');y=760
        for i,m in enumerate(t['lignes'],1):
            texte+='Ligne '+str(i)+' :\n\n'+'\n'.join('- '+c['label']+' = '+str(m.get(c['cle']) or '(laisser vide)') for c in cat['colonnes_saisie'])+'\n- Référence de source de la ligne = '+m['reference_source']+'\n\n'
            for line in [*[c['label']+' : '+str(m.get(c['cle'],'')) for c in cat['colonnes_saisie']],'Reference source : '+m['reference_source'],'']:
                if y<60:pdf.showPage();y=800;pdf.setFont('Helvetica',9)
                for chunk in [line[j:j+105] for j in range(0,len(line),105)] or ['']:
                    pdf.drawString(35,y,chunk);y-=13
        pdf.showPage()
    pdf.save();texte+=SUITE;source=R/'docs/LIASSE_TAXE_PROFESSIONNELLE_761.md';source.write_text(texte,encoding='utf8')
    spec=importlib.util.spec_from_file_location('guide759',R/'docs/guide/generer_guide.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    g.SOURCE=source;g.STEM=HERE/'MODE_EMPLOI_TP761';blocs=g.blocs();orig=g.word_table;widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    g.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows));g.docx(blocs);table=g.Table
    g.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*g.mm,64*g.mm,63*g.mm,19*g.mm]});g.pdf(blocs)
    cas=[[c.strip() for c in l.strip('|').split('|')] for l in texte.splitlines() if l.startswith('|TP761-')];assert len(cas)==8
    wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True);ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
    for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Fiscalité!K2:K9,A{i})'])
    ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws=wb.create_sheet('Fiscalité');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
    for ident,action,attendu,statut in cas:ws.append([ident,'Préparation TP brute',action,'Société fictive MAD ; préparation conservée ; guide761 ; rôles dédiés','DONNEES_TP761.json et guide champ par champ',action,attendu,'Aucune écriture créée ou modifiée','Brut7200/avis7400/écart−200 ; aucun dû ou dépôt validé',attendu,statut,'','','','','Captures/fichiers demandés au résultat attendu'])
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(dv);dv.add('K2:K9')
    ws=wb.create_sheet('Données exactes');ws.append(['Rubrique','Ligne','Champ','Valeur exacte'])
    for t,cat in zip(data['tables'],catalogue):
        ws.append([t['code'],'','Justification',t['justification']])
        for i,m in enumerate(t['lignes'],1):
            for c in cat['colonnes_saisie']:ws.append([t['code'],i,c['label'],m.get(c['cle'],'')])
            ws.append([t['code'],i,'Référence source',m['reference_source']])
    ws=wb.create_sheet('Calculs indépendants');ws.append(['Montant','Oracle MAD','Formule Excel à recalculer'])
    for a,b,c in [('VLtotale',42000,'=30000+12000'),('BrutA',6000,'=30000*20%'),('BrutB',1200,'=12000*10%'),('Bruttotal',7200,'=6000+1200'),('Avistotal',7400,'=6200+1200'),('Écartbrutmoinsavis',-200,'=7200-7400')]:ws.append([a,b,c])
    ws=wb.create_sheet('Preuves');ws.append(['ID','Preuve réelle','Observations'])
    for c in cas:ws.append([c[0],'',''])
    ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
    for ws in wb:
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42
        for row in ws:
            for cell in row:cell.alignment=Alignment(wrap_text=True,vertical='top')
    wb.save(HERE/'MODE_EMPLOI_TP761.xlsx')
    return {'humains_non_testes':8,'feuilles':wb.sheetnames,'oracle':data['attendus']}

if __name__=='__main__':print(generer())
