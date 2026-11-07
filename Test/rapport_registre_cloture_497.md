# Lot497 — Registre des immobilisations stable pendant la clôture API

Deux courses sont reproduites sur PostgreSQL temporaire : une modification
du registre aboutit pendant le calcul de clôture ; inversement la clôture
aboutit alors qu'une modification n'est pas encore confirmée.
Avant correction :2échecs,29avertissements en31,25s.

Un service commun prend désormais un verrou transactionnel partagé pour les
mutations du registre, exclusif pour la clôture. Le périmètre est la société :
un plan peut concerner plusieurs exercices, et une création doit être protégée
même si le registre est vide. Les écritures de sociétés distinctes restent
indépendantes. Deux clôtures de la même société sont donc aussi sérialisées,
même si elles visent des exercices différents.

Le verrou est pris avant le calcul de clôture et les verrous d'exercice, puis
conservé jusqu'au commit/rollback. Toute mutation HTTP du module participe au
protocole, y compris création et assistants de réconciliation. Le lot annuel
appelé directement par le routeur de préparation de clôture est couvert aussi.
Les verrous par immobilisation495 et par dotation493 restent conservés.

Le conflit renvoie409 sans attendre et sans relance comptable automatique.
La consultation reste disponible. Aucune nouvelle migration, écriture
historique réécrite, règle de calcul ou obligation fiscale ajoutée.

## Tests exécutés

- Deux courses corrigées :2réussis,29avertissements en29,14s.
- Extension :15réussis,29avertissements en49,85s,0échec/erreur/ignoré.

Les deux ordres sont testés avec de vraies requêtes retenues par des verrous
de tables du seul laboratoire. La clôture aboutit après libération, avec
sources comptables originales conservées et FEC exportable. Le jeu fictif
contient capital1000, acquisition10000HT/TVA2000, dotation2000. Le résultat avant
impôt est-2000, la CM existante du laboratoire3000 est conservée, résultat
net-5000. Ce jeu ne valide pas le régime fiscal d'une entreprise réelle.

Onze chemins sont refusés sous verrou exclusif : création sans génération
d'écriture, modification, suppression, paiement, sortie, dotation individuelle,
lot annuel, bouton de préparation de clôture et trois assistants de
réconciliation. Les tables métier restent identiques ; les refus HTTP
modifiants conservent normalement leur trace d'audit. Les consultations restent
possibles, une autre société peut modifier son registre et clôturer. Une
création sur registre vide bloque la clôture ; un refus métier de clôture
libère le verrou et permet de reprendre les mutations.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_registre497_isole.py Test/test_restauration_journal098_isole.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_e2e_cloture_isole.py -ra
```

**62exécutions réussies,29avertissements en267.50s**,0échec/erreur/ignoré.
Les15cas497 sont regroupés avec les oracles495/493 conservés, les parcours Edge
d'acquisition, dégressif, cession/rebut et différée, vente/achat puis
validation/règlement/lettrage, clôture/à-nouveaux et les tests unitaires.
Une restauration froide098 est rejouée et l'ancien E2E de clôture sans098
est exécuté séparément : le même parcours existe dans deux configurations,
et62cas métier distincts ne sont pas revendiqués.

La restauration conserve74tables, quatre pièces, données/schéma/ACL/séquences
et FEC ; fonctions098 et refus409/reprise disponibles après copie, source
préservée et cibles nettoyées. Invariants finaux :0pièce déséquilibrée,
0montant non fini,0définitive sans numéro/date. Sources/fonctions/ACL inchangées
pendant les tests. Cinq Python compilés,98SQL et115guides intacts.

## Installation et limites

Installer ensemble `routers/immobilisations.py`, `routers/cloture.py` et
`services/immobilisations_verrou_service.py`, API arrêtée puis redémarrée.
Aucune migration supplémentaire ;098 après097 reste nécessaire pour les
protections natives Journal/clôture déjà livrées. Aucune base réelle utilisée.

Le protocole protège les mutations HTTP du registre et les appels internes
explicitement raccordés, face à la clôture API. Il ne protège pas un SQL
arbitraire, une clôture native qui ignore le protocole, tous les stocks ou
paramètres fiscaux. Les assistants de réconciliation participent désormais
au verrou de clôture, mais leur concurrence entre eux et avec les mutations
courantes par immobilisation reste à qualifier. Les contrôles existants
continuent de s'appliquer après la libération ; aucun gel historique permanent
supplémentaire du registre n'est introduit.

Frontend inchangé : pas de nouveau build Vite annoncé. Recette utilisateur,
installation réelle, production et point6 restent en attente. Les115 fichiers
de guide/recette et les98SQL antérieurs sont conservés.
