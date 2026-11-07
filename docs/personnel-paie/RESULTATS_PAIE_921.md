# Résultats — RNI mensuel préparatoire921

**188cas distincts réussis** dans la campagne finale : {'unitaires_source': 142, 'API_SQL_restauration_PostgreSQL_natif_isole': 36, 'navigateur_Edge_API_PG_isole': 10}. Aucun échec, erreur ou ignoré dans cette sélection. [Preuve et chronologie](../../Test/PREUVE_PAIE_921.json). Le premier échec de fixture concernait une rubrique ponctuelle correctement bloquée ; le test positif utilise désormais une nouvelle rubrique mensuelle approuvée, sans changer la règle métier ni réécrire une source approuvée.

Source réelle de recette : brut9800.11 → bases fiscales9300.11/base de frais9000.10 → déductible60.00 → frais fictifs déclarés2250.03 → RNI6990.08. Transformation annuelle/12 : avant597.0240, réduction mathématique100.0000, après497.0240, fraction62128/125. Aucun de ces résultats n’est autorisé comme retenue à prélever. Retenue, déclaration, versement et net restent indéterminés.

Inconnues, excès de déductions, bornes du barème et fractions exactes contrôlés. Rappels, primes non mensuelles et versements source sur une autre année bloquent le cas général même après confirmation. Sources périmées refusées pour une nouvelle création ; lecture historique et idempotence conservées. Les snapshots ne peuvent pas être modifiés ou rattachés à une fausse préparation, y compris sous propriétaire. Migration124 rejouée et rôle limité testés sur PostgreSQL natif éphémère.

Edge1440/390 : parcours depuis les bases, saisie, résultat et fractions, retour à la source, inconnues, révocation et comptabilité inchangée. Écran390 inspecté visuellement. Non-régression des bases, rattachements et contrôles/documents annuels existants. Restauration100tables : contrôle, fractions et source restitués sous rôle limité ; schéma/données/séquences/ACL identiques, source intacte et cible nonce supprimée.

Build{'code': 0, 'modules': 213, 'secondes_vite': 9.57, 'avertissements': 'xlsx/chunks existants'}, compilation12fichiersPython, candidat546empreintes. AucunSQL ancien modifié.153cas humains dans quinze ensemblesPDF/Excel restent Non testé.

[Guide](RNI_MENSUEL_PREPARATOIRE_921.md) · [RecettePDF](RECETTE_RNI_MENSUEL_PAIE_921.pdf) · [SuiviExcel](SUIVI_RNI_MENSUEL_PAIE_921.xlsx). Prochaine étape : qualifier la liquidation mensuelle (frais/plafonds, arrondis, primes/rappels et régularisations) avant retenue effective, net et bulletins. Cette qualification ne peut être déduite du seul barème annuel.
