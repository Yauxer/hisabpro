# Annulation d'une RAS historique — lot 308

10 octobre 2026. Correction technique de conservation de la piste d'audit, sans taux fiscal, migration ni qualification réglementaire nouvelle.

## Anomalie reproduite avant correction

L'annulation du dernier règlement d'une facture portant `ras_comptabilisee=true` cherchait librement la première OD de RAS, puis effaçait le flag même si aucune OD n'était retrouvée. Une situation ambiguë pouvait donc contrepasser une seule des OD candidates et présenter ensuite une imputation historique nulle.

- Session93934 :2 échecs,5 désélectionnés,16,15s. Le cas OD absente a réellement retourné200 au lieu409 ; le cas double a échoué durant sa préparation, car les snapshots auxiliaires de la fixture n'étaient pas encore renseignés. Ce second résultat ne prouvait pas l'anomalie métier.
- Après préparation des lignes via le helper auxiliaire existant, session9943 :2 échecs,5 désélectionnés,15,77s. **Les deux cas absente et double retournent200 au lieu409**, sur l'API réelle connectée au PostgreSQL nonce.

Les données historiques fictives sont préparées exclusivement dans le cluster isolé : flag de facture renseigné avant validation, OD et règlement ensuite validés normalement. Aucune protection de pièce définitive n'est désactivée.

## Correction minimale

`resoudre_od_ras_historique` reprend les contrôles déjà appliqués au calcul de date : société, référence, libellé exact, journal OD, source règlement, unicité, absence de contrepassation, deux lignes, montant exact et vrai collectif/tiers. Il retourne l'OD certaine ou `None`. Le wrapper `date_od_ras_historique` conserve son contrat et utilise désormais le même résolveur.

L'annulation du dernier règlement actif verrouille la facture et contrôle cette OD **avant toute mutation**. L'absence, l'ambiguïté, un montant incorrect ou une contrepassation existante provoquent409. Les snapshots de facture, règlement et toutes les colonnes des écritures/lignes sont comparés pour vérifier l'absence de mutation.

Quand une OD exacte unique est trouvée, l'annulation contrepassera l'écriture de trésorerie et cette OD, puis désactivera le flag historique dans la même transaction. Les originaux validés restent inchangés. Si un autre règlement actif demeure, l'OD historique entière reste imputée et n'est pas contrepassée. Le flux de captures explicites du lot293 conserve ses liens, annulations et règles propres.

## Jeu de données et oracles

- Facture fictive1000 HT +200 TVA =1200 TTC ; taux d'estimation explicitement saisi10%, historique déclaré100.
- Règlement unique1100 : avant annulation le reliquat est0. Après une annulation déterminable, seules deux nouvelles écritures apparaissent, cash1100 et RAS100 ; le reliquat redevient1200.
- Cas positifs vente et achat : OD de RAS inversée, débit = crédit =100 ; originaux validés identiques ; rejeu d'annulation sans écriture supplémentaire.
- Cas négatifs : aucune OD, deux OD exactes, OD équilibrée99 au lieu100, OD déjà contrepassée. Refus409 et snapshots avant/après identiques.
- Deux règlements600 et500, RAS historique100 : annuler600 laisse500 +100 imputés, donc reliquat600. Une seule contrepassation cash est créée, le flag reste vrai et l'OD de RAS n'est pas contrepassée.

Ces chiffres servent uniquement d'oracle de test technique ; aucune attestation ni règle fiscale automatique n'est revendiquée.

## Commandes et résultats exécutés

Environnement `PYTHON_DOTENV_DISABLED=1`, aucun `.env` utilisateur chargé :

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_historique_annulation_postgres.py -k 'absente or double' --tb=short
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_historique_annulation_postgres.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_ras_capture_reglement_postgres.py Test/test_ras_estimation_solde_postgres.py Test/test_patch127_etic_ras_recoupement.py Test/test_e2e_reglement_edition_isole.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -m py_compile hisabpro-backend/routers/commercial.py hisabpro-backend/services/ras_paiement_service.py Test/test_ras_historique_annulation_postgres.py
```

- Session25470 :7 réussis,25 avertissements,20,25s, sortie0, après correction.
- Compilation des trois fichiers Python modifiés/ajoutés : sortie0.
- Connexes session93230 :30 réussis,25 avertissements,71,90s, sortie0. Captures explicites293, séparation estimation/imputation291, ETIC127 et édition/annulation de règlements.

Rectificatif documentaire du lot293 : la commande23483, correctement reproduite dans son rapport, énumérait **sept modules**, contrairement au message de coordination mentionnant huit. Son résultat42 réussis/100,72s reste inchangé ; aucun test supplémentaire n'est attribué à cette commande.

## Limites et déploiement

PostgreSQL réel utilisateur jamais contacté ; aucune donnée historique réelle réparée. L'absence ou l'ambiguïté doit être examinée par un opérateur avec justificatifs, sans créer automatiquement une OD pour débloquer l'annulation. La nouvelle garde conserve volontairement le refus d'une piste historique déjà contrepassée, au lieu d'effacer silencieusement son flag. Aucun nouveau comportement réglementaire n'est validé par ces tests. La recette complète et les sauvegardes du lot293 restent consignées dans leurs lots distincts.
