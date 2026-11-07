# Couverture422 — finalisation du14octobre2026


## État consolidé du14octobre2026 — lots411à432

- Préparation interne annuelle des ventes418/423 : factures et avoirs àleur date, identités figées, CSV/Excel/PDF et refus409des exports obsolètes. Le format fiscal officiel reste àqualifier.
- [Précision428](rapport_precision_ventes_428.md) : 32 cas : 32 réussis, 0 échecs, 0 erreurs, 0 ignorés, 202.496s. Suppression du détourfloat dans la seule préparation, en conservant les gardes et le moteur TVA partagé. Grands montants contrôlés sur API/CSV/Excel/PDF. Les centimes déjà perdus au stockageFloat ne sont jamais inventés.
- [Banc dégressif429](rapport_degressif_synchronisation_429.md) : 3 cas : 3 réussis, 0 échecs, 0 erreurs, 0 ignorés, 43.712s. Attente des cellules après rafraîchissement, réseau normal et latence contrôlée. Aucun calcul ni montant attendu modifié.
- [Guide424](rapport_guide_exports_ventes_424.md) : Word/PDF6pages et Excel3feuilles7cas « Non testé », données exactes270/54/324 et variante370/74/444. Office et recette humaine non exécutés.
- [Globale426](rapport_consolidation_globale_426.md) :3422cas,3332réussis,60échecs,30erreurs,0ignoré,729empreintes identiques avant428. XML/log complets,code wrapper non récupéré.72incidents sous-processus Windows0xC0000142,17fermetures du pilote Playwright et1lecture DOM vide. Aucune réussite rétrospective déclarée.
- [Globale430](rapport_consolidation_globale_430.md) : 3426 cas : 3426 réussis, 0 échecs, 0 erreurs, 0 ignorés, 6358.352s,code0. Conclusion :réussie sur les sources figées après428/429. Les suites ciblées ne sont pas additionnées àce total.
- [Sources fiscales421](rapport_source_cgi2026_421.md) et [sociales427](rapport_source_sociale_alternative_427.md) : documents requis non obtenus ; preuves antérieures conservées, aucune règle nouvelle installée.09F/09G restent absentes ;EDI etqualification sociale complète restent ouverts.
- [Source officielle431](rapport_source_lf2026_adala_431.md) : copie Adala de la loi50-25 effectivement obtenue,103pages,SHA etlecture des amendements151/157/247/273 contrôlés. Cette preuve supplémentaire ne constitue niCGI consolidé complet ni modèle de déclaration ;aucune règle métier nouvelle codée.
- [Index des recettes432](../docs/recette/INDEX_RECETTES_HISABPRO.md) : guides Word/PDF etannexes accessibles depuis un point d’entrée stable.36liens locaux contrôlés ;cahier218cas208Non testé/10Bloqué,ventes7Non testé. Aucun résultat humain prévalidé,aucun artefact du scénario annuel modifié.

70fonctions :15terminé,47partiel,4absent,4bloqué.73demandes :40terminé,30partiel,2absent,1bloqué. Ces découpages ne sont pas additionnés. Développement global partiel ; tests validés seulement dans leurs périmètres réellement exécutés ; recette utilisateur àeffectuer ; production non validée. Point6en attente utilisateur. Aucune base réelle ni donnée réelle,main,models,schemas ouSQL modifié.

Prochaine action :Compléter la recette d’installation vierge au-delàdu manifeste082avec083_ras_reglements.sql puis084_rapprochement_ventilations.sql, dans l’ordre de leurs prérequis048/083 ;tester les droits applicatifs etla restauration sur cible jetable. Préserver le banc historique082. Les annexes tiers/TP exigent encore le modèle etle référentiel applicables ;aucun EDI inventé.

Comptages70/73, identifiants uniques etliens locaux contrôlés réellement. Le premier contrôle documentaire excluait àtort les préfixesJUL19/JUL26 avec chiffres ;expression corrigée sans modifier les statuts. Pas de test métier nouveau dans ce lot documentaire. Le reçu426est inclus pour corriger deux coquilles etclarifier ses90incidents ;traces etrésultats inchangés.
