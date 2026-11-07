# Justificatifs et contexte747 — rapport

Seul src/services/api.js change côté produit : l’envoi multipart de pièces de
balance réutilise verifierReponseSession à réception, puis verifierJetonReponse
après lecture du JSON de succès ou d’erreur. Le même contrôle protège désormais
les trois chemins fetch de ce service. Le format d’envoi,les droits serveur,
les versions,les liens etles calculs restent inchangés. Aucun fichier n’est
supprimé ou réécrit pour masquer une erreur de contexte.

34 tests connexes réussis en 174.27s ;2 annuels en 53.39s ;5 ciblés en56,13s. Zéro échec/erreur/ignoré dans les validations finales,campagnes recouvrantes non additionnées. Build6,05s code0 ;1200SHA figés,témoins fiscaux/comptables/pièces/rendus préservés,272sources backend inchangées. Avant1échec attendu40,72s(4non sélectionnés). Word,PDF6pages,Excel5feuilles,4cas humains Non testé etPDF de recette/hash fournis.

Reproduction avant correction :un vrai401ancien effaçait le nouveau jetonB.
Cinqcas FormData/PDF natifs dansEdge :refusancien,succèsancien201,en-têtes ou
fin deJSON retenus,succèscourant,refuscourant. Jetons d’unswitchAPI natif du
mêmeutilisateur adminA/lectureB. Aucun statut ou corps métier inventé ;bancdu
client compilé distinct d’une recette complète du sélecteurUI ou de touslesonglets.

Un envoiabouti reste exactement une pièce dansA,octets/taille/SHAidentiques,
B404,préparation financière inchangée,aucun autre tableau métier modifié. Refus
401sans pièce/fichierorphelin ;nouvelle sessionconservée ou sessioncourante
refusée déconnectée selonlecas. Aucun rejeu dePOST. Un message de contexte
n’annule pas une opération déjà exécutée,àvérifier danssasociété avantressaisie.

Les34cas couvrent aussi API/SQLimmuables104,idempotence/concurrence/capacité,
fichiersaltérés/manquants,manifestes,UI3rôles1440/390,uploads/téléchargements,
relecture,refus/reprise etGET/POSTtardifs entreversions ;401739et200745 rejoués.
PostgreSQL104nonce sousLOGINnonpropriétaire,aucune base réelle.1200sources
figées et témoins financiers/fiscaux/pièces/export nonvides préservés. Deux
annuels séparés pour oracle etcycle banque/facturation/paiement/lettrage/clôture/
AN avec balances indépendantes. Backend272sources etSQL inchangés dans747.

[Mode d’emploi](../docs/JUSTIFICATIFS_CONTEXTE_747.md),[Word](../docs/recette/MODE_EMPLOI_PIECES_CONTEXTE_747.docx),
[PDF](../docs/recette/MODE_EMPLOI_PIECES_CONTEXTE_747.pdf),[Excel](../docs/recette/MODE_EMPLOI_PIECES_CONTEXTE_747.xlsx).
FixturePDF explicitementfictive fournie avec taille/SHA,aucune valeur fiscale.
Quatre cas humains Non testé,réels/anomalies/preuves vierges. Office/cible/
recetteutilisateur/production nonvalidés,RH/paie etpoint6 différés.
