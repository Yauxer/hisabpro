# MODE D’EMPLOI ET RECETTE — CESSIONS ET RETRAITS DOCUMENTAIRES

Version 1 du 21 octobre 2026. Complément B3 de la préparation depuis balances.

## Fonction et limites

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
consulter une préparation puis ouvrir Documenter les cessions et retraits
d’immobilisations. Le formulaire B3 est un complément documentaire interne,
selon les données du tableau de cessions déjà présent dans HisabPro. Il ne
prétend pas constituer un modèle DGI exhaustif ou officiellement validé.

Désignation, date/type de sortie, valeur d’entrée, valeur nette d’amortissement
VNA et prix sont saisis depuis des sources explicites. Aucun de ces mouvements
n’est déduit des seules balances N/N-1 ou du registre comptable réel de la
société active. Le contrôle arithmétique donne prix déclaré moins VNA déclarée.
Il ne calcule pas un résultat fiscal et ne crée aucune écriture.

Le contrôle est figé avec la version, sa méthode, son auteur, sa date UTC et
l’empreinte de sa source. Les contrôles affichés concernent la version conservée,
pas le brouillon. Une information inconnue reste vide ; un zéro est explicite.
Un prix ou une VNA inconnus rendent la différence de la ligne indisponible.
Le total reste indisponible si une seule ligne est inconnue ou si aucune ligne
n’est déclarée. Une déclaration Néant est une déclaration justifiée, pas une
preuve de l’exhaustivité du registre ou du rapprochement B2/B2bis.

## Prérequis et jeu de données

Utiliser uniquement une société fictive séparée en MAD et l’exercice2026 ouvert.
La préparation depuis balances et la migration071 existantes doivent être
installées. Aucune nouvelle migration n’est ajoutée. Redémarrer le backend et
reconstruire le frontend après application des fichiers. Utilisateurs : un
administrateur/comptable pour saisir et un lecteur pour vérifier les droits.
Ajouter un logo fictif aux paramètres société et noter le nombre d’écritures
au Journal avant l’essai : il doit rester inchangé.

Réutiliser les CSV fictifs du lot707 : BALANCE_FICTIVE_PARTICIPATIONS707_N.csv
et BALANCE_FICTIVE_PARTICIPATIONS707_N1.csv, dans docs/recette. Chaque période
a débit=crédit=10000MAD. Ces soldes ne prouvent pas les sorties ci-dessous :
les déclarations proviennent du registre et des pièces fictives distinctes.
Les données exactes sont aussi fournies dans DONNEES_CESSIONS711.json.

Choisir B3, déclaration Saisie documentée — à revoir et justification
Registre fictif711 et pièces de sortie. Ajouter deux lignes :

- Ligne1 : Désignation Machine Atlas fictive ; date2026-06-30 ; type cession ; valeur d’entrée10000,00MAD ; VNA6000,00MAD ; prix5000,00MAD ; référence Acte fictif711 A.
- Ligne2 : Désignation Matériel Rif fictif ; date2026-09-15 ; type retrait ; valeur d’entrée3000,00MAD ; VNA0 explicitement ; prix0 explicitement ; référence PV fictif711 B.

Oracle indépendant : ligne1 =5000−6000=−1000MAD ; ligne2 =0−0=0MAD ; total−1000MAD.
Remplacer ensuite le prix de ligne1 par5999,99MAD : différence5999,99−6000=−0,01MAD,
total−0,01MAD. Ces chiffres servent uniquement à la recette documentaire,
sans affirmer une qualification juridique ou un calcul fiscal des opérations.

## Parcours d’utilisation

1. Importer et conserver la préparation fictive ; noter son numéro et son empreinte.
2. Ouvrir Documenter les cessions et retraits d’immobilisations. Choisir le statut et saisir la justification puis les deux lignes ci-dessus.
3. Les dates sont facultatives. Si renseignées, utiliser AAAA-MM-JJ ou le sélecteur de date. Le type peut rester vide ; sinon choisir cession, retrait ou autre.
4. Cocher Je confirme les données et déclarations saisies, sans valider une liasse complète. Cliquer Conserver les tableaux ETIC dans une nouvelle version.
5. La nouvelle version est immédiatement sélectionnée. Rouvrir le formulaire : ligne1−1000, ligne2 0, total−1000MAD.
6. Modifier le prix de la première ligne en5999,99 sans conserver. Les contrôles restent ceux de la version conservée, soit−1000MAD. Confirmer et conserver pour obtenir une nouvelle version à−0,01MAD.
7. Revenir à la version précédente : son prix5000 et son total−1000 doivent rester inchangés. Comparer le nombre d’écritures au Journal.
8. Télécharger PDF, Excel et dossier ZIP de la dernière version, puis vérifier le logo et les données.

