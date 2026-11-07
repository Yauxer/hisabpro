# Lot 553 — Ajustements d'inventaire et continuité des exercices

L'assistant existant contient déjà sept modèles : CCA, PCA, FNP, FAE,
provisions pour risques et dépréciations clients/stocks. Il n'a pas été recréé.
RH et paie sont différées à la demande de l'utilisateur.

## Corrections

- Refus métier des montants non finis, malformés ou hors capacité NUMERIC(18,2),
  avant insertion. Arrondi au centime conservé ; booléens refusés.
- Numéros de compte sur dix chiffres maximum. Les contreparties CCA/PCA/FNP/FAE
  restent celles des modèles existants, avec leurs subdivisions ; un appel API
  ne peut plus remplacer la contrepartie fixe de l'écran par un compte de capital.
- Tailles du libellé et des comptes contrôlées par le schéma API.
- Un exercice suivant déjà présent avec une date de début non contiguë est
  refusé explicitement. Ses dates ne sont jamais déplacées automatiquement.
  Contrôle partagé par les ajustements, la préparation N+1 et la clôture.
- Pour un exercice décalé cohérent, contrepassation au lendemain de la clôture,
  sans supposer le 1er janvier. Suppression des seuls brouillons ; une écriture
  validée reste intacte et bloque la suppression de son ajustement.

## Preuves

Tests historiques initiaux : 15 réussis, 1 avertissement, 0,61 s.
Reproduction des entrées invalides : 15 échecs / 8 réussites avant correction.
Après correction : 38 réussis, 1 avertissement, 0,75 s.

Première exécution API/PostgreSQL isolé : 19 réussis / 1 échec en 49,01 s.
L'échec a révélé une contrepassation au 01/01/2026 pour un exercice clos le
30/06/2025, avec N+1 civil déjà créé à l'inscription. Correction du contrôle
partagé puis décision explicite de calendrier via l'API administrateur.
Suite suivante : 59 réussis, 29 avertissements, 48,28 s.

Les sept modèles sont contrôlés indépendamment : deux lignes attendues,
montant 1 200,13 MAD, sens débit/crédit, dates, exercice, brouillon,
contrepassation pour les quatre cut-off, puis validation et refus de suppression
sans mutation. Douze entrées invalides sont refusées sans écriture ni calendrier
supplémentaire. Les tests exécutent l'API sous rôle SQL applicatif limité.

Extension finale après maintien du message historique : **83 réussis,
29 avertissements, 154,26 s, code 0**. Elle couvre aussi les tests existants de
reprise d'ouverture, deux clôtures et les messages affichés dans Edge.
Six fichiers Python compilés. Frontend inchangé dans ce lot.

## Limites

Aucune migration et aucune connexion au PostgreSQL de l'utilisateur.
Les accès aux textes MEF/CNC et CGNC OEC ont encore échoué (timeout/502) ;
aucune nouvelle règle fiscale ou obligation réglementaire n'est revendiquée.
Les contrôles alignent l'API sur les modèles et les contraintes déjà présents.

Les montants restent déterminés par le comptable sur ses justificatifs.
Pas de calcul documentaire automatique ni de reprise automatique des provisions.
Recette utilisateur et mise en production non validées.

Prochaine étape : aperçu des écritures avant création, dates réelles à l'écran,
et contrôle des actions d'inventaire proposées en consultation seule.
