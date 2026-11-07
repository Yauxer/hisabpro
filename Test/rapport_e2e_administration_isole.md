# Recette E2E administration sur environnement isolé

Exécution du 6 octobre 2026, reprise autonome. Cette recette ne constitue pas
une recette utilisateur ni une autorisation de mise en production.

## Résultat réellement exécuté

Commande PowerShell :

```powershell
hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_administration_isole.py Test/test_e2e_isole_guard.py -o addopts=
```

**3 tests réussis, aucun échec ou ignoré, 28,80 s** : deux parcours navigateur
Edge avec UI React complète, plus une garde refusant une cible non isolée avant
création du moteur, DDL ou lancement d'un serveur.

Parcours réellement effectués :

- Inscription depuis la page de connexion et création atomique d'une société.
- Plan comptable synthétique consulté dans l'interface puis complété explicitement.
- Création d'un utilisateur lecteur depuis les paramètres ; liste actualisée sans F5.
- Création d'un exercice suivant dans l'interface et sélection automatiquement actualisée.
- Création d'une seconde société depuis le sélecteur et changement de contexte.
- Déconnexion puis reconnexion réelle avec le compte principal.
- Connexion du lecteur, consultation du plan et de l'annuaire ; boutons administratifs absents.
- Tentative réelle POST du lecteur depuis le navigateur : refus 403 par le backend.
- Vérification PostgreSQL des sociétés, comptes, exercices/périodes et actions d'audit.
- Aucun événement d'erreur JavaScript et aucune réponse API 5xx dans ces parcours.

## Isolation et limites

Le support crée son propre cluster PostgreSQL éphémère, protégé par chemin,
marqueur nonce, nom de base et port distinct de 5432. Le schéma ORM et la migration
036 sont appliqués uniquement à cette base vierge. Quatre références de comptes
synthétiques y sont préparées ; ce test n'est pas une validation du référentiel
CGNC exhaustif ni de toutes les migrations de production.

La vraie API `main:app` tourne dans un sous-processus uvicorn avec URL isolée,
clé de test, CORS loopback et création de schéma au démarrage désactivée. Les
chargements `.env` sont désactivés. L'UI complète `src/main.jsx` et ses véritables
CSS/CSS modules sont compilés par esbuild avec URL API explicite, puis servis
par un serveur HTTP SPA local. Aucune API métier n'est interceptée ou remplacée.

Les CDN décoratifs Google Fonts et Tabler sont explicitement bloqués dans cette
recette : polices et icônes distantes non validées. Le repli typographique local
est utilisé. Le fonctionnement de ces ressources sur l'installation finale reste
à vérifier. Trois essais précédents avec Vite ont échoué avant le parcours :
`src/main.jsx` restait en attente. La trace réseau a infirmé l'hypothèse initiale
de blocage exclusivement lié aux CDN. Le support utilise désormais esbuild.

L'arrêt des processus propres à la recette, du thread HTTP et du cluster est
garanti par les contextes. Les tests vérifient que ces processus sont terminés et
que les répertoires temporaires ont été supprimés après fermeture. Aucun serveur
de développement n'est lancé sur la base réelle de l'utilisateur.

Le parcours annuel complet facturation → inventaire → clôture → dossier fiscal,
la restauration de l'installation réelle, les rôles PostgreSQL de moindre
privilège et la recette utilisateur connectée restent des validations distinctes.
