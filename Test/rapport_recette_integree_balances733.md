# Livraison733 — Cahier intégré et recette connectée des compléments

Un seul jeu fictif troisans, avec RAN cohérents et soldes/flux TVA rapprochés,
réunit B12/B13/B14/C3/N-2/extra. N :13comptes/25500, net6020/situation17520 ;
N1 :10comptes/16500, net3000/situation13200 ;N2 :4comptes/12000, net1000/
situation11000. RAN N1=1000 ;RAN N=1000+3000−distribution1000=3000.
B12 avant impôts7600, fiscal7900, IS théorique1580 au taux explicitement déclaré20.
B13 courant6600/base6900/après impôt déclaré5220, impôt N1 inconnu préservé.
B14 fins1000/500/200, récupérable700/net300, écarts0 ;extra C3 N3,50personnes,
bénéfices2000/résultat par titre60,20/distribution20, explicitement déclarés.
Aucun régime, salarié, paiement ou déclaration déposée déduits automatiquement.

Cahier professionnel complémentaire au cahier global existant, avec huit cas
complets :ID,module,objectif,prérequis,données,actions,résultat/écritures/fiscalité,
contrôles,statut,preuve attendue et champs réels vierges. Word/PDF10pages et
Excel14feuilles, un domaine parcas, graphique/formules/statuts de progression,
données et anomalies. TroisCSV etJSON reproductibles, oracles Decimal indépendants.
Les décisions et effectifs sont des hypothèses documentaires, pas scénario de
paie ou validation sociale. Les anciens cahiers/résultats humains restent intacts.

Échec initial25,39s :test comparait les chaînes0/10000 aux exports normalisés
0.00/10000.00. Attendu canonique corrigé, sans changer les chiffres ou l’application.
Quatre parcours réels ont ensuite réussi64,25s. Inspection des exports :63pages,
une page par petite donnée C3. Correction minimale de présentation :les quatre
valeurs de chaque période sont groupées, unités conservées ;aucune formule changée.
Nouveau parcours et module PDF :6réussites64,64s, dossier45pages,43feuillesExcel,
15fichiers vérifiés, logos/CRC/SHA/manifeste. CSV réellement importés par UI pour
admin/comptable ;lecteur consulte/exporte sans conservation. Tables métier hors
préparation, anciennes versions etsource N2 préservées. Capture390 etpage PDF C3
vraies sur données fictives livrées ;ne valent pas recette humaine.

Tests réellement exécutés : 6tests définitifs64,64s :1parcours API PostgreSQL104 et3Edge connectés (admin1440,comptable390,lecture390),2PDF historiques (pur/API SQLite).0échec/erreur/ignoré.4parcours précédents64,25s ;410connexes validés avant seule modification de pagination PDF, autres1171fichiers préservés sauf ce fichier.1173SHA suivis,4Python compilés,108SQL/bootstrap protégés. Cahier Word/PDF10pages/Excel14feuilles,8cas humains Non testé et3CSV équilibrés. Dossier exporté45pages au lieu de63,43feuillesExcel/15fichiers avec logos/manifestes.

Les campagnes se recouvrent :ne pas additionner en cas uniques. Les2tests PDF
historiques incluent une API SQLite ;les4nouveaux parcours utilisent PostgreSQL
natif isolé104 etEdge réel. Les410tests antérieurs couvrent le même code métier ;
seule cette pagination a changé après, validée par les6tests ciblés. Aucun nouveau
build frontend requis :tous les fichiers frontend sont identiques au build731
réellement réussi4,95s. Aucun nouveau SQL ou bootstrap changé.

Les PDF du cahier ont été rendus etinspectés (pages1/5/10), Word XML/Excel
formules/validations/chart vérifiés ;Office lui-même n’a pas été ouvert. Statuts
humains laissés Non testé. Pas de projet déclaré terminé ou prêt pour production.
Prochaine extension fiscale du mode externe :textes officiels intégraux et
justificatifs requis. Les tentatives MEF/DGI sont en timeout, index insuffisant ;
aucune règle nouvelle codée. RH/paie etpoint6 humain restent différés.
