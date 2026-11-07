# Comptabilité et facturation — état après le lot 955

Les compensations signées sont prises en compte en TVA, le parcours annuel sur encaissements est vérifié et le contrôle CM est complété sur copies indépendantes.

| État | Conclusion |
|---|---|
| Développement | Correctif produit 953 et migration additive 126 ; aucun changement produit supplémentaire en 955 |
| Tests automatisés | 46 cas distincts réussis dans deux campagnes sur le même candidat de 550 fichiers ; build Vite 953 réussi |
| Recette utilisateur | À effectuer ; résultats humains inchangés |
| Prêt pour production | Non déclaré ; migration sur copie, configuration cible et réserves métier à lever |

Suivi : 250 réussis, 10 partiels, 12 bloqués sur 272 fiches. Les 46 tests ciblés ne représentent pas un rejeu de toute l'historique de tests du produit.

La migration 126 est à vérifier sur copie restaurable ; votre PostgreSQL n'a pas été utilisé. Les sources ETIC incomplètes, historiques sans justificatifs, réserves de cession et configuration de production restent visibles. Personnel/Paie est distinct ; le point 6 soumis au retour humain reste en attente. Ni recette utilisateur, ni dépôt DGI, ni certification ne sont déclarés validés.

Prochaine étape : compléter la preuve de restauration du dossier annuel fictif, puis traiter les cas partiels indépendants des sources humaines manquantes.

[Résultats 955](RESULTATS_MVP_955.md) · [Bilan 953–955](BILAN_SESSION_20261029_953_955.md) · [Guide TVA](TVA_ENCAISSEMENTS_953.md) · [Guide CM](CM_COPIES_955.md) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_955.xlsx).
