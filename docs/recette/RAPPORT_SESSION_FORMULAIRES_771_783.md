# HisabPro — bilan de session :formulaires et recette automatisée

Cinq améliorations livrées :nom de banque libre persistant ;tiers récemment créés en tête ;notes facultatives du bon de commande ;date de facture choisissable depuis le BL ;autocomplete du compte fermé au changement de focus pour préserver le clic Enregistrer sur mobile.

Tests réellement exécutés sur Edge et PostgreSQL temporaire isolé :41tests paramétrés distincts réussis après reprises,67tentatives dont11échecs initiaux conservés. Aucun ignoré final. Les diagnostics mobile -k390 avaient1cas désélectionné explicitement,ensuite exécuté danslacampagne complète. Les693tests de la précédente session ne sontpas additionnés. Dernier build Vite0 en5,01s,avec avertissement de poids du bundle.

Parcours exacts du cahier :société et paramètres,banque,7tiers/3articles,achats/acomptes/paiements/lettrage,devis/BC/BL/facture,chèque/avoir/crédit/secondevente,inventaire,rôles etseconde société protégée. Sous-parcours marchandises :14écritures définitives/33lignes,débit=crédit177000MAD,stock60auCMUP110,comptabilisation6600en3111/6114,bilan provisoire44000 etrésultat22100. Ce ne sontpas lesrésultats annuels complets du cahier.

CAP-01est saisi séparément dansune société vierge :200000MAD,enBQ,2lignes5141/1111,date etpièce01/01/2025,référenceCAP-01,libellés duplan respectés ;brouillon puisvalidation,exportFECréduit etbilan200000/résultat0. Il n’estpas ajouté rétroactivement aux14écritures déjàvalidées.

Le dernierlot a reproduit4fois la perte de clicmobile. Les traces montrent mousedown surEnregistrer,puis apparition tardive de2libellés de compte aprèsfermeture desautocomplete,déplacement38px etmouseup horsbouton. Unessai CSS nonconcluant aété retiré. Correctionracine :fermer l’autocomplete au blur. Aucun clicforcé,aucun retry intégré,aucundélai ajouté. Dernière campagne6tests réussis en98.43s,avecdiagnostics ;leséchecs antérieurs restent danslesJUnit.

Suivi individuel :32fiches complètes rapprochées depreuves,230nonqualifiées individuellement et10bloquées dansla source. Lescas nonqualifiés ne sontpas présentés comme toussans tests techniques. Lesanciens classeurs de recette humaine sont inchangés. Lescomptes etbases de test sont fictifs ;aucune base PostgreSQL réelle utilisée,aucun backend oumigration modifié.117protections restent àvérifier dansle contrôle final.

Limites :recette humaine etproduction nonvalidées ;RH/paie etpoint6 différés ;EDI officiel etdocuments DGI manquants restent bloqués. L’incident de reload Lettrage769 reste ouvert,malgréles nouveaux replays réussis. Les autresopérations annuelles,immobilisations,services,effets etfiscalité doivent être rejoués dansleurordrecomptable.

Reprise :utiliser jeu_donnees_recette.json etles suivis sansréappliquer lescorrectifs ;organiser une nouvelle société pour le parcours annuel chronologique des50opérations. Ne pas comptabiliser rétroactivement lecapital oudespaiements antérieurs dans le sous-parcours dontlesécritures sont définitives.
