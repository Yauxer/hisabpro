# Avancées de session — 11 octobre 2026, 16h05 UTC

## Session du 11 octobre 2026 — reprise 16h05 UTC — lots 378 à 390

- Consolidation378 : **3241 réussites**, zéro échec/erreur/ignoré, 3877.960s, code0 ; 697 empreintes stables. Elle couvre l'état après377, avant379/381. La preuve échouée373 est conservée. [Rapport378](../Test/rapport_consolidation_globale_378.md).
- 379 : règlements d'une facture N-1 visibles en N dans le bon cycle ; projection native isolée par société, statut et diagnostics partagés. [Rapport379](../Test/rapport_reglements_inter_exercices_379.md).
- 380 : variante annuelle ventilations2025, clôture, reports clients/fournisseurs120, compléments2026, validation, lettrage et exports. Avant impôt9écritures/22lignes/D=C2200, AN4180, balance2026 nette4060. [Rapport380](../Test/rapport_annee_ventilation_380.md).
- 381 : annulation collective native en transaction unique, contrepassations et capturesRAS tracées ; refus/rollback et concurrence testés, quatreEdge. Instrument bancaire unique et rapprochement à une ligne restent à traiter. [Rapport381](../Test/rapport_annulation_ventilation_381.md).
- 382 : acquisition60000HT/72000TTC et cinq dotations dégressives24000/14400/8640/6480/6480 ;6écritures définitives,D=C132000,VNC0,aucun doublon. [Rapport382](../Test/rapport_immobilisations_degressif_382.md).
- 383 : mode d'emploiWord/PDFv12,30pages,439blocs,18fiches et17statutsNon testé ; trois variantes chiffrées ajoutées. [Rapport383](../Test/rapport_guide_ventilation_degressif_383.md).
- 384 : preuve primaire supplémentaire des partsLT, mais consolidation sociale applicable et schémaEDI toujours non qualifiés ; aucun taux/schema installé. [Rapport384](../Test/rapport_sources_paie_edi_384.md).
- 385 : consolidation des consommateurs règlement/RAS après379/381, avant388 : **228 réussites**, zéro échec/erreur/ignoré, 691.620s, code0 ; 701 empreintes stables. [Rapport385](../Test/rapport_consolidation_reglements_ras_385.md).
- 388 : preview tardive de l'annulation reproduite et corrigée ; une ancienne réponse après changement d'exercice/cycle/jeton ne peut plus confirmer, poster ou rafraîchir le nouveau contexte. QuatreEdge bureau/mobile et22connexes exécutés. [Rapport388](../Test/rapport_annulation_contexte_388.md).
- 389 : consolidation après388, avant390 : **232 réussites**, zéro échec/erreur/ignoré, 705.560s, code0 ; 702 empreintes stables. Ces suites connexes ne valent pas une nouvelle globale de tout le dépôt. [Rapport389](../Test/rapport_consolidation_reglements_contexte_389.md).

- 390 : réponse GET retardée de2026 remplaçant la liste2025 reproduite puis corrigée ; génération, exercice, cycle et jeton vérifiés avant chaque mise à jour. **42tests racine réussis**, zéro échec/erreur/ignoré, 276.989s, puis28connexes(112.397s) sur la garde finale avant invalidation, compilation0 et buildfinal0. [Rapport390](../Test/rapport_reglements_chargement_390.md).

Les suites se recoupent et ne sont pas additionnées. 70fonctions :15terminé/46partiel/5absent/4bloqué ;73demandes :40terminé/30partiel/2absent/1bloqué. Développement global partiel ; validations automatisées limitées à leurs périmètres ; recette utilisateur à effectuer. **Point6 en attente à la demande de l'utilisateur** : aucune préparation de mise en production engagée. Aucun PostgreSQL réel, donnée comptable réelle, modèle,main ou migration modifié.

Prochaine reprise : nouvelle globale couvrant379/381 et tous modules, puis instrument bancaire unique/rapprochement des paiements ventilés et variantes annuelles restantes. Paie définitive/EDI seulement après qualification des textes/schémas officiels applicables. Attendre le retour utilisateur pour le point6.

## Utiliser les changements

Installer le ZIP cumulatif sur une copie de recette selon la procédure habituelle ; aucun SQL nouveau dans cette session. Redémarrer le backend et recharger le frontend après application des fichiers.

Dans Cycle commercial → Achat/Vente → Règlements, retrouver les paiements de l'année même si leur facture appartient à l'exercice précédent. Pour une ventilation native, le bouton Annuler toute la ventilation relit toutes les lignes avant de demander confirmation ; les lignes annulées et les contrepassations restent visibles. Valider les nouvelles écritures selon le circuit normal.

Les variantes détaillées et les chiffres attendus figurent dans le [mode d'emploi Word](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx) et le [PDF](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf), version12. Aucun résultat partenaire prérempli. Ne pas exécuter ces essais sur des données réelles.

## ZIPs différentiels des étapes techniques

Ces archives séparées sont disponibles dans le dossier de livraison. Le cumulatif utilise leurs versions finales.

- [HisabPro_Patch378_Consolidation_Globale_Apres_Cloture.zip](../HisabPro_Patch378_Consolidation_Globale_Apres_Cloture.zip)
- [HisabPro_Patch379_Reglements_Factures_Exercice_Precedent.zip](../HisabPro_Patch379_Reglements_Factures_Exercice_Precedent.zip)
- [HisabPro_Patch381_Annulation_Collective_Ventilation.zip](../HisabPro_Patch381_Annulation_Collective_Ventilation.zip)
- [HisabPro_Patch380_Recette_Annuelle_Ventilation_2025_2026.zip](../HisabPro_Patch380_Recette_Annuelle_Ventilation_2025_2026.zip)
- [HisabPro_Patch382_Recette_Degressif_Cinq_Ans.zip](../HisabPro_Patch382_Recette_Degressif_Cinq_Ans.zip)
- [HisabPro_Patch383_Mode_Emploi_Ventilation_Degressif_Word_PDF.zip](../HisabPro_Patch383_Mode_Emploi_Ventilation_Degressif_Word_PDF.zip)
- [HisabPro_Patch384_Preuve_Primaire_Paie_Limites_EDI.zip](../HisabPro_Patch384_Preuve_Primaire_Paie_Limites_EDI.zip)
- [HisabPro_Patch385_Consolidation_Reglements_RAS.zip](../HisabPro_Patch385_Consolidation_Reglements_RAS.zip)
- [HisabPro_Patch388_Annulation_Preview_Contexte_Securise.zip](../HisabPro_Patch388_Annulation_Preview_Contexte_Securise.zip)
- [HisabPro_Patch389_Consolidation_Finale_Reglements_Contexte.zip](../HisabPro_Patch389_Consolidation_Finale_Reglements_Contexte.zip)
- [HisabPro_Patch390_Reglements_Chargement_Contexte.zip](../HisabPro_Patch390_Reglements_Chargement_Contexte.zip)

Couverture et journal : `HisabPro_Patch386_Couverture_Session_1605.zip`. Cumulatif de session : `HisabPro_Session_20261011_1605_Cumulatif_Verifie.zip`.
