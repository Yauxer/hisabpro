# Dossier de préparation de balances — utilisation et vérification

Version 1 du 21 octobre 2026

Le dossier ZIP regroupe les fichiers d’une **version conservée** de préparation
de balances. Il permet de transmettre au comptable les états, sources et
compléments disponibles. C’est un dossier interne à compléter, distinct d’une
archive fiscale annuelle définitive ou d’un fichier officiel de dépôt.

## Télécharger le dossier

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
ouvrir les préparations, sélectionner la version, puis cliquer
**Télécharger le dossier de préparation ZIP**. Le fichier s’appelle
`HisabPro_Dossier_Preparation_2026_v2.zip` pour l’exercice2026/version2.
Le rôle Lecture dispose du même téléchargement, sans créer de préparation.

Le téléchargement ne crée aucune écriture ni nouvelle version, ne finalise
pas la liasse et ne modifie pas les anciennes versions. Un changement de session
pendant une réponse retardée empêche le téléchargement de cet ancien contexte.

## Contenu et limites

- `preparation.pdf` et `preparation.xlsx` : même version que l’écran, avec le
  logo/identité actuels et les compléments documentaires éventuels.
- `preparation.json` : données de la version conservée et son empreinte.
- `balance_N.csv`, `balance_N1.csv` : seulement les sources normalisées réellement
  présentes. Ce ne sont pas les fichiers binaires d’origine. SansN-1, aucun
  fichierN-1 vide ou rempli de zéros n’est fabriqué.
- `echeances_documentaires.json` : présent seulement si la version contient
  ce complément. Montants inconnus et reliquats non qualifiés restent explicites.
- `identite_export.json` : identité actuelle et présence d’un logo valide ;
  ces éléments restent hors empreinte du contenu historique.
- `LIRE_MOI.txt` : portée, absences de sources et travaux restant à compléter.
- `MANIFESTE_SHA256.json` : liste exacte des autres fichiers, tailles etSHA-256.

Le manifeste ne s’auto-hache pas. Il contrôle la cohérence des fichiers du paquet,
sans constituer une signature, une certification ou une preuve de dépôt.
Les dates techniques de génération du PDF/XLSX peuvent changer d’un téléchargement
à l’autre ; leurs empreintes sont recalculées dans chaque nouveau manifeste.
Le contenu conservé et son empreinte historique restent les mêmes.

Les noms d’import, même atypiques, restent des métadonnées ; les entrées du ZIP
ont des noms fixes et ne reprennent aucun chemin fourni dans un nom de fichier.
Un ancien logo incompatible est signalé absent ; aucune URL n’est téléchargée.
Une ancienne version sans sources détaillées reste exportable avec ses états
conservés et les absences signalées. Une empreinte incohérente bloque le dossier.

## BAL689-01 — recette administrateur, à effectuer

Prérequis : laboratoire fictif du cahier687, version2 ou3 conservée. Réutiliser
`RECETTE ECHEANCES 687 SARL` et les données du CSV de recette ; aucune base réelle.
Statut humain : Non testé. Résultat réel, anomalies et preuves à renseigner.

1. Sélectionner la version2 ou3 et relever sa version et son empreinte.
2. Télécharger le dossier ZIP et utiliser « Extraire tout » dans un dossier
   de recette distinct. Ouvrir la notice, le PDF et l’Excel.
3. Vérifier les montants : bilan9000, CPC0 ; B6solde8000, ventilé3000,
   reliquat5000. Pour version3, B7ventilé3000/reliquat0 ; pour version2,
   B7non ventilé/reliquat3000. Les champs inconnus restent inconnus.
4. Vérifier l’absence du CSVN-1 puisque ce jeu n’en fournit pas ; retrouver
   `n1` dans les sources absentes du manifeste.
5. Comparer version/empreinte entre écran, PDF, feuilleDossier de l’Excel,
   JSON de préparation et manifeste. Vérifier le logo actuel s’il est configuré.
6. Contrôle technique facultatif par le technicien, dans le dossier extrait :
   `Get-FileHash -LiteralPath .\preparation.pdf -Algorithm SHA256`.
   Comparer à la valeurSHA-256 de ce fichier dans le manifeste ; contrôler
   aussi les tailles et la liste exacte des fichiers. Aucun accès base requis.
7. Revenir dans le Journal : il doit rester vide pour cette société de recette.
   La liste des versions doit rester inchangée.

Résultat attendu : paquet cohérent et limité aux sources/compléments disponibles,
sans nouvelle écriture, nouvelle version, liquidation ou archive définitive.
Preuves : ZIP téléchargé, captures de la sélection, PDF/Excel et contrôleSHA si fait.
Aucun impact fiscal nouveau attendu ; aucune conformité ou recette humaine présumée.

## BAL689-02 — recette Lecture, à effectuer

Prérequis : compteLecture du cahier687. Statut humain : Non testé ; résultat
réel, anomalies et preuves à renseigner. Sur390px de largeur ou sur poste normal,
sélectionner la même société et la même version puis télécharger le dossier.
Ouvrir les fichiers et reprendre les contrôles du cas01. Vérifier qu’aucune
commande d’import ou conservation n’est proposée au lecteur. Changer pour une
autre société de laboratoire : cette préparation ne doit pas apparaître dans
sa liste. Revenir : retrouver les mêmes versions et la même empreinte.

Résultat attendu : consultation et export autorisés, sans mutation ni mélange
de sociétés. Écritures et impacts fiscaux attendus : aucun. Conserver le ZIP
et les captures comme preuves, puis renseigner le classeur de suivi associé.

## Installation et suite

Aucune nouvelle migration ; dépend des préparations071 et des fonctions
677/679/687 pour les détails et compléments. Le cumul689 fournit les fichiers
applicatifs correspondants. Les essais utilisent un PostgreSQL103 jetable,
jamais le PostgreSQL réel. Recette utilisateur et production non validées.

L’ETIC officielle complète, les flux du financement, les retraitements et
liquidations, annexes et formats officiels restent à compléter selon la matrice.
RAS/EDI restent bloqués par les spécifications applicables manquantes ; RH/paie
et point6 humain différés. Le dossier ZIP n’efface pas ces limites.
