# Conversion BL/BR — prix historiques et commit, lot343

## Défauts réellement reproduits

La conversion BL/BR vers facture utilisait `prix_article or 0` lorsque le
prix du bon puis celui du BC ne fournissaient pas de prix non nul. Un prix
article historique NULL créait alors un brouillon de montant0. NaN/+Inf/-Inf
dans un prix sélectionné provoquaient une erreur500 de validation de réponse.
Un prix individuellement fini pouvait aussi produire un montant non fini,
par multiplication ou addition de plusieurs lignes.

Les photographies SQL du PostgreSQL nonce montrent effectivement la
persistance du brouillon, de ses lignes et du lien `facture_id` du bon après
une réponse200 à prixNULL, mais aussi après500 sur un dépassement de montant.
Aucune donnée de l’installation utilisateur n’a été consultée ou réparée.

## Correction minimale

Dans `convertir_bl_en_facture`, la source article n’est qualifiée que si le
fallback existant la requiert. Le validateur numérique partagé est utilisé
avant la conversion en float ; le prix effectivement sélectionné doit être
fini. Un prix réellement0 reste0. Un prix explicite du bon reste prioritaire
et n’est pas bloqué par un prix articleNULL inutilisé. Les priorités BC/bon/
article et les formules existantes ne sont pas modifiées.

Les totaux HT/TVA/TTC sont contrôlés avant le commit. Un prix nécessaire
inconnu/non fini ou un montant non représentable provoque409 et rollback de
l’ensemble du brouillon, de ses lignes et des liens logistiques. La sélection
partielle qualifie uniquement les lignes effectivement facturées.

## Preuves exécutées par le principal

Runner avec `PYTHON_DOTENV_DISABLED=1`, application/API réelles et PostgreSQL
éphémère vérifié par URL/dossier/nonce. Aucun PostgreSQL réel. Les fixtures
ne sont pas des tests de concurrence ou des réparations historiques.

- Baseline22cas :14échecs,8réussites,25avertissements,51,58s,code1.
  XML distinct `conversion343_avant.xml` :22/14/0/0,51,534s.
- Baseline complémentaire :6échecs,2réussites,18désélectionnés,
 25avertissements,31,10s,code1. XML distinct :8/6/0/0,31,021s.
  Les huit cas exécutés incluent quatre dépassements, deux prixNULL et
  deux témoins à prix explicite. Photos SQL avant/après et journaux500
  authentiques conservés dans `.codex-tests/conversion343_*`.
- Première vérification après correction :26réussis,25avertissements,
 53,89s,code0 ; XML26/0/0/0,53,880s. Cette version du test est distincte
  de la sélection finale étendue.
- Compilation des trois fichiers Python modifiés/ajoutés :code0.

Deux preuves intermédiaires échouées restent conservées :67réussis/2échecs,
169,40s, puis deux Edge seuls échoués68,70s. La préparation des nouveaux
tests navigateur omettait d’abord le paramètre d’exercice obligatoire du
GET des BR, puis la transition à l’état reçu nécessaire au bouton Facturer.
Les fixtures ont été corrigées selon ces prérequis réels : transitions API
expédié puis livré avec assertions200 avant injection du prixNULL. Aucun
sélecteur, délai ou garde métier n’a été assoupli ; application inchangée.

**Sélection finale :69réussis,0échec/erreur/ignoré,25avertissements,
240,15s,code0.** XML distinct `conversion343_verifie.xml` relu. Elle comprend
30nouveaux casAPI PGnonce,13casBR341,19contrôles structurels de facturation
et **sept Edge connectés**, dont deux nouveaux refus bureau/mobile et cinq
cycles achats/vente positifs jusqu’au règlement/lettrage ou retourBR.

Les nouveaux Edge vérifient réellement409, l’alerte lisible, le maintien du
formulaire et le bouton réactivé, sans erreurJavaScript/500 ni changement
des photos SQL. La seconde ligne invalide annule l’ensemble de la conversion ;
sa non-sélection autorise une facture partielle correcte.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_conversion_bon_prix_historique_postgres.py Test/test_e2e_conversion_bon_prix_historique_isole.py Test/test_br_cout_historique_postgres.py Test/test_fact3_partiels_ligne_par_ligne.py Test/test_fact4_facturation_robuste.py Test/test_fact4b_durcissement.py Test/test_e2e_cycle_achat_reception_partielle_isole.py Test/test_e2e_cycle_commercial_isole.py Test/test_e2e_facturation_br_retour_non_bloquant_isole.py --tb=short --junitxml=.codex-tests/conversion343_verifie.xml
```

Les683empreintes sont stables pendant/après la vérification finale ; seuls
`commercial.py` et les deux nouveaux fichiers de test diffèrent de la version341.
Les snapshots intermédiaires restent distincts du snapshot final. Les
avertissements multipart/Pydantic sont préexistants. Aucun frontend modifié,
donc aucun nouveau build revendiqué pour ce lot.

## Limites conservées

Les sources historiques non tarifaires et les autres conversions restent
à qualifier séparément. Ce lot ne tranche pas la signification d’un ancien
prix0 de bon/BC et conserve son fallback existant. Aucun nouveau barème,
champ obligatoire fiscal, migration ou modification d’écriture définitive.
La consolidation336 et les122tests341 sont des preuves antérieures,
non additionnées à ce lot. Recette partenaire et production à valider.
