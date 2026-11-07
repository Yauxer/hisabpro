# Factures correspondantes entre sociétés

Le lot635 permet de préparer chez une société acheteuse le brouillon d'achat
correspondant à une vente validée chez une société vendeuse. Les droits et
comptabilités restent propres à chaque société. Ce mécanisme ne constitue pas
une consolidation ou une qualification fiscale de groupe.

## Préparer une vente et sa correspondance

1. Configurer les deux sociétés et leur comptabilité en MAD. Créer les tiers et
   les articles dans chacune ; ne pas réutiliser un identifiant technique de
   l'autre société. Préparer les exercices et périodes nécessaires.
2. En étant administrateur des deux sociétés, enregistrer leur association dans
   **Paramètres → Sociétés liées**, selon le [guide633](SOCIETES_LIEES_633.md).
3. Créer puis valider une facture de vente pour le client de cette liaison. Une
   proforma, un brouillon ou une vente annulée ne peut pas servir de source.
4. Ouvrir le détail de la facture puis **Correspondance entre sociétés**.
   Choisir la liaison et associer explicitement chaque ligne à un article de
   l'acheteur. Les références d'articles ne sont pas rapprochées par leur nom.
5. Déclarer la nature TVA de l'achat et le pourcentage propre à cette facture.
   Ce choix ne qualifie pas fiscalement l'opération. Le prorata annuel de
   l'acheteur sera appliqué par sa comptabilité ordinaire.
6. Cliquer **Vérifier le brouillon d'achat**. Vérifier l'acheteur, son fournisseur,
   la date, son exercice, les articles, les montants et les frais ; confirmer la
   vérification puis **Créer le brouillon chez l'acheteur**.
7. La référence fournisseur du brouillon est le numéro de vente d'origine. Le
   numéro interne d'achat n'est attribué qu'à sa propre validation. La date de
   la facture est conservée ; son exercice est déterminé avec le calendrier de
   l'acheteur, y compris s'il diffère de celui du vendeur.

La création du brouillon et du lien d'origine se fait dans une seule transaction.
Une répétition de la même commande retrouve le même document. Une nouvelle clé
ne permet pas de créer un second achat pour la même vente. Un échec ne laisse
pas un brouillon orphelin. Le stock et le Journal de l'acheteur restent inchangés
à cette étape.

## Valider et comptabiliser dans chaque société

Basculer vers l'acheteur avec le sélecteur de société, sélectionner **l'exercice
acheteur indiqué par le suivi**, puis ouvrir sa facture dans la liste des achats.
Un achat daté de2026 peut appartenir à2027 dans son calendrier décalé ; ne pas
chercher uniquement dans l'année civile de la date. Vérifier le brouillon. Utiliser les commandes ordinaires de
validation et de génération d'écriture, puis valider le brouillon comptable au
Journal. La vente suit ses propres commandes chez le vendeur. Aucun compte,
statut de paiement ou écriture définitive de l'autre société n'est modifié par
le bouton de correspondance.

Exemple fictif : deux lignes de200 et300MAD HT, TVA20%, TTC600MAD, avec TVA
d'achat déclarée100% et prorata100% dans le jeu de laboratoire :

| Société | Débit | Crédit |
|---|---|---|
|Vendeur|3421 Clients600|71243 Ventes500 et4455 TVA100|
|Acheteur|6111 Achats500 et34552 TVA100|4411 Fournisseurs600|

Les comptes ci-dessus sont ceux des articles et tiers du jeu de test. Les
autres comptes/configurations suivent le paramétrage existant. Cet exemple
n'atteste pas une déductibilité fiscale réelle. Les deux FEC utilisent la
référence du même document vendeur tout en conservant leurs écritures, numéros,
comptes auxiliaires et sociétés respectifs.

Pour le sens inverse, préparer une liaison où l'autre société est vendeuse,
avec son client et le fournisseur de l'autre côté. Aucun lien inverse n'est
présumé à partir du premier.

