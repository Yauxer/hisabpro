# Sources et portée C3 — lot723

Le calcul comptable est celui de `etic_service._calcul_c3_depuis_soldes`, déjà
présent et contrôlé par `Test/test_patch103_etic_c3.py`. L’option
`decimal_exact=True` modifie uniquement la représentation de sortie en chaînes
décimales ; le contrat flottant par défaut et les formules existantes sont
conservés. Les deux tests historiques sont réellement réexécutés dans le lot.

Le détail indépendant normalise les seules sources N/N-1 conservées en Decimal.
Les gardes de clôture119 existantes à l’import sont partagées entre B11/B13/C3
dans `balance_source_controle_service.py`. B11 corrige ainsi la création d’un
faux0 depuis un ancien CPC sans drapeau d’indisponibilité. Les snapshots déjà
conservés ne sont pas modifiés ou recalculés : créer une nouvelle version.

Les références sont celles du bilan/CPC figés, sans recalcul de ces états.
La situation nette est rapprochée des capitaux propres et assimilés du bilan
moins ses non-valeurs nettes. Après119, son montant reste calculable sans
ajouter un second résultat ; les indicateurs d’activité deviennent inconnus.
Une absence de source n’est jamais remplacée par le Journal courant.

Consultations du21octobre2026 :

- [Catalogue MEF/CNC](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx) : référence CGNC tomesI/II indexée, ouverture directe en timeout.
- [PDF ministériel CGNC référencé dans le dépôt](https://www.finances.gov.ma/Publication/depp/2010/7004_recettes_priv_annee25_11_210.pdf) : ouverture directe en timeout.
- [CGNC hébergé par l’OEC Casablanca](https://oec-casablanca.ma/app/webroot/img/uploads/Code_general_de_la_normalisation_comptable.pdf) : ouverture502 ; pas de texte intégral téléchargé ou d’empreinte binaire.
- [Plan sectoriel immobilier du MEF](https://www.finances.gov.ma/Publication/depp/2022/Plan%20comptable%20du%20secteur%20Immobilier.pdf) : extrait C3 indexé, périodesN/N-1/N-2 et catégories comptables/extra-comptables distinguées ; ce texte sectoriel n’est pas transposé en norme générale.

Aucune nouvelle règle fiscale, aucun taux ou calcul de paie introduit.
N-2, effectif moyen, distributions et données par titre restent indisponibles
sans source explicite ; le nombre de salariés actifs du module RH ne sert
pas à inventer un effectif moyen historique. Les rémunérations6171 sont un
solde comptabilisé, pas une certification des salaires bruts ou bulletins.
Le C3 réglementaire complet reste distinct de cette projection comptable.
La consultation partielle des sources ne prouve aucune conformité officielle.
