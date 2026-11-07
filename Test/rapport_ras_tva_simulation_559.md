# Lot 559 — Assistant de préparation RAS TVA

Nouvel assistant dans **Déclaration TVA → Assistant RAS TVA · 2026**.
La qualification est limitée au périmètre décrit dans la
[note de sources](../docs/audit/SOURCES_RAS_TVA_20261018.md).
Le CGI2026 a été lu sur l'hébergement officiel TGR ; le téléchargement Python
a renvoyé403. Aucun binaire local ou SHA n'est annoncé comme obtenu.

## Comportement

- Faits renseignés explicitement : parties, prestation, exclusions,
  attestation et date réelle du paiement. Rien n'est déduit d'un nom, d'un
  compte comptable ou de la date d'échéance commerciale.
- TVA de la quote-part payée saisie distinctement du montant TTC avant retenues.
  Le résultat expose base, part retenue, montant, net après cette seule RAS TVA
  et mois de reversement. Les autres retenues restent distinctes.
- Informations absentes ou contradictoires : à compléter, montants inconnus.
  Hors périmètre/millésime : à examiner séparément, jamais « pas de retenue ».
- Justification explicite d'une exclusion ; aucun seuil ou cumul fournisseur
  calculé depuis une facture isolée. Une attestation non qualifiable ne produit
  pas automatiquement un taux de substitution.
- Réponses retardées écartées après modification du formulaire. Les montants
  du serveur restent des chaînes jusqu'à l'affichage : pas de perte de centimes
  sur les grands nombres. Champs avec libellés HTML associés.
- Simulation autorisée aux trois rôles authentifiés. Aucun règlement, facture,
  paramètre TVA ou journal modifié ; non incluse dans l'impression de déclaration.

## Tests réellement exécutés

44 tests de calcul purs réussis avant intégration,1avertissement,0,39s.
Première intégration :45réussis/3échoués,29avertissements,108,70s.
Les trois échecs révélaient des libellés de listes déroulantes incluant leurs
options : correction par association explicite `label`/`id`, sans assouplir
les sélecteurs ou les résultats attendus.

Qualification corrigée : **49 réussis,29avertissements,47,31s,code0** :

- 44 tests de règles/validation dont paiements partiels, faits manquants,
  domaines exclus, dates d'attestation, arrondis et grands montants ;
- 1 test Node du format exact, y compris valeur inconnue refusée ;
- 1 scénario API avec authentification, deux sociétés, saisies invalides et
  empreintes de toutes les tables métier inchangées ;
- 3 parcours Edge admin1440/comptable390/lecture390, données incomplètes,
  calcul, réponse réelle retardée, montant dépassant la précision de `Number`,
  attestation expirée, cas hors périmètre et exclusion de l'impression.

Capture mobile lecteur inspectée. Build Vite corrigé : réussi en6,58s,
avertissement de taille du bundle conservé. La consolidation avec les recettes
TVA existantes est consignée après achèvement dans le journal actif.

## Limites restantes

**FIS-02 passe d'absent à partiel.** L'assistant ne déclare pas la RAS TVA
opérationnelle sur tout le cycle. Restent l'intégration aux paiements et aux
écritures, le suivi des retenues effectivement opérées/reversées, les autres
situations de l'article117, leurs transitions et les modèles administratifs.
L'applicabilité des faits renseignés et les justificatifs restent à contrôler.

Aucune migration, aucun PostgreSQL réel et aucune donnée utilisateur modifiés.
RH/paie différées. Recette utilisateur et production non validées.

Consolidation finale : **16 réussis, 29 avertissements, 59,98 s, code 0**.
Elle reprend les quatre scénarios API/Edge559 et les recettes TVA préexistantes
(factures/paiements partiels, paramètres, lecteur et impression), plus les règles
TVA pures. Les suites se recouvrent ; ne pas additionner les comptes.
Six fichiers Python compilés ; aucun SQL modifié.
