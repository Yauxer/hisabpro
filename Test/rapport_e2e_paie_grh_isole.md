# Paie & GRH — recette connectée de l’espace salariés

Date : 7 octobre 2026. Agent frontend ; trois scénarios Edge réellement exécutés sur FastAPI et PostgreSQL éphémères. Aucune connexion au PostgreSQL réel ni donnée comptable réelle.

## Modifications

- Écran `Paie & GRH` et navigation harmonisés avec les cartes, formulaires FormSection et couleurs de HisabPro : équipe, fiches salariées, recherche, actifs/archives, préparation mensuelle et provenance des paramètres.
- Création, édition, archivage conservant la fiche et réactivation réellement connectés aux routes existantes. Consultation complète des fiches autorisée en rôle lecture, champs désactivés et mutations masquées.
- Année de l’exercice et mois transmis au serveur. Un changement de société/année/mois recharge les données ; les réponses obsolètes sont ignorées. Erreurs distinctes des dossiers et des calculs affichées.
- Suppression des taux 2025 codés dans le composant et du bouton d’export sans action. Les calculs affichés proviennent exclusivement du serveur. Des paramètres absents ou un salaire historique invalide produisent des tirets, aucun total de paie inventé.
- Export CSV réel uniquement pour une simulation complète, avec société, période, brut, retenues, IR, net et charges. Noms/matricules commençant par un caractère de formule neutralisés.
- Salaire historique manquant : édition/réactivation demande une saisie explicite au lieu de convertir silencieusement en zéro. Poste optionnel null supporté.
- Bouton d’ajout désactivé pendant le chargement initial de la société, évitant que la fiche ouverte soit effacée à l’arrivée de son identité.

## Tests exécutés

Commandes :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
& ./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_paie_grh_isole.py -x
& ./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_administration_isole.py -x
& ./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_paie_grh_isole.py
npm run build
```

- Dernier parcours complet, session 56033 : **3 réussis, 0 échoué, 0 ignoré, 24,72 s**. Compilation Python réussie.
- Non-régression administration UI réelle, session 73511 : **2 réussis, 21,09 s**.
- Build Vite final après la garde de chargement : **134 modules, réussi en 4,21 s**. Build intermédiaire 131 modules, 4,28 s également réussi.
- Avertissements existants : classes Config Pydantic, python_multipart ; taille du bundle et import XLSX.

### Scénarios

1. Salariée fictive : création avec brut 10 000 MAD, édition à 12 000 MAD, matricule/CNSS/date conservés, rafraîchissement automatique. Février réellement demandé au serveur. Paramètres absents : statut bloqué, cotisations/totaux null, affichage des tirets et export désactivé. Archivage/réactivation, rechargement et formulaire à largeur réduite. **Aucune écriture comptable ni ligne créée.**
2. Consultation : fiche et salaire lisibles, champs désactivés, actions d’écriture masquées ; DELETE réellement refusé 403. Deuxième société indépendante : liste vide, dossier de la première société inaccessible 404.
3. Référentiel **explicitement fictif de laboratoire**, créé uniquement dans le cluster nonce vérifié puis supprimé par identifiants précis : brut 10 000, retenues sociales 600, IR 0, net 9 400, charges patronales 1 700, coût 11 700 MAD. Oracle indépendant : revenu net imposable annuel 120 000 − 30 000 − 7 200 = 82 800 MAD. Simulation affichée, CSV téléchargé et lu, préfixes anti-formules vérifiés, poste null modifiable/réactivable. Changement vers l’année suivante dépourvue de référentiel : préparation bloquée sans repli sur les taux précédents.

### Essais échoués consignés

- Session 65711 : 1 échec en 17,38 s, assertion de test sur séparateur de milliers ; `formatMAD` affiche bien `10.000,00` en fr-MA. Assertion corrigée sans modification produit.
- Session 97142 : 2 scénarios réussis en 23,03 s.
- Session 27105 : 2 réussis et 1 échec en 24,49 s ; ancienne assertion arithmétique 84 000 préchargée dans le processus. Oracle corrigé à 82 800, aucune règle métier contournée.
- Session 21862 : 3 réussis en 24,35 s.
- Session 68976 : 1 échec en 35,29 s ; course entre ouverture de fiche et chargement initial de société. Cause corrigée par garde de disponibilité ; session 56033 passée.

## Limites

Préparation de salaire fixe uniquement, pas bulletin définitif, paiement, déclaration CNSS ni journal des rémunérations. Référentiel social non confirmé pendant la session : les paramètres historiques incomplets restent bloquants et visibles. Variables, congés/absences et proratisation, primes, avances, CIMR et régimes particuliers restent des lots distincts. La recette utilisateur et la validation réglementaire demeurent à effectuer ; aucune conformité officielle annoncée.

## Complément — contrat facultatif, 7 octobre 2026

- Un contrat historique NULL n’est pas assimilé à CDI. Le formulaire affiche **À renseigner**, le payload conserve `type_contrat: null`, et la modification/réactivation n’invente pas de contrat.
- Une création peut choisir explicitement CDI/CDD/Autre ; le choix initial est **À renseigner**.
- Tests réels, session 16416 : **3 réussis, zéro échec/ignoré, 23,74 s**, incluant consultation et préservation du contrat NULL après édition et archivage/réactivation, ainsi qu’un CDI explicitement sélectionné sur la première fiche.
- Build final : **135 modules, réussi en 4,32 s** ; compilation Python réussie.
- Inspection visuelle indépendante, session 30557 : deux captures équipe/absences réellement générées via Edge/FastAPI et cluster PostgreSQL fictif, vues avec view_image ; cluster arrêté/nettoyé. Style cohérent ; un débordement horizontal des actions à largeur desktop constaté reste à corriger dans un lot distinct. Ces captures temporaires dans `.codex-tests` ne sont pas incluses dans les ZIPs.

## Complément — tableaux et fuite CSS, reprise du 8 octobre 2026

Le débordement desktop a été reproduit avant correction (échec17,75s rapporté par agent). La règle globale `table { min-width:1320px }`, ainsi que th/td, provenait de DelaisPaiement.module.css et affectait tous les écrans malgré le nom « module ». La cause est corrigée en limitant ces sélecteurs au conteneur de la page Délais. Le tableau Paie conserve un texte lisible, les noms longs se replient et le scroll horizontal est prévu à largeur mobile.

Après reprise, commande lancée par le principal : `Test/run_unit_tests.py Test/test_e2e_paie_grh_isole.py Test/test_e2e_grh_absences_isole.py --tb=short --show-capture=no` : **5 réussis, aucun échec/ignoré, 72,44s**. Les tests mesurent la largeur à1440px, l'accès par défilement à720px, les noms longs et l'absence de fuite sur une table étrangère au module. Les tests dossiers, simulation et workflow passent sur API/Edge/PostgreSQL éphémère. Connexes Délais/règlements : **13 réussis en0,51s**. Les anciens processus interrompus ne sont pas comptabilisés comme succès.
