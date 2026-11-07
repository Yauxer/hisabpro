# Livraisons de session18h12UTC


## Session du 11 octobre 2026 — reprise 18h12 UTC — lots391 à398

- [Globale391](../Test/rapport_consolidation_globale_391.md) :3282 réussites et **un échec** de délai de connexion Edge sur3283cas,4251,60s;703empreintes stables. Reprise isolée du fichier :8réussites39,345s sans changement. La preuve globale en échec est conservée; cause du délai non démontrée.
- [Rapprochement392](../Test/rapport_rapprochement_ventilation_392.md) :une ligne réelle du relevé pour plusieurs lignes bancaires d'une ventilation native immédiate, choix explicite, dépointage atomique, gardesSQL/permissions/concurrence/clôture. Migration084 additive et manuelle; modèles/main et migrations antérieures inchangés. Sans084 les rapprochements simples restent disponibles.
- [Année393](../Test/rapport_annee_rapprochement_393.md) :facturation→validation→règlement→lettrage→clôture→à-nouveaux;relevé2025 trois opérations pour cinq lignes,solde1000/flux1480;en2026 deux compléments120,solde1000/flux240;comptabilité originale préservée.
- [Guide394](../Test/rapport_guide_rapprochement_394.md) :Word/PDFv13,31pages,18fiches/17Non testé;annexeExcel3feuilles/8casNon testé. Contrôles techniques des fichiers réussis, MicrosoftWord/Excel non ouverts.
- [Restauration398](../Test/rapport_sauvegarde_ventilation_398.md) :deuxPGnonce distincts,pg_dump/pg_restore,huit tables comparées,liens et gardes restaurés,rôleLOGIN application et cible non vide vérifiés. Aucun dump livré.
- [Consolidation397](../Test/rapport_consolidation_bancaire_397.md) :**92réussites**,zéroéchec/erreur/ignoré,298.918s,sources finales figées;compilation et build0. Elle couvre les modules bancaires connexes, l'année et la restauration, et ne constitue pas une nouvelle globale de tous les modules. Les suites se recoupent et ne sont pas additionnées.

Couverture conservée :70fonctions,15terminé/46partiel/5absent/4bloqué;73demandes,40terminé/30partiel/2absent/1bloqué. Le rapprochement à une ligne est désormais disponible pour les ventilations natives immédiates. Instrument unique chèque/effet,escompte/frais,moteur automatique exhaustif et historiques ambigus restent partiels. Paie définitive/EDI toujours bloqués par qualification officielle.

Aucun PostgreSQL réel ni données comptables réelles utilisés. **084 non appliquée sur installation réelle. Point6 en attente utilisateur.** Développement global partiel;tests automatisés validés sur leurs périmètres;globale391 en échec malgré reprise isolée réussie;recette utilisateur à effectuer;mise en production non validée.

Prochaine reprise :nouvelle globale sur les sources après392, surveiller le délai de connexion observé en391,puis variantes annuelles et instruments/frais bancaires restant au périmètre. Ne pas réappliquer392/393/398. Attendre le retour utilisateur pour le point6.

Livraisons : [391](../HisabPro_Patch391_Consolidation_Globale_Reglements.zip), [392](../HisabPro_Patch392_Rapprochement_Ventilations.zip), [393](../HisabPro_Patch393_Recette_Annuelle_Bancaire.zip), [394](../HisabPro_Patch394_Guide_Word_PDF_Recette_Bancaire_Excel.zip), [397](../HisabPro_Patch397_Consolidation_Bancaire_Finale.zip), [398](../HisabPro_Patch398_Sauvegarde_Restauration_Ventilations.zip).

[Guide Word](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx), [PDF](guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf), [annexe Excel](recette/ANNEXE_RECETTE_RAPPROCHEMENT_VENTILATIONS.xlsx), [activation recette](INSTALLATION_RECETTE_RAPPROCHEMENT_VENTILATIONS_392.md).

Complément399 :[annulation après rapprochement](../Test/rapport_annulation_rapprochement_399.md),deux vraisEdge vente bureau/achat mobile réussis en racine. Origines,contrepassations et relevé préservés;dépointage explicite possible,lot annulé non reproposable. Aucun changement produit après397.

[ZIP399](../HisabPro_Patch399_Annulation_Apres_Rapprochement.zip).

Complément400 :[RAS et banque](../Test/rapport_ras_rapprochement_400.md),deux casAPI/PGnonce vente/achat réussis en racine. Banque210 ventilée90/120,retenue10 indépendante conservée;aucune règle fiscale nouvelle. Code produit inchangé après397.

[ZIP400](../HisabPro_Patch400_RAS_Rapprochement_Bancaire.zip).


## Complément401 — protection du numéro technique

[Rapport401](../Test/rapport_namespace_ventilations_401.md) :saisie manuelle du numéro natif reproduite201 puis refusée422 au POST public;flux natif et numéros commerciaux préservés. 89tests racine réussis,202.546s,zéroéchec/erreur/ignoré;compilation0. Avant correction:2échecs et1réussite,créations201du format technique reproduites. La suite397 précède cette correction du seulcommercial.py;autres sources397 identiques. Historiques non modifiés,aucune migration supplémentaire,statuts de couverture conservés. Nouvelle globale des sources finales restant à exécuter.

[ZIP401](../HisabPro_Patch401_Numero_Technique_Ventilation.zip). Le cumulatif396 précédent couvre les neuf lots antérieurs;le cumulatif final402 inclura ce complément.
