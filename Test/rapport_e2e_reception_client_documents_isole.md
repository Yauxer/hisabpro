# Documents de réception transmis par le client — 8 octobre 2026

## Analyse préalable

Le backend dispose déjà d'un stockage de pièces jointes pour `docType=bl`, réservé aux bons de livraison vente de la société courante. PDF, JPG/JPEG et PNG sont acceptés, ainsi que les formats bureautiques existants. Les routes vérifient l'appartenance du BL, le rôle d'écriture, l'extension, la taille et les chemins. Un suffixe UUID évite l'écrasement silencieux d'un fichier homonyme.

L'onglet Vente → Réception client affiche les BL mais ne présente pas le composant PiecesJointes. Il propose seulement le PDF généré par HisabPro et des actions de statut. Le besoin JUN07 reste donc partiel : aucun dépôt du bon de réception externe dans cet écran.

La correction réutilise le composant PiecesJointes et le type `bl` existants dans une fenêtre « Documents reçus du client », ouverte depuis chaque BL de l'onglet Réception client. Le lecteur peut consulter et télécharger ; seuls les rôles d'écriture voient le dépôt. Les pièces existantes restent consultables sans bouton de suppression dans cette fenêtre. Elle n'ajoute ni nouveau document commercial métier, ni état de signature, ni confirmation automatique de réception. Un fichier transmis par le client ne prouve pas automatiquement une signature authentique. Le dépôt laisse inchangés le statut BL, les articles, les mouvements de stock et les écritures.

La fenêtre capture le BL et l'année, puis se ferme et réinitialise sa sélection lors d'un changement d'année. Le composant de pièces est remonté pour chaque périmètre année/BL. Le Layout existant remonte déjà les pages lors d'un changement de société ; aucun nouveau contexte ni calcul commercial n'est ajouté.

## Isolation obligatoire du stockage de test

Le chemin historique des pièces est fixé dans `hisabpro-backend/uploads`. Une base PostgreSQL éphémère ne suffit pas à isoler ces fichiers, notamment lorsque les identifiants des sociétés recommencent à 1. Aucun upload de cette recette n'est exécuté sur ce chemin.

Le backend accepte maintenant `HISABPRO_UPLOAD_DIR`, avec le chemin historique conservé par défaut. Le serveur de test utilise obligatoirement un répertoire d'upload privé dans le dossier temporaire de sa fixture. Le test vérifie ce périmètre avant le premier dépôt, puis vérifie le chemin physique et le contenu exact des fichiers. Aucune donnée ni aucun fichier utilisateur réel n'a été modifié.

## Scénario exécuté

Deux largeurs Edge, 1365 et 390 px, sur vraie API et PostgreSQL nonce. Société/client/article/BL fictifs créés par API, BL en préparation, stock physique initial de cinq unités et déclencheur stock vente au BL. Un PDF reportlab explicitement fictif et un PNG valide sont préparés dans les fichiers temporaires du test.

Trois dépôts sont réalisés : deux PDF de même nom puis le PNG. Les téléchargements sont comparés au contenu original par SHA-256 et les fichiers physiques contrôlés dans la racine isolée. Le rechargement, le lecteur sans bouton de dépôt/POST HTTP 403, l'autre société HTTP 404 et le snapshot métier inchangé sont vérifiés. Aucun statut « signé » ou « reçu » n'est inventé.

## État des tests

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_reception_client_documents_isole.py -x
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 -m py_compile Test/test_e2e_reception_client_documents_isole.py
```

Le gel applicatif a été levé explicitement par l'agent principal après la globale historique `2199 passed`. La configuration du stockage isolé a été branchée avant tout upload.

Premier ciblé : **2 passed en 25,67 s**, sans échec. Compilation Python des trois fichiers modifiés/ajoutés : **exit 0**. Build Vite : **139 modules, exit 0 en 4,41 s** ; avertissements existants concernant XLSX et la taille des chunks.

Complément de preuve ajouté : téléchargement par le lecteur avec comparaison SHA-256 et fenêtre entièrement comprise dans les deux largeurs de viewport.

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_reception_client_documents_isole.py Test/test_e2e_cycle_commercial_isole.py Test/test_fact11_production_hardening.py Test/test_compta4_justificatifs_fec.py Test/test_patch071_detail_bon_livraison.py -x
```

Résultat final : **26 passed en 49,34 s**, zéro échec et zéro test ignoré. Ce run contient les deux nouvelles recettes Edge, la recette du cycle commercial existant et les contrôles connexes pièces/RBAC/détail BL. La compilation Python a été répétée après le complément de test : exit 0.

## Limites et prochaine étape

Le test utilise uniquement des pièces et des sociétés fictives. La validation utilisateur de ses propres documents/signatures reste à effectuer. Le stockage est local et doit être inclus dans les procédures de sauvegarde ; cette étape n'ajoute pas une preuve cryptographique de signature ni un archivage légal automatique. La prochaine tâche distincte est l'alerte indicative de stock dans les devis, avec sauvegarde autorisée même en rupture.
