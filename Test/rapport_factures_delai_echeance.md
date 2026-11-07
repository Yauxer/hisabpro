# Délai de paiement et échéance

Lot `FACTURES-DELAI-ECHEANCE-20261008`, 7 octobre UTC / 8 octobre 2026 Europe/Paris.

## Analyse et correction

À la création, une échéance saisie manuellement empêchait le recalcul lorsque le délai était ensuite explicitement changé. À l’édition, le délai et l’échéance étaient deux états indépendants, sans recalcul.

Changer explicitement le délai de paiement recalcule maintenant l’échéance depuis la date de facture, pour la création et l’édition. Zéro signifie bien la date de facture. Le bouton reprenant le délai du tiers réactive aussi le calcul. Le helper `dateEcheance` déjà présent dans le composant est utilisé par les deux formulaires, avec conversion en date locale ISO, sans décalage UTC.

Une saisie manuelle d’échéance reste prioritaire si l’utilisateur change seulement la date de facture ou le tiers. Elle cesse d’être prioritaire au prochain changement explicite du délai. En mode calculé, un changement de date ou de délai du tiers actualise l’échéance. À l’édition, l’échéance enregistrée est conservée au montage, sans réinterpréter une donnée historique comme automatiquement calculée ; un message explique que modifier le délai la recalculera. Ces champs sont désactivés pour les factures définitives validées. Aucun champ obligatoire, règle fiscale, backend, migration ou pièce validée n’a été ajouté ou modifié.

## Oracle et tests réellement exécutés

Deux E2E Edge connectés à FastAPI réel et PostgreSQL éphémère protégé testent les factures datées du **31 janvier** et du **28 février**. L’oracle indépendant utilise `datetime.timedelta`, et non le helper JavaScript de l’application.

Pour 2026, 31 janvier + 30 jours = 2 mars ; + 60 jours = 1er avril ; 28 février + 30 jours = 30 mars ; + 60 jours = 29 avril. Les tests contrôlent également les changements de date, puis les délais 30, 0 et 60 sur ces nouvelles dates. Ils sélectionnent réellement un client à 60 jours puis un client comptant, vérifient le recalcul automatique, saisissent une échéance manuelle et contrôlent sa conservation lors d’un changement de date et de tiers. La modification explicite du délai la recalcule.

Un brouillon est créé dans l’interface avec POST réel, puis édité avec PATCH réel. L’édition conserve initialement l’échéance enregistrée, préserve une nouvelle échéance manuelle après changement de date, puis recalcule pour 60, 30 et 0 jours. La lecture API finale confirme délai zéro et date de facture = échéance, sans validation ni génération d’écriture. Aucun échec JavaScript ni HTTP 500 n’est observé.

- `Test/run_unit_tests.py Test/test_e2e_factures_delai_echeance_isole.py` : première exécution **2 réussis en 32,66 s** ; après réutilisation du helper existant, exécution finale **2 réussis en 32,83 s**.
- `Test/run_unit_tests.py Test/test_e2e_ras_editeur_diagnostic_isole.py Test/test_e2e_facturation_isole.py` : **5 réussis en 67,29 s**. Conservation du diagnostic RAS et du choix explicite, pièce historique validée protégée, taux existant 7 %, cycles vente/achat avec validation, règlements et lettrage.
- Build final `npm run build` : **OK**, 139 modules, 4,69 s. Premier build également OK en 7,10 s. Avertissements XLSX et taille du bundle déjà connus.
- `python -m py_compile Test/test_e2e_factures_delai_echeance_isole.py` : **OK**.

**Aucun échec intermédiaire dans ce lot.** Aucun PostgreSQL réel de l’utilisateur n’a été utilisé. La recette sur ses données et conditions contractuelles réelles reste à effectuer ; le présent lot ne répare aucune échéance historique.

## Fichiers différentiels et suite

- `src/pages/Factures.jsx`
- `Test/test_e2e_factures_delai_echeance_isole.py`
- `Test/rapport_factures_delai_echeance.md`

Journal et ZIP vérifié assurés par l’agent principal. Prochaine étape indépendante proposée : poursuivre la checklist commerciale à partir de sa matrice, en conservant les validations déjà exécutées.
