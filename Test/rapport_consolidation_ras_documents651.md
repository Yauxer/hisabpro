# Consolidation des documents RAS et flux connexes —651

218cas distincts réussis en453.945s, zéro échec/erreur/ignoré. Schéma102 natif, LOGIN limité, témoins commerciaux/RAS et deux fichiers inchangés ;379sources applicatives SHA inchangés. Python compilé. Aucun produit modifié ; campagnes recouvrantes non additionnées.

Le banc regroupe les fonctions des campagnes RAS593 et facturation635,
la cohérence RAS/états/IS/lettrage, les documents647, l'oracle649 et les
gardes645/642. Une même fonction importée plusieurs fois est exécutée une
seule fois avec toutes ses variantes paramétrées. Aucun filtrage de résultat
ou test échoué exclu pour obtenir cette campagne.

Une seule application réelle et un schéma102 PostgreSQL jetable, LOGIN limité.
Deux sociétés liées avec une facture correspondante et une troisième société
avec capture RAS annulée et deux fichiers servent de témoins non vides.
Avant/après : factures, lignes, écritures, règlements, captures, contrepassations,
dossiers099, références et listes de fichiers strictement identiques ; suivi
des deux sociétés et registres RAS identiques. Les379fichiers applicatifs
surveillés conservent leurs SHA256 pendant toute la campagne.

Les218cas sont ceux de cette sélection de modules, pas une suite globale de
tous les tests du dépôt. Ils ne s'additionnent pas aux résultats des campagnes
645/647/649, qui se recouvrent. La première tentative a échoué au setup : le
banc ordonnait toutes les tables par `id`, alors que les détails099 utilisent
`capture_id`. Le classement canonique par contenu JSON corrige l'observation
du banc, sans changement de schéma, de contrôles ou de produit.

Commandes exécutées avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_consolidation_ras_documents651_isole.py --collect-only -q
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_consolidation_ras_documents651_isole.py -q -x
```

La campagne garantit les comportements testés, pas la qualification fiscale
des faits saisis. La recherche officielle parallèle a mis en évidence une
réserve du cahier649 : son scénario principal à1200TTC et une société vierge
ne documentent pas l'absence de l'exclusion des petites prestations. Ses
calculs comptables réussis ne suffisent pas à qualifier cette hypothèse.
**Révision653 obligatoire avant d'utiliser ce cahier comme recette principale :
montants relevés, aucun cumul mensuel inventé, calculs/documents/tests refaits.**
Les petites valeurs des tests de calcul déclaratif restent des vecteurs
arithmétiques ; elles ne constituent pas des dossiers fiscaux validés.

Aucune base utilisateur connectée ou modifiée, aucun SQL ou produit applicatif
modifié dans ce lot. Recette humaine, installation cible, déclaration et
production non validées ; RH/paie et point6 différés. Suite : corriger le jeu
documentaire en653, puis audit des sources/archives et cumul final655.
