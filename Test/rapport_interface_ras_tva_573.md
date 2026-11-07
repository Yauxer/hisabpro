# Interface RAS TVA guidée573

Depuis Cycle commercial → Vente/Achat → Règlements → icôneRAS, le mode
« RAS TVA guidée » réutilise l'assistant559. Il prépare l'aperçu571, exige le
choix du compte et la confirmation des pièces, puis crée la capture et son OD.
Le dossier est consultable après création et accessible en lecture seule.

Le navigateur ignore les réponses d'aperçu devenues anciennes. Les champs et
le changement de mode sont désactivés pendant l'enregistrement ; Échap ne
ferme pas l'écran au milieu du POST. Les statuts et soldes se rafraîchissent
après réussite. Le compte reste explicitement choisi, sans affectation fiscale
automatique. L'installation sans099 affiche sa disponibilité sans DDL implicite.

## Corrections connexes nécessaires

- Les montants entiers ou à une décimale s'affichent exactement sans passage
  par Number, y compris les grands montants. Les formes invalides restent
  « À vérifier ». La vérification visuelle a révélé le cas entier initial.
- Les nouveaux faits monétaires sont sérialisés au centime. Le rejeu normalise
  en lecture les représentations anciennes équivalentes, sans réécrire leur
  dossier ou leur empreinte. Deux cas natifs couvrent entiers et exposants.
- Une déclaration TVA indisponible ne montre plus de tableaux ou de zéros
  provenant d'une réponse absente. Les paramètres et l'assistant restent
  consultables ; l'impression reste désactivée. Le traitement déclaratif
  des captures571 reste explicitement à qualifier.

## Tests réellement exécutés

- Premier navigateur :6 réussis,29 avertissements,72,59s.
- Après correction des affichages :34 réussis,29 avertissements,143,24s.
- Sources finales :**107 réussis,29 avertissements,216,99s, code0** dans
  `test_consolidation_ras_tva573_isole.py`, simulation559, moteurTVA et Node.
  Même cluster099 sous LOGIN limité : nouveaux cas API, anciens modes libres,
  simulations, validation et lettrage existants, trois rôles et écrans390/1440.
- Installation ancienne séparée, sans099 :**1 test Edge réussi**,29 avertissements,
  26,50s. Aucun POST de capture ou DDL implicite.
- Build final :**réussi en9,01s**, avertissement de taille des chunks conservé.

Les suites se recouvrent : ces chiffres ne s'additionnent pas comme des cas
uniques. Les avertissements pytest portent sur Pydantic/anyio historiques.
L'absence de python-docx a été constatée ; aucun paquet n'a été installé.

Les parcours utilisent deux règlements fictifs350/700MAD, des quotes-parts
400/800, TVA66,67/133,33 et retenues50/100. Les preuves comprennent les
réponses HTTP réellement retardées, les soldes et la consultation des dossiers.
Aucune réponse métier n'est simulée. La capture mobile du dossier a été
inspectée ; les montants et références restent lisibles sans débordement.

## Mode d'emploi et limites

[Guide PDF](../docs/guides/UTILISATION_RAS_TVA_GUIDEE_20261018.pdf),
[version texte](../docs/guides/UTILISATION_RAS_TVA_GUIDEE_20261018.md).
Trois pages, contrôle textuel, tableau calculé indépendamment avec Decimal,
capture fictive intégrée et renduPDF inspecté. Les anciens guides et cahiers
de recette sont conservés ; aucun résultat humain n'est prévalidé.

Migration099 à qualifier/appliquer sur l'installation cible par son administrateur.
Aucun PostgreSQL réel touché. La déclaration TVA des sociétés/périodes concernées,
son imputation et le reversement restent hors automatisation ; aucune déclaration
officielle ou conformité certifiée revendiquée. RH/paie différées.

Suite : qualification d'installation et de restauration099, puis cumulatif.
