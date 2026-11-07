# Préparer le rapprochement mensuel des retenues TVA opérées

Cette vue est une préparation interne en lecture seule. Elle ne dépose aucune
déclaration, ne prouve aucun versement et ne calcule pas un reste à payer.
Les RH et la paie ne sont pas concernées. Les captures libres et les retenues
historiques non qualifiées ne sont pas incluses.

1. Ouvrir Comptabilité → Déclaration TVA, puis « Préparation mensuelle des
retenues opérées ». La même vue est accessible dans Liasse fiscale → Retenues
TVA. Elle reste utilisable lorsque le solde de déclaration automatique est
indisponible pour des retenues guidées.

2. Choisir le « Mois de versement prévu ». Par exemple, novembre 2026 sélectionne
les paiements d'octobre 2026. Janvier 2027 sélectionne décembre 2026, indépendamment
des dates de l'exercice comptable. Le mois retenu et celui des paiements sont
affichés ensemble. La période est modifiable sans changer le registre annuel.

3. Comparer les quatre montants : toutes les captures du mois de paiement,
les captures encore actives, les actives dont l'OD est validée, et les captures
annulées. Les deux derniers montants ne doivent pas être additionnés au total
actif. Une OD à valider n'est pas présentée comme définitive. Une source de
montant inconnue reste « À vérifier », avec sa partie certaine.

4. Lire les références des factures, paiements, OD, comptes choisis et
attestations déclarées. Rapprocher ces références des pièces conservées et du
bordereau administratif effectivement utilisé. Les annulations postérieures
au mois restent visibles à leur état courant : vérifier toute régularisation
nécessaire si un bordereau a déjà été déposé. Aucune déduction automatique n'est
appliquée à un bordereau antérieur.

5. Télécharger CSV, Excel ou PDF. Le PDF et l'Excel reprennent le logo enregistré
dans les paramètres de la société. Les trois formats contiennent la même
empreinte des données SHA-256. Cette empreinte identifie les données exportées ;
elle n'est ni une signature ni le hash du fichier téléchargé. Si une OD, une
capture ou l'identité de société a changé, actualiser avant d'exporter.

6. Pour vérifier sur une société fictive : préparer trois captures opérées de
75 MAD, dont une annulée, une active avec OD validée et une active avec OD à
valider. Ajouter une capture subie sur vente de 75 MAD. Le mois suivant doit
afficher trois captures opérées seulement : saisies 225 MAD, actives 150 MAD,
actives avec OD validée 75 MAD, annulées 75 MAD. La vente reste dans le registre
annuel séparé. Aucun de ces chiffres ne justifie un reversement effectif.

Prérequis : installation du dossier 099 et capture guidée existante. Si 099 manque,
un message le signale, sans migration automatique ni faux total nul. Les rôles
admin, comptable et consultation peuvent lire et exporter. Cette préparation
est distincte du dossier fiscal annuel archivé et des tableaux T1…T25 internes.

La déclaration TVA complète, le suivi des justificatifs de versement et
l'imputation restent à terminer. L'installation sur la base utilisateur et
la recette humaine ne sont pas validées par ce guide.
