# Lot506 — Deux clôtures décalées et cession après reprise

## Défauts reproduits et correction

Après une reprise d'ouverture explicite, la cession recalculait les annuités
antérieures déjà couvertes : une AM2022 était créée rétroactivement, en plus
des trois pièces attendues pour la cession dans l'exercice courant.
Le premier parcours navigateur des deux clôtures passait déjà ; ce défaut
a été reproduit séparément par l'API sur PostgreSQL temporaire.

La sortie reconnaît maintenant la reprise liée à l'immobilisation par sa
référence exacte `RECON-OPEN-exercice-id`, dans la même société. La reprise
doit être validée, en journal AN, à la date de début de son exercice. Aucune
annuité antérieure à cette ouverture n'est recréée. Une sortie antérieure à
la reprise est refusée. Le cumul réellement comptabilisé est comparé au plan
à la date de sortie ; un écart ancien bloque l'opération au lieu de disparaître
avec le retrait du bien. Un refus annule aussi les dotations préparées dans la
transaction. Aucun commit intermédiaire ni réécriture d'une pièce définitive.

La lecture du cumul doit suivre le flush transactionnel des lignes nouvelles :
la session sans autoflush ne les voyait pas lors du premier essai du correctif.
Les tests ont détecté ce défaut du premier essai avant livraison.

La sortie ignorait aussi les corrections RECON-AMORT : elle refusait une
correction seule, un complément ou une reprise d'excès malgré une dotation nette
exacte. Le contrôle annuel compare désormais la somme signée des AM et
RECON-AMORT exactes de la même société et du même exercice au plan arrêté à
la sortie. Une correction suffisante ne provoque aucune nouvelle AM.
Les montants incohérents restent refusés ; les méthodes et taux sont inchangés.

## Parcours et oracles

Bien fictif10000MAD, linéaire5ans, service01/01/2022. Reprise explicite au
01/07/2023 : brut10000, amortissements3000, contrepartie4481 de7000 choisie
explicitement. Aucune ancienne dette ou information fiscale n'est supposée.

- Exercice2024, du01/07/2023 au30/06/2024 : dotation2000, cumul5000,
  résultat net−5000 avec la CM3000 du laboratoire, AN au01/07/2024.
- Exercice2025 sans cession : dotation2000, cumul7000, VNC3000,
  résultat net−5000, AN au01/07/2025. Les deux clôtures sont déclenchées
  dans Edge. Le second refus409 de continuité est affiché dans une alerte ;
  les dates de2026 encore vide sont corrigées dans le formulaire réel, puis
  la clôture est relancée. Aucune erreur JavaScript ni réponse API500 attendue.
- Cession au31/12/2024 : seule dotation courante1000, cumul6000/VNC4000,
  vente7500HT +TVA fournie1500 =créance9000, gain3500. Trois pièces nouvelles
  seulement, toutes en2025 au31/12/2024. Résultat de2025 :2500 avant impôt,
  −500 après CM3000 du laboratoire. Pas d'AM2022 recréée.
- Cession au30/06/2025 après correction seule2000, complément1500 sur AM500,
  ou reprise1000 sur AM3000 : charge nette2000, cumul7000/VNC3000,
  gain4500. Deux pièces nouvelles seulement, aucune nouvelle AM.
- Reprise brouillon, cumul ancien insuffisant/excessif et sortie avant reprise :
  refus409, sources et toutes tables métier conservées, hors audit de refus.

Les deux variantes de cession vont jusqu'à la validation, la clôture, le FEC
et les AN sans immobilisation résiduelle. La cession reste une créance3481,
sans encaissement ni tiers acheteur inventé ; ces tests ne prouvent pas un
lettrage client ni une facture de cession. Fiscalité réelle non qualifiée.

## Exécutions réelles

- Avant correctif :1échec/1réussite,29avertissements,35,46s.
- Trois refus historiques avant correctif :3échecs,2désélectionnés,
  29avertissements,30,36s.
- Premier essai du correctif avant flush :2échecs/3réussites,
  29avertissements,38,94s.
- Après flush :5réussites,29avertissements,39,01s.
- Extension des corrections :4échecs/5désélectionnés,29avertissements,31,51s.
  Trois défauts produit ; le quatrième était un prérequis absent du test avant
  reprise (aucun exercice à cette date), corrigé par création explicite de la
  période fictive. L'assertion de refus ciblé n'a pas été affaiblie.
- Module neuf cas :9réussites,29avertissements,46,64s, code0.
- Qualification finale : **110réussites,29avertissements,332.60s**, code0,
  aucun échec/erreur/ignoré. Sources figées vérifiées par empreintes. Oracles
  503/504/501/499/497/495/493, Edge, PDF, restauration098 et ancien E2E conservés.
  Restauration :74tables, source préservée/cibles supprimées, fonctions098 et
  refus409/reprise intacts. Invariants0 :pièces déséquilibrées, montants non
  finis, définitives sans numéro/date. Trois Python du lot et neuf du cumulatif
  compilés ;98SQL/115guides, main/models/AGENTS conservés.

Commande finale : `Test/run_unit_tests.py Test/test_consolidation_deux_clotures506_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_patch05_livre_inventaire.py Test/test_e2e_cloture_isole.py -ra`.

## Installation et limites

Installer le routeur avec les services503 et les prérequis497/499 déjà livrés,
puis redémarrer l'API. Aucune nouvelle migration, aucune réparation automatique
des reprises ou cessions déjà validées. Les incohérences historiques demandent
des justificatifs et une décision traçable sur période ouverte.

Le bornage porte sur les reprises explicites reconnues ; les données anciennes
sans lien technique ou une autre convention de référence ne sont pas assimilées
arbitrairement à ces reprises. Autres méthodes/dates, reclassements, SQL arbitraire,
concurrence avec les modifications manuelles du Journal et vente liée à un tiers
restent à qualifier. Recette utilisateur, production et point6 toujours en attente.
