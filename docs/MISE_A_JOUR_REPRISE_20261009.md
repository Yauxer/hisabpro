# HisabPro — mise à jour de la reprise du 9 octobre 2026

Cette reprise complète les lots 266–280. Le dépôt partagé contient déjà les corrections ; les ZIPs servent à les transférer dans une autre copie du même état de départ. Ils ne constituent ni une sauvegarde de base ni une installation complète depuis zéro.

## Contenu et prérequis

Le socle jusqu’au lot 265 doit être présent, notamment le démarrage GRH corrigé229, la protection des écritures, la numérotation interne de la liasse et le bilan détaillé256. Les différentiels de reprise conservent ces fonctions ; ils ne les réappliquent pas.

Les changements récents portent sur :

- les dates et réponses tardives dans balances, grand livre et rapprochement ;
- les nombres non finis dans les requêtes articles et les frais facultatifs d’emballage/transport ;
- l’aperçu des libellés et la sauvegarde depuis Fiscalité ;
- la qualification TVA dans l’éditeur des brouillons d’achat ;
- les filtres des tiers par délai de paiement ;
- les preuves de recette des achats, avoirs, réceptions partielles et leur stock.

L’[annexe de recette des corrections](recette/ANNEXE_RECETTE_CORRECTIONS_20261009.md) fournit huit cas avec données exactes. Ses versions [PDF](recette/ANNEXE_RECETTE_CORRECTIONS_20261009.pdf) et [Excel](recette/ANNEXE_RECETTE_CORRECTIONS_20261009.xlsx) conservent les résultats utilisateur à renseigner.

## Vérifier un ZIP avant copie

Dans une copie dédiée à la recette, conserver la version de code précédente et comparer les fichiers à remplacer avec les éventuelles modifications locales. Le ZIP doit conserver les chemins `src/`, `hisabpro-backend/`, `Test/` et `docs/`. Il ne contient pas de `.env`, de base, de pièces utilisateur, de venv ou de `node_modules`.

Les commandes suivantes lisent une archive existante ; adapter son nom au ZIP reçu :

```powershell
Set-Location -LiteralPath 'C:\Users\Y_N_e\hisabpro - GPT'
$pythonMiseAJour = Join-Path (Get-Location).Path 'hisabpro-backend\.venv\Scripts\python.exe'
$zipMiseAJour = Join-Path (Get-Location).Path 'HisabPro_Patch275_Facture_Achat_TVA_Edition.zip'
& $pythonMiseAJour -m zipfile -l $zipMiseAJour
& $pythonMiseAJour -m zipfile -t $zipMiseAJour
```

Appliquer les fichiers applicatifs à la racine de cette copie, après comparaison. Préserver ses secrets et fichiers de données. Les rapports et le journal livrés constituent des preuves de cette version ; conserver séparément un journal local plus récent. Le cumulatif de reprise réunit les dernières versions des fichiers livrés, sans inclure les ZIPs sources eux-mêmes.

## Ce qui change dans la base

**Aucun script SQL ni migration n’est ajouté ou modifié par les lots 266–280.** Le lot268 modifie la validation des requêtes Python, pas le schéma PostgreSQL. Les frais article, les paramètres de libellé, les choix TVA et les délais de tiers utilisent des colonnes déjà présentes.

Les corrections ne réécrivent pas les prix historiques, les salariés, les écritures définitives ou les tableaux d’une ancienne archive. Les tests comportant des données NULL ou invalides les préparent uniquement dans leur laboratoire avant la photographie de contrôle.

Lorsqu’un futur lot exige une nouvelle colonne ou contrainte, sa migration doit rester versionnée, additive et testée avec son rejeu lorsque pertinent. Une réparation de données historiques est distincte et doit conserver sa trace. Cette reprise n’exécute aucune migration sur le PostgreSQL de l’utilisateur.

Le démarrage de développement existant peut préparer les clés composites GRH et appliquer les compléments080–082 déjà présents : voir [le service de bootstrap](../hisabpro-backend/services/grh_bootstrap_service.py) et [la procédure d’exploitation](EXPLOITATION_HISABPRO.md). Un redémarrage ne doit donc pas être décrit comme une garantie d’absence de toute opération DDL. En production avec création désactivée, le manifeste de migrations et les droits de la cible restent à contrôler séparément.

## Vérification dans une copie de recette

Les dépendances applicatives ne changent pas dans ces lots. Après application, vérifier le frontend depuis la racine :

```powershell
npm.cmd run build
```

Pour démarrer une copie déjà provisionnée, configurer explicitement sa connexion de recette et suivre la [procédure d’exploitation](EXPLOITATION_HISABPRO.md). Aucun démarrage connecté à la base réelle n’est exécuté par ce guide.

Le runner de tests évite la connexion configurée dans `.env` et exclut l’ancien banc PostgreSQL non isolé. Les tests PostgreSQL qu’il lance utilisent leurs propres clusters contrôlés par les fixtures ; les tests unitaires purs peuvent utiliser SQLite. Exemple ciblé :

```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
& $pythonMiseAJour -X utf8 Test/run_unit_tests.py Test/test_e2e_facture_achat_tva_edition_isole.py --tb=short
```

La recette utilisateur se déroule dans une société fictive de la copie de recette. Contrôler les données sauvegardées, les totaux et les écritures avec le cahier, puis renseigner résultat réel, anomalies et preuves dans Excel. Les succès automatisés ne remplissent pas ce classeur à la place de l’utilisateur.

## État et limites

Les résultats réels figurent dans le [journal](../CODEX_PROGRESS.md), les rapports `Test/` et le [manifeste des ZIPs](audit/LIVRAISONS_SESSION_20261006_2012.json). La [matrice](audit/MATRICE_COUVERTURE_HISABPRO.md) distingue les fonctionnalités terminées dans leur périmètre, partielles, absentes ou bloquées.

Les frais article ne sont pas copiés automatiquement sur les documents. La qualification TVA saisie ne prouve pas un droit fiscal à déduction. Les anciens justificatifs FEC/ETIC manquants restent visibles. La paie définitive et le XML/EDI nécessitent encore leurs références officielles applicables. Le développement global, la recette utilisateur et l’exploitation de production restent des statuts distincts.
