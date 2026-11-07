# Recette recouvrement connectée — 7 octobre 2026

Le parcours existant `/situation` utilise la vraie UI React, Microsoft Edge,
FastAPI `main:app` et un PostgreSQL éphémère protégé par les gardes du banc
facturation. Aucune API métier n'est simulée, aucun `.env` ni PostgreSQL réel
n'est utilisé. Tous les contacts, sociétés, factures et commentaires sont fictifs.
Les relances sont des enregistrements internes ; aucun message n'est envoyé.

## Régressions constatées avant correction

- Création d'une relance par l'UI : réponse 201, promesse 400 MAD pour facture
  1 200 MAD TTC, canal téléphone, dates promesse/prochaine relance persistées.
  Historique retrouvé après rechargement. Aucune écriture comptable créée.
  Le parcours s'arrêtait ensuite sur l'absence d'action Modifier :
  **1 échec en 38,37 s**. Modification/annulation existaient côté API PATCH
  mais aucune action ni statut n'était disponible dans l'historique UI.
- Les trois filtres avancés étaient ignorés avec « Toutes les ouvertes » :
  la facture à 1 200 MAD échue aujourd'hui restait visible avec minimum 1 201 MAD,
  minimum un jour de retard ou échéance maximale hier.
- Le rôle lecture voyait une action Relancer. Sa tentative POST réelle était
  correctement refusée par l'API avec HTTP 403.
- Exécution ciblée filtres/lecture : **4 échecs, 1 désélectionné, 44,57 s**.
- Premier passage après correction UI : **6 réussis, 2 échecs, 52,10 s**.
  L'annulation d'une relance à promesse historique 400 MAD après règlement
  intégral 1 200 MAD était refusée par HTTP 409 : le backend contrôlait l'ancien
  montant contre le solde actuel même pour une modification de statut seule.
  Corrigé côté produit en contrôlant uniquement une nouvelle promesse fournie.
  L'autre échec était le sélecteur exact Commentaire d'une textarea déjà remplie ;
  le sélecteur du test a été corrigé.
- Un premier essai de construction du test a échoué sur le sélecteur Canal
  imbriquant les options : **1 échec, 37,50 s** ; sélecteur du test corrigé.

## Couverture prévue par le fichier de test

- Création, lecture de l'historique et rechargement complet.
- Modification de la promesse et du commentaire, puis annulation conservant
  l'enregistrement dans l'historique avec son statut.
- Trois filtres avancés composés avec le statut, puis effacement des filtres.
- Consultation par le lecteur, absence d'actions de mutation et refus API 403.
- NaN brut JSON sur création et modification : HTTP 422 attendu, instantané
  complet facture/lignes/relances inchangé et aucune écriture comptable.
- Modification du commentaire puis annulation après règlement intégral,
  en conservant la promesse historique 400 MAD et la facture payée.

## Résultats réels après corrections

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_recouvrement_isole.py
```

**8 réussis, 0 échec, 0 ignoré, 29,99 s**, dont cinq parcours navigateur
(trois filtres, lecteur, création/modification/annulation) et trois tests API
(NaN POST/PATCH et suivi après facture soldée), tous sur PostgreSQL éphémère.
25 avertissements de dépréciation existants Pydantic/multipart.

Avant les dernières corrections UI, les deux tests API NaN ciblés avaient aussi
réussi : **2 réussis, 5 désélectionnés, 16,39 s**.

Compilation `python -X utf8 -m py_compile Test/test_e2e_recouvrement_isole.py` :
**OK**, code retour 0.

Les corrections produit sont réalisées dans `SituationFinanciere.jsx` et
`routers/recouvrement.py` par l'agent principal. Ce rapport distingue les
exécutions effectuées ici de ses autres tests backend et de son build frontend.

## Limites

Cette recette ne valide ni envoi email/SMS/WhatsApp, ni recouvrement externe,
ni recette utilisateur annuelle, ni conformité officielle. Les ressources CDN
décoratives sont interrompues dans le banc ; aucun appel métier ne l'est.
Le schéma isolé reçoit les migrations du banc PostgreSQL opérations ; cela ne
constitue pas une validation de tous les chemins de migration historiques.
