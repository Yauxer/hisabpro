# Préfixe des factures et modèle de libellé — lot 273

## Diagnostic et correction

La numérotation et le modèle de libellé sont deux paramètres distincts déjà
fonctionnels. Le préfixe participe au numéro définitif réservé à la validation ;
le modèle est appliqué à la comptabilisation. Le texte littéral `FA°` d'un
modèle `FA° {numero} {tiers}` ne devient donc pas automatiquement `VTE°`.

La recette réelle a reproduit l'aperçu figé dans Paramètres : après sauvegarde
du préfixe `VTE`, il affichait encore
`FA° FA-2026-014 SOCIÉTÉ ALPHA CONSULTING SARL`. Cet exemple était codé en dur.
Les nouvelles pièces avaient pourtant les numéros attendus.

Correction limitée à `src/pages/Parametres.jsx` : l'exemple utilise désormais
le préfixe saisi, l'exercice sélectionné et le préfixe des avoirs pour leur
modèle. Sa référence illustrative suit le préfixe BL. La mention « exemple »
évite de confondre cette illustration avec une réservation de numéro.
L'onglet Fiscalité permet aussi d'enregistrer directement les modèles avec
le handler, l'état de sauvegarde et les contrôles serveur existants.

Aucun backend, migration, numéro existant, séquence, écriture ou règle
comptable n'a été modifié. Les réglages ne réécrivent pas les pièces définitives.

## Recette automatisée réelle

`Test/test_e2e_facture_libelle_parametres_isole.py` démarre un cluster PostgreSQL
éphémère distinct, une API isolée et Edge avec le frontend réel. Les données
sont entièrement fictives ; aucun serveur ou PostgreSQL utilisateur n'est utilisé.

Pour l'exercice 2026 exécuté ici :

| Action | Numéro définitif | Libellé attendu |
|---|---|---|
| Modèle initial `FA° {numero} {tiers}` | FA-2026-001 | FA° FA-2026-001 CLIENT LIBELLÉ FICTIF |
| Préfixe remplacé par VTE dans l'interface | VTE-2026-002 | FA° VTE-2026-002 CLIENT LIBELLÉ FICTIF |
| Modèle remplacé et enregistré dans Fiscalité | VTE-2026-003 | VENTE VTE-2026-003 / CLIENT LIBELLÉ FICTIF / REF-MODELE / 15/03/2026 |

Chaque facture : HT 100, TVA 20, TTC 120 MAD ; chaque écriture définitive :
débit = crédit = 120 MAD. Les snapshots SQL complets des factures, écritures
et lignes restent identiques après les modifications de paramètres. La séquence
ne bouge pas lors de la seule sauvegarde des réglages. Deux CSV téléchargés
depuis le journal avant et après le dernier changement de modèle sont ouverts
et identiques ; leur colonne « Libellé écriture » contient les trois intitulés.
L'écran du journal conserve ses libellés de mouvements existants.

### Commandes et résultats

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_facture_libelle_parametres_isole.py --tb=short -s
```

Résultat final : **1 passed, 22,85 s**, code 0. Aperçu réellement observé :
`Aperçu (exemple) : FA° VTE-2026-014 SOCIÉTÉ ALPHA CONSULTING SARL`.
Aucune erreur JavaScript ni réponse API 5xx dans ce parcours final.

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_patch057_parametres_multisocietes.py Test/test_session132_admin_parametres.py Test/test_patch063_tiers_libelles_modeles.py Test/test_patch082_libelles_lignes_ecritures.py Test/test_fact1_facturation_fondations.py --tb=short
```

Résultat : **49 passed, 2,37 s**, code 0.

`python -X utf8 -m py_compile Test/test_e2e_facture_libelle_parametres_isole.py` :
code 0. `npm run build` : **138 modules, 4,86 s**, code 0 ; avertissements
existants de taille du bundle et d'import statique/dynamique de xlsx.

### Échecs intermédiaires déclarés

- Première préparation : 1 failed, 19,82 s ; le test utilisait GET
  `/factures/{id}`, inexistant (405). Corrigé vers la liste réelle.
- Deuxième préparation : 1 failed, 21,19 s ; paramètre `annee` au lieu du
  paramètre obligatoire `exercice` de cette liste (422).
- Troisième préparation : 1 failed, 26,64 s ; la saisie commençait avant
  l'hydratation de la fiche société. Attente de la valeur réelle ajoutée.
- Quatrième préparation : 1 failed, 26,01 s ; le test cherchait le modèle
  dans Fiche société alors qu'il est exposé dans Fiscalité.
- Reproduction avant correction : 1 failed, 40,86 s ; aperçu figé réellement
  capturé, numéros/libellés/totaux/snapshots backend déjà contrôlés, puis attente
  erronée du titre d'écriture dans le tableau du journal qui affiche les libellés
  de lignes. Lecture correcte par CSV téléchargé, sans modification du journal.

## Procédure utilisateur et limites

1. Paramètres → Fiche société → Préfixe Factures : saisir le préfixe et enregistrer.
2. Pour changer également le texte précédant le numéro : Paramètres → Fiscalité
   → Format des libellés d'écritures → Facture de vente ; modifier le modèle,
   conserver `{numero}` si le numéro doit apparaître, puis enregistrer.
3. Créer et valider une nouvelle facture, puis la comptabiliser. Les réglages
   n'ont aucun effet rétroactif sur les pièces déjà comptabilisées/définitives.

La recette PostgreSQL/navigateur locale est automatisée sur données fictives.
La recette utilisateur sur son environnement reste à effectuer, sans réparation
automatique de ses libellés historiques. L'exemple ne prédit pas le prochain
numéro disponible. Le changement manuel d'exercice et les autres types de
documents ne sont pas exécutés dans ce nouveau scénario ciblé.
