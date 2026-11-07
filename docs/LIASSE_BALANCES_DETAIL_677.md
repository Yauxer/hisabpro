# Préparations de balances : bilan détaillé et exports conservés

Depuis **Comptabilité → Liasse fiscale → Préparer depuis des balances externes** :

1. Choisir l’exercice puis **Importer N / N-1**. Fournir une balance avant clôture technique ; N-1 est facultative. Les colonnes restent `compte`, `debit`, `credit`, avec un compte du plan de la société par ligne.
2. Cliquer **Contrôler et préparer** puis **Conserver une nouvelle version**. Les comptes, montants et états sont conservés dans une version immuable. Un nouvel import crée une nouvelle version.
3. Dans **Préparations conservées**, sélectionner la version souhaitée. Elle reste consultable après rechargement sans joindre à nouveau les fichiers.
4. Utiliser **Exporter la préparation Excel** ou **Exporter la préparation PDF**. Pour une version conservée, les deux documents viennent du serveur et portent le même exercice, numéro de version et empreinte du contenu normalisé.

Le PDF et l’Excel détaillent le bilan : brut N, amortissements/provisions N, net N et net N-1. Les immobilisations corporelles sont notamment décomposées selon les sous-postes déjà présents dans HisabPro. Les sous-postes sont **pour mémoire** : ne pas les additionner une seconde fois aux rubriques et aux totaux. Les amortissements/provisions ne sont pas répartis arbitrairement entre sous-postes ; les nets correspondants peuvent donc être indiqués **Indisponible**.

L’Excel contient une feuille **Dossier** avec la période, les sources déclarées et l’empreinte ; le bilan actif/passif, le CPC et l’ESG disponibles ; et les **balances sources normalisées N/N-1**, compte par compte, débit et crédit. Le PDF ajoute également ces comptes sources en annexe. Ce sont les données normalisées conservées, pas une copie binaire des fichiers d’origine. Les intitulés de comptes non conservés à l’import ne sont pas reconstitués depuis un plan qui aurait changé.

Le logo et l’identité actuels de la société apparaissent dans les exports. Ils restent hors de l’empreinte du contenu conservé ; un changement de logo ne réécrit pas l’ancienne préparation. Une ancienne version sans sources détaillées conserve ses agrégats ; les détails absents ne sont pas inventés.

Sans N-1, aucun comparatif nul n’est fabriqué. Si une balance après clôture technique ne permet pas le CPC/ESG, leur indisponibilité et son motif restent explicites. Les textes importés sont exportés comme texte, jamais comme formules Excel.

Le rôle **Lecture** peut sélectionner et exporter les versions existantes, sans importer ni conserver une nouvelle version. Une préparation d’une autre société reste inaccessible. Une incohérence d’empreinte bloque aussi les exports.

Avant conservation, le bouton Excel conserve son rôle d’export de l’aperçu ; il ne constitue pas une version conservée avec empreinte. Pour obtenir le dossier détaillé traçable, conserver puis exporter la version.

Cette préparation ne crée aucune écriture dans le Journal et ne remplace ni une ETIC documentée, ni les retraitements/liquidations/annexes fiscales, ni un dossier officiellement prêt à déposer. Le mode « Liasse seule » complet reste partiel.

La recette utilisateur reste à effectuer sur un dossier fictif isolé. Les résultats des tests automatisés de ce lot sont consignés séparément dans `Test/rapport_balance_exports677.md`.
