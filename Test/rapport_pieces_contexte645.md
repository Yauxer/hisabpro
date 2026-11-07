# Pièces jointes : erreurs et changements de contexte — 645

Le composant partagé masque désormais les résultats arrivant après un
changement de document, de jeton ou un démontage. Une liste refusée ne devient
plus un faux « Aucune pièce jointe ». Les erreurs sont lisibles, y compris les
détails structurés FastAPI. Un bouton permet de relire la liste sans F5.

La même garde protège l'envoi, la suppression, les callbacks de rafraîchissement
et le déclenchement d'un téléchargement. Une requête déjà reçue par le serveur
peut terminer dans son contexte initial ; son résultat n'est pas appliqué au
nouveau document. Il n'est pas prétendu qu'un changement d'écran annule une
mutation déjà engagée. Les vérifications serveur de société et permissions
restent inchangées. Aucun SQL ni règle fiscale ajouté.

## Preuves réelles

La reprise a relu tout le journal UTF8 (4 552 443 caractères, 1 951 événements),
les479étapes et les processus, puis vérifié les55fichiers du cumul643 contre
le dépôt. Aucun Python de test actif au départ. Le serveur PostgreSQL6028 et
ses enfants sont laissés intacts. Sans Git local, une photographie SHA256 de
1572sources sert de référence645. Les21tests de validation642 ont été relancés
et réussis en0,436s avant ce lot.

Les requêtes et données des scénarios viennent de la vraie API isolée. Pour
le cas de disparition du parent, une vraie réponse200 de référence est reçue
avant suppression du brouillon fictif, puis délivrée avec retard au navigateur ;
la liste des fichiers reçoit le vrai404. Aucun corps ou statut n'est inventé.
Pour les cas tardifs, `route.fetch()` consulte la vraie API avant changement
du jeton et `route.fulfill(response=...)` délivre sa réponse inchangée.

L'ancien composant exact a été retrouvé dans le ZIP453, avec SHA256 identique
à la photographie645. La version corrigée est sauvegardée et restaurée dans
un `finally`, sans toucher aux changements de l'utilisateur. Résultats sur
l'ancien composant : trois échecs sur quatre en60,188s (liste refusée et listes
tardives1440/390). Le contrôle initial du téléchargement observait trop tôt
l'absence d'événement ; sa fenêtre a été renforcée à1500ms. Ce cas a alors
réellement échoué en28,927s sur l'ancien composant : un document était téléchargé
après le changement de jeton. Cette reproduction distingue les défauts du
produit des erreurs du banc.

Deux premières tentatives404 étaient perturbées par la fermeture du dialogue
parent ou un GET arrivé avant suppression ; elles ne constituent pas une
preuve isolée du défaut. Un callback Python Playwright non pris en charge a
également été corrigé. Ces exécutions échouées sont conservées dans les traces.

La première campagne corrigée a réussi6cas en75,602s ; la campagne finale
ci-dessous reprend le test de téléchargement renforcé et les connexes.

La première suite connexe s'est arrêtée après10réussites et un échec d'un ancien
test de concurrence451 : il recherchait `UPDATE ecritures` dans les sessions
en attente, alors que la validation actuelle commence par `SELECT FOR UPDATE`.
Seule l'observation du test est corrigée : la vraie connexion bloquée doit
attendre précisément le PID détenteur du verrou du banc, et la validation ne
doit pas avoir fini. Les assertions200/409, conservation du fichier et de sa
trace restent présentes. Le code métier de validation n'est pas modifié.

Campagne finale : 23tests réussis en248.953s, zéro échec/erreur/ignoré ; concurrence ciblée1réussie en51.059s ; restauration73tables et pièces réussie, schéma/données/ACL/séquences identiques, cibles supprimées et preuve452 conservée. Build Vite6,91s, Python compilé. Suites recouvrantes non additionnées.

Commandes exécutées avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_reglements_centimes642.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_e2e_pieces_contexte645_isole.py Test/test_e2e_pieces_telechargement_refuse_isole.py Test/test_justificatifs_modeles_runtime_isole.py Test/test_e2e_reception_client_documents_isole.py Test/test_compta4_justificatifs_fec.py Test/test_restauration_justificatifs_acl_isole.py -q -x
npm run build
```

Les campagnes se recouvrent et ne sont pas additionnées. La restauration porte
sur des données fictives et des fichiers de laboratoire ; sa preuve historique
452 est conservée séparément de la preuve nouvelle645. Les fichiers comptables
originaux des cas de consultation et téléchargement restent identiques.

Recette utilisateur et déploiement sur cible non exécutés. Le comportement est
testé dans Edge ; aucune validation humaine ou certification d'archivage n'est
revendiquée. RH/paie et point6 restent différés. Prochaine étape : réutiliser ce
composant pour consulter/joindre les documents aux OD des captures et annulations
RAS, sans présumer d'attestation, de versement ou de crédit fiscal.
