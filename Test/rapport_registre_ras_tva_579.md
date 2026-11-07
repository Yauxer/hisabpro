# Registre interne des retenues TVA — lot579

## Comportement livré

Dans Fiscalité → Déclaration TVA, le registre annuel reste consultable même
lorsque le calcul de déclaration est bloqué par une capture TVA guidée.
Il sépare les retenues opérées sur achats des retenues subies sur ventes,
sans compensation entre elles. Les captures de paiements de l'année sont
ventilées entre déclarées, actives, actives avec OD validée et annulées.
Les annulations intervenues dans l'année sont également présentées séparément.
Les statuts sont ceux à la consultation, pas une reconstitution fiscale passée.

Seules les captures guidées adossées à099 sont couvertes : les captures libres
et les retenues historiques ne sont pas assimilées à des données qualifiées.
Le mois prévu est issu du calcul conservé ; il ne prouve aucun versement.
Ce registre interne ne calcule ni crédit imputable, ni reversement ni déclaration
officielle. L'absence de099 est signalée sans faux total nul ni export disponible.

Les trois rôles connectés peuvent lire et télécharger l'année entière en CSV,
Excel et PDF. Les pièces paginées à l'écran restent toutes dans l'export.
Logo de la société dans les documents Excel et PDF ; protection des chaînes
contre les formules CSV/Excel et maintien des gros montants au centime exact.

La lecture utilise une seule connexion PostgreSQL RO/REPEATABLE READ, y compris
en cas de validation concurrente. L'export exige l'empreinte de l'état affiché,
liée à la société, son identité/logo et ses sources ; si elles changent,
l'utilisateur doit actualiser. Aucune écriture métier lors des lectures/exports.

## Tests réellement exécutés ici le18/10/2026

- Première recette intégrée : 8 réussis, 3 échoués, 29 avertissements,91,79s.
  Les trois téléchargements navigateur avaient un nom `export.bin` : l'en-tête
  Content-Disposition n'était pas exposé au navigateur. Correction sur ces
  réponses uniquement, selon le modèle des exports de ventes existants.
- Après correction :12 réussis,29 avertissements,93,37s.
- Livraison :13 réussis,29 avertissements,95,63s, code0. Sept tests API natifs,
  quatre tests Edge et deux tests purs d'exports. Commande :
  `python -X utf8 Test/run_unit_tests.py Test/test_ras_tva_registre_isole.py Test/test_e2e_ras_tva_registre_isole.py Test/test_ras_tva_registre_precision.py -ra`.
- Absence099 :2 tests Edge réussis,29 avertissements,30,10s, code0 ; fichier
  `Test/test_e2e_ras_tva_capture_sans099_isole.py` sur l'ancienne fixture isolée.
- `npm run build` : réussi,5,76s ; avertissement existant sur les gros chunks.
- PDF réel et capture mobile inspectés. Le test multipage contrôle60 pièces,
  la répétition des en-têtes, les références longues et les limites de page.

Les tests natifs utilisent exclusivement des clusters PostgreSQL jetables
protégés par nonce. Ils couvrent la séparation société/année, les droits,
l'absence d'authentification, les annulations, l'obsolescence des exports,
PNG/JPEG, les montants à grande précision et la cohérence concurrente.
Les avertissements concernent la configuration Pydantic existante et anyio.

## Limites et suite

Aucune nouvelle migration dans579, aucun changement de main.py ou models.py.
099 reste une installation additive manuelle à prévoir sur l'environnement cible,
sans intervention de cette session sur le PostgreSQL réel. La recette humaine,
le paramétrage comptable réel et la déclaration fiscale restent à valider.
Suite : consolidation des tests et vérification des mêmes lectures après
restauration native, puis livraison cumulative571+.
