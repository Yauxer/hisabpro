# Lecture des factures historiques : défaut confirmé — lot359

**Diagnostic terminé ; défaut de lecture non corrigé.** Le fichier
`Test/diagnostic_lecture_factures_historiques.py` doit être lancé
explicitement :il est hors collecte `test_*.py` et conserve l'oracle
lecture200/facture saine visible. Un500 n'est jamais accepté comme succès.

Commande réelle, Python du venv backend avec `-X utf8` et dotenv désactivé :

```text
Test/run_unit_tests.py Test/diagnostic_lecture_factures_historiques.py
-vv -s --tb=short --junitxml=.codex-tests/lecture359_precisee.xml
```

Résultat :**2réussis,6échoués,0erreur/ignoré,25avertissements,38,06s,
code1**. Les deux contrôles sains et zéro explicite restent lisibles.
Chacun des cinq cas prixNaN/+inf/-inf/1e308 et quantitéNULL provoque
unGET500 sur la liste. Une facture saine du même exercice n'est alors
plus disponible dans cette lecture.

Le cas Edge connecté reçoit `net::ERR_FAILED` sur les lectures, affiche
l'alerte existante et ne montre aucune ligne de la facture saine. Aucun
corps de réponse API n'est simulé. La première version du diagnostic
attendait uniquement un événement réponse navigateur, absent dans cet
échec réseau :47,59s,2réussis/6échoués,code1. La version précisée attend
soit la vraie ligne, soit l'alerte, puis conserve l'assertion de présence
de la facture saine. Les deux preuves restent conservées séparément.

## Isolation et intégrité

Les huit cas utilisent l'API réelle et PostgreSQL éphémère protégé par
URL/répertoire/nonce. Les injections SQL sont limitées àdes factures
fictives en brouillon de ce banc. Les photographies de factures, lignes,
écritures, mouvements et séquences sont identiques avant/après les GET
et avant l'assertion de visibilité Edge. Aucun PostgreSQL réel ni donnée
comptable réelle n'est touché. Aucun ancien montant n'est réparé.

## Cause et périmètre de correction àreprendre

`routers/factures.py:lister_factures` calcule sans qualification préalable
les totaux, crédits, paiements et échéances. Les modèles de lecture
réutilisent les validateurs de saisie des lignes et exigent des totaux
numériques. `FacturesContext` conserve l'erreur mais vide la liste.
Il faut une réponse de lecture qualifiée conservant identités et lignes,
avec montants inconnus explicites, sans transformer une source invalide
en0 ni exclure silencieusement une pièce.

La correction devra couvrir aussi les situations de règlement, RAS,
avoirs et échéanciers, les agrégats et actions UI dépendants des montants,
ainsi que PDF/exports. La validation et comptabilisation doivent conserver
leurs refus actuels ; les contrôles344 ne sont pas assouplis.
Commencer par les mêmes cinq cas plus ventes/achats, multi-société et
factures définitives fictives. Vérifier que la facture saine reste lisible
et que les chiffres inconnus ne sont jamais présentés comme un zéro.

L'écran Factures protège déjà ses trois montants de synthèse lors d'un
échec de chargement ; ses deux compteurs et son état de liste restent
àqualifier dans le lot360. Ce lot ne résout pas leGET500 décrit ici.

Les3126tests354 et45tests357 restent des preuves antérieures distinctes.
Ce diagnostic ajoute un fichier Python, sources688 ; aucune source
applicative n'est modifiée par359. La recette humaine et la production
ne sont pas validées.
