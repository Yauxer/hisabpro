# Paramètres TVA clôturés — protection SQL 094

La migration additive `094_protection_parametres_tva_clotures.sql`, à appliquer
après093 par le propriétaire, refuse INSERT/UPDATE/DELETE sur les paramètres
d'un exercice dont le statut clôturé ou la trace de clôture est visible. Un
déplacement de ligne contrôle l'ancien et le nouveau périmètre société/exercice.
Les valeurs historiques restent inchangées ; aucun champ ni taux ajouté.

Deux fonctions invoker et un trigger sont créés. Le rôle `hisabpro` reçoit
explicitement EXECUTE sur ces deux seules fonctions nouvelles, sans nouveau
droit sur les tables/colonnes. Il n'y a pas d'élévation SECURITY DEFINER.
Les anciens droits sont conservés et le rejeu laisse données, schéma et ACL
stables. Aucun PostgreSQL utilisateur n'est utilisé.

## Tests exécutés sur la version finale

**22 réussis, zéro échec/erreur/ignoré, 29 avertissements, 78,05 s, code 0** :
douze cas de données (onze originaux plus trace de clôture seule) et un contrôle
de fonctions/permissions, ainsi que les neuf cas existants d'API, UI TVA,
clôture et concurrence réutilisés sans affaiblir leurs assertions. Runtime
limité et propriétaire sont testés. Les refus23514 identifient la contrainte
`ck_tva_parametres_exercice_ouvert` et préservent toutes les tables métier.
Les deux témoins ouverts restent modifiables. Le rôle applicatif conserve ses
refus d'identité/suppression/SETVAL existants.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_protection_sql_tva_cloture_isole.py -ra
```

Restauration froide distincte : **un réussi, 68,24 s, 29 avertissements**, code0.
Le scénario452 est réutilisé avec ses assertions inchangées, après préparation
091 puis092/093/094. Deux clusters nonce, source arrêtée avant dump et cible
vide marquée : 73tables, schéma, données, séquences et ACL identiques avant
reprise API, quatre pièces et FEC conservés, source préservée. Les droits
comptent1205entrées de relations,29colonnes,146fonctions,4sur le schéma,0défaut.
Les146 sont des entrées de privilèges, pas un nombre de fonctions.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_restauration_tva094_isole.py -ra
```

L'empreinte094 finale est
`6d4c3e90425f6793e5fd895714d84d6e1dc0d27824c7bd23c97439bfaf3679a5` :
elle correspond aux deux preuves locales de tests et de restauration. Les deux
tests Python sont compilés avant livraison. Aucun frontend modifié dans ce lot.

## Reproduction et incidents du banc

La première série sans094 a obtenu9échecs/2réussites/9désélections en39,41s.
Trois essais comportaient un INSERT incomplet : ils rencontraient NOTNULL avant
la règle visée. La première relance094 a obtenu10réussites/1échec de ce prérequis
en41,47s ; les deux INSERTs ont alors reçu crédit/prorata explicites.

Les mêmes oracles corrigés, exécutés sur un cluster093 neuf sans094, ont
réellement reproduit **neuf contournements acceptés**, avec2témoins ouverts
réussis et9connexes désélectionnés en40,90s. Sous094, les11cibles ont ensuite
réussi en41,81s. Les20connexes ont réussi69,56s ; trace seule1réussi27,74s et
première restauration1réussi65,67s. L'EXECUTE explicite des nouvelles fonctions
a ensuite été ajouté avant livraison : les résultats finaux22+restauration
ci-dessus qualifient cette version. Aucun résultat intermédiaire ne les remplace.

## Portée et limites

094 contrôle une clôture visible dans le snapshot SQL de l'opération. Il ne
sérialise pas à lui seul du SQL direct concurrent avec une clôture. Le verrou
API477 reste qualifié sur une ligne d'exercice existante, dans les deux ordres.
Le calcul complet de clôture préalable, tous les modes d'isolation, les autres
propriétaires/rôles et les transactions SQL directes concurrentes restent à
qualifier. Les réparations historiques éventuelles doivent rester distinctes,
autorisées et tracées ; aucun mécanisme de contournement n'est ajouté ici.

La qualification143 de478 concerne le runtime093 et les sources produit alors
figées. Elle n'est pas présentée comme une globale sous094 ; les22cas et la
restauration qualifient ce complément. Migrations092/093/094 réelles, recette
utilisateur et production restent à effectuer. Les115guides/recette et point6
restent inchangés.
