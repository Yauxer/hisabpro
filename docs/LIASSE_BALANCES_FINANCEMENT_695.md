# Financement documentaire depuis les balances conservées

Version 695 du 21 octobre 2026 — société fictive et base de test uniquement.

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
sélectionner une préparation puis **Préparer le tableau de financement depuis les balances**.
Les masses sont présentées depuis les balances N/N-1. Les flux doivent être
déclarés séparément, avec leur justification : une augmentation nette d’un
poste ne suffit pas à retrouver achats, cessions ou remboursements bruts.

## Saisir et conserver

Choisir **Flux à documenter**, puis **Période du flux**, renseigner le montant et
**Justification du flux**. Passer à un autre flux conserve les brouillons du
formulaire. Chaque zéro est une déclaration explicite et exige sa source.
Une cellule vide reste inconnue. Les flux N-1 ne sont ni copiés depuis N, ni
déduits de la seule balance N-1 ; ils sont désactivés si cette balance est absente.

Confirmer puis **Conserver le financement dans une nouvelle version**. Tous les
flux du formulaire sont conservés ensemble. La nouvelle version est sélectionnée
automatiquement. La partie emplois/ressources de chaque période reste inconnue
tant que les 16 flux et la CAF de cette période ne sont pas disponibles. Le
compteur décrit les flux saisis, pas la conformité ou la complétude fiscale.

La CAF doit recouper l’ESG conservé. Une balance après solde technique des
classes 6/7 ne permet pas de présumer une CAF nulle : les totaux concernés restent
indisponibles. Les variations et rapprochements N nécessitent la balance N-1.
Aucun rapprochement N-1 n’est présumé en l’absence de N-2.

L’écart de rapprochement est affiché. S’il est différent de zéro, revoir les
sources ; HisabPro ne modifie aucun flux pour annuler l’écart. Le diagnostic
du moteur partagé n’est pas une validation comptable ou fiscale indépendante.
Son seuil historique de rapprochement est 1 MAD ; l’indicateur `ecart_nul`
exige exactement zéro. Un écart de 50 centimes reste affiché et n’est pas déclaré nul.
Les cessions non ventilées restent visibles et à classer. Les calculs et leurs
libellés sont figés avec la version, jamais recalculés à sa relecture.

En cas de masses/totaux dépassant la borne technique de précision
9 999 999 999 999,99 MAD, les flux détaillés restent conservés exactement sous
forme décimale, mais les totaux sont indisponibles et une explication apparaît
dans l’interface, le PDF et l’Excel. Cette borne est technique, pas fiscale.

## Jeu de recette fictif et calcul indépendant

Prérequis : société fictive en MAD, exercice 2026, plan incluant les comptes
des fichiers, administrateur/comptable/lecteur et installation de test autorisée.
Importer les fichiers [N](recette/BALANCE_FICTIVE_FINANCEMENT695_N.csv) et
[N-1](recette/BALANCE_FICTIVE_FINANCEMENT695_N1.csv). Ces fichiers sont des
soldes de recette, pas des écritures à enregistrer dans une comptabilité réelle.
Les [16 flux chiffrés](recette/FLUX_FICTIFS_FINANCEMENT695.csv) et les
[données/oracle](recette/DONNEES_FINANCEMENT_FICTIF695.json) sont aussi fournis.

N : capital 10 000, dette de financement 5 000, produits 2 000, immobilisation 4 000,
clients 5 000, banque 8 000. Débit = crédit = 17 000 MAD. N-1 : capital 6 000,
clients 2 000, banque 4 000 ; débit = crédit = 6 000 MAD. Résultat/CAF N :
2 000 MAD ; N-1 : zéro.

Pour chaque cellule du tableau ci-dessous, utiliser comme justification
`État fictif FIN695 N` ou `État fictif FIN695 N-1` selon la période. Les zéros
sont fournis explicitement pour ce jeu fictif ; ne pas les recopier sur un
dossier réel sans source. Les flux N-1 sont facultatifs si l’on souhaite garder
le détail de cette période inconnu.

| Flux | N MAD | N-1 MAD | Source attendue |
|---|---|---|---|
|Distributions de bénéfices|0|0|État fictif FIN695|
|Cessions d’immobilisations incorporelles|0|0|État fictif FIN695|
|Cessions d’immobilisations corporelles|0|0|État fictif FIN695|
|Cessions d’immobilisations financières|0|0|État fictif FIN695|
|Cessions non ventilées — à classer|0|0|État fictif FIN695|
|Récupérations de créances immobilisées|0|0|État fictif FIN695|
|Augmentations de capital / apports|4000|6000|État fictif FIN695|
|Subventions d’investissement reçues|0|0|État fictif FIN695|
|Augmentations des dettes de financement|5000|0|État fictif FIN695|
|Acquisitions d’immobilisations incorporelles|0|0|État fictif FIN695|
|Acquisitions d’immobilisations corporelles|4000|0|État fictif FIN695|
|Acquisitions d’immobilisations financières|0|0|État fictif FIN695|
|Augmentations des créances immobilisées|0|0|État fictif FIN695|
|Remboursements des capitaux propres|0|0|État fictif FIN695|
|Remboursements des dettes de financement|0|0|État fictif FIN695|
|Emplois en non-valeurs|0|0|État fictif FIN695|

