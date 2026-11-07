# Profil Personnel seul881 — résultats et limites

28 octobre 2026. Le code ajoute le rôle `personnel`, des capacités toujours explicites, un confinement fermé des chemins/méthodes côté serveur, un contexte société minimal et une navigation dédiée. Le choix du rôle reste réservé à l’administrateur. La migration109 ne modifie aucun compte.

## Campagnes exécutées

Les preuves sélectionnent **362 cas distincts réussis** :42cas de qualification881 et320non-régressions (277de879 et43contrôles complémentaires d’authentification/administration).

- **152 tests unitaires/source**.
- **196 tests API/SQL/bootstrap sur PostgreSQL natif isolé**.
- **14 parcours Edge/API/PostgreSQL isolé**, dont les trois spécifiques881 :deux largeurs1440/390 et un transport interrompu puis rétabli.
- Compilation de11Python modifiés/ajoutés :OK.
- Build final `npm run build` :code0,201modules,Vite4,89s. Avertissements xlsx/imports et chunk volumineux préexistants.

La qualification881 (90,10s) inclut deux profils dédiés préparant/approuvant via UI, refus des autres modules, falsification du rôle local sans effet, changement de mot de passe via le formulaire partagé, invalidation des anciens jetons et nouvelle connexion. Les24cas API couvrent notamment19refus directs, les capacités et le module, le rôle actuel relu sur même JWT, un invité avec rôle local et révocation, ainsi que le secret personnel.

Les320non-régressions ont commencé avant les derniers ajouts limités au nouveau shell Personnel (client réseau partagé et Mon compte) ;les branches classiques n’ont pas changé. Les42qualifications et le build ont été exécutés après ces ajouts. Le backend est identique pendant les deux campagnes finales. Ne pas présenter les deux campagnes comme un seul lancement simultané.

## Essais intermédiaires conservés

- Première API :route de lecture des accès de sécurité absente de la liste autorisée ;corrigée vers le chemin existant `/api/employes/securite/acces`.
- Assertion positive sur une facture sans exercice :422 attendu par le contrat API ;test corrigé en précisant2026, sans changer la règle métier.
- Première UI :absence de route index dans le shell dédié ;écran vide reproduit puis route ajoutée. Deux parcours réussis après correction.
- Panne réseau :message anglais `Failed to fetch` reproduit ;utilisation du client API partagé pour le contexte, puis réessai réel réussi.
- Une commande de collecte nonreg a retourné code4 avant tout test, avec `Test/Test.py` inexistant ;chemins XML corrigés et lancement sous `personnel881_nonreg_final`. Aucun test n’est compté comme réussi par cette tentative.

Les campagnes initiales échouées et les passes intermédiaires sont conservées dans les XML. Le total362 utilise seulement les deux campagnes finales, sans double comptage. Aucun échec, erreur ou test ignoré dans cette sélection.

## Preuves

- [Résultats, identifiants et campagnes](../../Test/PREUVE_PERSONNEL_PAIE_881.json).
- [Empreintes479sources produit](../../Test/CANDIDAT_PERSONNEL_PAIE_881.json).
- [XML et indicateurs navigateur](../../Test/preuves_personnel881/).
- [Guide d’utilisation, installation et retour arrière](PROFIL_PERSONNEL_881.md).
- [Complément PDF de recette](COMPLEMENT_RECETTE_PROFIL_PERSONNEL_881.pdf),[classeur37cas humains](SUIVI_RECETTE_PERSONNEL_881.xlsx).

109 a été appliquée deux fois sur un PostgreSQL natif éphémère vérifié par nonce ;les empreintes des données métier restent identiques. Aucun compte, rôle ou capacité n’est automatiquement attribué. Les migrations antérieures ont été vérifiées inchangées.

**PostgreSQL utilisateur non contacté ;recette humaine non effectuée ;production non validée.** Le profil Personnel seul est livré ;le reste du Lot1 concernant les clés/RIB/pièces (D05) et régimes sociaux reste distinct. Les37statuts du classeur sont Non testé ;les formules/graphique se recalculent à l’ouverture Excel. Aucune règle de calcul fiscal/social nouvelle n’a été introduite.
