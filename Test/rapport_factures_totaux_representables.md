# Factures : montants calcules representables avant mutation (261)

Analyse : les champs individuels finis ne garantissaient pas que le moteur Decimal pouvait quantifier les produits et sommes. POST commitait avant les calculs de reponse ; PATCH pouvait enregistrer un brouillon impossible a relire.

Preuves reelles avant correction, API authentifiee et PostgreSQL nonce uniquement : POST quantite1e308 prix10 donne500 avec mutation (1failed19.92s) ; PATCH retourne200 et conserve les nouvelles valeurs impossibles a calculer (1failed8deselected20.07s).

Correction minimale dans routers/factures.py : une projection des valeurs proposees utilise le moteur TVA/Decimal et les montants de lignes existants avant toute mutation ou reservation de numero. DecimalException et OverflowError produisent422, ainsi que les resultats non finis. Aucun plafond arbitraire, changement de precision, formule ou taux fiscal. Pour PATCH, seuls les champs utilises par les calculs declenchent ce controle ; les notes historiques restent modifiables sans recalcul ni reparation. Protections de validation/comptabilisation conservees.

Tests executes par le principal avec PYTHON_DOTENV_DISABLED=1 :
- Premier apresfix :8passed1failed20.39s ; erreur de fixture GET detail inexistant405.
- Suite avec documents valides, fact4 et2Edge achat/vente :118passed1failed90.58s ; seule la fixture normale omettait exercice obligatoire dans GET liste. Les refus de limites et les connexes passent ; cette suite n'est pas declaree verte.
- Fixture corrigee : Test/run_unit_tests.py Test/test_factures_totaux_representables.py Test/test_patch02b_tva_service.py Test/test_conform1_tva_frais.py :30passed18.62s,25warnings,exit0.
- Ajout test historique notes independantes : relance finale Test/run_unit_tests.py Test/test_factures_totaux_representables.py :10passed20.27s,25warnings,exit0.
- Compilation routers/factures.py et nouveau test : exit0.

Les10cas couvrent POST/PATCH produits non representables, valeur finie1e27 incompatible avec la quantification actuelle, transport et emballage extremes, normal/gratuit et notes seules sur un historique fictif anormal. Chaque refus compare toutes colonnes factures/lignes/ecritures/articles/stock. Oracle normal independant : HTcommercial60, financier57, TVA11.40, TTC68.40 avec remise10%, escompte5%, transport10 etemballage5.

Limites : anciens montants anormaux non repares ; leur lecture reste a auditer separement. Exports aux montants extremes, autres conversions et contexte de precision different ne sont pas declares valides par cette suite. Aucun test ou commande contre le PostgreSQL reel de l'utilisateur, aucune donnee comptable reelle touchee. Prochaine action : consolidation complete des sources stables.
