# Reprise après709 : cessions/retraits B3 et mouvements ETIC

707 et709 livrent le détail des participations et les déclarations des émetteurs.
Ne pas les réappliquer. Lire le journal actif et vérifier les ZIPs/preuves récents.

La prochaine cible indépendante est une saisie documentaire des cessions/retraits
B3 de l’exercice N. Le catalogue existant et etic_service._section_b3 emploient
date, désignation, type, valeur d’entrée, VNA, prix et différence prix−VNA.
Ces données ne sont pas déductibles des seules balances N/N-1. Réutiliser ces
colonnes dans un formulaire explicitement interne, avec référence de source,
montants inconnus préservés et contrôle arithmétique figé prix déclaré−VNA déclarée.
Ne pas générer une écriture, une imposition ou une réintégration fiscale depuis
cette saisie. Une différence comptable indicative n’est pas un résultat fiscal.

Réutiliser le service documentaire immuable et le formulaire partagé ; conserver
catalogue/note/auteur/UTC/source/UUID. Les dates facultatives restent facultatives ;
les dates incohérentes avec l’exercice peuvent être diagnostiquées sans inventer
une date. Les types ne sont pas inférés. Prix/VNA manquants donnent un contrôle
indisponible, jamais0. Les lignes complètes doivent être identifiables et sourcées.
Les contrôles conservés restent distincts du brouillon. Ne pas reconstituer le
registre des immobilisations depuis le Journal réel pour une balance externe.

Les mouvements B2/B2bis/B5 restent séparés : ouverture, acquisitions/augmentations,
sorties/diminutions, dotations/reprises et clôture doivent venir de sources
explicites. Une variation de solde ne suffit pas à identifier ces flux. Le B3
saisi ne prouve pas à lui seul le rapprochement des mouvements B2/B2bis.

Prévoir calculs Decimal/NaN/infinis/inconnus, cas de moins-value et écart d’un
centime, périodes/droits/sociétés/empreinte/rejeu/concurrence, Edge mobile et
brouillon/réponses tardives, PDF/Excel/ZIP/logo/manifeste, restauration froide.
Vérifier les règles nouvelles sur sources officielles si le périmètre dépasse
la simple saisie documentaire et l’arithmétique déjà présentes dans le code.
Les sources fiscales B12/B13/B14/C3 restent distinctes et partielles.
RH/paie et point6 humain restent différés ; recette humaine/production nonvalidées.
