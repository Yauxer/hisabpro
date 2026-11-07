# Qualification Personnel / RH — 28 octobre 2026

## Périmètre livré

Pièces privées chiffrées et coordonnées bancaires versionnées, préparation/soumission/décision indépendante, consultation explicite auditée, masques, contrôle des droits et séparation des sociétés. Interfaces desktop et mobile intégrées au Personnel existant. Configuration fermée par défaut, clés externes et procédures explicites.

Le Personnel disponible est testable sur copie isolée. Les lots du nouveau moteur de paie restent distincts et ne sont pas déclarés implémentés. Aucune écriture ni donnée comptable réelle n'a été modifiée.

## Commandes et résultats exécutés

Les campagnes sont lancées par `.codex-tests/lancer_session.py` avec `PYTHON_DOTENV_DISABLED=1` et une URL de collecte volontairement injoignable. Chaque fixture démarre uniquement son PostgreSQL natif temporaire protégé par un nonce. Les détails des cas et les JUnit conservés sont dans [la preuve structurée](../../Test/PREUVE_PERSONNEL_PAIE_887.json).

| Campagne | Résultat | Durée |
|---|---:|---:|
| personnel887_api | 8 réussis | 40,41 s |
| personnel887_ui | 11 réussis | 83,52 s |
| personnel887_restauration | 1 réussi | 39,48 s |
| personnel887_final, 34 fichiers pytest | 406 réussis ; aucun échec, erreur ou ignoré | 1 528,66 s |
| personnel887_ui_justificatif | 2 réussis | 93,86 s |
| Build frontend final | code 0 ; 202 modules | Vite 16,27 s |

La qualification finale compte **406 cas distincts** : 166 unitaires/source/outillage, 222 API/SQL/restauration PostgreSQL natif isolé, 18 parcours Edge/API/PostgreSQL isolé. Les petites campagnes ne sont pas additionnées à ce total. Après le lancement de la campagne complète, le téléchargement de la pièce associée depuis la fenêtre de décision a été ajouté dans deux composants frontend. Les deux E2E ont ensuite été rejoués sur cette dernière interface, avec comparaison binaire du téléchargement ; ils remplacent les deux mêmes identifiants dans le total. Le backend est resté identique. Le build final suit ce dernier changement ; l'exemple de variable d'environnement vide est documentaire.

Les avertissements pytest portent notamment sur Pydantic et les événements de démarrage historiques ; le build conserve les avertissements xlsx/chunk existants. Ils ne sont pas présentés comme des échecs. Les erreurs de harnais Windows de la première campagne 885 restent consignées séparément dans cette livraison antérieure ; elles ne sont pas effacées de l'historique ni comptées comme réussites.

La compilation Python a été exécutée sur les 11 fichiers Python modifiés/ajoutés du lot. Les deux générateurs documentaires ont ensuite été exécutés réellement après leur dernière correction. Le manifeste candidat identifie 487 fichiers produit par SHA-256. Les anciennes migrations, notamment 111, sont inchangées ; 112 est additive.

## Restauration et preuves visuelles

`pg_dump` / `pg_restore` ont réellement été exécutés vers une deuxième base temporaire. Les 85 tables, données, schéma, séquences et droits ont été comparés ; accès runtime restreint, absence des clés dans le dump, restitution exacte des pièces et coordonnées, refus sans clé puis récupération avec la clé sauvegardée : contrôles réussis. La base source temporaire est restée inchangée et la cible temporaire a été supprimée. Aucun PostgreSQL de l'utilisateur n'a été contacté.

Captures de recette fictive : [desktop](preuves/887_1440_coffre.png), [mobile](preuves/887_390_coffre.png). Les E2E contrôlent la séparation des droits, la révocation et l'absence de fuite dans le stockage navigateur et de débordement horizontal global.

## Livrables et statuts

Le [cahier PDF](CAHIER_RECETTE_PERSONNEL_HISABPRO_887.pdf) contient 59 cas sur 29 pages ; le [classeur Excel](SUIVI_RECETTE_PERSONNEL_887.xlsx) contient 11 feuilles, le tableau de bord, les données et les colonnes de résultats réels/anomalies/preuves. Tous les statuts humains sont **Non testé**. Les 59 identifiants, les totaux, les formules et les pièces fictives ont été contrôlés ; le fichier de refus de taille contient exactement 4 194 305 octets. Les sommes indépendantes des trois salaires contractuels connus restent 23 000,10 puis 23 876,54 MAD ; les deux autres salaires inconnus restent vides.

| Axe | État |
|---|---|
| Développement Personnel disponible, coffre et banque | Livré pour recette |
| Tests automatisés de ce périmètre | Réussis en environnement isolé |
| Recette utilisateur | À effectuer |
| Installation réelle 111/112, clés, ACL et procédures réelles | À effectuer sur copie avant production |
| Nouveau moteur de paie | Non livré par ce lot |
| Prêt pour mise en production | Non validé |

Les limites d'exploitation et le mode d'emploi sont dans [le guide 887](COFFRE_BANQUE_RH_887.md). Aucun antivirus, paiement automatique, purge automatique ou réchiffrement historique n'est présumé. Aucune conformité officielle n'est revendiquée.
