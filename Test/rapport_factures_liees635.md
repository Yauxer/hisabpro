# Lot635 — vente validée et achat correspondant

Fabrique de brouillon existante extraite sans commit interne. La route ordinaire
conserve son commit et ses règles ; le pont peut enregistrer facture et lien102
atomiquement. Les méthodes de validation, comptabilisation, stock, TVA et
auxiliaires sont réutilisées, sans validation automatique chez l'autre société.

API de préparation, aperçu, création et suivi dans les sociétés liées633.
Articles de l'acheteur choisis ligne par ligne ; conditions/frais/échéancier
copiés depuis la source validée, référence fournisseur égale au numéro vendeur.
Exercice selon le calendrier réel de l'acheteur, période et clôture contrôlées.
Permissions doubles relues après verrou, empreinte de fraîcheur, idempotence,
unicités SQL et registre immutable. Création et retrait sérialisés sur la paire.

Interface dans le détail de facture, chargement à l'ouverture, protection du
contexte société/jeton, consultation seule sans formulaire. Écarts de brouillon,
TVA inconnue, annulation ou avoir signalés sans synchronisation silencieuse.
Suppression d'une pièce liée refusée clairement. Montants/stock/Journal de
l'acheteur inchangés jusqu'aux commandes ordinaires de validation/comptabilisation.

24cas finaux passes91.164s ;82connexes sous102 passes165.577s ;2Edge ancien socle passes33.288s ;restore80tables1passe52.547s ;buildVite5.02s, Python compile. Zero echec/erreur/ignore final, sources et temoin non vide inchanges. Suites recouvrantes non additionnees.
Premières campagnes :15API réussis43,541s puis18API/Edge83,628s. Extension des
variantes arrêtée car le banc tentait d'injecterNaN déjà interdit par une
contrainte PostgreSQL existante : test corrigé pour exiger ce refus, sans
désactiver la contrainte. Ce passage interrompu n'est pas présenté comme réussi.

Périmètres vérifiés : prix, frais, source inchangée, référence et échéances,
droits/sociétés, période fermée/clôture en cours, aperçu périmé, concurrence,
rollback forcé sans brouillon orphelin, deux Journaux600MAD et FEC, TVA déclarée
non déductible, sens inverse explicite, calendrier décalé, logos propres aux
deux PDF, diagnostic NULL et refus SQLNaN, avoir non répliqué mais signalé.
Deux parcours Edge1440/390 créent la correspondance, basculent réellement vers
l'acheteur, valident/comptabilisent et ouvrent le Journal ; un lecteur mobile
ne peut pas créer et ne modifie aucune donnée. Capture390 inspectée visuellement.

Commandes exécutées avec PYTHON_DOTENV_DISABLED=1 :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_factures_liees635_isole.py Test/test_e2e_factures_liees635_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_consolidation_factures635_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_restauration_factures_liees635_isole.py -q -x
npm run build
```

SQL101/102 rejoués sur données non vides et ACL préservées. Les tests de
restauration comparent80tables, schéma/ACL/séquences, deux Journaux/FEC,
CPC/bilans, PDF texte/images/logos, lien et retrait ; source préservée et
cibles supprimées. Les preuves historiques452 restent intactes.

Limites : pas de synchronisation de paiements/acomptes/avoirs/livraisons ou
consolidation fiscale. Une vente n'a qu'un achat lié ; le lien d'origine est
conservé même après retrait ou annulation.500lignes, MAD uniquement et source
sans RAS directe dans ce parcours. Compte/prorata/déductibilité restent ceux
explicitement préparés par les utilisateurs, sans règle fiscale nouvelle.

Les schémas101/102 sont livrés mais ne sont pas déployés sur la base réelle.
Recette utilisateur, installation cible et production restent non validées.
RH/paie et point6 humains différés. [Mode d'emploi](../docs/FACTURES_CORRESPONDANTES_635.md).


Compatibilité : l'ancien scénario d'édition TVA tentait aussi d'injecter150%
sur un schéma qui le refuse depuis094. Le test exige maintenant l'erreur SQL
et le rollback sur schéma récent ; son parcours historique150% reste réellement
exécuté sur l'ancien socle dans deux Edge séparés. Le parcoursNULL est conservé
dans les deux configurations. Aucun cas exclu ni contrainte désactivée.
