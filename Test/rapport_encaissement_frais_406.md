# Parcours connecté encaissement avec frais —406

Facture initiale préparée par API dans une société fictive vierge ;paiement,remise,encaissement,validation Journal,confirmation de proposition et lettrage par interface Edge réelle. Chèque1365 et effet390,échéance du jour. Aucun appel métier simulé ;les bancs retardés405 sont distincts.

Oracle indépendant :HT100/TVA20 de laboratoire/TTC120 ;portefeuille120,remise120,encaissement5141D109,99+61472D10,01/attenteC120. Quatre pièces,dix lignes,D=C480 ;3421 et comptes d’attente0 ;banque109,99 ;frais10,01. Trois nouveaux brouillons validés,une ligne de relevéCrédit109,99 pointée,lettrage3421deux lignes120/120 avecAAA,rechargement conservé. Photographies des montants/numéros/validations intactes.

ContrôleFEC conforme_export dans ce jeu fictif et export réel :dix lignes,D=C480. Premier oracle d’export utilisait les mauvais noms Debit/Credit et a échoué ;corrigé selon les colonnes réelles Montant_Debit/Montant_Credit,puis deux tests réussis32,34s sur copie. Aucun changement produit pour cet oracle.

Variante annuelle supplémentaire réellement exécutée :2025→2026, résultat89,99 avant impôt de laboratoire3000,perte2910,01 ;clôtureUI etAN2026 validés,quatre lignesD=C3020 (5141D109,99/1199D2910,01/4455C20/4453C3000). FEC2025/2026réels etéquilibrés,pointage2025conservé enlectureseule,dérapprochement409 ;originaux inchangés. Premier essai1réussite27,19s surcopie. Année réduite,pas le scénario complet218cas ni un régime fiscal qualifié ou une recette utilisateur. Escompte et instrument regroupant plusieurs factures restent distincts.

185tests racine réussis,456.818s,zéroéchec/erreur/ignoré ;721empreintes stables ;compilation etbuild code0.

Aucun PostgreSQL réel ni donnée comptable réelle ;sources et tests finaux sur PGnonce/Edge. Aucun SQL nouveau,main/modèles/migrations conservés. Recette humaine etpoint6 en attente.
