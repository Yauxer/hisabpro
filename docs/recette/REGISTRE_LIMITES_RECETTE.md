# Registre des anomalies et limites de recette

Toutes les entrées ci-dessous sont des limites initiales, aucune donnée historique réelle n'est réparée artificiellement.

## HP-CLO-008 — Variante indépendante de facture à établir

La préparation TVA actuelle est issue des flux de facturation/paiement ; l'ajustement FAE ne démontre pas le rapprochement des taxes. L'absence de facture en N ne suffit pas à exclure la TVA au débit. Variante exclue de tous les totaux principaux.

Action : Ne pas ajouter cette FAE au scénario principal. Vérifier le contrat, le régime TVA et l'article 95 avec le responsable fiscal. L'assistant Clôture → FAE prépare un cut-off mais ne prouve pas la taxe. Après qualification seulement, contrôler le schéma comptable, la préparation TVA et la contrepassation 2026 dans cette copie.

## HP-LIA-004 — 09B — référentiel exhaustif DGI

Catalogue officiel courant, version, domaine et conditions applicables non exhaustivement intégrés.

Action : Consulter la matrice de couverture ; enregistrer le blocage. Ne pas inventer d'écran, d'export ou d'obligation pour terminer ce cas.

## HP-LIA-005 — 09C — XML/EDI SIMPL-IS

Schéma officiel applicable, version, XSD et recette de dépôt nonvalidés ; bouton désactivé.

Action : Consulter la matrice de couverture ; enregistrer le blocage. Ne pas inventer d'écran, d'export ou d'obligation pour terminer ce cas.

## HP-LIA-006 — 09E — état des ventes DGI

Pas de parcours dédié complet vérifié dans ce dépôt ; les statistiques commerciales ne sont pas un état DGI officiel.

Action : Consulter la matrice de couverture ; enregistrer le blocage. Ne pas inventer d'écran, d'export ou d'obligation pour terminer ce cas.

## HP-LIA-007 — 09F — rémunérations allouées aux tiers

Annexe déclarative complète et modèle officiel non implémentés ; crédits IS ne suffisent pas.

Action : Consulter la matrice de couverture ; enregistrer le blocage. Ne pas inventer d'écran, d'export ou d'obligation pour terminer ce cas.

## HP-LIA-008 — 09G — taxe professionnelle et annexes

Valeur locative, qualification et schéma annexe non déterminables avec certitude depuis les pièces principales.

Action : Consulter la matrice de couverture ; enregistrer le blocage. Ne pas inventer d'écran, d'export ou d'obligation pour terminer ce cas.

## HP-LIA-009 — 09H — prêt à déposer complet

Archive interne disponible mais annexes officielles et EDI non terminés ; impossible de valider un dépôt complet.

Action : Consulter la matrice de couverture ; enregistrer le blocage. Ne pas inventer d'écran, d'export ou d'obligation pour terminer ce cas.

## HP-LIA-012 — 09D — dossier fiscal complet en mode Liasse seule

Mode Liasse seule complet non terminé ; préparation de balances disponible.

Action : Documenter les limites : fiscalité, ETIC, financement et annexes ne se reconstituent pas depuis une simple balance. Reprendre quand un dossier autonome complet applicable est implémenté.

## HP-FAC-013 — Archivage individuel des factures

Archive annuelle liasse/livre disponible ; workflow dédié d'archivage individuel des factures non établi.

Action : Contrôler conservation du PDF et historique ; documenter la limite d'archivage individuel si aucun parcours dédié n'est proposé.

## HP-FIS-034 — Variante honoraires public et RAS TVA

Moteur actuel ne réconcilie pas toutes les retenues TVA article 117. Montants nets de contrôle seulement sous qualification légale explicite.

Action : Ne pas exécuter une déclaration automatique finale avec le régime incomplet. Vérifier les articles applicables, l'attestation et le type de prestation avec responsable réglementaire ; enregistrer la limitation du moteur TVA.

## HP-FAC-012 — Limite d'envoi externe des relances

La création, l'historique, la modification et l'annulation sont disponibles dans Facturation → Situation financière pour les rôles autorisés ; la recette utilisateur reste Non testé. L'envoi externe automatique n'est pas implémenté : enregistrer une relance journalise une action effectuée hors application, sans preuve automatique de transmission. Ne pas assimiler cette limite à l'absence des parcours de suivi existants.

## Validation transverse

Les autres cas restent Non testé. La validation PostgreSQL réelle, les parcours navigateur de bout en bout, la revue réglementaire et la sauvegarde/restauration complète doivent être exécutés dans un environnement isolé puis documentés. Ne pas supprimer les anomalies de sources FEC/ETIC lorsque les justificatifs manquent.
