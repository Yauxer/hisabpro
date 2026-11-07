# Reprise exacte après les contrôles annuels913–917

Les cumuls annuels, les frais professionnels généraux, le RNI constitué, le contrôleIR sourcé et ses exports sont présents. Ne pas les réimplémenter. Lire le [rapport917](RESULTATS_PAIE_917.md), les preuves et le journal actif, puis vérifier les processus et fichiers avant toute reprise de tests.

La prochaine priorité métier est **le calcul périodique connecté**, avant le net, les bulletins définitifs et les écritures. Le contrôle annuel existant ne fournit pas à lui seul toutes les règles de retenue mensuelle et de régularisation. Cette limite concerne la qualification des règles ; elle ne remet pas les montants annuels déjà conservés à zéro.

Sources effectivement obtenues dans cette session :

| Document | Accès et contenu réellement examiné | Portée |
|---|---|---|
| CGI2026, documentDGI publié par le CRI Casablanca-Settat | PDF765pages, SHA256`fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1` ; articles59,156 et167 relus sur les pages utiles ; barème et famille déjà documentés dans901/911 | Frais généraux annuels, retenue sur chaque paiement et arrondis. Ne prouve pas à lui seul une formule périodique pour tous les cas |
| Note circulaireDGI733, publiée par MarocPME | TéléchargementPowerShell200,1620763octets, SHA256`c6946daa9b360accc1cb7fe1a3d3d695bb197e5189b305748d36bf74dbd2ad34` ; passage sur les frais annuels et date d’effet2023 examiné | Illustration annuelle et distinction de revenus acquis ; ne pas reprendre son ancien barèmeIR ou ses valeurs familiales en2026 |
| DGI717, lien direct historique | Ancien accès403 documenté dans909 ; nouvelle tentativePowerShell503. Le miroir trouvé a également renvoyé503 | Corps non récupéré dans cette reprise ; ne pas annoncer sa vérification intégrale |
| DGI736/737 | Publications officielles repérées ; accès testés en délai dépassé pour les documents concernés | Aucune méthode mensuelle qualifiée sur la seule base d’un titre ou d’un extrait de recherche |

[CGI2026 duCRI](https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf) · [Note733 publiée par MarocPME](https://marocpme.gov.ma/wp-content/uploads/2023/03/NC-N%C2%B0-733-relative-aux-mesures-fiscales-de-la-LF-2023-vf.pdf) · [PublicationsMEF](https://www.finances.gov.ma/fr/Pages/publications.aspx).

Pour débloquer le calcul périodique, vérifier précisément les textes/doctrines applicables, leur millésime et les exemples officiels relatifs à :

- périodicité du barème, des frais professionnels, du seuil, des plafonds et des charges de famille ;
- revenu acquis, période concernée et date réelle de paiement, notamment primes, rappels ou revenus d’une autre année ;
- cumuls et régularisations, embauche/départ, changement de situation familiale et autres employeurs ;
- ordre et niveau des arrondis : assiette, retenue individuelle et versement global, qui ne sont pas le même montant ;
- traitement des déductions conditionnelles et cas particuliers encore hors du cadre général.

Conserver ensuite un référentiel daté avec sources et empreintes, des oracles indépendants pour les bornes et cas irréguliers, puis raccorder les préparations brutes/sociales/fiscales existantes. Ne pas proposer un résultat final tant qu’une condition déterminante est inconnue. Une approbation technique ou une règle de recette fictive n’est pas une preuve réglementaire.

Les derniers jeux automatisés restent synthétiques : régimeFISC909 et preuves marquéesFICTIF. Ils valident la mécanique, jamais un taux applicable à une vraie paie. Ne pas injecter ces règles comme valeurs légales par défaut.

L’environnement habituel, les secrets réels et les données comptables réelles restent interdits dans cette session. Continuer avec les ciblesPostgreSQL natives nonce, HTTP et Edge isolées. Ne pas substituerSQLite à un contrôle dépendant dePostgreSQL. Les fonctionnalités annuelles sont livrées, la recette utilisateur reste à effectuer et la production n’est pas validée.
