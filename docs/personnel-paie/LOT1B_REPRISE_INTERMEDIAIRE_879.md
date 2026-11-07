# Lot1B — état intermédiaire879, non validé

Session commencée le27/10/2026 à22:59UTC. Limite de deux heures dépassée au contrôle d'horloge suivant ; arrêt après consignation et emballage, sans ouvrir une nouvelle campagne de tests.

## Code présent

- Groupe de sidebar « Personnel & Paie », neuf rubriques numérotées, huit marquées « À venir » sans lien fonctionnel fictif. Lien vers l'ancien espace `/cnss` conservé. Ouverture du groupe sur navigation et attributs d'accessibilité ajoutés.
- Pages `/personnel-paie/personnel`, `/personnel-paie/personnel/:employeId`, `/personnel-paie/demandes`, `/personnel-paie/acces`. Une URL de rubrique future affiche son indisponibilité.
- Liste et filtres, consultation à date, fiche, création et reprise explicite, proposition d'identité/contrat/rémunération/sortie, soumission et approbation/rejet, historique et administration des habilitations.
- Contexte d'accès propre à la société et au jeton, droits relus depuis le serveur ; purge des écrans pendant le rafraîchissement. Les capacités et le rôle courant commandent les contrôles affichés ; le backend reste l'autorité.
- Saisie et affichage des nouveaux montants comme chaînes décimales, sans conversion en Number.
- Endpoint GET `/api/employes/personnel/options` pour choisir les comptes bénéficiaires et les fiches historiques non encore reprises. Projection sans salaire/CNSS, restreinte à identité/proposition et rôle admin/comptable. Les matricules manquants ou ambigus sont signalés.
- Noms des préparateurs/décideurs/auteurs ajoutés aux lectures de demandes et d'historique. Aucun changement de migration ou de transition métier.

## Vérification réellement faite

- Reprise877 :2tests réussis,15désélectionnés,32,65s, avant les modifications879 ; ce résultat ne qualifie pas l'interface nouvelle.
- `npm run build` :code0,200modules, Vite12,19s. Sortie récupérée de la session d'exécution48029. Avertissements existants xlsx/chunk volumineux.
- Compilation Python des deux fichiers backend modifiés :OK.
- **Aucun test navigateur, test API du nouveau endpoint ou test frontend automatisé879 exécuté.** Ne pas présenter le parcours comme validé ni comme prêt pour déploiement.
- Aucune donnée utilisateur/PostgreSQL réel contacté. Migrations105–107 à installer sur une copie pour la future recette ; aucune installation faite ici.

## Reprendre exactement ici

1. Lire AGENTS/journal, inspecter processus et empreintes du ZIP intermédiaire. Ne pas réécrire les composants déjà présents.
2. Créer `Test/test_e2e_personnel879_isole.py` en réutilisant la fixture107 de `test_personnel_workflow877_isole` et ses alias de fixtures. Utiliser exclusivement le cluster natif marqué nonce, dotenv désactivé et URL de collecte sentinelle.
3. Tester d'abord le GEToptions :société courante, rôles/capacités, membres actifs, identité historique sans salaire, blocage des matricules ambigus, fiches déjà reprises exclues. Tester aussi les nouveaux noms dans les projections existantes.
4. Parcours Edge1440et390 réellement connecté :préparateur et validateur dans deux contextes, création viaUI, soumission, approbation distincte, contrat approuvé, rémunération`9000.10`, hausse au01/01/2027 à`9876.54`, changement de date de consultation, refus d'auto-approbation et masques après révocation/Actualiser. Contrôler les écritures/lignes avant-après.
5. Parcours administrateur :attribution/révocation depuis l'UI et activation volontaire explicitement confirmée sur société fictive ; aucun grant ou état réel modifié. Tester le mode non installé/non activé et la désactivation du module.
6. Tester navigation directe, sidebar neuf rubriques/Àvenir, ancien `/cnss`, fermeture et clavier mobile, absence de débordement global, modales entièrement accessibles, rafraîchissement automatique et réponses périmées ignorées. Inspecter des captures réelles ordinateur/mobile.
7. Corriger chaque anomalie rencontrée avant de continuer. Non-régression877 et anciens parcours Edge ; nouveau build après corrections ; compilation des sources backend modifiées.
8. Mettre à jour preuves/matrice/guide utilisateur, puis ZIPdifférentiel final et cumulatif vérifiés ; terminer1B seulement alors. La recette d'ensemble1C restera une étape distincte.

Les formulaires et messages n'ont pas encore bénéficié d'une vérification visuelle réelle. Points à examiner particulièrement :sélecteurs de compte, lisibilité des noms homonymes dans les habilitations, confirmation d'indépendance, focus/scroll des modales et purge d'un détail ouvert après retrait de droit.

Ce ZIP est une sauvegarde intermédiaire de code, pas une livraison fonctionnelle validée. Développement1B en cours ; tests automatisés879 incomplets ; recette utilisateur et production non validées.
