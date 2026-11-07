# Avoirs : société de calcul de la RAS — lot 309

Reprise du10 octobre2026, suite à la globale300. Correction technique minimale, sans règle fiscale ni migration nouvelle.

## Cause et reproduction

`_credit_excedentaire_avoir(db, avoir)` appelait `montant_actif(db, societe_id, facture.id)` alors que la variable `societe_id` n'existe pas dans cette fonction. La lecture/création d'avoirs provoquait ainsi une erreur serveur. La société de la facture source est déjà contrôlée par `avoir.societe_id` dans toutes les requêtes précédentes de cette fonction.

La régression ajoutée appelle la vraie API sur un cluster PostgreSQL nonce exclusivement. Avant correction, session57990 :1 échec,3 désélectionnés,36,76s ; création d'avoir HTTP500 au lieu201. La première correction remplace uniquement l'identifiant fautif par `avoir.societe_id` dans l'appel au service de captures actives.

La vérification d'isolation a ensuite révélé une seconde anomalie : `utiliser_credit_avoir` combine `joinedload(Avoir.lignes)` et `FOR UPDATE` non ciblé. PostgreSQL refuse de verrouiller le côté nullable d'une jointure externe, avant même de pouvoir renvoyer404 pour un avoir d'une autre société. Session92005 fournit la vraie trace `FOR UPDATE cannot be applied to the nullable side of an outer join`. Le second correctif minimal précise `with_for_update(of=models.Avoir)` : le verrou de l'avoir est conservé, les lignes jointes ne font plus l'objet de ce verrou invalide. Aucun calcul, taux, migration ou état historique n'est modifié.

## Oracles et protections vérifiées

Chaque scénario crée une société fictive, un vrai tiers et une facture vente ou achat : deux unités de service à500 HT, TVA20% explicitement saisie, soit1000 HT/200 TVA/1200 TTC. RAS estimée100, règlement bancaire1100 comptabilisé et validé. Avoir d'une unité :500 HT/100 TVA/600 TTC.

- Sans capture effective ni flag historique : restant source100, l'avoir absorbe100 ; crédit excédentaire et disponible500. L'estimation100 ne vaut pas paiement.
- Avec capture explicitement déclarée100 sur le règlement, migration083 appliquée seulement au cluster nonce et OD validée : restant source0 ; crédit excédentaire et disponible600.
- Annulation du règlement capturé : cash et capture sont contrepassés, les originaux validés restent identiques ; l'avoir600 est entièrement absorbé et son disponible revient à0.
- Les deux sens vente/achat sont exercés. La création puis la lecture de l'avoir ne modifient aucune écriture ni ligne existante, toutes les colonnes étant photographiées.
- Un compte authentifié d'une seconde société ne voit aucun avoir de la première ; consultation des factures imputables et tentative d'utilisation renvoient404. Aucun crédit de capture d'une autre société n'est agrégé.
- Sans capture, l'avoir est ensuite comptabilisé et un remboursement fictif100 est enregistré par l'API existante : crédit excédentaire500, utilisé100, disponible400. Ce cas positif exerce réellement la route verrouillée corrigée dans les deux sens client/fournisseur.

Le test concerne le crédit calculé et un usage technique du flux existant. Il ne présente pas la conformité réglementaire d'un remboursement, une attestation fiscale ni une nouvelle qualification TVA comme validées automatiquement.

## Exécution

Toutes les commandes utilisent `PYTHON_DOTENV_DISABLED=1`, le venv du dépôt et le runner isolé ; aucun PostgreSQL utilisateur n'est contacté.

```powershell
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_avoirs_ras_societe_postgres.py -k 'False and vente' --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_avoirs_ras_societe_postgres.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -X utf8 Test/run_unit_tests.py Test/test_fact6_avoirs_retours.py Test/test_factG_acomptes_avoirs.py Test/test_session132_operations_postgres.py Test/test_session133_cloture_postgres.py --tb=short -x
& 'hisabpro-backend/.venv/Scripts/python.exe' -m py_compile hisabpro-backend/avoirs.py Test/test_avoirs_ras_societe_postgres.py
```

- Avant correction57990 :1 échec/3 désélectionnés,36,76s, sortie1, HTTP500 reproduit.
- Première relance79337 :1 échec,21,56s, sortie1. Création HTTP201 et premier oracle500 satisfaits ; la fixture omettait le paramètre obligatoire `exercice` au GET des avoirs, qui renvoyait422. Correction du test uniquement, sans changement applicatif supplémentaire.
- Connexes61002 :29 réussis,25 avertissements,39,77s, sortie0.
- Session73994 :1 échec,26,41s, sortie1 ; la tentative d'utilisation par une autre société renvoie500 au lieu404.
- Session92005 :1 échec/3 désélectionnés,20,69s, sortie1 ; le journal API conservé dans la capture pytest prouve le verrou invalide sur jointure externe.
- Session74819 :1 échec,21,15s, sortie1 ; le refus inter-société404 est désormais satisfait. Le cas positif révélait un prérequis de fixture manquant : la facture source n'était pas encore comptabilisée, d'où le refus métier409 de comptabiliser son avoir. La fixture comptabilise/valide maintenant cette source par l'API, avec qualification TVA achat explicitement charge/100%.
- Relance finale55166 des cinq fichiers ci-dessus après les deux corrections et la préparation complète :33 réussis,25 avertissements,58,90s, sortie0. Les quatre scénarios nouveaux et les29 cas connexes sont tous exécutés après la dernière version applicative.
- Compilation des deux fichiers Python après leur dernière modification : sortie0.

La globale300 et la relance navigateur des parcours affectés sont consignées par l'agent principal dans leurs lots propres. Résultat rapporté par le principal : session78572,8 E2E réussis/25 avertissements/166,68s, sortie0, après le correctif d'identifiant mais **avant celui du verrou d'utilisation** ; ce résultat ne valide donc pas la seconde version complète. Ce rapport distingue ces validations des commandes directement exécutées pour309.
