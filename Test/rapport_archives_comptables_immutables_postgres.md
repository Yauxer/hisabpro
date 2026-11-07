# Archives comptables — migration 074 — 7 octobre 2026

Les scripts 009/011 du livre d'inventaire n'installaient aucun trigger
d'immutabilité. Le trigger 071 des préparations de balance couvrait
UPDATE/DELETE, mais pas TRUNCATE. Les droits historiques directs, PUBLIC ou
hérités d'un groupe pouvaient ainsi contourner les seuls droits SELECT/INSERT
attendus de l'application.

Avant correction, quatre tests PostgreSQL réels ont échoué en 23,72 s :
UPDATE/DELETE/TRUNCATE du livre et TRUNCATE de la préparation étaient autorisés.
Ces opérations concernaient exclusivement des archives fictives dans un nouveau
cluster éphémère, supprimé à la sortie ; aucune base réelle n'a été contactée.

La migration additive 074 ajoute les triggers du livre et le trigger TRUNCATE
de préparation ; elle retire UPDATE/DELETE/TRUNCATE à PUBLIC et hisabpro.
Les migrations historiques et les contenus archivés restent intacts. Les droits
hérités d'un groupe ne sont pas retirés par ces REVOKE : les triggers les bloquent.

Après correction : **13 tests réussis, 0 échec/ignoré, 21,32 s** sur PostgreSQL
éphémère. Rejeu deux fois, rôle applicatif absent, propriétaire gardant les
triggers actifs, runtime LOGIN non propriétaire avec groupe historique,
catalogue ACL, SELECT/INSERT et nouvelle version contrôlés. Les instantanés
complets des lignes originales, dates et empreintes sont inchangés.

Tests connexes livre d'inventaire et import de balance : **33 réussis,
0 échec/ignoré, 0,91 s**. Compilation du test PostgreSQL : OK. Une première
commande connexe utilisait un chemin E2E inexistant ; aucun test n'avait alors
été exécuté et cette commande n'est pas comptée comme réussite.

L'application à un déploiement réel n'a pas eu lieu. Un propriétaire pouvant
désactiver un trigger reste un administrateur privilégié ; conserver un rôle
runtime distinct du migrateur. Cette protection technique ne valide ni la
recette annuelle utilisateur ni une conformité réglementaire officielle.
