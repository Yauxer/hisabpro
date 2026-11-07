# Stabilisation commerciale bornée673

Deux régressions ont été reproduites sur le dépôt : les factures achat/vente
étaient mélangées dans le cycle commercial malgré typeForce ; un refus natif
de lecture des devis devenait Aucun devis. Le même catch existait dans les
commandes, livraisons, factures et réceptions client. La lecture de factures
était limitée à100lignes et la dépendance de réception client masquait sa panne.

Une lecture partagée du composant distingue panne, chargement et vrai vide,
avec reprise explicite, garde de génération/exercice/cycle/jeton et nettoyage
au démontage. Les factures réutilisent listerTout existant. Le filtre de cycle
est appliqué aux factures ; les BL de vente restent dans la partie Vente.
Le repli du header conserve les commandes visibles sur390pixels.

## Résultats

- Reprise réelle du20octobre :28tests réussis en189,81s, zéro échec/erreur/ignoré ;30avertissements Python.
- Guide et annexe RAS après mise à jour des audits/index :9contrôles documentaires réussis en1,51s.
- Les24cas ciblés et les4cycles d’achat complets/partiels sont exécutés. Les campagnes précédentes se recouvrent et ne sont pas additionnées.
- Build final : code0,6,96s, sur les mêmes sources applicatives. Python du test compilé à la livraison.
- Captures finales erreur/reprise390 inspectées ; les10reprises vérifient la géométrie des commandes. Les5contextes disposent de traces navigateur réelles.
-106fichiers protégés inchangés : instructions, démarrage, modèles, schémas et SQL. Archives671 et cumul671 revérifiés par SHA, CRC et manifeste.

La première reproduction donne3échecs réels en56,10s,20cas volontairement non
sélectionnés. Après correction,18réussites et5échecs en151,37s : les5échecs
du nouveau banc cherchaient un numéro définitif sur une facture brouillon.
Le repère du test a été corrigé vers son vrai tiers unique ; aucune règle de
numérotation modifiée. La suite suivante passe24cas en144,93s.

Une commande intermédiaire mal nommée sort4 à la collecte,0test exécuté en
0,07s. Elle reste un échec de commande, jamais une preuve de réussite.
Le contrôle visuel a identifié le bouton Nouveau devis coupé par le nouveau
header sur390pixels ; le flex-wrap minimal et les assertions de géométrie
des10reprises sont inclus dans la dernière campagne ci-dessus.

La campagne de la veille après repli mobile comptait27réussites et1échec en
255,57s. Cet échec intervient avant le scénario, au remplissage du login
non affiché dans les10secondes. Il n’établit pas un défaut du changement
d’exercice. La reprise ajoute observateur et traces aux5cas de contexte,
sans assouplir délai ou assertions. La cause du timeout antérieur reste
indéterminée ; sa réussite ultérieure ne l’efface pas. Aucun correctif
applicatif supplémentaire n’est déduit de cette reprise.

## Portée réelle

Les tests utilisent Edge et un PostgreSQL nonce sous LOGIN applicatif non
propriétaire, sans .env réel. Les erreurs sont provoquées par REVOKESELECT
sur la seule table du bac, puis les ACL exactes sont restaurées. Les données
métier sont identiques avant/après consultation. Les réponses retenues pour
le changement d’exercice sont de vrais GET200 ; aucune réponse JSON inventée.
102factures couvrent les deux pages et les deux cycles. Les captures finales
erreur/reprise des devis390 sont inspectées, avec boutons lisibles.

Aucun backend, SQL, modèle, schéma, calcul, écriture ou donnée réelle modifié.
Les autres écrans, les opérations tardives de mutation et la recette humaine
restent distincts. Les statuts globaux de couverture ne sont pas promus.
Le [plan de sortie borné](../docs/audit/FIN_DEVELOPPEMENT_HORS_RH_20261020.md)
prévoit ensuite une campagne commune figée et l’installation vierge de la
candidate ; aucune nouvelle fonctionnalité indépendante n’est ajoutée.
