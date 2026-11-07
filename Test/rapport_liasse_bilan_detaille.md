# Bilan détaillé dans la liasse fiscale

Lot `LIASSE-BILAN-DETAILLE-20261008` (livraison 256), 8 octobre 2026.

## Résultat

La liasse live expose désormais `etats.bilan.detail.actif` et `passif`, produits par le helper existant `services.bilan_presentation.lignes_bilan_detaille`. Aucun nouveau classement comptable ni calcul fiscal n'est introduit. Les agrégats existants N/N-1 et les contrôles ne sont pas modifiés.

L'écran et les exports Excel/PDF de la liasse affichent les sous-postes déjà présents dans le bilan PDF autonome : terrains, constructions, installations, transport, mobilier et autres immobilisations, ainsi que les autres rubriques du référentiel existant. Les détails sont indentés et présentés pour mémoire ; ils ne sont pas ajoutés aux rubriques ou aux totaux. Si les amortissements d'une rubrique ne sont pas ventilés avec une source fiable, l'amortissement et le net de ses sous-postes restent absents, affichés « — » dans l'écran, sans montant inventé. Un N-1 indisponible reste absent.

Les archives anciennes dépourvues de `detail` gardent leur présentation agrégée, issue uniquement de leur snapshot. Aucune récupération du grand livre courant ni modification de l'archive n'est effectuée. Les prochaines archives captureront les détails disponibles lors de leur finalisation.

## Oracle fictif indépendant

Le jeu de test contient six immobilisations brutes : 1 000 + 2 000 + 3 000 + 4 000 + 5 000 + 6 000 = **21 000 MAD**. L'amortissement global de la rubrique est **300 MAD**, soit un net immobilisé de **20 700 MAD**. Stocks **7 000**, client **8 000** et banque **9 000** portent le total brut à **45 000**, le total net à **44 700**, équilibré avec un capital fictif de **44 700 MAD**. Chaque détail d'immobilisation conserve son brut exact mais aucun amortissement ni net n'est réparti arbitrairement. Aucun N-1 n'est créé dans cet oracle. Le test connexe 081 vérifie séparément un N-1 disponible de 75 MAD.

La recette connectée crée une société et un vrai client fictifs par API, rattache explicitement l'auxiliaire à la ligne 3421, puis crée et valide normalement l'écriture équilibrée. Elle utilise les comptes existants 2340 et 2380, sans ajouter de règle ou de compte au produit.

## Tests exécutés

Commande finale ciblée :

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_liasse_bilan_detaille_isole.py --tb=short
```

**3 réussis en 25,15 s**, aucun test ignoré : extraction d'un vrai PDF avec les six sous-postes, oracle des totaux et conservation de l'empreinte ; Node exécutant le véritable export Excel avec relecture XLSX et fallback ancien snapshot ; Edge → FastAPI → PostgreSQL nonce avec affichage, indentation réelle de 24 px et téléchargement/relecture Excel. Le test API vérifie également les agrégats et le contenu du PDF exporté.

Les trois fichiers connexes ont réellement été exécutés : `test_patch081_bilan_detaille.py`, `test_liasse_numerotation_interne.py` et `test_patch128_exports09a.py` : **16 réussis** lors des passages combinés. Ils couvrent notamment les totaux, N-1 absent et présent, la non-ventilation des dépréciations et les anciens exports. Le dernier passage combiné était de 18 réussis / 1 échec de fixture corrigé ensuite ; il n'est pas présenté comme une commande entièrement verte.

```text
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_archive_liasse_isole.py --tb=short
```

**1 réussi en 31,51 s** : finalisation connectée, exports, empreinte et immutabilité. Les dépréciations Pydantic et python_multipart existantes restent signalées.

```text
npm.cmd run build
hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile hisabpro-backend/services/liasse_service.py hisabpro-backend/services/liasse_pdf.py Test/test_liasse_bilan_detaille_isole.py
```

**Build OK en 9,67 s** et **compilation OK**. Avertissements existants : découpage xlsx et taille du bundle.

### Échecs intermédiaires conservés

La préparation du nouveau laboratoire a d'abord employé des comptes courts absents du plan (400), tenté un sous-compte sans parent actif (422), omis l'auxiliaire obligatoire de 3421 (422), puis utilisé le mauvais champ `type_tiers` au lieu de `type` lors de la création du client (422). Enfin l'oracle visuel attendait un espace comme séparateur de milliers alors que `fr-MA` dans Edge affiche `2.000,00`. Les fixtures ont été corrigées pour respecter les contrats réels et le format local ; aucun contrôle produit n'a été contourné et aucune correction du code applicatif n'a été nécessaire après ces échecs.

## Limites et fichiers

Aucun PostgreSQL réel, serveur utilisateur ou donnée comptable réelle n'a été modifié. Les tests PostgreSQL et navigateur concernent exclusivement des laboratoires temporaires isolés. Une recette utilisateur des données historiques reste nécessaire ; les anciennes archives restent intentionnellement agrégées. Cette livraison ne certifie aucune conformité officielle.

Différentiel : `hisabpro-backend/services/liasse_service.py`, `hisabpro-backend/services/liasse_pdf.py`, `src/pages/LiasseFiscale.jsx`, `src/pages/LiasseFiscale.module.css`, `Test/test_liasse_bilan_detaille_isole.py`, ce rapport. Le journal et le ZIP sont vérifiés par l'agent principal.
