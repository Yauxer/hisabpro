# Contexte des réponses HTTP — correctif745

Seul src/services/api.js change côté produit. Vérification du jeton à réception
etaprès lecture du JSON/blob,également avant synchronisation du rôle dansme.
Une réponse ancienne,même200,n’est pas restituée dans une nouvelle session.
Les erreurscourantes401etles refus anonymes conservent le comportement739.
Aucun rôle,jeton,backend ou calcul fiscal côté serveur n’est changé.

40 parcours connexes réussis en 258.02s ;2 annuels en 55.44s ;6 ciblés en59,70s et1POSTabouti en40,95s(6non sélectionnés). Zéro échec/erreur/ignoré dans les validations finales ;campagnes recouvrantes non additionnées. Build8,50s code0 ;1198SHA figés,nonvidefiscal/comptable/pièces/rendus préservés,272sources backend inchangées. Deux reproductionsrouges41,28/38,25s(5non sélectionnés). Word,PDF5pages,Excel5feuilles,4cas humains Non testé.

Reproduction avant correction :deuxsessions valides,puis le même utilisateur
adminA invitélectureB,avec véritable appel switcherAPI. Un ancien200profilA
restituaitA etécrasaitle rôle locallecture paradmin. Ce défaut duclient ne
modifiait pas les droits serveur. Les deuxpreuvesrouges sont conservées.

Septcas natifs :JSON/PDF courants,deuxcontextes aprèsen-têtes/aprèsdécodage,
POST201CSS déjà abouti dansA. Corps/statuts reçus du vrai serveur,sans donnée
métier inventée. Pour le décodage,la fin dujson/blob natif est retenue dansEdge,
son contenu ne change pas. Le jetonB vient d’unswitchAPI natif du mêmecompte.
Ce banc exerce leclient réel compilé,pasle sélecteurUI complet.

POST :une seule nouvelle version dansA,ancienne version préservée,lectureB404,
aucune écriture créée etaucun rejeu de mutation. Ignorer la réponse n’annule
pas une opération déjà exécutée ;revenir vérifier l’ancienne société avant
ressaisie. Les données métier des lectures restent identiques.

Campagne40 :ces7cas,les6cas401739,connexion décorative,PDF/Excel de balances,
cycles facture/paiement/lettrage achat/vente,catalogue commercial et9CSS.
PostgreSQL104 nonce sous LOGIN non propriétaire,Edge etAPI natifs ;1198sources
figées,témoins fiscaux/comptables/pièces/exports préservés. Deuxannuels séparés
pour oracle/cycle banque/facturation/règlement/lettrage/clôture/AN etbalances.
Aucun PostgreSQL réel,aucune migration,aucun backend modifié.

[Mode d’emploi](../docs/SESSIONS_CONTEXTE_HTTP_745.md),[Word](../docs/recette/MODE_EMPLOI_CONTEXTE_HTTP_745.docx),
[PDF](../docs/recette/MODE_EMPLOI_CONTEXTE_HTTP_745.pdf),[Excel](../docs/recette/MODE_EMPLOI_CONTEXTE_HTTP_745.xlsx).
Quatre cas humains Non testé,résultats réels/anomalies/preuves vierges.
Recettehumaine/Office/cible/production nonvalidées. Timeoutconnexion737 distinct,
non expliqué par745. Le chemin d’envoi multipart de justificatifs balance reste
un adaptateur séparé à qualifier ;il ne passe pas parrequest/downloadRequest.
RH/paie etpoint6 humain différés. Matrice70 inchangée.
