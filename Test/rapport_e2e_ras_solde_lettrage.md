# RAS estimée — solde complet et lettrage connecté

Lot `RAS-SOLDE-LETTRAGE-20261009-304`, exécuté par l'agent principal.
La facture fictive et son tiers sont préparés par les API réelles, puis sa
première écriture est validée. Les deux paiements, la validation des écritures
de paiement et le lettrage se font dans le navigateur Edge réel, sur les API
FastAPI et PostgreSQL nonce de la fixture `application`.

Quatre variantes : vente/achat, largeurs 1 365/390 pixels. HT 1 000, TVA 200,
TTC 1 200, taux documentaire choisi 10 %, estimation 100. Le formulaire propose
1 200 à régler. Un premier paiement bancaire explicite de 1 100 laisse 100 et
le statut partiellement payé ; un second paiement de 100 solde la facture.
L'estimation reste 100, l'imputation RAS reste zéro. Aucune OD RAS automatique,
aucune ligne 3453/4457 et aucun drapeau historique nouveau.

Les deux écritures de paiement sont validées par l'action du journal. Les trois
lignes du vrai auxiliaire sont sélectionnées et lettrées sous AAA ; le code
persiste après rechargement. Trois écritures définitives, sept lignes,
débit = crédit = 2 400. Collectif 3421/4411 soldé ; banque 5141 +1 200 en vente
et −1 200 en achat. Les snapshots complets de la facture comptabilisée restent
identiques pendant les paiements ; toutes les écritures et lignes persistées
restent identiques lors du lettrage. Aucune erreur navigateur ou serveur.

Commande réelle, avec `PYTHON_DOTENV_DISABLED=1` :

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_solde_lettrage_isole.py -x --tb=short
```

Première exécution, session64166 : **1 échec, 51,30 s**, attente de réponse de
validation par lot. Le nouveau test n'acceptait pas la confirmation native du
journal ; Playwright la rejetait par défaut, avant tout appel de validation.
La présence du `confirm` a été vérifiée dans `Journal.jsx`. Le test accepte
désormais les dialogues de l'opérateur fictif comme les recettes existantes.
Aucun code applicatif ni assertion comptable n'a été modifié.

Reprise, session11754 : **4 réussis, 25 avertissements, 49,81 s, code retour 0**.
Les avertissements Starlette/Pydantic existants sont conservés. Compilation
Python à consigner dans le journal avant livraison.

Uniquement des sociétés fictives dans des clusters isolés. Aucun PostgreSQL
réel, aucun changement de schéma ni de données comptables réelles. Cette recette
ne teste pas une nouvelle capture de retenue, un prorata fiscal ou une
attestation. Recette utilisateur et qualification fiscale demeurent distinctes.
