# Consolidation reproductible et annulations — lot661

Le banc651 lisait `baseline645.json` et `cumul649_preuve.json` dans
`.codex-tests`. Ces fichiers privés sont volontairement exclus des ZIPs :
le test livré ne pouvait donc pas être relancé tel quel dans un autre dépôt.

Le défaut a été reproduit en interdisant leur lecture, sans déplacer ni
supprimer les fichiers : une erreur `FileNotFoundError` au setup, en26,72s,
avant l’oracle comptable649. Cet essai rouge n’est pas un test produit réussi.

La correction calcule les empreintes depuis les sources locales `src` et
`hisabpro-backend`, plus les fichiers de configuration frontend présents.
Les caches, environnements, uploads, archives, journaux et fichiers `.env*`
sont exclus. L’ajout ou la suppression d’une source pendant la campagne
est désormais détecté, en plus des modifications de contenu.

## Vérifications

Un test de régression interdit la lecture des fichiers exclus et vérifie
l’ajout, la modification et le retrait d’une nouvelle source : **1réussi en1,98s**.
La campagne commune conserve l’interdiction des deux baselines pendant toute
son exécution et utilise de vraies API, PostgreSQL nonce et Edge.

255cas distincts reussis765,99s,zero echec/erreur/ignore,sous vrai PostgreSQL nonce et Edge;382sources et temoins comptables/documentaires non vides preserves,2documents. Deux baselines privees explicitement interdites durant campagne. Test de sources1reussi1,98s,regression avant correction1erreur setup26,72s conservee.49archives referencees SHA/CRC/manifeste intactes. Python compile;aucun produit/SQL modifie dans661;dernier build6595,06s.

Le regroupement déduplique les fonctions identiques, en conservant leurs
paramétrages : les nombres ne doivent pas être additionnés aux campagnes
précédentes. Les témoins non vides comprennent une vente/achat entre sociétés
explicitement associées et un dossier RAS annulé avec deux documents.
Les lignes comptables, captures figées, justificatifs et lectures liées sont
comparés avant/après. L’ancienne preuve651 a été sauvegardée avant réexécution.

Un contrôle annexe a révélé un défaut du récapitulatif privé657 : le champ
contenant l’empreinte d’archive avait été écrasé par le texte « OK » lors
d’une fusion de dictionnaires. Les ZIPs n’étaient pas modifiés. Les49archives
référencées ont été intégralement revérifiées depuis leurs preuves originales ;
les nouveaux champs distinguent l’empreinte du ZIP et le résultat de contrôle
de son contenu. L’essai de contrôle échoué reste consigné.

## Relancer dans le dépôt livré

Avec les dépendances du projet et les binaires PostgreSQL/Edge nécessaires :

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_sources_consolidation661.py -q
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_consolidation_annulations661_isole.py -q
```

Ces tests créent leurs propres cibles isolées et contrôlent leur nonce.
Ils ne doivent pas être redirigés vers la base de l’utilisateur.
Une installation de dépendances, les droits d’exécution et les binaires restent
des prérequis ; aucune qualification universelle de toutes les machines n’est annoncée.

Aucun code produit, migration ou règle fiscale modifié dans ce lot.
Recette humaine et production non validées ; RH/paie et point6 humain différés.
