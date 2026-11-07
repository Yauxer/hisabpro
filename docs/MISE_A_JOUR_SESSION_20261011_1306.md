# Mise à jour HisabPro — session11octobre2026, début13h06UTC

## Contenu à installer

Le ZIP cumulatif différentiel `HisabPro_Session_20261011_1306_Cumulatif_Verifie.zip` réunit les versions finales des lots371,372,373,374,375 et377, avec l'arborescence exacte. Copier ses fichiers dans le dépôt existant puis redémarrer backend et frontend avec ces mêmes versions. Aucun fichier de configuration, migration, dump, environnement ou dépendance n'est inclus. Aucune commande SQL n'est nécessaire pour ce lot ; `models.py`, `main.py` et les migrations n'ont pas été modifiés.

## Utilisation et vérification

Dans le cycle vente ou achat, ouvrir Règlements puis « Ventiler par tiers ». Sélectionner un tiers natif, saisir le montant total et répartir manuellement ses centimes entre ses factures validées ouvertes de même sens. Le total doit correspondre exactement ; solde, avoirs, acomptes et RAS connus sont respectés. Une à50factures sont autorisées. Les modes immédiats sont disponibles ; chèques/effets ne sont pas regroupés dans ce flux.

Les règlements individuels partagent la référence saisie. L'opération est atomique et sa répétition identique conserve les identifiants existants. Une modification ou annulation après succès ne constitue pas une reprise identique. Les écritures suivent le flux de validation normal ; le lettrage reste une action comptable distincte.

Le [guideWordv11](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx) et sa [versionPDF](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf),28pages, expliquent le laboratoire2026 indépendant de la recette annuelle2025 :factures120/240TTC, règlement240ventilé120/120, puis solde120 ;5écritures, débit/crédit720 et tiers360/360. Les résultats humains restent à renseigner.

La page Clôture conserve désormais les données du dernier exercice sélectionné même lorsqu'une réponse de l'ancien exercice arrive plus tard. Les anciens règlements liés à des factures après la première page restent visibles.

## Preuves et limites

- [Pagination371](../Test/rapport_reglements_pagination_371.md) :28tests réussis.
- [Ventilation372](../Test/rapport_reglements_par_tiers_372.md) :108ciblés connexes puis4Edge finaux réussis ; validation et lettrage réels.
- [Globale373](../Test/rapport_non_regression_reglements_373.md) :3235réussis,4échecs,0erreur/ignoré,code1,4419,71s. Ne pas présenter cette globale comme verte.
- [Reprise377](../Test/rapport_regression_recette_377.md) :3E2E clôture,8bancs et9connexes réussis ; build0. Nouvelle globale après corrections non exécutée.
- [Matrice](audit/MATRICE_COUVERTURE_HISABPRO.md) :70fonctions ;[checklist](audit/CHECKLIST_UTILISATEUR_20261007.md) :73demandes ;[registre](audit/REGISTRE_ANOMALIES_HISABPRO.md) conserve les limites.

Les paiements ventilés ne sont pas un instrument bancaire unique. Annulation groupée et rapprochement à une seule ligne bancaire restent à développer. Aucun PostgreSQL réel ou donnée comptable réelle utilisé ; tests sur bases jetables protégées. GuideOffice et recette utilisateur à effectuer. Développement global partiel, tests ciblés validés, production non validée.

Prochaine reprise :relancer la globale après377 puis poursuivre la recette annuelle connectée et le rapprochement des paiements ventilés. Lire intégralement AGENTS.md et CODEX_PROGRESS.md, examiner le journal actif et les processus avant toute reprise.
