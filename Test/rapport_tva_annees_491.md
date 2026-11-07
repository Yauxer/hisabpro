# Lot491 — Années TVA invalides et bornes du calendrier

Les trois routes TVA (lecture des paramètres, sauvegarde et déclaration)
refusent désormais les années hors1–9999 avec422, avant le calcul ou la mutation.
Ce sont les bornes techniques du calendrier Python utilisé par le module, sans
restriction à une période fiscale récente ni nouvelle règle marocaine.
La fonction de calcul des bornes renvoie aussi une erreur400 explicite pour
un appel interne hors calendrier.

La borne1 reste prise en charge : avant le1erjanvier0001, aucune situation
antérieure n'existe. Le calcul utilise le cas vide `None` déjà prévu par les
fonctions de situation facture/acompte, au lieu de soustraire un jour à date.min.
Les formules de TVA, prorata, crédit et faits générateurs restent inchangées.

## Reproduction et tests

- Année0, API de déclaration :500 reproduit,1échec/21désélectionnés en27,57s.
- Année1, déclaration annuelle :500 reproduit,1échec en27,96s, dépassement du
  calendrier lors du calcul de la veille de début de période.
- Premier passage après correction :4échecs/29réussites en64,26s. Les refus422
  fonctionnaient mais l'oracle exigeait aussi une piste d'audit inchangée surPUT.
  Le middleware conserve normalement une trace de refus. Le test contrôle
  désormais son ajout exact (chemin,422,échec,request_id), la conservation des
  événements antérieurs et toutes les tables métier inchangées. Aucune protection
  d'audit du produit n'est retirée.

33cas ciblent les années0,-1,10000 et2147483648, les trois routes, mois/trimestres,
les bornes1/9999 et la fonction interne. Les réponses invalides ne modifient
aucune table métier du laboratoire ; lesPUT refusés restent tracés. Les bornes valides conservent un crédit d'ouverture
de20MAD et une TVA due nulle sur société fictive sans opération. Les consultations
ne créent aucune écriture ni exercice. Ce scénario ne constitue pas un calcul
de TVA d'une entreprise réelle à ces millésimes.

Commande finale :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_tva_annees098_isole.py Test/test_restauration_journal098_isole.py -ra
```

**33tests ciblés réussis en62.33s**, puis **188exécutions
finales réussies,29avertissements en503.44s**,0échec/erreur/ignoré. Les passages
successifs ne sont pas additionnés. Les oracles098, avances, TVA, Journal,
vente/achat→validation→règlement→lettrage et clôture/à-nouveaux dans Edge sont
conservés. Une restauration froide098 est rejouée sur ce backend final :74tables,
quatre pièces, schéma/données/ACL/séquences et FEC conservés ; fonctions et
refus409/reprise disponibles après copie. Source préservée, cibles nettoyées.

Invariants finaux :0pièce déséquilibrée,0montant non fini,0définitive sans numéro
ou date de validation. Sources/fonctions/ACL inchangées pendant l'exécution.
Trois fichiers Python compilés ; aucune migration antérieure modifiée.

## Installation et limites

Installer `routers/tva.py` puis redémarrer l'API. Aucune nouvelle migration,
réparation automatique ou suppression de paramètres historiques. Les bornes
de calendrier ne prouvent pas qu'un taux, régime fiscal ou document officiel
est applicable à une année ; les limites fiscales du produit restent affichées.

Les contrôles de concurrence et la restauration098 sont rejoués sur le backend
final. La migration098 reste manuelle après097 pour ces protections. Aucune
base réelle n'est utilisée. Frontend inchangé, pas de nouveau build Vite ;
recette utilisateur/production et point6 restent en attente.
