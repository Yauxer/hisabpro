"""Jeu pédagogique et recette tiers759 ; aucun accès DB ou calcul fiscal."""
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

INTRO="""# MODE D’EMPLOI ET RECETTE — RÉMUNÉRATIONS DES TIERS HISABPRO

Version 1 du 23 octobre 2026. Lot759 : formulaire de préparation interne dans le mode Liasse seule.

## Fonction disponible et accès

Saisir un profil, des identités et des mouvements. Chaque conservation crée une nouvelle version et préserve les autres compléments. Le dossier contient JSON/PDF/Excel avec logo et manifeste SHA256. Aucun taux de retenue calculé, aucune écriture générée ou fiche tiers modifiée. Ce document n’est pas un formulaire DGI ; les modèles151 et annexes applicables restent à obtenir. Une revue déclarée ne prouve pas la conformité fiscale. La CNSS concerne le bénéficiaire tiers, pas la paie.

Installer le ZIP différentiel dans l’environnement de test avec son arborescence puis redémarrer les services habituels. Aucune migration nouvelle : conserver le socle des préparations104 déjà installé. Utiliser une société fictive MAD et un admin ou comptable. Lecture peut consulter et exporter sans conserver.

Ouvrir Comptabilité → Liasse fiscale → mode Liasse seule. Importer et conserver une balance de test, ou sélectionner une préparation fictive existante. Les CSV755 peuvent servir de support technique. Le jeu1400/740/37 ci-dessous est documentaire et indépendant : il n’est pas une ventilation exhaustive des21500 d’honoraires du scénario755. Il ne modifie pas les comptes et ne vérifie pas leur rapprochement. Pour un dossier réel, établir le rapprochement et l’exhaustivité sur pièces.

Ouvrir « Préparer les rémunérations des tiers ». Dans « Rubrique tiers à documenter », choisir successivement T151-P, T151-B et T151-M, codes internes. Pour chaque rubrique, choisir « Saisie documentée — à revoir », saisir la justification ci-dessous puis ajouter les lignes. Passer de rubrique conserve le brouillon ; les trois rubriques sont enregistrées ensemble.

## Données exactes du jeu fictif

Copier les identifiants des bénéficiaires dans leurs mouvements. Les références de mouvements sont uniques. Un champ indiqué vide reste vide, pas zéro. Les montants sont fournis par le scénario, sans taux fiscal prescrit.

"""
SUITE="""## Conservation et contrôles

Cocher « Je confirme les données et déclarations saisies, sans valider une liasse complète » puis « Conserver les rémunérations des tiers dans une nouvelle version ». Le numéro change et les données reparaissent sans F5. Rouvrir le formulaire pour voir les contrôles conservés.

Oracles indépendants : comptabilisé1000+500−100=1400MAD ; soumis600+200−60=740MAD ; retenu30+10−3=37MAD. B759-A/Honoraires :900/540/27 ; B759-B/Commissions :500/200/10. La correction est soustraite selon son sens explicite et conserve l’origine M759-A. Aucun taux ou paiement n’est déduit.

Les contrôles portent sur la version enregistrée ; modifier un brouillon ne les change pas avant conservation. Les points manquants sont indiqués par bénéficiaire/mouvement. L’identification TP peut renseigner l’identité lorsque l’identifiant fiscal est absent ; RC/ICE ne sont pas substitués. Une CNSS vide permet une version partielle et reste signalée à qualifier.

## Inconnus, refus et droits

Vider CNSS du bénéficiaireA : conservation partielle, identité à compléter. Vider une somme soumise : ce total devient indisponible, jamais zéro. NaN, Infinity, négatifs directs et précision supérieure à deux décimales sont refusés. Pour soustraire une correction documentaire, choisir Correction documentée et référencer une origine distincte. Aucune écriture historique n’est réparée.

Un bénéficiaire référencé mais absent, un identifiant interne en doublon ou une référence de mouvement en doublon est refusé. Retenu supérieur au soumis saisi est refusé. Aucune retenue déclarée exige0/0 explicites et date fiscale vide. CPU/autoentrepreneur, location, autres catégories et événements hors période restent à qualifier ; leurs données ne sont pas effacées. Une identification fiscale partagée alerte sans fusion. Les crédits IS reçus sur les ventes ne remplacent pas les rémunérations versées aux tiers.

## Exports et justificatifs

Télécharger le dossier ZIP. Vérifier les feuilles T151-P/B/M, contrôle, regroupements et points à revoir ; mêmes références et montants dans PDF/JSON, logo dans PDF/Excel. Le manifeste fournit taille/SHA256. Les totaux portent sur les seules pièces saisies, sans rapprochement comptable automatique.

Joindre JUSTIFICATIFS_FICTIFS_TIERS759.pdf à la version depuis les justificatifs complémentaires si souhaité. Pièce de recette sans valeur réelle. Consulter l’ancienne version : elle reste intacte. Renseigner les preuves et résultats dans le suivi Excel après exécution humaine.

## Cas de recette utilisateur

| ID | Actions | Résultat attendu et preuve | Statut |
|---|---|---|---|
|TIERS759-01|Ouvrir une préparation fictive MAD et parcourir les trois rubriques du formulaire tiers.|Profil/identités/mouvements accessibles, codes internes et limites visibles. Capture d’accès.|Non testé|
|TIERS759-02|Saisir exactement les trois rubriques ci-dessus et conserver.|Nouvelle version, totaux1400/740/37, groupes900/540/27 et500/200/10 ; aucune écriture. Capture version/contrôles.|Non testé|
|TIERS759-03|Modifier seulement un brouillon puis consulter l’ancienne version.|Totaux enregistrés et version historique intacts, aucun changement comptable. Captures avant/après.|Non testé|
|TIERS759-04|Sur copie, vider CNSS puis une somme soumise ; conserver des versions distinctes.|Identité à compléter ; total soumis indisponible si une valeur manque, zéro non inventé. Captures points à revoir.|Non testé|
|TIERS759-05|Sur copie, saisir NaN puis Infinity dans Somme comptabilisée et tenter de conserver ; corriger ensuite1000.|Refus lisible, brouillon préservé, aucune version parasite ; reprise sans F5. Captures refus/reprise.|Non testé|
|TIERS759-06|Sur copie, dupliquer un bénéficiaire puis une référence de mouvement ; retirer les doublons et supprimer l’origine de la correction.|Trois refus sans mutation comptable ni nouvelle version. Captures des références et refus.|Non testé|
|TIERS759-07|Consulter avec lecture, refaire avec comptable sur390px et tenter un accès depuis une autre société.|Lecture sans conservation, comptable autorisé, autre société refusée ; écran lisible. Captures rôles/mobile.|Non testé|
|TIERS759-08|Télécharger ZIP ; ouvrir PDF/Excel/JSON/manifeste, joindre la pièce fictive et consulter l’ancienne version.|Sources/totaux concordants, logos, manifeste et pièce traçable ; ancien état intact. Conserver fichiers/preuves.|Non testé|

## Limites et suite

Ces huit cas restent Non testé humainement. Les tests automatisés sont détaillés au rapport759 ; Word/Excel natifs et environnement cible restent à vérifier. Modèles administratifs et états particuliers à obtenir avant dépôt. Sources proposées automatiquement depuis le Journal et import en masse hors de ce lot. Aucun rapprochement comptable, droit fiscal, paiement ou dépôt validé. RH/paie etpoint6 différés.
"""

