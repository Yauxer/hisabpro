# MODE D’EMPLOI ET RECETTE — NON-VALEURS DEPUIS LES BALANCES

Version 1 du 21 octobre 2026. Complément B1 de la préparation indépendante.

## Fonction ajoutée et limites

Comptabilité → Liasse fiscale → Préparer depuis des balances externes propose
Détailler les non-valeurs depuis les balances conservées. Le complément B1
reprend le titre du catalogue interne existant ; aucune exhaustivité officielle
du modèle DGI n’est présumée. Ce guide couvre cette avancée seulement.

Le brut est le solde débiteur signé des comptes21, les amortissements groupés
le solde créditeur signé des comptes281, et le net leur différence, selon
l’arithmétique du bilan existant. Les soldes inverses restent signés.
Chaque total est rapproché de la rubrique21 du bilan déjà figé ; un écart
reste visible et ne provoque aucune correction automatique.

Les comptes21 et281 sont présentés séparément. Aucun amortissement n’est
réparti par compte21 ou par immobilisation. Les libellés individuels n’ont pas
été conservés à l’import et restent indiqués Libellé non conservé. La différence
N/N-1 ne prouve pas les acquisitions, sorties ou dotations : ces mouvements
ne sont pas déduits. B1 peut être disponible après clôture technique119, même
si le CPC ne l’est pas. Une source manquante/incomplète reste indisponible.

## Données fictives exactes

Le module de préparations depuis balances doit déjà être installé, avec sa
migration071 existante préservée. Ce lot ajoute uniquement un complément :
aucune migration supplémentaire n’est nécessaire. Après application des fichiers,
redémarrer le backend et utiliser le frontend reconstruit ou le serveur de
développement. L’installation cible n’a pas été modifiée par cette exécution.

Créer ou utiliser une société fictive séparée en MAD, exercice2026 ouvert,
avec1111,2111,28111,5141 dans son plan. Prévoir un administrateur/comptable et
un lecteur. Un administrateur ajoute auparavant un logo fictif aux paramètres
de société. Ne jamais utiliser votre société comptable réelle pour ces essais.
Noter le nombre d’écritures du Journal avant de commencer : il doit rester
identique après les opérations de préparation.

Fichiers fournis dans docs/recette : BALANCE_FICTIVE_NON_VALEURS705_N.csv,
BALANCE_FICTIVE_NON_VALEURS705_N1.csv et DONNEES_NON_VALEURS705.json.
Ce sont des balances fictives à importer en préparation, pas des écritures
à injecter dans votre comptabilité.

N :1111 crédit10000 ;2111 débit4000 ;28111 crédit1000 ;5141 débit7000.
Les autres cellules débit/crédit sont explicitement0. Débit = crédit =11000MAD.
N-1 :1111 crédit10000 ;2111 débit3000 ;28111 crédit500 ;5141 débit7500.
Débit = crédit =10500MAD. Les autres cellules valent0.

Oracle indépendant : N brut4000 − amortissements1000 = net3000 ; banque7000
+ net3000 = actif10000 = capital10000. N-1 brut3000 −500 =2500 ; banque7500
+ net2500 =10000. Résultat CPC0 dans les deux périodes de ce jeu de soldes.
Ces chiffres n’établissent aucun mouvement brut, ni charge de la période.

## Utilisation dans l’interface

1. Sélectionner société fictive et exercice2026, puis ouvrir Liasse fiscale.
2. Ouvrir Importer N / N-1 dans Préparer depuis des balances externes.
3. Choisir les deux CSV fournis, cliquer Contrôler et préparer, puis Conserver une nouvelle version.
4. Noter numéro et empreinte de la version source. Ouvrir Détailler les non-valeurs depuis les balances conservées.
5. Avant conservation, l’écran indique qu’aucun détail des non-valeurs n’est conservé dans cette version.
6. Cocher la confirmation depuis les seules balances de cette version, puis Conserver les non-valeurs dans une nouvelle version.
7. La nouvelle version se sélectionne automatiquement. Rouvrir le détail, vérifier brut4000, amortissements groupés1000, net3000 et les trois écarts0.
8. Choisir N-1 dans Période des non-valeurs : brut3000, amortissements500, net2500. Revenir à N.
9. Télécharger la préparation PDF, Excel et le dossier de préparation ZIP.

