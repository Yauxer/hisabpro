# Recette connectée achats BC → réception → facture — lot 271

Exécution réelle du 8 octobre 2026 UTC. Deux fichiers ajoutés uniquement :
`Test/test_e2e_cycle_achat_isole.py` et ce rapport. Aucun correctif applicatif,
aucune migration et aucune donnée réelle modifiés.

## Périmètre et oracle indépendant

Chaque scénario utilise une société fictive distincte, un fournisseur rattaché
au compte 4411 et un article stockable sans stock initial. Deux unités à
500 MAD HT donnent 1 000 MAD HT, 200 MAD TVA à 20 % et 1 200 MAD TTC.
Ce taux constitue une donnée de recette explicite ; aucune règle fiscale nouvelle
n'est introduite. Sur le brouillon converti, un vrai PATCH API renseigne
la référence fournisseur fictive, la nature d'achat `charge` et la déductibilité
100 %. Les valeurs persistées sont contrôlées avant validation.

L'écriture d'achat attendue, puis réellement observée et validée, comporte trois
lignes : débit 6111 = 1 000, débit 34552 = 200 et crédit 4411 = 1 200 MAD.
Débit = crédit = 1 200 MAD. La ligne fournisseur conserve le `tiers_id` réel
du jeu fictif et le snapshot du compte auxiliaire.

## Parcours navigateur réellement exécuté

Microsoft Edge headless : bureau 1 365 px et mobile 390 px, clics ordinaires
sans `force`. Authentification réelle, frontend Vite et API séparés, PostgreSQL
éphémère gardé par répertoire et nonce ; aucun PostgreSQL utilisateur utilisé.

1. Cycle commercial → Achat → Nouveau BC ; choix du fournisseur et de l'article,
   quantité 2, création de la commande.
2. Réceptionner → Nouveau bon de réception ; réception des deux unités avec
   conservation du lien au BC et à sa ligne.
3. Bons de réception : Marquer en cours puis Marquer réceptionné.
4. Facturer le bon de réception → Créer la facture en brouillon ; facture achat
   visible dans l'onglet Factures du cycle, sans numéro définitif avant validation.
5. Qualification charge/100 % et référence fournisseur par API réelle sur ce
   brouillon, puis page Factures : validation et comptabilisation par navigateur.
6. Journal : validation de l'unique écriture. Retour au cycle Achat → Factures,
   puis rechargement : facture toujours visible.

Le déclencheur de stock achat existant est vérifié dans la société : `facture`
(valeur de repli existante si NULL). Le BC, le BR, sa confirmation de réception
et la création de facture n'engendrent ni stock ni écriture dans cette configuration.
La validation facture produit exactement une entrée de deux unités, stock 0 → 2,
avec source facture et ligne exacte et clé d'idempotence. La comptabilisation
et les rechargements ne produisent aucun mouvement supplémentaire.

Les liens `bon_commande_id`, `facture_id`, `source_ligne_bc_id` et
`source_ligne_bl_id` sont contrôlés sur les données persistées. Les refus suivants
sont exécutés par API réelle : seconde conversion BC → réception = 400,
seconde conversion BR → facture = 409, seconde comptabilisation facture = 409.
Après ces refus et les rechargements, il reste exactement un BC, un BR,
une facture, une écriture et un mouvement de stock. Toutes les colonnes persistées
de l'écriture validée et de ses lignes restent identiques.
Aucune erreur JavaScript ou réponse serveur 5xx observée pendant les parcours.

## Commandes et résultats

Depuis la racine du dépôt, avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_isole.py -x
```

- Premier essai : **1 failed**, 25 avertissements, **25,78 s**, sortie 1,
  session 67570. Erreur de préparation du test : attente incorrecte d'un objet
  facture complet dans la réponse PATCH qui retourne un message. Le parcours
  BC → BR → facture était déjà exécuté, sans 5xx. Correction de l'assertion
  uniquement : lecture des champs effectivement persistés après ce PATCH.
- Deuxième essai : **2 passed**, 25 avertissements, **33,15 s**, sortie 0,
  session 19421, bureau et mobile.
- Renforcement final des contrôles d'unicité, puis ciblés et connexes :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_e2e_cycle_achat_isole.py Test/test_e2e_cycle_commercial_isole.py Test/test_e2e_avoir_fournisseur_isole.py
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 -m py_compile Test/test_e2e_cycle_achat_isole.py
```

**5 passed**, 25 avertissements, **96,79 s**, sortie 0, session 72220 : deux
cycles achat, un cycle vente et deux avoirs fournisseurs. Compilation Python :
sortie 0. Avertissements existants : multipart et configuration Pydantic obsolète.

## Limites et prochaine recette

Les paramètres TVA du brouillon converti sont explicités par API : ce lot ne
valide pas leur modification depuis l'éditeur navigateur. La configuration de
stock déclenché au BR, les réceptions/facturations partielles, les permissions
inter-sociétés de ces conversions et les exports PDF ne sont pas couverts par
ce nouveau scénario. Le règlement et le lettrage sont couverts par les scénarios
connexes d'avoirs et d'acomptes, sans être ajoutés au cycle BC → BR → facture ici.

Cette recette automatisée isolée ne constitue ni une recette utilisateur réalisée
sur les données réelles ni une validation réglementaire. Prochaine extension
possible : réception et facturation partielles avec réglage de stock au BR,
en préservant la règle observée et ses liens de traçabilité.
