# Garde de suppression SQL des factures définitives — 078

L'API refuse déjà la suppression d'une facture validée. La migration029 protège le parent en INSERT/UPDATE et ses lignes, mais laisse DELETE du parent possible lorsqu'aucun règlement ne le référence. La suppression du parent peut alors contourner le contrôle des lignes.

Migration additive078 : trigger BEFORE DELETE qui refuse une facture validée non proforma avec SQLSTATE23514. Aucun changement de données ni réécriture029. Brouillons et proformas restent supprimables selon les contrôles existants.

Tests PostgreSQL éphémère avec JWT réel et rôle LOGIN non propriétaire :

- Avant correction : DELETE définitif non réglé accepté sous propriétaire et runtime, **2échecs attendus en12,56s**. Chaque tentative est rollbackée : aucun test de reproduction ne laisse de suppression commise.
- Après correction finale : **36tests réussis en26,10s**, comprenant7tests078,7testsACL079 et22connexes fact4/factH. Aucun échec ni ignoré.
- Comparaison exacte des factures, lignes, règlements et écritures avant/après application deux fois puis rejeu sur données existantes ; refus DELETE23514 propriétaire/runtime etAPI409 ; suppression SQL de brouillons/proformas conservée.
- Compilation des tests078/079 : code0.

Exécutions intermédiaires : deux erreurs de setup12,26s sur requête SQL vide du banc précorrection ; puis3échecs/4réussis13,18s (proforma volontairement non validable etpermission de détachement manquante). La fixture proforma respecte maintenant le refus400 existant. Les permissions manquantes de suppression des brouillons sont traitées séparément par079. Une tentative de connexes au nom de fichier inexistant n'a exécuté aucun test.

La garde ne confère pas de nouveaux droits. Elle ne normalise pas les privilèges administratifs existants ; un propriétaire peut administrer/désactiver des triggers. Aucun PostgreSQL réel et aucune migration appliquée au dossier utilisateur.
