# Annexe de recette des documents RAS —649


> **Version courante : révision2 du lot653.** Les liens de ce rapport ouvrent
> désormais les documents révisés : facture12000TTC, quote-part6000,
> cash5250/RAS750 et capital100000. Les chiffres et tests ci-dessous décrivent
> l'historique649, resté exact arithmétiquement mais insuffisant pour qualifier
> l'absence d'exclusion du petit scénario. Voir le [rapport653](rapport_coherence_scenario653.md).

Livrables : [Word](../docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.docx),
[PDF](../docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.pdf),
[Excel](../docs/recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.xlsx),
[données](../docs/recette/donnees_recette_documents_ras_20261019.json) et
[PDF fictif à joindre](../docs/recette/DOCUMENT_FICTIF_649.pdf).

Douze cas humains avec les16champs du cahier, depuis une société de test vierge
et le paramétrage jusqu'à l'annulation, les documents et les contrôles négatifs.
Tous restent **Non testé** : résultat réel, anomalies et preuves sont vierges.
Les limites non exécutables sont séparées. Le cahier annuel et les annexes
antérieures sont conservés ; ce complément ne les remplace pas.

Le PDF compte16pages : données en français, calculs indépendants, Journal,
un cas par page et limites. Couverture, page des calculs et cas d'annulation
ont été rendus et examinés ici. Le Word est vérifié comme OOXML valide, avec
en-tête/date corrects et largeur suffisante de la colonne Phase du Journal.
Le classeur compte8feuilles : synthèse, trois domaines, données, Journal,
soldes et limites ; statuts contrôlés, résultats réels vierges, listes déroulantes,
formules et graphique de progression. Ouverture interactive Word/Excel et
recette humaine non exécutées.

## Jeu chiffré indépendant

SOCIETE FICTIVE DOC649 SARL, MAD, exercice2026. Capital10000 ; achat1000HT+
200TVA=1200TTC ; quote-part600TTC/100TVA ; capture75 et virement525. Le compte
4457 est choisi explicitement pour ce laboratoire ; aucune affectation obligatoire
n'est déduite. Les faits de l'assistant reprennent le cas existant573 ; aucune
qualification fiscale réelle ou attestation n'est créée.

Avant annulation :4pièces,9lignes, débit=crédit11800 ; banque9475, fournisseur600,
capture75, résultat comptable avant impôt−1000 ; bilan9675. Après annulation :
6pièces,13lignes, débit=crédit12400 ; banque10000, fournisseur1200, capture soldée,
résultat−1000 ; bilan10200. Les fichiers et la référence complémentaire créent
**zéro pièce, zéro ligne et zéro montant**.

Le générateur calcule en centimes entiers et n'importe aucun service, modèle,
routeur ou base de l'application. Le test natif confronte chaque ligne de
chaque pièce, les comptes, les deux FEC, les bilans/CPC et restes de facture.
Deux fichiers homonymes et une référence sans fichier sont ajoutés à l'OD,
puis un troisième fichier à la contrepassation. Les photos des écritures
avant/après ces ajouts restent identiques, ainsi que le dossier099 ; aucun
mouvement de stock. L'essai à0,005 est réellement refusé sans mutation.

Oracle API102 réussi1cas en24.133s : toutes lignes/Journal/FEC/bilan/CPC avant et après annulation conformes. Contrôles documentaires finaux4réussis en0.808s, zéro échec/erreur/ignoré. Word OOXML valide et tableau lisible, PDF16pages examiné, Excel8feuilles/12cas humains Non testé/formules et preuves vierges, PDF fictif1page. Python compilé ; aucun produit modifié, build64712,49s conservé.

Commandes exécutées avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/generer_annexe_ras_documents649.py
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_oracle_ras_documents649_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_annexe_ras_documents649.py -q -x
```

Mise au point conservée : le générateur Word exigeait une ligne Version datée,
ajoutée avant génération réussie. Les premiers titres de sections de niveau1
étaient interprétés comme des couvertures et non comme des sections : hiérarchie
corrigée pour séparer les cas. Les données JSON brutes du corps ont été remplacées
par une présentation française ; elles restent disponibles dans leur fichier
distinct. Les contrôles documentaires ont été relancés après ces finitions.
Aucune erreur de génération ou test initial échoué n'a été requalifié.

Aucun changement applicatif, SQL ou règle fiscale dans ce lot. Dernier build
applicatif647 exécuté séparément en12,49s. Les tests utilisent une base native
102 jetable sous LOGIN limité ; aucune connexion à PostgreSQL réel, aucune
donnée comptable réelle modifiée. RH/paie et point6 humains restent différés.
Prochaine étape : consolidation des interactions capture/documents/FEC/états,
actualisation finale des preuves, du journal et du cumul différentiel.
