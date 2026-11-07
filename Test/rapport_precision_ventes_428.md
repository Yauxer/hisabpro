# Préparation ventes428 — centimes calculés conservés

Perte d'un centime reproduite en lecture de préparation pour une facture et son avoir. Deux lignes créées par API :prix1000000000000000 entier et0,01,quantité1 chacune,taux20% de laboratoire. Les valeurs effectivement stockées sont contrôlées avant toute assertion sur le total. Le moteur Decimal calcule HT1000000000000000,01,TVA200000000000000,00,TTC1200000000000000,01 ;le détour par les wrappersfloat renvoyait HT/TTC terminés par,00.

Correction minimale du seul service de préparation :garder les contrôles existants des pièces,prendre directement les résultats du moteur Decimal partagé TVA,base avant escompte etTVA/TTC après escompte. Aucune duplication de règle fiscale,aucun nouveau taux ni modification du moteur partagé. Les centimes déjà perdus lors du stockageFloat ne sont pas reconstitués ;les wrappers d'autres écrans restent une limite distincte.

## Preuves réellement exécutées

Avant sur sources connues :2échecs,facture etavoir,sourcesSQL vérifiées. Copie après correction :32réussis176.245s,compilation0. Racine après intégration :

precision428_racine:32réussis,202.496s.

API de lecture,CSV,Excel/PDF réellement téléchargés sur grands montants,signe de l'avoir,somme nulle de la facture etde son avoir intégral,identités,non-mutation,non-finis/inconnus,empreinte/permissions etEdge bureau/mobile vérifiés. Excel garde les grands montants en texte exact. Les autres préparations/exports etleurs comportements restent couverts.

Oracle distinct de laboratoire :deux lignes100à20% et50à10%,escompte10%,avoir de moitié. HTcommercial150,TVA22,50,TTC157,50 ;avoir−75/−11,25/−78,75 ;net75/11,25/78,75. Aucune qualification générale de taux déclarée.

## Essais intermédiaires etlimites

Le premier banc tentait de stocker un prix unique1000000000000000,01dans une colonneFloat :le centime était déjà perdu en base. Deux essais échoués conservés,le second avait23connexes réussis ;ils ne démontraient pas la cause du wrapper. Banc remplacé par deux prix réellement représentables etcontrôlés,avec nouvelle preuve avant correction qui échoue bien sur la somme. Aucune assertion financière assouplie,aucune valeur historique reconstruite.

Une invocation a utilisé le mauvais dossier de travail etn'a exécuté aucun test ;la relance en copie dispose de sonXML distinct. Les erreurs d'invocation sont consignées,non présentées comme succès.

La globale426sur729sources précède cette correction ;son résultat exact,notamment le dégressif,est conservé dans son rapport. Cette livraison correspond aux730sources après428et àses tests ciblés,elle ne constitue pas une nouvelle globale exhaustive. Pas deSQL,main,models ouschemas modifiés,aucun PostgreSQL réel ou données réelles.09Ereste interne/partiel,recette utilisateur àeffectuer,production non validée etpoint6en attente.
