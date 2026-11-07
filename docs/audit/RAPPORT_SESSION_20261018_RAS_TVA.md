# HisabPro — livraison RAS TVA571–589 — 18octobre2026

## Résultat de cette reprise hors RH/paie

La simulation existante est maintenant reliée aux règlements par une capture
TVA guidée et une OD traçable. Le dossier déclaré est immuable, le rapprochement
avec le paiement est vérifié et l'annulation conserve les originaux avec
contrepassation. Le journal et les soldes commerciaux restent raccordés.
Le petit taux HT non nul n'est plus arrondi à zéro pour contourner la garde
interdisant le mélange HT/TVA dans ce mode.

Un registre interne annuel distingue achats/opérées et ventes/subies, captures
actives, OD validées et annulations. Il est accessible depuis Déclaration TVA
et **Liasse fiscale → Retenues TVA**. CSV/Excel/PDF couvrent l'année entière,
avec logo dans Excel/PDF et empreinte des données dans les trois formats.
Les exports exigent une actualisation si leurs sources changent. Les archives
fiscales existantes et les numéros internes T1–T25 ne sont pas modifiés.
Le cockpit propose explicitement les années civiles recouvertes par l'exercice
décalé : le registre couvre l'année civile entière choisie, pas les seules
dates de l'exercice. Le même périmètre est indiqué dans tous les exports.

Deux guides d'utilisation avec exemples fictifs sont fournis :

- [Préparer et contrôler une capture guidée — PDF,3pages](../guides/UTILISATION_RAS_TVA_GUIDEE_20261018.pdf)
- [Consulter et exporter le registre — PDF,2pages](../guides/UTILISATION_REGISTRE_RAS_TVA_20261018.pdf)

Leurs versions Markdown et générateurs sont dans le différentiel. Les captures
proviennent de véritables tests Edge sur sociétés de laboratoire. Les anciens
guides et cahiers de recette sont préservés ; aucun résultat humain prévalidé.

## Tests réellement exécutés

| Validation finale | Résultat | Durée |
|---|---|---:|
|Consolidation finale : captures libres/guidées, simulation, interfaces, registre, empreinte, cockpit, IS/états/lettrage et calculs purs|139réussis,1échec de préparation du nouveau cas décalé, corrigé ensuite|352,17s|
|Relance ciblée du cas juillet–juin corrigé|1réussi,6cas non sélectionnés déjà couverts ci-dessus|38,66s|
|Qualification préliminaire des deux parcours vente/achat, ensuite inclus dans139|2réussis|40,63s|
|Interface sans migration099, sur l'ancienne fixture isolée|2réussis|30,10s|
|Installation vierge099 et rejeux|1réussi|33,15s|
|Dernière restauration native avec la note du périmètre civil|1réussi|79,56s|
|Dernier build frontend|Réussi|10,44s|
|Guides PDF|3et2pages ouverts, textes/images et rendus inspectés|Contrôles distincts|

Les deux parcours587 sont inclus dans les139 réussis, pas additionnés.
Le test décalé utilisait une année d'ouverture au lieu de l'année de clôture
requise ; sa préparation a été corrigée puis le cas a réussi séparément.
Le banc complet n'a pas été relancé après ce seul correctif de fixture.
La consolidation précédente585 était entièrement verte :137tests,320,10s.
Aucun autre test n'a échoué dans la dernière consolidation ; aucun test ignoré.
Avertissements existants : Pydantic/anyio et gros chunks Vite.
Les erreurs de mise au point, dont le nom de fichier non exposé au navigateur,
le premier lancement avec Python global et les oracles/confirmations de587,
restent consignées dans leurs rapports et `CODEX_PROGRESS.md`.

Les parcours587 contrôlent indépendamment une factureTTC1200, deux cash525
et deux captures75. Les résultats CPC restent1000 pour la vente et-1000 pour
l'achat avant comptabilisation éventuelleIS. Les bilans restent équilibrés,
aucun crédit ou acompteIS n'est ajouté par la captureTVA. Cinq lignes sont
lettrées sous codeAAA ; après annulation, les écritures initiales sont
conservées, le solde de facture revient à600 et le registre distingue75actif
et75annulé. Il s'agit d'une qualification technique, pas d'un avis fiscal.

## Migrations et données

La seule nouvelle migration est **099_ras_tva_details.sql**, additive et
manuelle, après la chaîne existante jusqu'à098, notamment083. Elle n'est pas
appliquée automatiquement au démarrage ou par un formulaire. Le rôle
applicatif lit/insère les dossiers, sans droit de les modifier ou supprimer.

