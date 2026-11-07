# Lot639 — cahier de recette des sociétés liées

Word, PDF24pages, Excel avec tableau de bord et jeu JSON.20cas détaillés,
tous **Non testé**, résultats réels/anomalies/preuves vides. Deux limites
non exécutables séparées : consolidation fiscale et synchronisation automatique
des paiements/avoirs/livraisons. La recette humaine point6 reste en attente.

L'annexe couvre deux dossiers vierges, paramètres/préfixes, tiers/articles,
capitaux, liaison, vente, achat correspondant, deux Journaux, règlements
séparés, lettrages, états/FEC/PDF, lecteur, doublon, écart de brouillon et retrait.
Une variante utilise d'autres sociétés ; aucune facture définitive du scénario
principal n'est modifiée pour provoquer un contrôle.

Oracle indépendant en centimes, sans services comptables applicatifs :

| Contrôle | Société A | Société B |
|---|---|---|
|Capital bancaire initial|10000,00|10000,00|
|Facture HT / TVA / TTC|500 /100 /600|500 /100 /600|
|Règlement séparé|600,00 encaissé|600,00 payé|
|Banque finale|10600,00|9400,00|
|Résultat avant impôt|500,00|−500,00|
|Bilan actif=passif|10600,00|9500,00|
|Pièces / lignes définitives|3 /7|3 /7|
|Débit=crédit Journal|11200,00|11200,00|
|Solde client/fournisseur|0|0|

Le jeu réel a été exécuté via FastAPI/PostgreSQL natif jetable sous LOGIN
applicatif : préfixesATLAS/RIF distincts, référence fournisseurATLAS conservée,
montants de chaque ligne et de chaque pièce comparés, FEC7lignes par société
sommés, CPC/bilans contrôlés, absence de stock pour services et deux lettragesAAA
avec pièces définitives inchangées. Après le paiementB, A restait impayée600
jusqu'à l'enregistrement séparé de son encaissement. Ces résultats automatisés
ne remplissent pas les statuts humains du classeur.

5cas documentaires/oracle API passes24.983s, puis4documentaires finaux passes0.808s ; PDF24pages, XMLWord et Excel/formules/statuts valides, liens verifies {'docs/recette/README.md': 17, 'docs/recette/PAR_OU_COMMENCER_20261019.md': 43}.20cas humains Non teste,2limites separees. Oracle natif11200D=C par societe,6pieces/14lignes ; banques10600/9400, resultats500/-500, bilans10600/9500, lettrages sans modification des definitifs.

Commandes réellement exécutées :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/generer_annexe_societes639.py
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_societes639.py Test/test_oracle_societes639_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_societes639.py -q
```

Les contrôles documentaires lisent les vrais XML Word, PDF et cellules/formules
Excel, les cas et leurs statuts. Relecture visuelle PDF de la couverture et du
casGRP-009 ; présentation des données en tableau lisible et espacements améliorés,
puis quatre contrôles documentaires relancés. Le domaine email de laboratoire
example.com est accepté par le validateur installé ; example.test a été écarté
avant la recette réelle. Aucun envoi de message effectué.

README et index partenaire mis à jour, anciens cahiers conservés. Word et Excel
interactifs restent à ouvrir par le partenaire. Aucun impôt ou crédit de groupe
calculé, aucune déductibilité réelle qualifiée, aucune base utilisateur utilisée.
Installation101/102 et production restent non validées. RH/paie différées.
