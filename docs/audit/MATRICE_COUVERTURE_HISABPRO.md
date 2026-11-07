# Audit et matrice de couverture fonctionnelle — HisabPro

## Qualification 955 — cotisation minimale sur copies indépendantes

| Domaine | Statut | Preuve / suite |
|---|---|---|
| CM : copie exonérée et copie de contrôle non exonérée | terminé dans le périmètre testé | HP-FIS-024 ; Edge 1440/390, sauvegarde et rechargement, comptabilité inchangée |
| Réserves restantes | partiel | 10 fiches partielles et 12 bloquées ; résultats humains conservés |
| Dépôt officiel | absent de ce parcours | Préparations internes uniquement |
| Production et recette humaine | bloqué | Configuration cible, migration sur copie, justificatifs et décisions restantes |

Finale 955 : deux succès, aucun échec ni ignoré, 92,69 secondes XML. Produit identique au candidat 953, 550 fichiers ; aucun calcul ni taux modifié. Suivi : 250 réussis, 10 partiels, 12 bloqués sur 272. Aucun PostgreSQL réel utilisé. [Résultats](../recette/RESULTATS_MVP_955.md), [preuve](../../Test/PREUVE_MVP_955.json), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_955.xlsx). Historique conservé ci-dessous.

## Qualification 953 — TVA annuelle sur encaissements

| Domaine | Statut | Preuve / suite |
|---|---|---|
| Année complète sur encaissements et compensation signée | terminé dans le périmètre testé | HP-FIS-033 ; deux parcours Edge, clôture, 12 PDF, recouvrement N+1 |
| Réserves automatisées restantes | partiel | 11 fiches partielles et 12 bloquées ; statuts humains inchangés |
| Transmission officielle DGI | absent de ce parcours | Les préparations internes ne constituent pas un dépôt |
| Mise en production et recette humaine | bloqué | Migration sur copie, configuration cible, justificatifs et décisions restantes |

Finale 953 : 44 succès, aucun échec ni ignoré, 904,09 secondes XML. Build Vite : 214 modules / 10,29 secondes. Candidat 550 fichiers : cinq corrigés et migration 126 ajoutée, aucun historique qualifié arbitrairement. Suivi : 249 réussis, 11 partiels, 12 bloqués sur 272. Aucun PostgreSQL réel utilisé ; restauration non rejouée dans ce lot. [Résultats](../recette/RESULTATS_MVP_953.md), [preuves](../../Test/PREUVE_MVP_953.json), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_953.xlsx). Historique conservé ci-dessous.

## Qualification951 — exploitation et clôture de la couverture par fiche

| Domaine | Statut | Preuve / suite |
|---|---|---|
| Reprise backend et reproductibilité | terminé dans le périmètre testé | Arrêt/redémarrage réel,validation unique,audit ;commandes etpreuves |
| Installation,migrations,sauvegarde etrestauration du dossier complet | partiel | Banc104+125,84tables etpièces fictives testés ;configuration/dossier annuel réel non restaurés |
| Sécurité de la cible etavis réglementaire | bloqué | Revue HTTPS/secrets/permissions etavis responsable nécessaires ;point6humain maintenu |
| Rattachement des272fiches | terminé | 248Réussi,12Partiel,12Bloqué(source),aucune fiche sans classement ;statuts humains inchangés |

Finale951 :16réussis/0échec/0ignoré,233,51sXML :10API/SQLnatif,2scénariosrestauration,3unitaires/structure,1CLI. Produit949 inchangé,549empreintes ;pas de déploiement,PostgreSQL réel ou modification comptable historique. Le rattachement complet ne signifie pas une recette humaine ou production validée. [Résultats](../recette/RESULTATS_MVP_951.md),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_951.xlsx),[limites](../recette/EXPLOITATION_MVP_951.md).

## Qualification 949 — Refus ETIC,pièces manquantes etarchive immuable

