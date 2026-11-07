# MODE D’EMPLOI ET RECETTE — DÉCLARATIONS DES ÉMETTEURS

Version 1 du 21 octobre 2026. Complément documentaire709 de la préparation depuis balances.

## Accès et périmètre

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
consulter une préparation conservée puis ouvrir Documenter les émetteurs des
participations. Les identifiants B4-N et B4-N1 sont des codes internes du
formulaire, sans prétendre à une numérotation officielle DGI.

Le détail automatique B4 du lot707 reste séparé et inchangé. Le nouveau
formulaire permet de documenter les émetteurs, leur capital, la quote-part
et les produits reçus depuis des sources explicites. Ces informations ne sont
jamais déduites des seuls soldes comptables.

Le rapprochement porte sur la valeur brute déclarée par compte251 et son solde
brut signé dans la balance source conservée. Il ne compare ni le capital de
l’émetteur au montant investi, ni le seul251 au total24/25 du bilan. Aucun
pourcentage n’est déduit ou additionné entre des sociétés différentes.

## Prérequis et données exactes

Utiliser exclusivement une société fictive séparée en MAD, exercice2026 ouvert,
comptes1111,2411,2510 et5141 déjà au plan ; utilisateur administrateur/comptable,
puis lecteur pour les droits. Le module existant de préparations et sa migration071
doivent être installés. Aucune nouvelle migration n’est ajoutée. Redémarrer le
backend et reconstruire le frontend après application des fichiers.

Réutiliser les deux CSV du lot707 dans docs/recette :
BALANCE_FICTIVE_PARTICIPATIONS707_N.csv et BALANCE_FICTIVE_PARTICIPATIONS707_N1.csv.
Chaque balance a débit=crédit=10000MAD. N contient2510 débit4000 ; N-1 contient2510
débit3000. Les autres postes sont explicités dans DONNEES_PARTICIPATIONS707.json.
Le JSON DONNEES_EMETTEURS709.json fournit les déclarations fictives et les oracles.
Aucun identifiant légal réel n’est nécessaire ni inventé comme exigence.

N : choisir B4-N, statut Saisie documentée — à revoir, justification Relevé fictif709 N.
Ajouter deux lignes au tableau, compte2510 pour chacune :

- Ligne1 : Émetteur Atlas Industrie fictive ; identifiant FICTIF-A ; valeur brute2500,00MAD ; capital500000,00MAD ; quote-part20 ; produits reçus vides ; référence Attestation fictive A.
- Ligne2 : Émetteur Rif Services fictive ; identifiant vide ; valeur brute1500,00MAD ; capital et quote-part vides ; produits reçus100,00MAD ; référence Attestation fictive B.

N-1 : choisir B4-N1, même statut, justification Relevé fictif709 N-1. Ajouter
une ligne2510 : Atlas Industrie fictive ; identifiant vide ; valeur brute3000,00 ;
capital500000,00 ; quote-part20 ; produits reçus0 explicitement ; référence Attestation fictive N-1.

Toutes les références et entités ci-dessus sont fictives. Le capital et le
pourcentage sont des données déclarées indépendantes :20% ne se calcule pas
à partir de2500/500000. Une donnée inconnue reste vide, un zéro est explicite.

## Parcours et contrôles indépendants

1. Noter le nombre d’écritures au Journal et ajouter un logo fictif aux paramètres société.
2. Importer les CSV dans une préparation, contrôler puis conserver une nouvelle version. Le Journal doit rester inchangé.
3. Ouvrir Documenter les émetteurs des participations. Saisir N puis N-1 ci-dessus ; revenir à N pour vérifier que le brouillon est préservé.
4. Cocher Je confirme les données et déclarations saisies, sans valider une liasse complète. Cliquer Conserver les tableaux ETIC dans une nouvelle version.
5. La nouvelle version est immédiatement sélectionnée. Rouvrir le formulaire. Contrôle N :2500+1500=4000 ; écart4000−4000=0. N-1 :3000−3000=0.
6. Dans la version conservée, modifier la valeur brute de la première ligne N en2499,99. Les contrôles affichés concernent toujours la version conservée, donc écart0 tant que ce brouillon n’est pas enregistré.
7. Confirmer et conserver à nouveau. Le nouveau contrôle N devient2499,99+1500−4000=−0,01MAD. Revenir à la version précédente : son écart reste0.
8. Télécharger PDF, Excel et dossier ZIP de la nouvelle version ; vérifier les données et le logo.

