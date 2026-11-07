# Reprise après713 : rattacher les clôtures aux comptes sources

713 conserve les mouvements déclarés B2/B2bis/B5 et leurs seules équations.
707/709/711 sont livrés séparément. Vérifier journal/archives/preuves et ne pas
réappliquer ces étapes. RH/paie et point6 humain restent différés.

Le prochain lot doit conserver un rattachement explicite de chaque ligne de
mouvement à un compte présent dans la balance N figée. Le choix vide signifie
non rattaché, sans auto-attribution à partir d’un nom ou d’un montant. Plusieurs
lignes peuvent appartenir au même compte ; leurs clôtures déclarées connues
sont sommées puis comparées au solde du même compte. Une clôture inconnue ou
l’absence de ligne rattachée ne devient jamais0. Les lignes non rattachées et
comptes sources sans détail restent visibles, même si un autre écart vaut0.

Périmètres techniques existants à réutiliser depuis etic_service : B2 comptes
21/22/23, B2bis281/282/283 et B5 comptes15/29/39/45/59. Ce sont les périmètres
HisabPro actuels à expliciter, sans inventer une obligation réglementaire ou
modifier les moteurs comptables. Solde débiteur pour B2 ; créditeur pour B2bis/B5,
avec signes inverses préservés. Les comptes et montants viennent de contenu.sources.n,
jamais du Journal ou du plan actuels. N-1 ne prouve pas l’ouverture des flux.

Créer un bloc distinct, sans modifier les déclarations713. Conserver la SHA du
bloc de mouvements et celle des sources N avec les rattachements/contrôles/auteur/
UTC/version parent. Si les mouvements ou sources changent dans une version
suivante, l’ancien contrôle doit rester intact mais explicitement ancien/à refaire.
Ne pas recalculer silencieusement ni réutiliser un choix de ligne devenu ambigu.
Le formulaire montre le contexte actuel et distingue les contrôles conservés ;
les exportations gardent les anciennes clôtures/références de leurs contrôles.

Prévoir normalisation des indices de lignes stricts et uniques, trois tableaux
complets et aucune omission masquant une ligne. SHAparent/UUID/rejeu avant calcul,
verrou/concurrence, droits/sociétés/MAD, NaN/inconnus/grands nombres, multi-lignes,
source absente, périmètre invalide, nouveaux mouvements rendant ancien le contrôle,
Edge mobile/réponses tardives/brouillon, PDF/Excel/ZIP/logo et restauration native.
Un rapprochement exact ne prouve pas la complétude juridique ou fiscale.
La fiscalité autonome et les spécifications officielles restent distinctes.
