# Mise à jour RAS — HisabPro, 9 octobre 2026

La correction de l'estimation et des soldes291/292/295/296/297 fonctionne sans
migration nouvelle. Un taux documentaire ne constitue plus un paiement ; les
retenues historiquement comptabilisées sont conservées et identifiées.

Le flux de capture explicite293/303 nécessite une activation séparée. La
migration [083_ras_reglements.sql](../hisabpro-backend/083_ras_reglements.sql)
est **manuelle et additive** : deux tables de traces, contraintes, fonctions,
triggers et droits. Elle n'est ni dans `Base.metadata` ni dans le bootstrap
automatique de développement. Copier les fichiers ou démarrer l'application
ne doit pas créer ces deux tables. Aucune migration n'a été exécutée ici sur
une base réelle.

## Activation sur une installation isolée

1. Partir d'une copie compatible avec le socle du cumulatif
   `HisabPro_Session_20261009_1404_Cumulatif_Verifie.zip` : lots jusqu'à289.
   Comparer les modifications locales avant d'appliquer le différentiel RAS.
   Le dépôt de cette session contient déjà ces changements.
2. Utiliser une installation et une base de recette distinctes. Préserver
   configuration, fichiers de pièces et sauvegardes ; ne pas réinitialiser
   une base existante et ne pas rejouer les réparations historiques065–070.
3. Vérifier les migrations antérieures et les journaux/comptes actifs de la
   société fictive. L'ancienne correction de démarrage GRH229 reste dans le
   socle ;083 ne remplace ni080, ni081, ni082.
4. Faire appliquer **uniquement083**, avec le rôle de migration de cette base
   isolée, par la procédure habituelle de l'installation. Le script est
   transactionnel ; son rejeu est contrôlé par les tests dédiés. Aucun outil
   applicatif n'applique automatiquement cette migration.
5. Le script prévoit les droits minimaux pour le rôle `hisabpro` s'il existe.
   Si le rôle runtime est différent, faire provisionner explicitement ses
   droits SELECT/INSERT et l'usage des séquences sur les deux nouvelles tables,
   sans lui donner UPDATE/DELETE/TRUNCATE. Vérifier sous le vrai rôle runtime
   de la copie isolée, pas seulement avec le propriétaire des tables.
   Le trigger de contrôle des liens est une fonction `SECURITY DEFINER` :
   son propriétaire doit rester le rôle de migration autorisé. Ses lectures
   utilisent les tables `public` explicitement qualifiées et un `search_path`
   fixé à `pg_catalog,public`. Il contrôle les liens et l'acteur sans accorder
   au rôle applicatif un accès global supplémentaire aux appartenances société.
6. Redémarrer la copie de recette. Sans083, la consultation des règlements
   reste disponible et la capture indique son indisponibilité ; aucun POST
   de capture ne doit être envoyé pour contourner ce contrôle.
7. Exécuter les tests et les cas de recette isolés, puis vérifier les écritures,
   auxiliaires, soldes et exports. Les anciens taux/flags/OD ne sont pas
   réécrits, importés ou transformés en nouvelles captures.
8. Une application ultérieure sur une base réelle reste une opération distincte
   à préparer avec sauvegarde et contrôle de migration. Cette session n'exécute
   aucune commande contre cette base.

Commande des tests automatisés, depuis la racine du dépôt, sans charger `.env` :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_ras_capture_reglement_postgres.py Test/test_ras_capture_migration_isole.py Test/test_e2e_ras_capture_isole.py --tb=short
```

Ces fixtures possèdent leurs clusters PostgreSQL nonce ; le runner exclut le
banc historique non isolé. Le résultat de cette commande doit être consigné,
jamais déduit de la présence des tests. Les preuves réelles de cette session
sont consignées dans les [rapports backend293](../Test/rapport_ras_capture_reglement.md)
et [navigateur303](../Test/rapport_e2e_ras_capture_isole.md). Les cinq parcours
navigateurs finaux ont réussi ; ils ne prévalident pas une recette utilisateur.

Une sauvegarde PostgreSQL utilisant `--no-privileges` ne transporte ni rôles
ni ACL. Après restauration isolée, provisionner le rôle runtime puis rejouer
083 pour ses droits minimaux ; vérifier les traces et les refus de mutation.
Ne pas livrer de dump de données avec le ZIP de code. La preuve de sauvegarde
et restauration des nouvelles tables est consignée séparément dans le
[rapport305](../Test/rapport_sauvegarde_ras_reglements_isole.md) : onze tables,
huit triggers et sept écritures de laboratoire conservés ; droits reprovisionnés
et lecture/refus de mutation sous une vraie connexion LOGIN distincte.

## Portée métier

La capture est une saisie déclarative d'une retenue effectivement opérée sur
un règlement immédiat déjà comptabilisé, par virement ou espèces. Le montant,
la date d'opération, la référence et le compte destination sont explicites.
L'application ne choisit pas un compte fiscal, un taux ou un prorata universel.
Les autres moyens de paiement et les historiques déjà marqués comme retenus
ne sont pas mélangés à ce flux.

L'OD liée est préparée en brouillon et doit être contrôlée puis validée dans le
journal. Sa trace de capture reste conservée ; une annulation du règlement
doit créer les contrepassations liées et une trace d'annulation, sans effacer
ou modifier les écritures initiales. Une référence saisie ne crée pas une
attestation fiscale authentifiée.

RAS TVA complète, détermination IR/IS/TVA, attestations, déclarations et pont
automatique vers les crédits IS demeurent hors de cette activation. Le
[rapport des sources primaires](../Test/rapport_sources_ras_20261009.md)
documente les textes obtenus et ceux encore manquants. Aucun taux nouveau
ni conformité officielle ne sont validés par cette migration.

Le [cahier RAS estimation](recette/ANNEXE_RECETTE_RAS_ESTIMATION_20261009.pdf)
et son [Excel de suivi](recette/ANNEXE_RECETTE_RAS_ESTIMATION_20261009.xlsx)
portent sur des paiements sans capture effective. Leurs deux cas restent
**Non testé** pour l'utilisateur ; ne pas ajouter une capture pour changer
leurs oracles. Développement global partiel, recette utilisateur à effectuer,
mise en production non validée.

L'[annexe capture PDF306](recette/ANNEXE_RECETTE_RAS_CAPTURE_20261010.pdf)
et son [suivi Excel306](recette/ANNEXE_RECETTE_RAS_CAPTURE_20261010.xlsx)
couvrent deux sociétés neuves, les captures explicites30/70, la validation,
le lettrage puis l'annulation. Les deux cas restent **Non testé** pour
l'utilisateur. Les comptes et montants du laboratoire ne sont pas des
prescriptions fiscales.

## Annulations historiques

Le lot308 réutilise une résolution exacte et unique de l'OD historique.
Annuler le dernier règlement d'une facture historiquement marquée comme
retenue refuse409 si l'OD est absente, ambiguë, incohérente ou déjà contrepassée.
Ce refus préserve le règlement, la facture et les écritures ; il ne faut pas
créer artificiellement une OD ou modifier une pièce définitive pour le lever.
Conserver le diagnostic et réunir les justificatifs pour une vérification
contrôlée. Les cas déterminables vente/achat ont réussi sur PostgreSQL nonce.
Voir le [rapport308](../Test/rapport_ras_historique_annulation.md).
