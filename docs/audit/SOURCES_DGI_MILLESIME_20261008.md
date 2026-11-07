# Référentiel DGI et EDI SIMPL-IS — vérification du millésime

Lot `SOURCES-DGI-MILLESIME-20261008` (265). Consultation le 8 octobre 2026. Périmètre : seuls les blocages 09B/09C ; les audits comptables précédents ne sont pas refaits.

**Conclusion : le catalogue exhaustif et le schéma officiel applicables à 2026 n'ont pas été obtenus ni vérifiés.** Le référentiel officiel exhaustif reste à établir ; l'export EDI reste bloqué. Les libellés internes T1…T25 ne constituent pas des codes DGI. Aucun format, taux, modèle ou obligation n'est ajouté au produit à partir de cette recherche.

## Sources et accès réellement vérifiés

| Ressource primaire | Résultat de cette session | Portée retenue |
| --- | --- | --- |
| [MEF — lancement EDI SIMPL-IS, fiche 1414](https://www.finances.gov.ma/Fr/Pages/detail-actualite.aspx?fiche=1414) | Page ouverte par l'outil web ; publication indiquée : **25/11/2010**. | Provenance historique du lancement, aucune preuve du format applicable en 2026. |
| [MEF — cahier EDI SIMPL-IS V1.0](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf) | PDF lisible par l'outil web, **28 pages**, couverture V1.0. Téléchargement HTTP Python séparé : **ConnectTimeout** ; aucun binaire enregistré et aucun SHA-256 calculé. | Document ancien identifié, pas une spécification validée pour 2026. |
| [DGI — portail SIMPL-IS](https://www.tax.gov.ma/wps/portal/DGI/Tele-services/Simpl-IS) | Outil web : inaccessible. HTTP Python : **503**, corps HTML 7 842 octets, pas un XSD ou un catalogue. | Aucun document courant exploitable récupéré. Le 503 ne démontre pas l'absence d'une documentation officielle. |
| [DGI — entrée téléservices](https://www.tax.gov.ma/wps/portal/DGI/Teleservices) | Outil web : timeout. | Annexes actuelles non consultables dans cette session. |
| [MEF — e-services et formulaires](https://www.finances.gov.ma/fr/Pages/e-Services-et-formulaires.aspx) | Résultat indexé officiel disponible ; ouverture web et requête HTTP : timeout. | L'index identifie le service ; il ne fournit pas le schéma applicable. |

Le cahier historique indique, section 3.2 page 6, une évolution possible des formats selon les années. Ses sections 4.2 pages 15–16 associent modèle, période de validité et XSD, et renvoient à une annexe de codification des modèles et tableaux. Ces renvois permettent de préciser les pièces manquantes ; ils ne valident aucun identifiant, encodage, limite de fichier ni règle de dépôt pour 2026. [Cahier historique MEF](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf).

Les recherches web limitées aux domaines officiels `tax.gov.ma` et `finances.gov.ma`, portant notamment sur SIMPL-IS/XSD/annexes/codification/2026/version 2.0, n'ont pas fourni de lien primaire actuel exploitable. L'allégation commerciale d'une version **2.0.3** n'est pas retenue comme preuve normative. Aucun schéma hébergé chez un tiers n'a été utilisé comme référence officielle.

## État des pièces nécessaires

| Pièce à obtenir pour le périmètre TPE/PME retenu | État |
| --- | --- |
| Catalogue officiel exhaustif des tableaux, identifiants de modèle et période de validité couvrant les exercices visés | **Non obtenu** ; 09B non validé exhaustivement. |
| Cahier des charges courant, numéro de version, date d'application et historique des changements | **Non obtenu** ; V1.0 historique seulement. |
| XSD principal et toutes ses dépendances `include/import`, dictionnaire/codification des champs et tableaux | **Non obtenus** ; 09C bloqué. |
| Exemples XML officiels correspondants, règles conditionnelles et contrôles attendus | **Non obtenus** ; aucun générateur ou test de conformité XML réalisé. |

## Prochaine action précise

Depuis un accès officiel DGI fonctionnel, consulter l'espace professionnels SIMPL-IS et télécharger ensemble le cahier, ses annexes de codification, les XSD et exemples correspondant au modèle et à la période concernés. Si leur publication ne qualifie pas clairement 2026, obtenir une confirmation de leur période de validité auprès du support officiel, sans soumettre de dossier fiscal réel. Aucun contact n'a été envoyé pendant cette session.

Conserver alors URL d'origine, date de consultation, version/date d'effet annoncées et SHA-256 de chaque binaire réellement téléchargé. Comparer les identifiants du catalogue avec le référentiel interne existant, puis définir les tests de validation du schéma et des règles métier avant toute activation EDI. Une validation XSD locale seule ne prouvera pas un dépôt accepté.

## Vérifications et limites

Requêtes web et HTTP réellement exécutées ; aucune commande de test applicatif n'est déclarée pour ce lot documentaire. Les requêtes Python étaient en lecture seule avec timeout explicite ; aucune authentification, déclaration ou donnée comptable n'a été transmise. Le téléchargement historique aurait été conservé uniquement sous `.codex-tests`, mais il a échoué : aucun fichier source ou empreinte n'est présenté comme obtenu. Aucun code, migration, archive, matrice ou journal partagé n'a été modifié.
