# E2E connecté — Avoir client, retour physique et contrepassation

Lot `E2E-AVOIR-RETOUR-20261007`, exécuté le 7 octobre 2026.
Fichier : `Test/test_e2e_avoir_retour_isole.py`.

## Environnement et préparation

Edge headless, vraie application React, FastAPI réel et PostgreSQL éphémère
du banc E2E existant. Aucun mock API, aucune lecture de `.env`, aucun PostgreSQL
réel ni aucune donnée comptable historique modifiée.

L'API prépare une société/client/article fictifs et une facture de deux unités
à 500 MAD HT. Stock initial 10, coût d'achat configuré 300, TVA configurée 20 %,
compte de vente 7111. La facture est validée et comptabilisée, puis son écriture
validée par API avant le parcours navigateur : stock 8 et créance 1 200 MAD.
Ces paramètres reprennent les possibilités du produit, sans règle fiscale ajoutée.

## Parcours navigateur et preuves

1. Depuis le détail de la facture validée, créer un avoir pour une unité,
   motif « Retour fictif d'une unité », en cochant « Retour physique de
   marchandise ». L'avoir porte la ligne source exacte : HT 500, TVA 100,
   TTC 600 MAD. Avant comptabilisation, le stock reste 8 et les lignes de
   la facture définitive sont inchangées.
2. Ouvrir le détail de l'avoir sur la page Avoirs et comptabiliser. Le stock
   passe à 9 ; une entrée porte l'origine avoir et sa ligne. L'avoir conserve
   le lien vers la facture d'origine. Le ledger relie la facture par cet avoir,
   et son champ direct `facture_id` reste nul selon l'implémentation existante.
3. Vérifier l'écriture AV initialement brouillon : D7111 500, D4455 100,
   C3421 600 MAD. La valider réellement depuis le Journal. L'API de situation
   de la facture indique 600 MAD d'avoirs et 600 MAD de solde restant.
4. Sans utilisation/remboursement de ce crédit, annuler l'avoir depuis son
   détail. Le produit crée une écriture inverse, initialement brouillon,
   reliée par `ecriture_annulation_id`. Les lignes définitives d'origine sont
   conservées avec leurs identifiants, comptes, montants et snapshots auxiliaires.
5. Vérifier la compensation physique : mouvement `correction` de quantité
   absolue 1, stock avant 9/après 8, avec `annule_mouvement_id` pointant vers
   l'entrée d'origine. Cette correction est le flux existant du moteur stock.
6. Valider l'écriture inverse dans le Journal : C7111 500, C4455 100,
   D3421 600. Le solde facture retrouve 1 200 MAD, sans avoir actif.
7. Répéter l'annulation via API réelle : même identifiant d'écriture inverse,
   aucune création supplémentaire. Recharger la page Avoirs, contrôler le
   statut Annulé et l'absence de bouton d'annulation. Trois écritures et quatre
   mouvements stock restent présents ; stock 8, toutes les lignes inchangées.

L'annulation de l'avoir utilise une contrepassation traçable ; elle ne modifie
ni ne supprime la facture ou l'écriture de l'avoir déjà validée. Les transitions
« comptabilisé » et « écriture définitive » sont contrôlées séparément.
Le test ne prétend pas annuler arbitrairement une facture définitive.

## Commandes exécutées

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_avoir_retour_isole.py -x
```

Exécution finale : **1 passed, 25 warnings in 21.95s**, code retour 0.
Aucune erreur JavaScript ni réponse serveur en erreur pendant ce scénario.
Les avertissements concernent les dépréciations Pydantic/python_multipart.

Trois premières exécutions ont échoué sur des erreurs du test, ensuite corrigées :
action de table non visible au viewport (37,26 s), ambiguïté entre boutons de
table et de détail (18,57 s), puis présomption d'une sortie au lieu de la
correction réellement prévue par le moteur (19,80 s). Le test cible le détail
visible sans clic forcé et contrôle le flux comptable/stock existant.
Aucun changement du code produit dans ce lot.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_fact6_avoirs_retours.py Test/test_factG_acomptes_avoirs.py Test/test_stock_integrite_mouvements.py
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 -m py_compile Test/test_e2e_avoir_retour_isole.py
```

Connexes : **43 passed in 2.32s**, code retour 0. Compilation : code retour 0.
La preuve PostgreSQL vient de l'E2E connecté ; les tests connexes ne sont pas
présentés comme une validation de la base réelle.

## Limites

L'avoir testé est un retour client partiel, crédit inutilisé. Les utilisations,
remboursements, avoirs fournisseur, RRR/corrections de prix, périodes clôturées
et concurrence ne sont pas exercés par ce scénario navigateur. Le flux bloque
l'annulation lorsque des utilisations actives existent ; ce nouveau test ne
déclare pas cette branche validée. La correction de stock est une annulation
du retour physique fictif prévue par le produit ; aucune donnée réelle n'est
réparée. Aucun e-mail préparé/envoyé. La recette utilisateur et la validation
réglementaire restent à effectuer séparément.
