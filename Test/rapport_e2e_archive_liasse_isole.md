# Recette automatisée de l'archive annuelle — 7 octobre 2026

## Exécution réelle

Commande : `hisabpro-backend/.venv/Scripts/python.exe -m pytest Test/test_e2e_archive_liasse_isole.py -q`

Résultat final : **1 réussi, 0 échoué, 0 ignoré, 20,10 s**. Edge réel, frontend complet compilé par esbuild, API FastAPI réelle et cluster PostgreSQL éphémère. Aucun endpoint métier intercepté. Les CDN décoratifs sont bloqués par le support existant uniquement pendant les tests.

Deux essais précédents ont échoué dans le test : sélecteur « Exercice actif » demandé depuis le dashboard au lieu de Clôture (37,60 s), puis comparaison Excel sur deux colonnes au lieu des trois colonnes de la feuille (22,68 s). Ils ne sont pas des tests réussis et n'ont nécessité aucune correction produit.

Compilation : `python -m py_compile Test/test_e2e_archive_liasse_isole.py` : OK.

Tests connexes réellement exécutés : `python -m pytest Test/test_patch09_3_liasse_fiscale.py Test/test_patch120_liasse_exports_ventilations.py Test/test_patch131_liasse_pdf_identite.py -q` : **16 réussis, 0 échoué, 0 ignoré, 0,82 s**.

## Dossier synthétique et contrôles

- Société SARL fictive, IF `99000001`, ICE `009900000000001`, premier exercice 2025. Aucun identifiant réel ni dépôt fiscal.
- Capital libéré : 100 parts de 100 MAD détenues par un associé fictif ; D5141/C1111 : 10 000 MAD. Aucun chiffre d'affaires, stock, immobilisation, sûreté, engagement, opération en devises, changement de méthode ou événement postérieur dans ce scénario explicitement défini.
- Clôture via l'API autorisée. Le moteur existant constate la CM de 3 000 MAD, sans exemption ajoutée ni règle fiscale modifiée. Résultat avant impôt 0 ; résultat net −3 000 ; banque et actif 10 000 ; passif 10 000 ; liquidation confirmée après clôture.
- Compléments ETIC fournis explicitement par API : méthodes, associé, informations néant prévues par le scénario et dette fiscale classée à moins d'un an en N+1. Aucun classement provenant d'une date comptable supposée échéance. ETIC 23/23 et FEC sans anomalie bloquante ni avertissement dans ce dossier.
- UI « Finaliser » désactivée et API finalisation refusée avant les prérequis. Après contrôles admissibles : clic navigateur, confirmation, version 1 et empreinte complète visibles puis conservées après rechargement. Aucun contournement de contrôle.
- PDF téléchargé par l'UI et ouvert : identité figée et empreinte présentes. Excel téléchargé par l'UI et ouvert : nom `_FINAL.xlsx`, statut `finalisee`, identité figée, CPC net −3 000 et onglet ETIC.
- Empreinte SHA-256 recalculée indépendamment sur le contenu JSON persisté dans PostgreSQL, version et société vérifiées. Modification ultérieure de la raison sociale fictive par l'API : relecture de la liasse toujours issue de l'instantané initial.
- Deuxième finalisation et modification ETIC refusées (409). Tentatives SQL UPDATE et DELETE de l'archive refusées par le trigger immuable de la migration 027, chacune dans une transaction annulée.

## Isolation et limites

Le support vérifie URL, répertoire, nonce et marqueur du cluster créé par ce test. Il ne lit pas `.env`, ne contacte jamais PostgreSQL réel et termine ses processus API/navigateur/serveur ainsi que son cluster. Le schéma initial ORM et les migrations d'intégrité du support existant sont complétés par la migration 027 sur ce seul cluster. Ce parcours ne valide pas une installation vierge de toutes les migrations ni les privilèges d'un rôle de production.

L'Excel actuel n'embarque pas l'empreinte SHA-256 ; sa provenance figée est contrôlée par la version, le statut et les valeurs du snapshot. Le PDF et l'API portent l'empreinte. Une archive interne n'est pas une preuve de dépôt DGI. Les annexes 09B/09C/09E/09F/09G et le dossier fiscal complet restent des périmètres distincts.

Les 26 avertissements du parcours concernent des dépréciations existantes SQLAlchemy, python-multipart et Pydantic. Aucune erreur JavaScript ni réponse serveur 5xx observée. Pas de build produit supplémentaire : seuls un test et ce rapport ont été ajoutés.

Cette recette automatisée réduite ne valide ni la recette utilisateur annuelle complète, ni la réglementation fiscale, ni la mise en production.
