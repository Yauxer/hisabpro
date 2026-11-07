# Complément de preuves primaires paie / EDI — 11 octobre 2026

Lot 384, lecture seule. Les rapports [220](rapport_sources_paie_2026.md) et [282](rapport_acces_sources_cnss_20261009.md) sont conservés. Aucun taux, schéma, paramètre, migration ou donnée installé ; aucune nouvelle règle codée.

## Preuve supplémentaire obtenue

Le [décret 2-01-2723 publié par ACAPS](https://acaps.ma/sites/default/files/publication_documents/decret_ndeg_2-01-2723.pdf) a été ouvert : PDF d'une page, texte extrait. Son article 3 indique les parts LT **7,93 % patronal / 3,96 % salarial** ; article 4, plafond mensuel **6 000 MAD**. La version présente un CT ancien total de **1 %** ; elle ne confirme donc pas à elle seule la consolidation ultérieure des branches et leur application aux périodes à traiter. Une nouvelle ouverture depuis la liste ACAPS a ensuite produit un timeout ; cela n'efface pas la première lecture obtenue.

Cette pièce établit des parts LT textuelles, au lieu de les déduire d'un ratio deux tiers/un tiers. Elle ne permet pas de confirmer le référentiel social complet ni toutes ses modifications. Un texte ancien peut demeurer applicable ; aucun texte nouvellement estampillé « 2026 » n'est exigé, mais son applicabilité et ses modifications doivent être établies.

## Consultations complémentaires et limites

| Source primaire | Résultat observé | Portée réelle |
|---|---|---|
| [Fiche CNSS ACAPS](https://www.acaps.ma/fr/files/fichesynthetiquecnsspdf) | Trois pages ouvertes | Synthèse non millésimée ; ne résout pas la consolidation et les règles de paie particulières |
| [CNSS — paiement des cotisations](https://www.cnss.ma/fr/content/paiement-de-vos-cotisations-sociales) | Timeout / aucun tableau obtenu | Ne prouve pas une panne générale, ni l'absence d'un texte ; confirmation directe non obtenue |
| [Ordre du jour gouvernemental du 20 novembre 2014, SGG](https://www.sgg.gov.ma/Portals/0/conseil_gouvernement/OJ/2020/OJ_20.11.2014.pdf) | Document consulté, mention du projet 2-14-14 | Un projet à l'ordre du jour ne prouve ni promulgation ni entrée en vigueur |
| [Tableau Maroc CLEISS](https://www.cleiss.fr/docs/cotisations/maroc.html) | Page ouverte, tableau explicitement **2024** | Corroboration institutionnelle étrangère ; pas une qualification exhaustive des règles marocaines pour les périodes 2026 |
| [Annonce SIMPL-IS MEF](https://www.finances.gov.ma/Fr/Pages/detail-actualite.aspx?fiche=1414) | Page ouverte, annonce **2010** et lien vers un cahier | Ne fournit pas à elle seule un schéma applicable actuel |
| [Cahier des charges 2010 MEF](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf) | Index renvoyant une version 1.0 XML ; ouverture directe timeout | Aucun XSD téléchargé, parsé ou validé ; version actuelle et contrats de dépôt non qualifiés |

Des chemins exploratoires SGG de bulletins 2014 ont échoué à l'ouverture. Les résultats privés ont servi seulement à orienter la recherche, jamais à confirmer une obligation. Les requêtes ciblées CNSS/SGG n'ont pas fourni de pièce supplémentaire exploitable.

## Suite exacte

Paie : retrouver le texte officiel de modification et qualifier branches, parts exactes, assiettes, plafonds, exceptions, dates d'effet et arrondis ; rattacher les preuves au référentiel traçable déjà présent avant tout calcul définitif. Les parts LT désormais documentées ne suffisent pas à confirmer le reste. Pas d'exécution du script historique `donnees_fiscales.sql` sur une base réelle.

EDI : obtenir le schéma officiel réellement applicable, sa version, ses spécifications et exemples de dépôt ; tester localement la validation des fichiers avant d'implémenter un export officiel. Aucun XML de substitution fabriqué.

Ces deux dépendances réglementaires restent **bloquées**. Les tests et développements indépendants se poursuivent. Le point 6 reste en attente de l'utilisateur. Aucune certification ni conformité officielle annoncée.

## Contrôle documentaire

Contrôle local réellement exécuté, code 0 : UTF-8 strict, sept URL HTTPS sur domaines primaires et deux références locales présentes. Ce contrôle n'est pas un test métier ni une validation des documents non obtenus.
