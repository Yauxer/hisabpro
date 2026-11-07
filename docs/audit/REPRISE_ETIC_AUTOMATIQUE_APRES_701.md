# Prochaine reprise : détails ETIC sur balances indépendantes

Analyse ciblée effectuée pendant la qualification finale701, sans modification
supplémentaire du code applicatif. Ne pas réappliquer697/699/701.

## Première cible : B11, détail du CPC

Le catalogue existe dans services/etic_service.py ; le B11 du mode comptable
est produit dans _automatiques à partir des écritures et du plan courant.
Ne pas appeler cette fonction pour une préparation indépendante : elle lirait
la comptabilité actuelle, qui n’est pas la balance externe conservée.

Source sûre : contenu.sources.n et n1 du snapshot071, montants décimaux sous
forme de chaînes. Ne pas repartir de preparation.soldes, qui contient des
flottants, ni du Journal, ni des factures de la société active.

Le snapshot actuel ne conserve pas les libellés individuels de comptes.
Ne pas présenter un libellé du plan actuel comme un libellé historique importé.
Afficher le numéro et le manque de libellé, ou concevoir une nouvelle source
explicitement renseignée et figée avant d’ajouter ces libellés.

Reprendre le signal disponible=False/motif du CPC conservé. Les balances
après solde technique des classes6/7 et présence119 sont déjà signalées par
preparer_balance_liasse : ne pas leur fabriquer un détail de charges/produits
nul. Si la source détaillée d’une ancienne version ou N-1 manque, laisser
les détails correspondants indisponibles.

Construire les lignes des classes6 et7 avec les signes explicites : débit
moins crédit pour les charges, crédit moins débit pour les produits. Conserver
les soldes inverses, sans reclassification. Les sommes et leur rapprochement
au CPC figé doivent montrer un écart éventuel, jamais le masquer. Préserver
l’absence d’un comparatif ; aucun N-2 ou mouvement brut n’est déduit.

Définir avant codage le moment de conservation de cette présentation : version
immuable, titre/source/méthode/auteur/date figés. Une ancienne préparation ne
doit pas recevoir des valeurs prétendument déjà archivées. Réutiliser les
contrôles de société/empreinte/UUID/version et les exports existants.

## Tests nécessaires pour ce lot futur

- Decimal exact avec charge, produit, avoir de sens inverse et grands montants.
- Balance N seule, N/N-1, ancienne source détaillée absente, clôture technique.
- Refus intersociété, consultation seule, conservation sans mutation du Journal.
- Rapprochement au CPC conservé et écart non nul visible, sans reclassement.
- PDF/Excel/ZIP/version/logo/manifeste identiques sémantiquement après restauration.
- Edge : sélection de version et réponses tardives, mobile, brouillons si présents.

Lancer d’abord les cibles puis la campagne connexe adaptée aux sources finales.
Consigner le début du lot et une baseline avant toute mutation.

## À examiner ensuite sans présumer les données

B1 peut être détaillé depuis les soldes des non-valeurs. B2/B2bis/B3/B5 nécessitent
une revue séparée des informations réellement disponibles : deux balances de
clôture ne justifient pas automatiquement acquisitions, cessions, dotations,
reprises ou sorties brutes. B4 ne fournit pas l’identité de l’émetteur depuis
le seul compte251. B12/B13/B14 et C3 demandent leurs données fiscales/historiques
certaines ; ne pas brancher le Journal courant pour combler un dossier externe.

Le modèle DGI exhaustif, RAS/EDI et la recette humaine restent des limites
séparées. RH/paie et point6 demeurent différés. Aucun contrôle arithmétique ne
constitue une certification ou une validation fiscale officielle.
