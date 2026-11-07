# Reprises partielles de provisions — utilisation et installation

Cette fonctionnalité est un suivi interne lié aux dotations créées dans
HisabPro. Elle ne détermine ni la disparition d’un risque, ni la déductibilité
fiscale, ni les mouvements manuels antérieurs. Recette utilisateur à effectuer.

## Installation distincte du démarrage

Le correctif ajoute `hisabpro-backend/100_reprises_provisions.sql`. Il ne modifie
aucune ancienne migration, aucune donnée existante et aucun modèle chargé par
`Base.metadata.create_all`. Aucun SQL n’est lancé automatiquement au démarrage.

La chaîne de migrations existante doit être installée jusqu’à099 ;100 utilise
notamment les registres/protections083 et le verrou Journal/clôture098.
Avant tout déploiement réel, l’administrateur conserve une sauvegarde vérifiée,
applique100 avec le propriétaire du schéma sur une copie isolée de son dossier,
puis vérifie le démarrage et les droits du rôle applicatif `hisabpro`.
L’exécution réelle n’a pas été effectuée par Codex.

Sans100, l’application conserve son démarrage et les flux préexistants ; ouvrir
le panneau des reprises affiche une indisponibilité explicite mentionnant100.
Les registres reçoivent SELECT/INSERT pour le rôle applicatif, sans droit
UPDATE/DELETE/TRUNCATE. Le rejeu de100 conserve les données et les droits.

## Créer une reprise

1. Dans **Clôture**, ouvrir **Reprises partielles de provisions**.
2. Sélectionner une dotation. La liste comprend aussi les exercices antérieurs.
   Une source en brouillon doit d’abord être validée dans le Journal. Une
   source absente, déjà contrepassée ou incohérente reste à vérifier.
3. Lire la dotation initiale, les reprises validées actives, les réservations
   de brouillons et le disponible du registre. Ces chiffres ne remplacent pas
   le grand livre : des reprises manuelles non liées peuvent exister.
4. Saisir date, montant au centime et justification. La date doit appartenir
   à un calendrier préparé et à une période ouverte, sans précéder la source.
   Référence et date de pièce restent facultatives pour créer/valider ; le
   contrôle FEC peut ensuite signaler un justificatif manquant.
5. Cliquer **Vérifier la reprise**. Contrôler les comptes et leurs libellés,
   le débit de la provision et le crédit du produit de reprise.
6. Confirmer la vérification des mouvements et justificatifs, puis
   **Créer le brouillon de reprise**. Le reliquat est actualisé sansF5.
7. Ouvrir le Journal et valider le brouillon selon le flux habituel. Une
   répétition de la même demande technique ne crée pas de deuxième pièce.

Une nouvelle dotation doit rester une nouvelle source distincte. Le logiciel
ne rapproche pas automatiquement des provisions à partir de libellés similaires.
Les sources reconnues sont risques/charges, dépréciation client et stock ; une
nature non qualifiée n’est pas remplacée par un compte supposé.

L’aperçu précise la capacité pour la date demandée, en tenant compte des reprises
futures déjà réservées. Une annulation validée en juin ne libère pas de capacité
pour une nouvelle reprise de mars. Le disponible final affiché dans le suivi
peut donc différer de la capacité utilisable pour une date antérieure.

## Annuler une reprise

Dans le même panneau, cliquer **Annuler la reprise**, choisir une date ouverte
et fournir le motif. Le logiciel conserve l’original et crée un inverse en
brouillon. La réservation n’est libérée qu’après validation de la reprise
originale **et** de cet inverse. La validation de l’inverse seul est refusée
si l’original est encore en brouillon ; le lot du Journal peut traiter les deux
dans le bon ordre. Une annulation différente répétée est refusée explicitement.

Ne pas modifier/supprimer/contrepasser ces pièces depuis les commandes génériques
du Journal : elles sont protégées pour préserver le registre et la source.
Une source liée garde cette protection même après annulation de ses reprises.
Les corrections historiques exceptionnelles restent une opération distincte.

## Exemple de contrôle fictif

Dotation1000MAD, reprise400 : disponible600. Après validation de400, reprise
supplémentaire200 en brouillon : reprises validées400, réservation200,
disponible400. Annuler400 sans valider l’inverse laisse le disponible400.
Après validation de l’inverse : disponible800, dont200 encore réservés.
Aucun chiffre de cet exemple ne doit être saisi dans une société réelle.

Les tests automatisés, leurs limites et leurs commandes sont consignés dans
`Test/rapport_reprises615.md` et `CODEX_PROGRESS.md`.

## Télécharger le suivi — complément617

Sélectionner une dotation, puis **Télécharger le suivi PDF** ou
**Télécharger le suivi Excel**. Ces commandes existent aussi en consultation
seule. Elles relisent les faits courants et affichent le suivi correspondant,
avec identité et logo de la société, originaux/inverses, références déclarées,
réservations et disponible final. Le document explique que les mouvements
manuels non liés ne sont pas attribués par défaut.

Si le suivi ou l’identité change pendant le téléchargement, actualiser et
relancer. Une source incohérente reste exportable avec son diagnostic. Le
document ne constitue ni un dépôt fiscal ni une archive annuelle ; son empreinte
SHA identifie les données exportées et n’est pas une signature.

L’Excel contient les feuilles **Synthèse**, **Reprises** et, si un logo existe,
**Logo société**. Les grands montants dépassant la précision Excel restent en
texte exact : ne pas les convertir en nombre flottant. Les références saisies
comme des formules sont conservées en texte, sans exécution.


## Vérifier l’installation sur une base vierge jetable623

Depuis la racine, lancer :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/recette_installation_vierge_100.py --rapport .codex-tests/verification_installation100.md
```

Ce programme crée uniquement son propre cluster nonce, n’accepte aucune URL
externe et ne migre pas l’installation active. Il vérifie91SQL distincts,
27rejeux,77tables, droits minimaux, triggers et préservation du schéma/des
données au rejeu, puis supprime son cluster. La base utilisateur reste hors
de ce programme. Un échec doit être conservé et analysé, pas remplacé par un
test sur un dossier réel. [Rapport100](../Test/rapport_installation_vierge_100.md).

## Lire les exercices décalés et les inverses — complément625

Chaque ligne du suivi distingue la date et l’exercice de la reprise, puis la
date et l’exercice de son inverse. L’Excel ajoute ces deux exercices dans les
colonnes N/O ; le PDF les indique aussi. Exemple de laboratoire : une pièce
datée du01/07/2025 peut appartenir à l’exercice2026, son inverse du01/07/2026
à l’exercice2027, suivant les calendriers préparés. Ne pas renommer les dates
pour les faire correspondre à la référence de l’exercice.

Une reprise déjà close peut recevoir un inverse dans une période ultérieure
ouverte via le suivi. Les pièces closes restent conservées ; les contrôles
de clôture/fiscalité gardent leur fonctionnement, y compris la confirmation
explicite d’une imputation de déficit lorsque le dossier l’exige.
