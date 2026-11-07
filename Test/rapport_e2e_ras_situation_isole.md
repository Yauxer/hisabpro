# RAS — estimation, imputation historique et solde réel

Lot `RAS-INTERFACE-SITUATION-20261009-292` (journal géré par l’agent principal).

## Analyse et correction minimale

Le détail de facture et le modal de règlement présentaient la RAS documentaire calculée comme une somme déjà imputée. Ils proposaient aussi un reste calculé localement après erreur HTTP ou valeur NULL du solde serveur. Le backend 291 distingue désormais estimation et imputation historique ; FactureOut et PDF conservent leur estimation documentaire.

L’interface présente « RAS estimée » avec « ne constitue pas un règlement », et une éventuelle « RAS historiquement comptabilisée » avec « ne constitue pas une attestation ». Le détail, la création et le CSV nomment le net après cette estimation explicitement. Le modal et le détail utilisent exclusivement le solde serveur ; une erreur HTTP est visible, un solde NULL reste à vérifier et le règlement est désactivé. Les réponses devenues obsolètes après fermeture/changement de facture ne mettent pas à jour l’état de situation.

Les deux anciens formulaires définis dans Commercial sont aussi alignés avec la situation API : pas de déduction locale de l’estimation, ni de calcul TTC moins règlements ignorant les autres crédits. La lecture du JSX montre qu’ils ne sont actuellement pas montés ; l’onglet Règlements dirige vers Factures pour enregistrer. Ce lot ne les réactive pas et ne prétend pas les couvrir par un parcours navigateur accessible. Les tests connectés portent sur le modal actif Factures et la consultation du cycle commercial.

Ce lot ne permet pas de saisir une RAS effective nouvelle, ne calcule aucun taux/prorata, ne génère pas de preuve ou d’attestation et ne modifie aucune règle fiscale. Le flux effectif est un lot ultérieur distinct.

## Oracles et périmètre

Quatre recettes Edge bureau/mobile (1365/390), vente et achat : HT 1 000, TVA 200, TTC 1 200 et taux documentaire choisi 10 %, estimation 100/net estimé 1 100. Situation initiale : imputation RAS zéro, solde 1 200. Règlement virement explicite 1 100 : facture partiellement payée, solde 100 ; deux écritures/cinq lignes, débit=crédit 2 300, aucune OD RAS ni ligne 3453/4457. L’écriture de facture validée reste intégralement identique.

Deux recettes historiques : drapeau legacy préparé sur un brouillon fictif avant validation, et OD de 100 préparée explicitement avec les comptes déjà utilisés par le moteur historique. Après validation, le modal indique origine historique/absence d’attestation et solde 1 100. Les pièces et leurs lignes sont photographiées intégralement ; aucun paiement ni nouvelle écriture durant la consultation.

Un cas mobile historique NaN est inséré exclusivement dans le PostgreSQL nonce avant fixation de son état. Le diagnostic reste visible, estimation/solde inconnus ne deviennent pas zéro ; aucun règlement ne peut être enregistré et le NaN source reste intact.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_situation_isole.py -x --tb=short
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_ras_situation_isole.py
npm.cmd run build
```

Compilation Python avant ajout du dernier cas : exit 0. Build frontend réellement exécuté ici : **exit 0, 138 modules, 5,51 s** ; avertissements existants xlsx/taille de bundle.

Premier ciblé après stabilisation backend 291 : **1 failed en 31,58 s**, arrêté par `-x`. Le règlement réel 1 100, le solde 100 et le statut Part. payée dans Factures passent ; le même statut est ensuite présenté En attente dans Cycle commercial → Factures. La table `STATUT` de cet onglet ne contient pas `partiellement_payee` et applique son fallback `en_attente`. Cette anomalie est signalée au principal avant correction, sans changer l’oracle.

Sous-ensemble historique avant reprise complète : **2 passed, 1 failed, 4 deselected en 43,36 s**. Les deux consultations legacy passent ; le test NaN échoue sur son sélecteur exact du bouton. Le snapshot navigateur confirme pourtant le bouton désactivé : son nom accessible contient encore le glyphe d’icône devant « Enregistrer ». Le nouveau test utilise donc le suffixe réel `Enregistrer$` ; aucun comportement ou oracle d’inconnu n’est modifié.

Après autorisation du principal, une seule entrée `partiellement_payee` est ajoutée au mapping de l’onglet Factures commercial. Reprise complète : **7 passed en 53,22 s, exit 0**, aucun échec, erreur ou test ignoré. Les 25 avertissements Pydantic/Starlette existants ne sont pas des tests ignorés.

Compilation Python finale : **exit 0**. Build final après ce correctif de statut : **exit 0, 138 modules, 10,72 s**. Les avertissements Vite existants xlsx/taille de bundle sont conservés.

Commande connexe réellement exécutée :

```powershell
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_ras_lecture_conservation.py Test/test_e2e_ras_editeur_diagnostic_isole.py Test/test_e2e_reglement_edition_isole.py Test/test_patch073_actualisation_edition_facture.py Test/test_patch075_journal_apres_reglement.py -x --tb=short
```

Connexes : **22 passed en 93,96 s, exit 0**, aucun échec, erreur ou test ignoré. Ils incluent les contrôles API de conservation/diagnostic RAS, les recettes réelles d’éditeur et d’édition règlement, ainsi que les anciens supports unitaires Node des lots 073/075. Ils ne sont pas présentés comme 22 parcours PostgreSQL : chaque test conserve la nature de son propre banc. Aucune adaptation des supports 073/075 n’a été nécessaire.

## Limites

Uniquement sociétés et pièces fictives, Edge/FastAPI/PostgreSQL éphémères gardés. Aucune base réelle, aucune écriture définitive réelle ni migration n’est touchée. Les taux sont des données explicites de laboratoire, pas une validation réglementaire. Recette utilisateur et provenance documentaire des retenues historiques restent à effectuer. Journal et ZIP différentiel vérifié assurés par l’agent principal.
