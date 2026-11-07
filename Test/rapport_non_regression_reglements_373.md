# Suite complète après ventilation — lot373

Exécution réelle le11octobre2026, de13h33 à14h47UTC environ.
Commande : `python -X utf8 .codex-tests/empreintes_reglements373.py run`,
qui lance `Test/run_unit_tests.py Test -vv --tb=short` avec rapportJUnit.
Nodev24.17.0 ; environnement .env désactivé et PostgreSQL éphémère gardé par nonce.
Le banc historique07b3 non isolé reste exclu par le lanceur.

**Résultat :3235réussis,4échecs,0erreur,0ignoré,33avertissements,4419,71s,
code1.** XML :3239cas,4419,571s. Les696empreintes produit/tests/migrations/configs/
assets sont identiques avant/après. Aucune réussite complète n'est déclarée.

Preuves conservées sans écrasement :
`.codex-tests/reglements373_globale.{log,xml,exit,sources.json}`.
Le wrapper a continué pendant l'interruption de quota ; aucune relance globale.

Échecs précis à traiter dans le lot377 :

- Assets mobile390 :attente Déconnexion alors que le menu mobile est fermé.
- Banc Layout du plan vide :deux profils attendent une alerte, mais le préfixe
  d'extraction ne fournit pas les nouveaux hooks useLocation/useRef/useCallback.
- Clôture :après passage2026→2025, l'écran affiche l'en-tête2025 avec les périodes
  janvier/décembre2026 et zéro écriture. Le parcours seul passe1cas32,92s, mais
  la trace complète révèle un écrasement par réponse précédente :correction UI
  et reproduction contrôlée nécessaires, pas un simple rallongement de délai.

Les tests ciblés371/372 sont distincts de ce résultat global. Les suites ne
s'additionnent pas. Base réelle non utilisée, migrations préservées. Recette
utilisateur et préparation de production restent non validées.

Prochaine étape :corriger377, exécuter les cas concernés et connexes ; une
future globale conservera son propre résultat sans requalifier les quatre échecs.
