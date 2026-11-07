# Livraison709 — Déclarations des émetteurs

Formulaire documentaire N/N-1 dans la préparation indépendante depuis balances.
Comptes proposés uniquement parmi les251 de la source conservée de la période.
Déclarations par émetteur avec référence de source ; identifiant facultatif,
valeur brute signée, capital non négatif, quote-part0..100 à12décimales et
produits reçus signés. Deux décimales pour les montants MAD ; NaN/infinis et
précisions excessives refusés. Aucune identité, ratio ou donnée fiscale inférée.
Les valeurs inconnues restent inconnues ; une seule valeur brute manquante
rend la somme/écart de son compte indisponibles. Aucun pourcentage n’est sommé
entre émetteurs différents. Les données et références fictives du guide sont
cohérentes avec les fixtures et les résultats calculés indépendamment en Decimal.

Contrôles par compte figés avec méthode/catalogue/note/auteur/UTC/source dans
une nouvelle version : somme brute déclarée moins solde brut251 conservé. Ils
ne changent pas avec le brouillon, ne comparent pas le seul251 au total24/25,
et ne corrigent aucun écart. Note B4 non applicable et déclaration Néant avec
un solde251 non nul gardent leurs alertes. N-1 absent : saisie indisponible.
Le détail automatique707 et les autres compléments sont conservés séparément.
Empreinte parent, UUID/rejeu avant calcul, concurrence/verrou, rôles/société et
restriction MAD restent protégés. Aucune nouvelle migration ni modification
SQL/bootstrap ou des moteurs comptables partagés.

PDF/Excel/ZIP reprennent les données et contrôles conservés avec logo actuel,
références et source. XLSX garde les pourcentages exacts et les textes comme
textes, y compris les préfixes de formules. Les grands montants conservent leur
précision grâce au format texte si nécessaire. Manifestes vérifiés sur chaque
fichier. Pièces propres à chaque version, aucune copie implicite.

Tests réellement exécutés ici : 28API/calculs 40.79s puis8Edge+restauration 113.42s puis336connexes 801.76s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build4,96s code0 ; 10Python compilés,1114SHA figés. Restauration10483tables/5fichiers et témoins conservés.108SQL/bootstrap et moteurs comptables inchangés. Guide Word/PDF7pages/Excel5feuilles,six cas humains Non testé, Office non ouvert.

Cibles :28calculs/API natifs ; huit Edge (admin1440, comptable390, lecteur390,
brouillon/écart de centime, rejet101 puis correction, N-1 absent, trois GET
retardés et un POST retardé réels) ; restauration froide10483tables/cinq fichiers.
Connexes :336cas couvrant préparations, B1/B4/B11, échéances, notes, financement,
annexes, capital, justificatifs et exports/permissions. Les campagnes se recouvrent.
Les témoins comptables et documentaires ainsi que1114sources app/Test sont restés
inchangés pendant la campagne. Une version non vide d’émetteurs avec contrôles
N4000/N-1 3000 est restaurée ; ACL/séquences/données, pièces et rendus préservés,
source intacte et cibles jetables supprimées. Aucun PostgreSQL réel utilisé.

Guide Word/PDF et Excel cinq feuilles, six cas humains Non testé, résultats
réels/anomalies/preuves laissés vides. CRC/XML Word, identifiants PDF, données,
formules/listes Excel et calculs Decimal vérifiés. Capture mobile390 inspectée.
Générateur documentaire initial refusé pour date sans espaces, corrigée puis
génération réussie. Contrôle documentaire initial : feuille Données omise ; feuille
rétablie et oracles Decimal ajoutés au générateur, contrôle rejoué ; aucun test produit échoué dans ce lot. Office non ouvert.

Développement du complément terminé ; tests automatisés du lot validés ; recette
utilisateur à effectuer ; mise en production nonvalidée. LIA-09D reste partiel.
Le socle annuel347 de701 reste historique, non réexécuté ici. Prochaine étape :
les mouvements ETIC, sur sources explicites et avec contrôles d’ouverture/flux/
clôture ; les variations N/N-1 ne prouvent pas acquisitions/cessions/dotations.
Les sources fiscales restent distinctes du Journal courant. RH/paie et point6
humain restent différés. Aucune certification ni conformité officielle affirmée.