Les sources, titre, méthode, auteur et date sont figés lors de la conservation.
Lire ou exporter une ancienne version ne recalcule pas B1 avec le moteur actuel.
Les autres compléments sont conservés. Les justificatifs restent propres à leur
version ; ils ne sont pas copiés implicitement dans une nouvelle version.

## Vérifier les documents téléchargés

PDF : rubrique B1, comptes2111 et28111 séparés, totaux et rapprochements du
bilan. Excel : Origine non-valeurs, Non-valeurs N/N-1 et Contrôle non-valeurs
N/N-1. Les totaux dépassant la précision exacte d’Excel restent du texte exact.
ZIP : non_valeurs_documentaires.json, préparation conservée, CSV, PDF, Excel,
justificatifs propres à cette version si présents, et MANIFESTE_SHA256.json.

Le logo et l’identité actuels apparaissent dans PDF/Excel, hors de l’empreinte
historique du contenu. Une absence de balance N-1 doit afficher Indisponible,
alors qu’une balance complète sans solde21/281 donne explicitement0.
Aucune écriture, liquidation fiscale, archive définitive ou fichier EDI officiel
n’est créé. Un écart nul n’établit pas une conformité fiscale ou juridique.

## Cas de recette humaine

Prérequis communs : données ci-dessus, société fictive, rôle administrateur ou
comptable ; lecteur pour le dernier cas. Aucune écriture ou incidence fiscale
attendue dans tous les cas. Renseigner résultat réel, anomalies et preuves dans
l’Excel fourni. Les statuts ci-dessous restent Non testé par l’utilisateur.

|ID|Actions / données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|NV705-01|Importer les deux CSV, contrôler et conserver la préparation. Ouvrir le détail des non-valeurs.|Débit/crédit N11000 et N-1 10500 ; détail non encore conservé. Noter numéro/empreinte et capture de la version source.|Non testé|
|NV705-02|Confirmer et conserver les non-valeurs dans une nouvelle version, puis vérifier N et N-1.|N4000/1000/3000 ; N-1 3000/500/2500 pour brut/amortissements/net. Écarts0, lignes21 et281 séparées et libellés non conservés. Capture des totaux et empreinte.|Non testé|
|NV705-03|Revenir à la version du cas01, puis à celle du cas02 ; comparer le Journal au nombre noté avant import.|Ancienne version sans détail B1, nouvelle inchangée, aucune écriture ajoutée. Captures des deux versions et du Journal.|Non testé|
|NV705-04|Créer une autre préparation avec le CSV N seulement ; conserver la préparation puis le détail B1.|N net3000 ; N-1 indisponible avec motif de source absente, jamais un faux0. Capture du comparatif.|Non testé|
|NV705-05|Depuis la version du cas02 avec logo fictif paramétré, télécharger PDF, Excel et ZIP.|Logo visible dans PDF/Excel, soldes et totaux identiques ; JSON et empreinte de version cohérents, manifeste contrôlable. Conserver les trois fichiers.|Non testé|
|NV705-06|Se connecter avec le lecteur de cette société ; consulter la version du cas02 et télécharger son ZIP.|Consultation/export possibles, aucune conservation ou modification du détail. Conserver capture des droits et le ZIP réel.|Non testé|

## État et suite

Le guide et les données sont contrôlés techniquement ; leur ouverture dans
Word/Excel et cette recette humaine restent à effectuer. Les tests automatisés
réels sur PostgreSQL jetable/Edge/restauration sont consignés séparément dans
le rapport705. Aucune migration nouvelle n’est nécessaire et aucune base réelle
n’a été utilisée. B1 et B11 partagent uniquement leur interface de consultation
et conservation, sans fusionner leurs règles de calcul.

La liasse indépendante globale reste partielle. Les autres détails ETIC et
compléments fiscaux doivent reposer sur leurs sources certaines ; les mouvements
bruts et informations extra-comptables manquantes ne sont pas inventés.
RH/paie et le point6 humain précédemment différé restent en attente.
