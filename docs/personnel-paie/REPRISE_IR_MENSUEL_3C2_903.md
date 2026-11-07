# Reprise exacte — 3C2, assiette et IR mensuel

**État du produit :901.** Ne pas refaire les lots889/891/893/897/899/901 déjà livrés. Le contrôle annuel901 est un outil sur RNI déclaré, pas le moteur fiscal mensuel intégré.

## Première action à la prochaine session

Relire AGENTS, le master et le journal, puis `Test/journal_codex.py etat`. Inspecter les processus avant de relancer une commande. Vérifier les ZIPs903 et les519empreintes du candidat901 ; tous les SQL antérieurs doivent rester inchangés. La base réelle et `.env` restent hors des tests. Utiliser les gardes nonce des fixtures existantes.

La dernière campagne327cas figure dans `Test/PREUVE_PAIE_901.json`. Ne pas additionner ses résultats aux230/277 des lots précédents. L’étape suivante doit commencer par une reprise ciblée du brut/social/contrôle annuel sur le produit courant.

## Analyse à faire avant code

1. **Assiette IR distincte.** Inspecter `paie_catalogue_*`, les snapshots des variables et du brut, `paie_social_calcul_*` et `paie_ir_annuel_*`. Les rubriques possèdent déjà un traitementIR ; le brut, la baseCNSS et la baseAMO ne doivent pas être recopiés comme RNI.
2. **Frais professionnels.** Qualifier le cadre applicable, la base incluant/excluant les avantages et les catégories particulières, avec CGI58/59 et textes officiels effectivement lus. Le helper historique `paie_service.py` annualise un salaire fixe : ne pas le réutiliser en supposant qu’une prime ponctuelle est versée douze fois. Les passages de NC733 sont historiques ; leur existence ne prouve pas une revue complète2026.
3. **Cotisations fiscalement déductibles.** Chaque part salariale calculée socialement n’est pas automatiquement une déductionIR. Prévoir des règles sourcées/versionnées par branche ou régime, distinctes de la qualification sociale. Anciennes versions dépourvues de ce fait → À vérifier ; ne pas réécrire leurs snapshots.
4. **Cumuls et mensualisation.** Obtenir les règles officielles de retenue et de régularisation. Conserver les revenus/déductions/IR déjà prélevé et les périodes réellement couvertes ; absence d’historique ≠ zéro. Ne pas confondre mois de paiement, acquisition du revenu et période de calcul. Les entrées/sorties et mois incomplets restent des cas spécifiques.
5. **Famille.** Reprendre l’éligibilité confirmée et sa période/source, jamais seulement l’état civil. La réduction annuelle connue ne suffit pas à inventer les modalités de retenue mensuelle.
6. **Arrondis.** Le résultat901 à quatre décimales est mathématique. Qualifier les arrondis de retenue, liquidation et déclaration avant de produire un montant à prélever. Ne pas transformer le résultat annuel en net bancaire par simple division ou soustraction.

Le [rapport de sources901](SOURCES_IR_ANNUEL_901.md) distingue les accès effectivement obtenus. La publication officielle de NC737 a été repérée dans l’index du MEF, mais le document complet et les règles de retenue mensuelle n’ont pas été obtenus par ces recherches ; aucun schéma ou règle mensuelle n’a été codé sur cette seule piste. Une page de projet de loi2027 n’est pas une loi applicable à2026.

## Solution attendue, encore à concevoir

Créer une sous-étape stable et son baseline avant toute modification. Identifier les champs réellement manquants sans ajouter des obligations arbitraires. Les noms éventuels de services/tables et la migration119 restent **des propositions à revérifier**, aucun fichier119 n’est livré ici.

Le futur snapshot fiscal doit référencer le salarié réel, le brut et le social utilisés, les versions de règles, cumuls et confirmations nécessaires. Comparer les sources courantes au calcul, conserver l’historique, refuser l’incohérence plutôt que modifier une source approuvée. Le contrôle annuel901 peut servir de primitive de barème après qualification du contexte mensuel ; il ne devient pas une paie définitive par changement d’étiquette.

Tester d’abord les oracles indépendants : assiettes IR/CNSS/AMO différentes, frais et cotisations non déductibles, plafonds/cumuls, sources périmées, information inconnue, régularisation positive/négative sans restitution inventée, famille, autres années, concurrence, sociétés et droits. Ensuite API/SQL natif nonce, Edge1440/390 et restauration du nouveau snapshot. Livrer un différentiel vérifié et actualiser matrice/journal avant net et bulletins.

Les cas sociaux complexes et leur qualification restent partiels. Continuer les travaux indépendants lorsque les pièces manquent, en gardant visibles les limites. Paiements, OD, déclarations, archivage annuel de paie et production restent des étapes futures du master.
