# Livraison711 — Cessions et retraits documentaires B3

Formulaire documentaire B3 de l’exercice N depuis sources explicites. Reprend
les données déjà utilisées par le tableau de cessions HisabPro : désignation,
date/type, valeur d’entrée, VNA et prix. Dates/types facultatifs ; montants MAD
non négatifs à deux décimales, inconnus distincts de0. Le type est explicitement
cession/retrait/autre ou vide. Dates impossibles, NaN/infinis/booléens et précisions
excessives refusés. Les lignes documentées sont identifiées et sourcées.

Contrôle indicatif exact en Decimal : prix déclaré moins VNA déclarée. Une
VNA ou un prix manquant rend la différence et le total indisponibles. Absence de
lignes ne fabrique pas de0. Date hors période et VNA supérieure à valeur d’entrée
gardent des alertes sans ajustement ; contradiction avec note B3 visible.
Les résultats sont figés avec catalogue/note/méthode/auteur/UTC/source. Lecture,
exports et rejeu n’effectuent aucun recalcul des anciens contrôles ; brouillon
distinct des données conservées. Aucun mouvement n’est déduit des balances ou
du registre réel. Ni résultat fiscal ni écriture générés, aucun taux nouveau.
La saisie B3 ne prouve pas l’exhaustivité des sorties ou leur raccord B2/B2bis.

Sauvegarde documentaire immuable partagée avec droits, société, SHAparent,
UUID/rejeu avant calcul, concurrence et restriction MAD. Autres compléments,
versions antérieures et rattachements de pièces préservés. Champ de sélection
commun enrichi seulement d’un placeholder configurable, valeur par défaut
inchangée pour les comptes251. Aucun nouveau SQL ni changement aux moteurs
comptables existants. PDF/Excel/ZIP avec logo actuel, exactitude monétaire,
textes de formules conservés comme textes et manifestes vérifiés.

Tests réellement exécutés ici : 24calculs/API 64.36s,8Edge+restauration 158.65s,368connexes 1368.78s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build6,16s code0,10Python compilés,1120SHA figés. Restauration10483tables/5fichiers et témoins conservés.108SQL/bootstrap et moteurs comptables inchangés. Guide Word/PDF7pages/Excel5feuilles,six cas humains Non testé, Office non ouvert.

Cibles : huit oracles purs et seize cas API natifs (dont treize rejets), huit
Edge admin/comptable/lecture1440/390, erreurs et brouillon préservé, écart d’un
centime, trois GET et un POST réels retardés, téléchargement réel et capture.
Restauration froide10483tables/cinq fichiers, ACL/séquences/données, pièces,
versions/notes/annexes/logos et contrôles B3 non vides préservés ; source intacte,
cibles jetables supprimées. Campagne connexe368 sur préparations et tous les
compléments récents ; témoins comptables/documentaires et1120empreintes stables.
Aucun PostgreSQL réel utilisé. Les campagnes se recouvrent, sans addition en
cas uniques. Le socle annuel347 de701 reste historique, non réexécuté ici.

Historique : premier oracle5réussites/un échec3,13s, attente sans alerte erronée
pour une VNA de stress supérieure à la valeur d’entrée. Assertion corrigée pour
exiger cette alerte, sans modifier le produit ; campagne finale24réussites64,36s.
Script privé initial refusé à la compilation pour guillemets JSX avant exécution,
corrigé sans effet produit. Les échecs initiaux restent consignés.

Guide Word/PDF et Excel cinq feuilles, six cas humains Non testé et résultats/
anomalies/preuves vides. Oracles Decimal, CRC/XML Word, six ID PDF, formules et
listes Excel vérifiés. Capture mobile390 inspectée. Office non ouvert et recette
humaine à effectuer. Développement du complément terminé ; tests automatisés
du lot validés ; mise en production nonvalidée. LIA-09D et statuts globaux restent
partiels. Suite : mouvements B2/B2bis/B5 avec sources explicites, puis fiscalité
indépendante. RH/paie et point6 humain restent différés.
