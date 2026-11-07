# Sources et limites du contexte fiscal735

Contrôle du 22 octobre2026. Le code et les tests du dépôt ont été relus avant
intervention : moteurs IS, CM, CSS, crédits, acomptes et passage B12 existants.
Les règles historiques ne sont pas automatiquement requalifiées comme vérifiées
juridiquement par leur présence dans le dépôt.

La consultation directe du [CGI2026 publié par le MEF](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf)
a échoué par timeout. L’adresse sans www est inaccessible par l’outil ; l’accès
HTTP redirige vers le même HTTPS en échec. Le lien DGI
`https://www.tax.gov.ma/wps/wcm/connect/08712531-1e81-4e28-a38b-2bd9edf8e09e/CGI+2026+FR.pdf?MOD=AJPERES`
renvoie Method Not Allowed dans l’outil. La consultation directe de la
[publication MEF sur la LF2026](https://www.finances.gov.ma/Maliya%20tawassol/SLF2026-Fr.pdf)
a également échoué par timeout. Cela ne démontre ni absence des documents ni
panne générale des sites.

Des passages indexés officiels de la LF2023 et de la note circulaire733 ont
été trouvés. Ils ne suffisent pas à qualifier à eux seuls l’ensemble des règles
applicables au contexte2026. Aucun miroir, extrait secondaire, projet de texte
ou résultat ancien n’est utilisé pour inventer une nouvelle obligation.

## Ce qui est effectivement ajouté

Quatre rubriques documentaires internes, avec valeurs explicitement déclarées,
références, auteur, date UTC, parent et version. La saisie vérifie seulement
les formats, bornes techniques, doublons et cohérence arithmétique des montants.
L’agrégation des lignes conserve les inconnus. Crédit total moins part déjà
imputée et comparaison des deux déclarations d’imputation sont des différences
arithmétiques ; aucune éligibilité ou disponibilité juridique n’est déduite.

CM et CSS sont saisies explicitement, sans base/taux/exonération calculés.
Aucun impôt dû, calendrier, ordre d’imputation, liquidation ou solde final n’est
ajouté. Les moteurs fiscaux historiques restent inchangés. L’IS B12 est copié
depuis le contrôle conservé pour mémoire, jamais recalculé par ce complément.
Un changement de B12 est signalé sans modifier le contrôle fiscal historique.

## Validation restant nécessaire

Avant toute liquidation automatique externe : obtenir et lire les articles
applicables complets, leurs dispositions transitoires, les conditions propres
au contribuable et les justificatifs des imputations. Vérifier distinctement
CM, CSS, crédits/retenues, crédits antérieurs, acomptes, excédents et restitution.
La CSS ne doit pas être ajoutée silencieusement à une liquidation IS.
XML/EDI attend toujours le schéma officiel applicable.

Cette réserve ne bloque pas la saisie documentaire ni les travaux indépendants
d’ergonomie et de fiabilité. Aucun PostgreSQL réel n’a été utilisé ; RH/paie
et point6 humain restent différés.

Contrôle réseau complémentaire par GET HTTP local, sans authentification :
MEF ConnectTimeout après10secondes ; DGI HTTP405 text/html, pas un PDF.
Aucun document officiel intégral récupéré. Les tentatives sont consignées
séparément des tests applicatifs et ne sont pas présentées comme réussies.
