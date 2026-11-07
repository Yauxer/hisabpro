# Guide utilisateur — actualisation329

Le mode d’emploi demandé pour une présentation à deux est actualisé en
Markdown, Word et PDF. Version2 : familles historiques à TVA inconnue,
calendrier implicite, polices/icônes locales et confirmation BR non bloquante.
Les18fiches gardent leurs chemins d’accès, prérequis, saisies chiffrées,
actions, résultats attendus et limites. Les17résultats de suivi demeurent
**Non testé**, sans remplir une recette humaine avec les succès automatisés.

Exécutions réellement terminées par le principal :

- `python -X utf8 docs/guide/generer_guide.py` : code0,376blocs, sorties Word/PDF.
- `.codex-tests/verifier_guide_323.py` réutilisé sur cette version : code0,
  DOCX CRC et XML/rels valides,18chapitres et17lignes vierges ; PDF22pages,
  texte extrait sur chaque page, aucun caractère de remplacement ;11chemins
  de documents locaux présents et oracles Decimal indépendants inchangés.
- Pages PDF4/5/9/11/20 réellement rendues et vues : tableaux/paragraphes
  lisibles, nouvelles instructions article et BR présentes. La numérotation
  du contrôle négatif de fiche02 et certains espacements ont été corrigés,
  puis génération et vérificateur relancés avec code0.

Une tentative de patch documentaire avait un contexte de ligne incorrect :
elle a échoué sans modifier le document, puis a été remplacée par des
substitutions déterministes de texte ; aucun résultat de test attribué à
cette tentative. Le générateur reste inchangé et n’est pas répété dans le
différentiel329 ; il est déjà livré par323.

Aucun appel DB ni test métier relancé par cette génération. Word n’a pas été
ouvert dans Microsoft Word : contrôle OOXML et rendu PDF uniquement. La
validation visuelle du Word et la recette utilisateur restent à effectuer.
La consolidation325 est une preuve séparée décrite dans son rapport, sans
effacer les échecs historiques315.
