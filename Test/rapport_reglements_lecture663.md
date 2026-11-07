# Lecture des règlements : erreur distincte d’une liste vide — lot663

`OngletReglements.charger()` transformait toute erreur de lecture en tableau
vide. Le serveur pouvait refuser l’accès et l’écran afficher pourtant
« Aucun règlement trouvé ». Le total était alors calculé comme celui d’une
liste vide. Une ancienne somme pouvait aussi rester visible pendant le
chargement d’une nouvelle lecture.

Le refus a été reproduit dans Edge : un rôle LOGIN non propriétaire perd
temporairement son SELECT sur `reglements`, exclusivement dans PostgreSQL
nonce. L’API renvoie un vrai500, l’ancien écran annonce une liste vide et
aucune alerte. **Échec de régression attendu :1cas en33,46s.** Les deux essais
précédents concernaient le banc : attente d’un événement response malgré un
refus CORS, puis oubli du paramètre exercice dans le contrôle HTTP. Ils restent
consignés séparément et ne sont pas présentés comme des preuves produit.

## Correction minimale

Une erreur explicite remplace le faux vide. **Réessayer** relance la lecture,
et **Actualiser** permet une relecture volontaire. Le tableau et son total ne
sont pas présentés comme disponibles tant que le chargement n’a pas réussi.
Une vraie réponse200 vide continue d’afficher « Aucun règlement trouvé ».
Les gardes d’exercice, de cycle, de jeton et de génération sont conservées.
Aucune règle de paiement, écriture ou permission serveur ne change.

## Résultats

Les quatre premiers Edge ordinateur/mobile réussissent en41,50s et le build
Vite en8,99s. Le banc a ensuite été renforcé : un vraiGET200 est retenu avant
d’être livré au navigateur ; l’ancien total240 doit rester masqué durant
l’attente, puis les deux règlements réapparaître.

63 tests connexes réussis en 344,82 s avant la retouche visuelle, puis 8 Edge finaux réussis en 92,91 s après celle-ci, zéro échec/erreur/ignoré. Refus SQL réels, reprise sans F5, attente de vrai GET, vrai vide, contextes, historiques invalides, annulations et lettrage. Build final : 6,28 s, code0. Capture390 finale inspectée : consigne lisible, erreur/reprise sans débordement ; ACL et photos comptables préservées. Python du test compilé. Campagnes recouvrantes non additionnées.

Les tests distinguent refus initial, nouveau refus après une lecture réussie,
reprise sans F5 et véritable absence de données. Les rôles SQL sont contrôlés,
les droits sont rétablis en finally et les ACL doivent retrouver exactement
leur état initial. Les photographies comptables restent identiques. Les500
et erreurs réseau attendus proviennent du vrai refus SQL ; aucune réponse
métier n’est fabriquée ou remplacée.

Les campagnes se recouvrent et ne s’additionnent pas. Aucun PostgreSQL réel,
ancienne migration ou donnée comptable réelle touché. Recette utilisateur et
production restent à valider ; RH/paie et point6 humain différés.

La capture390 a aussi révélé une ancienne consigne comprimée dans le bandeau. Un retour à la ligne local et une largeur souple ont été ajoutés, puis les huit Edge et le build rejoués.
