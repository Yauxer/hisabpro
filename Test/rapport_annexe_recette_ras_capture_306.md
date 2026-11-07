# Annexe utilisateur — capture RAS déclarative et annulation

Lot 306 — 10 octobre 2026. Périmètre documentaire exclusivement : générateur, tests, PDF/Excel/Markdown et présent rapport. Aucun fichier du lot 298 ni source applicative modifié.

## Parcours proposé

Deux cas **Non testé**, vente et achat dans deux sociétés fictives neuves distinctes. Activation manuelle 083 sur une copie isolée, suivant le guide 302 ; aucune commande contre une base réelle. Le lecteur utilisateur ne doit ni manipuler SQL ni fabriquer d’historique. La date D est le jour réel de recette, E son année, à noter explicitement avant de commencer ; les opérations sont effectuées le même jour pour correspondre à l’annulation par bouton qui utilise le jour courant.

Les noms des boutons et champs ont été vérifiés dans les sources UI et la recette 303 présente : Consulter ou déclarer la RAS, Montant RAS *, Date de l’opération RAS *, Référence RAS *, Compte destination RAS *, Préparer la RAS déclarée, Valider les brouillons, Lettrer 5 lignes, Délettrer le code AAA et Annuler par contrepassation. Les confirmations natives sont explicitement indiquées. La préparation des virements passe par Encaisser le client / Payer le fournisseur.

TVA 20 %, estimation 10 %, montants déclarés 30/70 et comptes choisis 3453/4457 restent des données de laboratoire. Aucun compte, taux ou prorata n’est imposé comme règle fiscale. OD déclaratives préparées en brouillon, contrôlées puis validées ; pas d’attestation authentifiée ni de crédit IS automatique.

## Oracle indépendant

Calculs `Decimal`, sans import des services métier ni connexion à une base :

- HT 1 000 + TVA 200 = TTC 1 200 ; estimation documentaire 100.
- Virement 400 : reste 800 ; capture explicite 30 : reste **770**.
- Virement 700 : reste 70 ; capture explicite 70 : reste **0**.
- Une facture, deux virements et deux captures : **cinq écritures / onze lignes**, débit = crédit **2 400**. Quatre brouillons nouveaux à valider après la première facture déjà validée.
- Cinq lignes du tiers lettrées sous AAA dans une société vierge, puis délettrage explicitement demandé avant annulation. Le retrait volontaire du lettrage ne doit pas être présenté comme une anomalie de conservation des montants.
- Annulation du second virement et de sa capture : reste **770**, retenue active **30**, **sept écritures / quinze lignes**, débit = crédit **3 170**.
- Soldes finaux D − C : vente, banque +400 / retenue +30 / client +770 ; achat, banque −400 / retenue −30 / fournisseur −770. Aucun apport initial prévu. Les cinq écritures originales conservent comptes, montants, dates, références et numéros ; leur code de lettrage a été retiré volontairement.

## Documents réellement générés et ouverts

`docs/recette/ANNEXE_RECETTE_RAS_CAPTURE_20261010.md`, `.pdf`, `.xlsx` : PDF **9 pages** ; Excel **Synthèse**, **Recouvrement**, **Jeu de données**. Deux statuts Non testé, résultats réels/anomalies/preuves réelles/observations vides ; preuves attendues dans une colonne distincte. Synthèse avec formules de suivi, filtre et validation des statuts. Les formules ont été relues, pas calculées par un moteur Excel dans cette session.

Le PDF et l’Excel du dépôt ont été ouverts avec PyMuPDF et openpyxl, indépendamment des documents temporaires générés par pytest. Pages PDF **1, 4 et 5** rendues dans `.codex-tests/recette306-visuel/`, puis inspectées visuellement : texte lisible, actions et résultats accessibles, rubrique de capture et d’annulation présente. Après suppression des lignes isolées en début de page, dernier rendu également généré. Ces images temporaires ne sont pas incluses dans le ZIP.

## Commandes et résultats réels

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/generer_annexe_recette_ras_capture_306.py
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_annexe_recette_ras_capture_306.py Test/test_annexe_recette_ras_298.py Test/test_annexe_recette_achats_partiels_284.py --tb=short
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/generer_annexe_recette_ras_capture_306.py Test/test_annexe_recette_ras_capture_306.py
```

Générations sortie 0. Premier passage : **9 réussis en 2,02 s**. Après labels français des oracles Excel : **9 réussis en 1,43 s**. Dernier passage après amélioration de pagination : **9 réussis en 1,40 s**, sortie 0, aucun échec ni test ignoré. Trois tests nouveaux, six connexes des annexes 298/284 ; arithmétique indépendante, sources présentes, suivi vierge, contenu et ouverture PDF/Excel/Markdown. Compilation sortie 0.

## Limites

Cette étape teste le document et ses oracles, pas l’application ni la recette humaine. Aucun nouveau test E2E navigateur ou PostgreSQL lancé pour le lot 306 ; les preuves métier 293/303 et sauvegarde 305 sont distinctes et ne prévalident pas les cases du classeur. Aucun historique réel, migration appliquée ou processus utilisateur touché. Journal et ZIP : agent principal.
