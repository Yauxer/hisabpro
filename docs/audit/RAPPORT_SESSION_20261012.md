# HisabPro — reprise du12octobre2026

Périmètre :travaux depuis00:49UTC,puis reprise20:45UTC après interruption. Le cumulatif à venir consolide ces deux exécutions pour ne pas perdre les lots déjà livrés. Dépôt local seul source de vérité ;absence de dépôtGit confirmée. Aucun PostgreSQL réel,donnée comptable réelle,modèle,main oumigration modifié. Le point6 reste en attente du retour utilisateur.

## Développement livré

- Préparation annuelle interne des ventes418 :onglet dans la liasse,lecture seule dans la société/exercice sélectionnés,factures définitives etavoirs à leur date,identités historiques,sources etdiagnostics. Les montants incomplets restent inconnus ;partie certaine séparée. CSV exact. Hors ventes non issues de facturation etextérieur àl'archive fiscale.
- Exports423 :Excel Synthèse/Sources etPDF interne,montants exacts ettextes littéraux. Empreinte de l'aperçu contrôlée avant export ;sources modifiées refusées409,actualisation proposée. Nom du fichier exposé au navigateur,protection contre réponses tardives après changement de contexte.
- Guide ventes420puis424 :Word/PDF6pages etclasseur3feuilles7cas humains Non testé. Données exactes270/54/324 etvariante370/74/444 ;CSV,Excel/PDF,identités etrefus d'export obsolète expliqués.
- Variante annuelle persistante417 :chèque bureau/effet mobile intégrés au banc existant ;facture120,frais10,01,banque109,99,lettrage etFEC,clôture2025puisAN2026.
- Bancs414/415/416 :test des frais par le vrai validateur,dépendance AST bancaire,synchronisation du diagnostic stock,attente de connexion DOMContentLoaded etcontrôle explicite de l'interface authentifiée. Aucun assouplissement des assertions financières.

## Résultats réels conservés

| Lot | Exécution | Conclusion |
|---|---|---|
| 411 | 3390cas,3385réussis,5échoués,0erreur,0ignoré,4301.675s,exit1 | Globale échouée ;preuve ettraces conservées |
| 414 | 3échecs/12réussis avant,39réussis après | Bancs corrigés,tests ciblés/connexes exécutés |
| 415 | Défaut bureau reproduit ;3réussis puis37connexes | Diagnostic stock synchronisé,produit inchangé |
| 416 | Deux cas contrôlés échoués avant ;12réussis après | Attente de connexion améliorée ;cause du délai original411non démontrée |
| 417 | 4réussis43.726s | Deux cycles courants etdeux annuels réduits,conservation des origines |
| 418 | 14réussis,puisLecture1etEdge3 ;archives/bilan/navigation8 | Préparation/CSV testés ;suites recouvrantes non additionnées |
| 419 | Interruption à27%,au moins3échecs,niXML final ni.exit | Global non validé ;rejeu des trois modules8réussis101.999s,cause inconnue |
| 423 | Copie20API/rendus,6Edge,1PDF120sources ;racine27puis19connexes | Exports etpermissions testés ;compilation/build0,141modules11.05s |
| 424 | DOCX CRC/XML/relations,PDF6pages sans débordement,Excel3feuilles7NonTeste | Contrôles techniques exécutés ;Office etrecette humaine non effectués |
| 426 | 3422cas,3332réussis60échecs30erreurs,XML/log complets ;code wrapper non récupéré | Globale échouée,empreintes729conservées ;preuve livrée |
| 427 | Piste alternative Adala/SGG/ACAPS ; texte recherché non obtenu | Aucune nouvelle qualification sociale ni taux modifié ; constat livré |

Les tests ci-dessus se recoupent ;aucun total additionné ne sert de preuve globale. Les premiers échecs de noms de fichier,invoqueurs,fixtures etdonnées de test sont consignés dans leurs rapports ;ils ne sont pas présentés comme tests réussis.

## Couverture etlimites

70fonctions :15terminé,47partiel,4absent,4bloqué. Seul09Echange d'absent àpartiel grâce àla préparation exploitable ;une préparation interne ne qualifie pas le format fiscal. Les73demandes utilisateur restent40terminé,30partiel,2absent,1bloqué.

Sources officielles421 :accès direct au CGI2026etmodèles non obtenu,timeouts ;aucune nouvelle règle fiscale codée. Référentiel social/CNSS412,XML/EDI applicable,catalogue DGI exhaustif,09F/09G etjustificatifs historiques restent ouverts. Les reliquatsFEC/ETIC ne sont jamais artificiellement réparés.

Développement global :partiel. Tests automatisés :réussis sur les périmètres ciblés précisés,dernier résultat430 :3426 cas : 3426 réussis, 0 échecs, 0 erreurs, 0 ignorés, 6358.352s,code0,suiteréussie sur les sources figées après428/429 ;historiques en échec conservés. Recette utilisateur :à effectuer. Mise en production :non validée,point6 en attente.

Prochaine action :récupérer la preuve426,vérifier les729empreintes puis corriger tout échec reproductible avant nouvelle recette ;compléter couverture etlivrer leZIPcumulatif différentiel. Ensuite prioriser les fonctions partielles indépendantes des textes manquants,avec données synthétiques ettraçabilité.

## Reprise du14octobre2026

| Lot | Tests exécutés | Portée |
|---|---|---|
| 428 | 32 cas : 32 réussis, 0 échecs, 0 erreurs, 0 ignorés, 202.496s | Précision préparation etexports |
| 429 | 3 cas : 3 réussis, 0 échecs, 0 erreurs, 0 ignorés, 43.712s | Synchronisation dégressif,aucune règle modifiée |
| 430 | 3426 cas : 3426 réussis, 0 échecs, 0 erreurs, 0 ignorés, 6358.352s,code0 | réussie sur les sources figées après428/429 |


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
