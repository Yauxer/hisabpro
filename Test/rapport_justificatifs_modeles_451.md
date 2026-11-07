# Pièces justificatives et modèles sous LOGIN SQL limité — lot451

Recette du 15octobre2026, uniquement sur des clusters PostgreSQL nonce et des
sociétés/documents fictifs. Aucun PostgreSQL utilisateur consulté ou modifié.

Le serveur testé est le vrai `main:app`, avec l'installation explicite091,
`HISABPRO_CREATE_TABLES=false` et le LOGIN `hisabpro` non propriétaire. Les modèles,
références documentaires et pièces jointes existaient déjà : ils ne sont pas
réimplémentés et aucun nouveau schéma comptable ou taux fiscal n'est introduit.

## Anomalies reproduites et correction minimale

- Une suppression de pièce d'écriture brouillon retirait le fichier avant le
  DELETE/commit SQL. Le retrait temporaire du droit DELETE dans le seul cluster
  nonce provoque réellement42501 : HTTP500, trace conservée, téléchargement404.
  Le fichier est maintenant retiré après le commit ; rollback explicite au refus.
- Une validation attend déjà un verrou parent réel : la suppression concurrente
  contournait ce verrou et répondait204. La suppression verrouille désormais la
  seule table parent avec `FOR UPDATE OF`, puis relit le statut. Si la validation
  passe avant elle, elle répond409 et conserve le fichier et sa trace.
- Le composant retirait sa ligne sans vérifier le statut HTTP. Il conserve
  maintenant la ligne et affiche « Suppression impossible » au refus HTTP ou à
  l'échec réseau. Un500 non géré peut être présenté comme un échec CORS par le
  navigateur ; le cas API distinct contrôle bien le500 et la conservation réelle.

Les protections des écritures définitives, le tenant et les permissions de
lecture/écriture sont conservés. Aucune migration nécessaire pour ce lot.

## Parcours réellement exécutés

Sept cas ciblés : catalogue de modèles et détection3461, refus SQL de modification
du catalogue ; deux PDF homonymes téléchargés et vérifiés par SHA256 ; deux
références prioritaires successives, recherche par pièce et export FEC18champs ;
comparaison brute des écritures/lignes avant-après ; append-only SQL ; suppression
brouillon autorisée ; refus autre société404 et lecteur403 ; défaillance SQL et
course de validation ; Edge créant une souscription fictive de100 par le modèle
existant3461D/1111C, validation, référence/PDF, téléchargement et rechargement ;
Edge maintenant une pièce visible sur un refus de suppression.

Les500 des injections de faute sont attendus ; ils ne sont pas présentés comme
une absence générale d'erreurs serveur. Les privilèges temporairement retirés sont
restaurés en `finally`. Les processus et répertoires créés sont nettoyés par le
banc isolé ; aucun processus utilisateur arrêté.

## Résultats et preuves

- Reprise existante :13réussis en0.35s (`reprise451_unit.xml`).
- Avant corrections :3réussis/1échec45.50s (oracle du banc :ligne vide volontaire),
  puis3réussis/1échec36.23s (strip du banc supprimant les champs FEC vides).
- Perte physique reproduite :1échec25.27s (`justificatifs451_perte_avant.xml`).
- Course et premier banc UI :2échecs31.84s, dont un sélecteur ambigu corrigé.
  Attente UI d'un événement response non exposé par CORS :1échec58.35s, résultat
  non probant pour qualifier à lui seul la correction UI.
- Après première correction :6réussis/1échec74.78s, uniquement l'attente UI.
- Final ciblé :**7réussis46.28s**,29avertissements de dépendances,
  zéroéchec/erreur/ignoré (`justificatifs451_final.xml` et `.exit=0`).
- Compilation Python des deux fichiers modifiés :code0.
- Build Vite :code0,9.79s ;avertissement de taille de bundle conservé.
- Suite connexe : **44 réussis en154.37s**,29avertissements, zéroéchec/erreur/ignoré
  (`justificatifs451_connexes.xml` et `.exit=0`). Elle inclut les sept nouveaux cas,
  les contrôles FEC/modèles/sécurité, les deux recettes de réception documentaire,
  les erreurs de saisie et la restauration conjointe historique des documents.

Les logs/XML/exit sont dans `.codex-tests/` et sont exclus du ZIP. Les fichiers de
test livrés permettent de rejouer la recette. Les suites se recouvrent : ne pas
additionner leurs nombres de cas.

## Limites et suite

La validation de l'installation de l'utilisateur et sa recette restent à faire.
La suppression SQL et le disque ne constituent pas une transaction distribuée :
une panne disque après commit n'a pas été injectée dans ce lot. Le fichier restant
visible peut alors nécessiter une nouvelle suppression autorisée ; ce lot démontre
la conservation au refus SQL et la sérialisation avec validation, sans revendiquer
une atomicité universelle disque/base.

Suite : restauration conjointe de ces pièces, traces append-only et droits natifs
sur une seconde cible vide, puis couverture et cumulatif. Point6 reste en attente
du retour utilisateur. Production et conformité réglementaire non prévalidées.