Les montants saisis sont non négatifs en MAD, avec deux décimales maximum ;
leur différence peut être négative. NaN, infinis, booléens et précisions
excessives sont refusés. Aucun taux ou traitement fiscal n’est ajouté.
Une VNA supérieure à la valeur d’entrée déclarée garde une alerte visible ;
aucun chiffre n’est ajusté. Une date déclarée hors de la période conservée est
signalée. La désignation et la référence sont requises pour identifier chaque
ligne déclarée documentée, sans rendre date/type ou montants inconnus obligatoires.
Une note B3 Non applicable et un tableau renseigné conservent une contradiction visible.

## Vérifier les exports

PDF : déclarations, références, source/auteur/UTC, différences conservées et
logo actuel. Excel : Origine cessions, Cessions déclarées N, Déclaration cessions,
Contrôle cessions. Les montants inconnus restent indisponibles et ne deviennent
pas0. Les textes restent des textes, même s’ils commencent par un signe égal ;
les grands nombres deviennent des textes si nécessaire pour préserver la précision.

ZIP : cessions_documentaires.json, sources, PDF, Excel, pièces propres à la version
et MANIFESTE_SHA256.json. Les données et contrôles JSON correspondent à ceux
conservés ; vérifier les empreintes du manifeste. Le logo actuel est extérieur
à l’empreinte historique. Les autres compléments et anciennes versions sont
préservés. Les pièces jointes ne sont pas copiées implicitement entre versions.

## Recette humaine à effectuer

Prérequis communs ci-dessus ; administrateur/comptable sauf cas06 lecteur.
Résultat comptable et fiscal attendu du formulaire : aucune écriture, aucune
liquidation fiscale, aucun changement au bilan/CPC de la préparation.
Remplir résultat réel, anomalies et preuves dans le classeur fourni. Les tests
automatisés ne renseignent pas la recette utilisateur à votre place.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|C711-01|Importer et conserver les CSV707 dans une société fictive2026/MAD ; noter le Journal ; saisir B3 et les deux lignes ci-dessus.|Brouillon avec dates/types explicites et sources fictives. Aucun contrôle conservé avant enregistrement. Capture et nombre initial d’écritures.|Non testé|
|C711-02|Confirmer puis conserver et rouvrir B3.|Nouvelle version sélectionnée immédiatement ; ligne1−1000MAD, ligne2 0, total−1000. Auteur/source et données corrects. Capture des contrôles.|Non testé|
|C711-03|Modifier le prix ligne1 de5000 en5999,99 ; regarder les contrôles puis confirmer et conserver ; revenir à la version précédente.|Brouillon ne change pas le contrôle conservé−1000 ; après sauvegarde, nouvelle version−0,01 ; ancienne version toujours−1000 ; Journal inchangé. Captures des versions.|Non testé|
|C711-04|Sur un autre brouillon, saisir prix−1 et tenter de conserver ; corriger en5999,99. Essayer aussi VNA10001 avec entrée10000 et date2025-12-31.|Prix négatif refusé, brouillon préservé ; correction réinitialise confirmation puis réussit. VNA supérieure/date hors2026 conservent deux alertes sans ajustement. Captures erreur et alertes.|Non testé|
|C711-05|Télécharger PDF, Excel et ZIP du cas03 avec logo fictif ; ouvrir les trois fichiers ; sur un autre brouillon laisser le prix vide puis conserver.|Logo/source/références présents ; total−0,01 exact et manifeste vérifiable. Avec prix inconnu, différence et total indisponibles, jamais0. Conserver exports et capture des inconnus.|Non testé|
|C711-06|Se connecter comme lecteur ; consulter B3 du cas02 et télécharger son ZIP.|Champs désactivés et aucun bouton de conservation ; consultation et téléchargement autorisés ; aucune nouvelle écriture/version. Capture droits et ZIP.|Non testé|

## État et suite

Les tests exécutés et limites sont consignés au rapport711. La recette humaine,
l’ouverture Office sur votre poste et la mise en production restent à effectuer.
B3 documentaire ne prouve ni l’exhaustivité des sorties ni leur rapprochement
avec B2/B2bis. Les mouvements d’immobilisations, amortissements et provisions
restent à documenter depuis des sources explicites, puis la fiscalité autonome.
RH/paie et point6 humain restent différés. Aucune certification officielle affirmée.