Si une valeur brute d’une ligne est inconnue, la somme de son compte et son
écart restent indisponibles. Le capital, la quote-part ou les produits reçus
peuvent rester inconnus sans empêcher un rapprochement brut dont toutes les
valeurs brutes sont connues. Une déclaration Néant avec un solde251 non nul
garde une alerte visible ; elle ne crée pas un zéro pour faire disparaître l’écart.

Les montants signés valeur brute et produits reçus ont deux décimales maximum.
Le capital est non négatif et a deux décimales. La quote-part va de0 à100 et
accepte au plus douze décimales. NaN, infinis et précisions monétaires excessives
sont refusés. Aucun taux fiscal ou règle de détention juridique n’est ajouté.
En l’absence de source N-1 détaillée, sa saisie est désactivée et le contrôle
reste indisponible. Les montants sont des contre-valeurs MAD documentées :
aucun cours de change ni conversion automatique n’est inventé.

## Exports et traçabilité

PDF : déclarations, références, auteur/date/version source, contrôles conservés
par compte et logo actuel. Excel : Origine émetteurs, Émetteurs N/N-1,
Déclaration émetteurs N/N-1 et Contrôle émetteurs N/N-1. Le pourcentage est un
texte décimal exact ; une cellule vide ne se transforme pas en0. Les textes
commençant par un signe égal restent des textes. Les montants trop grands pour
être représentés exactement comme nombres Excel sont exportés comme textes.

ZIP : declarations_emetteurs.json et les exports/source/pièces du dossier,
avec MANIFESTE_SHA256.json. Les anciennes versions et les autres compléments
restent inchangés ; les pièces restent rattachées à leur version d’origine.
Le logo actuel figure dans les exports et reste extérieur à l’empreinte
historique du contenu. Une note B4 déclarée non applicable alors que des
émetteurs sont saisis conserve une alerte ; aucune correction silencieuse.

## Recette humaine à effectuer

Prérequis communs ci-dessus ; conserver captures des versions, exports et
Journal. Aucun test automatisé ne remplit le résultat réel de votre recette.
Aucune écriture comptable ni liquidation fiscale n’est créée par ce formulaire.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|E709-01|Importer N et N1 du lot707, conserver ; saisir les deux lignes N et la ligne N-1 détaillées ci-dessus.|Comptes disponibles2510 uniquement ; brouillons préservés en changeant de période. Capture des trois lignes.|Non testé|
|E709-02|Confirmer puis conserver ; rouvrir N puis N-1.|Nouvelle version immédiatement sélectionnée ; N somme4000/écart0 ; N-1 somme3000/écart0. Capital et quote-part Rif inconnus, produits N-1 explicitement0. Capture des contrôles.|Non testé|
|E709-03|Modifier2500 en2499,99 dans N sans enregistrer, examiner les contrôles puis confirmer et conserver.|Avant enregistrement, contrôle conservé toujours0 ; après, nouvelle version écart−0,01. Version précédente toujours écart0, Journal inchangé. Captures des deux versions.|Non testé|
|E709-04|Dans un autre brouillon, saisir quote-part101 puis conserver ; corriger en20 et reconfirmer. Créer aussi une préparation N seul et ouvrir B4-N1.|101 refusé avec erreur lisible et brouillon conservé ; correction réinitialise confirmation puis réussit. N-1 absent : saisie désactivée et contrôle indisponible. Captures erreur et période absente.|Non testé|
|E709-05|Avec logo fictif, télécharger PDF, Excel et ZIP de la version du cas03 ; ouvrir les fichiers.|Montants signés, écart−0,01, données inconnues distinctes du0, références/auteur/source et logo présents. JSON contrôles identiques à l’écran, manifeste vérifiable. Conserver trois exports.|Non testé|
|E709-06|Se connecter comme lecteur à la société fictive ; ouvrir la version du cas02 et télécharger le ZIP.|Champs désactivés, aucun bouton de conservation, consultation et téléchargement autorisés ; aucune nouvelle version/écriture. Capture droits et ZIP.|Non testé|

## État et limites

Le développement et les tests automatisés du complément sont consignés dans
le rapport709. La recette humaine reste à effectuer ; l’ouverture Word/Excel
sur votre poste et la mise en production ne sont pas validées automatiquement.
La préparation indépendante ne devient pas une liasse complète ou prête à déposer.
Les mouvements ETIC, la fiscalité autonome et les validations réglementaires
restent des travaux distincts. RH/paie et point6 humain restent différés.
