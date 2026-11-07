# Qualification701 — contrôles documentaires du capital

Complément701 : contrôles arithmétiques C1 figés dans les nouvelles versions
(documentaire uniquement) : titres × nominal, sommes et écarts des capitaux,
rapprochement indicatif au solde des comptes 111 fournis et somme des pourcentages.
Inconnus préservés, écarts de centimes visibles sans ajustement ; anciennes
versions sans recalcul et brouillons distingués des valeurs conservées.
16 tests ciblés en 164,60s puis 213 tests connexes en 778.29s et 347 du socle
annuel en 1793.19s réussis, zéro échec/erreur/ignoré. Campagnes recouvrantes.
Build 6,14 s, 1 089 empreintes app/Test figées,108 fichiers SQL/bootstrap et moteurs comptables partagés inchangés ;
restauration de 83 tables/cinq fichiers et témoins indépendants préservés.
[Guide](../LIASSE_BALANCES_CONTROLES_CAPITAL_701.md), [rapport701](../../Test/rapport_balance_capital701.md).
Word/PDF de 5 pages/Excel de 5 feuilles et quatre cas humains Non testé. Guide consolidé de session : Word, PDF13pages, Excel7feuilles et16cas humains Non testé.
Un écart nul ne prouve pas l’exhaustivité juridique ou la conformité fiscale.
LIA-09D reste partiel ; RH/paie et point6 humain restent différés.


## Portée et résultats

Calculs Decimal avec une précision interne de 60 chiffres, suffisante pour les
100 lignes autorisées et les limites de titres/nominal. Les grands produits
restent exacts, y compris au-delà d’un montant financier saisissable. Ils ne
sont ni arrondis en flottant ni convertis en montant fiscal. Capital/pourcentages
inconnus et tableau vide donnent des contrôles indisponibles, jamais des zéros.
Le compte111 reprend la rubrique du bilan existant ; comparaison indicative
au capital social ou personnel fourni, sans attribution juridique présumée.

Les résultats sont ajoutés au snapshot071 lors de sa nouvelle création.
Lecture et exports utilisent le contrôle conservé, même si le calculateur
évolue. Un rejeu UUID identique renvoie la version existante sans recalcul.
Un contrôle ne peut pas remplacer les champs déclarés ou les métadonnées.
Le panneau porte explicitement sur la version conservée, pas le brouillon.
PDF/Excel/JSON partagent ces valeurs et leurs unités ; identité/logo actuels
restent hors empreinte historique. Aucune nouvelle migration ou règle fiscale.

## Tests réellement exécutés

- Cible :16 réussites en 164,60 s :10 cas arithmétiques, 2 API, 3 Edge, 1 restauration.
- Finale connexe :213 réussites en 778.29s ;0 échec/erreur/ignoré,30 avertissements existants.
- Socle annuel :347 réussites en 1793.19s ;0 échec/erreur/ignoré,30 avertissements existants.
- Les campagnes recouvrantes ne sont pas additionnées en cas uniques. Le guide consolidé a un jeu de balances cohérent avec les redevances B10 : résultat/CAF800MAD et actif/passif15800MAD, contrôlés indépendamment et par le moteur pur, sans PostgreSQL pour ce contrôle documentaire.
- Build6,14s code0 ;11Python compilés ;1 089 SHA app/Test figés.
- Témoins comptables/documentaires indépendants préservés ; socle annuel103
  distinct de la restauration104 :83tables/cinq fichiers, schéma/données/ACL/
  séquences et exports identiques, source préservée et cibles nettoyées.
-108 fichiers SQL/bootstrap et moteurs liasse/ETIC/import inchangés ; archives699 intactes.
- Guides Word/OOXML/PDF de 5 pages/Excel de 5 feuilles et quatre cas humains Non testé,
  données/oracles indépendants contrôlés. Capture mobile 390 inspectée,
  Office non ouvert. Aucun échec intermédiaire dans la cible 701.

## Limites et prochaine reprise

Aucune base réelle ou donnée comptable réelle modifiée. Aucune recette humaine,
conformité réglementaire ou aptitude à la production validée automatiquement.
Les écarts demandent une revue des sources, jamais un changement automatique
pour les annuler. La saisie des huit schémas manuels du catalogue existant est
développée/testée dans ces périmètres ; l’ETIC autonome normative complète et
les données fiscales restent partielles. Les autres tableaux automatiques/
assistés du mode indépendant restent à examiner sans déduire des flux inconnus.
RAS/EDI nécessitent les spécifications officielles. RH/paie et point6 différés.
