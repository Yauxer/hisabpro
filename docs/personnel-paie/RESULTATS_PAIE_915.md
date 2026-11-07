# Résultats — IR annuel depuis un RNI constitué915

**215 cas distincts réussis** dans la finale, sans échec, erreur ou test ignoré : {'unitaires_source': 163, 'API_SQL_restauration_PostgreSQL_natif_isole': 42, 'navigateur_Edge_API_PG_isole': 10}. Les campagnes recouvrantes ne sont pas additionnées. Les quatre échecs du premier montage de tests, leurs causes et la reprise réussie figurent dans [la preuve](../../Test/PREUVE_PAIE_915.json).

Douze mois effectivement préparés sur PostgreSQL natif, puis contrôle913 complet et IR créé par le nouveau parcours. RNI83881.0200 conservé ; base83890.00 avant application du barème ; IR7167.0000 avant famille puis5967.0000 après2×600. Aucun revenu ressaisi ou tronqué. Une famille inconnue laisse le résultat final inconnu ; source incomplète ou périmée refusée, anciens snapshots et reprises inchangés. Concurrence et clé partagée avec le parcours manuel, profil Personnel, sociétés distinctes, FK et gardes d’immutabilité vérifiés.

Edge1440/390 : lien depuis le cumul, formulaire prérempli, chargement du RNI, calcul et retour à la source, révocation, stockage navigateur et comptabilité inchangés. Restauration native de99tables, contenu et lien annuel relus avec rôle limité, précision RNI et IR identiques, schéma/données/séquences/ACL conservés ; preuve négative d’index altéré détectée, source intacte et cible nonce supprimée.

Build : {'code': 0, 'modules': 212, 'secondes_vite': 6.79, 'avertissements': 'xlsx/chunks existants'}. Compilation : 12 fichiersPython ; candidat538empreintes. Migration122 additive rejouée deuxfois et avec données, aucun SQL antérieur modifié.135cas humains dans douze ensemblesPDF/Excel, tous Non testé.

[Guide](IR_ANNUEL_SOURCE_915.md) · [RecettePDF](RECETTE_IR_SOURCE_PAIE_915.pdf) · [SuiviExcel](SUIVI_IR_SOURCE_PAIE_915.xlsx). La prochaine étape reste la qualification de la retenue mensuelle et des cas complexes avant net/bulletins. Le calcul annuel ne prouve pas un paiement ou une conformité officielle. Aucune base habituelle, clé ou donnée comptable réelle utilisée.
