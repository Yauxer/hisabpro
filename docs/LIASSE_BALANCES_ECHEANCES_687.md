# Documenter les créances et dettes d’une balance importée

Depuis **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
sélectionner une préparation conservée puis ouvrir **Compléter les échéances
documentaires des balances**. Ce complément exploite seulement la balance N
de cette version. Il ne lit pas les factures ou le Journal de la société.

1. Choisir un compte dans **Compte à documenter**. Le filtre permet de retrouver
   un compte ; au-delà de100résultats, préciser le filtre. B6/B7 désignent ici
   les sections de préparation issues de la sélection ETIC déjà présente.
2. Renseigner seulement les montants connus : plus d’un an, moins d’un an,
   échues, puis analyses devises, État/organismes publics, entreprises liées
   et effets. **Un champ vide reste inconnu.** Un zéro explicite est conservé.
3. Indiquer la **Justification / référence de source** des montants saisis.
   Ne pas déduire une échéance de la seule date comptable. La ventilation
   concerne la fin de période conservée ; aucune date n’est calculée ici.
4. Les trois catégories d’échéance ne peuvent pas dépasser le solde du compte.
   Le reliquat reste non qualifié. Les quatre autres analyses sont plafonnées
   séparément au même solde ; elles peuvent se recouper et ne s’additionnent pas.
5. Passer aux autres comptes pour conserver leur saisie dans le même formulaire,
   confirmer puis **Conserver les compléments dans une nouvelle version**.
   Tous les comptes renseignés sont enregistrés ensemble. Le formulaire doit
   être confirmé à nouveau après une modification de montant ou justification.
6. La nouvelle version est sélectionnée automatiquement. Rouvrir son panneau
   pour relire les montants et le reliquat recalculés par le serveur. Les totaux
   affichés pendant la saisie correspondent à la version précédemment conservée.
7. Exporter cette version en **PDF** ou **Excel**. Les compléments, justifications,
   inconnus et reliquats y figurent avec les empreintes de la version et de son
   parent. Le logo et l’identité actuels restent hors de ces empreintes.

La version source reste intacte : balances, bilan, CPC, ESG et période ne sont
pas recalculés lors du complément. Pour corriger ou retirer un classement,
ouvrir la version concernée, modifier/vider les champs puis conserver une
nouvelle version ; les anciennes restent consultables. Une même demande rejouée
avec sa clé ne crée pas une deuxième version. Deux créations simultanées sont
sérialisées avec la numérotation des préparations ordinaires.

## Exemple exclusivement fictif

Créance3421 de8000MAD : plus d’un an2000, échues1000, moins d’un an inconnu.
Le montant ventilé est3000 et le reliquat5000. Rien ne classe ce reliquat en
échues. Dette4411 de3000MAD :1000dans chacune des trois catégories, reliquat0.
Un montant en devises et un montant d’entreprise liée peuvent concerner la même
créance ; leur somme n’est pas une nouvelle échéance.

Les soldes de sens inverse restent visibles, sans ventilation dans ce panneau.
Une ancienne version sans sources détaillées invite à réimporter explicitement
la balance. Aucun intitulé actuel ou tiers supposé ne remplace une source absente.

Le rôle **Lecture** consulte les champs désactivés et télécharge les exports.
Seuls les rôles autorisés à écrire créent une nouvelle version. Les autres
sociétés sont inaccessibles et l’empreinte source est contrôlée avant la création.
La création du complément est limitée à une société explicitement enMAD.

## Installation et limites

Aucune nouvelle migration. La table immuable071 des préparations doit déjà
exister ; les bancs récents tournent sur un PostgreSQL103 isolé. Le cumul687
contient les dépendances applicatives. Aucune base réelle n’a été utilisée.

Il s’agit d’une préparation documentaire. Les autres analyses ETIC, flux du
financement, liquidations et annexes fiscales restent à compléter. Ce panneau
ne rend pas le dossier officiellement prêt à déposer et n’alimente pas le Journal.
RAS/EDI restent conditionnés aux spécifications officielles ; RH/paie différées.

[Word de recette](recette/RECETTE_ECHEANCES_BALANCES_687.docx),
[PDF](recette/RECETTE_ECHEANCES_BALANCES_687.pdf),
[Excel de suivi](recette/RECETTE_ECHEANCES_BALANCES_687.xlsx),
[CSV fictif](recette/BALANCE_FICTIVE_ECHEANCES687.csv).
Sept cas humains Non testé, distincts des résultats automatisés du
[rapport687](../Test/rapport_balance_echeances687.md).
