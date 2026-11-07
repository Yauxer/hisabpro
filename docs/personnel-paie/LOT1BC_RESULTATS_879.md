# Personnel / RH879 — résultats exécutés

28 octobre 2026. Le dépôt est la source de vérité. Les15 tests spécifiques879 et les262 tests connexes sélectionnés ont réellement été exécutés pendant cette reprise.

## Résultats finaux

| Campagne | Résultat | Durée pytest |
|---|---:|---:|
| `personnel879_final` —données, API, intégration, UI |15réussis ;0échec/erreur/ignoré|118,07s|
| `personnel879_nonreg` —Personnel873/875/877, paie/GRH historiques, avances et sécurité|262réussis ;0échec/erreur/ignoré|407,80s|
| Frontend `npm run build` |Code0 ;200modules|Vite6,71s|
| Compilation des Python ajoutés/modifiés |6fichiers :OK|Exécutée avec `py_compile`|

Total sans double comptage : **277 cas distincts**, dont **124 tests unitaires/source**, **142 tests API/SQL/bootstrap sur PostgreSQL natif isolé**, **11 parcours Edge/API/PostgreSQL isolé**. Le test d’options API présent dans le fichier E2E n’est pas compté comme un parcours navigateur. Les duréesJUnit dans les fichiers de preuves sont les sommes de temps des cas ; elles diffèrent de la durée totale pytest.

Les avertissements préexistants SQLAlchemy/Pydantic et Vite (imports mixtes xlsx, bundle volumineux) restent signalés. Aucun échec ni test ignoré dans les deux campagnes finales. Le build a été relancé après les dernières modifications produit.

## Commandes

Exécution par `.codex-tests/lancer_session.py`, avec dotenv désactivé et URL de collecte volontairement injoignable ; les fixtures créent leur propre PostgreSQL natif temporaire protégé par nonce et utilisent un runtime non propriétaire. Aucun fichier `.env` utilisateur ni serveur PostgreSQL réel n’a été utilisé.

```text
python .codex-tests/lancer_session.py personnel879_final Test/test_personnel879_donnees_isole.py Test/test_e2e_personnel879_isole.py
python .codex-tests/lancer_session.py personnel879_nonreg Test/test_personnel_workflow877_unitaire.py Test/test_personnel_workflow877_isole.py Test/test_personnel_workflow877_deploiement_isole.py Test/test_personnel_dossiers875_unitaire.py Test/test_personnel_dossiers875_isole.py Test/test_personnel_dossiers875_deploiement_isole.py Test/test_personnel_habilitations873_isole.py Test/test_personnel_habilitations873_compat_isole.py Test/test_e2e_personnel_habilitations873_isole.py Test/test_paie_grh_postgres.py Test/test_grh_absences_postgres.py Test/test_paie_referentiel_postgres.py Test/test_avances_salaries_isole.py Test/test_demarrage_grh_base_existante_postgres.py Test/test_fact11_production_hardening.py Test/test_paie_grh_service.py
npm run build
python Test/generer_recette_personnel879.py
```

Pour réexécuter les tests hors de cette session, suivre les prérequis des fixtures natives et des guides précédents ; ne pas remplacer leur isolation par l’URL de production. Les XML livrés contiennent les identifiants et résultats réellement exécutés. Les outils privés de session ne sont pas nécessaires pour lancer directement les mêmes fichiers avec `python -m pytest`.

## Corrections et essais intermédiaires

- Premier parcours : échec d’identification accessible d’une liste déroulante. Cause corrigée par labels explicitement liés aux contrôles, puis parcours ordinateur/mobile réussis.
- Création et modification complétées par les coordonnées facultatives, CNSS et données fiscales connues. Application seulement après approbation ; champs omis conservés et données/motifs masqués selon capacités. Aucun calcul fiscal ajouté.
- Une demande dont le préparateur était désactivé ne pouvait plus être rejetée : échec409 reproduit, puis correction par la nouvelle migration108. Rejet indépendant200, approbation toujours409 et auteur conservé. Migration108 rejouée deux fois dans la fixture, sans mutation de données métier existantes.
- Sélection de proposition après une sortie future rendue cohérente avec les contrôles backend. Présentation de sidebar corrigée ; comptes distingués par nom et e-mail.
- Campagnes intermédiaires conservées, y compris les deux échecs initiaux ; elles ne sont pas additionnées aux277 cas finaux. La reprise877 antérieure aux modifications ne sert pas à qualifier879.

## Ce que les parcours couvrent

Création/soumission/approbation indépendante ; contrat et hausse future ; sortie à date ; attribution, révocation et activation via UI ; reprise historique, rejet et nouvelle proposition ; réseau interrompu puis rechargement réel ; conflit de révision sans écrasement ; changement de société sans fuite de données ou de brouillon ; rôles, masquage, absence de nouvelle écriture et conservation d’une pièce définitive fictive.

Les principales opérations passent sur Edge1440/390. Les trois scénarios réseau/concurrence/changement de société ont chacun leur parcours distinct ; tous les scénarios ne sont pas doublés sur chaque largeur. Les captures livrées sont issues des essais réels sur données fictives ; une inspection visuelle de fiche et formulaire mobile a également été faite.

## Traçabilité et limites

- [Preuve structurée,277identifiants et campagnes](../../Test/PREUVE_PERSONNEL_PAIE_879.json).
- [Empreintes de476sources produit](../../Test/CANDIDAT_PERSONNEL_PAIE_879.json). Les anciennes migrations ont été vérifiées inchangées. Le produit a été gelé avant les deux campagnes finales.
- [XMLJUnit et indicateurs navigateur](../../Test/preuves_personnel879/).
- [Guide et limites du pilote](LOT1BC_UTILISATION_RECETTE_879.md).

La protection du grand livre a été contrôlée sur des écritures fictives, sans modifier de comptabilité réelle. Aucune migration105–108 installée sur la cible utilisateur. Le guidePDF et l’Excel ont été générés et relus automatiquement :29cas présents, statuts humains tous Non testé, calculs indépendants23000,10/23876,54MAD ;7feuilles, formules et graphique présents. La recette humaine et les calculs réglementaires de paie ne sont pas validés par cette campagne.
