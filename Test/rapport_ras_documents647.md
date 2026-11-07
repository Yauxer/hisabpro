# Documents complémentaires des OD RAS — lot647

Depuis le registre annuel ou la préparation mensuelle, **Documents liés aux OD**
sépare la capture et sa contrepassation. Le rôle autorisé peut joindre un fichier
via le stockage existant du Journal ; le lecteur consulte et télécharge. Les
fichiers et métadonnées du panneau sont relus sans F5. Les documents originaux
ne sont pas transformés pour leur ajouter un logo.

Les références complémentaires, dates, types, noms déclarés et marquages FEC
proviennent exclusivement de `ecriture_justificatifs`, filtrés par société et
vraies OD. La lecture est groupée par lots de1000identifiants, dans la même
session RO/RR que le registre. Aucun disque parcouru pour fabriquer cette vue.
Les totaux RAS et le dossier099 ne sont pas modifiés.

CSV, Excel et PDF ajoutent une section documentaire lorsqu'il existe des
compléments, avec distinction capture/contrepassation et logo dans Excel/PDF.
Les montants et positions des colonnes de captures restent conservés.
Les références ressemblant à des formules restent du texte. Le PDF conserve
les100références du vecteur multipage ; une date absente n'est pas inventée.

L'empreinte du registre inclut les métadonnées documentaires. Un ancien export
est refusé après ajout d'une référence ou d'un fichier. Les fichiers ne sont
pas incorporés dans l'export et cette empreinte ne signe pas leurs octets.
La disponibilité et les droits du fichier sont contrôlés au téléchargement.
Aucun document joint n'est automatiquement qualifié d'attestation fiscale,
de versement, de crédit ou de bordereau officiel.

## Tests réellement exécutés

Baseline existante12réussis en85.865s ;5API nouveaux réussis en48.561s ;29connectés/format finaux réussis en201.393s, dont4Edge nouveaux et100références multipages ;2restaurations réussies en129.082s (socle73tables/4fichiers et10280tables/7fichiers). Zéro échec/erreur/ignoré final. Build12,49s, Python compilé. Campagnes recouvrantes non additionnées.

Les cinq API sont exécutées sous LOGIN limité sur le schéma102 de laboratoire :
absence de complément explicite, trois documents/OD/contrepassation distincts,
original et dossier099 inchangés, formule Excel neutralisée, exports/logos,
ancien hash refusé, lecteur403 en écriture, autre société404 et registre vide.
Le test de concurrence utilise une seule connexion locale RO/RR et un vrai
ajout externe simultané : la lecture courante conserve son instantané, la
suivante retrouve le nouveau complément.

Les quatre parcours Edge couvrent administrateur1440/registre, comptable390/
préparation, lecteur390/registre et lecteur1440/préparation. Ils vérifient
l'ajout, le rafraîchissement du fichier et de sa référence sans F5, son export
immédiat, les octets téléchargés, la séparation des OD, l'absence d'actions
d'écriture du lecteur, les originaux comptables inchangés et la largeur utile.
Les captures1440/390 ont été ouvertes et examinées ici ; cela ne constitue
pas une recette humaine effectuée par l'utilisateur.

La restauration native102 compare80tables, schéma, données, ACL, séquences et
fichiers. Les deux registres, leurs JSON/empreintes, CSV, valeurs Excel, textes
PDF et logos, dossiers actifs/annulés et trois fichiers RAS sont identiques.
Le socle de restauration73tables a également été relancé séparément dans la
même commande. La preuve historique452 est conservée octet pour octet ; les
preuves nouvelles sont distinctes. Les cibles temporaires sont supprimées.

Mise au point conservée : la première lecture openpyxl du fichier téléchargé
échouait à cause du nom temporaire UUID sans extension ; le test lit maintenant
les octets. L'assertion PDF « Non renseignée » a été normalisée pour son retour
de ligne, sans modifier le document. Le socle de restauration attendait quatre
fichiers ; il accepte désormais une liste explicite de suppléments et exige
exactement4+3fichiers avec tailles/SHA attendus, sans filtrer le manifeste.
Les assertions de restauration source/cible restent intégrales. Aucune erreur
de banc n'a été présentée comme une correction métier ou ignorée silencieusement.

Commandes exécutées avec `PYTHON_DOTENV_DISABLED=1` :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_ras_tva_registre_isole.py Test/test_ras_tva_preparation_isole.py Test/test_ras_tva_registre_precision.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_ras_documents647_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_e2e_ras_documents647_isole.py Test/test_e2e_ras_tva_registre_isole.py Test/test_e2e_ras_tva_preparation_isole.py Test/test_ras_tva_registre_isole.py Test/test_ras_tva_preparation_isole.py Test/test_ras_documents647_precision.py Test/test_ras_tva_registre_precision.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -u -X utf8 Test/run_unit_tests.py Test/test_restauration_justificatifs_acl_isole.py Test/test_restauration_ras_documents647_isole.py -q -x
npm run build
```

Les suites se recouvrent et ne sont pas additionnées comme des tests uniques.
La base réelle n'a été ni connectée, ni modifiée. Aucun nouveau SQL ou critère
fiscal. Les anciennes migrations et les écritures définitives sont conservées.
La qualification fiscale, le déploiement cible et la recette utilisateur
restent à effectuer. Déclaration complète, imputation et reversement ne sont
pas rendus disponibles par cet ajout. RH/paie et point6 humains restent différés.

[Mode d'emploi](../docs/RAS_DOCUMENTS_647.md). Prochaine étape : complément
Word/PDF/Excel de recette, chiffres et contrôles indépendants, sans préremplir
de réussite humaine, puis consolidation et cumul de session.
