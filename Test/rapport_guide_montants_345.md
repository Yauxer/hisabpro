# Guide Word/PDF et procédure — version5, lot345

Le mode d’emploi conserve18fiches et17statuts utilisateur **Non testé**.
La fiche04 précise le refus des sources monétaires non finies avant
validation définitive ou conversion de proforma : aucun nouveau numéro
définitif ou mouvement, brouillon/proforma et lignes conservés. Le dépannage
distingue coût de réception, prix de conversion BL/BR et montant invalide.
Les contrôles négatifs historiques nécessitent une copie isolée préparée
par le technicien ; aucun SQL d’injection n’est proposé à un utilisateur
sur une base réelle.

La procédure exige désormais le niveau342, ou le cumulatif1939, avant le
nouveau cumulatif2129 contenant uniquement les livraisons depuis343. Une
installation au niveau312 doit d’abord passer par le cumulatif1939. Les
fontes locales restent un prérequis de cette installation, sans être
relivrées comme des fichiers modifiés dans ce nouveau lot. Aucun ajout SQL
343/344 ; configuration, pièces et migrations existantes conservées.

Vérifications réellement exécutées par le principal :

- Génération par `docs/guide/generer_guide.py` inchangé :387blocs,Word/PDF.
- `.codex-tests/verifier_guide_323.py` :XML/rels/CRC du Word,18chapitres,
 17statuts vierges,23pages PDF avec texte extractible,11références locales
 et oracles indépendants cohérents ; code0.
- `.codex-tests/verifier_guide_345.py` :version5, preuves343/344 séparées
 de346, contrôles de refus, prérequis342,11liens de procédure existants,
 deux ZIPs343/344 CRC valides sans SQL/environnement/secret ; code0.
- Pages7 et23 rendues et inspectées :fiche04 complète et références/statuts
 de dernière page lisibles. La fiche18 se poursuit sur deux pages comme
 précédemment ; aucun résultat utilisateur prérempli.

Le guide consigne69réussites343 et91réussites344 sur leurs propres versions,
sans addition des suites. La consolidation346 est suivie séparément dans
le journal ; la génération documentaire n’est pas une nouvelle exécution
des tests métier. Les dépréciations de l’API fitz restent visibles dans
les commandes de vérification. Ouverture MicrosoftOffice, installation
et recette partenaire à effectuer. Aucun PostgreSQL réel utilisé.
