# HisabPro — reprise du 18 octobre 2026, hors RH et paie

Les priorités hors RH/paie restent actives. Cette livraison améliore des parcours
existants et ajoute deux outils de préparation ; elle ne termine pas toute la
roadmap. La recette utilisateur et la mise en production restent à effectuer.

## Modifications utilisables

| Lot | Utilisation et contrôle | Rapport |
|---|---|---|
| 553 | Inventaire : refus des montants invalides et comptes incompatibles ; contrôle de continuité des exercices décalés avant contrepassation. Les sept modèles existaient déjà. | [Tests et limites](../../Test/rapport_ajustements_inventaire_553.md) |
| 555 | Clôture → ajustements : préparer les données, afficher l'aperçu des lignes et dates, puis créer. Toute modification invalide l'aperçu. Consultation seule protégée. | [Aperçu](../../Test/rapport_apercu_inventaire_555.md) |
| 557 | Calendrier des périodes : un administrateur peut rouvrir une période d'un exercice encore ouvert, avec motif et audit. Un exercice définitivement clôturé reste verrouillé. | [Réouverture](../../Test/rapport_reouverture_periodes_557.md) |
| 559 | TVA → assistant RAS TVA : renseigner explicitement les faits du cas couvert pour obtenir une simulation. Une information manquante reste à compléter. Aucune retenue, écriture ou déclaration n'est créée. | [Périmètre limité](../../Test/rapport_ras_tva_simulation_559.md) |
| 561 | Liasse → préparation des ventes : comparer le HT documentaire aux mouvements validés711/712 ; consulter les écarts et exporter. Excel et CSV détaillent les mouvements. Un écart nul ne prouve pas le rattachement individuel des factures. | [Raccordement](../../Test/rapport_ventes_raccordement_561.md) |
| 563 | Installation technique : chaîne existante jusqu'à098 exécutée puis rejouée sur une base vierge jetable. Aucun ancien SQL réécrit. | [Installation](../../Test/rapport_installation_vierge_098.md) |
| 567 | Sauvegarde/restauration isolée : nouveaux relevés de ventes, logo et simulation retrouvés après reprise, sans modification des tables métier pendant les lectures. | [Restauration](../../Test/rapport_restauration_ventes_ras_567.md) |

[Exemple PDF fictif avec logo](exemples/VENTES_RACCORDEMENT_LOGO_FICTIF_20261018.pdf).
Les montants de ces exemples sont exclusivement des données de test.

## Résultats propres aux lots

Commandes réellement exécutées dans cette reprise, suites recouvrantes :

- 553 :83 tests connexes réussis ; le défaut de calendrier a été reproduit puis corrigé.
- 555 :34 tests connexes réussis, dont les réponses HTTP retardées et les droits.
- 557 :37 tests regroupés natifs PostgreSQL et Edge réussis.
- 559 :49 tests ciblés puis16 connexes réussis, dont le navigateur mobile et trois rôles.
- 561 :28 tests regroupés réussis ;12 tests historiques exécutés dans leur banc
  d'origine et1 test de logos PDF/Excel réussi. Lecture concurrente testée en
  transaction cohérente sur une seule connexion SQL.
- 563 :1 test d'installation réussi,114 exécutions SQL dont25 relectures,
  89 fichiers distincts. Tables métier vides, références existantes conservées.
- 567 :1 test de restauration réussi ;74 tables, schéma, séquences et ACL
  identiques avant reprise ; texte PDF, CSV, empreinte et valeurs comparés.

Les builds frontend des lots555,557,559 et561 ont réussi. Les avertissements
et échecs intermédiaires sont consignés dans les rapports ; un ancien scénario
de données non finies reste testé dans son banc historique, sans désactiver les
contraintes modernes. Ne pas additionner ces chiffres comme des cas uniques.

La consolidation finale est décrite dans le
[rapport565](../../Test/rapport_consolidation_hors_rh_565.md).
Ses deux commandes successives ont réussi :356 tests en1183,64s, puis247 en
218,79s,29 avertissements dans chacune, aucun test ignoré ni échoué.

## État et suite

La [matrice](MATRICE_COUVERTURE_HISABPRO.md) conserve70 rubriques :16 terminées,
47 partielles,3 absentes et4 bloquées, y compris les rubriques RH différées.
Ce comptage ne représente pas un pourcentage de commercialisation.

- Développement : terminé pour les lots livrés dans leur périmètre ; globalement partiel.
- Tests automatisés : résultats limités aux suites effectivement exécutées.
- Recette utilisateur : à effectuer, point6 réservé au retour humain.
- Prêt pour production : non validé ; configuration, sauvegarde et déploiement
  de l'installation cible restent à qualifier.

Aucun PostgreSQL réel ni donnée comptable réelle utilisé. Aucun développement
RH/paie, aucun commit ni push. Les98 SQL existants et115 documents antérieurs
de guide/recette sont conservés. Les contrôles FEC/ETIC historiques ambigus
restent visibles ; aucune pièce ou information fiscale n'est inventée.

La suite prioritaire est le raccordement opérationnel de la RAS TVA aux
règlements, après vérification des règles et comptes applicables. Suivent les
variantes d'inventaire, annexes fiscales et le mode liasse seule. Le catalogue
DGI exhaustif, le schéma officiel EDI et les justificatifs historiques restent
des limites explicites : voir le [plan de finalisation](PLAN_FINALISATION_HORS_RH_20261018.md).

## Archives différentielles

Chaque archive conserve les chemins du dépôt. Le cumulatif final contient les
dernières versions des fichiers des lots, sans projet complet, base ou dépendances.

- [553](../../HisabPro_553_Inventaire_Ajustements_Calendrier.zip)
- [555](../../HisabPro_555_Inventaire_Apercu_Dates_Droits.zip)
- [557](../../HisabPro_557_Periodes_Reouverture_Audit_Mobile.zip)
- [559](../../HisabPro_559_RAS_TVA_Assistant_2026.zip)
- [561](../../HisabPro_561_Ventes_Raccordement_Comptable_Exports.zip)
- [563](../../HisabPro_563_Installation_Qualification_Chaine_098.zip)
- [567](../../HisabPro_567_Restauration_Ventes_RAS_TVA_Logo.zip)
- [565 — consolidation](../../HisabPro_565_Consolidation_Financiere_Hors_RH.zip)
- [Cumulatif553–569](../../HisabPro_Session_20261018_Hors_RH_553_569.zip)
