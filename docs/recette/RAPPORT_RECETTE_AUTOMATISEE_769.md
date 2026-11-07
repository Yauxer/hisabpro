# Rapport de recette automatisée — HisabPro —769

Campagne exécutée le 24 octobre 2026 : 698 tentatives, 696 réussies. Deux échecs initiaux sont conservés : un test documentaire corrigé et un écran vide non reproduit lors des passages de diagnostic. 693 identités de test distinctes réussies après reprise ; aucun test ignoré. L’incident d’écran vide reste ouvert.

Ces résultats concernent des tests exécutés ici sur des données fictives isolées. Ils ne constituent pas une validation de production ni une recette humaine complète.

## Campagnes

| Campagne | Tentatives | Réussies | Échecs | Ignorés | Secondes |
|---|---:|---:|---:|---:|---:|
| metier | 309 | 308 | 1 | 0 | 1375.12 |
| reprise_metier | 5 | 5 | 0 | 0 | 33.31 |
| societe | 1 | 1 | 0 | 0 | 47.25 |
| commerce | 11 | 11 | 0 | 0 | 203.78 |
| actifs | 11 | 11 | 0 | 0 | 224.45 |
| administration_journal | 9 | 8 | 1 | 0 | 203.81 |
| reprise_journal | 2 | 2 | 0 | 0 | 48.44 |
| stabilite_journal | 2 | 2 | 0 | 0 | 46.77 |
| fiscal | 287 | 287 | 0 | 0 | 954.13 |
| annuel | 2 | 2 | 0 | 0 | 69.03 |
| installation | 2 | 2 | 0 | 0 | 54.13 |
| ux | 14 | 14 | 0 | 0 | 142.8 |
| cahiers | 42 | 42 | 0 | 0 | 51.68 |
| journal_cahier | 1 | 1 | 0 | 0 | 53.63 |

## Correction minimale

Le test Test/test_guide_actualisation671.py attendait encore 47 lignes partielles et 3 absentes. La matrice actuelle en contient 49 partielles et 1 absente. L’assertion a été actualisée avec contrôle des preuves759/761 ; les statuts métier et les fonctions absentes/bloquées sont conservés. Aucun code applicatif n’a été modifié. Un second échec, un écran vide après rechargement du lettrage, n’a pas été reproduit lors des reprises : sa cause reste ouverte. Le test conserve désormais les erreurs navigateur et les requêtes échouées pour faciliter un prochain diagnostic.

## Cas du cahier exécutés directement

- HP-ADM-001 : Réussi — Création société et administrateur via interface,connexion immédiate.
- HP-ADM-002 : Réussi — Identité et paramètres exacts saisis,sauvegardés,rechargés et comparés àAPI.
- HP-ADM-003 : Partiel — Exercices2025/2026 présents avec12mois exacts,sélection2025 ; branche création conditionnelle nonrequise.

Rejeu comptable exact : 50 écritures, 118 lignes validées via API. Bilan : 337010,00 MAD ; résultat net : 106409,75 MAD ; CAF : 112709,75 MAD. Matériel informatique : 24000 brut, 4800 amortissement, 19200 net ; sous-poste235 visible. Les soldes non nuls recoupent intégralement balance_attendue_2025.csv. Les montants d’impôt de ces écritures proviennent de l’oracle : leur saisie ne prouve pas leur calcul par le module fiscal.

## Limites et suite

- Les nombres comptent des fonctions de tests paramétrées. Ils ne représentent ni 272 fiches manuelles ni autant de fonctionnalités distinctes.
- Les campagnes se recoupent. Le classeur conserve chaque tentative ; le total par identité source déduplique les reprises et les fonctions communes identiques.
- Le cycle commercial complet du cahier n’a pas été rejoué via tous ses formulaires dans une société unique. Les 50 écritures attendues ont été saisies et validées par API dans une société dédiée, puis comparées à la balance et aux états indépendants. Ce rejeu ne crée pas les factures, règlements commerciaux, stock physique ou déclarations fiscales correspondantes. Les autres scénarios métier utilisent leurs propres jeux fictifs.
- HP-ADM-001 et HP-ADM-002 ont été exécutés avec les valeurs du cahier ; HP-ADM-003 reste partiel : calendrier et sélection vérifiés, branche de création conditionnelle non rejouée dans ce cas.
- La campagne initiale métier reste en échec dans son XML : 308 réussites, 1 échec documentaire, 3 cas non exécutés. Le test de matrice obsolète a été corrigé, puis 5 tests réussis ont couvert les 4 cas restants et un rejeu.
- Un écran vide après rechargement du lettrage est survenu au premier parcours achat. Les deux sens ont ensuite réussi avec diagnostics, puis ont été rejoués une seconde fois : quatre passages réussis. Cause initiale non établie : incident ouvert, pas un correctif applicatif validé.
- Build Vite exécuté : code0 en9,57 secondes, avec avertissement de taille du bundle (>500kB).
- Aucun résultat humain prérempli ou modifié dans les classeurs existants. Les 272 fiches de pilotage conservent leurs statuts manuels.
- PostgreSQL natif et navigateur Edge ont été utilisés sur des installations temporaires isolées. La base et l’installation réelles de l’utilisateur n’ont pas été testées ou modifiées.
- Les préparations tiers et taxe professionnelle restent documentaires ; aucun dépôt officiel, schéma EDI ou conformité réglementaire n’est validé.
- RH/paie et point6 différés. Les données historiques incomplètes FEC/ETIC ne sont pas réparées. L’appréciation ergonomique et la recette utilisateur restent à effectuer.
- Aucun changement du code applicatif ni des migrations pendant cette étape. Les seuls changements sont des tests, des preuves et la documentation.

Prochaine étape : compléter les formulaires commerciaux du scénario principal annuel et raccorder leurs documents aux attentes chiffrées, puis effectuer la recette humaine ciblée sur les décisions métier et les écrans. Les dépendances officielles DGI restent séparées.

Preuves : Test/preuves_recette769/*.xml, PREUVE_RECETTE_AUTOMATISEE769.json ; détail exploitable dans RAPPORT_RECETTE_AUTOMATISEE_769.xlsx.