def generer():
    # Extraire uniquement les fonctions pures évite tout import de fixtures/DB.
    t=ast.parse((R/'Test/tiers759_support.py').read_text(encoding='utf8'))
    fn=next(a for a in t.body if isinstance(a,ast.FunctionDef) and a.name=='body')
    ns={'uuid4':uuid4};exec(compile(ast.Module(body=[fn],type_ignores=[]),'jeu_fictif','exec'),ns)
    b=ns['body']({'empreinte_sha256':'a'*64})
    data={'societe':'DOSSIER PEDAGOGIQUE TIERS759','exercice':2026,'tables':b['tables'],'attendus':{'comptabilise':'1400.00','soumis':'740.00','retenu':'37.00'},'comptabilite_raccordee':False,'fictif':True,'statut_humain':'Non testé'}
    for k,v in data['attendus'].items():
        assert sum(D(m[k])*(-1 if m['sens']=='Correction documentée' else 1) for m in data['tables'][2]['lignes'])==D(v)
    assert D('1000')+D('500')-D('100')==D('1400') and D('600')+D('200')-D('60')==D('740') and D('30')+D('10')-D('3')==D('37')
    (HERE/'DONNEES_TIERS759.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    t=ast.parse((R/'hisabpro-backend/services/balance_remunerations_tiers_service.py').read_text(encoding='utf8'))
    fn=next(a for a in t.body if isinstance(a,ast.FunctionDef) and a.name=='catalogue')
    ns={'deepcopy':deepcopy,'BLOC':'remunerations_tiers_documentaires'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'labels','exec'),ns)
    catalogue=ns['catalogue']({'contenu':{}})
    pdf=canvas.Canvas(str(HERE/'JUSTIFICATIFS_FICTIFS_TIERS759.pdf'),invariant=1)
    texte=INTRO
    for t,cat in zip(data['tables'],catalogue):
        texte+='### '+t['code']+' — '+cat['titre']+'\n\nJustification du tableau : '+t['justification']+'\n\n'
        pdf.setFont('Helvetica-Bold',13);pdf.drawString(35,805,'HISABPRO - SOURCES FICTIVES TIERS759')
        pdf.setFont('Helvetica',9);pdf.drawString(35,785,'Aucune valeur fiscale reelle - aucun paiement ou depot valide');y=760
        for i,m in enumerate(t['lignes'],1):
            texte+='Ligne '+str(i)+' :\n\n'+'\n'.join('- '+c['label']+' = '+str(m.get(c['cle']) or '(laisser vide)') for c in cat['colonnes_saisie'])+'\n- Référence de source de la ligne = '+m['reference_source']+'\n\n'
            for line in [*[c['label']+' : '+str(m.get(c['cle'],'')) for c in cat['colonnes_saisie']],'Reference source : '+m['reference_source'],'']:
                if y<60:pdf.showPage();y=800;pdf.setFont('Helvetica',9)
                for chunk in [line[j:j+105] for j in range(0,len(line),105)] or ['']:
                    pdf.drawString(35,y,chunk);y-=13
        pdf.showPage()
    pdf.save();texte+=SUITE;source=R/'docs/LIASSE_REMUNERATIONS_TIERS_759.md';source.write_text(texte,encoding='utf8')
    spec=importlib.util.spec_from_file_location('guide759',R/'docs/guide/generer_guide.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    g.SOURCE=source;g.STEM=HERE/'MODE_EMPLOI_TIERS759';blocs=g.blocs();orig=g.word_table;widths={'650':'1200','3000':'3050','1250':'3050','3400':'1000'}
    g.word_table=lambda rows:re.sub(r'w:w="(650|3000|1250|3400)"',lambda m:'w:w="'+widths[m[1]]+'"',orig(rows));g.docx(blocs);table=g.Table
    g.Table=lambda rows,**kw:table(rows,**{**kw,'colWidths':[24*g.mm,64*g.mm,63*g.mm,19*g.mm]});g.pdf(blocs)
    cas=[[c.strip() for c in l.strip('|').split('|')] for l in texte.splitlines() if l.startswith('|TIERS759-')];assert len(cas)==8
    wb=Workbook();wb.calculation=CalcProperties(fullCalcOnLoad=True);ws=wb.active;ws.title='Synthèse';ws.append(['Statut humain','Nombre'])
    for i,statut in enumerate(['Non testé','Réussi','Échoué','Bloqué'],2):ws.append([statut,f'=COUNTIF(Fiscalité!K2:K9,A{i})'])
    ws.append(['Progression','=IF(SUM(B2:B5)=0,0,B3/SUM(B2:B5))']);ws['B6'].number_format='0%'
    ws=wb.create_sheet('Fiscalité');ws.append(['ID','Module','Objectif','Prérequis','Données exactes','Actions interface','Résultat attendu','Écritures attendues','Impact fiscal attendu','Contrôles','Statut humain','Résultat réel','Anomalies','Preuves réelles','Observations','Justificatif attendu'])
    for ident,action,attendu,statut in cas:ws.append([ident,'Préparation interne tiers',action,'Société fictive MAD ; préparation conservée ; guide759 ; rôles dédiés','DONNEES_TIERS759.json et guide champ par champ',action,attendu,'Aucune écriture créée ou modifiée','1400/740/37 documentaires ; aucun taux calculé ni dépôt validé',attendu,statut,'','','','','Captures/fichiers demandés au résultat attendu'])
    dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(dv);dv.add('K2:K9')
    ws=wb.create_sheet('Données exactes');ws.append(['Rubrique','Ligne','Champ','Valeur exacte'])
    for t,cat in zip(data['tables'],catalogue):
        ws.append([t['code'],'','Justification',t['justification']])
        for i,m in enumerate(t['lignes'],1):
            for c in cat['colonnes_saisie']:ws.append([t['code'],i,c['label'],m.get(c['cle'],'')])
            ws.append([t['code'],i,'Référence source',m['reference_source']])
    ws=wb.create_sheet('Calculs indépendants');ws.append(['Montant','Oracle MAD','Formule Excel à recalculer'])
    for a,b,c in [('Comptabilisé',1400,'=1000+500-100'),('Soumis',740,'=600+200-60'),('Retenu',37,'=30+10-3'),('Honoraires comptabilisés',900,'=1000-100'),('Honoraires soumis',540,'=600-60'),('Honoraires retenus',27,'=30-3')]:ws.append([a,b,c])
    ws=wb.create_sheet('Preuves');ws.append(['ID','Preuve réelle','Observations'])
    for c in cas:ws.append([c[0],'',''])
    ws=wb.create_sheet('Anomalies');ws.append(['ID','Cas','Constat','Décision','Statut'])
    for ws in wb:
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=42
        for row in ws:
            for cell in row:cell.alignment=Alignment(wrap_text=True,vertical='top')
    wb.save(HERE/'MODE_EMPLOI_TIERS759.xlsx')
    return {'humains_non_testes':8,'feuilles':wb.sheetnames,'oracle':data['attendus']}

if __name__=='__main__':print(generer())
