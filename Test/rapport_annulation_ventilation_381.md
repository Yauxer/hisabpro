# Annulation collective des règlements ventilés — lot 381

## Modification minimale

L'opération native est identifiée par l'UUID déjà encodé dans ses numéros `VT-…-01`, `VT-…-02`, etc. Aucune reconstitution depuis une référence libre, aucun nouveau modèle et aucune migration.

Le service d'annulation individuelle existant est extrait sans commit intermédiaire. La nouvelle route collective verrouille le lot, ses factures et l'identifiant d'opération, puis annule toutes les lignes dans **une seule transaction**. Chaque règlement comptabilisé conserve son écriture d'origine et reçoit sa contrepassation exacte, avec les auxiliaires et la piste d'audit. Les captures RAS associées utilisent le même service existant de contrepassation.

Un lot déjà entièrement annulé est rejouable sans nouvelle écriture. Un lot partiellement annulé, incomplet, étranger, de cycle engagé ou comportant un montant invalide est refusé. Si une ligne tardive échoue, les changements préparés sur les précédentes sont annulés par rollback.

Dans **Cycle commercial → Achat/Vente → Règlements**, le bouton « Annuler toute la ventilation » complète l'annulation individuelle. Avant confirmation, le frontend relit toutes les lignes de l'opération auprès du backend : le compte et le total confirmés ne proviennent pas seulement du filtre visible. Après succès, règlements et factures sont rechargés automatiquement. Les lignes annulées restent visibles.

## Tests réellement exécutés dans la copie isolée

PostgreSQL temporaire nonce, vraie API et Edge ; `.env` désactivé. Aucun accès au PostgreSQL de l'utilisateur.

- Avant ajout : **1 échec attendu**, route collective absente (404), 19,38 s.
- Première relance : **6 réussites / 1 échec**, 25,61 s. La photographie de conservation était prise avant la création de la deuxième société dans la fixture ; corrigé sans changer le produit ni les contrôles métier.
- Annulation + ventilation API/Edge + variante annuelle : **53 réussites**, 26 avertissements, 154,78 s.
- Annulation avec permissions/RAS + suites RAS API/Edge : **36 réussites**, 26 avertissements, 144,40 s.
- Version finale des **22 nouveaux tests** : **22 réussites**, 26 avertissements, 49,79 s.
- Build Vite de la copie : code 0, 6,42 s. Avertissements existants sur l'import xlsx et la taille du bundle.

Les suites se recoupent, leurs effectifs ne sont pas additionnés. Les derniers ajouts de tests ne modifient pas le produit testé.

Couverture : achats/ventes, contrepassations exactes d'originaux validés inchangés, soldes des factures rétablis, répétition sans doublon, concurrence de deux annulations, refus après annulation individuelle partielle, rollback après erreur sur la deuxième origine, numérotation incomplète, tiers absent, société étrangère, période clôturée, lecture seule, UUID invalide, captures RAS inversées et conservées, NaN/±infini/zéro/négatif lisibles mais non annulables ; quatre Edge bureau/mobile.

## Mode d'emploi et limites

Sur société de recette, créer deux factures TTC 120 et 240 MAD d'un même client ou fournisseur. Ventiler un virement de 240 MAD en 120/120. Le solde de la deuxième facture reste 120. Annuler toute la ventilation : la confirmation indique deux règlements et 240 MAD. Les deux lignes deviennent annulées ; les soldes redeviennent 120 et 240. Dans le journal, contrôler deux contrepassations de 120, puis les valider selon le circuit normal. Les originaux ne sont pas effacés.

Pour un lot déjà partiellement annulé, contrôler les lignes individuellement : l'action collective ne dissimule pas cet état. Les chèques et effets conservent leur cycle dédié.

Un instrument bancaire unique et son rapprochement avec une seule ligne de relevé restent distincts de cette annulation collective. Les historiques sans identifiant natif ne sont pas regroupés automatiquement. Recette utilisateur à effectuer, point 6 laissé en attente ; aucune validation de production ou de conformité réglementaire.

Fichiers intégrés après la consolidation378 et livraison379.

## Contrôle final dans le dépôt courant

22 tests réussis,0échec/erreur/ignoré,44.271s,code0,à la racine intégrée sur cibles nonce. Suites copie distinctes non additionnées.

La globale378 précède ce changement. Les consommateurs règlement/RAS finaux seront consolidés séparément dans385.
