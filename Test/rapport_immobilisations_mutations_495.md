# Lot495 — Plan, sorties et règlements d'immobilisations concurrents

Deux défauts sont reproduits sur PostgreSQL nonce et API réelle : une double
sortie reste possible lorsque les dotations existent déjà ; une modification
du plan peut être confirmée pendant une génération, ou inversement. Cela peut
laisser une durée10ans avec une dotation2000 calculée sur l'ancien plan5ans.

Les mutations courantes prennent désormais un verrou transactionnel par
société/immobilisation avant la lecture du registre. Le conflit renvoie409
sans attente, et le verrou est libéré au commit/rollback. Sont concernés :
modification, suppression, paiement d'acquisition, dotation individuelle,
sortie, encaissement de cession et chaque immobilisation du lot annuel.
Le bouton de préparation de clôture utilise ce même lot.

Le lot parcourt les identifiants dans un ordre explicite, recharge le plan
après verrou puis revérifie ses critères de période. Le rafraîchissement
remplace aussi les valeurs périmées déjà présentes dans le cache ORM.
Le verrou493 par dotation et son contrôle de référence restent conservés.
Aucune écriture historique, formule d'amortissement ni règle fiscale modifiée.

## Tests exécutés

- Avant correction :1échec en30,25s sur double rebut, puis6échecs/3désélectionnés
  en33,02s sur génération/modification du plan, dans les deux sens et les trois
  chemins unité/lot/clôture.
- Premier passage corrigé :9réussis,29avertissements en34,94s.
- Extension14cas :14réussis,29avertissements en43,35s, aucun échec/erreur/ignoré.

Les courses utilisent uniquement des verrous de tables du laboratoire pour
retenir une requête réelle. Les oracles vérifient une seule sortie/cession,
un seul paiement/encaissement, les sources originales intactes, refus409 et
rejeu refusé ou autorisé selon le statut. Après passage confirmé de5 à10ans,
la génération utilise1000MAD au lieu de2000 sur un matériel fictif10000MAD.

Sont également contrôlés : consultation disponible pendant le conflit,
indépendance des sociétés et immobilisations, refus404 sur objet étranger,
libération après erreur métier400, annulation intégrale d'un lot lorsqu'un
conflit survient sur sa seconde immobilisation, puis reprise2dotations4000MAD.
Un test PG/Session réel confirme le rafraîchissement d'un plan préchargé.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_immo495_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py -ra
```

**46tests réussis,29avertissements en195.56s**,0échec/erreur/ignoré. Les14cas495
sont regroupés avec les oracles493 conservés, les parcours Edge d'acquisition,
dégressif, cession/rebut et différée, vente/achat puis validation/règlement/lettrage,
clôture/à-nouveaux, les tests unitaires et une restauration froide098 sur backend
final. Les passages successifs ne sont pas additionnés.

La restauration conserve74tables, quatre pièces, schéma/données/ACL/séquences
et FEC ; les fonctions098 et le refus409/reprise sont disponibles après copie.
Source préservée, cibles nettoyées. Invariants finaux :0pièce déséquilibrée,
0montant non fini,0définitive sans numéro/date. Sources/fonctions/ACL restent
inchangées pendant les tests. Trois Python compilés,98SQL et115guides intacts.

## Installation et limites

Installer `hisabpro-backend/routers/immobilisations.py` et redémarrer l'API.
Aucune migration supplémentaire.098 après097 reste nécessaire pour les
protections Journal/clôture déjà livrées. Aucune base réelle n'est utilisée.

Le protocole protège les mutations courantes API qui le respectent. Il ne
verrouille pas une insertion ou modification SQL arbitraire, les assistants
de réconciliation historique ni tous les calculs/paramètres de la clôture.
La stabilité globale du registre pendant une clôture reste à qualifier.
Aucun doublon ni plan historique n'est réparé automatiquement.

Frontend inchangé : aucun nouveau build Vite annoncé. La recette utilisateur,
l'installation réelle, la production et point6 restent en attente. Les115
fichiers guide/recette et les scripts SQL antérieurs restent conservés.
