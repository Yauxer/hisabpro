# MODE D’EMPLOI — PROPOSITION CONDITIONNELLE DU SOLDE IS/CM

Version 1 du 23 octobre 2026. Complément 753 du mode Liasse seule.

## Résultat de cette étape

Dans Comptabilité → Liasse fiscale → Import Balance / Liasse seule, une préparation peut maintenant relier B12, CM, crédits qualifiés et acomptes justifiés pour conserver une proposition de solde IS/CM. Le contrôle vérifie les liaisons entre les sources et la cohérence des montants. Il refuse de produire un solde si une source nécessaire reste inconnue ou si un contrôle dépend encore d’une ancienne source.

Conserver crée une version figée. Cela ne réalise aucun paiement, aucune imputation effective, aucune écriture comptable ni confirmation fiscale. La CSS reste affichée séparément ; aucun total global IS+CSS n’est inventé. L’excédent arithmétique ne constitue pas un droit à remboursement ou report confirmé.

## Préparer les sources fictives

Utiliser une société de test MAD2026, période 01/01–31/12, avec les jeux des guides 741,749 et 751. Les montants de cet oracle vérifient le fonctionnement et les liens des contrôles sur des hypothèses explicitement fictives ; ils ne constituent pas une déclaration annuelle prête à déposer ou un exercice comptable complet.

B12 : résultat net 6400 MAD, impôts comptabilisés 1600, résultat avant impôts 8000, réintégrations 500, déductions 200, déficit disponible explicitement fourni 1000. Base proposée 8000+500−200−1000=7300 ; taux déclaré 20% ; IS théorique 1460 MAD. Pour une vraie société, les millésimes/conditions du déficit et le régime/taux doivent être vérifiés sur pièces ; ne pas simplement recopier les confirmations de ce test.

CM741 : qualification du régime normal 2026, base exclue 0, base réduite 0, exonération totale non, minimum exonéré non. CM proposée 3000 MAD ; maximum IS/CM3000 MAD.

Crédits 749 :500 MAD saisis ;150 déjà utilisés sur acomptes ;25 autres utilisations ; disponible qualifié 325 MAD. Acomptes 751 :1000 effectivement versés déclarés,100 d’excédent antérieur affecté,150 de retenues affectées et rapprochées exactement : total 1250 MAD. Excédent antérieur restant 0. Les 150 de retenues déjà utilisées ne sont pas déduits une seconde fois des crédits.

Si le contexte 735 initial est présent, son total crédits 600 diffère des justificatifs typés 500 : l’alerte source reste visible. Ce contexte générique ne prouve pas une éligibilité et n’est pas corrigé artificiellement pour obtenir un contrôle vert.

La CSS n’est pas nécessaire pour simuler le seul solde IS/CM. Sans qualification CSS, elle reste indisponible. Pour un scénario séparé cohérent avec la référence 751, une qualification CSS2026 sur un bénéfice fiscal 2025 explicitement justifié de 100000 MAD donne 0 MAD, dans le profil IS déclaré sans exonération permanente ; sa date de clôture/calendrier n’est pas inventée. Le scénario CSS743 à 2millions est un autre cas, pas une source à reprendre sans examen.

## Examiner l’ordre de la simulation

Le calcul réutilise l’ordre de simulation existant : PPRF/Sukuk, rémunérations de tiers/location, excédent antérieur réservé au solde annuel, puis acomptes. Les regroupements restent techniques ; leur emploi dans cette simulation ne vaut pas affirmation d’un ordre légal universel. Les conditions réellement applicables et les droits de restitution/report doivent être examinés dans le dossier.

Un excédent antérieur restant après acomptes n’est pas repris automatiquement : le montant demandé doit être saisi explicitement, même s’il est nul, et ne doit pas dépasser le restant justifié. La même fraction ne peut pas être utilisée à la fois comme acompte et comme excédent annuel.

## Saisir la revue LIQ-N

1. Ouvrir « Proposer le solde IS/CM — 2026 » sur la dernière préparation contenant tous les contrôles à jour.
2. Choisir « Saisie documentée — à revoir ». Justification : « Revue fictive 753 des justificatifs et ordre de simulation documenté ». Ajouter une ligne.
3. Désignation : « Revue fiscale fictive 2026 ». Choisir oui pour taux/régime/déficits B12 vérifiés, qualification CM vérifiée, crédits et acomptes exhaustifs vérifiés, solde d’excédent antérieur vérifié et ordre de simulation examiné et justifié. Ces choix sont des déclarations de revue, pas une certification automatique.
4. Excédent antérieur à utiliser dans cette simulation annuelle :0. Référence : « REVUE753 et contrôles B12/CM/CR/AP conservés ».
5. Cocher la confirmation puis « Conserver la proposition IS/CM dans une nouvelle version ». Réouvrir la rubrique. La nouvelle version et son contrôle doivent apparaître sans F5.

## Vérifier les montants