| Domaine | Statut | Suite |
|---|---|---|
| Refus montants,ventilation etarchive | terminé dans le périmètre testé | 3fiches Réussi,preuves réelles |
| HistoriqueHP-NEG-036 | partiel | Référence absente/reliquat préservés ;ancien NULL non reproduit |
| Autres fiches non rattachées individuellement | partiel | 8restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique949 :117réussis/0échec/0ignoré,273.75s XML. Suivi{'Réussi': 246, 'Partiel': 8, 'Bloqué (source)': 10, 'Non qualifié par fiche': 8} ;4humains Non testé. Candidat949 :seul serviceETIC corrigé,aucun SQL/frontend ni règle fiscale nouvelle,donnéesnonce uniquement. Non rejouée ;preuves antérieures distinctes. [Résultats](../recette/RESULTATS_MVP_949.md),[rattachement](../../Test/QUALIFICATION_FICHES_949.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_949.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification 947 — Déficits,déductions etrefus fiscaux exacts

| Domaine | Statut | Suite |
|---|---|---|
| Déficits,déductions etrefus fiscaux exacts | terminé dans le périmètre testé | 7fiches reliées à53tests,méthodes explicites |
| Autres fiches non rattachées individuellement | partiel | 12restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique947 :53réussis/0échec/0ignoré,210.84s XML. Suivi{'Réussi': 243, 'Partiel': 7, 'Bloqué (source)': 10, 'Non qualifié par fiche': 12} ;7humains Non testé. Produit549empreintes identique945,aucune règle nouvelle ni donnée réelle. Non rejouée ;preuves antérieures distinctes. [Résultats](../recette/RESULTATS_MVP_947.md),[rattachement](../../Test/QUALIFICATION_FICHES_947.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_947.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification945 — TVA des acomptes

| Domaine | Statut | Preuve et suite |
|---|---|---|
| Dates et états des acomptes | terminé dans le périmètre testé | Attente/rejet sans encaissement0,date effective,UIadmin/comptable etlecteur403 |
| Affectations partielles et multiples | terminé dans le périmètre testé | Montants propres à chaque facture,annulation,absence de double TVA |
| Variante annuelle encaissementHP-FIS-033 | partiel | Flux ciblé exact passé ;50opérations dans ce régime non rejouées |
| Sources historiques et déclarations déposées | bloqué pour validation finale | Dates inconnues visibles ;rejets inter-périodes etventilation comptable à qualifier |
| Production et recette utilisateur | bloqué | Aucun résultat humain ni configuration cible validés par ces tests |

Finale945 :47réussis/0échec/0ignoré,419,39s XML ;build214modules/6,55s,code0. Nouveau candidat549empreintes :2fichiers backend et1frontend changent,aucun SQL ni modèle. Suivi historique236/7/19/10,sur272 ;les anciens succès ne sont pas une réexécution globale sur945. [Résultats](../recette/RESULTATS_MVP_945.md),[sources](SOURCES_TVA_ACOMPTES_945.md),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_945.xlsx). Pas de PostgreSQL utilisateur,ni modification d'écritures historiques.

## Qualification 943 — Exports de liasse et finalisation annuelle non forcée

| Domaine | Statut | Suite |
|---|---|---|
| Exports PDF/Excel annuels | terminé dans le périmètre testé | HP-LIA-002,ordinateur/mobile,preuves réelles |
| Finalisation du cahier annuel | bloqué | HP-LIA-001,ETIC20/23,sources et confirmations manquantes ;refus409vérifié |
| Autres fiches non rattachées individuellement | partiel | 20restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique943 :7réussis/0échec/0ignoré,597.58s XML. Suivi{'Réussi': 236, 'Partiel': 6, 'Non qualifié par fiche': 20, 'Bloqué (source)': 10} ;2humains Non testé. Produit549empreintes identique931,aucune règle nouvelle ni donnée réelle. Non rejouée ;preuves antérieures distinctes. [Résultats](../recette/RESULTATS_MVP_943.md),[rattachement](../../Test/QUALIFICATION_FICHES_943.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_943.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification 941 — Cycle acomptes751 et proposition IS/CM753

| Domaine | Statut | Suite |
|---|---|---|
| Cycle acomptes751 et proposition IS/CM753 | terminé dans le périmètre testé | 16fiches reliées à114tests,méthodes explicites |
| Autres fiches non rattachées individuellement | partiel | 22restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique941 :114réussis/0échec/0ignoré,236.43s XML. Suivi{'Réussi': 235, 'Partiel': 6, 'Non qualifié par fiche': 22, 'Bloqué (source)': 9} ;16humains Non testé. Produit549empreintes identique931,aucune règle nouvelle ni donnée réelle. Non rejouée ;preuves antérieures distinctes. [Résultats](../recette/RESULTATS_MVP_941.md),[rattachement](../../Test/QUALIFICATION_FICHES_941.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_941.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification 939 — Qualification des crédits IS749

| Domaine | Statut | Suite |
|---|---|---|
| Qualification des crédits IS749 | terminé dans le périmètre testé | 8fiches reliées à70tests,méthodes explicites |
| Autres fiches non rattachées individuellement | partiel | 38restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique939 :70réussis/0échec/0ignoré,144.84s XML. Suivi{'Réussi': 219, 'Partiel': 6, 'Non qualifié par fiche': 38, 'Bloqué (source)': 9} ;8humains Non testé. Produit549empreintes identique931,aucune règle nouvelle ni donnée réelle. Non rejouée ;preuves antérieures distinctes. [Résultats](../recette/RESULTATS_MVP_939.md),[rattachement](../../Test/QUALIFICATION_FICHES_939.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_939.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification 937 — Préparation brute de taxe professionnelle761

| Domaine | Statut | Suite |
|---|---|---|
| Préparation brute de taxe professionnelle761 | terminé dans le périmètre testé | 8fiches reliées à64tests,méthodes explicites |
| Autres fiches non rattachées individuellement | partiel | 46restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique937 :64réussis/0échec/0ignoré,203.36s XML. Suivi{'Réussi': 211, 'Partiel': 6, 'Non qualifié par fiche': 46, 'Bloqué (source)': 9} ;8humains Non testé. Produit549empreintes identique931,aucune règle nouvelle ni donnée réelle. Restauration froide native du banc761 :83tables,données/schéma/ACL/séquences identiques,pièces/logos/versions relus,source préservée,cibles nonce supprimées. Ne qualifie pas la restauration de votre cible complète ou de la paie. [Résultats](../recette/RESULTATS_MVP_937.md),[rattachement](../../Test/QUALIFICATION_FICHES_937.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_937.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification 935 — Préparation des rémunérations de tiers759

| Domaine | Statut | Suite |
|---|---|---|
| Préparation des rémunérations de tiers759 | terminé dans le périmètre testé | 8fiches reliées à68tests,méthodes explicites |
| Autres fiches non rattachées individuellement | partiel | 54restantes |
| Dépôt officiel depuis cette préparation | absent de ce parcours | Ne pas assimiler aux données et exports internes |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations restantes |

Finale unique935 :68réussis/0échec/0ignoré,211.22s XML. Suivi{'Réussi': 203, 'Partiel': 6, 'Non qualifié par fiche': 54, 'Bloqué (source)': 9} ;8humains Non testé. Produit549empreintes identique931,aucune règle nouvelle ni donnée réelle. Restauration froide native du banc759 :83tables,données/schéma/ACL/séquences identiques,pièces et logos relus,source préservée,cibles nonce supprimées. Ne qualifie ni la restauration de votre cible ni le périmètre paie100tables. [Résultats](../recette/RESULTATS_MVP_935.md),[rattachement](../../Test/QUALIFICATION_FICHES_935.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_935.xlsx). Réserves de cession et Personnel/Paie inchangés ;historique ci-dessous conservé.

## Qualification individuelle du scénario755 — lot933,état courant

| Domaine | Statut | Suite |
|---|---|---|
| Préparation interne755 :CSV N/N-1,B12,CM,CSS,crédits,acomptes,revue,exports,droits et refus | terminé dans le périmètre testé | 14fiches reliées à13tests,gestes négatifs11–13 par API |
| Autres fiches de recette non rattachées individuellement | partiel | 62restantes ;commencer par tiers759 |
| Liquidation/paiement/dépôt officiel depuis cette préparation interne | absent de ce parcours | Ne pas assimiler aux propositions ou exports |
| Recette humaine,réserves métier et production | bloqué | Configuration cible,pièces et validations du responsable |

Finale unique933 :13réussis/0échec/0ignoré en113.31s XML. Suivi par fiche195Réussi/6Partiel/62Non qualifié/9Bloqué à la source,14humains755 Non testé. Aucun code produit modifié (549empreintes identiques931),aucune règle fiscale nouvelle,aucune base réelle. Dernier build931214/5,55s ;aucun build/restauration933. [Résultats](../recette/RESULTATS_MVP_933.md),[rattachement](../../Test/QUALIFICATION_FICHES_933.json),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_933.xlsx). Les réserves de cession et Personnel/Paie921 restent inchangés ;les sections suivantes conservent l’historique.

## Lecture et reprise des immobilisations931 — état courant comptabilité/facturation

| Domaine | Statut | Suite |
|---|---|---|
| Erreurs du registre/plan distinctes de zéro,reprises GET,rafraîchissement après modification | terminé dans ce périmètre | Quatre cas humains et recette cible |
| Renommage après dotation,verrou d’un vrai changement de plan,mobile quatre indicateurs | terminé pour les défauts reproduits | Contrôles métier conservés |
| Prorata,TVA/régularisation de cession,délais et justificatifs | partiel | Qualification par les sources et le responsable |
| Recette utilisateur et production | bloqué | Configuration cible et validations humaines restantes |

Finale unique931 :34tests réussis,0échec/ignoré,584.79s XML ;build214modules/5,55s. Historique des échecs intermédiaires conservé et distingué. Pannes de transport explicitement injectées dans Edge,reprises HTTP/PG nonce réelles ;aucune donnée réelle,migration ou restauration931. Quatre cas humains Non testé ;anciens résultats humains inchangés. Suivi par fiche181/6/76/9 inchangé ;IMM004 demeure Partiel. [Résultats](../recette/RESULTATS_MVP_931.md),[décision](../recette/DECISION_FACTURATION_COMPTABILITE_931.md),[guide](../recette/LECTURE_IMMOBILISATIONS_931.md). Personnel/Paie921 inchangé. Les sections suivantes conservent l’historique.

## Droits des immobilisations929 — état courant comptabilité/facturation

| Domaine | Statut | Suite |
|---|---|---|
| Commandes du registre et du plan selon rôle ;diagnostic historique consultable,corrections administrateur | terminé dans ce périmètre | Recette pilote avec les trois cas humains |
| Conservation PDF,sessions et aperçu de sortie923–927 | terminé pour les cas livrés | Versions homogènes sur copie et recette cible |
| Convention de prorata,TVA/régularisation de cession,délais et justificatifs | partiel | Sources et décisions du responsable ;aucune qualification artificielle |
| Recette utilisateur et production | bloqué | Configuration cible et validations humaines restantes |

Finale unique929 :69tests réussis,0échec/ignoré,746.27s (XML),build214modules/5,87s. L’échec de reproduction initial est conservé et distingué de la finale verte. PostgreSQL natif jetable et Edge ;aucune base réelle,migration ou restauration929. Trois cas humains Non testé ;six927 Non testé,jeu précisé pour le compte4411. Suivi par fiche inchangé181Réussi/6Partiel/76Non qualifié/9Bloqué à la source. [Résultats](../recette/RESULTATS_MVP_929.md),[décision](../recette/DECISION_FACTURATION_COMPTABILITE_929.md),[guide](../recette/DROITS_IMMOBILISATIONS_929.md). Personnel/Paie921 inchangé. Les sections suivantes conservent l’historique.

## Aperçu des sorties927 — état courant comptabilité/facturation

| Domaine | Statut | Suite |
|---|---|---|
| Aperçu partagé cession/rebut,lecture sans mutation métier,contrôle de péremption | terminé dans ce périmètre | Recette pilote avec les six cas humains |
| Convention de prorata et TVA/régularisation de cession IMM004 | partiel | Qualification par les sources et le responsable ;aucun montant forcé |
| Copies PDF et sessions923/925 | terminé pour les cas livrés | Installation homogène sur copie et recette cible |
| Recette utilisateur et mise en production | bloqué | Configuration cible et validations humaines restantes |

Finale unique927 :62tests réussis,0échec/ignoré,30avertissements,539,33s ;build214modules/4,91s. PostgreSQL natif jetable et Edge,aucune base réelle ;aucune nouvelle migration ni restauration927. Six cas humains Non testé. Le suivi par fiche reste181Réussi,6Partiel,76Non qualifié individuellement,9Bloqué à la source :IMM004 demeure Partiel. [Résultats](../recette/RESULTATS_MVP_927.md),[décision](../recette/DECISION_FACTURATION_COMPTABILITE_927.md),[guide](../recette/APERCU_SORTIES_IMMOBILISATIONS_927.md). Personnel/Paie921 inchangé. Les sections suivantes conservent l’historique.

## Sessions et qualification du MVP925 — état courant comptabilité/facturation

| Domaine | Statut | Suite |
|---|---|---|
| Anciens JWT sans version refusés,connexion/bascule et invalidation du mot de passe | terminé dans ce périmètre | Reconnexion unique des anciens navigateurs et recette cible |
| Conservation PDF et navigation Journal923 | terminé pour les cas livrés | Migration125 sur copie,recette humaine |
| Cessions,délais et justificatifs historiques | partiel | Sources/décisions métier et réserves de la décision925 |
| Recette utilisateur et production | bloqué | Configuration réelle et validations humaines restantes |

Qualification925 :109cas distincts finalement réussis en union de la finale et de la reprise835 ;pas une campagne unique entièrement verte. Les deux premières attentesUI835 et leur correction sont conservées. Frontend inchangé,dernier build923214modules/7.21s ;restauration84tables. [Résultats](../recette/RESULTATS_MVP_925.md),[décision](../recette/DECISION_FACTURATION_COMPTABILITE_925.md). Douze nouveaux cas humains923/925 Non testé ;anciens résultats préservés. Les états Personnel/Paie921 ci-dessous restent inchangés.

## Conservation individuelle des factures923 — état courant du MVP comptabilité/facturation

| Domaine | Statut | Suite |
|---|---|---|
| FAC013 :copie interne figée d’une vente validée,PDF/logo/empreinte/audit et relecture | terminé dans ce périmètre | Migration125 sur copie et recette humaine |
| Validation en lot Journal :retour intégré et navigation immédiate | terminé pour la cause reproduite | Confirmation et montants conservés |
| Document fournisseur original et archivage légal certifié | absent de ce parcours | Ne pas assimiler à la copie interne |
| Recette utilisateur et production | bloqué | Configuration cible et réserves de la décision923 |

Finale48cas réussis,build214modules/7.21s,restauration84tables sur seconde cible isolée. FAC013 qualifié automatiquement ;181réussis,6partiels,76non qualifiés individuellement,9bloqués à la source dans le suivi documentaire hérité869. Huit nouveaux cas humains Non testé. [Résultats](../recette/RESULTATS_MVP_923.md),[décision](../recette/DECISION_FACTURATION_COMPTABILITE_923.md). Les états Personnel/Paie921 ci-dessous restent inchangés ;la paie définitive n’est pas validée par ce lot.

## RNI mensuel préparatoire921 — état courant

| Domaine | Statut | Suite |
|---|---|---|
| Sources fiscales connectées, RNI déclaré, contrôles immuables | terminé dans ce périmètre | Migration124 et recette sur copie |
| Équivalence du barème annuel/12 | terminé comme contrôle mathématique | Ne constitue pas une retenue liquidée |
| Liquidation mensuelle, arrondis et régularisations | partiel | Politique réglementaire complète à qualifier |
| Net, bulletins, paiements et OD de paie | absent | Lots suivants |
| Recette utilisateur et production | bloqué |153cas humains Non testé |

Finale188cas distincts réussis, build213modules/9.57s, restauration100tables. [Résultats](../personnel-paie/RESULTATS_PAIE_921.md). Les sections suivantes sont historiques ; aucune retenue effective ni paiement n’est confirmé par ce nouveau contrôle.

## Rattachement des revenus919 — état courant

| Domaine | Statut | Suite |
|---|---|---|
| Périodes de référence et versements déclarés, workflow et snapshots | terminé dans ce périmètre | Migration123 et recette sur copie |
| Calcul périodiqueIR et régularisations | partiel | Règles et arrondis à qualifier ; faits désormais conservés |
| Net,bullletins,paiements etOD de paie | absent | Lots suivants |
| Recette utilisateur etproduction | bloqué |147cas humains Non testé |

Finale191cas distincts réussis, build212modules/6.41s,restauration99tables. [Résultats](../personnel-paie/RESULTATS_PAIE_919.md). Les sections suivantes sont historiques ; la nouvelle collecte ne confirme aucun paiement et ne recalcule aucun ancienIR.

## Documents du contrôle annuel917 — état courant

| Domaine | Statut | Suite |
|---|---|---|
| Chaîne des préparations mensuelles au contrôle IR annuel | terminé dans ce périmètre | Général2026, sources complètes et confirmations |
| ExportsPDF/Excel du contrôle sourcé, logo et audit | terminé dans ce périmètre | Recette sur copie etvotreExcel |
| Retenue mensuelle et régularisation | partiel | Périodicité, faits et doctrine à qualifier |
| Net,bulletins,paiements etOD | absent | Lots suivants |
| Recette utilisateur etproduction | bloqué | Copie isolée etrecette àvalider |

Qualification917 :171cas distincts réussis, {'unitaires_source': 134, 'API_SQL_restauration_PostgreSQL_natif_isole': 27, 'navigateur_Edge_API_PG_isole': 10}. Build212modules/6.45s,restauration99tables ;141cas humains Non testé. [Résultats](../personnel-paie/RESULTATS_PAIE_917.md),[guide](../personnel-paie/DOCUMENTS_IR_ANNUEL_917.md). Les sections suivantes sont historiques ;aucune paie définitive produite.

## IR annuel depuis un RNI constitué915 — état courant

| Domaine | Statut | Suite |
|---|---|---|
| Chaîne préparations mensuelles → frais annuels → contrôleIR annuel | terminé dans ce périmètre | Général2026, source complète et confirmations requises |
| RNI source exact, base annuelle arrondie, provenance immuable | terminé | Migration122 sur copie à valider |
| Retenue mensuelle et régularisation | partiel | Doctrine, périodicité et faits à qualifier |
| Net,bulletins,paiements etOD | absent | Lots suivants |
| Recette utilisateur etproduction | bloqué | Copie isolée etrecette àvalider |

Finale915 :215cas distincts réussis, {'unitaires_source': 163, 'API_SQL_restauration_PostgreSQL_natif_isole': 42, 'navigateur_Edge_API_PG_isole': 10}. Build212modules/6.79s,restauration99tables ;135cas humains Non testé. [Résultats](../personnel-paie/RESULTATS_PAIE_915.md),[guide](../personnel-paie/IR_ANNUEL_SOURCE_915.md). Les sections suivantes sont historiques ;aucune mensualisation déduite du contrôleannuel.

## Cumuls et frais annuels913 — état courant

| Domaine | Statut | Suite |
|---|---|---|
| Cumuls des préparations choisies et frais annuels59-I-A | terminé dans ce périmètre | Année complète2026 et cadre confirmé |
| RNI annuel arithmétique après autres déductions déclarées | terminé dans ce périmètre | ContrôleIR sourcé àrelier |
| RNI et retenue mensuels, entrées/sorties et cas particuliers | partiel | Doctrine et faits complémentaires nécessaires |
| Net,bulletins,paiements etOD | absent | Lots suivants |
| Recette utilisateur etproduction | bloqué | Copie isolée etrecette àvalider |

Finale913 :176cas distincts réussis, {'unitaires_source': 134, 'API_SQL_restauration_PostgreSQL_natif_isole': 36, 'navigateur_Edge_API_PG_isole': 6}. Build211modules/5.89s,restauration98tables ;129cas humains Non testé. [Résultats](../personnel-paie/RESULTATS_PAIE_913.md),[guide](../personnel-paie/CUMULS_FRAIS_ANNUELS_913.md). Les sections suivantes sont historiques ;aucune mensualisation déduite du contrôleannuel.

## Comparaison annuelle911 — état courant

| Domaine | Statut | Limite |
|---|---|---|
| Comparaison après arrondi de base annuelle2026 (CGI167) | terminé | Contrôle annuel uniquement,sans versement |
| Qualifications etbases fiscales907/909 | terminé dans ce périmètre | RNI intégré non déterminé |
| Frais,cumuls etretenue mensuelle | partiel | Àqualifier etdévelopper avant net/bulletins |
| Net,bulletins,paiements etOD | absent | Lots suivants |
| Recette utilisateur etproduction | bloqué | Installation surcopie etrecette àeffectuer |

Finale connexe911 :131cas distincts réussis, {'unitaires_source': 98, 'API_SQL_restauration_PostgreSQL_natif_isole': 27, 'navigateur_Edge_API_PG_isole': 6}. Build210modules/9.46s,restauration96tables ;123cas humains Non testé. Anciens snapshots901 etclés de reprise conservés. [Résultats](../personnel-paie/RESULTATS_PAIE_911.md),[guide](../personnel-paie/ARRONDI_BASE_ANNUELLE_911.md). Les sections suivantes sont historiques.

## Bases fiscales909 — état courant

| Domaine | Statut | Suite |
|---|---|---|
| Qualifications fiscales séparées907 et préparation des bases909 | terminé | Recette humaine sur copie |
| Liaison brut/social,preuves,snapshots et contrôle des sources | terminé | Conserver les anciennes versions |
| Frais professionnels,autres déductions,cumuls et retenue mensuelle | partiel | Qualification des règles et calcul intégré |
| Net,bulletins,paiements etOD de paie | absent | Lots suivants du master |
| Recette utilisateur et production | bloqué | Installation sur copie et exploitation à valider |

Finale connexe909 :388cas distincts réussis, {'unitaires_source': 280, 'API_SQL_restauration_PostgreSQL_natif_isole': 100, 'navigateur_Edge_API_PG_isole': 8}. Build210modules/6.4s,restauration96tables ;117cas humains Non testé. [Résultats](../personnel-paie/RESULTATS_PAIE_909.md),[bilan](../personnel-paie/BILAN_SESSION_PAIE_907_909.md),[suite](../personnel-paie/REPRISE_PAIE_APRES_BASES_909.md). Les sections suivantes sont historiques ;aucun RNI définitif,IRmensuel ou net déterminé par ce lot.

## Qualifications fiscales907 — état courant

| Domaine | Statut | Limite / suite |
|---|---|---|
| Personnel, catalogue/variables, brut et social pédagogique | terminé | Recette humaine à effectuer |
| Frais professionnels : qualification de base par rubrique | terminé | Ne calcule pas la déduction forfaitaire |
| Déductibilité IR : qualification de la part salariale par branche | terminé | Aucun automatisme depuis le calcul social |
| Assiette fiscale intégrée et retenue mensuelle | partiel | Liaison aux sources, frais, cumuls et arrondis à poursuivre |
| Net, bulletins, paiements et OD de paie | absent | Lots suivants du master |
| Recette utilisateur et production | bloqué | Installation sur copie et exploitation à valider |

Qualification :372cas distincts réussis après correction des scripts, {'navigateur_Edge_API_PG_isole': 24, 'API_SQL_restauration_PostgreSQL_natif_isole': 109, 'unitaires_source': 239}. Les campagnes sont distinguées dans [les résultats](../personnel-paie/RESULTATS_PAIE_907.md). Build209modules/8.1s, restauration95tables.111cas humains Non testé. Les sections suivantes sont historiques.

## Recette API annuelle905 — produit901 inchangé

Douze mois2026 de variables/brut/social fictifs effectivement préparés etcomparés,sommes des lignes arrondies conservées etjanvierstable aprèsles autres mois.1nouveau cas natif isolé réussi42.57s ;328cas distincts enunion avec les327901,221unitaires/85API-SQL-restauration/22Edge. Aucune nouvellecampagnecomplète328 revendiquée.519sourcesproduit inchangées,dernierbuild208/10.52s etrestauration95tables. [Résultats](../personnel-paie/RESULTATS_ANNEE_SOCIALE_905.md),[bilan](../personnel-paie/BILAN_SESSION_PAIE_897_903.md).105cas humains Non testé,IRmensuel/net/bulletins etproduction àpoursuivre ;statutsfonctionnels903 inchangés.

## Consolidation903 — produit901 inchangé

Les lots897/899/901 sont livrés :référentiel social, calcul social connecté et contrôle annuel IR. Dernière qualification327cas distincts,build208modules10.52s,restauration95tables ; aucune nouvelle réussite produit inventée pour cette consolidation documentaire.519empreintes produit et115anciens SQL vérifiés inchangés ;19archives antérieures SHA/CRC contrôlées.

Vérification documentaire réellement exécutée :7ensemblesPDF/Excel,105cas humains tous Non testé,60liens locaux valides ; aucun classeur modifié par le vérificateur. [Bilan](../personnel-paie/BILAN_SESSION_PAIE_897_903.md), [installation surcopie](../personnel-paie/INSTALLATION_COPIE_PAIE_116_118.md), [preuve](../../Test/PREUVE_SESSION_PAIE_903.json), [reprise3C2](../personnel-paie/REPRISE_IR_MENSUEL_3C2_903.md). Paie complète,recette utilisateur etproduction restent nonvalidées. Les sections suivantes sont historiques.

## Paie — contrôle annuel IR901, état courant

05 · Fiscalité salariale est accessible pour le contrôle annuel du barème général2026 sur RNI déclaré. Calcul exact progressif, réduction familiale confirmée sans déduction depuis l’état civil, inconnus explicites, sources et empreintes conservées. Aucun salaire multiplié par12, arrondi de liquidation ou net inventé.

| Domaine courant | Statut | Suite |
|---|---|---|
| Personnel, catalogue/variables, brut, référentiel et social pédagogique | terminé | Recette humaine sur copie |
| 3C1 contrôle annuel du barème général IR, API/UI et snapshots | terminé | Contrôle arithmétique uniquement, avant arrondis |
| 3B complet : qualification et cas sociaux complexes | partiel | Textes/régimes, cumuls et cas particuliers à qualifier |
| 3C complet : assiette et retenues mensuelles reliées aux sources | partiel | Frais, cotisations déductibles, cumuls et régularisations |
| Net, bulletins, paiement et comptabilisation de paie | absent | Lots suivants du master |
| Recette utilisateur et production | bloqué | Installation sur copie et exploitation à valider |

Qualification901 : **327cas distincts réussis**, {'navigateur_Edge_API_PG_isole': 22, 'API_SQL_restauration_PostgreSQL_natif_isole': 84, 'unitaires_source': 221}. Build208modules/10.52s code0 ; restauration native95tables. [Résultats](../personnel-paie/RESULTATS_PAIE_901.md), [guide et105cas humains](../personnel-paie/MODE_EMPLOI_PERSONNEL_PAIE.md), [sources](../personnel-paie/SOURCES_IR_ANNUEL_901.md). Aucune base réelle. Les sections suivantes sont historiques ; la paie complète et la production ne sont pas validées.

## Paie — calcul social899, état courant

Le parcours03→04 relie un brut conservé aux simulations sociales par salarié et branche. Assiettes CNSS/AMO distinctes, bases/éligibilité déclarées, exclusions avant plafonds, cumuls mensuels par rubrique, taux et forfaits exacts, snapshots immuables et idempotence. Sources courantes différentes, informations manquantes et unités non calculables restent bloquantes ; aucun zéro ou brut de secours.

| Domaine courant | Statut | Suite |
|---|---|---|
| Personnel, catalogue/variables, brut et référentiel social | terminé | Recette sur copie |
| 3B2 calcul social pédagogique connecté, API/UI et snapshots | terminé | Recette humaine selon899 |
| Lot3B complet : règles réglementaires et cas complexes | partiel | Qualifier textes/éligibilité, cumuls et cas particuliers |
| 3C moteur fiscal intégré et net, bulletins et lots suivants | absent | Continuer le master |
| Recette utilisateur et production | bloqué | Installation sur copie, conformité métier et exploitation à valider |

Qualification899 : **277cas distincts réussis**, {'navigateur_Edge_API_PG_isole': 20, 'API_SQL_restauration_PostgreSQL_natif_isole': 74, 'unitaires_source': 183}. Build207modules/5.79s code0 ; restauration native94tables. [Résultats](../personnel-paie/RESULTATS_PAIE_899.md), [guide et99cas humains](../personnel-paie/MODE_EMPLOI_PERSONNEL_PAIE.md), [preuves](../../Test/PREUVE_PAIE_899.json). Aucun PostgreSQL réel ni données comptables modifiés. Les sections suivantes sont historiques.

## Paie — référentiel social897, état courant

**04 · Charges sociales** est accessible : branches par société/régime, parts salariale et patronale exactes, assiettes/plafonds propres, périodes et sources, qualification dédiée, versions immuables et décision indépendante. Le contrôle de composants couvre les intervalles entiers et bloque les doubles couvertures dans un même régime. Aucun taux préchargé ni régime attribué automatiquement.

| Domaine courant | Statut | Suite |
|---|---|---|
| Personnel, coffre/banque, catalogue et variables | terminé | Recette humaine sur copie |
| 3A campagnes normales et brut pédagogique | terminé | Mois complets ; aucune paie définitive |
| 3B1 référentiel social versionné, API et formulaires04 | terminé | Qualifier les paramètres et preuves réels |
| 3B calcul social connecté au brut | partiel | Référentiel prêt ; moteur et snapshots à suivre |
| 3C IR/net, cas complexes et bulletins | absent | Continuer le master |
| Recette utilisateur et production | bloqué | Installation sur copie et exploitation à valider |

Qualification897 : **230 cas distincts réussis**, {'API_SQL_restauration_PostgreSQL_natif_isole': 60, 'navigateur_Edge_API_PG_isole': 18, 'unitaires_source': 152}. Build206 modules/8.96s code0 ; restauration native93 tables. Aucun PostgreSQL réel. [Résultats](../personnel-paie/RESULTATS_PAIE_897.md), [guide et93cas humains](../personnel-paie/MODE_EMPLOI_PERSONNEL_PAIE.md), [preuves](../../Test/PREUVE_PAIE_897.json). Les sections suivantes conservent les états historiques ; facturation/comptabilité inchangées.

## Consolidation de session895 — produit893 inchangé

Les lots889/891/893 sont livrés etqualifiés :catalogue,variables mensuelles etsimulation du brut. [Bilan de session](../personnel-paie/BILAN_SESSION_PAIE_20261028.md),[mode d'emploi et87cas humains](../personnel-paie/MODE_EMPLOI_PERSONNEL_PAIE.md). La consolidation895 ajoute uniquement la préparation3B etles livrables de reprise ;elle n'ajoute ni taux,cotisation,IR,net oubulletin.

Les502empreintes produit sont celles de893 ;dernière qualification171cas distincts etbuild205modules,restaurations91/85tables. Aucun nouveau test produit n'est inventé pour cette étape documentaire. Recette utilisateur,installation surcopie etproduction restent àvalider. [Prochaine sous-étape3B](../personnel-paie/PREPARATION_COTISATIONS_3B_895.md) :référentiel social versionné,preuves desbranches etdates,calculs séparés parassiette ;ne pas transformer les simulations historiques enpaie définitive. Les sections suivantes gardent les états datés.

## Paie — campagnes et brut 893, état courant

La rubrique03 est accessible pour les campagnes normales et les snapshots de simulation du brut. Bases mensuelles et gains approuvés sont conservés avec leurs sources ;anomalies et totaux inconnus restent explicites. Aucun net, cotisation, IR ou bulletin n'est présumé. Les sections891 et antérieures restent historiques.

| Domaine courant | Statut | Suite |
|---|---|---|
| Personnel, coffre/banque et catalogue/variables disponibles | terminé | Recette humaine sur copie |
| 3A : campagnes normales, snapshots/idempotence et brut pédagogique sur mois complet | terminé | Recette humaine ;aucune approbation de paie définitive |
| Lot2 complet : règles complexes d'exonération et cumuls réglementaires | partiel | Qualifier les textes et traitements avant liquidation |
| 3B/3C : cotisations par branche, IR et net | absent | Prochain chantier du master |
| Cas complexes, bulletins, verrouillage et approbation définitive | absent | Sous-étapes3D/3E puis lots4–7 |
| Recette utilisateur et production | bloqué | Installation sur copie, tests métier et exploitation à valider |

Qualification893 : **171 cas distincts réussis**,104unitaires/source,51API/SQL/restaurationPGnatifsisolés,16Edge/API/PG. Build205modules code0/5,82s. Restauration native91tables et contre-régression coffre85tables ;vraie altération de prédicat d'index détectée. Le premier échec de comparaison textuelle et sa correction sont conservés dans [les résultats](../personnel-paie/RESULTATS_PAIE_893.md). Aucun PostgreSQL utilisateur. [Mode d'emploi et cahiers](../personnel-paie/MODE_EMPLOI_PERSONNEL_PAIE.md), [preuves](../../Test/PREUVE_PAIE_893.json). Facturation/comptabilité inchangées.

## Paie — variables 891, état courant

Les variables mensuelles et leurs formulaires sont livrés, avec conditions approuvées à date, source/pièces référencées, montants exacts ou quantité×taux, snapshots, doublons/récurrences/non-cumuls, soumission, décision indépendante et historique. Aucun paiement ni écritures générés. Les sections889 et antérieures sont historiques.

| Domaine courant | Statut | Suite |
|---|---|---|
| Catalogue et versions, interface, qualification réglementaire dédiée | terminé | Recette sur copie selon889 |
| Saisie et approbation des variables, contrôles des sources et non-cumuls | terminé | Recette sur copie selon891 ;approbation des pièces humaine |
| Lot2 complet : règles réglementaires complexes et intégration aux campagnes | partiel | Pourcentages/SMIG/cumuls conditionnels et verrouillage des périodes à compléter |
| Campagnes, cotisations/IR et bulletins | absent | Continuer les sous-étapes du lot3 |
| Production | bloqué | Installation113/114 et recette humaine/exploitation à valider |

Qualification891 : **98 cas distincts finalement réussis**, 54unitaires/source,40API/SQLPGnatifsisolés,4Edge/API/PG. Deux anciens échecs de sélecteurs sont remplacés par les deux E2E corrigés réussis ;chronologie explicite dans [les résultats](../personnel-paie/RESULTATS_PAIE_891.md). Build204modules code0/8,36s. Aucun PostgreSQL utilisateur. [Guide](../personnel-paie/VARIABLES_PAIE_891.md), [PDF10cas](../personnel-paie/RECETTE_VARIABLES_PAIE_891.pdf), [Excel](../personnel-paie/SUIVI_VARIABLES_PAIE_891.xlsx), [preuves](../../Test/PREUVE_PAIE_891.json). Statuts humains Non testé ;facturation/comptabilité inchangées.

## Paie — catalogue 889, état courant du lot 2

Le catalogue versionné et son interface sont livrés dans **02 · Éléments de paie**, avec séparation IR/CNSS/AMO, dates, conditions, preuves déclarées, types de justificatifs et incompatibilités. L'approbation est indépendante ; qualifier des règles déclarées validées nécessite une capacité réglementaire dédiée, sans attribution automatique. Aucun taux ou plafond légal nouveau n'est préchargé.

| Domaine | Statut de couverture | Limite |
|---|---|---|
| 2A : catalogue, versions, déclarations de règles et contrôle de qualification | terminé | Preuves et interprétation à vérifier par l'expert habilité ;aucune certification automatique |
| 2B : formulaires du catalogue et aperçu arithmétique séparé | terminé | Aperçu pédagogique à l'opération ;pas de cumul supposé |
| Lot 2 complet : variables mensuelles et contrôle des preuves/non-cumuls | partiel | Prochaine sous-étape891 |
| Campagnes, moteur cotisations/IR, bulletins des lots suivants | absent | Développement à poursuivre dans l'ordre du master |
| Recette utilisateur et mise en production | bloqué | Migration113 sur copie,habilitation expert et recette à effectuer |

Les tests et leur chronologie sont consignés dans [la preuve889](../../Test/PREUVE_PAIE_889.json). [Guide](../personnel-paie/CATALOGUE_PAIE_889.md), [complément PDF12cas](../personnel-paie/RECETTE_CATALOGUE_PAIE_889.pdf), [Excel](../personnel-paie/SUIVI_CATALOGUE_PAIE_889.xlsx). Les statuts Personnel887 et comptabilité/facturation restent inchangés ;les sections suivantes sont historiques.

## Personnel / RH — état courant 887

Le coffre et la banque sous workflow sont désormais livrés : interfaces, chiffrement authentifié à portée société/salarié, clés externes sauvegardées/versionnées, pièces privées, consultation bancaire auditée et approbation indépendante. Le socle 885 ci-dessous reste historique ; son interface et la banque ont été complétées en 887. Aucune formule de paie ou écriture comptable administrative ajoutée.

| Périmètre courant | Statut de couverture | Vérification restante |
|---|---|---|
| Personnel disponible : dossiers, contrats/salaires, régimes déclarés, sorties, historique, accès | terminé | Recette humaine sur copie |
| Coffre privé, banque versionnée, UI et configuration explicite | terminé | Clés, ACL et procédures d'exploitation réelles à configurer |
| Sauvegarde/restauration technique isolée du coffre et de la banque | terminé | 85 tables restaurées ; infrastructure réelle à qualifier |
| Nouveau moteur de paie, déclarations et paiements des lots suivants | absent | Lots distincts du cahier des charges |
| Mise en production | bloqué | Installation sur copie, recette humaine et exploitation à valider |

**406 cas distincts réussis** : 166 unitaires/source/outillage, 222 API/SQL/restauration PostgreSQL natif isolé et 18 Edge/API/PG. Build final : 202 modules, code 0, 16,27 s. Aucun PostgreSQL réel contacté. Cahier consolidé : 59 cas, PDF 29 pages et Excel 11 feuilles ; tous les statuts humains restent Non testé. La qualification automatisée ne valide ni la recette utilisateur ni la production.

[Guide](../personnel-paie/COFFRE_BANQUE_RH_887.md), [résultats et limites](../personnel-paie/RESULTATS_RH_887.md), [cahier](../personnel-paie/CAHIER_RECETTE_PERSONNEL_HISABPRO_887.pdf), [suivi Excel](../personnel-paie/SUIVI_RECETTE_PERSONNEL_887.xlsx). Les statuts des modules comptabilité/facturation restent inchangés ; les sections suivantes conservent les états historiques datés.

## Coffre RH —885 (socle API)

Socle **terminé dans ce périmètre** :clés externes versionnées,chiffrement authentifié lié société/salarié/pièce,déclaration explicite de politique,pièces privées bornées à4Mio,audit etimmutabilité. Collecte fermée sans clés/politique/capacités/protection.111 additive,rejouée2fois,aucune ancienne donnée modifiée. Utilitaire de sauvegarde/rotation de cléactive,sans affichage secret ;pas de réchiffrement historique ni purge implicite.

**45cas réussis** (29unitaires/source/outillage,16API-SQLPGnatifsisolés),9Python compilés ;frontend inchangé,pasdebuild885. Erreurs initiales du harnaisWindows documentées,sans succès fictif. Aucune clé/base réelle. Interface etbanque sousworkflow encore **partielles**,àlivrer887. ACL,hébergement etpolitique réelle restent àrenseigner ;production nonvalidée. [Guide etpreuves](../personnel-paie/COFFRE_RH_885.md). Statuts précédents comptabilité/facturation conservés.

## Personnel / RH —883

**Disponible et qualifié** :date d’entrée connue distincte du contrat,régimes AMO/retraite/mutuelle déclarés dans les versions approuvées,masques des valeurs/motifs/références etprotection desversions.110 additive,sans renseignement historique automatique. Reprise limitée au contrat applicable ;CDD expiré ne présume pas le régime suivant. Nouveau contrat refusé s’il détacherait une rémunération future approuvée ;aucun montant/date réécrit.

**373cas distincts réussis** :152unitaires/source,205API-SQL-bootstrapPGnatifsisolés,16Edge/API/PG ;5Python compilés ;build201modulescode0,4,66s.28qualifications finales comprennent17API877 rejouées qui remplacent leurs résultats dans les362nonrégressions ;chronologie et tentatives échouées explicites dans le rapport. PDFconsolidé20pages/43cas,Excel9feuilles/43statuts humains Non testé,jeu chiffré complet de saisie.

| Périmètre | Statut | Suite |
|---|---|---|
| Personnel disponible :dossiers,contrats/salaires,approbation,historique,sorties,accès,UI etrégimes déclarés | terminé | Recette utilisateur à effectuer |
| Lot1 intégral :RIB/pièces sécurisées | bloqué | D05 :hébergement/rotation/conservation desclés etpièces àarrêter avant collecte |
| Nouveau moteur de paie | absent | Lots2–7 distincts ;aucune formule nouvelle livrée ici |
| PostgreSQL cible etproduction | bloqué | Migration sur copie,recette etexploitation àvalider ;base réelle noncontactée |

[Guide/limitesD05](../personnel-paie/REGIMES_ET_LIMITES_RH_883.md),[résultats etpreuves](../personnel-paie/RESULTATS_RH_883.md),[cahier43cas](../personnel-paie/CAHIER_RECETTE_PERSONNEL_HISABPRO_883.pdf),[classeur](../personnel-paie/SUIVI_RECETTE_PERSONNEL_883.xlsx). Les entrées précédentes restent historiques ;la limite profil exclusivement Personnel a été levée en881 etlesrégimes sont désormais disponibles. Statuts comptabilité/facturation conservés.

## Personnel seul —881

**Profil dédié terminé**,sans rôle comptable ajouté :liste fermée de chemins/méthodes côté serveur,contexte minimal et shell sans fournisseurs de données financières. Migration109 rejouable,sans attribution ni modification de compte. Rôle local principal/invité relu par requête ;capacités,protection,module et séparation des acteurs conservés. Mot de passe personnel accessible sans ouvrir Paramètres.

**362cas distincts réussis** :152unitaires/source,196API-SQL-bootstrapPGnatifsisolés,14Edge/API/PG ;11Python compilés ;build201modules code0,4,89s. Essais initiaux et échecs corrigés conservés séparément ;voir chronologie des campagnes dans le rapport. Recette humaine37cas/8feuilles,complémentPDF3pages ;aucun statut humain réussi par avance.

Lot1 intégral reste **partiel** pour RIB/pièces/clés/conservation(D05) et régimes sociaux à compléter ;profil exclusivement Personnel désormais livré. Nouveau moteur paie toujours absent ;production bloquée sur prérequis de déploiement/recette,aucune base réelle contactée. Déployer881 partout avant attribution du nouveau rôle ;ne pas revenir à un ancien backend avec ce rôle actif. [Guide](../personnel-paie/PROFIL_PERSONNEL_881.md),[résultats](../personnel-paie/RESULTATS_PROFIL_PERSONNEL_881.md),[suivi37cas](../personnel-paie/SUIVI_RECETTE_PERSONNEL_881.xlsx).

## Personnel / RH — interfaces et intégration879 qualifiées

Pilote 1A/1B/1C : **terminé dans son périmètre documenté**. Liste, création/reprise, coordonnées facultatives, contrat/salaire versionnés, décisions indépendantes, sorties, historique, habilitations et sidebar neuf rubriques (huit À venir). Masques, réseau interrompu, révision concurrente et changement de société contrôlés. Migration108 permet le rejet tracé après désactivation du préparateur ; approbation toujours refusée. Anciennes migrations inchangées.

**277 cas distincts réussis** :124unitaires/source,142API-SQL-bootstrapPGnatifsisolés,11parcoursEdge/API/PG ;sixPython compilés ;build200modules code0,6,71s. Données/écritures réelles non contactées. PDF17pages,29cas,Excel7feuilles et jeu chiffré livrés ;statuts humains tous Non testé.

| Périmètre | Statut | Limite explicite |
|---|---|---|
| Pilote Personnel : dossiers, conditions, approbations, UI et intégration | terminé | Recette humaine encore à effectuer |
| Lot1 intégral du master / déploiement général | partiel | Profil Personnel seul, RIB/chiffrement, pièces sécurisées et régimes sociaux à compléter/cadrer avant usage |
| Nouveau moteur de paie et rubriques02–09 | absent | Lots2–7, hors livraison879 ; ancien espace conservé |
| Mise en production et validation PostgreSQL cible | bloqué | Installation sur copie, recette humaine et exigences d’exploitation restantes ; aucune validation officielle revendiquée |

[Guide et limites](../personnel-paie/LOT1BC_UTILISATION_RECETTE_879.md),[résultats et preuves](../personnel-paie/LOT1BC_RESULTATS_879.md),[cahierPDF](../personnel-paie/CAHIER_RECETTE_PERSONNEL_HISABPRO_879.pdf),[suiviExcel](../personnel-paie/SUIVI_RECETTE_PERSONNEL_879.xlsx). L’entrée intermédiaire ci-dessous reste historique et ne décrit plus la qualification actuelle. Statuts globaux comptabilité/facturation conservés.

## Personnel & Paie — 1B intermédiaire (879)

Interface/sidebar écrites :liste,fiche,création/reprise,propositions/décisions,historique ethabilitations ;neufrubriques donthuitÀvenir,anciencnssconservé. Endpointoptions de saisie etnomsd'auteurs ajoutés enlecture. **Statut :partiel,nonqualifié navigateur.** Build200modules12,19s code0 et2Python compilés ;aucunE2E/API879exécuté,limite de session atteinte. Reprise8772passantérieure auxmodifications,non utilisée pourvalider879. Aucune base réelle ni migrationmodifiée. Anciensstatutsglobaux conservés. [Point de reprise](../personnel-paie/LOT1B_REPRISE_INTERMEDIAIRE_879.md).

## Personnel & Paie — 1A.3 (877)

Backend de dossiers et décisions livré : migration107 additive, brouillons sans salaire fictif, reprise explicite, propositions typées, soumission, approbation/rejet indépendants, montants exacts à date, demandes/historique masqués, révisions/concurrence/rollback et sorties. Anciennes mutations protégées, aucun mouvement comptable ; écriture définitive témoin conservée. **262 cas distincts réussis** :124unitaires/source,134API-SQL-bootstrapPGnatifsisolés,4Edge/API/PG ;10Python compilés. Frontend inchangé,build non relancé. Migration cible non installée ;interfaces/sidebar1B etrecette1C à suivre. Personnel & Paie global reste **partiel**,moteur et production non validés ;anciennes fiches globales conservées. [GuideAPI](../personnel-paie/LOT1A3_API_PERSONNEL_877.md),[résultats](../personnel-paie/LOT1A3_RESULTATS_877.md).

## Personnel & Paie — 1A.2 (875)

Fondation backend livrée : migration106 additive (cinq tables, deux vues), contrats/rémunérations versionnés avec montants exacts et périodes dérivées, demandes et événements protégés, diagnostic API administrateur sans réparation ni reprise implicite. Nouvelles structures en lecture seule pour le runtime ; le circuit de mutations/approbations reste à livrer en1A.3. **212 cas distincts réussis** :93unitaires/source,115API-SQL-bootstrapPGnatifsisolés,4Edge/API/PG. SeptPython compilés ;frontend inchangé,build non relancé. Aucune migration installée sur base utilisateur. Lot1A complet **partiel** ;sidebar1B et paie non livrées. Statuts globaux et anciennes fiches de recette conservés. [Guide](../personnel-paie/LOT1A2_DOSSIERS_VERSIONS_875.md),[résultats](../personnel-paie/LOT1A2_RESULTATS_875.md).

## Personnel & Paie — 1A.1 (873)

Socle de consultation protégée activable explicitement par société :quatre capacités de lecture,délégation/révocationadmin,masquesAPI/ancienschemins,blocagedesanciennesmutations aprèsactivation,purge du détailaprèsrafraîchissement desdroits. Sansactivation,modehistorique conservé. Migration105 additive,aucunedonnéecomptableréellemodifiée.187casdistincts qualifiés (81unitaires/source,95API-SQLPGisolés,11Edge/API/PG),build0. Lot1Acomplet encorepartiel :versions de dossiers/salaires etapprobations à suivre,sidebar1B. Statutsglobaux et180fichesdu suivi869 conservés. [Guide](../personnel-paie/LOT1A1_HABILITATIONS_873.md),[résultats](../personnel-paie/LOT1A1_RESULTATS_873.md).

## Personnel & Paie — Lot 0 (871)

Audit du master27/10/2026 :cartographie réelle19tablesORM/14routes/49sources,architecture/RBAC25capacités/planmigrations et1A proposés. Neufrubriques prévues dans la sidebar,sans écransnouveaux livrés.241cas exécutés réussis :105unitaires/schéma,127API-SQL-bootstrapPGnatifsisolés,9Edge/API/PG ;build0. Les3caractérisations constatent des écarts au master (doublons,salaireécrasé,lecturesensible),pas une validation du futur module. Aucunproduit ni migration modifié ;statutsfonctionnels globaux et180fiches du suivi869 inchangés. [Audit](../personnel-paie/LOT0_AUDIT_ARCHITECTURE.md),[synthèsePDF](../personnel-paie/LOT0_SYNTHESE.pdf),[plan1A](../personnel-paie/LOT1A_PLAN.md).

## Cahier869

NEG009 qualifié Edge1440/390/API/PG :F-CONTROLE,02 et002 même jour/TTC240,articleS-ACH/6125 ;FEC2pièces/6lignes D=C480,ETIC B7deux factures/480,sansécart ni reliquat. Lectures sansmutation ni réparation.2parcours finaux réussis ;candidat865 conservé. [Rapport](../recette/RAPPORT_CAHIER_869.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_869.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 180, 'Bloqué (source)': 10, 'Partiel': 6, 'Non qualifié par fiche': 76}.

## Cahier867

Candidat865 requalifié sans nouveau correctif :2parcours annuels complets Edge1440/390 réussis en265,84s,FEC145lignes D=C1646060MAD,archives et à-nouveaux uniques ;restauration froide native réussie en69,37s,83tables/8fichiers,ACL/séquences/FEC/logos identiques.463sources produit conservées. [Rapport](../recette/RAPPORT_CAHIER_867.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_867.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 179, 'Bloqué (source)': 10, 'Partiel': 6, 'Non qualifié par fiche': 77}.

## Cahier865

SEC008 qualifié Edge1440/390/API/PG :paiement partiel300,avoir600 imputé et effet1200 portefeuille distingués ;3421=300,3425=1200,banque1500,ETIC3421certain300. Corrige badges Payée ambigus par Règlement en cours et taux commercial,calculs inchangés.2E2E+4connexes réussis,build0. [Rapport](../recette/RAPPORT_CAHIER_865.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_865.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 179, 'Bloqué (source)': 10, 'Partiel': 6, 'Non qualifié par fiche': 77}.

## Cahier863

SEC004 partiellement qualifié :22contrôles d'écran Edge sur1366x768/390x844,2modales par parcours, facture et détail GrandLivre accessibles ;aucun débordement global mesuré, titres et commandes contrôlés dans la largeur. Journal conservé. Appréciation complète humaine encore requise. [Rapport](../recette/RAPPORT_CAHIER_863.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_863.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 178, 'Bloqué (source)': 10, 'Partiel': 6, 'Non qualifié par fiche': 78}.

## Cahier861

SEC010 qualifié dans Edge1440/390 sur PG natif isolé : brouillon Paramètres abandonné lors de la bascule Aadmin vers Blecture ; profils et écritures inchangés, témoin A absent de B, création masquée par désactivation et POST direct403. Aucun correctif produit nécessaire. [Rapport](../recette/RAPPORT_CAHIER_861.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_861.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 178, 'Bloqué (source)': 10, 'Partiel': 5, 'Non qualifié par fiche': 79}.

## Cahier859

SEC005/009 qualifiés Edge1440/390/API/PG isolé :coupure transport GETJournal,message français etRéessayer200 sansmutation ;règlement120sur240 visible Part.payée,solde120 et nouvellepièceJournal sansF5 niPOSTdoublé. Défaut UXFailedtofetch corrigé dans client partagé,HTTP401403422 etAbort préservés ;build0. [Rapport](../recette/RAPPORT_CAHIER_859.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_859.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 177, 'Bloqué (source)': 10, 'Partiel': 5, 'Non qualifié par fiche': 80}.

## Cahier857

SEC007 qualifié Edge1440/390/API/PG isolé :identité Atlas<SARL>&associés et référence Réf<PIECE>&857 conservées littéralement dansPDF UI/API,image incorporée aveclogo fictif configuré,journal/profil conservés. Deuxparcours et13connexesPDF/logo réussis ;produit inchangé. [Rapport](../recette/RAPPORT_CAHIER_857.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_857.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 175, 'Bloqué (source)': 10, 'Partiel': 5, 'Non qualifié par fiche': 82}.

## Cahier855

ADM004/SEC006 qualifiés Edge1440/390/API/PG isolé :comptes du jeu actifs,subdivisions51111/51112/51132 lisibles,journaux manuels disponibles etCL réservé,POSTCLmanuel422,suppression5141refusée409. Quatre sélections3421/2355 relisentles bons libellés sansGETplan supplémentaire ;plan/journal conservés. [Rapport](../recette/RAPPORT_CAHIER_855.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_855.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 174, 'Bloqué (source)': 10, 'Partiel': 5, 'Non qualifié par fiche': 83}.

## Cahier853

NEG027/028 qualifiés Edge1440/390/API/PG natif isolé :dotation2025définitive4800 unique,APIunitaire409 et lots/clôture0nouvelle ;résiduelle1001pourcoût1000refusée400 côté UIetAPI,registre/tiers/journal/exercices conservés. Mêmeformulaire accepte1000résiduelle0. HuitcontrôlesPGdeconcurrence réussis. [Rapport](../recette/RAPPORT_CAHIER_853.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_853.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 172, 'Non qualifié par fiche': 85, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier851

NEG025/026 qualifiés Edge1440/390/API/PostgreSQL natif isolé :comptageM01−1 refusé côté formulaire et parAPI ;stock10surserviceS-VTE refusé409,stock0 etaucunmouvement. Articles,mouvements,inventaires,archives etécritures conservés aprèsrefus. Contrôle positif :comptage60 valide un seul snapshot sansrégularisation. [Rapport](../recette/RAPPORT_CAHIER_851.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_851.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 170, 'Non qualifié par fiche': 87, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier849

NEG023 :défaut réel corrigé. Remplacer directement une ligne déjà rapprochée était accepté200 ;désormais refus409 demandant dérapprochement explicite. Deux parcours Edge1440/390 vérifient refus dans les deux sens,liens/journal conservés et dépointage/repointage autorisé. Backend seul modifié,aucune migration. [Rapport](../recette/RAPPORT_CAHIER_849.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_849.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 168, 'Non qualifié par fiche': 89, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier847

NEG017–020 qualifiés Edge1440/390/API/PG natif isolé :encaissement14/05 avantéchéance15/05 refusé400,frais10001sur10000 refusés422,rejetCHQ01 déjàencaissé refusé400,dates future/avantémission refusées400. Aucune mutation après refus. Positif10000brut/10frais/9990banque exact et originaux conservés. [Rapport](../recette/RAPPORT_CAHIER_847.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_847.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 167, 'Non qualifié par fiche': 90, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier845

NEG014–016 qualifiés Edge1440/390/API/PG natif isolé :avoir3000 refusé vers autre tiers422,imputation3001409 et retour101sur100409. Refus visibles en interface et états banque/tiers/stock/écritures conservés. Retour10 puis imputation exacte3000 acceptés sur copie. [Rapport](../recette/RAPPORT_CAHIER_845.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_845.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 163, 'Non qualifié par fiche': 94, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier843

NEG012 et NEG013 qualifiés Edge1440/390/API/PG natif isolé :241sur240 refusé dans le formulaire et par API ;paiement exact240 accepté et seule écriture4411D/5141C240. AcompteAC-C01 de24000 entièrement imputé :nouvelle imputation1 refusée409,commande UI absente. Aucune mutation après refus. [Rapport](../recette/RAPPORT_CAHIER_843.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_843.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 160, 'Non qualifié par fiche': 97, 'Bloqué (source)': 10, 'Partiel': 5}.

## Qualification core841

100tests finaux réussis,112navigations et restauration83tables/8fichiers sur PostgreSQL natif isolé. Cycle annuel50opérations, lettrage et archivev2 qualifiés bureau/mobile. Incident initial mobile conservé, cause inconnue ; pas de correction de navigation revendiquée. Statuts globaux70inchangés ; suivi158/5/99/10. Recette humaine et production non validées. [Décision et réserves](../recette/DECISION_FACTURATION_COMPTABILITE_841.pdf), [preuves](../../Test/PREUVE_QUALIFICATION_CORE841.json). Aucun PostgreSQL utilisateur. RH/paie et EDI différés.

## Cahier839

Cycle annuel complet et intégrité qualifiés Edge1440/390 et PostgreSQL natif isolé :50opérations rapprochées aux oracles, clôture, report2026 unique, états et FEC. NEG010/011/037/038/039/040 et CLO009 qualifiés ; livre archivé avec auteur/version/SHA et conservé après une opération2026. [Rapport](../recette/RAPPORT_CAHIER_839.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_839.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 158, 'Non qualifié par fiche': 99, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier837

NEG042–045 qualifiés dans Edge1440/390 avec API et PostgreSQL isolé : lecteur sans mutation facture/journal/ETIC, documents et pièces B refusés à A, déconnexion locale et accès anonyme401. Dernier administrateur protégé. Témoins comptables A/B et facture B conservés. [Rapport](../recette/RAPPORT_CAHIER_837.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_837.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 151, 'Non qualifié par fiche': 106, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier835

SEC001–003 qualifiés Edge1440/390/PGisolé :invitéA révoqué403 maiscompteprincipalB200 ;motdepassepersonnel admin/lecture,actuelincorrect400/confirmationdifférente sansPOST,changement204,anciensecretetjetonversionné401,nouvelleconnexion200. Témoincomptablevalidé conservé. Erreurcalendrieraprès403 corrigée avecalertetretry explicites. [Rapport](../recette/RAPPORT_CAHIER_835.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_835.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 147, 'Non qualifié par fiche': 110, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier833

NEG001–008 qualifiés en Edge1440/390/PGisolé : doublon email, mot de passe court, ICE14chiffres, chevauchement/duréeexercice, écartD100/C99, PU−10 etTVA101 refusés. Aucune société/utilisateur orphelin, facture ni écriture ; identité et calendrier conservés. Minimum inscriptionUI aligné8surserveur. [Rapport](../recette/RAPPORT_CAHIER_833.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_833.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 144, 'Non qualifié par fiche': 113, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier831

PAY020 réussie enEdge1440/390/PGisolé :virement10000du25/01/2025annulé parcontrepassation06/10/2026 validée,créance10000réouverte ;5écritures2025 etbilan/CPC/ESG strictement conservés,source règlement non effacée,rejeu sansdoublon. [Rapport](../recette/RAPPORT_CAHIER_831.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_831.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 136, 'Non qualifié par fiche': 121, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier829

FAC016 réussie en Edge1440/390/PGisolé :avoir intégral30000au10/02/2025,retour100unités unefois,remboursementvirement30000au11/02 ;AV25000+5000/BQ30000 exacts et validés,originauxetpaiement conservés,crédit final0,double remboursement409sansmutation. [Rapport](../recette/RAPPORT_CAHIER_829.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_829.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 135, 'Non qualifié par fiche': 122, 'Bloqué (source)': 10, 'Partiel': 5}.

## Cahier827

FAC015 réussie sur Edge1440/390 et PostgreSQL isolé : échéancier600/600, règlement600, reliquat600au31/05 ;liste/détail/indicateurs alignés sur la prochaine échéance ouverte, contrat et écritures conservés, ETIC B6 échues600 recoupé, modification après paiement refusée409. [Rapport](../recette/RAPPORT_CAHIER_827.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_827.xlsx). Statuts fonctionnels inchangés ; qualification des fiches : {'Réussi': 134, 'Non qualifié par fiche': 123, 'Bloqué (source)': 10, 'Partiel': 5}.

## Achat825

Date de facture fournisseur choisie depuis BR, vide bloqué ;FAC014 exacte bureau/mobile,BC01/02→BR02/02→facture03/02/2025,10×100HT,stock10/un mouvement,AC1200 et doublon409 sans mutation. [Rapport](../recette/RAPPORT_ACHAT_825.pdf),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_825.xlsx) :133/5/124/10 ;70statuts inchangés. Aucune migration.

## Navigation823

CPT004 qualifiée : parcours commercial annuel réel bureau/mobile,48écritures/114lignes avantIS,D=C947940,RN129830,14exports contrôlés, puis50écritures annuelles. Navigation de test synchronisée sur les polices, sans délai augmenté ni changement produit ;hypothèses HTTP/1.1/BFCache rejetées, cause navigateur interne non attribuée. [Rapport](../recette/RAPPORT_NAVIGATION_823.pdf),[suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_823.xlsx) :132/5/125/10 ;70statuts inchangés.

## Export821

Nom CSV corrigé par exposition CORS de Content-Disposition ; téléchargements réels bureau/mobile et refus origine étrangère/authentification vérifiés. [Rapport](../recette/RAPPORT_EXPORT_821.pdf), [suivi](../recette/SUIVI_AUTOMATISATION_CAHIER_821.xlsx) :131/6/125/10, statuts fonctionnels inchangés ; FAC017 reste partielle pour sa période initiale et sa qualification fiscale.

## Suivi819

Relance interne créée/modifiée/annulée et persistante en Edge1440/390 : HP-FAC-012 réussi. Compléments fournisseurs/export CSV contrôlés en T1 2026 ; FAC017 partielle, période initiale T4 inadaptée et nom export.bin incorrect. [Rapport](../recette/RAPPORT_SUIVI_819.pdf), [suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_819.xlsx) :131/6/125/10 ;70statuts inchangés. Aucun produit modifié dans ce lot.

## Journal et avant IS817

FiltreJournal Toutes/Brouillons/Validées validé2largeurs/CSV/rafraîchissement ;build0 et4connexes. AvantISbureau complet48écritures/114lignes/D=C947940/RN129830/7exports,mais mobileincomplet(timeoutnavigation). **CPT004Partiel**,pasRéussi. Stresspolicesnonvalidé,queue128essayée puisrestaurée ;causeàétablir. [Rapport](../recette/RAPPORT_AVANT_IS_817.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_817.xlsx) :130/5/127/10 ;70statutsinchangés.

## Lettrage815

4groupesannuelsAAA–AAD persistants/FEC118lignes,impayés14400/480ouverts ;NEG021/022refusUI/API400. 4parcoursEdge et9connexes ;50écrituresetétatsimmuables. [Rapport](../recette/RAPPORT_LETTRAGE_815.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_815.xlsx) :130/4/128/10 ;70statutsinchangés. Aucun produit modifié ;historiqueécran769nonattribué.

## Banque813

Frais60UI,17mouvementsrelevéXLSX/CSV,soldes287730,17pointagesmanuels/rechargement/réimportsansdoublons,NEG024refusé. 2parcoursEdge et21connexes ;build0,50écrituresintactes. Propositionsstrictesinchangées :UIexplique0automatique surlibellésréférence+descriptif. [Rapport](../recette/RAPPORT_BANQUE_813.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_813.xlsx) :127/4/131/10 ;70statutsinchangés.

## Imports négatifs811

5 fichiers originaux refusés422 sur Edge1440/390 :déséquilibre,compteinconnu,doublon,NaN,résultat+gestion. Diagnostics/captures,0écriture/compte/version ;formulaire accepteensuitebalancevalide. [Rapport](../recette/RAPPORT_NEGATIFS_811.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_811.xlsx) :122/4/136/10. Aucun produit modifié ;70statutsfonctionnels inchangés.

## Recette balances809

4 fiches import/versions/AN/comparatif exécutées sur Edge1440/390 avec les fichiers originaux. 22 exports ouverts, logos contrôlés, lecteur403 ;50écritures etétats inchangés, aucune archive créée. [Rapport](../recette/RAPPORT_BALANCES_809.pdf), [suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_809.xlsx) :117/4/141/10. Préparation indépendante, N2026sansCPC/CAF ;70statutsfonctionnels inchangés.

## B14 corrigé807

Liquidations OD TVA reconnues par structure comptable stricte, sans référence/libellé ni réécriture. Reproduction50opérations ;13tests ciblés,274connexes et2parcoursEdge. ConfirmationB14,21/23,PDF/Excel,archive409 etimmutabilité. [Rapport](../recette/RAPPORT_B14_807.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_807.xlsx) :113/4/145/10. B6/B13 restentpartiels,aucundépôt attesté ;70statutsfonctionnels inchangés.

## ETIC805

19 rubriques documentées enregistrées et relues, B7 complet, ETIC 20/23 sur Edge 1440/390 et PostgreSQL temporaire. B6/B13/B14 partiels ; qualification manuelle justifiée de 3421, alerte de rejet et reliquat 11 080 conservés. Confirmation incomplète 422, archive 409 ; écritures et snapshot préservés. [Rapport](../recette/RAPPORT_ETIC_CAHIER_805.pdf), [suivi 272](../recette/SUIVI_AUTOMATISATION_CAHIER_805.xlsx) : 112/5/145/10. Les 70 statuts fonctionnels ne sont pas modifiés.

## États et FEC803

Scénarioannuelclôturé :Bilan/CPC/ESG,financementnonapplicableN1absent,livreinventairePDF,FEC145lignes/18colonnes équilibré1646060avec02/002distincts,0réparationauto ;Edge1440/390. 12moisTVA/24PDFetN+1rejoués avec3échéancesdufixturealignéescahier. [Rapport](../recette/RAPPORT_ETATS_CAHIER_803.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_803.xlsx) :93/2/167/10 ;70statutsfonctionnels inchangés. FECcontrôletechniqueexistant,pasconformitéofficielle ;échecsdetestinitiaux conservés.

## Chargement du journal801

GETancien masquantcréation reproduit1440/390puis corrigé,validation etnuméroofficielUI/API réels. 26statiques etruntime rôles/lettrage/concurrence/parcoursannuel réussis après séparation d’un conflit decollection conservé. [Rapport](../recette/RAPPORT_CONTEXTE_CAHIER_801.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_801.xlsx) :89/2/171/10inchangés,70statutsfonctionnels inchangés. Incident797compatiblemaisnonattribuécertainement ;Lettrage769resteouvert.

## Impression et exports799

Impression Journal corrigée :45pièces/90lignes complètes sur6pages,avantfix5références seulement. Parcoursannuel exports797 rejoué1440/390,20fichiers CSV/Excel/PDF contrôlés etécritures/snapshot conservés. [Rapport](../recette/RAPPORT_IMPRESSION_CAHIER_799.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_799.xlsx) :89réussies/2partielles/171nonqualifiées/10bloquées ;70statuts fonctionnels inchangés. Rafraîchissement797 etLettrage769 restentouverts.

## Exports partiels797

CSVjournalvide corrigé etjustificatifCAP01vérifié ;2testsGETretenu et8connexesréussis,build0. Parcoursannuelexports ENÉCHEC :PDFjournalmobile incomplet,incidentrafraîchissementValider àanalyser,grandlivre/balancesnonatteints. [Rapport](../recette/RAPPORT_EXPORTS_CAHIER_797.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_797.xlsx) :88réussies/3partielles/171nonqualifiées/10bloquées. 70statuts fonctionnels maintenus ;aucunevalidationhumaine/production.

## TVA et échéances795

12mois/24PDF,TVA/ISsoldesN+1etacomptes/CSSissusdelaliquidation2025 testés Edge1440/390. 3correctionsprouvées :facturemasquéeparGETtardif,reportTVAavoirs(4700vs4200février),pertesaisieacomptes. CGI2025officielconsulté,éligibilitéinchangée. [Rapport](../recette/RAPPORT_TVA_ECHEANCES_CAHIER_795.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_795.xlsx),[source](VERIFICATION_REPORT_TVA_795.md) :87réussies/2partielles/173nonqualifiées/10bloquées. DépôtDGI/imprimantephysiquenonvalidés,70statutsfonctionnelsmaintenus.

## Fiscalité et clôture793

Parcours annuel→retraitements4000/crédit200→clôture2025/AN343810/CP2026→snapshotIS23220,25 :2nouveaux Edge1440/390et3connexes réussis,50définitivespréservées,verrous423/409. FECconformeavec1avertissementconservé. [Rapport](../recette/RAPPORT_CLOTURE_CAHIER_793.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_793.xlsx) :72réussies/2partielles/188nonqualifiées/10bloquées. CMhypothèsefictivepartielle,déclarationsTVAetqualificationréglementaireàpoursuivre ;aucunproduitmodifié,70statutsfonctionnelsmaintenus.

## Exercice connecté791

50opérations/118lignes2025 produites parformulaires réels Edge1440/390 :2parcours et20connexesréussis ;soldesindépendants,bilan337010,résultat106409,75,CAF112709,75,stock6600etimmo24000/4800/19200. 2contrepassations2026 laisséesbrouillon. [Rapport](../recette/RAPPORT_ANNUEL_CAHIER_791.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_791.xlsx) :66réussies/1partielle/195nonqualifiées/10bloquées. Clôture,liquidation/déclarations fiscales encoreàtester ;aucuncontrôlecontourné,aucunproduitmodifié,70statutsfonctionnelsmaintenus.

## Semestre connecté789

Parcours unique capital/acquisition → marchandises → services/effets/acomptesclients, janvier–juin2025 :31écritures/76lignes confrontées àsource indépendante, 2nouveaux tests1440/390 et4connexes réussis. [Rapport](../recette/RAPPORT_SEMESTRE_CAHIER_789.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_789.xlsx) :50réussies/1partielle/211nonqualifiées/10bloquées. TVA manuelle du Journal uniquement ;déclarations etannée complète encoreàpoursuivre. Aucunproduitmodifié,70statuts16/49/1/4maintenus.

## Cession du cahier787

Deux tests Edge1440/390 et PostgreSQL temporaire réussis : cession20000HT/TVA4000/banque24000,sortie etprotection2025. Écart documentaire : la convention30/360 inclusive ajoute13,33 au01/01/2026, doncVNC19186,67/gain813,33, faceaux19200/800du cahier. HP-IMM-004 reste PARTIELLE ; qualification/régularisationTVA nonvalidée. [Précisions](../recette/PRECISIONS_CESSION_CAHIER_787.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_787.xlsx) :35réussies/1partielle/226nonqualifiées/10bloquées. Statutsfonctionnels70 maintenus,aucuncalculproduitmodifié.

## Immobilisation du cahier785

Acquisition/paiement/dotation exacts exécutés dans Edge1440/390 et PostgreSQL temporaire :4tests finaux/connexes réussis,3fiches rapprochées. Brut24000/amorti4800/net19200,bilan détaillé etanti-double409 contrôlés. [Rapport](../recette/RAPPORT_IMMOBILISATION_CAHIER_785.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_785.xlsx) :35réussies,227nonqualifiées,10bloquées. Date du registre clarifiée sans modification de calcul ;70statuts16/49/1/4 maintenus. Cession etparcours annuel encoreàpoursuivre.

## Capital manuel et clic mobile783

CAP-01200000saisiUI sur1440/390,brouillon/validation/libellés exacts etFECréduit vérifiés.6tests finaux réussis,build0 en5,01s. Perte de clicmobile reproduite4fois,essaiCSS retiré,puiscorrectionracine fermetureautocomplete au blur. [Bilan de session](../recette/RAPPORT_SESSION_FORMULAIRES_771_783.pdf),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_783.xlsx) :32fiches complètes,230nonqualifiées et10bloquées source. 41tests paramétrés distincts réussis aprèsreprises danscettesession,échecs initiaux conservés ;70statutsfonctionnels16/49/1/4 maintenus. Aucune recette humaine/production validée ;incident Lettrage769 ouvert.


## Administration du cahier781

CréationUI2025absent,comptable/lecture etseconde sociétéBexécutés :2nouveaux et2connexes réussis ;rôles/403/404,doublon409,PDFpièceprotégés et14écrituresvalidées deAinchangées. [Rapport](../../Test/rapport_administration_cahier781.md),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_781.xlsx) :31fiches complètes,0partielle,231nonqualifiées et10bloquées source. Variante decréation2025 etbrouillon fictif1MADsupprimé204 explicités ;aucune donnée réelle utilisée. Aucun code produit modifié ;70statutsfonctionnels16/49/1/4 maintenus ;recette humaine/production nonvalidée.


## Inventaire du cahier779

Inventaire physique60unités/6600MAD etvraie écriture3111/6114 validés sur1440/390 ;2parcours et4cas connexes réussis.14écritures définitives/33lignes177000MAD,préfixe13inchangé,anti-doublon409explicite. Bilanprovisoire44000/résultat22100 du sous-parcours uniquement,non exerciceannuelcomplet. [Rapport](../../Test/rapport_inventaire_cahier779.md),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_779.xlsx) :28fiches complètes,1partielle,233nonqualifiées et10bloquées source. Aucun code produit modifié ;70statutsfonctionnels16/49/1/4 maintenus ;recette humaine/production nonvalidée.


## Suite commerciale du cahier777

Chèque20000,avoirretour10,secondevente50 etcrédit3000/virement5000 rejoués viaUI sur1440/390 :2parcours et5cas connexes réussis ;échec initial de locator conservé.13écritures définitives/31lignes170400MAD,stock60CMUP110,soldeclient10000,préfixe7écritures inchangé. [Rapport](../../Test/rapport_suite_cahier777.md),[suivi272](../recette/SUIVI_AUTOMATISATION_CAHIER_777.xlsx) :26fiches complètes et2partielles,234nonqualifiées et10bloquées source. Aucun code produit/migration modifié ;70statuts fonctionnels conservés16/49/1/4 ;recette humaine/production nonvalidée.


## Cycle commercial du cahier775

Notes facultatives BC exposées etdate de facture choisissable depuis le BL,contrat API existant conservé.13tests finaux réussis (2parcours exacts du cahier sur1440/390 et11commerciaux connexes),build0 en6,02s.7écritures définitives/17lignes,total84400MAD,lettrage fournisseur persistant,stock100auCMUP110,solde vente20000. Les3échecs initiaux sont conservés (2helpers,1note absente). [Rapport](../../Test/rapport_cycle_cahier775.md),[suivi272fiches](../recette/SUIVI_AUTOMATISATION_CAHIER_775.xlsx),[précisions de saisie](../recette/PRECISIONS_RECETTE_FORMULAIRES_775.md).20fiches complètes et2partielles rapprochées des preuves769–775 ;aucun statut humain modifié.70statuts fonctionnels inchangés :16terminés49partiels1absent4bloqués. Incident Lettrage769 nonrésolu malgré reloads réussis.


## Référentiels du cahier773

Tri des nouvelles fiches en tête de Tiers corrigé après échec reproduit.6tests Edge/API/PostgreSQL éphémère réussis (7tiers/3articles du cahier sur1440/390 et4connexes délais/activité),build0 en5,13s.9cas du cahier complets dans ce périmètre,HP-ADM-013 partiel tant que comptes de stock non confirmés dans l’inventaire ;classeurs humains inchangés. [Rapport](../../Test/rapport_referentiels_cahier773.md).70statuts fonctionnels conservés :16terminés49partiels1absent4bloqués ;aucune recette utilisateur/production validée.


## Formulaire bancaire771

Défaut du nom libre reproduit puis corrigé :champ persistant au clavier et à la réouverture,nom vide bloqué,choix prédéfini conservé.5tests Edge/API surPostgreSQL éphémère réussis après correction (2bancaires et3connexes),build0 en12s ;échec avant correctif conservé. HP-ADM-005 réussi automatiquement dans ce périmètre. [Rapport](../../Test/rapport_banque_cahier771.md). Classeurs humains inchangés ;70statuts fonctionnels maintenus (16terminés49partiels1absent4bloqués). Aucun PostgreSQL réel ;incident Lettrage769 toujours ouvert.


## Recette automatisée769 — 24 octobre2026

698 tentatives exécutées :696 réussies,2 échecs initiaux conservés. Après reprises,693 identités de test paramétrées distinctes réussies ;aucun test ignoré. Le premier échec était une assertion documentaire obsolète, corrigée ;le second est un écran vide après reload Lettrage,non reproduit lors de4passages de diagnostic, dont la cause reste ouverte. Aucun code applicatif ni migration modifié. Build Vite0 en9,57s,avec avertissement de taille du bundle.

Tests API/Edge et PostgreSQL natif temporaire :cycle commercial,stocks,immobilisations,administration,journal,fiscalité,annuel,installation vierge104,UX etoracles documentaires. Société et paramètres du cahier saisis viaUI ;rejeu distinct parAPI des50écritures/118lignes :balance exacte,bilan337010MAD,résultat net106409,75MAD,CAF112709,75MAD ;matériel informatique24000brut/4800amortissement/19200net et sous-poste235 vérifiés. Ce rejeu comptable ne constitue pas le cycle commercial complet du cahier via ses formulaires.

[Rapport PDF](../recette/RAPPORT_RECETTE_AUTOMATISEE_769.pdf),[résultats Excel](../recette/RAPPORT_RECETTE_AUTOMATISEE_769.xlsx),[preuves et essais](../../Test/PREUVE_RECETTE_AUTOMATISEE769.json). Les272fiches humaines existantes conservent leurs statuts ;HP-ADM-003 n’est que partiellement couvert par le nouveau parcours. Installation réelle,recette utilisateur et dépendances officielles restent à valider. RH/paie etpoint6 différés.70statuts fonctionnels inchangés :16terminés49partiels1absent4bloqués.


## UX Factures767

14 tests Edge/API surPostgreSQL éphémère réussis en144.1s,aucun échec/erreur/ignoré.4nouveaux parcours UX,2régressions dates100/101factures,8lectures historiques etvrai exercice vide. Campagnes précédentes4puis14 également réussies,recouvrements non additionnés. Build final7,92s code0 ;compilation2tests Python OK.
[Rapport](../../Test/rapport_ux_factures767.md), [utilisation](../UX_FACTURES_FILTRES_767.md). Réinitialisation globale,effacement nommé,focus/clavier etvide explicite lisible surmobile. Statuts fonctionnels inchangés :16terminés49partiels1absent4bloqués,70lignes. Aucune nouvelle règle ni validation de recette humaine/production ;RH/paie etpoint6 différés.


## Livraison de recette765

42 tests de documents et oracles réussis en49.99s ; après ajustement final de la largeur du tableau Word/PDF,18ciblés revalidés en27.78s. Zéro échec/erreur/ignoré dans ces campagnes finales ; recouvrements non additionnés. Compilation des3Python modifiés OK. Word OOXML/CRC et liens,PDF7pages rendu,Excel20feuilles/272fiches verticales contrôlés sur les fichiers réels.262Non testé,10Bloqué,aucun succès humain prérempli. Produit/frontend/migrations et117protections inchangés.
[Rapport](../../Test/rapport_pilotage_recette765.md), [guide Word](../recette/PILOTAGE_RECETTE_HORS_RH_765.docx), [suivi unique](../recette/PILOTAGE_RECETTE_HORS_RH_765.xlsx).272cas existants regroupés, pas une nouvelle recette humaine ni une fonctionnalité produit supplémentaire.70statuts fonctionnels inchangés :16terminés49partiels1absent4bloqués. Documents officiels toujours nécessaires selon[763](DEPENDANCES_OFFICIELLES_20261023_763.md). RH/paie etpoint6 différés.


## Contrôle des exports763 et dépendances

21 tests connexes réussis en91.62s, zéro échec/erreur/ignoré dans cette campagne finale. Ciblés11réussis en4.94s,1cas UI désélectionné puis exécuté dans la campagne complète ; recouvrements non additionnés. Compilation des4fichiers Python modifiés OK. Source produit/frontend,117protections et migrations inchangés.
[Rapport](../../Test/rapport_exports_liasse763.md), [documents exacts à obtenir](DEPENDANCES_OFFICIELLES_20261023_763.md). Les deux exécutions initiales échouées sont conservées au rapport. Aucun nouveau module livré ; seuls4bancs et leur capteur commun corrigés.70statuts inchangés :16terminés49partiels1absent4bloqués. Catalogue09B absent,09F/09Gpartiels,EDI bloqué ; aucune déclaration officielle ou recette utilisateur validée.


## Préparation TP761 livrée

Campagne finale :287 tests connexes réussis en478.03s ;2parcours annuels en62.76s. Zéro échec/erreur/ignoré dans ces campagnes finales. Ciblés53API/oracles,8Edge,1restauration ; campagnes recouvrantes non additionnées. Build5,30s code0 ;1237sources/scripts figés,117protections et témoins comptables/fiscaux/pièces/rendus préservés. Restauration104/83tables/8fichiers. Guide Word/PDF10pages,Excel6feuilles et8cas humains Non testé.
Premier passage complet :286réussis et1échec467,37s, timeout20s sur le champ de connexion avant restauration. Cause inconnue, non reproduite lors du diagnostic1réussi/286désélectionnés64,73s, puis campagne finale287réussis. Aucun correctif produit de connexion, retry, délai étendu ou assertion affaiblie ; instrumentation de capture conservée si récidive. Les traces initiales sont conservées, pas remplacées par un résultat vert.
LIA-09G passe de absent à partiel.70statuts :16terminés49partiels1absent4bloqués.09B reste absent ;09F/09Gpartiels, EDI officiel bloqué. [Guide](../LIASSE_TAXE_PROFESSIONNELLE_761.md), [sources](SOURCES_TAXE_PROFESSIONNELLE_20261023_761.md).


## Module fonctionnel tiers759

226 tests connexes natifs réussis en 344.4s ;2annuels en 36.09s. 66ciblés finaux réussis180,13s (57API/oracles+8Edge+1restauration), recouvrements non additionnés. Zéro échec, erreur ou ignoré. Build5,05s code0 ;1230sources/scripts figés,117protections et témoins comptables/fiscaux/pièces/rendus inchangés. Restauration104/83tables/septfichiers. Word/PDF10pages/Excel6feuilles et8cas humains Non testé.
LIA-09F passe de absent à partiel sur preuves de code/API/Edge/exports/restauration.70statuts :16terminés48partiels2absents4bloqués. [Guide](../LIASSE_REMUNERATIONS_TIERS_759.md), [sources](SOURCES_REMUNERATIONS_TIERS_20261023_759.md), [périmètre de clôture](CLOTURE_PERIMETRE_HORS_RH_20261023.md). Aucun dépôt officiel ou conformité réglementaire validé.


## Préparation de LIA-09F757

Cadrage documentaire uniquement. Correspondance14donnees verifiee par AST/lecture des sources et5empreintes ; grille XLSX4feuilles/40lignes vierges/8cas futurs Bloque controlee. 1223sources/scripts755 et117protections inchanges. Aucun nouveau testAPI/PostgreSQL/navigateur, build ou comportement metier valide revendique.
Audit640 conservé, pas de nouvelle recherche exhaustive : le texte CGI local déjà obtenu est exploitable, modèle151 et annexes applicables non obtenus. [Contrat concret et correspondance au code](CONTRAT_PREPARATION_TIERS_757.md), [grille hors application](../recette/GRILLE_PREPARATION_TIERS757.xlsx). LIA-09F reste absent ; la grille n’est pas importable et ne constitue pas une déclaration.
Suite : premier lot documentaire interne selon contrat, identité/provenance/montants explicites sans classement juridique automatique ; obtenir modèle officiel avant génération administrative.70statuts16terminés47partiels3absents4bloqués inchangés. Les résultats749–755 restent ceux de leurs rapports. RH/paie etpoint6 différés.


## Recette annuelle intégrée755

10 tests connexes natifs réussis en 127.38s et2annuels en 36.57s ; campagnes ciblées2UI/4API/1restauration également réussies, recouvrements non additionnés. Zéro échec, erreur ou ignoré dans les validations finales. 1223sources/scripts figés,117protections inchangées, témoins comptables/fiscaux/pièces/rendus préservés. 444fichiers produit inchangés dans755 ; build753 code0 toujours applicable, aucun nouveau build revendiqué. Word/PDF16pages et Excel10feuilles/14cas humains Non testé ; calculs Decimal indépendants exécutés.
[Rapport755](../../Test/rapport_recette_fiscale755.md), [cahier](../RECETTE_FISCALE_INTEGREE_755.md), [sources](SOURCES_RECETTE_FISCALE_20261023_755.md).
Le sous-parcours société neuve→balances→six contrôles fiscaux→proposition3650→exports/restauration est validé automatiquement sur environnement isolé. Matrice70 inchangée :16 terminés,47 partiels,3 absents,4 bloqués ; LIA-09D reste partiel pour le dossier annuel exhaustif. Les anciennes mentions de compléments fiscaux à développer sont historiques : B12/CM/CSS/CR/AP/proposition ont désormais leurs contrôles et preuves, les autres limites ne sont pas effacées.
Suite indépendante recommandée : cadrer LIA-09F, préparation documentaire des rémunérations allouées aux tiers, en vérifiant d’abord référentiel officiel applicable et sources existantes ; aucun format de dépôt inventé. Réserves FEC/ETIC historiques, XSD/EDI, recette cible et RH/paie/point6 restent séparés.


## Proposition annuelle IS/CM753

212 tests connexes réussis en 329.32s ;2 annuels en 37.36s ;48 ciblés en43,11s et9Edge+restauration en120,71s. Zéro échec/erreur/ignoré ;campagnes recouvrantes non additionnées. Build final code0 ;1218SHA figés et témoins comptables/fiscaux/pièces/rendus préservés. Migrations/modèles/bootstrap et moteurs fiscaux protégés inchangés. Word,PDF10pages,Excel5feuilles,8cas humains Non testé.
[Rapport753](../../Test/rapport_balance_liquidation753.md), [guide](../LIASSE_BALANCES_LIQUIDATION_753.md), [sources](SOURCES_LIQUIDATION_20261023_753.md).
Matrice70 inchangée :16 terminés,47 partiels,3 absents,4 bloqués. LIA-09D partiel ;prochaine étape recette fiscale annuelle cohérente N/N-1 depuis société fictive neuve. Réserves FEC/ETIC historiques conservées ;RH/paie et point6 différés.


## Acomptes IS externes qualifiés751

155 tests connexes réussis en 274.95s ;2 annuels en 37.72s ;46 ciblés en46,91s et9Edge+restauration en113,88s après correction du banc. Zéro échec/erreur/ignoré ;campagnes recouvrantes non additionnées. Build final code0 ;1212SHA figés et témoins comptables/fiscaux/pièces/rendus préservés. Migrations/modèles/bootstrap et moteurs fiscaux protégés inchangés. Word,PDF10pages,Excel5feuilles,8cas humains Non testé.
[Rapport751](../../Test/rapport_balance_acomptes751.md), [guide](../LIASSE_BALANCES_ACOMPTES_751.md), [sources](SOURCES_ACOMPTES_20261023_751.md).
Matrice70 inchangée :16 terminés,47 partiels,3 absents,4 bloqués. LIA-09D partiel ;prochaine étape liquidation externe conditionnelle. Réserves FEC/ETIC historiques conservées ;RH/paie et point6 différés.


## Crédits IS externes qualifiés749

298 tests connexes réussis en 529.06s ;2 annuels en 42.02s ;57 ciblés en52,58s et12Edge+restauration validés. Zéro échec/erreur/ignoré ;campagnes recouvrantes non additionnées. Build final code0 ;1206SHA figés et témoins comptables/fiscaux/pièces/rendus préservés. Migrations/modèles/bootstrap et moteurs fiscaux protégés inchangés. Word,PDF9pages,Excel5feuilles,8cas humains Non testé.
[Rapport749](../../Test/rapport_balance_credits749.md), [guide](../LIASSE_BALANCES_CREDITS_749.md), [sources](SOURCES_CREDITS_20261022_749.md).
Matrice70 inchangée :16 terminés,47 partiels,3 absents,4 bloqués. LIA-09D partiel ;prochaine étape acomptes puis liquidation externe conditionnelle. Réserves FEC/ETIC historiques conservées ;RH/paie et point6 différés.


## Envoi de justificatifs et contexte747

Multipart réutilise les gardescommunes,ancien401/201 ignoré sans effacer la
nouvelle session ;pièceaboutie unefois dansA,octets/SHA/versionpréservés,B404. 34 tests connexes réussis en 174.27s ;2 annuels en 53.39s ;5 ciblés en56,13s. Zéro échec/erreur/ignoré dans les validations finales,campagnes recouvrantes non additionnées. Build6,05s code0 ;1200SHA figés,témoins fiscaux/comptables/pièces/rendus préservés,272sources backend inchangées. Avant1échec attendu40,72s(4non sélectionnés). Word,PDF6pages,Excel5feuilles,4cas humains Non testé etPDF de recette/hash fournis.
[Rapport747](../../Test/rapport_pieces_contexte747.md),[bilan de session](RAPPORT_SESSION_20261022_739_747.md).
Statuts70inchangés16/47/3/4 ;29nouveauxcas humainsde sessionNonTesté.
Crédits/acomptes/liquidation etcalendrierCSS àqualifier,EDI surschéma officiel,
recettehumaine/production nonvalidées,RH/paie etpoint6 différés.

## Réponses HTTP du contexte745

Ancien200JSON/blob ignoré après changement dejeton,vérificationaprèsdécodage
etavantsynchronisationdu rôle ;POSTabouti préservé sansrejeu. 40 parcours connexes réussis en 258.02s ;2 annuels en 55.44s ;6 ciblés en59,70s et1POSTabouti en40,95s(6non sélectionnés). Zéro échec/erreur/ignoré dans les validations finales ;campagnes recouvrantes non additionnées. Build8,50s code0 ;1198SHA figés,nonvidefiscal/comptable/pièces/rendus préservés,272sources backend inchangées. Deux reproductionsrouges41,28/38,25s(5non sélectionnés). Word,PDF5pages,Excel5feuilles,4cas humains Non testé.
[Rapport745](../../Test/rapport_contexte_http745.md),[guide](../SESSIONS_CONTEXTE_HTTP_745.md).
Matrice70inchangée16/47/3/4 ;adaptateurmultipartdejustificatifs àqualifier
séparément,recettehumaine/production nonvalidées,RH/paie etpoint6 différés.

## CSS externe qualifiée743 —22octobre2026

Bénéfice fiscal du dernier exercice clos explicitement sourcé,tauxproportionnel
partagé,exonération permanente déclarée,comparaisonCSS etversions figées.
Aucune échéance,liquidationIS ou donnéeextra-comptable inventée. 229 tests connexes réussis en 639.74s ; 2 annuels en 59.36s ; 45 API/purs en75,77s et9Edge+restauration en160,93s. Zéro échec/erreur/ignoré ; campagnes recouvrantes non additionnées. Build6,18s code0 ;1196SHA figés,témoins comptables/fiscaux/pièces/rendus préservés.110SQL/bootstrap/modèles,7moteurs fiscaux etCM741 inchangés. Restauration104/83tables/5fichiers. Word,PDF5pages,Excel5feuilles,8cas humains Non testé etsource fictive2025.
[Rapport743](../../Test/rapport_balance_css743.md),[guide](../LIASSE_BALANCES_CSS_743.md),[sources](SOURCES_CSS_20261022_743.md).
LIA-09D partiel,statuts70inchangés16/47/3/4. Qualifications/dateclôture/échéance,
recettehumaine/production àvalider ;RH/paie etpoint6 différés.

## CM externe qualifiée741 —22octobre2026

Base sur balance conservée2026 etparamètres explicitement sourcés ;moteur CM
partagé,versions figées,alerte B12 etexports avec logos. Aucun calcul de solde
final ou liquidation confirmée. 519 tests connexes réussis en 1299.36s ; 2 annuels en 54.60s ; 53 ciblés en158,66s avant seule retouche de retourligne mobile,reprise dans les519. Zéro échec/erreur/ignoré dans les validations finales ; campagnes recouvrantes non additionnées. Build5,90s code0 ;1190SHA figés,témoins fiscaux/comptables/pièces/exports préservés.110SQL/bootstrap/modèles et7moteurs fiscaux inchangés. Restauration104/83tables/5fichiers. Premier banc43réussites/1assertionPDF typographique52,06s corrigée. Cahier Word,PDF5pages,Excel5feuilles,8cas humains Non testé et2CSV équilibrés.
[Rapport741](../../Test/rapport_balance_cm741.md),[guide](../LIASSE_BALANCES_CM_741.md),[source CGI intégrale](SOURCES_CM_20261022_741.md).
Blocage documentaire CGI levé via republication institutionnelle CRI ;EDI
reste conditionné à son schéma. LIA-09D partiel,statuts70 inchangés16/47/3/4.
Recettehumaine/production nonvalidées ;RH/paie etpoint6 différés.

## Sessions HTTP401739 —22octobre2026

Connexion refusée lisible sans rechargement,401ancien sans effacement d’une
nouvelle session ;session courante refusée toujours déconnectée,JSON/exports.
24 parcours connexes réussis en162,86s ;3 administration/mot de passe en43,09s ;2annuels réussis ;6ciblés en54,86s et13de reprise en48,54s. Zéro échec/erreur/ignoré dans les validations finales ;campagnes recouvrantes non additionnées. Build9,52s code0,1184SHA figés,témoins comptables/fiscaux/pièces/exports préservés,270sources backend inchangées. Avant1échec attendu44,36s ;premier banc8réussites/1échec de composition76,67s,assertion4comptes contre892,administration exécutée séparément ensuite. Guide Word/PDF5pages,Excel5feuilles,cinqcas humains Non testé.
[Rapport739](../../Test/rapport_sessions_http401739.md),[mode d’emploi](../CONNEXION_SESSIONS_739.md).
Statuts globaux70 inchangés :16terminé/47partiel/3absent/4bloqué.
Timeoutconnexion737 distinct,sous surveillance ;RH/paie etpoint6 différés.

Correction737 : sélecteur d’articles commercial sans repli aux non-résultats,
chargement/erreur/réessai et garde de contexte ; descriptions libres et prix
achat/vente conservés. 52parcours connexes réussis256,88s et2annuels34,18s,0échec/erreur/ignoré ;10ciblés54,17s et1ciblé connexion32,66s(51non sélectionnés),campagnes recouvrantes non additionnées. Build7,67s code0 ;1182SHA figés et témoins fiscaux/comptables/documents préservés. Backend/SQL intégralement inchangés. Avant correction1échec26,11s ;premier banc après4réussites/1échec61,92s(attente événement réseau corrigée) ;première campagne32réussites/1timeoutconnexion185,44s,cause indéterminée et nonreproduite dans52cas,délai inchangé. Guide Word/PDF6pages,Excel5feuilles,6cas humains Non testé.
[Mode d’emploi](../CATALOGUE_ARTICLES_COMMERCIAL_737.md), [rapport](../../Test/rapport_catalogue_articles737.md),
[livraisons735–737](LIVRAISONS_SESSION_20261022_735_737.md), [reprise](REPRISE_APRES_CATALOGUE_737.md).
Statuts globaux inchangés. Timeoutconnexion non expliqué sous surveillance ;
fiscalité externe/EDI conditionnés aux sources officielles. RH/paie/point6 différés.

Complément735 : contexte fiscal externe CM/CSS/crédits/acomptes sourcé,
totaux exacts/inconnus et référence B12 figée avec alerte de changement.
Aucun impôt dû ou solde final automatique ; CSS séparée et imputations comparées,
aucune qualification fiscale inventée. 460connexes réussis758,61s et2annuels33,95s ;0échec/erreur/ignoré. Ciblés34API/purs76,02s,8Edge+restauration191,63s,1Edge B12 supplémentaire48,49s(8non sélectionnés). Reprise733:4réussis107,39s. Campagnes recouvrantes non additionnées. Build7,23s code0,1180SHA figés,110SQL/bootstrap/modèles et7moteurs fiscaux inchangés. Restauration104/83tables/cinqfichiers. Guide Word/PDF8pages,Excel5feuilles,huitcas humains Non testé.
[Guide735](../LIASSE_BALANCES_CONTEXTE_FISCAL_735.md), [rapport](../../Test/rapport_balance_contexte_fiscal735.md),
[livraisons](LIVRAISONS_SESSION_20261022_735.md), [reprise](REPRISE_APRES_CONTEXTE_FISCAL_735.md).
LIA-09D reste partiel, statuts globaux inchangés (70:16/47/3/4).
Sources officielles nécessaires pour la liquidation/EDI ; suite indépendante
catalogue commercial737. RH/paie etpoint6 humain différés.

Complément733 : cahier intégré B12/B13/B14/C3/N2/extra sur un jeu troisans
cohérent (RAN/TVA/impôt théorique),Word/PDF10pages/Excel14feuilles/8cas humains
Non testé/3CSV. Import CSV etparcours connecté API/Edge3rôles exécutés,net6020/
situation17520 etIS théorique1580,aucune liquidation confirmée. PDF du dossier
compacté63→45pages par regroupement C3,unités conservées,aucun calcul modifié.
6tests définitifs64,64s :1parcours API PostgreSQL104 et3Edge connectés (admin1440,comptable390,lecture390),2PDF historiques (pur/API SQLite).0échec/erreur/ignoré.4parcours précédents64,25s ;410connexes validés avant seule modification de pagination PDF, autres1171fichiers préservés sauf ce fichier.1173SHA suivis,4Python compilés,108SQL/bootstrap protégés. Cahier Word/PDF10pages/Excel14feuilles,8cas humains Non testé et3CSV équilibrés. Dossier exporté45pages au lieu de63,43feuillesExcel/15fichiers avec logos/manifestes.
[Commencer](../recette/PAR_OU_COMMENCER_20261022_733.md),[rapport](../../Test/rapport_recette_integree_balances733.md),
[livraisons](LIVRAISONS_SESSION_20261022_725_733.md),[reprise](REPRISE_APRES_RECETTE_INTEGREE_733.md).
Statuts globaux inchangés,LIA-09D partiel. Fiscalité autonome complète conditionnée
aux sources officielles applicables ;RH/paie etpoint6 humain différés.

Complément731 : données extra-comptables C3 N/N-1/N-2 explicitement déclarées,
unités personnes/MAD/MAD par titre, sources et affectations à justifier. Aucun
RH/Journal repris, net/capital non utilisés pour inventer des valeurs par titre.
Nouvelle conservation C3 requise, anciennes versions inchangées. Aiguillage du
validateur numérique corrigé après échec réel, cas141,25 et perte−1001 testés.
extra731_api_final: 58 réussis en 83.69s ; extra731_141: 1 réussis en 35.79s ; extra731_perte: 1 réussis en 32.51s ; extra731_visuel: 3 réussis en 47.36s ; extra731_cible: 9 réussis en 128.8s ; extra731_nature: 3 réussis en 36.38s ; extra731_commune_final: 410 réussis en 497.67s ; extra731_annuel: 2 réussis en 46.61s. Campagnes recouvrantes, aucun échec/erreur/ignoré dans les validations finales. Échec numérique initial1cas2,44s corrigé ; première campagne1ReadTimeout+24réussites45,33s, puis3cas ciblés36,38s et relance complète à code/délai inchangés. Sélections ciblées avec32/33/407cas désélectionnés. Build final4,95s code0 ; 11Python compilés ;1171SHA stables ; restauration104/83tables/5fichiers ;108SQL/bootstrap protégés. Guide7pages/Excel5feuilles/6cas humains Non testé/4CSV.
[Guide731](../LIASSE_BALANCES_C3_EXTRA_731.md), [rapport](../../Test/rapport_balance_c3_extra731.md),
[livraisons](LIVRAISONS_SESSION_20261022_725_731.md), [reprise](REPRISE_APRES_C3_EXTRA_731.md).
LIA-09D reste partiel, statuts globaux inchangés. Fiscalité externe complète et
justificatifs à poursuivre ; RH/paie etpoint6 humain différés.

Complément729 : source N-2 C3 explicitement rattachée depuis une préparation
conservée de même société/exercice N-2. Sources/états/référence/SHA figés ; aucun
Journal/RH repris. C3 nécessite une nouvelle conservation, anciens contrôles
inchangés ; garde119 et comparatifs aux états réutilisés.
n2729_api: 48 réussis en 72.8s ; n2729_cible: 9 réussis en 120.25s ; n2729_commune: 368 réussis en 470.99s ; n2729_annuel: 2 réussis en 38.46s. Aucun échec/erreur/ignoré, campagnes recouvrantes. Build4,99s code0 ; 11Python compilés ;1165SHA stables ; restauration104/83tables/5fichiers ;108SQL/bootstrap protégés. Guide7pages/Excel5feuilles/sixcas humains Non testé et4CSV distincts.
[Guide729](../LIASSE_BALANCES_COMPARATIF_N2_729.md), [rapport](../../Test/rapport_balance_comparatif_n2729.md),
[livraisons](LIVRAISONS_SESSION_20261022_725_729.md), [reprise](REPRISE_APRES_COMPARATIF_N2_729.md).
LIA-09D reste partiel, statuts globaux inchangés. Suite C3 extra-comptable et
fiscalité externe complète sur sources explicites ; RH/paie etpoint6 différés.

Complément727 : B14 autonome, soldes TVA4455/34552/34551 certains, ouvertures/
opérations/déclarations explicitement justifiées, signes et inconnus préservés.
N-1 pour mémoire, écarts visibles, aucun dépôt/liquidation/paiement déduit.
Libellés métier B12 rendus lisibles dans PDF/Excel, JSON financier inchangé.
tva727_api_final: 34 réussis en 38.23s ; tva727_cible: 9 réussis en 123.65s ; tva727_commune: 337 réussis en 367.17s ; tva727_annuel: 2 réussis en 39.4s. Aucun échec/erreur/ignoré, campagnes recouvrantes. Build5,07s code0 ; 12Python compilés ;1159SHA stables ; restauration104/83tables/5fichiers ;108SQL/bootstrap protégés. Guide7pages/Excel5feuilles/sixcas humains Non testé.
[Guide727](../LIASSE_BALANCES_TVA_727.md), [rapport](../../Test/rapport_balance_tva727.md),
[livraisons](LIVRAISONS_SESSION_20261022_725_727.md), [reprise](REPRISE_APRES_TVA_727.md).
LIA-09D reste partiel, statuts globaux inchangés. Suite C3 N-2/extra-comptable
et fiscalité externe complète sur sources explicites ; RH/paie etpoint6 différés.

Complément725 : B12 autonome depuis la balance N, net/67/avant impôts distincts,
base fiscale pure partagée et taux/déficit explicitement déclarés, inconnus
préservés. IS théorique distinct du montant à payer ; CM/CSS/crédits/acomptes/
solde final inconnus, aucune liquidation ou Journal réel lus ou modifiés.
passage725_api: 50 réussis en 56.01s ; passage725_cible: 9 réussis en 119.97s ; passage725_commune: 295 réussis en 317.1s ; passage725_annuel: 2 réussis en 37.83s. Aucun échec/erreur/ignoré, campagnes recouvrantes. Build7,04s code0 ; 11Python compilés ;1153SHA stables ; restauration104/83tables/5fichiers ;108SQL/bootstrap protégés. Guide7pages/Excel5feuilles/sixcas humains Non testé.
[Guide725](../LIASSE_BALANCES_PASSAGE_FISCAL_725.md), [rapport](../../Test/rapport_balance_passage_fiscal725.md),
[livraisons](LIVRAISONS_SESSION_20261022_725.md), [reprise](REPRISE_APRES_PASSAGE_FISCAL_725.md).
LIA-09D reste partiel, statuts globaux inchangés. B14 et sources fiscales/extra-
comptables à poursuivre ; RH/paie etpoint6 humain différés.

Complément723 : C3 comptable indépendant depuis N/N-1, moteur partagé en
Decimal exact, comparatifs aux états figés et inconnus N-2/extra-comptable
préservés. Garde119 commune B11/B13/C3 ; faux0 B11 historique reproduit puis
corrigé, sans réécrire les snapshots. Situation nette après119 sans double
ajout, activité indisponible. Contrat historique C3 préservé, aucun Journal/RH lu.
27calculs/API dont2historiques53,79s ;8Edge+restauration1 169,44s ;195connexes469,39s ;2annuels66,80s.0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build9,38s code0,14Python compilés,1147SHA figés. Restauration10483tables/5fichiers ; témoins et exports conservés.108SQL/bootstrap protégés. Guide Word/PDF7pages/Excel5feuilles/sixcas humains Non testé, troisCSV équilibrés.
[Guide723](../LIASSE_BALANCES_INDICATEURS_723.md), [rapport](../../Test/rapport_balance_indicateurs723.md),
[livraisons](LIVRAISONS_SESSION_20261021_721_723.md), [reprise](REPRISE_APRES_INDICATEURS_723.md).
LIA-09D et statuts globaux inchangés ; C3 réglementaire complet et fiscalité
autonome partiels, recette humaine/production nonvalidées. Suite B12/B14 et
sources historiques/extra-comptables explicites ; RH/paie etpoint6 différés.


Complément721 : résultat courant documentaire B13 depuis les seules sources
N/N-1. Périmètre71/73 moins61/63 et rapprochement au CPC VII figé ; compte67
comptabilisé présenté séparément, jamais assimilé à un impôt théorique courant.
Une synthèse explicitement sourcée par période, réintégrations/déductions/impôt
théorique déclarés, inconnus conservés, équations documentaires sans taux ni
liquidation. Anciennes balances119 sans drapeau CPC protégées contre le faux0.
Versions/droits/UUID/SHAparent/MAD, brouillons et contrôles figés, exports/logo,
restauration et autres compléments réellement testés.
40calculs/API 74.53s,8Edge+restauration1 180.36s,486connexes 2109.50s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build14,87s code0,10Python compilés,1140SHA figés. Restauration10483tables/5fichiers, témoins conservés.108SQL/bootstrap et moteurs comptables existants inchangés. Guide Word/PDF7pages/Excel5feuilles,six cas humains Non testé ; Office non ouvert.
[Guide721](../LIASSE_BALANCES_RESULTAT_COURANT_721.md),
[rapport721](../../Test/rapport_balance_resultat_courant721.md),
[livraisons721](LIVRAISONS_SESSION_20261021_721.md).
LIA-09D/statuts globaux inchangés ; fiscalité autonome encore partielle,
recette humaine/installation cible/production nonvalidées. Prochaine zone C3,
puis B12/B14 selon [reprise721](REPRISE_APRES_RESULTAT_COURANT_721.md).
RH/paie et point6 humain différés.


Contrôle719 : cohabitation du parcours annuel bancaire connecté avec
les préparations715 dans la même société fictive. Factures/validation/comptabilisation,
règlements ventilés, lettrage, rapprochement, clôture2025/AN2026, paiements2026,
FEC et balance, puis préparation indépendante sans altération du Journal.
Banque réelle du jeu comptable1000MAD contre source documentaire4200MAD :
les valeurs restent séparées et toutes les tables métier hors préparation/audit
restent identiques pendant la création/export des trois versions.
2tests réels réussis61,60s :oracle indépendant et parcours annuel bancaire Edge/API/PostgreSQL104 enrichi,0échec/erreur/ignoré,30warnings existants.1134SHA figés ; application715 et anciens tests inchangés. Toutes les tables métier hors préparation/audit et les lignes définitives restent identiques pendant création/export des trois versions. Banque Journal1000MAD distincte de source externe4200MAD ; FEC2025/2026 et balance2026 contrôlés après. Un Python compilé ; cluster/application jetables nettoyés.
[Rapport719](../../Test/rapport_cohabitation_annuelle719.md),
[livraisons](LIVRAISONS_SESSION_20261021_707_717.md).
Un parcours et son oracle, pas une réexécution des347cas701 ni une recette humaine.
LIA-09D/statuts globaux inchangés ; fiscalité autonome encore partielle,
RH/paie et point6 humain différés ; production nonvalidée.


Complément717 : cahier consolidé Word/PDF23pages et Excel9feuilles,
30cas humains Non testé des cinq compléments707–715, avec données exactes,
parcours, résultats attendus, preuves/anomalies et suivi de progression.
Trois jeux fictifs distincts, sans confusion entre leurs registres. Correction
minimale du lecteur UTF8-BOM Windows ; titres Word/PDF711/713 régénérés, cinq
classeurs individuels préservés octet par octet. 8contrôles documentaires réussis1,92s,0échec/erreur/ignoré après régression1réussi/1échec attendu1,22s avec6non sélectionnés.3Python compilés.1132empreintes715 intactes, backend/frontend et anciens tests inchangés. Word/PDF23pages,Excel9feuilles,30cas humains Non testé ;5Excel préservés. Aucune base contactée ; dernier build71510,70s et438connexes1713,49s restent les validations applicatives de715.
[Livraisons](LIVRAISONS_SESSION_20261021_707_717.md),
[cahier](../recette/CAHIER_PREPARATIONS_BALANCES_717.md),
[rapport717](../../Test/rapport_cahier_preparations717.md).
Les statuts globaux ne changent pas : recette humaine/production nonvalidées.
Suite : contrôle de cohabitation annuelle puis sources fiscales autonomes.
RH/paie et point6 humain différés.


Complément715 : rattachements explicites des clôtures B2/B2bis/B5 aux
comptes réellement présents dans la source N figée, périmètres techniques
HisabPro existants. Multi-lignes par compte ; clôtures inconnues, non-rattachées
et comptes sans détail visibles sans faux0. Contrôles figés somme déclarée
moins solde source, signes inverses préservés. Double empreinte mouvements/N :
une révision rend l’ancien contrôle explicitement À refaire, sans recalcul ou
réemploi silencieux des choix. Les anciennes clôtures/références restent dans
les exports, distinctes du contexte courant. Versions, droits, mobile/longs
textes, exports/logo et restauration réellement testés.
28calculs/API 69.71s,9Edge+restauration 164.09s,438connexes 1713.49s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build10,70s code0,10Python compilés,1132SHA figés. Restauration10483tables/5fichiers et témoins conservés.108SQL/bootstrap et moteurs comptables inchangés. Guide Word/PDF8pages/Excel5feuilles,six cas humains Non testé, Office non ouvert.
[Guide](../LIASSE_BALANCES_RACCORDS_715.md), [rapport715](../../Test/rapport_balance_raccords715.md).
LIA-09D et statuts globaux inchangés ; recette humaine/production nonvalidées.
Suite : guide consolidé des compléments, puis sources fiscales autonomes.
RH/paie et point6 humain différés.


Complément713 : mouvements documentaires B2/B2bis/B5 de l’exercice N,
ouvertures/augmentations/diminutions/clôtures depuis sources explicites, sans
inférence de N/N-1. Contrôles figés ouverture+augmentations−diminutions puis
clôture déclarée−reconstituée ; inconnus distincts de0 et soldes inverses signés.
Chaque tableau conserve ses totaux séparément ; aucun raccord au bilan/registre
ou aux cessions B3 prouvé par cette seule équation. Versions immuables,
brouillon distinct des contrôles, exports/logo et restauration testés.
25calculs/API 66.78s,8Edge+restauration 159.73s,401connexes 1615.49s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build6,77s code0,10Python compilés,1126SHA figés. Restauration10483tables/5fichiers et témoins conservés.108SQL/bootstrap et moteurs comptables inchangés. Guide Word/PDF7pages/Excel5feuilles,six cas humains Non testé, Office non ouvert.
[Guide](../LIASSE_BALANCES_MOUVEMENTS_713.md), [rapport713](../../Test/rapport_balance_mouvements713.md).
LIA-09D et statuts globaux inchangés ; recette humaine/production nonvalidées.
Suite : rattachements explicites des clôtures aux comptes sources, sans auto-attribution,
puis sources fiscales autonomes. RH/paie et point6 différés.


Complément711 : cessions/retraits B3 déclarés depuis sources explicites,
sans inférence de mouvements à partir des balances. Date/type facultatifs ;
valeur d’entrée/VNA/prix inconnus distincts de0, différence prix−VNA figée et
signée, sans calcul fiscal. Alertes date hors période et VNA supérieure à entrée,
aucune correction automatique. Brouillon distinct des contrôles conservés ;
versions immuables, exports/logo/manifeste et restauration réellement testés.
24calculs/API 64.36s,8Edge+restauration 158.65s,368connexes 1368.78s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build6,16s code0,10Python compilés,1120SHA figés. Restauration10483tables/5fichiers et témoins conservés.108SQL/bootstrap et moteurs comptables inchangés. Guide Word/PDF7pages/Excel5feuilles,six cas humains Non testé, Office non ouvert.
[Guide](../LIASSE_BALANCES_CESSIONS_711.md), [rapport711](../../Test/rapport_balance_cessions711.md).
LIA-09D et statuts globaux inchangés ; recette humaine/production nonvalidées.
B2/B2bis/B5 et sources fiscales restent distincts ; RH/paie et point6 différés.


Complément709 : déclarations sourcées des émetteurs N/N-1 par compte251
réellement présent dans chaque balance conservée. Émetteur, identifiant facultatif,
valeur brute, capital, quote-part et produits reçus restent explicitement déclarés ;
inconnus distincts de0. Contrôles figés somme brute déclarée moins solde251, écarts
signés sans correction ; aucune somme de pourcentages entre sociétés ni ratio inféré.
Brouillon distinct des contrôles conservés ; versions immuables, exports/logos et
restauration testés. 28API/calculs 40.79s puis8Edge+restauration 113.42s puis336connexes 801.76s,0échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes. Build4,96s code0 ; 10Python compilés,1114SHA figés. Restauration10483tables/5fichiers et témoins conservés.108SQL/bootstrap et moteurs comptables inchangés. Guide Word/PDF7pages/Excel5feuilles,six cas humains Non testé, Office non ouvert.
[Guide](../LIASSE_BALANCES_EMETTEURS_709.md), [rapport709](../../Test/rapport_balance_emetteurs709.md).
LIA-09D et statuts globaux inchangés ; recette humaine/production nonvalidées.
Prochaine étape : mouvements ETIC sur sources explicites, sans les déduire de N/N-1.
RH/paie et point6 humain différés.


Complément707 : détail B4 des titres251, décomposition séparée des autres
soldes financiers24/25 et contrôle du brut entier sur la même rubrique du bilan
figé. Aucun écart trompeur du seul251 avec24/25 ; informations émetteur, capital,
quote-part et produits reçus inconnus et à documenter séparément. Nouvelle version
immuable et exports PDF/Excel/ZIP avec logo actuel ; calculs exacts conservés.
44 tests ciblés en 333.46s puis300connexes en 1053.59s réussis,
zéro échec/erreur/ignoré,30warnings existants ; campagnes recouvrantes.
Build5,02s,1108SHA app/Test figés,108SQL/bootstrap et moteurs financiers inchangés.
Restauration83tables/cinq fichiers et témoins B4/B1/B11 intacts.
[Guide](../LIASSE_BALANCES_PARTICIPATIONS_707.md), [rapport707](../../Test/rapport_balance_participations707.md).
Word/PDF7pages/Excel5feuilles,six cas humains Non testé. Deux CSV/JSON
fictifs et oracle indépendant : N titres4000/autres2000/brut6000MAD, N-1 3000/1000/4000.
LIA-09D et statuts globaux inchangés ; recette humaine et production nonvalidées.
Prochaine étape : déclarations sourcées par émetteur, sans inférence de la balance.
RH/paie et point6 différés ; autres mouvements ETIC/fiscalité encore partiels.


Complément705 : détail B1 des non-valeurs depuis les seules balances exactes
conservées, contrôle brut21/amortissements groupés281/net, comparaison avec
la rubrique21 du bilan figé. Soldes inverses et écarts préservés, sans allocation
par compte21, déduction de flux bruts, libellé historique inventé ou faux zéro.
Nouvelle version immuable via service partagé ; interface commune B1/B11.
35 tests ciblés en 257.67s puis271 connexes en 978.81s
réussis, zéro échec/erreur/ignoré ; campagnes recouvrantes,30warnings existants.
Build5,31s,1102empreintes app/Test figées,108 SQL/bootstrap et moteurs comptables
inchangés ; restauration83tables/cinq fichiers, témoins et versions B1/B11 intacts.
[Guide](../LIASSE_BALANCES_NON_VALEURS_705.md), [rapport705](../../Test/rapport_balance_non_valeurs705.md).
Word/PDF7pages/Excel5feuilles et six cas humains Non testé.
Oracle fictif N4000−1000=3000MAD, N-1 3000−500=2500MAD, bilan10000MAD
vérifié indépendamment et par moteur pur sans connexion PostgreSQL.
LIA-09D et statuts globaux inchangés ; recette humaine/production nonvalidées.
RH/paie et point6 différés ; autres ETIC et sources fiscales encore à compléter.


Complément703 : détail B11 du CPC depuis les seules balances exactes conservées,
charges et produits signés, rapprochement avec le CPC figé et écarts explicites.
Nouvelle version immuable, calcul/méthode/titre/auteur/source figés ; lecture et
exports sans recalcul. Libellés historiques absents signalés ; sources manquantes,
N-1 absent et solde technique119 restent indisponibles, jamais un zéro fabriqué.
32 tests ciblés en 192.79s puis244 tests connexes en 864.69s réussis,
zéro échec/erreur/ignoré. Campagnes recouvrantes,30 avertissements existants.
Build10,94s ;1095empreintes app/Test stables ;108fichiers SQL/bootstrap et moteurs
partagés inchangés ; restauration83tables/cinq fichiers et témoins indépendants intacts.
[Guide](../LIASSE_BALANCES_DETAIL_CPC_703.md), [rapport703](../../Test/rapport_balance_cpc703.md).
Word/PDF8pages/Excel5feuilles : sept cas humains Non testé, données
fictives équilibrées et oracle indépendant900,19MAD contrôlé sans base réelle.
LIA-09D reste partiel, statuts globaux inchangés ; recette humaine et production
nonvalidées. Prochaine cible B1 non-valeurs sur sources certaines, sans déduire
les mouvements bruts des seules balances. RH/paie et point6 humain différés.


Complément701 : contrôles arithmétiques C1 figés dans les nouvelles versions
(documentaire uniquement) : titres × nominal, sommes et écarts des capitaux,
rapprochement indicatif au solde des comptes 111 fournis et somme des pourcentages.
Inconnus préservés, écarts de centimes visibles sans ajustement ; anciennes
versions sans recalcul et brouillons distingués des valeurs conservées.
16 tests ciblés en 164,60s puis 213 tests connexes en 778.29s et 347 du socle
annuel en 1793.19s réussis, zéro échec/erreur/ignoré. Campagnes recouvrantes.
Build 6,14 s, 1 089 empreintes app/Test figées,108 fichiers SQL/bootstrap et moteurs comptables partagés inchangés ;
restauration de 83 tables/cinq fichiers et témoins indépendants préservés.
[Guide](../LIASSE_BALANCES_CONTROLES_CAPITAL_701.md), [rapport701](../../Test/rapport_balance_capital701.md).
Word/PDF de 5 pages/Excel de 5 feuilles et quatre cas humains Non testé. Guide consolidé de session : Word, PDF13pages, Excel7feuilles et16cas humains Non testé.
Un écart nul ne prouve pas l’exhaustivité juridique ou la conformité fiscale.
LIA-09D reste partiel ; RH/paie et point6 humain restent différés.


Complément699 : six annexes manuelles documentaires A2/A3/B10/C1/C2/C4,
sources, déclarations explicites, dates historiques et unités MAD/titres/%.
Montants inconnus préservés, pourcentages à douze décimales et titres à dix-huit
chiffres conservés exactement ; aucune conversion de devise présumée.
36 tests ciblés puis 198 tests connexes réussis en 776.78s, build 5,32 s,
restauration de 83 tables/cinq fichiers. 1 083 empreintes app/Test et 108 fichiers SQL/bootstrap
conservés. Les campagnes recouvrantes ne s’additionnent pas en cas uniques.
[Guide](../LIASSE_BALANCES_ANNEXES_ETIC_699.md), [rapport699](../../Test/rapport_balance_etic_annexes699.md).
Word/PDF de 7 pages/Excel de 5 feuilles et six cas humains Non testé ; jeu humain cohérent
avec capital/produits de la balance695, distinct des stress-tests de précision.
Les huit tableaux de type manuel/table du catalogue existant sont désormais
saisissables en mode indépendant avec 697/699. LIA-09D reste partiel : autres
états ETIC automatiques/assistés et compléments fiscaux à traiter.
RH/paie et point6 différés ; recette humaine et production non validées.


Complément697 : tableaux B8/B9 documentaires dans Liasse seule, sources et
inconnus explicites, néant justifié, nouvelles versions immuables et alerte sur
notes contradictoires. PDF/Excel/ZIP cohérents avec logo actuel et manifeste.
26 tests ciblés puis163 tests connexes réussis en 625.91s, build5,86s, restauration83 tables/
cinq fichiers ;1 077empreintes app/Test et108 fichiers SQL/bootstrap conservés.
[Guide](../LIASSE_BALANCES_TABLEAUX_ETIC_697.md), [rapport697](../../Test/rapport_balance_etic_tables697.md).
Six cas humains Non testé en Word/PDF de 6 pages/Excel de 5 feuilles. LIA-09D reste partiel :
ce sont des compléments documentaires, pas une liasse officielle complète.
RH/paie et point6 humain différés ; recette utilisateur et production non validées.


Campagne élargie695 :347tests réussis1810,38s, zéro échec/erreur/ignoré. Sources et témoins conservés, restauration83tables/cinq fichiers ; [rapport695](../../Test/rapport_balance_financement695.md).

Complément695 : financement documentaire depuis balances conservées, flux N/N-1
explicitement justifiés et calcul figé du moteur partagé. Masses, CAF, totaux et
écarts affichés ; données inconnues préservées, aucune déduction de flux bruts
depuis les variations nettes.138tests du périmètre réussis et24tests du moteur.
[Guide](../LIASSE_BALANCES_FINANCEMENT_695.md). LIA-09D reste partiel : autres
tableaux ETIC structurés et compléments fiscaux encore nécessaires, pas de
dossier automatiquement prêt à déposer. Statuts globaux inchangés.

Complément693 : notes documentaires par rubrique du catalogue ETIC existant,
états explicites/justifications, auteur et catalogue figés, nouvelle version
immuable et PDF/Excel/ZIP cohérents. [Guide](../LIASSE_BALANCES_NOTES_ETIC_693.md).
Ce sont des notes de préparation : LIA-09D reste partiel, les tableaux ETIC
structurés et les flux de financement restent à compléter. Aucun statut global promu.

Complément691 : pièces justificatives des préparations, auteur/SHA/taille figés,
lecture et octets contrôlés, ajout au dossierZIP.104 additive manuelle et
restauration83tables/cinq fichiers qualifiées ;445testsA puis33ciblésB après
correction de tailleUI, backend/SQL identiques. [Rapport](../../Test/rapport_balance_documents691.md).
LIA-09D reste partiel ; ces pièces ne certifient pas la complétude fiscale.

Complément689 : dossier partageable d’une préparation conservée, PDF/XLSX et
sources normalisées avec manifesteSHA-256 ;46tests finaux réussis137,87s,
restauration82tables et build4,72s. [Rapport](../../Test/rapport_balance_dossier689.md).
LIA-09D demeure partiel, aucun statut global promu ni archive officielle déduite.

Complément687 : [échéances documentaires sur balances conservées](../LIASSE_BALANCES_ECHEANCES_687.md),
saisie justifiée/partielle, inconnus et reliquats visibles, nouvelle version
immuable et exports cohérents. LIA-09D reste partiel : pas d’ETIC officielle
complète, de flux de financement ni de liquidation déduits. Les statuts globaux
ne sont pas promus. [Rapport technique](../../Test/rapport_balance_echeances687.md).

Point vérifié le21octobre2026 : **681**, rapprochements documentaires RAS
partiels, retraits immuables et PDF avec logo ;347tests finaux réussis en1942,84s,
build11,72s. Installation/restauration103 sur clusters jetables,390sources et
témoins non vides conservés ; [rapport](../../Test/rapport_ras_rapprochements681.md).
Cahier complémentaire Word/PDF/Excel,15cas humains Non testé ; quatre contrôles
documentaires/oracle natif réussis en29,20s. Aucun statut global promu :
70fonctions,16terminé/47partiel/3absent/4bloqué ; checklist73 inchangée.
FIS-02 reste partiel : le rapprochement ne certifie aucun versement DGI,
déclaration ou crédit. [Bilan actuel](RAPPORT_SESSION_20261020_677_681.md).

Complément679 : [consultation détaillée des préparations conservées](../../Test/rapport_balance_detail679.md),
avec comptes sources N/N-1, filtre/pagination et présentation commune aux exports.
LIA-09D reste partiel ; aucun statut global promu par cette consultation.

Complément677 : préparations de balances PDF/XLSX détaillées et traçables,
62tests réussis en104,66s, build6,38s ; [preuves](../../Test/rapport_balance_exports677.md).
LIA-09D reste partiel : dossier fiscal autonome complet non déduit des balances.
Les70statuts globaux restent16terminé/47partiel/3absent/4bloqué.

Dernier point vérifié :20octobre2026, lots591–675. Préparation RAS mensuelle, calcul documentaire CCA/PCA, cahier complémentaire PDF/Excel, clôture interexercices et suivi des contrepassations qualifiés en laboratoire ; comptes de provision contrôlés par type. Statuts globaux inchangés :16 terminé,47 partiel,3 absent,4 bloqué. Les résultats humains restent à renseigner ; déclaration TVA complète/versement et dossiers historiques de provisions restent partiels.

Stabilisation bornée clôturée675 :312cas réussis en1424,85s sans échec/erreur/ignoré,
382sources et témoins non vides préservés, installation102 et build9,48s réussis.
CLI102 :schéma/ACL/rejeux et runtime partiel ; banc applicatif102 distinct.
106fichiers protégés et63archives antérieures vérifiés. Les statuts globaux ne
sont pas promus. [Bilan final675](RAPPORT_STABILISATION_HORS_RH_20261020.md).

Stabilisation673 : mélange achat/vente et limite100 des factures corrigés,
cinq listes avec panne/vide/reprise/contextes distincts.28tests actuels réussis
en189,81s avec les achats complets/partiels ; build6,96s. Le timeoutlogin de
la campagne précédente reste documenté. [Preuves673](../../Test/rapport_listes_commerciales673.md)
et [liste bornée de sortie](FIN_DEVELOPPEMENT_HORS_RH_20261020.md).

[Rapport précédent645–671](RAPPORT_SESSION_20261019_645_671.md), [rapport633–643](RAPPORT_SESSION_20261019_633_643.md), [rapport précédent615–631](RAPPORT_SESSION_20261019_615_631.md), [rapport précédent571–589](RAPPORT_SESSION_20261018_RAS_TVA.md), [reprise précédente553–569](RAPPORT_SESSION_20261018_HORS_RH.md) et [plan restant hors RH](PLAN_FINALISATION_HORS_RH_20261018.md). [Session antérieure](RAPPORT_SESSION_20261016.md).

Reprise du 7 octobre 2026 à 06:21 UTC, interrompue par le quota.
Nouvelle exécution demandée par l'utilisateur à 11:34 UTC, limite 13:34 UTC.
Reprise après quota à 17:03 UTC, limite de cette exécution 19:03 UTC.
Reprise après quota à 21:58 UTC, limite 23:58 UTC (8 octobre à 01:58 Paris).
Reprise suivante le8octobre04:54UTC, limite06:54UTC ; aucun Python de tests encore actif à la reprise.
Reprise du 8 octobre à 11:16 UTC après correction du démarrage ; limite 13:16 UTC. Backend et Vite de l'utilisateur actifs et laissés intacts.

Reprise du 8 octobre 17:52 UTC : bilan détaillé livré. Reprise à 23:01 UTC interrompue par quota ; nouvelle exécution du 9 octobre 14:04–16:04 UTC. Lots 266–280 vérifiés dans le dépôt et les archives, sans réapplication.

Cette matrice est fondée sur les fichiers, migrations et tests du dépôt courant.
Les 17 ZIPs 114–131 puis les archives jusqu'à 159 ont été inspectés :
45 ZIPs différentiels, CRC valides et fichiers présents. Les dernières versions
archivées correspondent au dépôt, sauf les trois fichiers du mot de passe
personnel, désormais livrés dans le ZIP160. Aucun patch ancien réappliqué.
Il n'y a pas de dépôt Git local ; une empreinte initiale de 446 fichiers sert au
contrôle des différentiels. Les caches, environnements et données de test ne sont pas livrés.

**Développement global : partiel. Tests automatisés : exécutions détaillées dans
CODEX_PROGRESS.md. Recette utilisateur : à effectuer. Production : non validée.**

« Terminé » désigne ici un périmètre implémenté avec des tests ciblés réellement
exécutés, jamais une certification ou une recette utilisateur complète.
« Partiel » indique une intégration, couverture ou fonction manquante.
« Absent » signifie qu'aucune implémentation exploitable n'a été retrouvée.
« Bloqué » exige une source officielle, des pièces ou une décision humaine.

Comptage des70 lignes fonctionnelles vérifié le18octobre2026 :
**16 terminé,47 partiel,3 absent,4 bloqué**. Les73 demandes de la checklist
utilisateur utilisent un découpage distinct ; leurs totaux ne sont pas additionnés.

| ID | Domaine / fonction | Statut | Preuve dans le dépôt | Limite / prochaine validation |
|---|---|---|---|---|
| ADM-01 | Inscription et création d'une société | terminé | auth.py, multi_societes.py ; ZIP 158 ; [447](../../Test/rapport_multi_societes_runtime_447.md) | Création primaire et secondaire, plan et exercice vérifiés via API/Edge sous LOGIN SQL limité. Recette utilisateur complète à effectuer. |
| ADM-02 | Multi-société et changement de contexte | partiel | multi_societes.py ; [447](../../Test/rapport_multi_societes_runtime_447.md) | Création, switch JWT, liste autorisée et rechargement testés sous rôle SQL applicatif ; 090 ajoute uniquement les droits des liaisons. [633](../../Test/rapport_societes_liees633.md) et [635](../../Test/rapport_factures_liees635.md) : associations déclarées, achat correspondant et deux Journaux via flux ordinaires qualifiés ; paiements/avoirs/livraisons non répliqués et consolidation fiscale absente. Recette humaine et installation101/102 à effectuer. |
| ADM-03 | Utilisateurs, invités, RBAC et dernier administrateur | partiel | utilisateurs.py, utilisateurs_acces_service.py ; ZIP 144/146/154 ; [447](../../Test/rapport_multi_societes_runtime_447.md) ; [457](../../Test/rapport_journal_lecture_457.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md)  ; [545](../../Test/rapport_credits_consultation_seule_545.md) | Invitation, lecture→comptable avec droits relus, désactivation/réactivation/suppression secondaire, compte personnel et dernier administrateur protégés. 090 limite UPDATE aux colonnes rôle/activation. Autres parcours/rôles restent à étendre. Journal en consultation seule : commandes de mutation indisponibles, pièces/audit/diagnostics accessibles et aucun POST automatique FEC. Comptable conserve ses compléments ; backend 403 inchangé, autres écrans à étendre.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts.  Complément545 : consultation seule Avoirs/Acomptes sans commande de mutation, historique actif/crédit libre/chèque en attente/PDF conservés ;6Edge vente/achat lecteur390/1440 et comptable1440,28connexes et build réussis.403 directs et absence de mutation vérifiés. Aucun calcul ou droit serveur changé ; autres écrans distincts. |
| ADM-04 | Identité juridique/fiscale et paramètres | partiel | societe.py, parametres.py, identifiants_maroc_service.py ; migrations043/055/063 ; [462](../../Test/rapport_logos_exports_462.md), [463](../../Test/rapport_logos_xlsx_463.md), [466](../../Test/rapport_logos_impression_466.md)  ; [547](../../Test/rapport_grh_registre_pdf_547.md) | Ne pas inventer IF/ICE ; qualité des données réelle à contrôler Logo facultatif repris dans les PDF/XLSX générés et impressions, identité attendue avant export ; anciennes références URL/chemins à réimporter en image intégrée.  Complément547 : registre interne congés/absences PDF avec société/logo, filtre de statut, périodes/jours calendaires et historique déclarés. Admin/lecteur,2sociétés,notes longues et Edge390/1440,5ciblés/208connexes et build réussis, lecture sans mutation. Aucun calcul de congé acquis/paie/taux ni déclaration sociale ajouté ; statut global partiel conservé. |
| ADM-05 | Exercices et périodes | partiel | exercices.py, exercices_service.py ; migrations008/055/059 ; ZIP139/158 | GET pur et gestion UI livrés ; calendrier décalé et clôture annuelle connectée restent à étendre |
| ADM-06 | Journaux et numérotation | partiel | ecritures.py ; migrations015/017/018/019 ; tests07B/07C ; [464](../../Test/rapport_modeles_avances_464.md) | Vérifier concurrence et migrations dans PostgreSQL isolé Journal SA déjà présent aligné dans le schéma de saisie API ; CL reste réservé au moteur de clôture. |
| ADM-07 | Plan comptable par société | terminé | plan_comptable.py, models.CompteSociete ; migration055 ; tests055/058/064  ; [516](../../Test/rapport_commerce_logos_runtime_516.md) | Création/import d'une subdivision et permissions à inclure dans E2E  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur. |
| ADM-08 | Démarrage et privilèges production | partiel | production_bootstrap_service.py, grh_bootstrap_service.py ; [installation090](../../Test/rapport_installation_vierge_090.md) ; [448](../../Test/rapport_consolidation_runtime_448.md) ; [472](../../Test/rapport_tva_parametres_runtime_472.md) ; [480](../../Test/rapport_protection_sql_tva_480.md)  ; [530](../../Test/rapport_reglements_sources_concurrence_530.md) | Protection de démarrage employés/société déjà présente et préservée. 085–091 restent manuelles, hors bootstrap ; aucune base réelle migrée. LOGIN non propriétaire et privilèges fermés vérifiés sur les parcours couverts ; provisionnement exhaustif et déploiement encore partiels. Migrations manuelles jusqu’à093 ; seuls INSERT et UPDATE de trois colonnes des paramètres TVA ajoutés, identités/suppression/SETVAL protégés. Aucune migration réelle exécutée.  Migration094 additive, manuelle : aucun DML, ancien/nouveau périmètre clôturé protégés, anciennesACL conservées et EXECUTE sur deux nouvelles fonctions invoker seulement.  Complément530 : comptabilisation de règlement sérialisée avec modification/suppression/annulation ; lecture RAS compatible LOGIN limité sans élargir UPDATE. 16 nouveaux cas et 110 connexes exécutés, vente/achat → validation → lettrage → pointage, annulations Edge et permissions. Autres sources historiques/accès hors API distincts. |
| ADM-09 | Sauvegarde et restauration isolée | terminé | ops/postgres_sauvegarde.py ; ZIP 239/246/250 ; [446](../../Test/rapport_restauration_runtime_acl_446.md) ; [090](../../Test/rapport_multi_societes_runtime_447.md) ; [452](../../Test/rapport_restauration_justificatifs_452.md) ; [468](../../Test/rapport_restauration_logos_modeles_468.md), [472](../../Test/rapport_tva_parametres_runtime_472.md) ; [480](../../Test/rapport_protection_sql_tva_480.md)  ; [549](../../Test/rapport_restauration_grh_registre_549.md) | Défaut sans ACL préservé ; option explicite de copie native des droits. Schéma/73 tables/séquences et ACL relations/colonnes/fonctions identiques, FEC identique et nouveau cycle runtime 360 après restore ; 26 droits de colonnes restaurés en 090. Cible vide/nonce, rôles préparés séparément. Production, propriétaires différents à qualifier. Restauration conjointe 091 sur cible vide : 73 tables/schéma/séquences/ACL, quatre PDF et décision/PV fictifs restitués ; reprise du vrai main:app sous LOGIN limité. Même propriétaire migrateur ; production et autres propriétaires non qualifiés. Restauration native avec logos,64modèles et ACL093 :73tables/schéma/données/séquences/droits identiques avant reprise, pièces et FEC préservés. Autres propriétaires et production non qualifiés.  Restauration094 à froid réussie :73tables/schéma/données/séquences/ACL,quatre pièces,FEC etsource préservés.  Complément549 : restauration froide098 réellement exécutée avec données GRH, logo et historique ;74tables/schéma/données/ACL,source préservée et cibles nettoyées. JSON identique et texte PDF identique hors heure d’édition sous LOGIN non propriétaire ;1test61.21s réussi. Aucune restauration de production ni recette utilisateur validée. |
| ADM-10 | Changement du mot de passe personnel | terminé | CompteSecurite.jsx, routers/auth.py ; ZIP160 | 14 tests exécutés cette reprise : API, Edge et PG isolé ; JWT historiques sans version restent compatibles jusqu'à expiration |
| FAC-01 | Devis, commandes et conversions partielles | partiel | routers/commercial.py ; migrations028–046 ; tests fact2/fact3/factC ; ZIP241/242/248/249/251/254 ; [cycle runtime436](../../Test/rapport_permissions_documents_commerciaux_436.md)  ; [516](../../Test/rapport_commerce_logos_runtime_516.md)  ; [543](../../Test/rapport_factures_finalisation_concurrente_543.md) | Alerte autorisant devis à approvisionner, cumul par article, services exclus et inconnus visibles. Deux Edge création/édition, relecture et réponse tardive ignorée ; API76tests et limites représentation35tests. Totaux calcules non finis refuses avant mutation254 :127connexes puis15finaux. Historiques consultables sans réparation. Conversion et variantes annuelles à compléter ; stock actuel sans réservation. 085 permet le cycle documentaire vente/achat sous rôle SQL applicatif ; quatre variantes service/stock, doublons refusés et origines conservées.  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur.  Complément543 : double validation/conversion vente et achat sans erreur500 ; parent relu sous verrou, validation200/200 même numéro et conversion200/400, un seul mouvement de stock2→1/3, répétition sans mutation puis comptabilisation/validation/FEC.4nouveaux et356+247exécutions finales sur sources figées ; aucune garde SQL retirée. |
| FAC-02 | Livraisons et réceptions | partiel | commercial.py, valorisation.py ; ZIP240/271/280 ; [cycle runtime436](../../Test/rapport_permissions_documents_commerciaux_436.md)  ; [516](../../Test/rapport_commerce_logos_runtime_516.md) | Pièces client avec SHA et permissions testées240. Achat BC→BR→facture271 testé desktop/mobile, liens conservés et stock unique. Réceptions partielles280 avec paramètre br : entrées1+3, stock4, aucune seconde entrée aux factures ; autres variantes annuelles restent à étendre. BC→BL/BR→facture également exécuté sous rôle SQL non propriétaire, avec stock unique et lettrage.  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur. |
| FAC-03 | Factures clients et fournisseurs | partiel | factures.py, Factures.jsx ; ZIP162/271/275/280/363  ; [516](../../Test/rapport_commerce_logos_runtime_516.md)  ; [536](../../Test/rapport_journal_sources_factures_ras_536.md)  ; [538](../../Test/rapport_factures_comptabilisation_concurrence_538.md)  ; [541](../../Test/rapport_factures_proforma_lecture_541.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md)  ; [543](../../Test/rapport_factures_finalisation_concurrente_543.md) | Édition de qualification TVA achat275 réelle sur deux largeurs : charge80 donne1040/160/1200, non déductible0 et historiques inconnus préservés ; pièces définitives protégées. Deux factures partielles280 total2000/400/2400. Ces choix de laboratoire ne valident pas un droit fiscal réel. Lecture363 :JSON200 qualifié, identités/lignes conservées, inconnus et détail lecture seule ;40ciblés,6sources/avoirs liés,8Edge finaux réussis. Diagnostic359 conservé ; sa suite originale passe8cas après correction. Aucune réparation des données ; parcours annuel complet reste à étendre.  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur.  Complément536 : suppression facture fournisseur et recomptabilisation cohérentes, vraie création auditée prioritaire sur référence renommée/en collision ; date/auxiliaires contradictoires refusés, RAS distincte conservée.17nouveaux/171connexes réussis ; baseline ne reconstitue pas une création et historique manquant reste à vérifier.  Complément538 : deux demandes simultanées de comptabilisation facture vente/achat donnent200/409 et une seule pièce équilibrée, validée puis exportée au FEC. Avoir déjà verrouillé confirmé sans modification de son code ; origine définitive et audit conservés.4nouveaux cas et344+247exécutions finales en deux commandes, aucune réparation historique.  Complément541 : statut proforma existant restitué par création/liste API, sans préfixe déduit ni migration ;2parcours vente/achat PDF/conversion/comptabilisation/FEC et18connexes réussis. Recette visuelle540 reprise séparément.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts.  Complément543 : double validation/conversion vente et achat sans erreur500 ; parent relu sous verrou, validation200/200 même numéro et conversion200/400, un seul mouvement de stock2→1/3, répétition sans mutation puis comptabilisation/validation/FEC.4nouveaux et356+247exécutions finales sur sources figées ; aucune garde SQL retirée. |
| FAC-04 | Validation, écritures et snapshots documentaires | partiel | factures.py, compta_mapping_service.py ; tests factH/062/077 ; ZIP162  ; [516](../../Test/rapport_commerce_logos_runtime_516.md)  ; [536](../../Test/rapport_journal_sources_factures_ras_536.md)  ; [538](../../Test/rapport_factures_comptabilisation_concurrence_538.md)  ; [541](../../Test/rapport_factures_proforma_lecture_541.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md)  ; [543](../../Test/rapport_factures_finalisation_concurrente_543.md) | UI réelle : facture 1 200 TTC, validation, comptabilisation puis validation des écritures ; stock et PDF annuels à rapprocher  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur.  Complément536 : suppression facture fournisseur et recomptabilisation cohérentes, vraie création auditée prioritaire sur référence renommée/en collision ; date/auxiliaires contradictoires refusés, RAS distincte conservée.17nouveaux/171connexes réussis ; baseline ne reconstitue pas une création et historique manquant reste à vérifier.  Complément538 : deux demandes simultanées de comptabilisation facture vente/achat donnent200/409 et une seule pièce équilibrée, validée puis exportée au FEC. Avoir déjà verrouillé confirmé sans modification de son code ; origine définitive et audit conservés.4nouveaux cas et344+247exécutions finales en deux commandes, aucune réparation historique.  Complément541 : statut proforma existant restitué par création/liste API, sans préfixe déduit ni migration ;2parcours vente/achat PDF/conversion/comptabilisation/FEC et18connexes réussis. Recette visuelle540 reprise séparément.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts.  Complément543 : double validation/conversion vente et achat sans erreur500 ; parent relu sous verrou, validation200/200 même numéro et conversion200/400, un seul mouvement de stock2→1/3, répétition sans mutation puis comptabilisation/validation/FEC.4nouveaux et356+247exécutions finales sur sources figées ; aucune garde SQL retirée. |
| FAC-05 | Avoirs et annulations | partiel | avoirs.py, commercial.py ; ZIP183/267/272/309 ; [runtime437](../../Test/rapport_permissions_acomptes_avoirs_437.md) ; [concurrence438](../../Test/rapport_concurrence_avoirs_438.md)  ; [516](../../Test/rapport_commerce_logos_runtime_516.md)  ; [518](../../Test/rapport_mouvements_stock_cloture_518.md)  ; [538](../../Test/rapport_factures_comptabilisation_concurrence_538.md)  ; [545](../../Test/rapport_credits_consultation_seule_545.md) | Fournisseur267 : achat2×500, retour1, avoir600 puis paiement600 etAAA ; stock1,3écritures8lignes D=C2400. Deux Edge et connexes exécutés. AV unique filtre/sélecteur272, deux sources clients distinctes conservées ; ancien doublon utilisateur non reproduit. Lot309 : société source du crédit corrigée, verrou PostgreSQL limité aux avoirs ; 33 tests finaux passent, dont vente/achat, captures et isolation inter-société. Autres annulations annuelles restent à étendre. 086 minimale ; annulation d’utilisation corrigée sur PostgreSQL. Huit courses438 empêchent doubles AV/ANN et annulation après consommation, vente/achat ; une même identité authentifiée, pas une charge exhaustive.  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur.  Complément518 : moteur central des mouvements protégé pendant clôture/comptage/comptabilisation ; exercice décalé trouvé par dates, refus409 et reprise, sources conservées.312tests finaux réussis dont cycles commerciaux/logos après correction. Validité d’une photographie après mouvements successifs et SQL/Python directs restent distincts.  Complément538 : deux demandes simultanées de comptabilisation facture vente/achat donnent200/409 et une seule pièce équilibrée, validée puis exportée au FEC. Avoir déjà verrouillé confirmé sans modification de son code ; origine définitive et audit conservés.4nouveaux cas et344+247exécutions finales en deux commandes, aucune réparation historique.  Complément545 : consultation seule Avoirs/Acomptes sans commande de mutation, historique actif/crédit libre/chèque en attente/PDF conservés ;6Edge vente/achat lecteur390/1440 et comptable1440,28connexes et build réussis.403 directs et absence de mutation vérifiés. Aucun calcul ou droit serveur changé ; autres écrans distincts. |
| FAC-06 | Acomptes et imputations | partiel | acomptes.py ; migrations035/045 ; tests fact8/factG ; ZIP188/189/252 ; [runtime437](../../Test/rapport_permissions_acomptes_avoirs_437.md)  ; [545](../../Test/rapport_credits_consultation_seule_545.md) | Parcours connecté acompte400 + règlement800 sur facture1200, validation et lettrage testé ; montants non finis refusés. DeuxEdge fournisseur252 desktop/mobile valides jusquAAA ;4ecritures9lignesD=C2800,13tests regroupes. Recette annuelle etretours historiques restent a etendre. Avance60, imputations40/20 puis contrepassations sur deux factures120 : huit pièces, D=C480, sources préservées sous vrai LOGIN applicatif.  Complément545 : consultation seule Avoirs/Acomptes sans commande de mutation, historique actif/crédit libre/chèque en attente/PDF conservés ;6Edge vente/achat lecteur390/1440 et comptable1440,28connexes et build réussis.403 directs et absence de mutation vérifiés. Aucun calcul ou droit serveur changé ; autres écrans distincts. |
| FAC-07 | Règlements partiels et complets | partiel | commercial.py, ReglementParTiers.jsx ; [405](../../Test/rapport_rapprochement_propositions_405.md), [406](../../Test/rapport_encaissement_frais_406.md) ; [456](../../Test/rapport_instruments_runtime_456.md)  ; [530](../../Test/rapport_reglements_sources_concurrence_530.md)  ; [532](../../Test/rapport_reglements_annulation_sources_532.md)  ; [534](../../Test/rapport_journal_liberation_sources_534.md)  ; [536](../../Test/rapport_journal_sources_factures_ras_536.md) | Ventilation native atomique/rejouable et annulation collective conservées. Propositions exactes simple/lot immédiat ;frais individuels au centime. Instrument unique chèque/effet regroupé et historiques ambigus restent à traiter. Chèques/effets individuels avec frais, impayé remplacé et deux annuels rejoués sous LOGIN limité 091 : huit Edge et 79 connexes. Instruments groupés et escompte automatique restent partiels.  Complément530 : comptabilisation de règlement sérialisée avec modification/suppression/annulation ; lecture RAS compatible LOGIN limité sans élargir UPDATE. 16 nouveaux cas et 110 connexes exécutés, vente/achat → validation → lettrage → pointage, annulations Edge et permissions. Autres sources historiques/accès hors API distincts.  Complément532 : origine de règlement contrôlée (société/source/date/totaux/liaison unique), pas de fallback sur lien explicite incohérent ; correction existante refusée409, conflit Journal refusé sans interblocage puis reprise. 18 nouveaux cas et128connexes réussis, sans réparation historique ni promotion de statut.  Complément534 : suppression de brouillon libère uniquement son règlement natif, référence commune/renommée ou collision sans effet sur un autre document ; correction associée à une annulation conservée409, fallback historique unique et montants concordants.26nouveaux/323connexes réussis ; autres rattachements documentaires distincts.  Complément536 : suppression facture fournisseur et recomptabilisation cohérentes, vraie création auditée prioritaire sur référence renommée/en collision ; date/auxiliaires contradictoires refusés, RAS distincte conservée.17nouveaux/171connexes réussis ; baseline ne reconstitue pas une création et historique manquant reste à vérifier. |
| FAC-08 | Chèques, effets, remise et impayés | partiel | Effets.jsx, commercial.py ; [404](../../Test/rapport_effets_frais_precision_404.md), [406](../../Test/rapport_encaissement_frais_406.md) ; [456](../../Test/rapport_instruments_runtime_456.md) ; [471](../../Test/rapport_effets_date_locale_471.md)  ; [545](../../Test/rapport_credits_consultation_seule_545.md) | Dates effectives et cycle chèque/effet individuel avec frais10,01, net109,99, validation/pointage/lettrage/FEC testés sur PGnonce/Edge. Frais invalides refusés et affichés ;instruments groupés, escompte et variantes annuelles restent à étendre. Impayé de 1200 remplacé : cinq pièces/onze lignes D=C6000, quatre lignes client lettrées. Frais10,01/net109,99, annuels et refus demi-centime confirmés sous LOGIN limité ; pas un calcul d’escompte réglementaire. Effet dû aujourd’hui disponible dès la date locale, lendemain bloqué ; horloge Edge Europe/Paris et huit parcours instruments connexes réussis.  Complément545 : consultation seule Avoirs/Acomptes sans commande de mutation, historique actif/crédit libre/chèque en attente/PDF conservés ;6Edge vente/achat lecteur390/1440 et comptable1440,28connexes et build réussis.403 directs et absence de mutation vérifiés. Aucun calcul ou droit serveur changé ; autres écrans distincts. |
| FAC-09 | Échéanciers et relances | partiel | echeanciers.py, recouvrement.py, SituationFinanciere.jsx ; ZIP164 | 8 tests connectés réussis : filtres, lecture, création/modification/annulation, NaN et historique après paiement ; aucun envoi externe automatique |
| FAC-10 | PDF, justificatifs et archivage documentaire | partiel | document_pdf_service.py, attachments.py ; tests fact9/factH ; ZIP240/246 ; [451](../../Test/rapport_justificatifs_modeles_451.md), [452](../../Test/rapport_restauration_justificatifs_452.md), [453](../../Test/rapport_pieces_telechargement_453.md) ; [462](../../Test/rapport_logos_exports_462.md), [463](../../Test/rapport_logos_xlsx_463.md), [466](../../Test/rapport_logos_impression_466.md), [467](../../Test/rapport_pdf_textes_467.md) | Pièces BL client déposées/téléchargées dans deux Edge, puis vraie restauration conjointe API/DB/fichiers : homonymes, SHA, lecteur et autre société vérifiés. Autres types de documents restaurés, archivage légal et volume de production restent à étendre. Fichiers d’écritures conservés au refus SQL, suppression sérialisée avec validation et refus visible ; 404/401 ne téléchargent plus du JSON en faux PDF. Quatre PDF et traces restaurés avec ACL natives ; archivage légal, volume et panne disque après commit non qualifiés. Logo dans les pièces générées PDF/XLSX et impressions ; pièces jointes importées conservées. Identités/libellés PDF littéraux, aucune image chargée depuis les textes testés. CSV/FEC restent textuels. |
| CPT-01 | Journal et écritures manuelles | partiel | ecritures.py ; migration072 ; ZIP148/161/217 ; [CSV435](../../Test/rapport_csv_partage_435.md) ; [454](../../Test/rapport_modeles_journal_454.md), [455](../../Test/rapport_modeles_detection_455.md), [457](../../Test/rapport_journal_lecture_457.md), [458](../../Test/rapport_ecritures_capacite_458.md) ; [464](../../Test/rapport_modeles_avances_464.md), [465](../../Test/rapport_modeles_taux_465.md), [470](../../Test/rapport_lecture_journal_historique_470.md)  ; [490](../../Test/rapport_journal_cloture_490.md)  ; [520](../../Test/rapport_stock_validation_journal_520.md)  ; [522](../../Test/rapport_journal_mutations_validation_522.md)  ; [528](../../Test/rapport_contrepassation_concurrence_528.md)  ; [530](../../Test/rapport_reglements_sources_concurrence_530.md)  ; [532](../../Test/rapport_reglements_annulation_sources_532.md)  ; [534](../../Test/rapport_journal_liberation_sources_534.md)  ; [536](../../Test/rapport_journal_sources_factures_ras_536.md)  ; [538](../../Test/rapport_factures_comptabilisation_concurrence_538.md) | Triggers PG et montants non finis testés ;99ciblés/connexes. Intitulés du plan même désactivés, CSV et passage A→B→A vérifiés217 :13pytest et5Node exécutés par principal. Snapshots auxiliaires et lignes définitives inchangés ; annuel manuel à compléter. CSV partagé : montants invalides « À vérifier », textes de formule protégés et CR quotés ; téléchargements Journal bureau/mobile et sources conservées. Modèles choisis et détectés :100HT/20TVA/120TTC puis trésorerie120, tiers natifs/validation/lettrage/FEC240. Détection vente D100/C140 corrigée par calcul partagé. Lecture seule cohérente et dépassement Numeric18,2 refusé422 au lieu de500 ; précision flottante extrême/modèles complexes restent à étendre. Cinq aides aux avances personnel, sélection explicite des modèles ambigus et HT conservé au changement de taux. Historiques NaN/zéro illisibles signalés409 ; Journal sans faux totaux/exports, aucune réparation automatique.  Complément490 : en-têtes/lignes Journal sérialisés avec clôture488 via098 additive, deux périmètres des déplacements protégés et clôture sans exercice bloquante. 155exécutions finales dont Edge vente/achat/clôture et restauration098 ; installation réelle et concurrence globale des autres modules restent à qualifier.  Complément520 : lecture verrouillée avant validation individuelle/lot et régénération stock ; quatre erreurs500 reproduites puis remplacées par refus métier. Numéro/audit uniques, lignes intactes, lots recoupants chronologiques, clôture/FEC.331tests finaux réussis ; autres mutations/générateurs Journal distincts.  Complément522 : modification/suppression verrouillées avant contrôle du parent ; quatre erreurs500 remplacées par refus423, sources/numéro/audit conservés ; ordre inverse validant les nouvelles lignes ou refusant une pièce supprimée.385tests finaux réussis, dont régressions NaN/non finis ; autres générateurs et accès hors API distincts.  Complément528 : contrepassation simultanée idempotente200, même correction/date/motif, numéro et validation uniques ; original/audit intacts, auxiliaires copiés, original clôturé corrigé sur exercice suivant et FEC effectif.416tests finaux réussis ; autres générateurs et accès hors API distincts.  Complément530 : comptabilisation de règlement sérialisée avec modification/suppression/annulation ; lecture RAS compatible LOGIN limité sans élargir UPDATE. 16 nouveaux cas et 110 connexes exécutés, vente/achat → validation → lettrage → pointage, annulations Edge et permissions. Autres sources historiques/accès hors API distincts.  Complément532 : origine de règlement contrôlée (société/source/date/totaux/liaison unique), pas de fallback sur lien explicite incohérent ; correction existante refusée409, conflit Journal refusé sans interblocage puis reprise. 18 nouveaux cas et128connexes réussis, sans réparation historique ni promotion de statut.  Complément534 : suppression de brouillon libère uniquement son règlement natif, référence commune/renommée ou collision sans effet sur un autre document ; correction associée à une annulation conservée409, fallback historique unique et montants concordants.26nouveaux/323connexes réussis ; autres rattachements documentaires distincts.  Complément536 : suppression facture fournisseur et recomptabilisation cohérentes, vraie création auditée prioritaire sur référence renommée/en collision ; date/auxiliaires contradictoires refusés, RAS distincte conservée.17nouveaux/171connexes réussis ; baseline ne reconstitue pas une création et historique manquant reste à vérifier.  Complément538 : deux demandes simultanées de comptabilisation facture vente/achat donnent200/409 et une seule pièce équilibrée, validée puis exportée au FEC. Avoir déjà verrouillé confirmé sans modification de son code ; origine définitive et audit conservés.4nouveaux cas et344+247exécutions finales en deux commandes, aucune réparation historique. |
| CPT-02 | Grand livre et balances | partiel | Balances.jsx, GrandLivre.jsx ; ZIP211/213/216/217/224/266/270 ; [exports connexes435](../../Test/rapport_csv_partage_435.md) ; [458](../../Test/rapport_ecritures_capacite_458.md) ; [462](../../Test/rapport_logos_exports_462.md), [463](../../Test/rapport_logos_xlsx_463.md) ; [474](../../Test/rapport_lectures_comptables_474.md) | Cinq balances et exports relus ; course comparative264 reproduite puis corrigée266 : filtre mars préservé après contexte tardif, sociétés/années distinctes. Grand livre270 : initial1000/crédit200/final800, CSV vrais avant/après,3nouveaux+26connexes. Recette annuelle complète reste à effectuer. 68 tests connexes incluent les CSV du Grand Livre et les exports Excel/PDF des balances ; suites non additionnées aux anciennes preuves. Borne valide représentable stockée/validée puis balance et grand livre relus200. Exports réels des balances inclus dans les79connexes ; aucune nouvelle restriction de schéma sur la lecture historique. Logos des balances PDF et XLSX vérifiés ; données et coordonnées des cellules préservées, course avant identité société corrigée. Grand livre : rapport et export masqués sur erreur, filtre corrigé rétablit le rapport ; quatre nouveaux parcours accueil/Grand livre dans474. |
| CPT-03 | Collectifs, auxiliaires et lettrage | partiel | lettrage.py ; 049/053/089 ; [444](../../Test/rapport_e2e_runtime_annuel_444.md) ; [454](../../Test/rapport_modeles_journal_454.md), [459](../../Test/rapport_consolidation_reprise_459.md)  ; [528](../../Test/rapport_contrepassation_concurrence_528.md)  ; [530](../../Test/rapport_reglements_sources_concurrence_530.md)  ; [532](../../Test/rapport_reglements_annulation_sources_532.md)  ; [534](../../Test/rapport_journal_liberation_sources_534.md)  ; [536](../../Test/rapport_journal_sources_factures_ras_536.md) | Clé SQL alignée sur tiers natif puis auxiliaire figé, repli historique conservé. AN et paiement à libellés distincts lettrés ; tiers différents de même libellé refusés. Sept refus SQL atomiques, délettrage tracé, originaux préservés. Historiques réels ambigus non réparés. Modèles manuels achat/vente et trésorerie lettrés dans Edge après validation ; originaux bruts et tiers natifs préservés, code d’au moins trois lettres et FEC relu. Consolidation :20 liens, aucun déséquilibre.  Complément528 : contrepassation simultanée idempotente200, même correction/date/motif, numéro et validation uniques ; original/audit intacts, auxiliaires copiés, original clôturé corrigé sur exercice suivant et FEC effectif.416tests finaux réussis ; autres générateurs et accès hors API distincts.  Complément530 : comptabilisation de règlement sérialisée avec modification/suppression/annulation ; lecture RAS compatible LOGIN limité sans élargir UPDATE. 16 nouveaux cas et 110 connexes exécutés, vente/achat → validation → lettrage → pointage, annulations Edge et permissions. Autres sources historiques/accès hors API distincts.  Complément532 : origine de règlement contrôlée (société/source/date/totaux/liaison unique), pas de fallback sur lien explicite incohérent ; correction existante refusée409, conflit Journal refusé sans interblocage puis reprise. 18 nouveaux cas et128connexes réussis, sans réparation historique ni promotion de statut.  Complément534 : suppression de brouillon libère uniquement son règlement natif, référence commune/renommée ou collision sans effet sur un autre document ; correction associée à une annulation conservée409, fallback historique unique et montants concordants.26nouveaux/323connexes réussis ; autres rattachements documentaires distincts.  Complément536 : suppression facture fournisseur et recomptabilisation cohérentes, vraie création auditée prioritaire sur référence renommée/en collision ; date/auxiliaires contradictoires refusés, RAS distincte conservée.17nouveaux/171connexes réussis ; baseline ne reconstitue pas une création et historique manquant reste à vérifier. |
| CPT-04 | Banques, relevés et rapprochement | partiel | rapprochement.py, RapprochementBancaire.jsx ; 084/087 ; [441](../../Test/rapport_permissions_banque_releves_441.md)  ; [530](../../Test/rapport_reglements_sources_concurrence_530.md)  ; [532](../../Test/rapport_reglements_annulation_sources_532.md)  ; [534](../../Test/rapport_journal_liberation_sources_534.md) | Quatre cycles vente/achat simple/lot sous LOGIN : import, doublon, soldes, propositions, pointage/dépointage, clôture et isolation vérifiés. 087 ajoute les seuls droits bancaires nécessaires. Aucune écriture modifiée. Instruments groupés et rapprochement approximatif restent partiels.  Complément530 : comptabilisation de règlement sérialisée avec modification/suppression/annulation ; lecture RAS compatible LOGIN limité sans élargir UPDATE. 16 nouveaux cas et 110 connexes exécutés, vente/achat → validation → lettrage → pointage, annulations Edge et permissions. Autres sources historiques/accès hors API distincts.  Complément532 : origine de règlement contrôlée (société/source/date/totaux/liaison unique), pas de fallback sur lien explicite incohérent ; correction existante refusée409, conflit Journal refusé sans interblocage puis reprise. 18 nouveaux cas et128connexes réussis, sans réparation historique ni promotion de statut.  Complément534 : suppression de brouillon libère uniquement son règlement natif, référence commune/renommée ou collision sans effet sur un autre document ; correction associée à une annulation conservée409, fallback historique unique et montants concordants.26nouveaux/323connexes réussis ; autres rattachements documentaires distincts. |
| CPT-05 | Import CSV de relevés | terminé | src/utils/releveImport.js, RapprochementBancaire.jsx ; ZIP157 | CSV UTF8/Windows1252 et Excel stricts ; 82 tests historiques dont Edge/PG ; doublons parfaitement identiques indiscernables documentés |
| CPT-06 | Stock, CMUP et annulations | partiel | stock_movement_service.py ; migrations010–012 ; ZIP135/147/148/224  ; [508](../../Test/rapport_inventaire_cloture_508.md)  ; [510](../../Test/rapport_stock_comptabilisations_510.md)  ; [518](../../Test/rapport_mouvements_stock_cloture_518.md)  ; [520](../../Test/rapport_stock_validation_journal_520.md)  ; [524](../../Test/rapport_stock_mouvements_ordinaires_524.md)  ; [526](../../Test/rapport_stock_sources_exercices_526.md)  ; [543](../../Test/rapport_factures_finalisation_concurrente_543.md) | Concurrence CMUP/idempotence vérifiée sur PG isolé ; annuel réduit224 :10unités achetées,4vendues,6restantes CMUP100,2mouvements etvaleur600 contrôlés. Recette complète multi-articles etvariantes restent à effectuer.  Complément508 : validation API de comptage et calcul de clôture sérialisés par société/exercice, deuxordres refus409 puis reprise, autres périmètres disponibles, refus métier libère verrou.158exécutions finales avec Edge inventaire1365/390px/historiques/restauration. Autres mouvements et double comptabilisation de stock restent distincts.  Complément510 : comptages et générations de stock exclusifs par société/exercice ; doublon réel deux brouillons160 reproduit puis empêché, trois courses refus409 et une seule régularisation validée160/200 avec clôture/FEC. Régénération volontaire brouillon préservée, définitive intacte.164exécutions finales réussies ; autres mouvements et mutations Journal restent distincts.  Complément518 : moteur central des mouvements protégé pendant clôture/comptage/comptabilisation ; exercice décalé trouvé par dates, refus409 et reprise, sources conservées.312tests finaux réussis dont cycles commerciaux/logos après correction. Validité d’une photographie après mouvements successifs et SQL/Python directs restent distincts.  Complément520 : lecture verrouillée avant validation individuelle/lot et régénération stock ; quatre erreurs500 reproduites puis remplacées par refus métier. Numéro/audit uniques, lignes intactes, lots recoupants chronologiques, clôture/FEC.331tests finaux réussis ; autres mutations/générateurs Journal distincts.  Complément524 : régression du verrou trop large518 corrigée ; mouvements ordinaires coordonnés en partagé, sérialisation par article conservée ; comptage/génération/clôture toujours exclusifs409. Deux mouvements en attente native puis240 validé/clôture/FEC.15tests PostgreSQL historiques inchangés,401tests finaux réussis ; accès hors moteur et inventaires devenus anciens distincts.  Complément526 : régénération identifiée par lien réel cohérent société/exercice/origine stock ; secours par référence limité au même exercice et unique. Autres pièces/manuelles préservées, doublons et liens incohérents refus409 sans réparation silencieuse.9nouveaux cas et410tests finaux réussis ; origine historique incertaine reste à examiner.  Complément543 : double validation/conversion vente et achat sans erreur500 ; parent relu sous verrou, validation200/200 même numéro et conversion200/400, un seul mouvement de stock2→1/3, répétition sans mutation puis comptabilisation/validation/FEC.4nouveaux et356+247exécutions finales sur sources figées ; aucune garde SQL retirée. |
| CPT-07 | Inventaire physique et photographie de clôture | partiel | stock_service.py, inventaire_nombres_service.py, livre_inventaire_service.py ; ZIP224/313/334 ; [rapport313](../../Test/rapport_inventaire_nombres_historiques.md), [audit334](../../Test/rapport_ledger_stock_nombres_historiques.md)  ; [508](../../Test/rapport_inventaire_cloture_508.md)  ; [510](../../Test/rapport_stock_comptabilisations_510.md)  ; [516](../../Test/rapport_commerce_logos_runtime_516.md)  ; [518](../../Test/rapport_mouvements_stock_cloture_518.md)  ; [520](../../Test/rapport_stock_validation_journal_520.md)  ; [524](../../Test/rapport_stock_mouvements_ordinaires_524.md)  ; [526](../../Test/rapport_stock_sources_exercices_526.md) | Comptage complet explicite ; sources historiques inconnues diagnostiquées sans réparation, refus avant mutation et conservation des brouillons. Principal148tests60,73s ; agent4Edge46,66s bureau/mobile :200→160/perte40, écriture3111/6114 validée, CSV/PDF, droits et archivage refusé. AuditCMUP334 :95tests, dont deux Edge bureau/mobile, totaux inconnus NULL et contrôles indépendants préservés. Variantes annuelles multi-articles restent à étendre.  Complément508 : validation API de comptage et calcul de clôture sérialisés par société/exercice, deuxordres refus409 puis reprise, autres périmètres disponibles, refus métier libère verrou.158exécutions finales avec Edge inventaire1365/390px/historiques/restauration. Autres mouvements et double comptabilisation de stock restent distincts.  Complément510 : comptages et générations de stock exclusifs par société/exercice ; doublon réel deux brouillons160 reproduit puis empêché, trois courses refus409 et une seule régularisation validée160/200 avec clôture/FEC. Régénération volontaire brouillon préservée, définitive intacte.164exécutions finales réussies ; autres mouvements et mutations Journal restent distincts.  Complément516 :10E2E supplémentaires sous rôleLOGIN non propriétaire098, cycles vente/achat et logos PDF/Excel/impression desktop/mobile ; sources intactes et buildVite réussi. Exports cités seulement, sans prétendre couvrir chaque pièce ni valider la recette utilisateur.  Complément518 : moteur central des mouvements protégé pendant clôture/comptage/comptabilisation ; exercice décalé trouvé par dates, refus409 et reprise, sources conservées.312tests finaux réussis dont cycles commerciaux/logos après correction. Validité d’une photographie après mouvements successifs et SQL/Python directs restent distincts.  Complément520 : lecture verrouillée avant validation individuelle/lot et régénération stock ; quatre erreurs500 reproduites puis remplacées par refus métier. Numéro/audit uniques, lignes intactes, lots recoupants chronologiques, clôture/FEC.331tests finaux réussis ; autres mutations/générateurs Journal distincts.  Complément524 : régression du verrou trop large518 corrigée ; mouvements ordinaires coordonnés en partagé, sérialisation par article conservée ; comptage/génération/clôture toujours exclusifs409. Deux mouvements en attente native puis240 validé/clôture/FEC.15tests PostgreSQL historiques inchangés,401tests finaux réussis ; accès hors moteur et inventaires devenus anciens distincts.  Complément526 : régénération identifiée par lien réel cohérent société/exercice/origine stock ; secours par référence limité au même exercice et unique. Autres pièces/manuelles préservées, doublons et liens incohérents refus409 sans réparation silencieuse.9nouveaux cas et410tests finaux réussis ; origine historique incertaine reste à examiner. |
| CPT-08 | Immobilisations, amortissements et cessions | partiel | immobilisations_service.py, Immobilisations.jsx ; [382](../../Test/rapport_immobilisations_degressif_382.md) ; [444](../../Test/rapport_e2e_runtime_annuel_444.md)  ; [493](../../Test/rapport_dotations_concurrentes_493.md)  ; [495](../../Test/rapport_immobilisations_mutations_495.md)  ; [497](../../Test/rapport_registre_cloture_497.md)  ; [499](../../Test/rapport_reconciliations_concurrentes_499.md)  ; [501](../../Test/rapport_cloture_correction_501.md)  ; [503](../../Test/rapport_reprise_ouverture_503.md)  ; [504](../../Test/rapport_historiques_partiels_504.md)  ; [506](../../Test/rapport_deux_clotures_506.md) | Dégressif 60000 sur 5 ans :24000/14400/8640/6480/6480, six pièces définitives D=C 132000 et VNC 0, sous LOGIN limité avec réseau normal/latence. Acquisition originale préservée et anti-doublon. Éligibilité fiscale réelle, dates/biens et autres variantes restent à qualifier.  Complément493 : génération commune de dotations protégée contre doublons concurrents, refus409/rejeu et isolation société/immobilisation/exercice ; 32tests finaux avec Edge et restauration098. Modifications de plan, sorties simultanées et concurrence globale du registre restent à qualifier.  Complément495 : modifications de plan/sorties/paiements/encaissements sérialisés avec les dotations courantes, cache relu et lot atomique ;46tests finaux dont oracles493/Edge/restauration. Réconciliations historiques, SQL arbitraire et stabilité globale pendant clôture restent distincts.  Complément497 : registre société stable pendant clôture API face aux mutations HTTP, créations/réconciliations et appel direct du lot compris ;62exécutions finales avec Edge/restauration/compatibilité ancien schéma. SQL arbitraire, concurrence propre aux réconciliations et autres modules restent à qualifier.  Complément499 : assistants historiques sérialisés avec mutations courantes, lots atomiques et sélections uniques ; correction RECON-AMORT gèle plan et empêche dotation automatique en double sur N,N+1 préservé. 83exécutions finales réussies ; recette de clôture avec correction seule complétée au lot501 pour un montant exact.  Complément501 : correction RECON-AMORT seule reconnue uniquement si charge nette de N exactement égale au plan,société/exercice/référence stricts ;88exécutions finales réussies. Écarts1000/3000 et autres périmètres refusés,sources intactes,zéro AM supplémentaire. Historiques annuels exhaustifs restent à qualifier.  Complément503 : reprise calculée à l’ouverture réelle sans dépendre de N−1, rapprochement à date réelle et refus409 d’un N+1 non contigu sans déplacement automatique. Cinq parcours jusqu’à clôture/FEC/AN ;28tests module réussis. Historiques partiels et autres variantes restent à qualifier.  Complément504 : dotations partielles/excessives de N corrigées sans réécrire les sources, écarts anciens conservés et clôture refusée ; trois PDF du livre lus.101exécutions finales réussies avec503/oracles précédents/Edge/restauration. Variantes pluriannuelles et cessions décalées restent à qualifier.  Complément506 : deux clôtures décalées successives dans Edge, refus de discontinuité et correction explicite des dates ; cession après reprise sans recréer anciennes annuités, cumul contrôlé avant sortie et corrections annuelles AM/RECON reconnues sans doublon.9cas nouveaux et110exécutions finales réussies. Autres conventions historiques, reclassements et concurrence Journal restent distincts. |
| CPT-09 | Provisions, CCA, FNP et FAE | partiel | Assistant de clôture : sept modèles CCA/PCA/FNP/FAE/provision/dépréciations ; [553](../../Test/rapport_ajustements_inventaire_553.md), [555](../../Test/rapport_apercu_inventaire_555.md) | Montants, comptes et contrepassations contrôlés ; calendrier décalé incohérent refusé sans mutation. Montants déterminés par le comptable ; calcul CCA/PCA595 et suivi601 livrés. Reprises partielles615 liées à une dotation validée : registre100, réservations datées, annulation et protections Journal, API/Edge/ACL/restauration testés ; exports PDF/Excel617 avec identité/logo et snapshot cohérent. Les mouvements manuels historiques et natures non qualifiées nécessitent une analyse distincte ; recette humaine et migration100 réelle non exécutées. |
| CPT-10 | Clôture et contrôles d’inventaire | partiel | cloture.py, cloture_service.py ; [448](../../Test/rapport_consolidation_runtime_448.md) ; [456](../../Test/rapport_instruments_runtime_456.md)  ; [488](../../Test/rapport_tva_calcul_cloture_488.md)  ; [490](../../Test/rapport_journal_cloture_490.md)  ; [493](../../Test/rapport_dotations_concurrentes_493.md)  ; [495](../../Test/rapport_immobilisations_mutations_495.md)  ; [497](../../Test/rapport_registre_cloture_497.md)  ; [499](../../Test/rapport_reconciliations_concurrentes_499.md)  ; [501](../../Test/rapport_cloture_correction_501.md)  ; [503](../../Test/rapport_reprise_ouverture_503.md)  ; [504](../../Test/rapport_historiques_partiels_504.md)  ; [506](../../Test/rapport_deux_clotures_506.md)  ; [508](../../Test/rapport_inventaire_cloture_508.md)  ; [510](../../Test/rapport_stock_comptabilisations_510.md)  ; [512](../../Test/rapport_fiscalite_concurrence_512.md)  ; [514](../../Test/rapport_deficits_multiexercices_514.md)  ; [518](../../Test/rapport_mouvements_stock_cloture_518.md)  ; [520](../../Test/rapport_stock_validation_journal_520.md)  ; [522](../../Test/rapport_journal_mutations_validation_522.md)  ; [524](../../Test/rapport_stock_mouvements_ordinaires_524.md)  ; [526](../../Test/rapport_stock_sources_exercices_526.md)  ; [528](../../Test/rapport_contrepassation_concurrence_528.md) | Même application complète 090+091 : année avec stock/TVA/inventaire/amortissement, clôture/AN et exports. 091 corrige la lecture post-clôture des décisions. Année bancaire 2025→2026 également contrôlée ; cahier 218 cas et autres variantes ne sont pas prévalidés. Deux annuels chèque/effet sous schéma091/LOGIN : frais et rapprochement conservés à la clôture, à-nouveaux et FEC des deux années ; impôt de laboratoire3000 non qualifié comme régime réel.  Complément488 : paramètres TVA protégés dès le début du calcul de clôture API, seconde clôture refusée409 et verrou libéré après échec.122exécutions finales avec restauration et compatibilité ancien banc ; autres écrivains comptables non couverts globalement.  Complément490 : en-têtes/lignes Journal sérialisés avec clôture488 via098 additive, deux périmètres des déplacements protégés et clôture sans exercice bloquante. 155exécutions finales dont Edge vente/achat/clôture et restauration098 ; installation réelle et concurrence globale des autres modules restent à qualifier.  Complément493 : génération commune de dotations protégée contre doublons concurrents, refus409/rejeu et isolation société/immobilisation/exercice ; 32tests finaux avec Edge et restauration098. Modifications de plan, sorties simultanées et concurrence globale du registre restent à qualifier.  Complément495 : modifications de plan/sorties/paiements/encaissements sérialisés avec les dotations courantes, cache relu et lot atomique ;46tests finaux dont oracles493/Edge/restauration. Réconciliations historiques, SQL arbitraire et stabilité globale pendant clôture restent distincts.  Complément497 : registre société stable pendant clôture API face aux mutations HTTP, créations/réconciliations et appel direct du lot compris ;62exécutions finales avec Edge/restauration/compatibilité ancien schéma. SQL arbitraire, concurrence propre aux réconciliations et autres modules restent à qualifier.  Complément499 : assistants historiques sérialisés avec mutations courantes, lots atomiques et sélections uniques ; correction RECON-AMORT gèle plan et empêche dotation automatique en double sur N,N+1 préservé. 83exécutions finales réussies ; recette de clôture avec correction seule complétée au lot501 pour un montant exact.  Complément501 : correction RECON-AMORT seule reconnue uniquement si charge nette de N exactement égale au plan,société/exercice/référence stricts ;88exécutions finales réussies. Écarts1000/3000 et autres périmètres refusés,sources intactes,zéro AM supplémentaire. Historiques annuels exhaustifs restent à qualifier.  Complément503 : reprise calculée à l’ouverture réelle sans dépendre de N−1, rapprochement à date réelle et refus409 d’un N+1 non contigu sans déplacement automatique. Cinq parcours jusqu’à clôture/FEC/AN ;28tests module réussis. Historiques partiels et autres variantes restent à qualifier.  Complément504 : dotations partielles/excessives de N corrigées sans réécrire les sources, écarts anciens conservés et clôture refusée ; trois PDF du livre lus.101exécutions finales réussies avec503/oracles précédents/Edge/restauration. Variantes pluriannuelles et cessions décalées restent à qualifier.  Complément506 : deux clôtures décalées successives dans Edge, refus de discontinuité et correction explicite des dates ; cession après reprise sans recréer anciennes annuités, cumul contrôlé avant sortie et corrections annuelles AM/RECON reconnues sans doublon.9cas nouveaux et110exécutions finales réussies. Autres conventions historiques, reclassements et concurrence Journal restent distincts.  Complément508 : validation API de comptage et calcul de clôture sérialisés par société/exercice, deuxordres refus409 puis reprise, autres périmètres disponibles, refus métier libère verrou.158exécutions finales avec Edge inventaire1365/390px/historiques/restauration. Autres mouvements et double comptabilisation de stock restent distincts.  Complément510 : comptages et générations de stock exclusifs par société/exercice ; doublon réel deux brouillons160 reproduit puis empêché, trois courses refus409 et une seule régularisation validée160/200 avec clôture/FEC. Régénération volontaire brouillon préservée, définitive intacte.164exécutions finales réussies ; autres mouvements et mutations Journal restent distincts.  Complément512 : paramètres/retraitements protégés pendant clôture, mutations et confirmation exclusives par société/exercice, double confirmation409 ; instantané cohérent et compléments acomptes postclôture conservés.245tests finaux réussis dont Edge fiscal. Stock global déficits historiques et règlements CSS hors de cette garantie.  Complément514 : stock global des déficits stable pendant clôture/confirmation ; six mutations exclusives entre exercices, solde1000 consommé une fois et seconde proposition0 après reprise. Contrôles du déficit utilisé conservés.256tests finaux réussis. Protection de concurrence, sans nouvelle interdiction permanente de saisie historique ; CSS/lectures/directSQL distincts.  Complément518 : moteur central des mouvements protégé pendant clôture/comptage/comptabilisation ; exercice décalé trouvé par dates, refus409 et reprise, sources conservées.312tests finaux réussis dont cycles commerciaux/logos après correction. Validité d’une photographie après mouvements successifs et SQL/Python directs restent distincts.  Complément520 : lecture verrouillée avant validation individuelle/lot et régénération stock ; quatre erreurs500 reproduites puis remplacées par refus métier. Numéro/audit uniques, lignes intactes, lots recoupants chronologiques, clôture/FEC.331tests finaux réussis ; autres mutations/générateurs Journal distincts.  Complément522 : modification/suppression verrouillées avant contrôle du parent ; quatre erreurs500 remplacées par refus423, sources/numéro/audit conservés ; ordre inverse validant les nouvelles lignes ou refusant une pièce supprimée.385tests finaux réussis, dont régressions NaN/non finis ; autres générateurs et accès hors API distincts.  Complément524 : régression du verrou trop large518 corrigée ; mouvements ordinaires coordonnés en partagé, sérialisation par article conservée ; comptage/génération/clôture toujours exclusifs409. Deux mouvements en attente native puis240 validé/clôture/FEC.15tests PostgreSQL historiques inchangés,401tests finaux réussis ; accès hors moteur et inventaires devenus anciens distincts.  Complément526 : régénération identifiée par lien réel cohérent société/exercice/origine stock ; secours par référence limité au même exercice et unique. Autres pièces/manuelles préservées, doublons et liens incohérents refus409 sans réparation silencieuse.9nouveaux cas et410tests finaux réussis ; origine historique incertaine reste à examiner.  Complément528 : contrepassation simultanée idempotente200, même correction/date/motif, numéro et validation uniques ; original/audit intacts, auxiliaires copiés, original clôturé corrigé sur exercice suivant et FEC effectif.416tests finaux réussis ; autres générateurs et accès hors API distincts. |
| CPT-11 | Réouverture d'une période non définitivement clôturée | terminé | exercices.py ; migration059 ; [557](../../Test/rapport_reouverture_periodes_557.md) | Admin seul, audit append-only, refus après clôture annuelle en API et SQL, séparation des sociétés ;6scénarios natifs/Edge puis37cas regroupés réussis. Recette sur installation cible à effectuer. |
| CPT-12 | Réouverture d'un exercice définitivement clôturé | bloqué | cloture.py retourne 409 | Décision métier nécessaire ; ne pas débloquer silencieusement |
| CPT-13 | À-nouveaux, affectation et exercice suivant | partiel | cloture.py, affectation_resultat_service.py ; [448](../../Test/rapport_consolidation_runtime_448.md) ; [452](../../Test/rapport_restauration_justificatifs_452.md)  ; [528](../../Test/rapport_contrepassation_concurrence_528.md) | AN 4180 du scénario bancaire et AN 25000 du scénario stock distincts, originaux conservés. Affectation fictive de perte 3000 : OD 1169/1199 définitive, PV/justificatif tracés et doublon 409 ; droits 091 en insertion/lecture seuls. Décision sociale réelle et autres affectations à vérifier humainement. La décision091 et son PV fictif sont désormais restaurés avec fichiers/ACL et relus sur main:app non propriétaire. Décision sociale réelle, autres affectations/propriétaires et déploiement restent à valider.  Complément528 : contrepassation simultanée idempotente200, même correction/date/motif, numéro et validation uniques ; original/audit intacts, auxiliaires copiés, original clôturé corrigé sur exercice suivant et FEC effectif.416tests finaux réussis ; autres générateurs et accès hors API distincts. |
| FIS-01 | TVA collectée/récupérable, débit/encaissement | partiel | tva.py, tva_service.py, DeclarationTVA.jsx ; ZIP173 ; [472](../../Test/rapport_tva_parametres_runtime_472.md) ; [477](../../Test/rapport_tva_verrou_exercice_477.md) ; [480](../../Test/rapport_protection_sql_tva_480.md)  ; [485](../../Test/rapport_tva_cloture_sql_concurrente_485.md)  ; [487](../../Test/rapport_tva_trace_concurrente_487.md)  ; [488](../../Test/rapport_tva_calcul_cloture_488.md)  ; [491](../../Test/rapport_tva_annees_491.md) | 2UI connectées vente/achat-paiements, mois/trimestre/année et impressionnative/PDF réel ; crédit20/prorata80 persistés ; rôlelecture protégé ;14 tests paramètres dont6API invalides ; dépôt/gel non implémentés Enregistrement des paramètres TVA sous LOGIN limité qualifié après093 ; lecteur403, exercice clôturé409, données préservées et refus tracés. Verrou de ligne477 qualifié dans les deux ordres pour un exercice existant ; SQL direct, absence de ligne et calcul complet de clôture concurrent restent à qualifier.  Sous094 :22cas réussis, dont refus SQL directs après clôture et trace seule sans ligne exercice ;témoins ouverts autorisés. SQLdirect concurrent et calcul préalable complet de clôture restent non qualifiés.  Complément485 :096 et API partagée/UPSERT qualifiés sur77cas, dont statut SQL concurrent pour une ligne exercice existante, deux premières saisies200/200 et restauration froide. Les limites précédentes restent valables pour absence de ligne, trace seule concurrente et calcul complet de clôture.  Complément487 :097 protège aussi absence de ligne et trace seule concurrente, avec rollback/409 ciblé et reprise.118cas incluant restauration ; aucun exercice créé automatiquement. Calcul préalable complet et autres écrivains non qualifiés globalement.  Complément488 : paramètres TVA protégés dès le début du calcul de clôture API, seconde clôture refusée409 et verrou libéré après échec.122exécutions finales avec restauration et compatibilité ancien banc ; autres écrivains comptables non couverts globalement.  Complément491 : années non représentables refusées422, bornes techniques1/9999 conservées sans sous-débordement ; tables métier inchangées et refusPUT tracé. 188exécutions finales avec oracles098/restauration ; aucune validation de régime fiscal par ces bornes. |
| FIS-02 | Retenues à la source TVA | partiel | Simulation117-V-b2026, capture guidée099, OD et registre ; [571](../../Test/rapport_ras_tva_capture_571.md), [573](../../Test/rapport_interface_ras_tva_573.md), [579](../../Test/rapport_registre_ras_tva_579.md), [585](../../Test/rapport_empreinte_ras_tva_585.md), [587](../../Test/rapport_coherence_ras_tva_587.md), [sources](SOURCES_RAS_TVA_20261018.md)  ; [documents647](../../Test/rapport_ras_documents647.md) | Faits explicites sur pièces, ventilation justifiée, capture immuable/idempotente liée au paiement, annulation par contrepassation, consultation et CSV/Excel/PDF avec logo/empreinte.137tests consolidés,2parcours de cohérence supplémentaires et restauration75tables qualifiés. Déclaration automatique indisponible pour les périodes/reports touchés ; imputation fiscale, reversement, autres cas et formats officiels restent à traiter. Registre interne distinct d'un dépôt officiel ; aucun compte imposé par hypothèse.  Complément647 : références/fichiers des OD distincts, ajout/lecture/exports et restauration102 qualifiés ; aucune preuve de versement ou imputation automatique.  Complément681 : rapprochement documentaire MAD à pièce validée, parts/retraits immuables et PDF ; [347tests communs103](../../Test/rapport_ras_rapprochements681.md). Sans déclaration, crédit imputé ni preuve de versement DGI. |
| FIS-03 | Résultat fiscal et retraitements | partiel | fiscalite.py, fiscalite_retraitements_service.py ; migrations021/064  ; [512](../../Test/rapport_fiscalite_concurrence_512.md)  ; [514](../../Test/rapport_deficits_multiexercices_514.md) | Contrôles présents ; vérification annuelle et preuve documentaire  Complément512 : paramètres/retraitements protégés pendant clôture, mutations et confirmation exclusives par société/exercice, double confirmation409 ; instantané cohérent et compléments acomptes postclôture conservés.245tests finaux réussis dont Edge fiscal. Stock global déficits historiques et règlements CSS hors de cette garantie.  Complément514 : stock global des déficits stable pendant clôture/confirmation ; six mutations exclusives entre exercices, solde1000 consommé une fois et seconde proposition0 après reprise. Contrôles du déficit utilisé conservés.256tests finaux réussis. Protection de concurrence, sans nouvelle interdiction permanente de saisie historique ; CSS/lectures/directSQL distincts. |
| FIS-04 | IS et barèmes | partiel | fiscalite_is_service.py ; tests08_1/101  ; [512](../../Test/rapport_fiscalite_concurrence_512.md) | Taux/situations applicables à vérifier sur source officielle pour le scénario  Complément512 : paramètres/retraitements protégés pendant clôture, mutations et confirmation exclusives par société/exercice, double confirmation409 ; instantané cohérent et compléments acomptes postclôture conservés.245tests finaux réussis dont Edge fiscal. Stock global déficits historiques et règlements CSS hors de cette garantie. |
| FIS-05 | CM et CSS | partiel | fiscalite_cm_service.py, fiscalite_css_service.py ; migrations023/025 | Exonérations/assiette ne doivent pas être déduites arbitrairement |
| FIS-06 | Acomptes et paiement partiel | partiel | fiscalite_acomptes_service.py ; migration024 ; tests088/092/093  ; [512](../../Test/rapport_fiscalite_concurrence_512.md)  ; [514](../../Test/rapport_deficits_multiexercices_514.md) | Paiement, solde et retard à rapprocher aux écritures et calendrier  Complément512 : paramètres/retraitements protégés pendant clôture, mutations et confirmation exclusives par société/exercice, double confirmation409 ; instantané cohérent et compléments acomptes postclôture conservés.245tests finaux réussis dont Edge fiscal. Stock global déficits historiques et règlements CSS hors de cette garantie.  Complément514 : stock global des déficits stable pendant clôture/confirmation ; six mutations exclusives entre exercices, solde1000 consommé une fois et seconde proposition0 après reprise. Contrôles du déficit utilisé conservés.256tests finaux réussis. Protection de concurrence, sans nouvelle interdiction permanente de saisie historique ; CSS/lectures/directSQL distincts. |
| FIS-07 | Retenues et crédits IS | partiel | fiscalite_credits_service.py ; migration025 ; tests089/127 | Attestation requise ; ne pas déduire un crédit d'un taux seul |
| FIS-08 | Déficits reportables | partiel | fiscalite_deficits_service.py ; migration022 ; tests08_3 | Millésimes et imputations annuelles à tester dans E2E |
| FIS-09 | Liquidation confirmée et historique | partiel | fiscalite.py ; migrations024/066 ; tests094/101  ; [512](../../Test/rapport_fiscalite_concurrence_512.md)  ; [514](../../Test/rapport_deficits_multiexercices_514.md) | Snapshot présent ; cohérence comptable/fiscale annuelle à exécuter  Complément512 : paramètres/retraitements protégés pendant clôture, mutations et confirmation exclusives par société/exercice, double confirmation409 ; instantané cohérent et compléments acomptes postclôture conservés.245tests finaux réussis dont Edge fiscal. Stock global déficits historiques et règlements CSS hors de cette garantie.  Complément514 : stock global des déficits stable pendant clôture/confirmation ; six mutations exclusives entre exercices, solde1000 consommé une fois et seconde proposition0 après reprise. Contrôles du déficit utilisé conservés.256tests finaux réussis. Protection de concurrence, sans nouvelle interdiction permanente de saisie historique ; CSS/lectures/directSQL distincts. |
| LIA-09A | États existants, ETIC et contrôles croisés | bloqué | liasse_service.py, etic_service.py ; rapport_session09a | Société réelle : IF/ICE absents, FEC16 bloquants, ETIC9/23 ; ne bloque pas les développements indépendants |
| LIA-09B | Référentiel exhaustif des tableaux DGI | absent | ETIC CGNC présent, pas de catalogue DGI exhaustif versionné | Nécessite codification officielle du millésime applicable |
| LIA-09C | XML/EDI SIMPL-IS | bloqué | Bouton désactivé dans LiasseFiscale.jsx | XSD/codification officiels applicables non validés ; aucun format inventé |
| LIA-09D | Import balances N/N-1, mode Liasse seule | partiel | balance_import_service.py, ImportBalanceLiasse.jsx ; migration071 ; ZIP142/155/156/159 ; [462](../../Test/rapport_logos_exports_462.md), [463](../../Test/rapport_logos_xlsx_463.md) ; [677](../../Test/rapport_balance_exports677.md) | Versions immuables, rechargement et exports. 677 ajoute le bilan détaillé brut/amortissements/net, les comptes sources N/N-1 et le XLSX serveur portant version/empreinte et logo actuel, sans recalcul des agrégats historiques. Sous-postes pour mémoire, inconnus explicites ; aucune écriture ni archive fiscale complète déduite. Fiscalité/ETIC autonome et dossier Liasse seule complet restent à développer.  Complément679 : bilan détaillé et sources normalisées consultables, filtres/pagination, contrôles de version/jeton et droits ;72tests réussis. Cinq E2E de balances réexécutés dans la finale681.  Complément687 : échéances documentaires explicites, partiels/inconnus/reliquats, parent et nouvelle version immuable, PDF/XLSX ;97tests finaux réussis215,25s, restauration82tables. ETIC officielle et dossier fiscal complet toujours partiels.  Complément689 : dossier ZIP de préparation (PDF/XLSX, sources et manifeste), lecture sans écriture ;46tests finaux réussis137,87s et restauration82tables. Aucune archive fiscale officielle déduite.  Complément691 : justificatifs par version, auteur/taille/SHA figés, intégrité des octets et ZIP ;104 manuelle, restauration83tables/cinq fichiers.445testsA puis33ciblésB, autres fonctions ETIC/fiscales encore partielles. Complément693 : notes ETIC justifiées par rubrique, auteur et catalogue figés, nouvelle version et PDF/Excel/ZIP ;111tests finaux réussis, restauration83tables/cinq fichiers. Les tableaux structurés et le financement restent partiels. Complément695 : financement documentaire N/N-1, flux explicitement justifiés, CAF/totaux/écarts, calcul figé, droits et PDF/Excel/ZIP ;138tests du périmètre et24du moteur réussis. Autres tableaux ETIC structurés et compléments fiscaux toujours partiels.  Complément697 : B8/B9 structurés documentaires, versions/sources/inconnus et exports ;163 tests connexes réussis en 625.91s, restauration83tables. Autres ETIC et compléments fiscaux partiels.  Complément699 : autres six annexes manuelles, dates/unités exactes et versions/exports ;198 tests connexes réussis en 776.78s. Autres ETIC/fiscalité autonomes toujours partiels.  Complément701 : arithmétique C1 figée, inconnus/écarts et exports sans correction ;213 tests connexes et347 du socle annuel réussis. Autres états ETIC/fiscalité indépendants partiels. |
| LIA-09E | État des ventes annuel fiscal | partiel | Préparation interne, pièces et avoirs signés, CSV/Excel/PDF ; [423](../../Test/rapport_exports_ventes_423.md), [561](../../Test/rapport_ventes_raccordement_561.md) | Raccordement arithmétique aux comptes711/712 validés hors clôture, mouvements manuels visibles séparément, instantané RO/RR et empreinte incluant Journal. Un écart nul ne prouve pas chaque pièce. Format fiscal officiel et exhaustivité documentaire hors facturation à qualifier ; préparation extérieure aux archives fiscales. |
| LIA-09F | Rémunérations allouées aux tiers | partiel | [Préparation interne759](../../Test/rapport_remunerations_tiers759.md) ; balance_remunerations_tiers_service.py ; formulaire et exports | Profil/identités/mouvements versionnés, montants comptabilisés/soumis/retenus distincts, sources explicites, inconnus et corrections visibles ;226connexes+2annuels réussis. Modèle administratif151 et états particuliers applicables non intégrés ; aucun rapprochement comptable automatique ni dépôt validé. |
| LIA-09G | Taxe professionnelle et annexes | partiel | [Préparation interne761](../../Test/rapport_taxe_professionnelle761.md), balance_taxe_professionnelle_service.py, formulaire et exports | Profil/établissements versionnés, VL/classe sourcées et revues, simulation brute normale distincte des avis ;287connexes et2annuels réussis. Assiette complète, régimes particuliers, modèle administratif et montant dû non validés. |
| LIA-09H | Dossier annuel et prêt à déposer | partiel | etats.py, LiasseFiscale.jsx ; migrations027/073/076 ; ZIP172/181 ; [462](../../Test/rapport_logos_exports_462.md), [463](../../Test/rapport_logos_xlsx_463.md) | Finalisation réelle Edge dossier fictif, PDF/XLSX ouverts, version/SHA exacts, snapshot figé après changement société, refus doublon/mutation ; prêt à finaliser interne ne vaut pas dépôt DGI Logo de l’identité inclus dans les nouvelles liasses ; anciennes archives sans logo non enrichies avec les paramètres courants. Référentiel DGI et dépôt officiel toujours incomplets. |
| LIA-EXP | PDF/Excel des états et ETIC | terminé | liasse_pdf.py, LiasseFiscale.jsx ; tests120/128/131 ; ZIP195/256 | Repères internes T1 Bilan/T2 CPC/T3–T25 ETIC :24tests et1Edge exports/archive réussis ; codes persistés et SHA conservés. Bilan detaille256 UI/Excel/PDF :3nouveaux+16connexes+1archive passent, totaux preserves. Anciennes archives agregees conservees. Pas de codification officielle DGI revendiquée. |
| LIA-FEC | FEC et diagnostics | partiel | fec_service.py, fec_source_recovery_service.py ; [446](../../Test/rapport_restauration_runtime_acl_446.md) ; [451](../../Test/rapport_justificatifs_modeles_451.md), [452](../../Test/rapport_restauration_justificatifs_452.md), [457](../../Test/rapport_journal_lecture_457.md) | Ordre des lignes persistantes stabilisé par identifiant, copie sans mutation ORM ; FEC identique octet par octet après restore. Contrôles des 18 colonnes et justificatifs maintenus. Pièces historiques incomplètes à compléter avec preuve, sans réparation arbitraire. Références prioritaires après validation, recherche par pièce et18champs vérifiés ; FEC2025 identique après restore. Lecteur voit les anomalies sans tentative de réparation. Brouillons/références manquantes des cas négatifs restent visibles ; aucune pièce historique inventée. |
| UX-01 | Formulaires, scroll et lisibilité | partiel | tests065–086, tests React124 ; ZIP253/257 ; [466](../../Test/rapport_logos_impression_466.md), [467](../../Test/rapport_pdf_textes_467.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md)  ; [545](../../Test/rapport_credits_consultation_seule_545.md) | Tables factures etlettrage auparavant hauteur0/25px : chacune3Edge troisviewports passes, selections etvalidation natives ;13connexes chacun. Autres ecrans restent a completer. Menu mobile370 :contenu390px au lieu de170, navigation repliable et clavier ;4parcours,40connexes puis18finaux après correction du filtre Effets, tous réussis. [Rapport370](../../Test/rapport_navigation_mobile_370.md). Logo en impression Journal/TVA, texte littéral dans les PDF financiers et nom du livre ; boîte système et version Excel du partenaire à vérifier.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts.  Complément545 : consultation seule Avoirs/Acomptes sans commande de mutation, historique actif/crédit libre/chèque en attente/PDF conservés ;6Edge vente/achat lecteur390/1440 et comptable1440,28connexes et build réussis.403 directs et absence de mutation vérifiés. Aucun calcul ou droit serveur changé ; autres écrans distincts. |
| UX-02 | Rafraîchissement après mutation et contextes | partiel | Contextes et pages ; ZIP266/269/270/273/274/275/279 ; [453](../../Test/rapport_pieces_telechargement_453.md), [457](../../Test/rapport_journal_lecture_457.md) ; [463](../../Test/rapport_logos_xlsx_463.md), [470](../../Test/rapport_lecture_journal_historique_470.md) ; [474](../../Test/rapport_lectures_comptables_474.md)  ; [541](../../Test/rapport_factures_proforma_lecture_541.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md) | Frais articles relus sansF5, aperçu préfixes/sauvegarde Fiscalité273, édition TVA275 et filtre délai279 connectés ; contextes tardifs balances/grandlivre/banque protégés. Tous les autres écrans restent à vérifier. Échec de suppression/document indisponible signalé sans faux succès ; pièces et compléments relus sansF5, commandes Journal adaptées au rôle. Autres écrans et changement de rôle externe en temps réel restent à étendre. Export attend l’identité société ; échec de lecture du Journal affiché avec relance, sans afficher de faux totaux. Le bloc brouillons de l’accueil affiche aussi erreur/chargement et relance ; les indicateurs indépendants restent visibles. Grand livre sans faux résumé nul en erreur.  Complément541 : statut proforma existant restitué par création/liste API, sans préfixe déduit ni migration ;2parcours vente/achat PDF/conversion/comptabilisation/FEC et18connexes réussis. Recette visuelle540 reprise séparément.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts. |
| UX-03 | Plan comptable rapide et libellés | terminé | planComptableCache.js, FormulaireEcriture.jsx ; tests063/064 | Vérifier invalidation après mutation de plan |
| IND-01 | Tests unitaires et recettes API | partiel | [Globale430](../../Test/rapport_consolidation_globale_430.md) ; [session](RAPPORT_SESSION_20261015.md) ; [459](../../Test/rapport_consolidation_reprise_459.md) ; [462](../../Test/rapport_logos_exports_462.md), [472](../../Test/rapport_tva_parametres_runtime_472.md) ; [478](../../Test/rapport_qualification_finale_478.md) ; [480](../../Test/rapport_protection_sql_tva_480.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md)  ; [543](../../Test/rapport_factures_finalisation_concurrente_543.md) | Globale 430 historique :3426 réussis sur ses sources figées. Les suites 433–448 réussissent dans leurs périmètres, sans additionner les nombres recouvrants. Dernière 448 :44 connexes, zéro échec/erreur/ignoré. Pas de nouvelle globale 3426 ni de recette humaine validée. 61cas regroupés sur sources finales :Node/Python purs, API/Edge sur installation091 commune et restauration conjointe indépendante. Invariants finaux/ACL/16empreintes conformes ; pas une nouvelle suite globale complète. Tests ciblés réels, résultats et échecs initiaux dans les rapports ; Qualification finale478 : 143 réussis en 423,15 s, zéro échec/erreur/ignoré ; 780 empreintes/ACL conservées, invariants à zéro. Deux parcours de catalogue476 supplémentaires réussis sans changement produit. Globale historique430 non revendiquée à nouveau.  Complément094 distinct :22réussis78,05s etrestauration1réussi68,24s ;la143478reste une qualification runtime093, pas une globale094.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts.  Complément543 : double validation/conversion vente et achat sans erreur500 ; parent relu sous verrou, validation200/200 même numéro et conversion200/400, un seul mouvement de stock2→1/3, répétition sans mutation puis comptabilisation/validation/FEC.4nouveaux et356+247exécutions finales sur sources figées ; aucune garde SQL retirée. |
| IND-02 | E2E navigateur connecté sur base vierge | partiel | e 2 e_isole_support.py ; [448](../../Test/rapport_consolidation_runtime_448.md) ; [459](../../Test/rapport_consolidation_reprise_459.md) ; [462](../../Test/rapport_logos_exports_462.md), [472](../../Test/rapport_tva_parametres_runtime_472.md)  ; [540](../../Test/rapport_factures_consultation_seule_540.md)  ; [543](../../Test/rapport_factures_finalisation_concurrente_543.md)  ; [547](../../Test/rapport_grh_registre_pdf_547.md) | Dix parcours Edge, deux API et deux oracles regroupés sur la même application/schéma 82 SQL sous LOGIN limité ; plus affectation/ACL/rôle absent. Année stock/TVA/inventaire et année bancaire distinctes vérifiées. Scénario utilisateur 218 cas toujours à effectuer. Parcours de reprise regroupés sur main:app/LOGIN limité, sociétés fictives et PostgreSQL nonce ; source commune31sociétés/63écritures/168lignes et2clôtures. Recette humaine et scénario annuel exhaustif non prévalidés. Edge1440/390, API réelle, PostgreSQL nonce sous LOGIN limité ; logos, modèles, facturation/règlement/lettrage, TVA et instruments dans la recette regroupée469.  Complément540 : Factures en consultation seule sans commande de mutation, CSV/PDF et justificatifs d’achat téléchargeables, API403 et absence de mutation vérifiées.6Edge vente/achat lecteur390/1440 et comptable1440, puis352+247exécutions finales incluant541 sur sources figées ; buildVite réussi. Autres écrans et recette utilisateur distincts.  Complément543 : double validation/conversion vente et achat sans erreur500 ; parent relu sous verrou, validation200/200 même numéro et conversion200/400, un seul mouvement de stock2→1/3, répétition sans mutation puis comptabilisation/validation/FEC.4nouveaux et356+247exécutions finales sur sources figées ; aucune garde SQL retirée.  Complément547 : registre interne congés/absences PDF avec société/logo, filtre de statut, périodes/jours calendaires et historique déclarés. Admin/lecteur,2sociétés,notes longues et Edge390/1440,5ciblés/208connexes et build réussis, lecture sans mutation. Aucun calcul de congé acquis/paie/taux ni déclaration sociale ajouté ; statut global partiel conservé. |
| IND-03 | Migrations et intégrité PostgreSQL | partiel | Scripts 001–091 ; [CLI090](../../Test/rapport_installation_vierge_090.md) ; [091 explicite](../../Test/rapport_consolidation_runtime_448.md) ; [458](../../Test/rapport_ecritures_capacite_458.md), [459](../../Test/rapport_consolidation_reprise_459.md) ; [464](../../Test/rapport_modeles_avances_464.md), [472](../../Test/rapport_tva_parametres_runtime_472.md) ; [480](../../Test/rapport_protection_sql_tva_480.md)  ; [490](../../Test/rapport_journal_cloture_490.md)  ; [563](../../Test/rapport_installation_vierge_098.md) | CLI 090 :81 SQL distincts, 17 rejeux, 36 tables métier vides ; anciens 082/084/087/089 préservés. 091 appliquée explicitement dans la recette regroupée, pas par le CLI 090. SQL historiques/main/models/schemas inchangés ; données historiques et activation réelle non validées. Aucun nouveau SQL ni ancienne migration modifiée dans451–459. CLI090 inchangé,091 explicite dans le banc ; capacité réelle18,2 confirmée et sources figées. Activation sur installation réelle non effectuée. 092 et093 additives, rejouées sur bases jetables, aucune ancienne migration réécrite ; droits TVA limités et restauration native des ACL. 094rejouée sans changement de données/schéma/ACL, anciennes migrations conservées ;pas de migration réelle exécutée.  Complément490 : en-têtes/lignes Journal sérialisés avec clôture488 via098 additive, deux périmètres des déplacements protégés et clôture sans exercice bloquante. 155exécutions finales dont Edge vente/achat/clôture et restauration098 ; installation réelle et concurrence globale des autres modules restent à qualifier.  Qualification563 : CLI098 unique,89SQL/25rejeux/114executions, schema/ACL/sequences/donnees idempotents ;37tablesmetier vides etcluster nettoye. Aucun SQL modifie ou deploiement reel. |
| IND-04 | Logs et audit append-only | partiel | main.py, production_audit_service.py ; migrations036/073–075 ; ZIP167/171/177/178 | Connexion LOGIN nonowner, fonctions audit definer et refusDML réels ; immutabilité archives/complements y comprisTRUNCATE et droits hérités ; déploiement exhaustif à valider |
| IND-05 | Installation et déploiement | partiel | [Exploitation](../EXPLOITATION_HISABPRO.md) ; [installation090](../../Test/rapport_installation_vierge_090.md) ; [restoreACL](../../Test/rapport_restauration_runtime_acl_446.md) ; [452](../../Test/rapport_restauration_justificatifs_452.md)  ; [490](../../Test/rapport_journal_cloture_490.md)  ; [549](../../Test/rapport_restauration_grh_registre_549.md)  ; [563](../../Test/rapport_installation_vierge_098.md) | Installation de laboratoire 090 et restauration 090 avec droits par colonne vérifiées ; 091 ensuite testée sur le cycle annuel regroupé. Aucun déploiement réel. Rôles, secrets, propriétaires, fichiers joints, droits des autres modules et reprise de production à qualifier. Restauration091 avec fichiers et droits natifs qualifiée sur deux bacs ; démarrage cible main:app sous LOGIN limité. Rôles/secrets préparés séparément ; aucun déploiement ou restauration de production validé.  Complément490 : en-têtes/lignes Journal sérialisés avec clôture488 via098 additive, deux périmètres des déplacements protégés et clôture sans exercice bloquante. 155exécutions finales dont Edge vente/achat/clôture et restauration098 ; installation réelle et concurrence globale des autres modules restent à qualifier.  Complément549 : restauration froide098 réellement exécutée avec données GRH, logo et historique ;74tables/schéma/données/ACL,source préservée et cibles nettoyées. JSON identique et texte PDF identique hors heure d’édition sous LOGIN non propriétaire ;1test61.21s réussi. Aucune restauration de production ni recette utilisateur validée.  Qualification563 : CLI098 unique,89SQL/25rejeux/114executions, schema/ACL/sequences/donnees idempotents ;37tablesmetier vides etcluster nettoye. Aucun SQL modifie ou deploiement reel. |
| IND-06 | Cahier recette et oracle indépendant | terminé | generer_cahier_recette.py ; docs/recette PDF/XLSX/JSON ; ZIP232/247/262/277/284/298/306 ; [annexe commerciale](../../Test/rapport_annexe_recette_commerciale.md) | Cahier218cas,50écritures :208Non testé/10Bloqué. GRH26cas :23Non testé/3Bloqué. Annexes commerciale5cas, bilan4cas, corrections8cas et achats partiels2cas distinctes. RAS estimation298 et capture306 : chacune2Non testé, PDF6/9pages et Excel3onglets. Documents réellement ouverts, oracles indépendants et suivi vierge ; aucun résultat utilisateur prévalidé. |
| OPT-01 | Paie / GRH demandée le 7 octobre | partiel | CNSS.jsx, employes.py, grh.py, paie_service.py ; migrations080–082 ; ZIP192/194/198/199/203/226–232 ; [464](../../Test/rapport_modeles_avances_464.md) ; [476](../../Test/rapport_catalogue_avances_ui_476.md)  ; [482](../../Test/rapport_avances_salaries_482.md)  ; [483](../../Test/rapport_avances_acces_483.md)  ; [547](../../Test/rapport_grh_registre_pdf_547.md)  ; [549](../../Test/rapport_restauration_grh_registre_549.md)  ; [551](../../Test/rapport_grh_pdf_limites_551.md) | Dossiers, simulation Decimal conditionnelle, congés tracés et preuves documentaires versionnées livrés. Taux invalides refusés, dates inconnues non présumées. Taux sociaux officiels, variables, bulletins figés, déclarations et écritures SA restent à traiter. Cinq modèles Journal d’avances/récupération/remboursement personnel ; aucun pont automatique ajouté au bulletin, ni droit à retenue ou taux social inventé. Cinq modèles réellement sélectionnés/calculés puis annulés dans Paie en1440/390 ; aucune écriture créée par la consultation.  Registre095 : rattachement explicite salarié/ligne3431 définitive, soldes limités aux affectations, mouvements non affectés et annulations motivées conservés. Aucune écriture ni retenue automatique. Installation réelle095 et recette utilisateur à effectuer ; clôture concurrente complète non qualifiée.  Quatre Edge additionnels : lecture sans action,403 sur POST lecteur, aller-retour A/B avec formulaire abandonné et404 étrangers, écritures et registres inchangés.  Complément547 : registre interne congés/absences PDF avec société/logo, filtre de statut, périodes/jours calendaires et historique déclarés. Admin/lecteur,2sociétés,notes longues et Edge390/1440,5ciblés/208connexes et build réussis, lecture sans mutation. Aucun calcul de congé acquis/paie/taux ni déclaration sociale ajouté ; statut global partiel conservé.  Complément549 : restauration froide098 réellement exécutée avec données GRH, logo et historique ;74tables/schéma/données/ACL,source préservée et cibles nettoyées. JSON identique et texte PDF identique hors heure d’édition sous LOGIN non propriétaire ;1test61.21s réussi. Aucune restauration de production ni recette utilisateur validée.  Complément551 :2rendus purs sans logo avec commentaires extrêmes/texte échappé réussis,aucune troncature ; aucun changement produit. |
| GRH-01 | Dossiers salariés et accès | terminé | migration080, employes.py ; ZIP192/194/198/203 | CRUD, archivage/restauration, contrats optionnels, lecture et multi-société testés sur PG isolé et Edge ; aucune conversion automatique en CDI. |
| GRH-02 | Demandes congés et absences | terminé | grh.py, migration081, CNSS.jsx ; ZIP198/199 | Dates inclusives informatives, workflow, chevauchements concurrents et historique append-only testés. Aucun solde légal ni retenue salariale calculé. |
| GRH-03 | Paie réglementaire complète | bloqué | paie_service.py et rapports paie ; annexe recette201 ; audit220 | Preuves officielles IR/AMO/TFP documentées avec limites, parts CNSS etréférentiel social2026 non entièrement confirmés. Bulletin figé, variables, déclarations etjournal SA automatique non implémentés. Simulation de laboratoire ne valide pas ces fonctions. |
| GRH-04 | Sources et versions documentaires du référentiel paie | terminé | paie_referentiel_service.py, employes.py, CNSS.jsx ; migration082 ; ZIP227/228/230/231/232 | 24 ciblés API/PG et 172 avec connexes ; deux Edge avec GET/POST tardifs, scopes société/année et droits réels. Versions immuables, dates absentes conservées et statut Périmé. Consignation ne modifie aucun taux et n'autorise pas la paie définitive ; référentiels de calcul encore globaux. Annexe26cas utilisateur non prévalidés. |
| UX-04 | Retard de factures et paiements partiels | terminé | echeancesFactures.js, Dashboard.jsx, Factures.jsx ; ZIP197 | 19tests Node/Edge/API réels ; échéance réelle prioritaire, délai zéro, pas de retard le jour même, alerte et filtre cohérents après solde. |
| ADM-11 | Logo société optionnel | terminé | LogoSociete.jsx, logo_societe_service.py ; ZIP200 | Import PNG/JPEG borné, aperçu/retrait, droits admin et image dans vrai PDF facture :20ciblés et1E2E réussis par agent. Historique préservé. |
| UX-05 | Factures : filtres par dates et totaux complets | terminé | Factures.jsx, facturesPeriod.js, collecterPages.js ; ZIP210 | Bornes inclusives, propre date des avoirs,100/101factures, exportCSV, HT457/TTC548,40 testés surAPI/Edge ; indicateurs documentaires explicitement distincts d'un CA comptable. |
| UX-06 | Délai et échéance dans les formulaires facture | terminé | Factures.jsx ; ZIP215 | Changement volontaire du délai recalculant création/édition, délai0 et fins de mois testés ; échéance manuelle conservée pour les autres modifications. |

## Complément de reprise à 17:03 UTC

- ZIP183 : avoir, retour et annulation connectés ; 1 Edge et43connexes réussis par agent, écriture originale intacte.
- ZIP184/187 : permissions runtime du cycle commercial, migration077 et079, tests LOGIN non propriétaire exécutés. Permissions héritées globales des anciennes migrations005/008/012 non supprimées ; manifeste complet reste partiel.
- ZIP185/188 : montants d'échéanciers et acomptes finis, rejets sans mutation testés réellement. ZIP186 : suppression SQL d'une facture validée refusée.
- ZIP189 : acompte400, facture1200, solde800, validation etlettrage ; 28tests réussis par principal, dont API isolée et Edge.
- ZIP190 : liquidation IS connectée avec oracle de laboratoire et snapshot ; 1 Edge et29connexes réussis par agent. Ce jeu ne valide aucun taux réglementaire nouveau.
- ZIP191 : nouveaux codes de lettrage minimum trois lettres ; 18tests réussis par principal, historiques préservés.
- La checklist utilisateur comporte73points audités ; ses statuts sont actualisés après chaque livraison dans CHECKLIST_UTILISATEUR_20261007.md.
- Numérotation interne T1…T25 et correction des factures échues partiellement payées livrées et testées dans195 et197.
- ZIP204 : styles des tables isolés, aucun débordement GRH sur desktop et actions mobiles accessibles ;5E2E et13connexes exécutés par principal.
- ZIP205 : six listes commerciales triées par création puis identifiant, sans inventer de date historique ;6E2E,29connexes et3parcours connectés exécutés par agent.
- ZIP206/207 : taux RAS finis et contrat API conservant le taux à l'édition ;42tests puis89tests API/Edge/PGisolé exécutés par agent. Les taux historiques invalides sont diagnostiqués sans réécriture.
- ZIP208 : audit RAS ; RAS HT partielle, TVA distincte absente, textes officiels complets et qualification restent nécessaires.

## Dépendances et conclusions

- Développement global : **partiel**. Tests automatisés ciblés : **validés dans
  leurs périmètres exécutés**, pas une validation globale de l'application.
  Recette utilisateur : **à effectuer**. Mise en production : **non prête**.
- Les lots parents REPRISE-PG et REPRISE-LOTS-FINAUX ont été réconciliés avec
  leurs livraisons148–150 et146/147/154 ; leurs tests historiques sont distingués
  des commandes réellement exécutées le7octobre.
- Aucune connexion au PostgreSQL réel autorisée dans cette reprise. Les
  constats09A sur la société réelle restent des résultats historiques.

- Le plan et les périodes sont des prérequis du premier flux de facturation.
- Facture, règlement, stock, TVA, grand livre et auxiliaire doivent être contrôlés
  ensemble ; un test de fonction isolée ne valide pas ce parcours.
- La balance importée ne contient ni justificatifs, ni échéances, ni flux détaillés
  de financement : ces informations ne doivent pas être inventées.
- L'archivage interne doit rester immuable, et ne constitue pas un dépôt fiscal.
- Les scripts 065/067/068/069/070 de réparation historique doivent être examinés
  séparément du déploiement du schéma ; aucune exécution sur la base réelle cette session.
- La présence d'une migration n'est pas une preuve de son application réelle.

## Vérification de la spécification EDI

Le MEF publie un [cahier EDI version 1.0 daté de 2010](https://www.finances.gov.ma/Publication/dgi/2010/9370_cahierdescharges.pdf)
et l'[annonce de lancement](https://www.finances.gov.ma/Fr/Pages/detail-actualite.aspx?fiche=1414).
Ces publications anciennes ne valident pas le schéma applicable au millésime de
recette. Les versions repérées sur des sites tiers ne sont pas utilisées comme
spécification de développement. XSD, codification et exemples officiels actuels
restent à obtenir et vérifier avant 09B exhaustif et 09C.

La recherche265 du8octobre confirme ces limites ; les publications2010 ne
valident pas le millesime2026. [Journal des sources et echecs d'acces](SOURCES_DGI_MILLESIME_20261008.md).

## Compléments vérifiés du 9 octobre

Reprise suivante : **19:44–21:44 UTC**, après interruption du quota.
Le journal et les processus ont été inspectés ; les services utilisateur ont
été conservés. La globale286 (2582 réussites) est une preuve de la version
précédente ; elle ne prévalide pas les nouveaux changements RAS.

Lots291/292 : estimation documentaire distincte de l'imputation historique,
aucune OD RAS entière au premier nouveau règlement. Facture1200, estimation100,
dû1200 ; paiement1100 laisse100. Sept Edge réels, API et tests connexes passent,
avec préservation des historiques et diagnostics NULL. Le prolongement304
ajoute quatre Edge vente/achat1365/390 : paiement complémentaire100, validation
des deux écritures de paiement puis lettrage trois lignes AAA ; trois écritures,
sept lignes, D=C2400, collectif soldé et banque+1200/−1200.

Recouvrement295 :34tests dont Edge desktop/mobile et isolation ; inconnus
visibles et exportés. Consommateurs296 :12tests API/exports, dashboard NULL
et PDF âgé avec lignes diagnostiquées et totaux À vérifier. Les interfaces
complémentaires et une capture effective par règlement sont des lots distincts.
Les statuts généraux restent partiels ; RAS TVA et attestations ne sont pas
déclarées achevées. [Sources officielles et limites294](../../Test/rapport_sources_ras_20261009.md).

La reprise du10octobre livre293/303 : capture déclarative par virement ou
espèces comptabilisés, saisie explicite, OD brouillon puis validation et
annulation liée. Cinq Edge finaux et contrôlesAPI/SQL passent ; la migration083
reste manuelle, horsBase/bootstrap. Sauvegarde/restauration305 réellement
exécutée sur deux clusters nonce : onze tables/huit triggers et droits runtime
reprovisionnés, données inchangées.

Le lot308 reproduit les anciennes annulations injustifiées puis impose une OD
exacte unique ;409sansmutation si la piste est incertaine. Sept tests et trente
connexes passent ; aucun historique réel réparé. Deux Edge307 prolongent un
chèque rejeté jusqu'au virement, à la validation et au lettrage : cinq écritures,
onze lignes D=C6000, banque1200 et comptes d'attente/collectif soldés.

Annexe estimation298 : deuxNon testé, PDF6pages/Excel3onglets ; annexe capture306 :
deuxNon testé, PDF9pages/Excel3onglets. Les oracles sont indépendants et le suivi
utilisateur reste vierge. La nouvelle globale300 est une preuve distincte,
exécutée par le principal après ces lots sur645empreintes figées :
2627réussis,12échecs,0erreur,0ignoré,32avertissements ; code1 en2386,05s.
Empreintes avant/après identiques. La variable de société non définie dans
le calcul du crédit d'avoir est démontrée par les traces. Correction309 et
nouvelle consolidation restent des preuves distinctes ; cette globale300
ne sera jamais reclassée comme verte.

Les demandes article emballage/transport sont exposées269 et les requêtes numériques sont sécurisées268 (207ciblés puis38connexes). Les frais restent à reporter explicitement sur les documents. Le filtre tiers279 utilise le délai de la fiche, avec comptant0 et valeurs inconnues, sans calculer une échéance. La recette utilisateur garde ses statuts à renseigner.

Le lot310 rend sept nombres historiques d'article consultables sousNULL avec
diagnostics, sans réparer les données. Les champs inconnus restent vides et
une édition envoie seulement les valeurs modifiées. Devis/commandes/factures
requièrent prix et TVA explicites lorsqu'ils sont inconnus ; totaux indicatifs
À vérifier et choix TVA atomique. Agent92tests puis230connexes ; principal
3tests dont2Edge47,20s,5connexes88,95s et build139modules12,72s réussis.
Inventaire, familles et moteurs sont des consommateurs distincts encore à
sécuriser. La consolidation311 termine avec 2 734 réussites et 4 échecs,
sans erreur ni ignoré, 32 avertissements ; code1 en3 150,16s. Les649sources
sont identiques avant/après. Deux échecs articles sont des POST de lecture
du stock comptés à tort comme mutations ; deux autres sont des délais
navigateur à la navigation ou au login, sans cause produit démontrée.
La mesure est corrigée séparément312 et les relances sont consignées dans
son [rapport312](../../Test/rapport_e2e_articles_diagnostic_stock_mesure.md).
Les trois modules ciblés passent :13réussites140,11s, code0 ; les quatre
cas en échec311 sont exercés. Cette globale reste une preuve d'échec,
sans requalification et sans addition des suites.

L’annexe corrections277 contient huit cas Non testé : PDF18pages, Excel7feuilles, quatre sociétés fictives et oracles indépendants. Elle complète le cahier annuel et les annexes existantes ; elle ne certifie ni les données réelles ni la conformité réglementaire.

Le prolongement283 règle les deux factures issues des BR partiels : deux paiements600/1800 puis lettrage communAAA, quatre écritures/dix lignes D=C4800, fournisseur soldé, stock4 et deux entrées BR conservés. Huit tests finaux sont exécutés, sans changement applicatif. L’échec mobile de278 garde une cause non établie ; le diagnostic préserve désormais l’exception initiale.

L’annexe284 fournit deux cas supplémentaires Non testé, [PDF](../recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.pdf) et [Excel](../recette/ANNEXE_RECETTE_ACHATS_PARTIELS_20261009.xlsx), six pages et trois feuilles. Ses oracles sont indépendants ; le solde bancaire fictif−2400 n’est pas une trésorerie réelle financée.

## Reprise du 10 octobre, 10:45 UTC — inventaire313

Le lot313 sécurise inventaire, clôture et livre/PDF pour les nombres historiques inconnus, sans réparation des données. 148tests intégrés exécutés par le principal et4Edge exécutés par l’agent ; ces suites distinctes ne sont pas additionnées aux anciennes preuves. Build139modules4,93s et compilations réussis. Le différentiel313 comprend17fichiers, CRC et arborescence vérifiés.

La globale315 est terminée sur653sources identiques :2742réussites,49échecs,
5erreurs,0ignoré,32avertissements3410,26s. Le code de sortie du wrapper n’a
pas été récupéré ; le résultat XML/log démontre l’échec.52incidents concernent
le lancement Node/driver, deux sont des délais navigateur. Les preuves315,
311 et les délais LIM20 restent conservés ; un retest ciblé ne les requalifie
pas. Les70fonctions et73demandes conservent leurs statuts : aucun parcours
annuel humain ni production validé.

## Reprise du 10 octobre, 14:34 UTC

Le lot318 reproduit le500 lors d’une écriture sur un exercice implicite :
les périodes n’étaient pas insérées avant le trigger PostgreSQL. Correction
transactionnelle minimale,60tests réussis41,79s dont8nouveaux ; calendrier
partiel et périodes fermées conservés. [Rapport318](../../Test/rapport_exercice_implicite_periodes.md).
Le lot320 sert les polices localement : deux Edge réussis42,17s avec CDN
volontairement muets, ressources/fontes vérifiées et licences incluses.

Le lot324 rend les familles historiques à TVA inconnue lisibles avec
diagnostic et exige un choix explicite dans la fiche article/création rapide.
347tests backend,4Edge nouveaux et6Edge connexes réussis, snapshots conservés.
[Rapport324](../../Test/rapport_familles_tva_historique.md). Le lot326 retire
seulement l’alternative textuelle des glyphes décoratifs : visuels conservés,
noms accessibles restaurés, quatre Edge chargement/accessibilité passent.

Le lot330 remplace l’alerte de succès tardive après conversionBR par une
confirmation visible/status dès réponse API, avant fermeture de la fenêtre.
Quatre Edge passent60,01s, dont les deux cycles achats déjà présents jusqu’au
règlement/lettrage. [Rapport330](../../Test/rapport_facturation_br_retour_non_bloquant.md).
La [globale325](../../Test/rapport_non_regression_reprise_20261010_1434.md)
a terminé : 2 853 réussis, aucun échec/erreur/ignoré, 32 avertissements,
2 973,36 s, code retour 0. Les 675 empreintes, assets publics inclus,
restent identiques après exécution et à la reprise de 19:39 UTC.

Le [mode d’emploi Word](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx)
et son [PDF](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf),323, présentent
18fiches avec17contrôles Non testé. L’[annexe inventaire PDF](../recette/ANNEXE_RECETTE_INVENTAIRE_20261010.pdf)
et son [Excel](../recette/ANNEXE_RECETTE_INVENTAIRE_20261010.xlsx),317, proposent
19cas et un oracle indépendant. Les documents structurent la recette humaine
à effectuer ; ils ne la déclarent pas réussie.

## Reprise du 10 octobre, 19:39 UTC

- 332 : alertes de stock inconnues lisibles sans fausse rupture ni disparition,
  seuil5 et valeurs finies signées conservés.19tests par agent passent36,29s.
  [Rapport332](../../Test/rapport_articles_alertes_stock_historique.md).
- 333 : historique brut nullable avec diagnostics ; contraintes PostgreSQL
  préservées et refus de quantité0/-Inf réellement testés.45tests par principal
  passent, XML40,328s. [Rapport333](../../Test/rapport_mouvements_stock_historique_lecture.md).
- 334 : auditCMUP conditionnel, inconnues visibles et valorisation incomplète
  distincte de chaîne historique incomplète.95tests par principal passent,
  XML52,287s, dont deux Edge1365/390 sans500/erreurJavaScript/mutation.
  [Rapport334](../../Test/rapport_ledger_stock_nombres_historiques.md).
- 337 : guide Word/PDF version3,23pages et18fiches/17statuts Non testé,
  avec procédures du filtre et du recontrôleCMUP. Le Word reste à ouvrir
  dans Microsoft Office et la recette partenaire reste à effectuer.
- 335 : moteur des mutations et annulations sécurisé avant changement,
  qualification de toutes les origines, reprises idempotentes et périodes
  fermées conservées.106tests par agent passent98,28s ; baselines conservées.
  [Rapport335](../../Test/rapport_mutations_stock_historique.md).
- 339 : [procédure de mise à jour](../MISE_A_JOUR_SESSION_20261010.md)
  actualisée ;11liens et quatre différentiels vérifiés, sans nouvelle SQL.
  Installation réelle et recette partenaire à effectuer.
- 336 : consolidation exécutée par le principal,3009réussis,aucun échec,
  erreur ou ignoré,32avertissements,4072,44s,code0. Les680empreintes des
  sources/tests/SQL/configurations/assets restent identiques avant/après.
  Cette preuve couvre332–335 et précède341. [Rapport336](../../Test/rapport_non_regression_reprise_20261010_1939.md).
- 341 : coût historique nécessaire au BR déplacé dans le `try` existant,
  refus409 et rollback intégral. Baseline9échecs/4réussites ; finale agent
  122réussites227,75s dont3Edge achats/vente, XML relu par le principal.
  Priorités et formules inchangées ; aucune réparation ni migration.
  [Rapport341](../../Test/rapport_br_cout_historique.md).
- 342 : guide version4 Word/PDF23pages,18fiches17statuts Non testé,
  prérequis de stock au BR, dates2025, chemin des préfixes et dépannage.
  OOXML/CRC/11références/oracles et pages11/12/23 contrôlés ; procédure
  avec11liens et cinq ZIPs sans SQL vérifiée. [Preuves342](../../Test/rapport_guide_stock_br_342.md).

Les70statuts fonctionnels restent inchangés. Les correctifs des consommateurs
historiques ne constituent pas une validation annuelle exhaustive ou réglementaire.

## Reprise du 10 octobre, 21:29 UTC

- 343 : conversion BL/BR protégée avant commit : prix nécessaireNULL/non
  fini et dépassements de totaux refusés409 avec rollback intégral. Les
  prix connus0/explicites, la sélection partielle et les priorités historiques
  sont conservés.69tests principal réussis240,15s,25avertissements,code0,
  dont sept Edge ;683empreintes stables. Baselines et deux erreurs de
  préparation des nouveaux Edge conservées. [Rapport343](../../Test/rapport_conversion_bon_prix_historique.md).
- 344 : garde de montants partagée avant validation normale/proforma,
  snapshots et numéro définitif.91tests principal réussis170,78s,
 25avertissements,code0, dont58nouveauxAPI et quatre Edge connexes ;
 684empreintes stables. Dix validations invalides réellement persistées
 en baseline nonce sont empêchées ; aucun ancien document définitif réel
 modifié. [Rapport344](../../Test/rapport_validation_facture_montants_historiques.md).
- 345 : guideWord/PDF version5,23pages18fiches17statuts Non testé,
  refus et procédure avec prérequis342. OOXML/CRC/liens/oracles/layout
  contrôlés ; ouvertureOffice et recette humaine à effectuer.
  [Preuves345](../../Test/rapport_guide_montants_345.md).
- 346 : nouvelle consolidation3112cas collectés,684sources figées ;
  **en exécution**, aucun résultat final revendiqué à ce stade.
  [Suivi346](../../Test/rapport_non_regression_reprise_20261010_2129.md).

Les statuts70fonctions15terminé/46partiel/5absent/4bloqué ne changent pas.
Les autres sources historiques commerciales/fiscales restent à qualifier
sur leur propre preuve ; les suites superposées ne sont pas additionnées.

## Résultat définitif de consolidation346 — 11 octobre 2026

Cette mise à jour remplace l'état « en cours » de la reprise21:29 ci-dessus.
**3 105 réussis, 7 échoués, 0 erreur/ignoré**,32 avertissements,
4 000,94s,code1 ;684 empreintes identiques avant/après. La globale346
est **échouée**, sans promotion des statuts de couverture.
[Rapport et sept échecs](../../Test/rapport_non_regression_reprise_20261010_2129.md).
Un délai de connexion devis, quatre annulations RAS refusées422 et deux
attentes de rejet de date future restent à diagnostiquer. Le passage de
minuit peut affecter les dates calculées à l'import ; hypothèse à vérifier.
Les preuves ciblées343/344 restent distinctes, sans effacer cet échec.
Les contrôles négatifs344 sont API ; les quatre Edge344 sont des parcours
positifs connexes. La lecture UI des anciens montants invalides reste à
qualifier. GuideWord/PDFv5 livré, recette utilisateur et Office à effectuer.
Budget23:29UTC dépassé lors du suivi final : arrêter le développement,
livrer le cumulatif puis reprendre par le diagnostic isolé des sept cas.
Aucun PostgreSQL réel, donnée comptable réelle ou nouvelle migration touché.

## Reprise du11octobre08:11UTC — corrections de dates

-350 : diagnostic des sept échecs346,27cas passent àheurecourante avant
 correction ; diagnostic réseau du devis enrichi sansretry ni délai
 assoupli. Cause du délai de connexion nonétablie.
 [Rapport350](../../Test/rapport_diagnostic_sept_echecs_350.md).
-351 : quatre annulationsRAS reproduites422 à00h30locale et huit modales
 d'effets datées UTCveille/lendemain. Trois expressions utilisent désormais
 dateLocaleISO. Sélection finale63réussis25avertissements201,80s,code0,
 dont11Edgeconnectés et16composantsAPI simulée distincts. BuildVite5,85s
 code0, avertissementtaille conservé.
 [Rapport351](../../Test/rapport_dates_locales_reglements_351.md).
-352 : date future du banc calculée àl'import devenue courante après
 minuit. Deux reproductions échouées puis24tests ORM/structure réussis
 1,67s,code0. Dates calculées àl'exécution, assertions et backend conservés.
 [Rapport352](../../Test/rapport_effets_dates_minuit_352.md).
-353 : guideWord/PDFv6,23pages18fiches17statuts Non testé ; pieddate
 dérivé du titre11/10, sixliens procédure et11référencesguide/oracles
 contrôlés. WordOffice et recettehumaine àeffectuer.
 [Rapport353](../../Test/rapport_guide_dates_353.md).
-354 : consolidation achevée,3126réussis,0échec/erreur/ignoré,32avertissements,
 3866,88s,code0 ;686sources avant/après identiques. Cette globale précède357.
 [Rapport354](../../Test/rapport_non_regression_reprise_20261011_0811.md).
-357 : formulaire bancaire :date locale, saisie conservée au chargement
 et cartes non comprimées.45réussis dont13Edgeconnectés,112,18s,code0 ;
 build6,80s,code0 ;687sources finales stables, seules trois différences
 depuis354. Échecs intermédiaires conservés ;aucun clic forcé.
 [Rapport357](../../Test/rapport_rapprochement_date_locale_357.md).
-358 : guideWord/PDFv7 actuel,25pages,18fiches et17statuts Non testé ;
 fiche bancaire avec alternative manuelle400/800MAD, septliens procédure
 et11références/oracles contrôlés, page13 inspectée. Office àeffectuer.
 [Rapport358](../../Test/rapport_guide_banque_358.md).

La globale346 reste3105réussis/7échoués ; les suites ciblées ne sont pas
additionnées ni substituées àsa preuve. Couverture70fonctions et73demandes
inchangée. Aucun PostgreSQL réel, migration nouvelle ou écriture réelle
modifié. Prochaine tâche : lecture API/UI des anciens montants invalides
àqualifier ; règles fiscales/sociales et recettehumaine restent distinctes.

## Diagnostic de lecture historique et garde d'affichage — lots359/360

Recontrôle Edge après360 :1échec,7désélectionnés,25avertissements,
29,74s,code1. La facture saine reste invisible lorsque la lecture échoue ;
la garde UI ne corrige pas ce défaut. Les689sources restent identiques.

-359 : défaut noncorrigé. Deux contrôles sains/zéro réussis, cinqGET500
 etunEdge facture saine invisible :2réussis/6échoués,38,06s,code1.
 Diagnostic explicite hors collecte test_*.py ; oracle200 conservé ;
 photographies inchangées. Les chiffres invalides ne sont pas réparés.
 [Diagnostic359](../../Test/rapport_lecture_factures_historiques_359.md).
-360 : garde d'affichage uniquement. Compteurs « — », liste indisponible,
 CSVdésactivé etRéessayer réel sansF5.22réussis,25avertissements,109,16s,
 code0,dont11Edgeconnectés. Build6,25s0,compilation0,689sources stables.
 Les listes vides connues gardent leurs zéros. LeGET500 de359 reste visible.
 [Rapport360](../../Test/rapport_factures_erreur_lecture_360.md).
-GuideWord/PDFv8 actuel :25pages18fiches17statuts Non testé,390blocs,
 fiche04 décrit indisponibilité etRéessayer ; huitliens procédure,
 onze références/oracles,OOXMLCRC etPDF contrôlés,page7 inspectée.
 Office et recettehumaine nonfaits.

La globale354 couvre686sources avant357/359/360. Les45ciblés357,
22ciblés360 et diagnostic359 ne sont pas additionnés aux3126réussis354.
Les six échecs diagnostiques359 ne sont ni supprimés ni présentés comme
réussis. Couverture70fonctions et73demandes :statuts inchangés ;FAC03
reste partiel. Aucun PostgreSQL réel,migration ou donnée comptable réelle
touché. Production nonvalidée.

Prochaine tâche :reprendre diagnostic_lecture_factures_historiques.py,
qualifier la lecture API/UI avec montants inconnus explicites, conserver
factures saines et identités/lignes historiques. Couvrir règlements,RAS,
avoirs,échéanciers etexports sans faux0 ni exclusion silencieuse.

## Session du11octobre2026 — reprise13h06UTC — lots371 à377

- 371 :liste de règlements complète au-delà des100premières factures ;28tests réussis. [Rapport371](../../Test/rapport_reglements_pagination_371.md).
- 372 :paiement immédiat ventilé par client/fournisseur natif, transaction atomique, centimes exacts, UUID de reprise, référence commune, gardes des soldes, avoirs, acomptes et RAS.108ciblés connexes puis4Edge finaux réussis, sans additionner ces suites. [Rapport372](../../Test/rapport_reglements_par_tiers_372.md).
- 373 :globale réelle3235réussis et4échecs,0erreur/ignoré,4419,71s,code1 ;696empreintes stables. Cette preuve échouée est conservée. [Rapport373](../../Test/rapport_non_regression_reglements_373.md).
- 374 :guideWord/PDFv11,28pages,419blocs,18fiches et17statuts Non testé. Variante2026 distincte :factures120/240TTC,240ventilés120/120 puis120 ;5écritures, débit/crédit720,tiers360/360 et lettrage. [Rapport374](../../Test/rapport_guide_ventilation_374.md).
- 377 :course de clôture reproduite puis corrigée, réponses d'ancien exercice ignorées ; bancs admin/menu mobile adaptés.3E2E clôture en60,01s,8bancs en78,97s et9connexes en0,35s réussis ; build0 en9,29s. Les échecs intermédiaires restent consignés. [Rapport377](../../Test/rapport_regression_recette_377.md).

Couverture inchangée :70fonctions,15terminé/46partiel/5absent/4bloqué ;73demandes,40terminé/30partiel/2absent/1bloqué. Les règlements ventilés sont des règlements individuels, pas un instrument bancaire groupé. Aucune migration, donnée ou base PostgreSQL réelle touchée. Tests connectés sur bases jetables protégées uniquement. Développement global partiel ; tests ciblés validés, dernière globale échouée ; recette utilisateur à effectuer ; production non validée.

Prochaine action :relancer la consolidation globale après377, puis étendre la recette annuelle intégrée et le rapprochement bancaire des paiements ventilés. Préserver les limites documentaires/réglementaires et les historiques ambigus.

## Session du 11 octobre 2026 — reprise 16h05 UTC — lots 378 à 390

- Consolidation378 : **3241 réussites**, zéro échec/erreur/ignoré, 3877.960s, code0 ; 697 empreintes stables. Elle couvre l'état après377, avant379/381. La preuve échouée373 est conservée. [Rapport378](../../Test/rapport_consolidation_globale_378.md).
- 379 : règlements d'une facture N-1 visibles en N dans le bon cycle ; projection native isolée par société, statut et diagnostics partagés. [Rapport379](../../Test/rapport_reglements_inter_exercices_379.md).
- 380 : variante annuelle ventilations2025, clôture, reports clients/fournisseurs120, compléments2026, validation, lettrage et exports. Avant impôt9écritures/22lignes/D=C2200, AN4180, balance2026 nette4060. [Rapport380](../../Test/rapport_annee_ventilation_380.md).
- 381 : annulation collective native en transaction unique, contrepassations et capturesRAS tracées ; refus/rollback et concurrence testés, quatreEdge. Instrument bancaire unique et rapprochement à une ligne restent à traiter. [Rapport381](../../Test/rapport_annulation_ventilation_381.md).
- 382 : acquisition60000HT/72000TTC et cinq dotations dégressives24000/14400/8640/6480/6480 ;6écritures définitives,D=C132000,VNC0,aucun doublon. [Rapport382](../../Test/rapport_immobilisations_degressif_382.md).
- 383 : mode d'emploiWord/PDFv12,30pages,439blocs,18fiches et17statutsNon testé ; trois variantes chiffrées ajoutées. [Rapport383](../../Test/rapport_guide_ventilation_degressif_383.md).
- 384 : preuve primaire supplémentaire des partsLT, mais consolidation sociale applicable et schémaEDI toujours non qualifiés ; aucun taux/schema installé. [Rapport384](../../Test/rapport_sources_paie_edi_384.md).
- 385 : consolidation des consommateurs règlement/RAS après379/381, avant388 : **228 réussites**, zéro échec/erreur/ignoré, 691.620s, code0 ; 701 empreintes stables. [Rapport385](../../Test/rapport_consolidation_reglements_ras_385.md).
- 388 : preview tardive de l'annulation reproduite et corrigée ; une ancienne réponse après changement d'exercice/cycle/jeton ne peut plus confirmer, poster ou rafraîchir le nouveau contexte. QuatreEdge bureau/mobile et22connexes exécutés. [Rapport388](../../Test/rapport_annulation_contexte_388.md).
- 389 : consolidation après388, avant390 : **232 réussites**, zéro échec/erreur/ignoré, 705.560s, code0 ; 702 empreintes stables. Ces suites connexes ne valent pas une nouvelle globale de tout le dépôt. [Rapport389](../../Test/rapport_consolidation_reglements_contexte_389.md).

- 390 : réponse GET retardée de2026 remplaçant la liste2025 reproduite puis corrigée ; génération, exercice, cycle et jeton vérifiés avant chaque mise à jour. **42tests racine réussis**, zéro échec/erreur/ignoré, 276.989s, puis28connexes(112.397s) sur la garde finale avant invalidation, compilation0 et buildfinal0. [Rapport390](../../Test/rapport_reglements_chargement_390.md).

Les suites se recoupent et ne sont pas additionnées. 70fonctions :15terminé/46partiel/5absent/4bloqué ;73demandes :40terminé/30partiel/2absent/1bloqué. Développement global partiel ; validations automatisées limitées à leurs périmètres ; recette utilisateur à effectuer. **Point6 en attente à la demande de l'utilisateur** : aucune préparation de mise en production engagée. Aucun PostgreSQL réel, donnée comptable réelle, modèle,main ou migration modifié.

Prochaine reprise : nouvelle globale couvrant379/381 et tous modules, puis instrument bancaire unique/rapprochement des paiements ventilés et variantes annuelles restantes. Paie définitive/EDI seulement après qualification des textes/schémas officiels applicables. Attendre le retour utilisateur pour le point6.

## Session du 11 octobre 2026 — reprise 18h12 UTC — lots391 à398

- [Globale391](../../Test/rapport_consolidation_globale_391.md) :3282 réussites et **un échec** de délai de connexion Edge sur3283cas,4251,60s;703empreintes stables. Reprise isolée du fichier :8réussites39,345s sans changement. La preuve globale en échec est conservée; cause du délai non démontrée.
- [Rapprochement392](../../Test/rapport_rapprochement_ventilation_392.md) :une ligne réelle du relevé pour plusieurs lignes bancaires d'une ventilation native immédiate, choix explicite, dépointage atomique, gardesSQL/permissions/concurrence/clôture. Migration084 additive et manuelle; modèles/main et migrations antérieures inchangés. Sans084 les rapprochements simples restent disponibles.
- [Année393](../../Test/rapport_annee_rapprochement_393.md) :facturation→validation→règlement→lettrage→clôture→à-nouveaux;relevé2025 trois opérations pour cinq lignes,solde1000/flux1480;en2026 deux compléments120,solde1000/flux240;comptabilité originale préservée.
- [Guide394](../../Test/rapport_guide_rapprochement_394.md) :Word/PDFv13,31pages,18fiches/17Non testé;annexeExcel3feuilles/8casNon testé. Contrôles techniques des fichiers réussis, MicrosoftWord/Excel non ouverts.
- [Restauration398](../../Test/rapport_sauvegarde_ventilation_398.md) :deuxPGnonce distincts,pg_dump/pg_restore,huit tables comparées,liens et gardes restaurés,rôleLOGIN application et cible non vide vérifiés. Aucun dump livré.
- [Consolidation397](../../Test/rapport_consolidation_bancaire_397.md) :**92réussites**,zéroéchec/erreur/ignoré,298.918s,sources finales figées;compilation et build0. Elle couvre les modules bancaires connexes, l'année et la restauration, et ne constitue pas une nouvelle globale de tous les modules. Les suites se recoupent et ne sont pas additionnées.

Couverture conservée :70fonctions,15terminé/46partiel/5absent/4bloqué;73demandes,40terminé/30partiel/2absent/1bloqué. Le rapprochement à une ligne est désormais disponible pour les ventilations natives immédiates. Instrument unique chèque/effet,escompte/frais,moteur automatique exhaustif et historiques ambigus restent partiels. Paie définitive/EDI toujours bloqués par qualification officielle.

Aucun PostgreSQL réel ni données comptables réelles utilisés. **084 non appliquée sur installation réelle. Point6 en attente utilisateur.** Développement global partiel;tests automatisés validés sur leurs périmètres;globale391 en échec malgré reprise isolée réussie;recette utilisateur à effectuer;mise en production non validée.

Prochaine reprise :nouvelle globale sur les sources après392, surveiller le délai de connexion observé en391,puis variantes annuelles et instruments/frais bancaires restant au périmètre. Ne pas réappliquer392/393/398. Attendre le retour utilisateur pour le point6.

Complément399 :[annulation après rapprochement](../../Test/rapport_annulation_rapprochement_399.md),deux vraisEdge vente bureau/achat mobile réussis en racine. Origines,contrepassations et relevé préservés;dépointage explicite possible,lot annulé non reproposable. Aucun changement produit après397.

Complément400 :[RAS et banque](../../Test/rapport_ras_rapprochement_400.md),deux casAPI/PGnonce vente/achat réussis en racine. Banque210 ventilée90/120,retenue10 indépendante conservée;aucune règle fiscale nouvelle. Code produit inchangé après397.


## Complément401 — protection du numéro technique

[Rapport401](../../Test/rapport_namespace_ventilations_401.md) :saisie manuelle du numéro natif reproduite201 puis refusée422 au POST public;flux natif et numéros commerciaux préservés. 89tests racine réussis,202.546s,zéroéchec/erreur/ignoré;compilation0. Avant correction:2échecs et1réussite,créations201du format technique reproduites. La suite397 précède cette correction du seulcommercial.py;autres sources397 identiques. Historiques non modifiés,aucune migration supplémentaire,statuts de couverture conservés. Nouvelle globale des sources finales restant à exécuter.

## Session du 11 octobre 2026 — reprise 20h09 UTC — lots403 à410

- [Globale403](../../Test/rapport_consolidation_globale_403.md) :3320 tests, 0 échec, 0 erreur, 0 ignoré, 4071.765 s, 713 sources stables. Exécution des sources finales401, avant les nouveautés404/405/406. L’échec historique391 et sa reprise isolée restent conservés dans leur rapport.
- [Frais404](../../Test/rapport_effets_frais_precision_404.md) :six défauts API reproduits puis corrigés ;refus des booléens, fractions de centime et frais ignorés ;calculs Decimal et erreurs lisibles. Encaissement120 = banque109,99 + frais10,01. Aucun changement d’historique.
- [Propositions405](../../Test/rapport_rapprochement_propositions_405.md) :correspondances exactes et uniques, sélection explicite, confirmation atomique, refus d’aperçu obsolète et de doublons. Simple et lot natif immédiat ;gardes de contexte, dates, clôture, permissions et concurrence. Course initiale du chargement société reproduite puis corrigée. Aucune écriture créée par le pointage.
- [Parcours406](../../Test/rapport_encaissement_frais_406.md) :chèque bureau et effet mobile, remise/encaissement, validation du Journal, pointage du net, lettrage et FEC réel. Quatre pièces, dix lignes, D=C480 ;client/attente0, banque109,99, frais10,01. Annulation après cycle bancaire refusée409 sans mutation. Facture initiale préparée viaAPI fictive ;ce cas n’est pas une année complète.
- [Guide407](../../Test/rapport_guide_propositions_frais_407.md) :Word/PDFv14,32pages,18fiches/17Non testé ;nouvelle annexeExcel3feuilles/9Non testé. Contrôles techniques réussis,MicrosoftOffice non ouvert.
- [Consolidation410](../../Test/rapport_consolidation_propositions_frais_410.md) :185 réussis, zéro échec/erreur/ignoré, 456.818 s, sources finales figées et identiques, compilation/build code0. Dix-neuf fichiers couvrant les nouveaux lots, les opérations bancaires existantes, annulation/RAS, sauvegarde/restauration et année2025→2026. Suite connexe distincte de403 ;les résultats ne sont pas additionnés.

Couverture conservée :70fonctions,15terminé/46partiel/5absent/4bloqué ;73demandes,40terminé/30partiel/2absent/1bloqué. Propositions exactes et frais individuels développés/testés ;rapprochement approximatif exhaustif, instruments chèque/effet groupés et escompte restent partiels. Les références du relevé réel ne sont pas supposées égales au Journal. Paie définitive, XML/EDI et qualifications fiscales/documents historiques restent limités ou bloqués selon la matrice.

Développement global partiel ;tests automatisés validés sur les périmètres exécutés ;recette utilisateur à effectuer ;mise en production non validée. Aucun PostgreSQL réel ni données comptables réelles. Aucune nouvelle migration ;084 reste une activation manuelle distincte sur recette isolée. Point6 en attente utilisateur.

Parcours annuel réduit406 également exécuté :2025→2026, résultat89,99 avant impôt de laboratoire3000, perte2910,01 ;clôture etAN2026 validés,quatre lignesD=C3020 ;FEC des deux exercices équilibrés etpointage2025 conservé/verrouillé. Le scénario annuel utilisateur exhaustif reste distinct. Relevés historiques non finis ou non positifs405 :montants et totaux concernés signalés inconnus,pointage interdit,sources conservées ;les correspondances certaines restent confirmables.

Nouvelle globale411 déjà en cours sur les sources finales :3390 cas collectés,721 empreintes figées. Aucun résultat final annoncé. Lire .codex-tests/consolidation411_globale.exit et.xml puis vérifier les empreintes avant toute validation ;ne pas relancer une commande encore active ni modifier les sources pendant l’exécution. La suite connexe410 est réussie et ne remplace pas cette nouvelle preuve exhaustive.

[Recherche ciblée412](../../Test/rapport_source_modification_cnss_412.md) :texte de modificationCNSS non obtenu ;aucune nouvelle qualification réglementaire ni calcul modifié. Limite sociale maintenue,ainsi que la dépendance distincte au schéma officielEDI.

Prochaine reprise :ne pas réappliquer les lots livrés. Vérifier l’achèvement de la globale411 déjà lancée,puis instruire les instruments bancaires groupés,escompte et variantes annuelles exhaustives ;conserver les anomalies FEC/ETIC et ne pas débloquer paie/EDI sans sources officielles qualifiées. Point6 en attente utilisateur.

## État consolidé du14octobre2026 — lots411à432

- Préparation interne annuelle des ventes418/423 : factures et avoirs àleur date, identités figées, CSV/Excel/PDF et refus409des exports obsolètes. Le format fiscal officiel reste àqualifier.
- [Précision428](../../Test/rapport_precision_ventes_428.md) : 32 cas : 32 réussis, 0 échecs, 0 erreurs, 0 ignorés, 202.496s. Suppression du détourfloat dans la seule préparation, en conservant les gardes et le moteur TVA partagé. Grands montants contrôlés sur API/CSV/Excel/PDF. Les centimes déjà perdus au stockageFloat ne sont jamais inventés.
- [Banc dégressif429](../../Test/rapport_degressif_synchronisation_429.md) : 3 cas : 3 réussis, 0 échecs, 0 erreurs, 0 ignorés, 43.712s. Attente des cellules après rafraîchissement, réseau normal et latence contrôlée. Aucun calcul ni montant attendu modifié.
- [Guide424](../../Test/rapport_guide_exports_ventes_424.md) : Word/PDF6pages et Excel3feuilles7cas « Non testé », données exactes270/54/324 et variante370/74/444. Office et recette humaine non exécutés.
- [Globale426](../../Test/rapport_consolidation_globale_426.md) :3422cas,3332réussis,60échecs,30erreurs,0ignoré,729empreintes identiques avant428. XML/log complets,code wrapper non récupéré.72incidents sous-processus Windows0xC0000142,17fermetures du pilote Playwright et1lecture DOM vide. Aucune réussite rétrospective déclarée.
- [Globale430](../../Test/rapport_consolidation_globale_430.md) : 3426 cas : 3426 réussis, 0 échecs, 0 erreurs, 0 ignorés, 6358.352s,code0. Conclusion :réussie sur les sources figées après428/429. Les suites ciblées ne sont pas additionnées àce total.
- [Sources fiscales421](../../Test/rapport_source_cgi2026_421.md) et [sociales427](../../Test/rapport_source_sociale_alternative_427.md) : documents requis non obtenus ; preuves antérieures conservées, aucune règle nouvelle installée.09F/09G restent absentes ;EDI etqualification sociale complète restent ouverts.
- [Source officielle431](../../Test/rapport_source_lf2026_adala_431.md) : copie Adala de la loi50-25 effectivement obtenue,103pages,SHA etlecture des amendements151/157/247/273 contrôlés. Cette preuve supplémentaire ne constitue niCGI consolidé complet ni modèle de déclaration ;aucune règle métier nouvelle codée.
- [Index des recettes432](../recette/INDEX_RECETTES_HISABPRO.md) : guides Word/PDF etannexes accessibles depuis un point d’entrée stable.36liens locaux contrôlés ;cahier218cas208Non testé/10Bloqué,ventes7Non testé. Aucun résultat humain prévalidé,aucun artefact du scénario annuel modifié.

70fonctions :15terminé,47partiel,4absent,4bloqué.73demandes :40terminé,30partiel,2absent,1bloqué. Ces découpages ne sont pas additionnés. Développement global partiel ; tests validés seulement dans leurs périmètres réellement exécutés ; recette utilisateur àeffectuer ; production non validée. Point6en attente utilisateur. Aucune base réelle ni donnée réelle,main,models,schemas ouSQL modifié.

Prochaine action :Compléter la recette d’installation vierge au-delàdu manifeste082avec083_ras_reglements.sql puis084_rapprochement_ventilations.sql, dans l’ordre de leurs prérequis048/083 ;tester les droits applicatifs etla restauration sur cible jetable. Préserver le banc historique082. Les annexes tiers/TP exigent encore le modèle etle référentiel applicables ;aucun EDI inventé.

## Point du 15 octobre 2026 — lots 433 à 438

L’installation isolée est maintenant prouvée jusqu’à 084 : 75 SQL distincts,
11 rejeux et 25 tables métier vides. La restauration consolidée compare 73 tables
et leurs objets de schéma ; elle ne restitue pas automatiquement les rôles/ACL.
Les droits 085/086 sont testés séparément par les parcours commerciaux réels.
Les CSV partagés ont été corrigés sans modifier les sources ; les avoirs sont
sérialisés pour empêcher doubles pièces et annulation d’un crédit consommé.

Les suites connexes 433/434/435/436/437/438 passent respectivement 8/11/68/73/49/57
tests, sans échec, erreur ou ignoré. Elles se recouvrent etne sont pas additionnées.
La globale 430 reste une preuve historique antérieure à ces modifications.

70 fonctions : 15 terminé, 47 partiel, 4 absent, 4 bloqué. Checklist 73 inchangée.
Développement global partiel ; tests validés dans les périmètres exécutés ;
recette utilisateur à effectuer ; production non validée. Aucun PostgreSQL réel.
085/086 restent manuelles et les anciennes migrations n’ont pas été modifiées.
Point 6 toujours en attente utilisateur ; paie définitive, EDI et annexes officielles
conservent leurs limites de sources et de qualification.

Prochaine action : vérifier les droits du rôle applicatif pour comptes bancaires,
relevés et rapprochement, puis poursuivre les autres droits runtime encore manquants.
Voir le [rapport de session](RAPPORT_SESSION_20261015.md) pour les ZIPs etpreuves.

## Point final du 15 octobre — lots 441 à 448

Les nouvelles preuves couvrent les droits bancaires 087, les vrais parcours Edge sous
LOGIN SQL, la clôture et le lettrage natif 088/089, le FEC stable et la restauration
des ACL, le multi-société 090 puis la lecture/affectation du résultat 091.
La dernière recette regroupe les modules sur une même application complète ;
les oracles sont inchangés et les écritures définitives restent intactes.

Statuts fonctionnels conservés : **70 fonctions, 15 terminé/47 partiel/4 absent/4 bloqué**.
Checklist distincte inchangée :73 demandes, 40 terminé/30 partiel/2 absent/1 bloqué.
Les suites se recouvrent et ne s'additionnent pas. La globale 430 reste historique.
Les 115 fichiers guides/recettes sont conservés ;aucun statut de recette humaine
n'est changé. Aucun PostgreSQL réel ni pièce comptable réelle utilisé.

Développement global partiel ;tests automatisés validés dans leurs périmètres ;
recette utilisateur à effectuer ;mise en production non validée. Point 6 en attente.
La paie définitive, les modèles officiels d'annexes et le schémaEDI restent soumis
aux sources et validations déjà documentées. Aucun EDI ou justificatif inventé.
Prochaine tâche :pièces justificatives et modèles d'écritures sous LOGIN SQL,
puis variantes annuelles restantes ;préserver les historiques FEC/ETIC ambigus.

## Reprise 451–459 du 15 octobre 2026

Les [61 cas regroupés](../../Test/rapport_consolidation_reprise_459.md) vérifient
les sources finales, droits et invariants en isolement. Ils ne s’ajoutent pas aux
comptes des suites recouvrantes. Les 70 statuts restent inchangés : 15 terminé,
47 partiel, 4 absent, 4 bloqué. Aucun cas humain, guide ou résultat Excel prévalidé.
Les corrections ne demandent aucun nouveau SQL. Les variantes restantes,
modèles complexes et textes officiels manquants restent à traiter ; point 6 en attente.

## Reprise hors RH/paie553–567 — 18octobre2026

CPT11 terminé dans son périmètre de réouverture administrative ; FIS02
partiel avec assistant de simulation seulement. Raccordement ventes/Journal
qualifié561. Chaîne098 qualifiée563 en bac vierge, puis restauration
froide des nouvelles lectures : [567](../../Test/rapport_restauration_ventes_ras_567.md),
1test71,99s,74tables et ACL/séquences/source préservées.
Statuts actuels16terminé/47partiel/3absent/4bloqué ; production et recette
utilisateur non validées. RH/paie restent différées jusqu’aux priorités hors RH.

## Raccordement RAS TVA571

Capture declarative liee au calcul559 et dossier immuable099 :76tests de livraison reussis. FIS02 reste partiel : compte explicite, qualification sur pieces, pas de reversement ou declaration complete. Le soldeTVA automatique des periodes et reports touches est explicitement indisponible pour eviter un calcul sur le seul cash. Interface573 a suivre. Aucun statut global transforme en termine.

## Interface et guide RAS TVA573

Mode guide dans les reglements, dossier consultable et soldes rafraichis.107tests regroupes reussis,1Edge sans099 et build reussi. Entiers et anciennes representations monetaires geres sans reecriture ; aucune declaration TVA inconnue affichee comme zero. GuidePDF/MD fourni. Statuts globaux16/47/3/4 inchanges ; installation/restauration099 a qualifier.

## Qualification099575

Installation1test33.15s et restauration finale1test79.00s reussies sur clusters nonce.90SQL distincts/26rejeux/116executions ;75tables restaurees, dossiers actif/annule et gardeTVA conserves, source preservee et cibles supprimees. Aucune qualification de production ou recette humaine. Statuts globaux inchanges.

## Registre des retenues TVA579

FIS02 reste partiel : registre interne annuel des captures guidées, achats et
ventes séparés, annulations et OD visibles, CSV/Excel/PDF avec logo sur les
documents compatibles.13 tests API/Edge/exports réussis,2 Edge sans099 et build
réussi. Lecture cohérente sous concurrence, sources modifiées imposant une
actualisation, montants exacts et PDF multipage vérifiés. Aucun crédit fiscal,
reversement ou dépôt officiel déduit. Statuts16/47/3/4 inchangés ; guide et
[rapport](../../Test/rapport_registre_ras_tva_579.md) disponibles.

## Consolidation et restauration581

130tests connexes réussis sur le banc099, puis1 restauration native réussie
en76,65s :75tables/ACL/séquences et registre JSON/CSV/textePDF/valeursExcel/logo
conservés sans mutation. Voir [581](../../Test/rapport_qualification_ras_tva_581.md).
Les2Edge sans099 et le build579 sont des contrôles distincts réussis.
Statuts16/47/3/4 inchangés ; aucune recette humaine ou production déclarée validée.

## Cockpit fiscal583

Accès au même registre annuel depuis la Liasse, avec séparation explicite des
tableauxT1–T25 et de l'archive.6Edge réussis sur sources finales,64,99s,
trois rôles, changements d'année/société et navigation Bilan/CPC/ETIC conservée.
Build et guidePDF2pages vérifiés ; [rapport](../../Test/rapport_cockpit_ras_tva_583.md).
Aucun calcul, droit ou SQL ajouté ; statuts globaux inchangés.

## Traçabilité et qualification finale585

Empreinte des données conservée dans CSV/Excel/PDF.137tests regroupés réussis
sur les sources finales,320,10s, puis1restauration native réussie,84,49s,
avec JSON/CSV/textePDF/valeursExcel/logo identiques. Aucune signature officielle
ou imputation fiscale déduite. [Rapport585](../../Test/rapport_empreinte_ras_tva_585.md).
Statuts16/47/3/4 et recette humaine en attente conservés.

## Cohérence intermodules587

Deux parcours supplémentaires vente/achat réussis,40,63s : paiements525+525,
captures75+75, validation, vrai lettrage5lignes/codeAAA dans Edge et annulation.
Bilans équilibrés, CPC et calculs/acomptes/créditsIS inchangés par les captures,
sources originales préservées ; [rapport587](../../Test/rapport_coherence_ras_tva_587.md).
Pas de nouvelle règle fiscale ou comptable ; statuts globaux inchangés.

## Livraison589 et exercice décalé

Le registre reste civil : choix explicite de l'année depuis un exercice qui
chevauche deux années, note commune dans l'interface/exports.139tests réussis
dans la consolidation589 ; son seul échec de préparation (année de clôture
du nouveau cas) a été corrigé puis le cas a réussi séparément,38,66s.
Pas de relance globale après ce correctif de fixture. Restauration finale
1réussie79,56s, build10,44s, compilation28Python et guidePDF2pages vérifiés.
Voir le [rapport589](../../Test/rapport_livraison_session_589.md). Statuts inchangés.


## Préparation mensuelle593

FIS-02 reste partiel. Préparation des retenues opérées par mois de versement
prévu, paiements du mois précédent, achats seuls, annulations courantes séparées,
CSV/Excel/PDF avec logo et empreinte, droits de consultation. Recalcul TVA sans
perte du panneau et libellé du crédit lié à l'année civile sélectionnée.
**158 tests regroupés réussis en 347.43s**, absence099 et restauration native
testées à part. [Rapport593](../../Test/rapport_preparation_ras_tva_593.md).
Aucun reversement effectif, crédit fiscal, bordereau officiel ou recette humaine
déduit. Les statuts globaux restent inchangés.


## Calcul documentaire595

CPT-09 reste partiel. Calcul facultatif CCA/PCA en jours calendaires inclusifs,
montant et période déclarés, calendrier réel, source unique Decimal, PDF/logo/
empreinte et reprise explicite dans le formulaire ordinaire. Droits, péremption,
CPC/bilan et sources définitives conservées dans Edge.103tests regroupés réussis
182,63s, restauration native1réussie108,33s, build4,93s. [Rapport595](../../Test/rapport_calcul_documentaire_595.md).
Aucune TVA/déductibilité déduite, ni archivage automatique. Les provisions et
leurs reprises spécialisées restent à traiter. Statuts globaux inchangés.


## Annexe de recette597

24cas humains Non testé, PDF29pages, Excel de suivi et JSON de données fixes.
Oracle indépendant : Journal166000 équilibré, CCA/PCA5934,07 reportés.
4contrôles documentaires réussis. Deux limites non exécutables distinctes ;
statuts fonctionnels globaux inchangés. Recette utilisateur et recalcul Excel
interactif restent à effectuer. RH/paie différées. Suite : clôture connectée.


## Clôture connectée599

2parcours Edge/PG natif réussis45,943s : CCA/PCA, clôture2025 avec CM du
profil technique explicite, AN2026 et contrepassations validées. FEC deux
années exportés, états équilibrés, sources définitives conservées.
CPT-09 reste partiel : provisions/reprises spécialisées encore ouvertes.
Suite : visibilité des contrepassations dans leur exercice de destination.
Recette humaine/production non validées ; RH/paie différées.


## Contrepassations d’ouverture601

Contrepassations liées visibles dans leur exercice réel de destination,
source/date/statuts/debit-credit exacts, lecteur autorisé sans mutation,
pagination20 et Journal ordinaire.57tests natifs222,241s +55purs2,306s,
restauration1réussie80,754s75tables, build10,78s. [Rapport601](../../Test/rapport_contrepassations601.md).
CPT-09 reste partiel ; aucune reprise de provision présumée. Suite : corriger
les comptes proposés/acceptés pour les dépréciations stock/client ; anciennes
écritures conservées. Recette humaine et production non validées, RH/paie différées.


## Comptes de provision603

Croisements de comptes empêchés : stock391, client3942, risques15ou45,
subdivisions conservées. Suggestions issues du même référentiel serveur que
la validation ; champs accessibles Type/Comptes corrigés.70tests natifs
256,618s +74purs2,165s +5historiques0,279s réussis ; build5,14s.
[Rapport603](../../Test/rapport_provisions603.md), [sources](SOURCES_PROVISIONS_20261019.md).
Aucune pièce historique ni migration modifiée, aucune déductibilité ou reprise
déduite. CPT-09 demeure partiel. Suite : parcours de clôture CCA/PCA décalés.


## Clôtures décalées605

2Edge/PG natifs réussis44,120s : CCA/PCA au30juin, calcul6032,79, AN/CP
au1juillet2025 dans exercice2026, FEC deux années, états/sources cohérents.
Restauration civile distincte1réussie71,261s : dossier clos, CP validée,
FEC2025 identique en octets, suivi/états identiques,75tables et source
préservée/cibles nettoyées. [Rapport605](../../Test/rapport_cloture_decalee605.md).
CPT-09 reste partiel ; recette humaine et production non validées. Suite :
compléter annexe humaine avec suivi601/contrôle603/parcours605, Non testé.


## Annexe humaine607

Annexe étendue à30cas Non testé, PDF35pages, Excel/JSON, six sociétés
fictives et oracle indépendant civil/décalé. Suivi601, contrôles603 et
clôtures599/605 documentés ; deux limites non exécutables séparées.
4contrôles de livrable réussis, PDF inspecté. Excel interactif et recette
humaine non exécutés ; statuts fonctionnels inchangés.
[Rapport607](../../Test/rapport_annexe_suivi607.md). Suite : vérifier le cumul
et les empreintes de session ; reprises/fiscalité/production restent partielles.


## Suppression inventaire613

Journal ne supprime plus isolément une AD/CP brouillon liée à un ajustement :
409 lisible et suppression cohérente depuis Clôture conservée. Deux défauts
204 reproduits avant correction ;39tests natifs connexes et2ciblés renforcés
réussis, sans échec/ignoré. Suppression manuelle ordinaire204 conservée.
[Rapport613](../../Test/rapport_suppression_inventaire613.md). Aucune ancienne
pièce réparée/migration modifiée ; validation visuelle utilisateur à effectuer.
Suite : conception611 pour reprises partielles ; RH/paie toujours différées.


## Reprises partielles de provisions615

Registre immuable100 et panneau Clôture : dotation validée liée, montants exacts,
aperçu sans mutation, brouillons réservés, idempotence/concurrence, annulation
par inverse et protections du Journal. Capacité calculée selon les dates, en
réservant les reprises futures ; sources historiques incohérentes signalées
sans empêcher les autres.139cas regroupés réussis, puis5contrôles de compatibilité
(avec recouvrement), restauration native77tables et build réussis.
[Rapport615](../../Test/rapport_reprises615.md),
[manuel](../REPRISES_PROVISIONS_615.md). Migration100 non déployée sur la base
utilisateur. Aucun montant/risque/droit fiscal inventé. CPT-09 demeure partiel
pour les dossiers manuels historiques et natures non qualifiées ; recette
humaine/production non validées. RH/paie toujours différées. Suite : exports
du suivi avec identité/logo puis annexe de recette Word/PDF/Excel dédiée.


## Exports du suivi de provisions617

PDF/Excel internes avec identité/logo, originaux/inverses, montants exacts,
statuts et diagnostics. SnapshotRO/RR et SHA avant téléchargement, validation/
annulation/identité/logo/compte modifiés refusés409, contexte tardif écarté.
15API/Edge/concurrence et40connexes (avec recouvrement) réussis ; restauration
native77tables, données/texte-imagesPDF/cellules-types-imagesExcel identiques,
source préservée et cibles nettoyées ; build5,00s.
[Rapport617](../../Test/rapport_exports_reprises617.md).
Aucune nouvelle règle fiscale, migration ou donnée réelle ; CPT-09 reste
partiel pour les historiques manuels et natures non qualifiées. Excel interactif,
recette humaine et production non validés. Suite : cahier Word/PDF/Excel dédié.


## Cahier complémentaire des reprises619

Word, PDF25pages, Excel/JSON :20cas humains Non testé,2limites non exécutables
séparées, trois sociétés fictives. Oracle en centimes indépendant : capital20000,
dotation1000, reprises400+200 et inverse400 ;5pièces/10lignes22000, résultat−800,
provision800, disponible800, bilan20000. Deux vrais parcours Edge1440/390 et
4contrôles documentaires réussis, puis4contrôles après précision des libellés.
[Rapport619](../../Test/rapport_annexe_reprises619.md).
FEC exporté/sommé, source définitive intacte et suivi PDF téléchargé. Statuts
fonctionnels globaux inchangés ; aucune recette humaine, conformité fiscale ou
production prétendue validée. Word/Excel interactifs restent à ouvrir par le
partenaire. Suite : non-régression des autres modules avec SQL100 actif.


## Non-régression intermodules621

35cas existants regroupés sous SQL100 avec registre témoin non vide, réussis
sans échec/ignoré : vente/achat, validation/règlements/lettrage Edge, RAS, année
connectée stock/TVA/immo/clôture/AN et clôtures décalées. Source définitive et
reprise témoin inchangées. [Rapport621](../../Test/rapport_intermodules621.md).
Pas35nouvelles fonctions ni recette humaine ; statuts globaux inchangés.
Suite : chaîne d’installation vierge100 et rejeu, exclusivement sur nonce.


## Installation vierge100 —623

Chaîne100 autonome sans URL externe :91SQL distincts,27rejeux,118exécutions,
77tables ;75anciennes préservées, deux registres vides,9triggers actifs.
Schéma/données/ACL/séquences identiques au rejeu ; LOGIN limité etPUBLIC contrôlés,
cluster supprimé.2tests CLI réussis, aucune base utilisateur ni ancien SQL
modifié. [Rapport100](../../Test/rapport_installation_vierge_100.md).
Premier échec d’import du banc corrigé avant relance ; pas une erreur de
migration métier. Installation réelle/production restent non qualifiées.
Suite : suivi des reprises sur exercices décalés et annulation interexercices.


## Reprises sur exercices décalés625

Date civile/exercice de reprise et d’inverse explicités dans suivi/PDF et
colonnesExcelN/O, sans déplacement des13colonnes existantes. Source2025close,
reprise2026au01/07/2025, seconde clôture après confirmation réelle d’un déficit,
inverse2027au01/07/2026.55cas réussis puis2parcours renforcés (recouvrement),
restauration77tables : suivis/SHA/CPC/bilans/FEC trois années identiques ;
capital/source/reprise et état fiscal antérieur inchangés. Build5,70s.
[Rapport625](../../Test/rapport_reprises_decalees625.md). Aucun nouveau calcul
fiscal ou SQL ; hypothèse de déficit du laboratoire seulement, pas déductibilité
réelle qualifiée. Statuts humains et production restent non validés, RH/paie
différées. Suite : index de recette actualisé et vérification finale du cumul.


## Index de recette627

Le README pointe vers un guide partenaire avec les Word/PDF/Excel et données
actuels, sociétés fictives séparées, installation100, preuves et limites.
31liens locaux de l’index et11duREADME contrôlés ;20cas619 et30cas607 toujours
Non testé, anciens cahiers/fichiers de résultats conservés.
[Rapport627](../../Test/rapport_index_recette627.md). Aucun code ou statut
fonctionnel changé ; recette humaine et production restent à effectuer.
Suite : derniers contrôles des générateurs comptables avec100 actif et cumul.


## Générateurs comptables629

109cas existants regroupés sous100 avec registre témoin non vide, tous réussis
en137,236s : immo/stock, règlements par tiers, rapprochement/annulation ventilés,
finalisation concurrente, acomptes clients/fournisseurs et Edge. Suivi/source/
reprise témoin inchangés ; aucun correctif métier nécessaire pour ces cas.
[Rapport629](../../Test/rapport_generateurs629.md). Aucun test ignoré ; ce sont
des non-régressions, pas109nouvelles fonctions. Statuts globaux inchangés,
installation réelle100, recette humaine et production restent non qualifiées.
Suite : vérifier tous les ZIPs et le différentiel source, rapport/cumul final.


## Bilan final615–631

[Rapport de session actuel](RAPPORT_SESSION_20261019_615_631.md) : reprises
liées, annulation datée, réservations, exports avec logo, exercices décalés,
installation100 et restauration77tables. Word/PDF/Excel619 et index partenaire
disponibles ;20nouveaux cas humains restent Non testé. 109non-régressions629
et14tests du vérificateur631 réussis, sans sommer les suites recouvrantes.
15anciens ZIPs intacts, différentiels source couverts, aucun ancien SQL/main/
models/schemas modifié. Cumul final54fichiers, tous vérifiés par manifeste.
Matrice70lignes inchangée :16terminé/47partiel/3absent/4bloqué. Migration100
non déployée sur la base utilisateur, recette humaine et production non validées.
Suite indépendante : factures correspondantes entre sociétés explicitement
liées, droits doubles, paramétrage et prévention des doublons ; ce pont reste
absent. RAS/déclarations/annexes/EDI restent tributaires de leurs preuves.
RH/paie et point6 humains toujours différés.


## Sociétés liées633

Association commerciale déclarée vendeur/acheteur et tiers explicites, droits
administrateur dans les deux sociétés relus, retrait motivé unilatéral et
historique immuable101. Paramètres → Sociétés liées ; consultation seule sans
formulaire. Aucun groupe fiscal présumé, facture ou écriture créée.
Baseline multi-societes7passes104.423s ; suite63312passes41.222s, 0echec/erreur/ignore ; build final OK ; Python compile. API/LOGIN nonce/Edge1440 et390 et lecteur, registres et ACL preserves au rejeu non vide.
[Rapport633](../../Test/rapport_societes_liees633.md),
[mode d’emploi](../SOCIETES_LIEES_633.md). ADM-02 reste partiel : le pont de
facturation635 reste à réaliser. 101 non déployée sur la base utilisateur,
recette humaine/production non validées ; RH/paie et point6 humains différés.


## Factures correspondantes635

Liaison633 → vente validée → aperçu et brouillon d'achat102 atomique, articles
de l'acheteur explicitement choisis, référence vendeur conservée, droits doubles,
unicité/idempotence, frais/échéances et calendrier réel. UI dans le détail de
facture ; deux Journaux via commandes ordinaires, aucun définitif automatique.
Écarts de brouillon, TVA inconnue, avoir/annulation signalés sans synchronisation
silencieuse ; source conservée. Sens inverse déclaré et logos PDF propres aux
deux sociétés testés. 24cas finaux passes91.164s ;82connexes sous102 passes165.577s ;2Edge ancien socle passes33.288s ;restore80tables1passe52.547s ;buildVite5.02s, Python compile. Zero echec/erreur/ignore final, sources et temoin non vide inchanges. Suites recouvrantes non additionnees.
[Rapport635](../../Test/rapport_factures_liees635.md),
[mode d’emploi](../FACTURES_CORRESPONDANTES_635.md). ADM-02 reste partiel pour
les autres intégrations de groupe ; paiements/avoirs/livraisons non répliqués,
pas de consolidation fiscale. Installation réelle101/102, recette humaine et
production non validées. RH/paie et point6 humains différés.


## Installation vierge102 —637

CLI102 autonome qui étend100 sans modifier les anciens scripts, refuse toute
URL externe et ne migre jamais la base active. 2tests CLI passes24.757s code0 ;93SQL distincts/29rejeux/122executions,80tables,77anterieures preservees ;43tablesmetier vides, schema/donnees/ACL/sequences identiques au rejeu ;LOGIN limite/PUBLIC/sequences/9triggers verifies, cluster supprime. URL externe refusee avant cluster.
[Rapport102](../../Test/rapport_installation_vierge_102.md). Installation cible,
recette humaine et production restent non qualifiées ; aucun PostgreSQL réel.
Suite : cahier Word/PDF/Excel et oracle indépendant des sociétés liées.


## Aide de numérotation638

Paramètres décrit maintenant le numéro attribué à la validation, sans prétendre
qu’il est librement modifiable. Aucun calcul ou numéro changé. Build Vite 4.99s reussi ; texte obsolete absent, nouveau texte present. Pas de nouveau test metier pour cette clarification de texte.
[Rapport638](../../Test/rapport_numerotation_factures638.md). Statuts globaux inchangés.


## Cahier partenaire639

Word/PDF24pages/Excel et JSON pour633/635,20cas humains Non testé, deux
limites non exécutables séparées. Capitaux10000 chacun, vente/achat500HT+100TVA,
deux règlements600, lettrages séparés. 5cas documentaires/oracle API passes24.983s, puis4documentaires finaux passes0.808s ; PDF24pages, XMLWord et Excel/formules/statuts valides, liens verifies {'docs/recette/README.md': 17, 'docs/recette/PAR_OU_COMMENCER_20261019.md': 43}.20cas humains Non teste,2limites separees. Oracle natif11200D=C par societe,6pieces/14lignes ; banques10600/9400, resultats500/-500, bilans10600/9500, lettrages sans modification des definitifs.
[Rapport639](../../Test/rapport_annexe_societes639.md),
[index partenaire](../recette/PAR_OU_COMMENCER_20261019.md).
Couverture globale inchangée ; aucune déclaration ou consolidation fiscale,
recette humaine, ouverture interactive Word/Excel ou production validée.
RH/paie et point6 humains différés. Suite : audit final des sources/livraisons,
rapport et cumul, puis travaux horsRH restants selon matrice.


## Point ciblé151 —640

[Sources et limites151](SOURCES_ANNEXE151_20261019.md) : CGI2026TGR relu sur
les paragraphes concernés ; imprimé MEF ADC120F-12I écarté car article154, pas151.
Modèle151 applicable non obtenu, absence non déduite d'un timeout. Aucun
formulaire/taux/règle fiscale ajouté ni ancien audit comptable recommencé.
Poursuite indépendante : suivi regroupé des factures correspondantes633/635.


## Suivi regroupé641

Paramètres → Sociétés liées → Factures de la liaison : pagination10, états,
exercices et situations monétaires distinctes, encaissements/en cours et
imputations existantes. RO/RR avant auth sur une connexion, lecteurs et sociétés
contrôlés ; réponse tardive après changement de jeton écartée, retrait relu sansF5.
Un solde couvert ne prouve pas l'encaissement ; non fini/sous-centime indéterminé,
jamais faux zéro. Calendrier acheteur explicité et sélecteur global accessible.
29regroupes passes152.412s ;15precision/suivi/oracle/docs passes68.734s ;4Edge calendrier finaux passes45.709s dont achat2027date2026 ;restore80tables1passe63.934s, vue regroupee identique. BuildVite5.22s, Python compile. Zero echec/erreur/ignore final ; suites recouvrantes non additionnees.
[Rapport641](../../Test/rapport_suivi_correspondances641.md), guide et20cas humains
actualisés sans prévalidation. Aucun nouveau SQL. Limite révélée : API individuelle
acceptait0,005MAD, àcorriger en642 ; historiques restent signalés sans réécriture.
Installation101/102, recette humaine et production non validées ; RH/paie différées.


## Règlements au centime642

Anomalie révélée641 reproduite en PostgreSQL natif isolé : l'API acceptait0,005
MAD, enregistré0,005 contre0,01 dans les lignes du Journal. Validateur partagé
corrigé avant mutation, sans arrondi implicite ni réécriture historique.
Seul le bruit de représentation binaire des doubles est toléré (4ULP, plafond
1e-8MAD). Création et modification refusent les vrais sous-centimes ; note seule
préservée. Ancien montant inconnu signalé dans le suivi, jamais faux zéro.
35 tests precision/API/suivi/oracle passes en102.535s ;82 non-regressions connexes passees en164.890s, zero echec/erreur/ignore. Preuve635 preservee, temoin non vide inchange. Suites recouvrantes non additionnees. Python compile ; aucun frontend modifie depuis build6415.22s.
[Rapport642](../../Test/rapport_reglements_centimes642.md). Aucun nouveau SQL.
Installation101/102, recette utilisateur et production restent à qualifier ;
RH/paie et point6 différés. Les limites fiscales non documentées officiellement
restent visibles et n'ont pas été contournées.


## Bilan final633–643

[Rapport actuel de session](RAPPORT_SESSION_20261019_633_643.md) : sociétés
liées, achat correspondant à la vente, deux Journaux/règlements/lettrages,
suivi regroupé avec lecture cohérente et calendrier acheteur, sous-centimes
refusés à la source. Word/PDF/Excel639 et20cas humains Non testé disponibles.
35tests finaux642 et82connexes réussis,14tests du vérificateur643 réussis ;
campagnes recouvrantes non additionnées. Restauration64180tables et installation
vierge102 qualifiées en laboratoire. Build6415,22s ;22Python livrés compilés.
32archives antérieures intègres,1532sources initiales comparées ;15modifiés et
39ajouts avant bilan couverts par cumul642.103sources protégées intactes,
aucun fichier initial supprimé. Cumul final55fichiers et ZIP643 vérifiés.
Matrice70lignes inchangée :16terminé/47partiel/3absent/4bloqué. Serveur réel6028
intact, aucun Python de test ni cluster supplémentaire actif. Installation101/102
sur cible, recette humaine et production non validées. Annexes/EDI et
déclaration/imputation/reversement RAS gardent leurs limites documentées.
Prochaine reprise : journal/processus/archives puis lot RAS indépendant,
sans recréer capture083/099 ou préparation593 ; vérifier sources officielles
avant toute nouvelle règle. RH/paie et point6 humains restent différés.


## Pièces jointes et contexte645

Composant partagé sécurisé avant raccordement RAS : liste refusée signalée,
aucun faux vide ; réponses tardives et téléchargement écartés après changement
de document/jeton/démontage. Envoi/suppression et callbacks gardés, actualisation
sansF5. Droits, endpoints et SQL inchangés. Ancien composant retrouvé avec SHA
exact : trois défauts de liste reproduits, puis vrai téléchargement tardif
reproduit après renforcement de l'observation du banc. Ancien test de concurrence
451 actualisé pour observer le PID bloqueur plutôt que supposer UPDATE ;
assertions validation200/suppression409 et conservation de la pièce maintenues.
Campagne finale : 23tests réussis en248.953s, zéro échec/erreur/ignoré ; concurrence ciblée1réussie en51.059s ; restauration73tables et pièces réussie, schéma/données/ACL/séquences identiques, cibles supprimées et preuve452 conservée. Build Vite6,91s, Python compilé. Suites recouvrantes non additionnées.
[Rapport645](../../Test/rapport_pieces_contexte645.md). Reprise21tests642 réussis,
cumul643 vérifié à l'identique sans réapplication. Prochain lot : documents liés
aux OD de capture/annulation RAS et exports descriptifs, sans qualification
fiscale ou preuve de versement présumée. RH/paie et point6 humains différés.


## Documents RAS647

Registre annuel et préparation mensuelle : consultation et ajout des documents
du Journal sur les vraies OD de capture/contrepassation, rôles et sociétés
contrôlés, actualisation du panneau sansF5. Métadonnées groupées dans le même
snapshotRO/RR, empreinte périmée refusée après ajout documentaire. CSV/Excel/PDF
reprennent les références en section séparée, avec logos dans Excel/PDF.
Aucune donnée comptable ou dossier099 réécrit ; fichiers originaux non modifiés.
Une présence documentaire ne qualifie ni attestation, ni versement, ni crédit.
L'empreinte des métadonnées ne signe pas les octets des fichiers.
Baseline existante12réussis en85.865s ;5API nouveaux réussis en48.561s ;29connectés/format finaux réussis en201.393s, dont4Edge nouveaux et100références multipages ;2restaurations réussies en129.082s (socle73tables/4fichiers et10280tables/7fichiers). Zéro échec/erreur/ignoré final. Build12,49s, Python compilé. Campagnes recouvrantes non additionnées.
[Rapport647](../../Test/rapport_ras_documents647.md), [mode d'emploi](../RAS_DOCUMENTS_647.md).
Socle de restauration étendu avec trois fichiers explicitement attendus et SHA,
sans filtrage du manifeste ; preuve452 historique conservée. Aucun nouveau SQL.
Déclaration complète, imputation et reversement restent ouverts ; modèles
officiels151/EDI non inventés. Prochaine étape : annexe de recette humaine et
oracle chiffré sans prévalidation, puis consolidation et cumul645+. RH/paie et
point6 humains toujours différés.


## Cahier des documents RAS649

Annexe Word/PDF/Excel, données et PDF fictif à joindre disponibles depuis
[l'index de recette](../recette/PAR_OU_COMMENCER_20261019.md).12cas humains
Non testé, résultats réels/anomalies/preuves vierges ; limites séparées.
Oracle entier indépendant : capital10000, achat1200, cash525/RAS75 puis
annulation ;4pièces/9lignes D=C11800 deviennent6pièces/13lignes D=C12400.
Banques9475→10000, bilans9675→10200, résultat−1000 ; fichiers/références
créent0mouvement. Le compte4457 est choisi pour le laboratoire, pas imposé.
Oracle API102 réussi1cas en24.133s : toutes lignes/Journal/FEC/bilan/CPC avant et après annulation conformes. Contrôles documentaires finaux4réussis en0.808s, zéro échec/erreur/ignoré. Word OOXML valide et tableau lisible, PDF16pages examiné, Excel8feuilles/12cas humains Non testé/formules et preuves vierges, PDF fictif1page. Python compilé ; aucun produit modifié, build64712,49s conservé.
[Rapport649](../../Test/rapport_annexe_ras_documents649.md).
Aucune règle fiscale nouvelle, mutation réelle ou application changée.
Déclaration/imputation/reversement et modèles administratifs restent partiels.
Prochaine étape : consolidation RAS/facturation/états sur102 avec témoins
documentaires non vides préservés, puis rapport/cumul final. RH/paie et point6
humains différés ; Word/Excel interactifs et production non validés.


## Consolidation651 et réserve du scénario649

218cas distincts réussis en453.945s, zéro échec/erreur/ignoré. Schéma102 natif, LOGIN limité, témoins commerciaux/RAS et deux fichiers inchangés ;379sources applicatives SHA inchangés. Python compilé. Aucun produit modifié ; campagnes recouvrantes non additionnées.
[Rapport651](../../Test/rapport_consolidation_ras_documents651.md).
Sélection ciblée RAS/facturation/états/lettrage/documents, pas suite globale.
Première erreur de setup d'ordre SQL du banc conservée, corrigée sans produit.
Recherche officielle parallèle : le cahier649 à1200TTC d'une société vierge
ne documente pas l'absence d'exclusion petites prestations ; ses calculs
réussis ne qualifient pas fiscalement cette hypothèse. Révision653 requise
avant recette principale : montants relevés et oracle/documents/tests refaits,
aucun cumul mensuel inventé. Anciens ZIPs conservés intacts.
Déclaration/imputation/reversement, modèle151/EDI et recette humaine restent
non validés. RH/paie et point6 différés ; prochaine action653 puis bilan655.


## Scénario de recette révisé653

Réserve651 traitée : le jeu principal649 (société vierge/1200TTC) supposait
l'absence d'exclusion sans autre fait de cumul. Révision2 à12000TTC et quote6000,
sans cumul mensuel inventé ; profil fiscal déclaré du laboratoire toujours
distinct d'une qualification réelle. Montants et oracle indépendants ×10,
compte4457 choisi pour le jeu et non imposé. Anciens ZIPs intacts, nouveaux
Word/PDF/Excel/JSON et index remplacent le scénario principal ;12statuts humains
restent Non testé et preuves vierges. Contrôle visuel a corrigé des consignes
restées aux anciens montants malgré oracle correct ; elles sont maintenant
confrontées aux lignes D/C de l'oracle dans un test dédié.
7cas ciblés réussis en26.010s, zéro échec/erreur/ignoré : six contrôles documentaires/données/consignes et oracle natif102 avec Journal/FEC/bilan/CPC et originaux. Word/PDF16pages/Excel8feuilles révisés,12cas humains Non testé. Données12000TTC/quote6000/cash5250/RAS750/capital100000 vérifiées ; pourcentages, dates et0,005 conservés. Python compilé. Aucun produit ni SQL modifié ;218tests651 antérieurs non requalifiés en exécution653.
[Rapport653](../../Test/rapport_coherence_scenario653.md), [sources et limites](SOURCES_SCENARIO_RAS_20261019_653.md).
NC735 et BO7465bis lus par passages indexés officiels ; PDFCGI2026 actuellement
inaccessibles, aucune lecture intégrale revendiquée. Modèles/cahiers des charges
SIMPL-TVA à obtenir ; aucune déclaration ou règle applicative inventée.
Suite : audit final des sources/archives/journal, vérificateur ZIP et cumul655.
RH/paie et point6 humains différés ; recette utilisateur/production non validées.


## Annulation individuelle datee655

API existante exposee dans le formulaire commercial : date modifiable et motif facultatif, erreurs conservees, verrou de soumission et contexte. Apres succes, listes reglements/factures rechargees. Aucun backend ni SQL modifie. 9tests Edge/API/PostgreSQL isole reussis123.11s, puis2cibles apres correction couleur34.53s; zero echec/erreur/ignore. Builds4.97s et6.20s,exit0. Compilation des3tests Python livres. Campagnes recouvrantes non additionnees.
[Rapport655](../../Test/rapport_annulation_date655.md), [mode emploi](../ANNULATION_REGLEMENT_655.md). Achat12000/cash5250/RAS750 : refus futur sans mutation puis contrepassations datees et motivees, originaux intacts. RDO-008 devient executable avec ses champs;12cas humains restent Non teste. Annulation collective inchangee. Suite : audit archives/sources/journal, rapport et cumul657. RH/paie et point6 humains differes, aucune recette utilisateur/production validee.


## Bilan645-657

14 tests du verificateur reussis en0,74s ;45archives anterieures SHA/CRC/manifeste valides et inchangees ;106sources protegees dont toutes migrations,main,models,schemas et AGENTS inchangees ;46fichiers de session couverts exactement avant ce bilan,aucune suppression. Python cumulatif compile. Matrice70=16termines/47partiels/3absents/4bloques;14interruptions historiques preservees.
[Rapport de session](RAPPORT_SESSION_20261019_645_657.md). Cumul657 contient les versions courantes des lots645/647/649/651/653/655 et ce bilan; les anciens ZIPs restent intacts. Recette humaine Word/Excel et deploiement reel a effectuer;RH/paie etpoint6 differes. Prochaine priorite : referentiels et modeles fiscaux officiels manquants, ou travail horsRH independant si inaccessibles.


## Annulation collective datee659

Le formulaire655 couvre aussi toute ventilation :relecture complete,total/nombre/numeros, date et motif facultatif pour le lot. Aucun backend/SQL modifie. 67tests reussis en227,03s, zero echec/erreur/ignore : API PostgreSQL nonce,Edge vente/achat et1365/390,refus/rollback/concurrence/permissions/contextes/lettrage et annulations individuelles. Build Vite reussi5,06s. Compilation Python des tests modifies. Ces campagnes recouvrent les precedentes et ne sont pas additionnees.
[Rapport659](../../Test/rapport_annulation_ventilation659.md),[guide](../ANNULATION_REGLEMENT_655.md). Originaux definitifs conserves, erreurs sans mutation et rechargement automatique. Recherche09B officielle ne livre toujours pas catalogue2026;historiqueEDI2010 deja audite265 non utilise pour inventer un schema. Statuts globaux inchanges. Suite : rendre consolidation651 reproductible sans baselines privees puis refaire campagne sur produit courant. RH/paie etpoint6 humains differes.


## Consolidation portable661

255cas distincts reussis765,99s,zero echec/erreur/ignore,sous vrai PostgreSQL nonce et Edge;382sources et temoins comptables/documentaires non vides preserves,2documents. Deux baselines privees explicitement interdites durant campagne. Test de sources1reussi1,98s,regression avant correction1erreur setup26,72s conservee.49archives referencees SHA/CRC/manifeste intactes. Python compile;aucun produit/SQL modifie dans661;dernier build6595,06s.
[Rapport661](../../Test/rapport_consolidation_portable661.md),[bilan courant](RAPPORT_SESSION_20261019_645_661.md). Anciens ZIPs intacts;erreur du champ SHA dans recapitulatif prive657 corrigee dans nouvelle preuve distincte, sans modification archives. Matrice70 et statuts globaux inchanges. Prochaine anomalie : chargement reglements peut masquer un refus en liste vide;reproduire via permissions du seul bac puis correction663. RH/paie etpoint6 humain differes.


## Lecture fiable des règlements663

Un vrai refus de lecture ne devient plus Aucun règlement : alerte explicite, Réessayer/Actualiser, liste et total indisponibles pendant chargement/erreur. Vrai200vide et diagnostics historiques conservés. Consigne mobile repliée lisiblement. 63 tests connexes réussis en 344,82 s avant la retouche visuelle, puis 8 Edge finaux réussis en 92,91 s après celle-ci, zéro échec/erreur/ignoré. Refus SQL réels, reprise sans F5, attente de vrai GET, vrai vide, contextes, historiques invalides, annulations et lettrage. Build final : 6,28 s, code0. Capture390 finale inspectée : consigne lisible, erreur/reprise sans débordement ; ACL et photos comptables préservées. Python du test compilé. Campagnes recouvrantes non additionnées.
[Rapport663](../../Test/rapport_reglements_lecture663.md). Défaut avant correction reproduit33,46s après deux erreurs de banc conservées distinctement. Aucun backend/SQL/règle fiscale modifié ; seul SELECT du LOGIN nonce révoqué/restauré pour le test. Statuts globaux inchangés. Suite665 : commandes Règlements en consultation seule, puis guide/checklist actualisés ; RH/paie etpoint6 humain différés.


## Commandes de règlements et consultation665

Modifier/Supprimer/Annuler masqués pour Lecture via permission commune ; Actualiser et RAS lisibles, Comptable conserve ses commandes. Le serveur refusait déjà les mutations :aucun droit/API/SQL changé. 4 profils Edge/API/PostgreSQL102 réussis en 59,34 s, puis 12 parcours connexes réussis en 168,88 s ; zéro échec/erreur/ignoré. Lecture/Comptable, achat/vente,1440/390, GET200 et refus403 natifs, photographies comptables identiques et aucun POST navigateur. Build7,94 s, code0. Python compilé ; capture de liste Lecture390 inspectée. Campagnes recouvrantes non additionnées.
[Rapport665](../../Test/rapport_reglements_consultation665.md). Reproduction avant correction1échec43,87s ;erreur de banc Fermer ambigu conservée distinctement. Statuts globaux inchangés. Suite667 : panne et réponses tardives de réceptions fournisseurs, puis guide/checklist. RH/paie etpoint6 humain différés.


## Réceptions fournisseurs :lecture et contexte667

Erreur distincte du vide, compteur indisponible, Réessayer/Actualiser et garde génération/exercice/jeton. Deux régressions natives avant correction44,32s (faux vide et mauvais exercice). 8 Edge ciblés réussis en 62,69 s puis 12 connexes réussis en 199,70 s ;zéro échec/erreur/ignoré. BC/BR/facture et réceptions partielles, rôles et lectures de règlements vérifiés. Build6,25s code0, Python compilé. Capture erreur390 inspectée ; ACL et données métier après authentification préservées. Aucun stock, calcul, générateur comptable, SQL ou PostgreSQL réel modifié. Les campagnes recouvrent les précédentes.
[Rapport667](../../Test/rapport_receptions_lecture667.md). Les casJWT sont de vrais renouvellements du même compte ;pas de validation du sélecteur multi-société complet revendiquée. Un premier banc6pass/2timeouts de contexte invalide reste consigné. Autres listes commerciales/mutations distinctes. Suite669 :NouveauBR ouvre en réalité un BC;remplacer par parcours explicite via commandes, rendre bascule Vente/Achat lisible surmobile, puis guide/checklist671. RH/paie etpoint6 humain différés.


## Entrée de réception clarifiée669

NouveauBR ouvrait un formulaire de commande; remplacé par Préparer depuis une commande, navigation sans création vers BCachat. Formulaire mal placé retiré, entrée réservée au rôle autorisé. Bascule Vente/Achat se replie sans troncature390. 16 parcours connexes réussis en 210,93 s après les 4 profils ciblés45,74 s ;zéro échec/erreur/ignoré. Réceptions/années/jetons, achats complets et partiels, rôles des règlements vérifiés sur PostgreSQL nonce et Edge. Build6,87 s code0, Python compilé. Capture Comptable390 inspectée : bascule entière et BR lié visible. Campagnes recouvrantes non additionnées.
[Rapport669](../../Test/rapport_entree_reception669.md). Avant1échec34,91s ;après BC1200 puis BR2unités lié, aucun mouvement/écriture avant facture dans profil testé. Aucun backend/SQL/règle fiscale changé. Autres commandes commerciales distinctes, statuts globaux inchangés. Suite671 :guideWord/PDFv15,checklist73actualisée,recette annuelle isolée et audit/cumul avant22:05UTC. RH/paie etpoint6 humain différés.


## Guide, couverture et bilan671

Guide version15 du19octobre2026 actualisé en Word/PDF35pages : annulations
individuelles/collectives avec date et motif, consultation seule, lecture/reprise,
entrée de réception depuis les commandes, documents RAS et sociétés liées.
Les17statuts humains du guide et les12de l’annexe RAS restent Non testé.
Checklist73 :40terminé,31partiel,1absent,1bloqué ; SEP20-01 reclassé partiel sur
preuves633/635/661. Matrice70 inchangée :16terminé,47partiel,3absent,4bloqué.
9contrôles documentaires réussis en1,53s ; oracle et parcours annuel connecté
sur PostgreSQL091 isolé :2réussites en45,58s,15non sélectionnés volontairement,
30avertissements, zéro échec/erreur/ignoré. Les fonctions099–102 ont leurs bancs
distincts ; ce parcours ne qualifie pas toutes les fonctions annuelles.
106fichiers protégés inchangés,59archives antérieures vérifiées, cumul70fichiers.
[Bilan et livraisons645–671](RAPPORT_SESSION_20261019_645_671.md),
[rapport671](../../Test/rapport_guide_bilan671.md).
Suite : autres listes et commandes commerciales à qualifier, puis pièces
officielles et historiques à obtenir selon le registre. RH/paie et point6
humain différés. Recette utilisateur à effectuer ; production non validée.
