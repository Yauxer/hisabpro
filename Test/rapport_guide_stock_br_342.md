# Guide d’utilisation et de vérification — version4, lot342

## Corrections documentaires

Le scénario d’achat précise désormais le préalable de gestion du stock :
**Paramètres → Fiche société → Gestion du stock → Achats — entrée de stock →
À la réception — BR passé en “livré”**, puis enregistrement. Sans ce choix,
les résultats de stock annoncés au passage du BR ne correspondent pas au
paramétrage par défaut. Les libellés ont été comparés au composant réel
`src/pages/Parametres.jsx`, sans modifier ce composant.

Les dates exactes du laboratoire sont explicites : commande10/03/2025,
première réception et facture11/03, seconde14/03, règlements18/03. Le chemin
du paramétrage des préfixes a aussi été corrigé vers **Fiche société →
Numérotation des documents**. Le dépannage explique le refus du coût
historique nécessaire au BR : opération annulée, données conservées, aucune
substitution arbitraire par zéro.

La procédure de mise à jour distingue la globale336, **3009cas réussis sur
la version avant341**, des **122tests ciblés et connexes après341**, dont
trois parcours Edge. Ces suites superposées ne sont pas additionnées.

## Vérifications réellement exécutées par le principal

- Génération avec `docs/guide/generer_guide.py` :385blocs ; générateur inchangé.
- `.codex-tests/verifier_guide_323.py` : structure OOXML et relations internes,
  CRC,18fiches,17statuts **Non testé**,23pages PDF avec texte extractible,
  11références locales et oracles chiffrés indépendants contrôlés ; code0.
- `.codex-tests/rendre_guide342.py` : version4, dates, prérequis, libellés
  réellement présents dans le frontend et distinction336/341 ; code0.
- `.codex-tests/verifier_procedure_342.py` :11liens existants, cinq ZIPs
 332/333/334/335/341 avec CRC valide, sans SQL, environnement ou secret ; code0.
- Pages11/12 du PDF final rendues et inspectées : scénario d’achat complet
  sur une page, puis fiche09 directement sur la suivante. La première
  ébauche24pages comportait un paragraphe isolé ; il a été déplacé au
  dépannage, puis le document a été régénéré en23pages. La dernière page
  a également été rendue et inspectée.

La génération et ces contrôles sont des vérifications documentaires. Ils
ne constituent ni une exécution supplémentaire des tests métier, ni une
recette utilisateur réussie. L’ouverture du Word dans Microsoft Office et
la recette partenaire restent à effectuer. Les taux/comptes du scénario
restent des hypothèses explicites d’un laboratoire fictif. Aucun changement
de règle fiscale, migration, PostgreSQL réel ou donnée comptable réelle.
