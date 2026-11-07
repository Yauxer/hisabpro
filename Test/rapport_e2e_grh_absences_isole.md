# Congés & absences — recette connectée

Date : 7 octobre 2026. Agent frontend ; données exclusivement fictives dans des clusters PostgreSQL nonce éphémères. Aucun PostgreSQL réel utilisé.

## Modifications

- Onglet `Congés & absences` dans Paie & GRH, reprenant les cartes, tableaux, formulaires et couleurs existants.
- Demande datée : salarié actif, type congé/absence/autre, dates et motif ; affichage immédiat après succès, filtre par statut et ordre récent.
- Durée affichée explicitement en **jours calendaires inclusifs**, sans prétendre calculer des droits acquis, jours ouvrés ou retenues de salaire.
- Approuver/refuser avec commentaire, annuler sans suppression de la demande ; actions dérivées des permissions et états renvoyés par le serveur. Historique chronologique des décisions conservé et consultable.
- Erreurs lisibles : chevauchement 409 et dates inversées 422 ; aucun `[object Object]`. Consultation seule sans bouton de mutation.
- État et historique rechargés automatiquement ; aucune écriture comptable ni modification de salaire automatique.

## Exécutions réelles

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& ./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_grh_absences_isole.py -x
& ./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_grh_absences_isole.py Test/test_e2e_paie_grh_isole.py -x
& ./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_grh_absences_isole.py
npm run build
```

- Ciblés : **2 réussis, zéro échec/ignoré, 22,89 s**, session 40584.
- Consolidation congés/absences et paie initiale : **5 réussis, zéro échec/ignoré, 48,76 s**, session 20822.
- Compilation Python du nouveau test : réussie.
- Build final : **135 modules, réussi en 5,58 s**. Avertissements bundle/XLSX déjà connus.

### Parcours prouvés

1. Création réelle de 3 jours calendaires, chevauchement refusé 409 sans deuxième demande, dates inversées refusées 422 sans message objet brut, approbation commentée, annulation et nouvelle demande sur la période libérée puis refus commenté. Rechargement : deux demandes et cinq événements de suivi conservés, salaire 8 000 MAD inchangé, zéro écriture. Filtres et historique restent consultables.
2. Comptable différent de l’auteur : décisions et annulation masquées ; tentative PATCH réelle 403. Auteur comptable : annulation permise, approbation masquée. Lecteur : historique accessible, aucun bouton de mutation. Autre société : liste vide et demande inaccessible 404.

### Essais non réussis

- Premier montage : **1 erreur de setup, 0,78 s**, alias de fixture récursif ; aucun parcours métier exécuté. Fixture corrigée en important directement l’application de facturation isolée puis en appliquant 080/081.
- Une commande PowerShell de remplacement du texte de limite échoue au parsing d’une apostrophe typographique ; aucun fichier modifié ni test exécuté par cette commande, remplacée par apply_patch.
- Pendant une insertion JSX intermédiaire, deux commandes d’autres lots ont échoué à compiler CNSS (signalé au principal et au backend). Syntaxe rétablie avant build 4,61 s ; résultats de ces commandes restent des erreurs de montage, pas des réussites métier.

## Limites

Ce lot couvre le registre des demandes et décisions, pas les soldes légaux, acquisition de droits, jours ouvrés, justificatifs attachés, calendrier annuel visuel ou l’intégration de variables aux bulletins. Aucune règle légale marocaine de droits à congés n’a été ajoutée sans source officielle. Recette utilisateur et validation juridique restent à effectuer.
