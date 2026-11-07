# Révision du scénario de recette RAS —653

Consultation ciblée du19octobre2026, pendant la consolidation651. Il s'agit
de vérifier les hypothèses du **jeu de test**, pas d'ajouter un nouveau calcul
fiscal ni de refaire les audits de la liasse.

Le passage officiel indexé de la [NC735 du MEF, page24](https://www.finances.gov.ma/Publication/dgi/2024/Note-Circulaire735LF2024.pdf)
décrit une exclusion pour les petites prestations, avec un plafond de5000MAD
TTC par opération et une limite de50000MAD TTC mensuelle par fournisseur.
L'ouverture directe du PDF a échoué ; ce constat porte sur le passage indexé,
pas sur une lecture intégrale de la note.

Le [BO7465bis du16décembre2025, page imprimée3834](https://www.finances.gov.ma/Publication/db/2025/BO_7465-bis_fr.pdf)
présente l'extension2026 de l'article117-V et signale que la suite relative
aux exclusions n'est pas modifiée dans cette disposition. Le rapprochement
avec la NC735 est une **inférence de contrôle du scénario**, pas une validation
exhaustive de l'éligibilité fiscale d'un dossier2026.

Les ouvertures actuelles du [CGI2026 MEF](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf)
et du [CGI2026 TGR](https://www.tgr.gov.ma/wps/wcm/connect/9856b6bb-dee8-4578-bfe8-ef1521dcc80f/CGI%2B2026%2BFR.pdf?MOD=AJPERES)
ont échoué. Les pages lues lors des sessions précédentes restent des preuves
historiques ; elles ne sont pas présentées comme une nouvelle lecture complète.
Le passage indexé du CGI relatif aux paiements en espèces n'a pas été confondu
avec l'exclusion de retenue TVA. Aucun binaire officiel téléchargé ou SHA revendiqué.

## Conséquence pour le jeu humain

Le cas649 initial utilise une société vierge, une facture1200TTC et aucun autre
fait documenté de cumul. Le calcul comptable était exact, mais l'option
« aucune exclusion après contrôle » ne doit pas être implicitement justifiée
par un cumul inventé. Ce cas reste un vecteur arithmétique historique.

La révision conserve les douze parcours et leurs statuts humains vierges, avec
une facture12000TTC et une quote-part6000TTC : toutes deux dépassent le petit
montant évoqué ci-dessus. Capital100000, TVA de quote-part1000, retenue du jeu750,
trésorerie5250. Aucun montant de cumul mensuel antérieur n'est ajouté. Les
autres qualifications demeurent explicitement supposées pour le laboratoire,
et restent à vérifier pour tout dossier réel. Les éventuels autres traitements
fiscaux ne sont pas déterminés par cette annexe de documents RAS TVA.

## Déclarations restant à documenter

Le [rappel MEF/DGI du23août2024](https://www.finances.gov.ma/fr/pages/detail-actualite.aspx?fiche=6947)
indique que les spécifications de la retenue TVA et de son relevé détaillé
sont proposées dans le menu latéral de SIMPL-TVA. Cela fournit une piste
précise pour obtenir les modèles, pas leur contenu ni leur version actuelle.
Aucun accès authentifié, contact ou dépôt n'a été effectué. Aucun imprimé,
XSD, droit d'imputation, remboursement ou preuve de versement n'est inventé.

Aucune migration ou règle applicative modifiée. Anciens ZIPs conservés intacts ;
Word/PDF/Excel, données et oracle révisés dans un nouveau différentiel653.
