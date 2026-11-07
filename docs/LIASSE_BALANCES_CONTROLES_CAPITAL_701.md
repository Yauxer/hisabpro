# Vérifier le capital déclaré dans les annexes ETIC

Version 701 du 21 octobre 2026 — données fictives, environnement isolé uniquement.

Après les tableaux documentaires des lots 697/699, HisabPro conserve désormais
des contrôles arithmétiques C1 dans les nouvelles versions des annexes.
Ils comparent les nombres déclarés ; ils ne calculent pas une répartition
juridique présumée et ne corrigent pas les données ou la comptabilité.

## Où consulter les contrôles

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
choisir une version puis **Documenter les autres annexes ETIC**, sélectionner
**C1** et ouvrir **Vérifier les données chiffrées du capital conservé**.

Le panneau présente les données de la version conservée. Modifier les champs
du brouillon ne change pas ce panneau. Pour obtenir des contrôles sur la nouvelle
saisie, confirmer puis conserver les annexes dans une nouvelle version.
Une ancienne version sans contrôle reste identifiée comme telle : aucun
résultat ne lui est attribué automatiquement à sa lecture.

Pour chaque ligne, le produit titres × nominal est calculé lorsque les deux
facteurs sont connus. L’écart est capital déclaré moins ce produit, seulement
si le capital est également connu. Les données saisies restent intactes,
même si l’écart est non nul.

La somme des capitaux déclarés est disponible seulement s’il existe au moins
une ligne et si tous les capitaux des lignes sont connus. Elle est rapprochée
à titre indicatif du solde crédit moins débit des comptes 111 de la balance N
conservée. Ce préfixe est celui de la rubrique Capital social ou personnel du
bilan HisabPro existant. Les informations détaillées absentes ne deviennent
pas un solde nul. Le contrôle ne lit pas le Journal courant et ne modifie pas
le capital renseigné dans les paramètres de la société.

La somme des pourcentages et son écart par rapport à 100 sont présentés lorsque
tous les pourcentages des lignes sont connus. Une somme de 100 n’établit ni
l’exhaustivité des associés ni la validité juridique des titres. Aucune règle
fiscale nouvelle, condition d’immatriculation ou obligation documentaire n’est
créée par ce contrôle arithmétique.

Un tableau vide, même déclaré néant, ne devient pas une somme nulle. Un zéro
explicitement saisi reste un vrai zéro. Si une composante manque, le calcul
concerné reste Indisponible. Les calculs sont exacts en décimal et conservés
dans le snapshot ; ils ne sont pas rejoués à la lecture ou à l’export.

## Jeu de recette et calcul indépendant

Utiliser la société fictive en MAD et les balances 695 décrites dans le guide 699.
Capital des comptes 111 N : 10 000 MAD. Préparer C1 avec l’associé fictif et la
source **Registre A fictif699** : 100 titres, nominal 100 MAD, capital 10 000 MAD,
pourcentage 100. Conserver les annexes dans une nouvelle version.

Attendu : 100×100=10 000 MAD ; écart de ligne 0 MAD ; somme des capitaux 10 000 MAD ;
écart avec la balance 111 : 0 MAD ; somme des pourcentages 100 % et écart 0 %.
Ces égalités décrivent les nombres fictifs déclarés, pas la conformité du dossier.

Modifier le capital en **9999,99** et le pourcentage en **99,99**. Avant
conservation, le panneau conserve les anciens résultats. Après confirmation et
conservation : produit inchangé 10 000 MAD, capital déclaré 9999,99 MAD,
écart de ligne −0,01 MAD et écart avec la balance −0,01 MAD ; pourcentages 99,99 %
et écart par rapport à 100 de −0,01 %. Les champs ne sont pas ajustés automatiquement.
La version précédente garde ses écarts nuls.

Dans une nouvelle version, laisser le nominal, le capital déclaré et le
pourcentage vides. Avec désignation et source toujours présentes, la saisie
documentaire est conservable. Le produit, l’écart de ligne et les sommes/écarts
concernés restent indisponibles. Le solde 111 connu de 10 000 MAD reste visible.

Les données exactes et les attendus indépendants se trouvent dans
**DONNEES_CONTROLES_CAPITAL701.json**. Les grands produits des tests automatisés
servent à éprouver la précision, sans correspondre à des données réelles.

## Exports et droits

PDF, feuille Excel **Contrôles capital** et JSON des annexes dans le ZIP reprennent
les résultats conservés. Les valeurs sont exportées en texte exact pour préserver
les centimes, grands produits et pourcentages. Les pièces et autres compléments
restent attachés ou conservés selon les règles des lots précédents.
Le lecteur consulte les contrôles et télécharge les exports sans pouvoir modifier
la saisie ou conserver une nouvelle version.

## Cahier de recette humaine

Prérequis communs : société et données fictives ci-dessus, administrateur ou
comptable ; un lecteur pour le dernier cas. Aucune écriture ou liquidation
fiscale attendue. Capturer systématiquement version et empreinte.

| ID | Actions et données exactes | Résultat, contrôle et preuve attendus | Statut humain |
|---|---|---|---|
|C701-01|Saisir C1 : 100 titres,nominal 100,capital 10000,pourcentage 100,associé/source fictifs. Conserver puis ouvrir le panneau de contrôle.|Produit 10000 MAD ; somme des capitaux 10000 MAD ; comparaison à la balance 111 : 10 000 MAD ; trois écarts nuls. Source, version et empreinte visibles. Capture et JSON.|Non testé|
|C701-02|Modifier capital 9999,99 et pourcentage 99,99. Observer avant conservation ; confirmer puis conserver et rouvrir les contrôles.|Avant :ancienne situation. Après :produit 10000 MAD et écarts de ligne/balance −0,01 MAD ; somme 99,99 % et écart −0,01 %. Ancienne version intacte, aucune correction automatique. Captures comparées.|Non testé|
|C701-03|Dans une nouvelle saisie, laisser nominal,capital,pourcentage vides ; garder 100 titres,associé/source puis conserver.|Calculs et sommes concernés Indisponible, jamais 0. Solde 111 fourni toujours 10000 MAD. Aucune écriture créée. Capture des inconnus et JSON.|Non testé|
|C701-04|Avec un lecteur, consulter la version du cas 02 et télécharger PDF/Excel/ZIP avec logo de test.|Modification interdite ; valeurs conservées exactes dans PDF, feuille Contrôles capital et JSON. Version/logo/source cohérents. Garder les exports, manifeste et capture des droits.|Non testé|

Ces quatre cas restent Non testé pour votre recette utilisateur. Les tests
automatisés sont consignés séparément dans Test. La revue juridique/comptable,
les autres états ETIC/fiscaux et la mise en production ne sont pas validés par
ces calculs. RH/paie et point 6 humain restent différés.
