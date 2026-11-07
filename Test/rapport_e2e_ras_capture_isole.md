# Capture RAS déclarée sur règlement — recette isolée

Lot : `RAS-CAPTURE-INTERFACE-20261009-303`.

## Comportement livré

Dans Cycle commercial → Vente ou Achat → Règlements, l'action « Consulter ou déclarer la RAS » ouvre les capacités réelles du serveur et l'historique immuable du règlement. Le montant, la référence et le compte destination restent vides ; seule la date réelle du règlement est proposée. Aucun taux, prorata ou compte fiscal n'est présumé. Le compte est choisi parmi les comptes actifs de la société.

Le serveur reste autoritaire pour les permissions et les blocages : règlement immédiat complet et comptabilisé, par virement ou espèces, facture admissible, absence de capture précédente ou de RAS historique comptabilisée. Une OD brouillon est créée ; son statut réel est affiché et sa validation reste explicite dans le journal. Après capture, les listes et factures sont rafraîchies sans F5. La facture distingue « RAS déclarée sur règlement » de « RAS historiquement comptabilisée » ; aucune ne constitue une attestation.

Si les tables de capture manquent, l'interface indique la migration `083_ras_reglements.sql` à appliquer manuellement. Aucun bouton de capture ni DDL automatique n'est proposé. L'annulation du cash utilise le flux existant de contrepassation et conserve l'historique RAS lié.

## Oracle indépendant et banc

FastAPI réelle, Edge aux largeurs 1365 et 390, PostgreSQL temporaire gardé par nonce ; jamais le PostgreSQL réel. La migration 083 est appliquée explicitement uniquement au laboratoire des cas qui en ont besoin. Un cas distinct conserve les tables absentes.

Facture fictive : 1 000 HT + 200 TVA = 1 200 TTC. Son estimation documentaire existante de RAS reste 100 et ne règle rien automatiquement. Premier cash 400 + capture explicite 30 : solde 770. Deuxième cash 700 + capture explicite 70 : solde zéro. Cinq écritures, onze lignes : somme indépendante `Decimal(1200)+400+30+700+70 = 2400`, débit = crédit = 2 400.

Les quatre écritures de cash et capture sont initialement brouillons, puis validées explicitement dans Journal. Les cinq lignes du collectif 3421 ou 4411 sont lettrées ensemble sous AAA. Elles sont délettrées explicitement avant l'annulation du deuxième cash. Annuler ce cash contrepassera aussi sa capture de 70 : sept écritures finales et solde de facture 770 ; capture active restante 30. Les écritures originales sont photographiées et restent identiques après le délettrage et l'annulation.

## Commandes et résultats

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_capture_isole.py -x --tb=short
```

Résultats intermédiaires conservés :

- 9 octobre, avant interruption : 1 échec en 28,43 s. Le sélecteur « Fermer » correspondait au bouton de fermeture du composant Modal et au bouton de pied de formulaire. Le nouveau test vise maintenant le texte du bouton de pied ; aucune correction métier.
- Relance immédiatement suivante non exécutée : l'approbation automatique a échoué à cause de la limite d'usage. Aucun succès présumé.
- 10 octobre, reprise : 1 échec en 56,59 s. Les captures et le solde zéro étaient corrects, mais le test n'acceptait pas la confirmation native de validation du journal. Le test accepte maintenant les dialogues natifs ; aucune modification applicative.

- Essai suivant : 1 échec en 48,91 s. Le lettrage AAA des cinq lignes a réussi ; le nouveau test attendait à tort DELETE pour le délettrage, dont la route existante utilise POST. Le sélecteur de réponse est corrigé conformément au contrat réel, sans modification de l'application.

- Essai suivant : 1 échec en 47,92 s. L'action de validation était déclenchée avant l'arrivée des quatre brouillons du journal. Le nouveau test attend maintenant leur présence réelle avant de cliquer, sans délai arbitraire ni modification de données ou de l'application.

- Essai suivant : **4 réussis**, 1 échec en 66,45 s. Tous les parcours natifs vente/achat aux deux largeurs ont réussi, y compris AAA, délettrage et annulation. Le dernier cas attendait les tables absentes dans un banc de module qui avait déjà reçu 083 lors des quatre cas précédents. Le cas absent utilise désormais une instance distincte du même fixture isolé, sans suppression de tables ni de données.

- Essai suivant : **4 réussis**, 1 échec en 95,27 s. Le cas sans migration dispose bien d'un banc distinct aux tables absentes, mais a échoué à l'ouverture de Cycle commercial ; un diagnostic de page et l'observateur de navigateur standard ont été ajoutés à ce cas. Aucun résultat métier de ce cas n'est présumé.

- Cas absent exécuté seul avec observateur et diagnostic de page : **1 réussi**, **27,72 s**, code de sortie 0. La cause de l'échec précédent de navigation n'est pas prouvée ; aucun bouton n'a été contourné.

Relance finale du module complet sur le fichier final : **5 réussis**, 25 avertissements de dépendances, **81,20 s**, code de sortie 0. Les quatre parcours incluent la photographie inchangée des cinq écritures originales après annulation et l'oracle final de sept écritures / quinze lignes, débit = crédit = **3 170**. Le cinquième cas confirme les tables absentes, l'avertissement de migration manuelle, l'absence de POST et l'absence de DDL.

Connexes exécutés ici :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_situation_isole.py Test/test_e2e_reglement_edition_isole.py Test/test_patch073_actualisation_edition_facture.py Test/test_patch075_journal_apres_reglement.py -x --tb=short
```

**19 réussis**, 25 avertissements de dépendances, **96,11 s**, code de sortie 0. Les sept parcours Edge RAS existants et les deux parcours d'édition de règlement sont conservés, ainsi que les dix contrôles de rafraîchissement.

`python -X utf8 -m py_compile Test/test_e2e_ras_capture_isole.py` : code de sortie 0 sur le fichier final. `npm.cmd run build` : code de sortie 0, **138 modules**, **9,88 s**. Avertissements existants xlsx/bundles. Aucun fichier applicatif n'a changé depuis ce build. Les validations du backend 293 sont rapportées séparément par son agent.

## Limites

La qualification fiscale et les justificatifs restent du ressort de l'utilisateur. Le montant est déclaré explicitement, sans certification automatique. La migration reste une opération manuelle hors démarrage de l'application. Aucune base réelle, donnée comptable réelle ou règle fiscale nouvelle n'a été modifiée. La recette utilisateur sur son installation reste à effectuer.
