# Lot691 — justificatifs des préparations et intégrité du dossier partagé

Les pièces sont rattachées explicitement à une version conservée, avec nom
original, référence facultative, taille, SHA-256, auteur et date d’ajout figés.
Ces compléments restent hors empreinte historique des balances. Ils ne modifient
aucune écriture, facture, source de balance ou ancienne version. Ils ne sont pas
recopiés automatiquement vers une version suivante.

Migration104 additive, manuelle et rejouable : table immuable, trois triggers,
contrôle parent/société/empreinte/acteur, plafond documentaire, SELECT/INSERT
seulement et séquence sans SETVAL. Aucun modèleBase ou main modifié : sans104,
le panneau explique son indisponibilité, le ZIP décrit ce statut et les autres
exports restent possibles. Aucune migration automatique au démarrage.

Les fichiers sont stockés sous nomsUUID ; leur lecture contrôle les octets
contre la trace. Absence ou altération bloque le téléchargement et le ZIP.
Un refusSQL nettoie le fichier nouveau, un fichier déjà présent n’est pas écrasé.
Le rejeuUUID est sérialisé par société. Formats limités comme les pièces jointes
existantes, maximum10Mo par fichier/50Mo par version ; limites affichées dans
l’interface, rôleLecture sans ajout. Le paquet contient les octets, métadonnées
et empreintes, sans constituer une archive fiscale définitive ou preuve de dépôt.

## Commandes et résultats exécutés

- Première API :4réussites et2erreurs42,71s. Le cas du fichier10Mo avait unID
  pytest comprenant son contenu ; limiteWindows32767caractères de variable
  d’environnement dépassée avant exécution du cas. IDs courts ajoutés :
  **9réussites34,04s**, zéro échec/erreur/ignoré.
- Trois lecteursPowerShell du log42Mo ont été arrêtés après identification de
  leurs seuls PID ; aucun processus utilisateur ou PostgreSQL réel arrêté.
- Edge :**6réussites50,16s**. Admin1440/comptable390/lecture390, vrais fichiers
  envoyés/téléchargés et ZIP ouvert ; refus de format puis correction, réel
  REVOKE/GRANT SELECT avec reprise, réponsesGET/POST retenues puis changement
  de version sans mélange. Noms longs et empreintes dans la largeur mobile.
- Installation104 :**2réussites26,51s**,95SQL distincts,31rejeux,
  126applications,46tables métier vides,82anciennes tables préservées,
  trois triggers actifs et ACL/séquences identiques au rejeu. CLI de schéma et
  runtime partiel distinct des parcours applicatifs104 ; URL externe refusée.
- Restauration : premier échec46,24s avantdump, banc452 attendant quatre fichiers
  sans déclarer la nouvelle pièce. Utilisation de son paramètre existant de
  suppléments, sans modifier le banc historique : **1réussite57,50s**,83tables,
  schéma/données/ACL/séquences et cinq fichiers conservés, vrais octets/traces/
  rendus/logos/manifestes identiques, source préservée et cibles supprimées.
- Build de la candidateA :**6,67s**, code0, avertissements préexistants conservés.
- Campagne communeA :**445réussites1316,02s**,30avertissements, zéro échec,
  erreur ou ignoré. Sources397 et670scriptsTest figés. Parcours annuels675, RAS681, balances677/679,
  compléments687, dossier689 et justificatifs104 sont inclus ; cas unitaires,
  API/PostgreSQL et Edge, y compris bancs synthétiques historiques identifiés.

Les campagnes recouvrantes ne sont pas additionnées. Les erreurs de banc ne
sont pas présentées comme des tests produit réussis.

## Correction d’affichage et version livréeB

Après la campagneA, le petitPDF affiché0Mo a été reproduit dans un Edge réel :
1échec32,65s,5cas non sélectionnés. Une seule modification applicative : la
fonction d’affichage de BalancePreparationDocuments.jsx choisit désormais
octets/Ko/Mo. Aucun backend, SQL ou autre fichier applicatif ne change depuisA.
L’assertionKo est ajoutée aux trois rôles ; un contrôle complémentaire vérifie
le rejeuSQL104 après conservation de vraies traces et fichiers, sans changer
les données, ACL, séquence ou octets.

VersionB :**33réussites105,79s**,413cas non sélectionnés,30avertissements,
zéro échec/erreur/ignoré : API104, six Edge104, huit Edge de ventilations687,
dossier689 API et quatre Edge connexes. **Build livré4,85s, code0**.
Les445cas qualifientA ; ils ne sont pas présentés comme réexécutés surB.
La collecte actuelle contient446cas avec le contrôle de rejeu supplémentaire.
L’égalité de tous les fichiers backend/SQL et autres sources entreA/B est
vérifiée, ainsi que les deux seuls scripts de tests modifiés.

Les deux phases conservent les témoins de quatre sociétés, trois fichiers,
écritures, versions et contenu des dossiers. Baselines privées interdites dans
le banc ; applications/clusters nettoyés.397sources et670scriptsTest figés
vérifiés séparément,107anciens fichiers protégés et77archives antérieures
inchangés. **11Python compilés**. [Preuve structurée](PREUVE_SESSION_HORS_RH_691.json).

Commandes réellement exécutées avec Python du venv, dotenv désactivé et
DATABASE_URL de collecte SQLite inoffensive ; fixturesPostgreSQL natives :

```powershell
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py session691_final Test/test_session691_consolidee_isole.py -x -vv
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py session691_livraison Test/test_session691_consolidee_isole.py -x -k 'test_691_10_ or test_691_12_ or test_691_13_ or test_691_14_ or test_691_15_'
```

## Documents et contrôle visuel

Mode d’emploi Word/PDF10pages/Excel5feuilles : cinq cas humains **Non testé**,
résultats/anomalies/preuves vierges. SourcePDF d’une page strictement fictive,
son SHA/tailles/données et unTXT de format refusé fournis. OOXML/XML/CRC,
PDF, feuilles/listes/formules et blancs Excel contrôlés ; pagesPDF et interface
mobile inspectées. MicrosoftOffice non ouvert. La nouvelle captureB montre le
petitPDF et le total de version enKo ; nom long et empreinte restent lisibles.

## Limites maintenues

Aucun PostgreSQL réel. Migration104 à installer explicitement sur la cible
autorisée ; conserver la sauvegarde, le dossieruploads et le manifeste de
migrations. Une empreinte ne certifie pas le contenu comptable/fiscal du document.
Les sources jointes ne sont pas réécrites pour leur ajouter un logo ; les PDF
et Excel générés de préparation gardent le logo actuel. ETIC/fiscalité et
formats officiels complets restent partiels ou bloqués, RH/paie et point6 humain
différés. Recette utilisateur et production non validées.

[Mode d’emploi](../docs/LIASSE_BALANCES_JUSTIFICATIFS_691.md).
