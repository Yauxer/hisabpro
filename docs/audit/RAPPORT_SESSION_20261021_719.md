# Contrôle719 — Cycle annuel connecté et préparation indépendante

Le scénario bancaire annuel existant est composé avec un contrôle supplémentaire
après les paiements2026, dans la même société fictive et la même application104.
Les opérations passent par les routes normales et Edge réel. Aucun mock de calcul,
aucune modification de moteur ou de règle métier pour obtenir un résultat vert.

Le parcours existant couvre factures achat/vente, validation/comptabilisation,
règlements2025 ventilés, lettrage, TVA, paramètres fiscaux de laboratoire,
rapprochement bancaire, clôture2025, AN2026, paiements des reliquats120par sens,
validation/lettrage et banque2026. Le callback ajouté conserve la préparation713
et ses rattachements715 après ce parcours, puis vérifie les données/exportations.
Le scénario termine ensuite ses contrôles FEC2025/2026 et balance Excel2026,
dont le total soldes4060/4060 de l’oracle, sans perturbation du jeu comptable.

Résultats réels :2tests réels réussis61,60s :oracle indépendant et parcours annuel bancaire Edge/API/PostgreSQL104 enrichi,0échec/erreur/ignoré,30warnings existants.1134SHA figés ; application715 et anciens tests inchangés. Toutes les tables métier hors préparation/audit et les lignes définitives restent identiques pendant création/export des trois versions. Banque Journal1000MAD distincte de source externe4200MAD ; FEC2025/2026 et balance2026 contrôlés après. Un Python compilé ; cluster/application jetables nettoyés.

Les chiffres externes sont volontairement distincts du Journal : banque4200
contre1000MAD et contrôles2340/2834/1511 à11000/4500/700MAD, écarts0. Les trois
versions JSON sont créées/exportées ; leurs manifestes et empreintes sont
vérifiés. Aucun solde externe ne remplace celui du Journal. Toutes les autres
tables métier, y compris factures/règlements/lettrage/clôtures et données fiscales,
ainsi que les lignes définitives, sont identiques avant/après cette préparation.
Audit normal des requêtes exclu du comparatif des tables métier, sans suppression
ou altération de traces. Aucun PostgreSQL réel ni donnée comptable réelle utilisé.

Les deux tests sont un oracle et un parcours annuel enrichi. Le socle347de701
n’est pas réexécuté intégralement. Les paramètres fiscaux sont ceux du profil
laboratoire existant, sans nouvelle qualification réglementaire. Aucune validation
humaine/production automatique. L’application est inchangée depuis715 ; dernier
build71510,70s et438connexes1713,49s restent ses autres validations.

Historique : première commande de préparation refusée par le parseur PowerShell
avant exécution ; aucune modification ni test réalisé par cette commande.
Fichier ajouté avec apply_patch, puis les deux tests ont réellement réussi.
Le cahier717 demeure Word/PDF23pages, Excel9feuilles et30cas humains Non testé.
Prochaine tâche fonctionnelle : sources fiscales/historiques autonomes B12/B13/
B14/C3 selon le point de reprise717, sans emprunter le Journal courant pour une
balance externe. RH/paie et point6 restent différés.
