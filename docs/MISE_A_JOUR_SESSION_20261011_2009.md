# Livraisons de session20h09UTC


## Session du 11 octobre 2026 — reprise 20h09 UTC — lots403 à410

- [Globale403](../Test/rapport_consolidation_globale_403.md) :3320 tests, 0 échec, 0 erreur, 0 ignoré, 4071.765 s, 713 sources stables. Exécution des sources finales401, avant les nouveautés404/405/406. L’échec historique391 et sa reprise isolée restent conservés dans leur rapport.
- [Frais404](../Test/rapport_effets_frais_precision_404.md) :six défauts API reproduits puis corrigés ;refus des booléens, fractions de centime et frais ignorés ;calculs Decimal et erreurs lisibles. Encaissement120 = banque109,99 + frais10,01. Aucun changement d’historique.
- [Propositions405](../Test/rapport_rapprochement_propositions_405.md) :correspondances exactes et uniques, sélection explicite, confirmation atomique, refus d’aperçu obsolète et de doublons. Simple et lot natif immédiat ;gardes de contexte, dates, clôture, permissions et concurrence. Course initiale du chargement société reproduite puis corrigée. Aucune écriture créée par le pointage.
- [Parcours406](../Test/rapport_encaissement_frais_406.md) :chèque bureau et effet mobile, remise/encaissement, validation du Journal, pointage du net, lettrage et FEC réel. Quatre pièces, dix lignes, D=C480 ;client/attente0, banque109,99, frais10,01. Annulation après cycle bancaire refusée409 sans mutation. Facture initiale préparée viaAPI fictive ;ce cas n’est pas une année complète.
- [Guide407](../Test/rapport_guide_propositions_frais_407.md) :Word/PDFv14,32pages,18fiches/17Non testé ;nouvelle annexeExcel3feuilles/9Non testé. Contrôles techniques réussis,MicrosoftOffice non ouvert.
- [Consolidation410](../Test/rapport_consolidation_propositions_frais_410.md) :185 réussis, zéro échec/erreur/ignoré, 456.818 s, sources finales figées et identiques, compilation/build code0. Dix-neuf fichiers couvrant les nouveaux lots, les opérations bancaires existantes, annulation/RAS, sauvegarde/restauration et année2025→2026. Suite connexe distincte de403 ;les résultats ne sont pas additionnés.

Couverture conservée :70fonctions,15terminé/46partiel/5absent/4bloqué ;73demandes,40terminé/30partiel/2absent/1bloqué. Propositions exactes et frais individuels développés/testés ;rapprochement approximatif exhaustif, instruments chèque/effet groupés et escompte restent partiels. Les références du relevé réel ne sont pas supposées égales au Journal. Paie définitive, XML/EDI et qualifications fiscales/documents historiques restent limités ou bloqués selon la matrice.

Développement global partiel ;tests automatisés validés sur les périmètres exécutés ;recette utilisateur à effectuer ;mise en production non validée. Aucun PostgreSQL réel ni données comptables réelles. Aucune nouvelle migration ;084 reste une activation manuelle distincte sur recette isolée. Point6 en attente utilisateur.

Parcours annuel réduit406 également exécuté :2025→2026, résultat89,99 avant impôt de laboratoire3000, perte2910,01 ;clôture etAN2026 validés,quatre lignesD=C3020 ;FEC des deux exercices équilibrés etpointage2025 conservé/verrouillé. Le scénario annuel utilisateur exhaustif reste distinct. Relevés historiques non finis ou non positifs405 :montants et totaux concernés signalés inconnus,pointage interdit,sources conservées ;les correspondances certaines restent confirmables.

Nouvelle globale411 déjà en cours sur les sources finales :3390 cas collectés,721 empreintes figées. Aucun résultat final annoncé. Lire .codex-tests/consolidation411_globale.exit et.xml puis vérifier les empreintes avant toute validation ;ne pas relancer une commande encore active ni modifier les sources pendant l’exécution. La suite connexe410 est réussie et ne remplace pas cette nouvelle preuve exhaustive.

[Recherche ciblée412](../Test/rapport_source_modification_cnss_412.md) :texte de modificationCNSS non obtenu ;aucune nouvelle qualification réglementaire ni calcul modifié. Limite sociale maintenue,ainsi que la dépendance distincte au schéma officielEDI.

Prochaine reprise :ne pas réappliquer les lots livrés. Vérifier l’achèvement de la globale411 déjà lancée,puis instruire les instruments bancaires groupés,escompte et variantes annuelles exhaustives ;conserver les anomalies FEC/ETIC et ne pas débloquer paie/EDI sans sources officielles qualifiées. Point6 en attente utilisateur.

Livraisons : [403](../HisabPro_Patch403_Consolidation_Globale_Finale401.zip), [404](../HisabPro_Patch404_Frais_Bancaires_Centimes.zip), [405](../HisabPro_Patch405_Propositions_Rapprochement_Exact.zip), [406](../HisabPro_Patch406_Recette_Encaissement_Frais_Lettrage.zip), [407](../HisabPro_Patch407_Guide_Word_PDF_Propositions_Frais_Excel.zip), [410](../HisabPro_Patch410_Consolidation_Propositions_Frais.zip), [412](../HisabPro_Patch412_Recherche_Source_CNSS.zip).

[Mode d’emploi Word](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx), [PDF](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf), [suivi Excel](recette/ANNEXE_RECETTE_PROPOSITIONS_FRAIS.xlsx). Le cumulatif différentiel de cette exécution sera livré après vérification des huit ZIPs d’étape.
