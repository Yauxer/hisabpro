# Banc dégressif429 — attente des montants affichés

La trace globale426 montre une lecture all_text_contents() retournant [] pendant le rechargement du tableau après la deuxième génération. Aucun montant erroné n’est démontré. Le module rejoué sans modification donnait2réussites28.558s :incident intermittent,preuve globale conservée.

Correction minimale du banc :les trois cellules dotation,cumul,VNC sont contrôlées par expect(...).to_have_text(),qui attend leur présence etleur valeur après chaque rafraîchissement. Aucun calcul,aucun montant attendu,aucune écriture produit modifié. Aucun délai fixe ajouté au parcours.

Deux exécutions du cycle Edge réel :réseau normal etlatence contrôlée250ms via CDP,avec la même API etPostgreSQL nonce jetable. Le troisième cas est l’oracle indépendant déjà présent.

## Tests réellement exécutés

3réussis,43.712s,0échec/erreur/ignoré,code0 ;compilationPython0.

Les cinq dotations attendues restent24000/14400/8640/6480/6480pour60000HT,sans reliquat. Chaque écriture générée est validée. Six écritures équilibrées,D=C132000 ;acquisition définitive etses lignes initiales inchangées ;aucune double génération àla seconde demande. Les deux réseaux utilisent le même oracle etles mêmes contrôles.

Les89autres incidents426concernent72démarrages de sous-processus avec code Windows0xC0000142 et17fermetures du pilote Playwright. La cause système exacte reste non démontrée ;ces incidents ne sont pas masqués par une relance automatique ouune assertion affaiblie. La globale430réexécute tous les cas etdispose de preuves distinctes.

Aucun PostgreSQL réel,donnée réelle,SQL,main,modèle oucalcul métier modifié. Recette humaine etproduction non validées ;point6en attente. Prochaine étape :suite globale430figée,puis couverture422etZIPcumulatif425.