Oracle indépendant, en MAD : ressources stables N = 2 000 (CAF) + 4 000 (capital)
+ 5 000 (emprunt) = 11 000. Emplois stables N = 4 000 (acquisition).
Fonds de roulement N = 10 000 + 5 000 + 2 000 − 4 000 = 13 000 ; N-1 = 6 000,
variation = 7 000. BFG N = 5 000 ; N-1 = 2 000 ; variation = 3 000. Trésorerie
N = 8 000 ; N-1 = 4 000 ; variation = 4 000. Ainsi, 7 000 − 3 000 = 4 000 et
11 000 − 4 000 = 7 000 : écarts nuls.
Les montants n’impliquent aucune liquidation fiscale et aucune écriture n’est
créée par la préparation.

## Cas de recette utilisateur

Tous les cas sont **Non testé** côté utilisateur. Résultats réels, anomalies et
preuves restent vierges dans le classeur. Les tests automatisés sont rapportés
séparément. Utiliser les montants et références ci-dessus, sans les deviner.

| ID | Actions exactes | Résultat et preuve attendus | Statut |
|---|---|---|---|
|FIN695-01|Importer/conserver les deux balances. Ouvrir le financement sans saisir de flux.|Masses comparatives disponibles, CAF N/N-1 : 2 000/0 MAD ; les 16 flux par période sont inconnus. Aucun total emplois/ressources présumé. Capture initiale.|Non testé|
|FIN695-02|Renseigner les 16 flux N du tableau et leurs sources, confirmer/conserver. Rouvrir la nouvelle version.|Ressources : 11 000 ; emplois : 4 000 ; variations FR : 7 000, BFG : 3 000, trésorerie : 4 000 MAD. Écarts nuls. Ancienne version intacte ; flux N-1 inconnus. Capture et export.|Non testé|
|FIN695-03|Renseigner ensuite les 16 flux N-1 du tableau avec leurs sources puis conserver.|Nouvelle version : ressources N-1 = 6 000, emplois N-1 = 0 MAD. Données N inchangées ; aucun rapprochement N-1 depuis N-2 inventé. Capture comparatif.|Non testé|
|FIN695-04|Sur la version précédente, changer les distributions N de 0 à 1 000, source `Décision fictive FIN695 à vérifier`, confirmer/conserver.|Ressources N : 10 000 ; emplois : 4 000 ; écart : −1 000 MAD. Aucun ajustement automatique ; version antérieure intacte. Capture de l’écart.|Non testé|
|FIN695-05|Sur une nouvelle préparation, saisir 0 sans source puis conserver ; ajouter `Revue fictive FIN695` et confirmer/réessayer. Refaire l’import N seul pour tester N-1 absent.|Premier envoi refusé, brouillon conservé. Réessai : un seul flux connu, totaux inconnus. Sans balance N-1, saisie N-1 désactivée et rapprochement indisponible. Captures des refus/états.|Non testé|
|FIN695-06|Sous lecteur, consulter la version issue du cas FIN695-02, télécharger PDF/Excel/ZIP. Refaire depuis une autre société sans accès.|Aucun bouton de conservation ni champ éditable ; mêmes chiffres et empreinte, logo actuel PDF/Excel, financement_documentaire.json dans le manifeste ZIP. Autre société refusée. Conserver captures et fichiers.|Non testé|

## Exports, droits et limites

PDF, Excel et dossierZIP reprennent le calcul et les flux conservés. Le ZIP
contient `financement_documentaire.json`, couvert par son manifesteSHA256.
L’identité et le logo actuels des rendus restent hors empreinte historique.
Les anciennes versions ne sont pas modifiées. Les autres notes/ventilations
restent conservées ; les pièces restent attachées à leur version d’origine.

Pas de nouvelle migration. Aucune écriture, aucun ajustement du Journal, aucune
déclaration ni XML/EDI n’est créé. Les flux saisis ne sont pas vérifiés contre
des pièces non fournies. [Sources et portée](audit/SOURCES_FINANCEMENT_20261021_695.md).
La recette utilisateur, les tableaux ETIC structurés et les compléments fiscaux
restent à effectuer/compléter. HisabPro n’est pas présenté comme certifié.
