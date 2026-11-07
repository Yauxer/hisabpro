# Suppression cohérente des pièces d’inventaire — lot613

Deux tests PostgreSQL natifs ont reproduit une suppression204 depuis le Journal
du brouillon d’ajustement ou de sa contrepassation. Les FK SET NULL détachaient
la pièce du dossier ; le suivi d’ouverture pouvait alors perdre sa source.

Correction minimale dans DELETE Journal : lorsqu’un brouillon appartient à un
ajustement de la même société, réponse409 et instruction de supprimer depuis
Clôture. Le module conserve sa suppression cohérente du dossier et de ses deux
brouillons. Les protections existantes des écritures définitives et captures
RAS restent en place. Pas de migration, aucune donnée historique réparée.

Tests finaux réellement exécutés :39réussis en147.838s puis2ciblés
renforcés en38.061s (avec suppression manuelle ordinaire autorisée),
aucun échec/ignoré. Python compilé. Contrôles : refus AD/CP, absence de mutation,
suivi conservé puis suppression métier complète ; anciens tests inventaire et
périodes. Aucun PostgreSQL utilisateur ni donnée réelle utilisés.
Navigateur utilisateur : vérifier le message après tentative de suppression
d’un brouillon d’inventaire, puis suppression autorisée depuis Clôture lorsque
les deux pièces sont encore en brouillon. Ce parcours humain n’est pas validé.

La conception611 reste le point de reprise des reprises partielles ; elle
n’est pas devenue une fonctionnalité par ce correctif. Le cumul de session
conserve les guides et les30cas de recette humaine Non testé.