## Contrôler les écarts et corrections

Dans **Paramètres → Sociétés liées**, déplier **Factures de la liaison** pour
voir les correspondances regroupées, les plus récentes en premier, par pages
de10. Chaque côté affiche son exercice, validation/comptabilisation, TTC,
reste à régler, paiements encaissés/payés, règlements en cours et imputations.
**Actualiser les factures liées** relit les montants sansF5. Une liaison retirée
garde son historique. Ce suivi courant n'appartient pas à une archive fiscale.

« Solde couvert » ne prouve pas un encaissement : un chèque en portefeuille peut
couvrir le solde tout en restant entièrement en cours. Les montants indéterminés
affichent **À vérifier**, jamais un faux zéro. Les pièces annulées restent
identifiées ; leur reste calculé ne constitue pas une demande de règlement.

Le panneau affiche les états de validation/comptabilisation des deux pièces et
les écarts documentaires détectés. Le brouillon d'achat reste modifiable selon
le flux ordinaire ; une modification n'est jamais répercutée silencieusement
dans la vente validée. Les différences de référence, fournisseur, dates,
conditions, lignes/articles et TVA déclarée restent signalées.

Un avoir ou une annulation d'un côté est signalé et doit être traité dans
chaque société avec ses propres justificatifs. Les paiements, acomptes, lettrages,
avoirs, livraisons et pièces jointes ne sont pas automatiquement répliqués. Le
suivi ne constitue pas un contrôle exhaustif de ces flux. Le lien conserve
l'origine ; une facture liée ne se supprime pas. Utiliser son statut ou un
document correctif selon le flux métier, en conservant la piste d'audit.

Retirer la liaison commerciale ne supprime pas les factures déjà créées. Leur
correspondance reste consultable avec les droits dans les deux sociétés et le
rejeu de la commande initiale retrouve l'historique. Cela n'autorise pas une
nouvelle copie de la même vente. Pour éviter un mauvais rattachement initial,
vérifier attentivement la société et ses tiers avant la création.

## Limites et installation

- Administration de la liaison : administrateur dans les deux sociétés.
  Création de la correspondance : administrateur ou comptable dans les deux.
  Lecture du suivi : accès de consultation dans les deux. Les droits révoqués
  sont relus, même avec un ancien jeton.
- Parcours limité à500lignes, deux comptabilités MAD, une vente validée active
  sans RAS portée directement sur la facture et une période d'achat ouverte.
  Les acquisitions d'immobilisations utilisent leur module dédié. Une absence
  de calendrier ou un choix non qualifié est signalé sans données présumées.
- Aucun code fiscal de groupe, crédit, retenue ou traitement de change nouveau
  n'a été inventé. Les taux/proratas restent ceux du paramétrage ordinaire.
- Installer explicitement **101_societes_liees.sql**, puis
  **102_factures_correspondantes.sql**, après sauvegarde et préparation des droits
  selon les [procédures d'exploitation](EXPLOITATION_HISABPRO.md). Ces migrations
  ne s'exécutent pas automatiquement au démarrage. Aucune base utilisateur n'a
  été migrée ici ; sans102, seul le panneau signale son indisponibilité.

Tests automatisés natifs/Edge et limites : [rapport635](../Test/rapport_factures_liees635.md).
Le [rapport641](../Test/rapport_suivi_correspondances641.md) couvre la vue
regroupée, ses droits et la lecture cohérente pendant un paiement.

Les nouveaux règlements et modifications de montant doivent être exprimés au
centime. Une valeur telle que 0,005 MAD est refusée avant enregistrement au lieu
d'être arrondie implicitement dans le Journal. Un ancien montant non qualifié
reste signalé et ne doit pas être corrigé silencieusement dans une pièce
définitive. Voir le [contrôle 642](../Test/rapport_reglements_centimes642.md).

La recette humaine, le déploiement réel et la qualification réglementaire du
dossier restent distincts. RH/paie restent différées.
