# Reprise après B13 documentaire autonome721

Vérifier le dernier état du journal et les preuves/ZIPs avant de reprendre.
Le service B13, ses routes, son formulaire et ses exports sont présents dans
`balance_resultat_courant_service.py` et `BalancePreparationResultatCourant.jsx`.
Ne pas les réappliquer. La couverture fiscale globale reste partielle ; le B13
documentaire n’est ni une liquidation IS ni un modèle officiel de dépôt.

## Ce que721 apporte précisément

- Sources exactes N/N-1, périmètre courant71/73 moins61/63 du moteur existant,
  écart au CPC VII figé, compte67 distinct pour mémoire.
- Hypothèses fiscales explicitement saisies/référencées : réintégrations,
  déductions, impôt théorique courant et régime/avantages à documenter.
- Équations documentaires figées, sans taux fiscal, IS dû, paiement ou écriture.
- Inconnus, signes inverses, N-1 absent, anciennes balances119 et notes
  contradictoires préservés et visibles ; versions/UUID/SHAparent/droits/MAD.
- Guide Word/PDF et Excel à six cas humains Non testé, données/CSV fictifs.

Les tests effectivement achevés sont consignés dans le rapport721 et le journal.
Ne pas extrapoler une réussite automatisée à la recette humaine/production.

Le B13 du Journal reste sa vue indicative existante dans `etic_service` ;
721 ne le remplace pas et ne qualifie pas son impôt comme théorique. Une revue
normative de cette vue reste distincte du formulaire documentaire autonome.

## Prochaine zone : C3 depuis sources conservées

Le dépôt possède déjà `etic_service._calcul_c3_depuis_soldes` et
`Test/test_patch103_etic_c3.py`. Réutiliser les calculs comptables ; éviter de
dupliquer les formules entre Journal, préparation, PDF, Excel et contrôles.
Le format actuel renvoie des nombres flottants : prévoir une représentation
décimale exacte pour la préparation sans changer le contrat existant par défaut.

La préparation possède N et éventuellement N-1, pas N-2. Les soldes N-2 ne
doivent pas être prélevés dans le Journal de la société courante. Effectif,
bénéfices distribués, données par titre et références historiques restent
inconnus tant qu’ils n’ont pas été explicitement documentés. Ne pas réactiver
RH/paie pour compléter artificiellement cet état.

La situation nette calculée par le moteur actuel ajoute le résultat car sa
source Journal exclut la clôture technique. Examiner chaque cas externe :
119 déjà soldé, balance avant clôture, CPC absent/indisponible. Ne pas montrer
un résultat d’activité nul à partir de classes6/7 soldées ; ne pas compter
deux fois un résultat déjà présent en119. Les écarts au bilan/CPC figés doivent
rester visibles et les anciennes versions ne doivent pas être recalculées.

## Ensuite : B12 et B14

B12 nécessite ses propres données sourcées : retraitements, déficits par
millésime, crédits et acomptes. `fiscalite_is_service.calculer_is` est pur ;
`routers.fiscalite.situation_is` interroge le Journal et les modules de la
société et ne doit pas alimenter une préparation indépendante. Réutiliser les
moteurs purs plutôt qu’inventer un second calcul, en vérifiant les textes
officiels applicables avant toute règle nouvelle/modifiée.

B14 nécessite des flux et des références de déclarations explicites. Une
variation de soldes TVA ou le journalTV ne prouve pas une déclaration déposée.
Ne pas reprendre des données réelles du dossier courant pour compléter des
balances externes. Conserver les inconnus et les écarts documentaires.

Le [point de reprise717](REPRISE_SOURCES_FISCALES_APRES_717.md) conserve l’analyse
des dépendances. RAS/EDI officiels, anomalies historiques sans justificatif,
recette utilisateur et installation cible restent des limites distinctes.
RH/paie et point6 humain restent différés.
