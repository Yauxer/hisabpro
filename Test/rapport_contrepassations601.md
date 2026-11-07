# Suivi des contrepassations d’ouverture — lot601

Clôture affiche les contrepassations déjà liées aux ajustements d’inventaire
dans leur exercice de destination, même si l’exercice source est clôturé.
Source, date réelle, type, débit/crédit exacts, statut, source en brouillon,
compteurs et pagination par20. Consultation seule pour tous les rôles ;
validation ordinaire dans le Journal. Retour et actualisation rechargent le statut.

GET `/api/cloture/contrepassations?exercice=2026&page=1` : transaction lecture
cohérente RO/RR, une connexion, périmètre société sur ajustement/source/CP,
tri date/id décroissants, aucune création d’exercice ni écriture. Pas de
migration, modèle ou SQL historique modifié. Les écritures manuelles non liées
ne sont pas déduites de leur libellé. Aucun risque ou montant de reprise présumé.

## Tests réellement exécutés

- API ciblée :3 réussis38,558s, puis reprise dans la consolidation finale.
- Edge ciblé final :4 réussis (admin1440, comptable/lecture390, pagination).
- Consolidation native finale :57 réussis222,241s, aucun échec/ignoré.
  Inclut ancienne recette inventaire, exports, calcul, clôture CCA/PCA599,
  nouveaux contrôles de permissions, comptes étrangers, dates décalées,
  pagination, lecteur403 et consultation sans mutation.
- Complément pur :55 réussis2,306s (prorata, entrées inventaire, précision RAS,
  affichage décimal). Les112 contrôles de cette consolidation sont donc
  répartis sur deux commandes, pas un unique run de112.
- Restauration native :1 réussie80,754s,75tables, source conservée et cibles
  nettoyées, schéma/données/ACL/séquences identiques. JSON de suivi identique,
  ainsi que calcul/PDF/logo et liens d’ajustement du banc précédent.
- Build Vite : réussi10,78s ; avertissement de taille des bundles conservé.
- Python compilé. Guide PDF1page bornes vérifiées et inspecté ; rendu mobile
  réel inspecté, absence de débordement mesurée.

Premier Edge :1succès/3échecs du montage, corrigés avant relance : accepter
la confirmation du Journal, attendre un bouton lecteur désactivé déjà présent.
Ces échecs ne sont pas présentés comme des réussites.

## Limites et suite

Aucun PostgreSQL utilisateur interrogé/modifié. Recette humaine et production
non validées. CPT-09 reste partiel : suivi/reprises spécialisés de provisions
à compléter. Une liste vide ne certifie pas l’absence de régularisations.
Prochain correctif identifié : les formulaires de dépréciation stock/client
autorisent les mêmes comptes de provision ; empêcher les croisements
incohérents en conservant les anciennes écritures et les subdivisions utiles.
