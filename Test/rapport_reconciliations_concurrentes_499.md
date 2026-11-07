# Lot499 — Réconciliations historiques concurrentes

Trois courses sont reproduites sur API et PostgreSQL nonce : deux reclassements,
reconstitutions ou corrections simultanés créent chacun leur écriture. Le plan
reste aussi modifiable après une correction RECON-AMORT, et une dotation AM
supplémentaire2000 peut être générée après une correction2000 du même exercice.

Les trois assistants prennent désormais le verrou par immobilisation495 avant
leur diagnostic. Le plan est relu sous verrou ; les mutations courantes et
autres assistants sont refusés409 pendant l'opération. La protection société
face à la clôture497 reste active. Les sélections répétant une immobilisation
sont refusées400 avant toute mutation, pour éviter des choix contradictoires
et le rafraîchissement d'un objet déjà modifié dans le même lot.

Le verrou du plan utilise les mêmes familles de références AM/RECON-AMORT que
le diagnostic existant. Une correction sur N bloque aussi une nouvelle
dotation automatique sur N et demande un contrôle explicite. Elle ne bloque
pas une dotation indépendante de N+1. Aucun montant ni compte historique n'est
deviné, aucun original validé réécrit, aucune réparation réelle effectuée.

## Tests exécutés

- Avant correction :4échecs en37,45s ; puis2échecs/3désélectionnés en29,01s pour
  tester séparément le gel du plan et la dotation après correction.
- Ciblés corrigés :5réussis en31,58s.
- Extension :14réussis en40,33s,29avertissements,0échec/erreur/ignoré.

Les choix sont explicites dans le laboratoire : matériel10000HT/TVA2000,
contrepartie4481 confirmée pour la reconstitution, catégorie«Matériel de bureau»
confirmée pour le reclassement. Une seule écriture attendue par assistant :

- Reclassement :2352D10000/2355C10000.
- Reconstitution :2355D10000+34551D2000/4481C12000.
- Correction annuelle :61935D2000/28355C2000.

Les acquisitions initiales validées restent identiques. Les tests couvrent les
trois doubles opérations, six conflits réciproques avec une modification
courante, deux sélections dupliquées, annulation complète d'un lot sur conflit
tardif puis reprise, gel du plan et refus du double amortissement avec N+1
conservé. Aucun succès n'est attribué aux passages avant correction.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_reconciliations499_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_e2e_cloture_isole.py -ra
```

**83exécutions réussies,29avertissements en272.57s**,0échec/erreur/ignoré.
Les14cas499 sont regroupés avec les oracles497/495/493, les tests purs historiques,
les parcours Edge immobilisations/vente/achat/règlement/lettrage/clôture, une
restauration098 et l'ancien E2E de clôture sans098. Les passages successifs ne sont
pas additionnés, ni les parcours répétés qualifiés de cas métier distincts.

Restauration :74tables/quatre pièces/données/schéma/ACL/séquences/FEC conservés,
fonctions098 et refus409/reprise disponibles ; source préservée et cibles nettoyées.
Invariants0 :pièce déséquilibrée,montant non fini,définitive sans numéro/date.
Sources/fonctions/ACL inchangées pendant les tests ;3Python compilés,
98SQL et115guides intacts.

## Installation et limites

Installer `routers/immobilisations.py` avec les fichiers497 déjà livrés puis
redémarrer l'API. Aucune nouvelle migration. Les écritures produites restent
en brouillon à contrôler et valider ; les justificatifs et décisions historiques
manquants restent à fournir. Le choix explicite d'un compte dans un laboratoire
ne prouve pas celui d'une entreprise réelle.

Point de reprise : le contrôle de dotations de clôture recherche encore une
référence AM classique. La recette annuelle avec une correction RECON-AMORT
seule doit être exécutée avant d'annoncer ce parcours couvert ; ne pas créer
une seconde dotation pour contourner ce contrôle. Le refus de génération après
correction ne vaut pas validation du montant ni du rapprochement de clôture.

SQL arbitraire et opérations qui ignorent le protocole restent hors garantie.
Frontend inchangé, pas de nouveau build Vite. Aucune base réelle utilisée ;
recette utilisateur/production et point6 en attente. Les98SQL et115guides
restent intacts.
