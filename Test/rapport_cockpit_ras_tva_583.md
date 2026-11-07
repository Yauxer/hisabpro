# Retenues TVA dans le cockpit fiscal annuel — lot583

## Changement

Un onglet **Retenues TVA** dans **Comptabilité → Liasse fiscale** réutilise le
registre annuel579. La société et l'année actives déterminent les pièces.
Les montants, états, détails et téléchargements sont ceux du même service,
sans dupliquer un calcul fiscal. L'interface distingue explicitement ce suivi
courant des tableaux T1–T25 et des exports/archives immuables de la liasse.
Les téléchargements du registre restent dans le registre, avec logo PDF/Excel.

Le texte EDI parle désormais de vérification du schéma applicable auprès
d'une source officielle, sans utiliser le mot « certifié » pour le produit.
Aucun XML/EDI, calcul fiscal, API, droit, SQL ou archivage n'a été ajouté.

Un guide PDF de2pages et son Markdown expliquent les deux accès, les totaux,
les contrôles et l'actualisation, avec une vraie capture mobile de laboratoire.
Le générateur fonctionne sans application ni base. Les anciens guides et le
cahier de recette restent inchangés ; aucun résultat humain prévalidé.

## Validation réelle le18octobre2026

Commande :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_liasse_ras_tva_isole.py -ra
npm run build
```

- Première exécution :6tests réussis,29avertissements,68,69s.
- Après la dernière formulation EDI :6tests réussis,29avertissements,64,99s,
  code0. Trois rôles (admin1440, comptable390, lecture390), téléchargement
  PDF avec logo et montant, changement2026→2025→2026, changement de société
  vers une société sans capture, navigation Bilan/CPC/éditeurETIC conservée.
- Empreintes des tables métier inchangées après lecture/exports et changements
  de contexte. API réelle, Edge réel et PostgreSQL nonce sous LOGIN limité.
- Build réussi en6,37s, avec l'avertissement existant des gros chunks.
- PDF guide ouvert :2pages, texte/image présents et absence de débordement
  contrôlée ; page1 et capture mobile inspectées visuellement.
- Comptage de la matrice :70lignes,16terminé/47partiel/3absent/4bloqué.

La finalisation d'une archive contenant une RAS TVA n'est pas un nouveau
scénario validé ici. Le suivi courant n'est pas ajouté à l'archive. Les
qualifications natives581 des captures et du registre restent distinctes.
PostgreSQL réel, recette utilisateur, déclaration TVA complète et production
non validés ; RH/paie toujours différées.
