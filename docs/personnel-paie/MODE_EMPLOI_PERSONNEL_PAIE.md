# Personnel & Paie — point d'entrée de la recette

[Dernière qualification921](RESULTATS_PAIE_921.md) · [RNI mensuel préparatoire](RNI_MENSUEL_PREPARATOIRE_921.md).


Utiliser une **copie isolée et restaurable**. Aucun des documents ci-dessous ne valide une recette utilisateur ou une mise en production automatiquement. Les chiffres et justificatifs fournis sont fictifs.

[Bilan courant907–909](BILAN_SESSION_PAIE_907_909.md) · [Installation119/120 sur copie](BASES_FISCALES_CONNECTEES_909.md) · [Suite exacte](REPRISE_PAIE_APRES_BASES_909.md).

Historique :[bilan897–905](BILAN_SESSION_PAIE_897_903.md) et [installation116–118](INSTALLATION_COPIE_PAIE_116_118.md).

| Ordre | Parcours disponible | Mode d'emploi et données | Cahier PDF | Suivi Excel |
|---|---|---|---|---|
| 1 | Personnel, contrats, rémunérations contractuelles, accès, régimes déclarés, coffre et banque | [Guide887](COFFRE_BANQUE_RH_887.md), [données](JEU_DONNEES_PERSONNEL_887.json) | [59cas](CAHIER_RECETTE_PERSONNEL_HISABPRO_887.pdf) | [Personnel](SUIVI_RECETTE_PERSONNEL_887.xlsx) |
| 2 | Catalogue des éléments et règles séparées IR/CNSS/AMO | [Guide889](CATALOGUE_PAIE_889.md), [données](JEU_CATALOGUE_PAIE_889.json) | [12cas](RECETTE_CATALOGUE_PAIE_889.pdf) | [Catalogue](SUIVI_CATALOGUE_PAIE_889.xlsx) |
| 3 | Variables mensuelles :saisie, pièces référencées, soumission, approbation | [Guide891](VARIABLES_PAIE_891.md), [données](JEU_VARIABLES_PAIE_891.json) | [10cas](RECETTE_VARIABLES_PAIE_891.pdf) | [Variables](SUIVI_VARIABLES_PAIE_891.xlsx) |
| 4 | Campagnes et snapshots de simulation du brut | [Guide893](CAMPAGNES_BRUT_893.md), [données](JEU_CAMPAGNES_PAIE_893.json) | [Recette](RECETTE_CAMPAGNES_PAIE_893.pdf) | [Campagnes](SUIVI_CAMPAGNES_PAIE_893.xlsx) |
| 5 | Référentiel des charges sociales par branche/régime et versions datées | [Guide897](REFERENTIEL_SOCIAL_897.md), [données](JEU_SOCIAL_PAIE_897.json) | [6 cas](RECETTE_SOCIAL_PAIE_897.pdf) | [Social](SUIVI_SOCIAL_PAIE_897.xlsx) |
| 6 | Calcul social pédagogique connecté au brut, sources et historique | [Guide899](SIMULATIONS_SOCIALES_899.md), [données](JEU_CALCUL_SOCIAL_PAIE_899.json) | [6 cas](RECETTE_CALCUL_SOCIAL_PAIE_899.pdf) | [Calcul social](SUIVI_CALCUL_SOCIAL_PAIE_899.xlsx) |
| 7 | Contrôle annuel du barème général IR sur RNI déclaré, distinct de la paie mensuelle | [Guide901](CONTROLE_IR_ANNUEL_901.md), [données](JEU_IR_ANNUEL_PAIE_901.json) | [6 cas](RECETTE_IR_ANNUEL_PAIE_901.pdf) | [IR annuel](SUIVI_IR_ANNUEL_PAIE_901.xlsx) |
| 8 | Qualification séparée des frais professionnels et de la déductibilité IR salariale | [Guide907](QUALIFICATIONS_FISCALES_907.md), [données](JEU_QUALIFICATIONS_IR_PAIE_907.json), [sources](SOURCES_FISCALES_907.md) | [6 cas](RECETTE_QUALIFICATIONS_IR_PAIE_907.pdf) | [Qualifications](SUIVI_QUALIFICATIONS_IR_PAIE_907.xlsx) |
| 9 | Bases fiscales reliées aux sources brut/social, sans RNI définitif présumé | [Guide909](BASES_FISCALES_CONNECTEES_909.md), [données fictives](JEU_BASES_FISCALES_PAIE_909.json) | [6 cas](RECETTE_BASES_FISCALES_PAIE_909.pdf) | [Bases fiscales](SUIVI_BASES_FISCALES_PAIE_909.xlsx) |
| 10 | Comparaison du contrôle annuel après arrondi de base, sans versement déterminé | [Guide911](ARRONDI_BASE_ANNUELLE_911.md), [données](JEU_ARRONDI_ANNUEL_PAIE_911.json) | [6 cas](RECETTE_ARRONDI_ANNUEL_PAIE_911.pdf) | [Arrondi annuel](SUIVI_ARRONDI_ANNUEL_PAIE_911.xlsx) |
| 11 | Cumuls des périodes choisies et frais professionnels annuels, sans mensualisation | [Guide913](CUMULS_FRAIS_ANNUELS_913.md), [données exactes](JEU_FRAIS_ANNUELS_PAIE_913.json) | [6 cas](RECETTE_FRAIS_ANNUELS_PAIE_913.pdf) | [Frais annuels et périodes](SUIVI_FRAIS_ANNUELS_PAIE_913.xlsx) |

Les statuts humains restent **Non testé**. Renseigner les résultats réels, anomalies, observations et preuves dans chaque classeur. Conserver les identifiants de dossier, demande, variable et simulation pour pouvoir retrouver les opérations.

Le Personnel, le brut, le calcul social pédagogique et le contrôle annuel du barème IR sont disponibles pour recette. **L’IR intégré à la paie mensuelle, le net, les bulletins et la paie définitive ne sont pas encore livrés.** Le contrôle annuel reçoit un RNI déjà établi ; il ne calcule pas automatiquement l’assiette et ne détermine aucun montant à déclarer. Les paramètres historiques ne sont pas automatiquement requalifiés. Les limites précises figurent dans les guides et rapports datés.

Cette session n’a exécuté aucune des migrations111 à118 sur la base réelle. Vérifier leur état puis préparer leur installation sur copie avec l’administrateur technique. La présence d’un ZIP ou de tests réussis ne signifie pas que ces migrations sont déjà installées.

Le [bilan de la session précédente](BILAN_SESSION_PAIE_20261028.md) conserve l’état895. La [préparation du moteur social3B](PREPARATION_COTISATIONS_3B_895.md) conserve les sources et leurs limites. Le référentiel897, les simulations sociales899 et le contrôle annuel IR901 sont désormais accessibles. La qualification juridique, les cas complexes et l’IR intégré à la paie mensuelle restent des étapes distinctes.
