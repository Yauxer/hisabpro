# RAS estimée et solde — lot 291, 9 octobre 2026

La RAS portée sur une facture reste une estimation documentaire. Elle ne réduit plus son solde et ne crée plus automatiquement une OD entière lors du premier nouveau règlement. Les factures et PDF conservent leur estimation ; aucune qualification fiscale ou règle de prorata nouvelle n'est introduite.

## Contrat et compatibilité

- `/api/factures/{id}/reglements` : `montant_ras` désigne désormais la RAS imputée ; `montant_ras_estime` et `montant_ras_impute` explicitent les deux notions. `ras_origine` vaut `aucune` ou `historique_comptabilisee`.
- Le flag historique `ras_comptabilisee=True` conserve son effet existant et les OD déjà présentes. Il n'est pas interprété comme une attestation de retenue fiscale. Aucun backfill ni recalcul de l'historique n'est exécuté.
- Recouvrement et crédit disponible des avoirs utilisent la même distinction. Le calcul pur exige explicitement le flag historique ; le test historique de 100 MAD le fournit.
- Pour une RAS historique invalide, la lecture règlement conserve son diagnostic et ses montants indéterminables à `null`. Le recouvrement retourne également une ligne diagnostiquée, sans faux zéro ; le résumé du domaine concerné porte `calcul_incomplet=true`, des totaux `null`, et la position nette devient `null`.
- Dans le suivi des délais, une RAS historique possède un événement uniquement lorsque l'OD est retrouvée exactement et sans ambiguïté : société, référence, libellé, montant, deux lignes, compte collectif et tiers source, contrepartie, absence de contrepassation. La date retenue est la date comptable de l'OD. L'échéance de facture n'est jamais substituée à cette date ; une recherche indéterminable produit un diagnostic.
- Aucun modèle, aucune migration, aucun taux fiscal nouveau. ETIC127 et annulation des OD historiques restent inchangés.

## Preuve et tests réellement exécutés

Commande commune :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_estimation_solde_postgres.py Test/test_fact7_recouvrement.py Test/test_ras_lecture_conservation.py Test/test_patch127_etic_ras_recoupement.py Test/test_factD_reglements_delais.py Test/test_factF_delais_paiement.py
```

Avant correction : session34841, **1 échec, 25 avertissements, 34,64 s**. Facture de 1 000 HT + 200 TVA sans paiement et RAS estimée100 : l'API retournait un dû1100, attendu1200.

Après première correction normale : session46277, **2 réussis, 25 avertissements, 22,45 s**.

Renforcement des fixtures, erreurs de préparation consignées :

- Session94431 : **42 réussis, 2 échoués, 25 avertissements, 58,68 s**. Le helper de test tentait de décoder JSON sur une suppression réussie204 vide ; corrigé par assertion du statut.
- Session75643 : **42 réussis, 2 échoués, 25 avertissements, 58,63 s**. Une tentative de préparation NaN sur facture validée fut refusée par le trigger ; aucun trigger désactivé. La fixture a été remplacée par une pièce historique distincte avant sa validation.
- Session83533 : **42 réussis, 2 échoués, 25 avertissements, 60,85 s**. Cette préparation omettait le numéro définitif exigé à la validation ; ajouté exclusivement au document fictif du cluster nonce.
- Session36841, ciblés finaux `--tb=short -x` : **2 réussis, 25 avertissements, 22,68 s**.

Les deux scénarios API réels couvrent vente et achat : dû1200 sans paiement, paiement non comptabilisé300 donnant900, paiement comptabilisé1100 donnant100 sans OD automatique ; pièce historique distincte avec flag préalable et OD100 conservée donnant0 ; contrôle de la date OD puis refus d'un compte collectif incorrect ; pièce historique NaN distincte, lecture200 avec `null` et diagnostic, résumé indéterminable. Les snapshots des écritures sont conservés lors des lectures.

Connexes supplémentaires :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_fact6_avoirs_retours.py Test/test_factG_acomptes_avoirs.py Test/test_factH_audit_final_facturation.py Test/test_patch02c_reglement_date_effective.py Test/test_patch075_journal_apres_reglement.py
```

**33 réussis, 4,23 s, sortie0**. Compilation Python des huit fichiers Python concernés : **sortie0**.

Confirmation finale des six modules : session74951, **44 réussis, 25 avertissements, 55,06 s, sortie0**.

Consommateurs relances : guards explicites409 sur solde indéterminable pour une création ou une nouvelle promesse, avec diagnostic, avant toute mutation. Une simple correction de commentaire conserve le flux historique. Commande supplémentaire `Test/run_unit_tests.py Test/test_ras_estimation_solde_postgres.py Test/test_recouvrement_promesse_montants.py --tb=short` : session32329, **16 réussis, 25 avertissements, 22,49 s, sortie0**. Les deux refus POST/PATCH de la fixture NaN conservent le nombre des relances et le montant promis initial. Compilation étendue au routeur recouvrement : sortie0.

## Limites et suite

Les tests API utilisent exclusivement PostgreSQL nonce isolé et des données fictives ; aucune connexion au PostgreSQL utilisateur. La recette navigateur des trois écrans est effectuée dans le lot292 et n'est pas revendiquée ici. Les interfaces consommant les résumés historiques indéterminables doivent afficher le diagnostic et ne pas présenter `null` comme zéro.

Audit des consommateurs complémentaires : `services/balance_pdf_service.py` transforme encore `reste_du=null` en zéro dans son filtre de balance âgée ; `services/dashboard_service.py` transforme encore les résumés indéterminables en zéros pour ses indicateurs. Ces deux limites historiques sont signalées au principal pour un lot distinct ou une extension explicitement consignée ; aucun correctif hors périmètre n'est présenté comme exécuté ici.

La saisie d'une RAS effectivement opérée, partielle et justifiée par règlement, reste un flux distinct à développer dans le lot293 ; ce lot291 ne crée aucune capture. La détermination du régime applicable et les justificatifs fiscaux restent à vérifier humainement et auprès des sources officielles.