Maximum IS/CM3000−crédits disponibles 325=2675 MAD. Acomptes justifiés 1250 : solde proposé 2675−1250=1425 MAD. Excédent arithmétique 0. La somme soustraite 1575 correspond à 1000 versés +100 d’excédent antérieur +500 de crédits −25 autres utilisations. Les 150 déjà utilisés sont inclus une seule fois.

Une modification du brouillon ne modifie pas le contrôle ou les exports tant qu’elle n’est pas conservée. Un champ de revue vide ou non confirmé, un excédent annuel vide, une source absente ou une incohérence bloque le solde : il reste indisponible, pas égal à 0.

## Reprendre après modification d’une source

Modifier le taux B12 en 10% et conserver une nouvelle version. L’ancienne proposition reste 1425 MAD pour mémoire et affiche « Proposition historique — sources modifiées ». Tenter de conserver immédiatement une nouvelle proposition laisse le solde indisponible, car la CM conserve encore sa référence à l’ancien B12.

Ouvrir la rubrique CM, relire les paramètres et conserver explicitement une nouvelle qualification sur le B12 actuel. Puis revenir à la proposition et conserver une nouvelle revue : le maximum reste 3000 MAD, donc le solde proposé reste 1425 MAD, cette fois sur des sources synchronisées. Les anciennes versions restent inchangées.

Le même principe s’applique aux crédits et acomptes : une nouvelle qualification crédits oblige à revoir le rapprochement acomptes avant une nouvelle proposition. Modifier seulement la CSS signale une source CSS ancienne sans recalculer l’IS historique.

## Exporter les justificatifs de la simulation

Télécharger le dossier de préparation ZIP : il contient `liquidation_is_documentaire.json`, le snapshot complet, les balances, PDF, Excel et le manifeste SHA256. Dans Excel, vérifier Origine proposition IS, Proposition IS CM, Revue proposition IS, Sources proposition IS et Répartition simulation IS. La CSS apparaît sur sa ligne séparée.

Le logo actuel valide de la société est intégré aux PDF/Excel. Les références commençant par = restent du texte. Les montants, sources et alertes sont repris depuis la version conservée ; aucun recalcul d’une ancienne proposition n’est effectué lors de sa lecture ou exportation.

## Cas de recette complémentaire

Les huit cas humains restent Non testé. Renseigner résultat réel, anomalies et preuves dans le classeur après exécution sur une société fictive.

| ID | Actions détaillées | Résultat attendu et preuve | Statut |
|---|---|---|---|
|LIQ753-01|Préparer les contrôles décrits, saisir les cinq confirmations de revue et l’excédent annuel 0 ; conserver.|Nouvelle version sans F5 ; maximum 3000, crédits 325, acomptes 1250, solde proposé 1425 MAD et excédent 0. Capture du contrôle et clé de version.|Non testé|
|LIQ753-02|Après conservation, modifier une confirmation du brouillon en non puis télécharger le ZIP.|Contrôle et exports restent 1425 MAD ; brouillon non promu. Garder PDF/Excel/JSON et version.|Non testé|
|LIQ753-03|Conserver une revue avec ordre non confirmé ou excédent annuel laissé vide.|Solde indisponible, aucun zéro ou paiement confirmé. Capture des champs et alerte.|Non testé|
|LIQ753-04|Tenter NaN puis 0,01 MAD d’excédent annuel alors que le restant justifié est 0.|Refus lisible sans nouvelle version ; saisie corrigeable. Capturer les refus et les versions.|Non testé|
|LIQ753-05|Changer le taux B12 en 10 et conserver ; observer l’ancienne proposition ; tenter une nouvelle revue avant actualisation CM.|Ancien 1425 figé avec avertissement ; nouvelle proposition indisponible car B12/CM désynchronisés. Captures et deux versions.|Non testé|
|LIQ753-06|Après le cas précédent, revoir et conserver la CM sur le nouveau B12 ; conserver une nouvelle proposition.|Solde 1425 MAD sur sources synchronisées, anciennes propositions préservées. Capturer CM, revue et clés sources.|Non testé|
|LIQ753-07|Comparer sans qualification CSS puis avec CSS2026 qualifiée sur bénéfice fiscal 2025 de 100000 MAD.|CSS d’abord indisponible, puis 0 MAD séparément après nouvelle revue ; solde IS1425 inchangé ; aucun total global IS+CSS. Captures des deux états.|Non testé|
|LIQ753-08|Avec rôles comptable puis lecture sur 390 px, consulter et télécharger PDF/Excel/ZIP.|Comptable peut conserver ; lecteur ne peut pas modifier ; pas de débordement global ; logo et montants cohérents. Preuves des rendus.|Non testé|

## Limites à conserver visibles

Cette proposition porte sur le principal IS/CM sous qualifications déclarées. Elle ne liquide pas des pénalités, ne confirme pas la disponibilité réelle d’un crédit et ne réalise aucun dépôt. Les régimes spécifiques, calendriers non couverts, schéma officiel XML/EDI, pièces manquantes historiques et recette humaine restent distincts. RH/paie et le point 6 humain restent différés. Aucune production qualifiée.
