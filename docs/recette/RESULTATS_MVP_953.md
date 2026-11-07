# Résultats du lot 953 — TVA sur encaissements

**44 tests distincts réussis, aucun échec ni test ignoré**, dans la finale `enc953_final` : 904,09 secondes dans le XML, code de sortie 0 (904,62 secondes affichées par pytest).

- 3 parcours Edge/API/PostgreSQL isolé : année complète en encaissements sur ordinateur et mobile, puis non-régression annuelle du régime des débits sur ordinateur.
- 33 tests API/SQL sur PostgreSQL natif isolé : compensations clients/fournisseurs, pièces absentes, dates incohérentes, annulation effective, isolation des sociétés, migration 126 et concurrence des avoirs.
- 8 tests unitaires : reports de crédit et calculs indépendants du jeu de recette.

Les deux variantes annuelles couvrent 50 opérations et 118 lignes avant clôture, les douze déclarations et leurs impressions PDF, la clôture, les à-nouveaux, le snapshot IS et le recouvrement en 2026 sans modification des écritures de 2025. TVA collectée annuelle : 31 500 MAD ; récupérable : 11 600 ; due : 19 900. Banque : 287 730 ; bilan net : 337 010 ; résultat net : 106 409,75 ; solde IS : 23 220,25.

Le défaut reproduit omettait 500 MAD de TVA lors de l'imputation d'un avoir. Le correctif prend en compte les compensations explicitement signées. Une ancienne date technique d'imputation ne devient pas automatiquement une date fiscale : les cas sans accord confirmé restent signalés.

La fiche **HP-FIS-033 passe de Partiel à Réussi dans le périmètre automatisé**. Le suivi compte désormais **249 réussis, 11 partiels et 12 bloqués**, sur 272 fiches ; les statuts de recette humaine restent inchangés. Les 339 anciens documents de recette ont été conservés octet pour octet.

Le candidat comporte 550 empreintes : cinq fichiers produit corrigés et une migration additive. Le build Vite isolé a réussi : 214 modules, 10,29 secondes. Les scripts Word/PDF et Excel ont été exécutés ; le PDF compte trois pages, les XML du Word et les feuilles/champs vierges de l'Excel sont contrôlés. Aucun contrôle visuel dans Microsoft Word n'est déclaré.

Après les parcours Edge, les doublons descriptifs du JSON ont été synchronisés. Les neuf groupes d'entrées et d'oracles financiers sont strictement identiques entre le fichier exécuté, conservé en preuve, et le fichier livré. Les tentatives initiales échouées sont conservées et ne sont pas additionnées aux 44 succès finaux.

La migration 126 n'a pas été appliquée à votre PostgreSQL. Elle doit être vérifiée d'abord sur une copie restaurable. Aucune restauration supplémentaire, recette humaine, certification ou transmission DGI n'est déclarée. Les réserves ETIC, d'exploitation et de Personnel/Paie restent distinctes.

[Preuves](../../Test/PREUVE_MVP_953.json) · [Rattachement](../../Test/QUALIFICATION_FICHES_953.json) · [Guide](TVA_ENCAISSEMENTS_953.md) · [Word](MODE_EMPLOI_TVA_ENCAISSEMENTS_953.docx) · [PDF](MODE_EMPLOI_TVA_ENCAISSEMENTS_953.pdf) · [Données Excel](JEU_RECETTE_ENCAISSEMENTS_953.xlsx) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_953.xlsx).