Installation réelle de laboratoire :90SQL distincts,26rejeux,116exécutions.
Les données des74tables antérieures restent intactes. La restauration
native copie75tables, schéma, ACL, séquences et données ; dossiers, JSON,
CSV, textePDF, valeursExcel et logos sont identiques après redémarrage.
Source de test préservée et cibles nettoyées.

**Aucun PostgreSQL réel contacté**, aucune donnée comptable réelle modifiée.
Les98SQL anciens, `AGENTS.md`, `main.py`, `models.py`, anciens guides et
recette sont inchangés par rapport à l'empreinte de départ571. Aucun commit,
push, nouveau développement RH/paie ou migration de production.

Pour l'installation cible, suivre [la procédure d'exploitation](../EXPLOITATION_HISABPRO.md)
avec contrôle des versions et sauvegarde préalable. La qualification en
laboratoire ne remplace pas cette installation ni la recette humaine.

## Limites et prochaine reprise

**Développement global : partiel. Tests automatisés : validés sur les périmètres
ci-dessus. Recette utilisateur : à effectuer. Production : non validée.**
La matrice conserve70lignes :16terminé,47partiel,3absent,4bloqué.

Le registre couvre les captures TVA guidées099, pas les captures libres ou
retenues historiques non qualifiées. Le compte reste explicitement choisi
et justifié. Les autres cas, mélanges HT/TVA, avoirs/acomptes affectés et
historiques ambigus ne sont pas assimilés à ce raccordement.

Le calcul de déclarationTVA fondé sur le cash seul reste explicitement
indisponible pour les périodes/reports concernés, sans ancien chiffre ni
zéro fictif. Le registre ne détermine ni créditTVA imputable ni reversement.
Le mois prévu ne prouve aucun paiement fiscal.

Prochaine action exacte : obtenir et vérifier les règles et modèles officiels
applicables à la déclaration/relevé RAS TVA, définir les preuves et périodes
d'imputation/reversement, puis ajouter les tests et l'intégration sans lever
la garde par hypothèse. Les nouvelles tentatives de consultation NC735/MEF
et CGI/TGR de cette reprise ont expiré ; aucun contenu non lu n'est revendiqué
comme vérifié. Voir [la note de sources](SOURCES_RAS_TVA_20261018.md).

Les travaux indépendants restent décrits dans [le plan hors RH](PLAN_FINALISATION_HORS_RH_20261018.md) :
provisions spécialisées, annexe151, taxe professionnelle, référentiel DGI,
liasse seule complète, opérations de groupe et exploitation cible. Le schéma
EDI applicable et les justificatifs historiques manquants restent des limites
visibles. La recette réservée au retour utilisateur reste en attente.

## ZIPs différentiels vérifiés

| Lot | Archive | Rapport |
|---|---|---|
|571|[Capture et dossier099](../../HisabPro_571_RAS_TVA_Capture_Tracee.zip)|[571](../../Test/rapport_ras_tva_capture_571.md)|
|573|[Interface et guide](../../HisabPro_573_RAS_TVA_Interface_Guide.zip)|[573](../../Test/rapport_interface_ras_tva_573.md)|
|575|[Installation et restauration099](../../HisabPro_575_Installation_Restauration_099.zip)|[575](../../Test/rapport_qualification099_575.md)|
|577|[Précision du taux HT](../../HisabPro_577_RAS_TVA_Taux_HT_Precision.zip)|[577](../../Test/rapport_ras_tva_taux_ht_577.md)|
|579|[Registre et exports](../../HisabPro_579_Registre_RAS_TVA_Exports.zip)|[579](../../Test/rapport_registre_ras_tva_579.md)|
|581|[Qualification et reprise](../../HisabPro_581_Qualification_RAS_TVA_Restauration.zip)|[581](../../Test/rapport_qualification_ras_tva_581.md)|
|583|[Cockpit et guide PDF](../../HisabPro_583_Cockpit_RAS_TVA_Guide.zip)|[583](../../Test/rapport_cockpit_ras_tva_583.md)|
|585|[Empreinte des exports](../../HisabPro_585_RAS_TVA_Empreinte_Exports.zip)|[585](../../Test/rapport_empreinte_ras_tva_585.md)|
|587|[Cohérence IS/états/lettrage](../../HisabPro_587_RAS_TVA_Coherence_IS_Lettrage.zip)|[587](../../Test/rapport_coherence_ras_tva_587.md)|
|589|[Année civile et livraison](../../HisabPro_589_Registre_Annee_Civile_Livraison.zip)|[589](../../Test/rapport_livraison_session_589.md)|

Le [ZIP cumulatif571–589](../../HisabPro_Session_20261018_RAS_TVA_571_589.zip)
contient les dernières versions de ces fichiers et le journal final, pas les
archives imbriquées ni le projet complet. Il complète la précédente livraison
553–569 ; il ne réapplique pas ses fichiers inchangés.
