# CSV partagés — montants invalides et textes — lot435

## Correction minimale

Le seul utilitaire `src/services/exportCSV.js` change. Les colonnes numériques
refusent désormais les types/chaînes non numériques complets etles nonfinis ;
elles affichent `À vérifier`,sans inventer un zéro. Les valeurs nulles/absentes
restent vides. Format FR,arrondis existants etnombres négatifs conservés.
Les textes commençant par =,+,-,@,même après espaces/tabulations,ont un préfixe
apostrophe pour leur usage comme texte dans un tableur. Les retours CR seuls
sont maintenant quotés,comme LF,point-virgule etguillemets.
Aucune donnée source,règle comptable,API oumigration modifiée.

## Preuves réellement exécutées

DiagnosticNode avant correction :Infinity exporté,12abc→12,00,1,5→1,00,
=1+1/TAB=1+1bruts etCRnonquoté. Premier banc :29échecs/12réussis2.62s,
dont2cas sans contenu mal analysés par le banc. Après ajout d’une colonne témoin
au banc,seuls les27défauts réels restent enéchec,14cas préservés réussissent2.56s.
Deux vrais téléchargementsEdge Journal1365/390avant correctif échouent surle
texte de formule brut,26.02s. Aucune réussite rétrospective déclarée.

68tests connexes réussis,0échec/erreur/ignoré,100.407s ;ciblés43réussis25.01s ;buildVite code0,5.86s ;node--check etcompilationPython code0.

Commande connexe :`Test/run_unit_tests.py Test/test_export_csv_partage.py
Test/test_e2e_csv_partage_isole.py Test/test_patch054_journal_conformite_finale.py
Test/test_balance_grand_livre_final.py Test/test_e2e_grandlivre_dates_contexte_isole.py
Test/test_e2e_balances_exports_isole.py`.

Nodeexécute le vraiJS etcontrôle les octetsBlob/BOM,échappements,types etfichier.
Edge clique le vrai bouton Journal etrelit le CSV téléchargé ;deux lignes
120,25/0,00 et0,00/120,25,noms/références protégés,API source identique avant/après.
Les tests connexes couvrent les téléchargementsGrandLivre,les contextes/dates,
balances générales/auxiliaires/âgées/comparatives etleurs Excel/PDF existants.
Les suites ciblées ne sont pas additionnées àla connexe ni àla globale430historique.
Build :avertissement de taille de certains chunks déjàexistant,aucune erreur.

## Limites

Exécution réelle deNode/Edge/FastAPI/PostgreSQLnonce ;aucun PostgreSQL réel.
MicrosoftOffice etrecette utilisateur nonexécutés. Les octets téléchargés sont
contrôlés ;les interprétations/options d’import de toutes les versions detableurs
ne sont pas qualifiées. Les centimes déjàperdus par stockage/calculNumber
ne sont jamais reconstruits. Le CSV réglementaire FEC etla préparation interne
des ventes serveur n’utilisent pas cet utilitaire etrestent inchangés.
