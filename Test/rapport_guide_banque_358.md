# Guide Word/PDF : saisie bancaire et résultats — lot358

Guidev7 du11octobre2026. La fiche10 explique l'alternative manuelle à
l'import, avec les deux crédits fictifs400/800MAD, dates10/02/2025 et
20/02/2025 et référencesVIR-DEMO-400/800. Il faut choisir une seule
méthode pour ces lignes. La date proposée, la vraie date du relevé,
la conservation d'une saisie et les bornes d'exercice sont distinguées.

Le paragraphe de preuves conserve les7échecs346 et précise la réussite
globale354 :3126tests,686sources inchangées, avant357. Le lot bancaire357
dispose de sa preuve séparée :45réussis dont13Edge connectés,112,18s,
build6,80s,687sources stables. Aucune addition des suites superposées.

La procédure de mise àjour reste destinée àune copie isolée déjà au
niveau349 ; aucun SQL nouveau ou remplacement de configuration.

## Vérifications réellement exécutées

- `docs/guide/generer_guide.py` :code0,389blocs Word/PDF générés.
- `.codex-tests/verifier_guide_323.py` :OOXML/XML/relations/CRC,
  18fiches,17statuts Non testé ;25pages PDF toutes lues ;11références
  locales et oracles chiffrés indépendants contrôlés.
- `.codex-tests/verifier_guide_358.py` :mentions nouvelles et anciennes
  preuves présentes, pieds11/10/2026 sur toutes les pages PDF et Word,
  7liens de procédure résolus ; page13 rendue puis inspectée visuellement.

Le guide conserve tous les statuts de recette humaine vierges. Office
n'a pas été ouvert ; les parcours du partenaire restent àeffectuer.
Générer les documents ne relance aucun test métier et ne touche aucune
base. L'avertissement de dépréciation fitz reste visible.

Prochaine action :couverture355 puis cumulatif356 ; lecture des factures
historiques aux montants inconnus àqualifier indépendamment.
