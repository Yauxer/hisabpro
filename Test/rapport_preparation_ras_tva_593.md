# Préparation mensuelle des retenues TVA opérées — lot593

La page Déclaration TVA et l'onglet Retenues TVA de la liasse proposent une
préparation mensuelle en lecture seule. Le mois sélectionné consulte les
paiements du mois précédent, y compris décembre → janvier. Seules les captures
TVA guidées opérées sur achats sont retenues. Les ventes restent dans le registre
annuel distinct. Aucun schéma ni fichier de démarrage modifié.

Les captures saisies, actives, actives avec OD validée et annulées sont séparées.
L'état est courant, y compris pour une annulation postérieure au mois étudié :
il ne corrige pas automatiquement un bordereau déjà déposé. Un montant inconnu
reste inconnu, accompagné de la partie certaine. Aucun reste à payer, versement
effectif, remboursement ou crédit fiscal n'est présumé.

Les exports CSV, Excel et PDF reprennent la même source RO/RR sur une connexion,
l'identité de société, les montants exacts et une empreinte des données. Excel
et PDF reprennent son logo. Une source changée exige une actualisation avant
export. Les utilisateurs en consultation disposent du même accès en lecture.
Une installation sans099 signale l'indisponibilité sans DDL ni faux total nul.

Le recalcul TVA démontait les panneaux de retenues et perdait leur saisie.
Ce défaut a été reproduit avec une lecture PostgreSQL réellement bloquée,
puis corrigé en conservant les panneaux pendant le chargement. L'identité et
le calendrier doivent être connus avant leur première ouverture. L'impression
reste protégée pendant le calcul. Le libellé du crédit d'ouverture suit aussi
l'année civile TVA sélectionnée au lieu de l'année de clôture de l'exercice.
Les dates du calendrier sont contrôlées avant conversion ; une chaîne vide
ne devient plus une année0. Les lectures TVA attendent l'identité et le
calendrier. Un scénario Edge bloque réellement la lecture des exercices
pendant l'ouverture, puis vérifie les requêtes et l'impression à la reprise.

## Preuves exécutées

- Reprise591 :140 tests regroupés réussis,349,56s, avant le nouveau lot.
- Montage initial :17 réussis/1 échec de facture future ; règle produit conservée.
- Montage suivant :16 réussis/1 échec de secret local du test calendrier ; puis
  une erreur de paramètre dans son helper. Montages corrigés sans bypass métier.
- Calendrier décembre/janvier :1 réussi,29,11s, routes réelles et PostgreSQL nonce,
  horloge seule contrôlée dans TestClient. Les parcours Edge utilisent l'horloge réelle.
- Absence099 :1 réussi,22,90s. Restauration native :1 réussi,82,00s ;75 tables,
  données, ACL et séquences identiques, dossiers et exports restitués, cibles supprimées.
- Régression de chargement : échec reproduit43,49s, puis16 Edge réussis177,15s.
- Libellé année civile :1 réussi31,18s. Build final produit :5,07s, code0.
- Banc157 initial :156 réussis/1 échec d'attente d'impression de l'ancien test
  lecteur. Attente asynchrone corrigée ; cible1 réussie33,21s.
- Relance157 :156 réussis/1 échec révélant une requête d'année0 avant chargement
  du calendrier. Cause produit corrigée et scénario natif de retard ajouté.
- Après protection du calendrier :9 cibles UI réussies81,30s, dont les deux
  parcours TVA ordinaires et les attentes PostgreSQL réelles.
- Validation globale de livraison : **158 réussis, aucun échec ni ignoré**,
  347.43s, code0, JUnit `consolidation593_validee.xml`.

Les avertissements Pydantic/pytest et de taille du bundle Vite sont conservés.
Les résultats intermédiaires ne sont pas additionnés aux résultats finaux.

## Limites et reprise

Aucun accès au PostgreSQL utilisateur. L'installation cible de099 et la recette
humaine restent à effectuer. La préparation n'est pas un bordereau administratif
et reste hors archive fiscale définitive. Déclaration TVA complète, règles
d'imputation, modèles officiels et justificatifs du versement restent ouverts.
RH/paie et retour utilisateur réservé sont différés.

Guide livré : `docs/guides/UTILISATION_PREPARATION_RAS_TVA_20261018.pdf`.
Prochain lot indépendant : calcul documentaire facultatif CCA/PCA, sans règle
de déductibilité déduite ni génération automatique d'écriture définitive.
