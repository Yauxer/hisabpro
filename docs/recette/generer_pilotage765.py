"""Pilotage de recettes existantes : lecture seule des sources, aucune connexion DB.

Les cas et oracles ne sont pas recalculés par le produit. Un dossier de sortie
existant est refusé pour ne jamais écraser une campagne renseignée par l'utilisateur.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.workbook.properties import CalcProperties
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.hyperlink import Hyperlink

ROOT = Path(__file__).resolve().parents[2]
RECETTE = ROOT / 'docs/recette'
STEM = 'PILOTAGE_RECETTE_HORS_RH_765'
STATUTS = ('Non testé', 'Réussi', 'Échoué', 'Bloqué')
DOMAINES = ('Administration', 'Facturation', 'Paiements', 'Comptabilité', 'Banques',
            'Stocks', 'Immobilisations', 'Fiscalité', 'Inventaire clôture',
            'États ETIC', 'Liasse exports', 'Sécurité UX', 'Exploitation', 'Scénarios négatifs')
SOURCES = (
    ('PRINCIPAL', 'CAHIER_RECETTE_HISABPRO', 218, 'Société ATLAS RECETTE 2025 ; exercice complet puis ouverture 2026. Suivre Ordre de passage.', 'CAHIER_RECETTE_HISABPRO.pdf'),
    ('F755', 'CAHIER_RECETTE_FISCALE_755', 14, 'Société neuve ATLAS CONSEIL 755 ; balances N/N-1. Solde proposé 3 650 MAD ; aucune écriture au Journal.', 'CAHIER_RECETTE_FISCALE_755.docx'),
    ('TIERS759', 'MODE_EMPLOI_TIERS759', 8, 'Copie/société fictive dédiée ; oracles documentaires 1 400 / 740 / 37. Ne pas les assimiler aux honoraires 21 500 de 755.', 'MODE_EMPLOI_TIERS759.docx'),
    ('TP761', 'MODE_EMPLOI_TP761', 8, 'Copie/société fictive dédiée ; VL 42 000, brut 7 200, avis 7 400, écart −200 ; aucun impôt dû confirmé.', 'MODE_EMPLOI_TP761.docx'),
    ('CR749', 'MODE_EMPLOI_CREDITS_IS_749', 8, 'Variante indépendante de crédits ; ne pas ajouter ses montants à 755.', 'MODE_EMPLOI_CREDITS_IS_749.docx'),
    ('AP751', 'MODE_EMPLOI_ACOMPTES_IS_751', 8, 'Variante indépendante d’acomptes ; ne pas ajouter ses montants à 755.', 'MODE_EMPLOI_ACOMPTES_IS_751.docx'),
    ('LIQ753', 'MODE_EMPLOI_LIQUIDATION_753', 8, 'Variante indépendante ; maximum 3 000 − crédits 325 − acomptes 1 250 = solde proposé 1 425 MAD, distinct de 3 650 de 755.', 'MODE_EMPLOI_LIQUIDATION_753.docx'),
)
COLONNES = ('Campagne', 'Ordre source', 'Identifiant', 'Module', 'Objectif', 'Prérequis',
    'Données exactes', 'Actions interface', 'Résultat attendu', 'Écritures attendues',
    'Impact fiscal attendu', 'Contrôles', 'Statut humain', 'Résultat réel', 'Anomalies',
    'Observations source', 'Justificatif attendu', 'Preuves obtenues', 'Observations réelles',
    'Classeur source', 'Onglet source', 'Ligne source', 'Guide')
HEAD_MAIN = ('Ordre', 'Identifiant', 'Module', 'Objectif', 'Prérequis', 'Données exactes',
    "Actions dans l'interface", 'Résultat attendu', 'Écritures attendues', 'Impacts fiscaux',
    'Contrôles', 'Statut', 'Résultat réel', 'Anomalies constatées', 'Observations / limites',
    'Preuve attendue', 'Preuves / captures obtenues')
HEAD_ANNEXE = ('ID', 'Module', 'Objectif', 'Prérequis', 'Données exactes', 'Actions interface',
    'Résultat attendu', 'Écritures attendues', 'Impact fiscal attendu', 'Contrôles',
    'Statut humain', 'Résultat réel', 'Anomalies', 'Preuves réelles', 'Observations', 'Justificatif attendu')


def adapter(row, campagne, principal, position):
    if principal:
        ordre, ident, module, objectif, prerequis, donnees, actions, attendu, ecritures, fiscal, controles, statut, reel, anomalies, observations, preuve, obtenue = row
    else:
        ident, module, objectif, prerequis, donnees, actions, attendu, ecritures, fiscal, controles, statut, reel, anomalies, obtenue, observations, preuve = row
        ordre = position
    if statut in ('Réussi', 'Échoué') or any(v not in (None, '') for v in (reel, anomalies, obtenue)):
        raise ValueError(f'Source déjà renseignée : {campagne}/{ident} ; conserver cette campagne sans la réinitialiser.')
    if not ident or statut not in STATUTS:
        raise ValueError(f'Identifiant/statut invalide dans {campagne} : {ident!r}/{statut!r}')
    return [campagne, ordre, ident, module, objectif, prerequis, donnees, actions, attendu,
            ecritures, fiscal, controles, statut, reel, anomalies, observations, preuve,
            obtenue, None]


def charger(recette=RECETTE):
    recette = Path(recette)
    cas, preuves, cles = [], [], set()
    for campagne, stem, nombre, limite, guide in SOURCES:
        fichier = recette / (stem + '.xlsx')
        w = load_workbook(fichier, read_only=True, data_only=False)
        lignes = []
        try:
            for sheet in w:
                header = tuple(next(sheet.values))
                if campagne == 'PRINCIPAL':
                    if header != HEAD_MAIN:
                        continue
                elif sheet.title != 'Fiscalité':
                    continue
                elif header != HEAD_ANNEXE:
                    raise ValueError(f'Colonnes inattendues : {fichier.name}/{sheet.title}')
                for numero, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                    if not any(v is not None for v in row):
                        continue
                    valeurs = adapter(row, campagne, campagne == 'PRINCIPAL', numero - 1)
                    cle = (campagne, valeurs[2])
                    if cle in cles:
                        raise ValueError(f'Cas dupliqué : {cle}')
                    cles.add(cle)
                    domaine = sheet.title if campagne == 'PRINCIPAL' else 'Fiscalité'
                    if domaine not in DOMAINES:
                        raise ValueError(f'Domaine inattendu : {domaine}')
                    lignes.append({'domaine': domaine, 'valeurs': valeurs + [fichier.name, sheet.title, numero, guide]})
            if len(lignes) != nombre:
                raise ValueError(f'{fichier.name} : {len(lignes)} cas, {nombre} attendus')
            lignes.sort(key=lambda c: c['valeurs'][1])
            cas.extend(lignes)
            preuves.append({'campagne': campagne, 'fichier': fichier.name, 'sha256': hashlib.sha256(fichier.read_bytes()).hexdigest(),
                            'cas': nombre, 'limite': limite, 'guide': guide})
        finally:
            w.close()
    return cas, preuves


def texte(cell, valeur):
    cell.value = valeur
    if isinstance(valeur, str):
        cell.data_type = 's'  # Même une référence commençant par = reste un texte source.


def morceaux(valeur):
    """Découper la lecture verticale sans perdre les caractères de la source."""
    bloc, taille = '', 0
    for ligne in str(valeur if valeur is not None else '—').splitlines(keepends=True):
        unite = max(1, math.ceil(len(ligne) / 95))
        if bloc and taille + unite > 22:
            yield bloc
            bloc, taille = '', 0
        bloc += ligne
        taille += unite
    if bloc:
        yield bloc


def classeur(destination, cas, preuves):
    wb = Workbook(); wb.active.title = 'Synthèse'
    wb.calculation = CalcProperties(fullCalcOnLoad=True, forceFullCalc=True)
    listes = wb.create_sheet('Listes')
    for s in STATUTS: listes.append([s])
    listes.sheet_state = 'hidden'
    wb.defined_names.add(DefinedName('StatutsRecette', attr_text="'Listes'!$A$1:$A$4"))
    domaines = {}
    for domaine in DOMAINES:
        ws = wb.create_sheet(domaine); ws.append(COLONNES)
        for case in (c for c in cas if c['domaine'] == domaine):
            n = ws.max_row + 1
            for i, valeur in enumerate(case['valeurs'], 1): texte(ws.cell(n, i), valeur)
            fichier, feuille, ligne, guide = case['valeurs'][19:23]
            ws.cell(n, 20).hyperlink = Hyperlink(ref=ws.cell(n,20).coordinate, target=fichier, location=f"'{feuille}'!A{ligne}")
            ws.cell(n, 23).hyperlink = guide
            for i in (20, 23): ws.cell(n, i).font = Font(color='185FA5', underline='single')
        dv = DataValidation(type='list', formula1="StatutsRecette", allow_blank=False)
        dv.errorTitle='Statut inconnu'; dv.error='Choisir Non testé, Réussi, Échoué ou Bloqué.'; dv.showErrorMessage=True; dv.errorStyle='stop'
        ws.add_data_validation(dv); dv.add(f'M2:M{ws.max_row}')
        for statut, couleur in [('Réussi','DFF1E5'),('Échoué','FCE0DF'),('Bloqué','FFF0C2')]:
            ws.conditional_formatting.add(f'M2:M{ws.max_row}', CellIsRule(operator='equal', formula=['"'+statut+'"'], fill=PatternFill('solid',fgColor=couleur)))
        ws.freeze_panes = 'F2'; ws.sheet_view.zoomScale = 75
        ws.print_title_rows = '1:1'; ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.orientation = 'landscape'; ws.page_setup.paperSize=ws.PAPERSIZE_A3; ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0
        domaines[domaine] = ws
    synthese = wb['Synthèse']; synthese.append(['Domaine', *STATUTS, 'Total', 'Exécution hors bloqués'])
    for domaine, ws in domaines.items():
        n=synthese.max_row+1
        synthese.append([domaine, *[f'=COUNTIF(\'{domaine}\'!$M$2:$M${ws.max_row},{chr(66+i)}$1)' for i in range(4)],f'=SUM(B{n}:E{n})',f'=IF(F{n}=E{n},0,(C{n}+D{n})/(F{n}-E{n}))'])
        synthese.cell(n,1).hyperlink=Hyperlink(ref=synthese.cell(n,1).coordinate,location=f"'{domaine}'!A1");synthese.cell(n,7).number_format='0%'
    fin=synthese.max_row+1;synthese.append(['TOTAL', *[f'=SUM({lettre}2:{lettre}{fin-1})' for lettre in 'BCDEF'],f'=IF(F{fin}=E{fin},0,(C{fin}+D{fin})/(F{fin}-E{fin}))']);synthese.cell(fin,7).number_format='0%'
    for ligne in [[],['Règle de lecture','Exécution = Réussi + Échoué, hors cas Bloqué. Ce taux ne vaut pas acceptation de la recette.'],['Décisions distinctes','Développement global partiel ; tests automatisés selon rapports ; recette utilisateur à effectuer ; production non validée.'],['Point 6 et RH/paie','Différés ; aucun ordre de lancement de recette humaine n’est donné par ce classeur.'],['Saisie','Renseigner les onglets de domaine, pas les formules. Colonnes M statut, N résultat, O anomalies, R preuves et S observations réelles.'],['Résultats sources','Copies initiales seulement. Ne pas renseigner en parallèle les anciens classeurs : aucun synchroniseur automatique.'],['Recalcul','Excel doit recalculer les formules à ouverture ; aucun calcul natif Office exécuté pendant génération.'],['Limites','272 cas regroupés depuis7 classeurs existants : pas272 nouveaux tests ; les autres annexes restent distinctes.']]:synthese.append(ligne)
    plan=wb.create_sheet('Campagnes');plan.append(['Campagne','Cas existants','Société / frontière du scénario','Guide','Classeur source','SHA-256 source'])
    for p in preuves:
        plan.append([p['campagne'],p['cas'],p['limite'],p['guide'],p['fichier'],p['sha256']])
        plan.cell(plan.max_row,4).hyperlink=p['guide'];plan.cell(plan.max_row,5).hyperlink=p['fichier']
    ordre=wb.create_sheet('Ordre de passage');ordre.append(['Campagne','Ordre source','Identifiant','Domaine','Objectif','Lien vers cas à renseigner'])
    positions={(ws.cell(n,1).value,ws.cell(n,3).value):(domaine,n) for domaine,ws in domaines.items() for n in range(2,ws.max_row+1)}
    fiches=wb.create_sheet('Fiches de lecture');fiches.append(['Champ', 'Valeur source', 'Navigation'])
    lectures={}
    for c in cas:
        v=c['valeurs'];domaine,n=positions[(v[0],v[2])]
        debut=fiches.max_row+1;lectures[(v[0],v[2])]=debut
        fiches.append([v[0]+'::'+v[2],v[4],'Renseigner le suivi'])
        fiches.cell(debut,3).hyperlink=Hyperlink(ref=fiches.cell(debut,3).coordinate,location=f"'{domaine}'!M{n}")
        for cellule in fiches[debut]:
            cellule.fill=PatternFill('solid',fgColor='E8EFF7');cellule.font=Font(bold=True,color='185FA5')
        for i in (0,1,2,3,5,6,7,8,9,10,11,15,16,19,20,21,22):
            for indice,bloc in enumerate(morceaux(v[i])):
                ligne=fiches.max_row+1
                texte(fiches.cell(ligne,1),COLONNES[i]+(' (suite)' if indice else ''))
                texte(fiches.cell(ligne,2),bloc)
                hauteur=sum(max(1,math.ceil(len(l)/95)) for l in bloc.splitlines())
                fiches.row_dimensions[ligne].height=min(380, max(30,14*hauteur+8))
        fiches.append([None,None,None])
    ordre.cell(1,6).value='Lire la fiche'
    ordre.cell(1,7).value='Renseigner le cas'
    for c in cas:
        v=c['valeurs'];domaine,n=positions[(v[0],v[2])]
        ordre.append([v[0],v[1],v[2],domaine,v[4],'Lire la fiche','Renseigner le cas'])
        ordre.cell(ordre.max_row,6).hyperlink=Hyperlink(ref=ordre.cell(ordre.max_row,6).coordinate,location=f"'Fiches de lecture'!A{lectures[(v[0],v[2])]}" )
        ordre.cell(ordre.max_row,7).hyperlink=Hyperlink(ref=ordre.cell(ordre.max_row,7).coordinate,location=f"'{domaine}'!M{n}")
    anomalies=wb.create_sheet('Anomalies');anomalies.append(['Référence anomalie','Campagne','Identifiant cas','Constat réel','Attendu','Preuve','Décision','Responsable','Statut'])
    anomalies.append(['À renseigner après constat',None,None,None,None,None,None,None,None])
    for ws in wb:
        if ws.title=='Listes':continue
        if ws.freeze_panes is None:ws.freeze_panes='A2'
        ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:
            lettre=col[0].column_letter;ws.column_dimensions[lettre].width=24
        if ws.title in DOMAINES:
            for lettre in 'EFGHIJKLPQRS':ws.column_dimensions[lettre].width=48
            ws.column_dimensions['M'].width=18
        for row in ws:
            for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
        if ws.title in DOMAINES:
            for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=86
            for row in ws.iter_rows(min_row=2):
                for i in (12,13,14,17,18):row[i].fill=PatternFill('solid',fgColor='FFF6D5')
    fiches.column_dimensions['A'].width=29;fiches.column_dimensions['B'].width=115;fiches.column_dimensions['C'].width=25
    fiches.auto_filter.ref='A1:C1';fiches.sheet_view.zoomScale=85
    fiches.page_setup.orientation='landscape';fiches.page_setup.paperSize=fiches.PAPERSIZE_A4;fiches.page_setup.fitToWidth=1;fiches.page_setup.fitToHeight=0
    # Les premières feuilles présentent le mode d'emploi, puis les cas.
    wb._sheets=[wb['Synthèse'],wb['Campagnes'],wb['Ordre de passage'],fiches,*[wb[d] for d in DOMAINES],wb['Anomalies'],wb['Listes']]
    wb.save(destination/(STEM+'.xlsx'))


def guide(destination, cas, preuves):
    etats=Counter(c['valeurs'][12] for c in cas)
    contenu=f'''# HISABPRO — PILOTER LA RECETTE HORS RH/PAIE

Version 1 du 24 octobre 2026. Lot 765. Point d’entrée et suivi des recettes existantes, sans nouvelle règle comptable ou fiscale.

## 1. Choisir le bon parcours

Ce dossier regroupe {len(cas)} cas de sept classeurs existants : 218 du scénario principal et 54 des compléments 749–761. Ce ne sont pas de nouveaux cas. État initial : {etats['Non testé']} Non testé, {etats['Bloqué']} Bloqué, aucun succès utilisateur prérempli. Les autres annexes restent disponibles dans [l’index des recettes](INDEX_RECETTES_HISABPRO.md) ; elles ne sont pas toutes recopiées ici.

Pour une démonstration commerciale/comptable générale, choisir PRINCIPAL. Pour vérifier les derniers formulaires du mode Liasse seule, choisir F755, puis une copie indépendante pour TIERS759 et TP761. CR749/AP751/LIQ753 servent à isoler un composant ; leur jeu ne remplace pas le scénario annuel 755.

Ouvrir d’abord [le suivi unique Excel](PILOTAGE_RECETTE_HORS_RH_765.xlsx), feuille Campagnes, puis le guide de la campagne retenue. Lire ce guide avant la première saisie : les données exactes, prérequis et variantes restent ceux de la source. Les liens sont relatifs : installer ce différentiel dans le dépôt existant, conserver l’arborescence docs/recette et ouvrir les fichiers extraits du ZIP. Les guides et jeux antérieurs doivent déjà être présents.

## 2. Préparer la recette séparée

Utiliser une installation de recette avec sociétés fictives ; aucune opération décrite ici ne doit être lancée sur les données comptables réelles. Le point 6 et la recette humaine restent différés jusqu’à votre décision ; ce livrable prépare leur exécution, il ne l’autorise pas à votre place.

Faire préparer les services et le schéma par la personne technique selon [Exploitation](../EXPLOITATION_HISABPRO.md). Ne pas exécuter tous les SQL au hasard sur une base existante. La chaîne 104 et le stockage des pièces doivent être cohérents ; les procédures distinguent installation vierge et mise à jour. Aucun changement de base n’est appliqué par ce générateur.

Avant chaque parcours, noter dans une copie du suivi : date, version installée, société fictive, exercice, rôle et navigateur. Les variantes négatives se font sur les copies prévues, sans altérer le scénario principal. Ne pas changer l’horloge du poste pour simuler une échéance.

## 3. Parcours principal : entreprise complète

Ouvrir [le cahier principal PDF](CAHIER_RECETTE_HISABPRO.pdf) et conserver [le jeu chiffré principal](jeu_donnees_recette.json) avec ses pièces fictives. Le scénario utilise ATLAS RECETTE HISABPRO 2025, puis l’ouverture 2026. Suivre les 218 cas dans l’onglet Ordre de passage, filtré sur PRINCIPAL ; l’ordre chronologique prime sur l’ordre des onglets de domaine.

Le parcours couvre création et paramètres, tiers/articles, cycle commercial, paiements/lettrage, banque, stock, immobilisations, fiscalité, inventaire/clôture, états et exports, permissions et exploitation. Les cas Bloqué sont des limites explicites, pas des manipulations à deviner. Le détail des montants et écritures attendues est conservé dans chaque ligne et dans les fichiers sources.

Repères du scénario principal déjà calculés dans sa source : résultat avant IS 129 830, bénéfice fiscal 133 830, IS 2025 de 23 420,25, crédit documentaire 200, solde 23 220,25 ; bilan 337 010, banque 287 730, stock 6 600, CAF 112 709,75. Ces attentes pédagogiques ne sont ni les chiffres du dossier 755 ni des données réelles.

## 4. Dernières préparations annuelles et annexes internes

| Campagne | Guide à ouvrir | Repère indépendant | Frontière |
|---|---|---|---|
|F755|[Recette annuelle755](CAHIER_RECETTE_FISCALE_755.docx)|Solde proposé 3 650|Société neuve, balancesN/N-1, aucun Journal|
|TIERS759|[Guide tiers759](MODE_EMPLOI_TIERS759.docx)|1 400 comptabilisé / 740 soumis / 37 retenu|Jeu documentaire distinct des honoraires 21 500 de 755|
|TP761|[Guide TP761](MODE_EMPLOI_TP761.docx)|Brut 7 200 / avis 7 400 / écart −200|Bases/classes déclarées, aucun impôt dû confirmé|
|LIQ753|[Guide composant753](MODE_EMPLOI_LIQUIDATION_753.docx)|3 000 − 325 − 1 250 = 1 425|Variante indépendante, à ne pas additionner à 755|

755 contient 14 cas depuis une société neuve et les balances 2025/2026, jusqu’aux formulaires et exports. Utiliser [les données755](DONNEES_FISCALES755.json), [balanceN](BALANCE_FICTIVE_FISCALE755_N.csv), [balanceN-1](BALANCE_FICTIVE_FISCALE755_N1.csv), [logo](LOGO_FICTIF755.png) et [pièces fictives](JUSTIFICATIFS_FICTIFS755.pdf). Bénéfice 120 000, IS 24 000, crédits disponibles 350, acomptes 20 000, solde proposé 3 650, CSS 0 séparée. Ne pas saisir au Journal les opérations qui expliquent ces balances.

759 contient 8 cas, données et rubriques champ par champ dans son guide ; [jeu tiers](DONNEES_TIERS759.json).761 contient 8 cas, [jeu TP](DONNEES_TP761.json). Un zéro, une donnée inconnue et une absence d’applicabilité sont trois situations différentes. Aucun modèle administratif ou paiement ne se déduit des sommes documentaires.

Pour isoler les composants : [crédits749](MODE_EMPLOI_CREDITS_IS_749.docx), [acomptes751](MODE_EMPLOI_ACOMPTES_IS_751.docx), [proposition753](MODE_EMPLOI_LIQUIDATION_753.docx),8 cas chacun. Choisir une copie dédiée. Les oracles 1 425 et 3 650 répondent à des jeux différents et ne doivent jamais être additionnés.

## 5. Renseigner le suivi unique

Dans Ordre de passage, filtrer la campagne puis cliquer Lire la fiche. La feuille Fiches de lecture présente les champs verticalement : les longs textes sont répartis sans perte sur plusieurs lignes. Elle sert à la lecture ; les résultats se saisissent une seule fois dans l’onglet de domaine, via Renseigner le cas ou Renseigner le suivi. La colonne M contient le statut. N reçoit le résultat réel, O l’anomalie, R le chemin ou la référence de preuve, S les observations réelles. Ces cellules de saisie sont jaunes. P conserve les observations de la source ; ne pas effacer ces limites initiales.

Réaliser l’action puis comparer au résultat attendu et aux écritures attendues. Pour Réussi, conserver une preuve quand elle est demandée ; pour Échoué ou Bloqué, décrire le constat et la dépendance. Arrêter les étapes dépendantes d’une anomalie comptable et poursuivre uniquement les branches indépendantes prévues. Ne jamais modifier une écriture définitive pour faire correspondre un résultat.

La Synthèse recalcule les statuts des onglets de domaine. Son taux d’exécution compte Réussi + Échoué et exclut les Bloqué ; il ne signifie donc pas que la recette est réussie. Les formules doivent être recalculées à l’ouverture d’Excel ; le générateur ne prétend pas les avoir exécutées dans Office natif. Les feuilles sources et les anciens suivis ne sont pas synchronisés : renseigner cette copie unique, pas deux classeurs en parallèle.

Les colonnesT/U/V gardent le fichier, l’onglet et la ligne source ; W ouvre le guide. La feuille Campagnes conserve les empreintesSHA-256 des sept fichiers lus. Ces empreintes décrivent l’état initial, pas les modifications que vous consignerez ensuite. Le générateur refuse d’écraser ses sorties existantes : conserver une copie de travail par campagne et archiver les preuves à côté.

## 6. Blocages et verdict

Les 10 cas Bloqué du principal restent bloqués. Certaines préparations internes ont évolué depuis sa rédaction, mais cela ne valide pas leur variante déclarative officielle. Les compléments 759/761 testent des préparations disponibles ; ils ne débloquent pas les déclarations administratives complètes 09F/09G. Le référentiel 09B, les modèles et l’EDI exigent les [documents officiels listés](../audit/DEPENDANCES_OFFICIELLES_20261023_763.md).

Les justificatifs historiques manquants FEC/ETIC ne sont pas inventés. Les autres annexes de l’index sont des scénarios indépendants : ne pas les ajouter automatiquement au principal. RH/paie restent différées et aucun cas de leur annexe n’est importé dans ce suivi.

Distinguer quatre décisions : développement global partiel ; tests automatisés validés seulement sur les périmètres des rapports ; recette utilisateur à effectuer ; mise en production non validée. Une archive interne ou un export local ne prouve pas un dépôt accepté. Le partenaire doit décider du verdict à partir de résultats et preuves réels, pas du nombre de tests automatiques.
'''
    source=destination/(STEM+'.md');source.write_text(contenu,encoding='utf8')
    spec=importlib.util.spec_from_file_location('guide_pilotage765',ROOT/'docs/guide/generer_guide.py')
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);g.SOURCE=source;g.STEM=destination/STEM
    word_table = g.word_table
    largeurs = {'650':'1200', '3000':'2800', '1250':'2000', '3400':'2300'}
    g.word_table = lambda rows: re.sub(r'w:w="(650|3000|1250|3400)"', lambda m: 'w:w="'+largeurs[m[1]]+'"', word_table(rows))
    g.docx(g.blocs())
    liens_docx(destination/(STEM+'.docx'))
    original_escape=g.escape
    def avec_liens(s):
        out=[];pos=0
        for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)',s):
            out.extend([original_escape(s[pos:m.start()]),'<link href="'+escape(m[2],{'"':'&quot;'})+'" color="#185FA5"><u>'+original_escape(m[1])+'</u></link>']);pos=m.end()
        return ''.join(out)+original_escape(s[pos:])
    g.escape=avec_liens
    table = g.Table
    g.Table = lambda rows, **kw: table(rows, **{**kw, 'colWidths':[24*g.mm,55*g.mm,40*g.mm,51*g.mm]})
    g.pdf(g.blocs())


def liens_docx(path):
    w='http://schemas.openxmlformats.org/wordprocessingml/2006/main';rel='http://schemas.openxmlformats.org/package/2006/relationships';rd='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    ET.register_namespace('w',w);ET.register_namespace('r',rd)
    with ZipFile(path) as z:files={n:z.read(n) for n in z.namelist()}
    doc=ET.fromstring(files['word/document.xml']);rels=ET.fromstring(files['word/_rels/document.xml.rels']);index=100
    for p in doc.iter('{'+w+'}p'):
        runs=p.findall('{'+w+'}r')
        if len(runs)!=1:continue
        t=runs[0].find('{'+w+'}t');s=t.text if t is not None else ''
        matches=list(re.finditer(r'\[([^\]]+)\]\(([^)]+)\)',s or ''))
        if not matches:continue
        p.remove(runs[0]);pos=0
        def run(parent,txt,link=False):
            rr=ET.SubElement(parent,'{'+w+'}r')
            if link:
                pr=ET.SubElement(rr,'{'+w+'}rPr');ET.SubElement(pr,'{'+w+'}color',{'{'+w+'}val':'185FA5'});ET.SubElement(pr,'{'+w+'}u',{'{'+w+'}val':'single'})
            ET.SubElement(rr,'{'+w+'}t',{'{http://www.w3.org/XML/1998/namespace}space':'preserve'}).text=txt
        for m in matches:
            run(p,s[pos:m.start()]);rid='rIdLien'+str(index);index+=1
            ET.SubElement(rels,'{'+rel+'}Relationship',{'Id':rid,'Type':rd+'/hyperlink','Target':m[2],'TargetMode':'External'})
            h=ET.SubElement(p,'{'+w+'}hyperlink',{'{'+rd+'}id':rid});run(h,m[1],True);pos=m.end()
        run(p,s[pos:])
    files['word/document.xml']=ET.tostring(doc,encoding='utf-8',xml_declaration=True);files['word/_rels/document.xml.rels']=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,data in files.items():z.writestr(n,data)


def generer(destination=RECETTE, recette=RECETTE):
    destination=Path(destination)
    outputs=[destination/(STEM+suffix) for suffix in ('.md','.docx','.pdf','.xlsx','.json')]
    if any(p.exists() for p in outputs):
        raise FileExistsError('Sorties existantes : choisir --output un autre dossier ; aucune campagne écrasée.')
    cas,preuves=charger(recette)
    destination.mkdir(parents=True,exist_ok=True)
    avant={p['fichier']:hashlib.sha256((Path(recette)/p['fichier']).read_bytes()).hexdigest() for p in preuves}
    classeur(destination,cas,preuves);guide(destination,cas,preuves)
    assert all(hashlib.sha256((Path(recette)/f).read_bytes()).hexdigest()==h for f,h in avant.items())
    resultat={'version':1,'lot':765,'cas_existants_regroupes':len(cas),'statuts_initiaux':dict(Counter(c['valeurs'][12] for c in cas)),
        'sources':preuves,'recette_utilisateur_executee':False,'formules_office_executees':False,'base_consultee':False,
        'nouvelles_regles_fiscales':False,'RH_paie_et_point6':'différés','autres_annexes':'distinctes, non intégrées à ces 272 cas'}
    outputs[-1].write_text(json.dumps(resultat,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return resultat


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=RECETTE);args=parser.parse_args()
    print(json.dumps(generer(args.output),ensure_ascii=False,indent=2))
