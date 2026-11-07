# Ventilation d'un paiement par tiers — lot372

Dans Cycle commercial → Vente/Achat → Règlements, le bouton **Ventiler par tiers**
ouvre une saisie de paiement immédiat. Les factures proposées sont validées,
non proforma, rattachées au tiers natif et avec montants qualifiés. Leurs soldes
proviennent de la situation serveur, incluant avoirs, acomptes et RAS imputée.
Le total saisi doit égaler exactement la somme des ventilations au centime.

L'API `/api/reglements/par-tiers` enregistre plusieurs règlements individuels
avec une référence commune dans une transaction unique. Chaque ligne conserve
son lien facture, son écriture, sa RAS éventuelle et sa contrepassation.
Le flux individuel utilise désormais la même création métier sans commit interne.
Les factures sont verrouillées par identifiant croissant ; un verrou d'opération
et un UUID conservé dans les numéros techniques évitent le double envoi.
Un UUID déjà enregistré avec un contenu ou un état différent est refusé409.
Un dépassement d'un seul centime est refusé. Aucun regroupement d'historique.

## Oracle et preuve réelle

Deux factures du même tiers : HT100/TVA20/TTC120 et HT200/TVA40/TTC240.
Paiement240 ventilé120/120 : première soldée, seconde partielle avec reste120.
Complément120 : deux factures soldées ; cinq écritures équilibrées, mouvement
de banque360 et solde collectif nul. En vente, banque5141 débit/client3421 crédit ;
en achat, fournisseur4411 débit/banque5141 crédit. Validation puis lettrage réel
des cinq lignes collectives dans Edge1365/390px. Captures locales enregistrées.

Autres scénarios : refus de tiers/sens/société mélangés, documents brouillons ou
proforma, période clôturée423, montant historique défaillant422, montant non fini,
booléen, nul, négatif, fraction de centime, doublon et référence trop longue.
Instantanés financiers identiques après chaque refus. Deux requêtes simultanées
du même UUID renvoient les mêmes identifiants ; deux opérations distinctes ne
peuvent consommer le même solde. Consultation seule refusée403.

Interactions achat/vente : acompte40 laisse80 à ventiler ; avoir24 laisse96 ;
paiement20 + RAS déclarée10 laisse90. Une estimation RAS n'est pas imputée seule.
Les montants0,10/0,20 sont traités exactement ; l'annulation conserve les écritures
validées et empêche de rejouer l'UUID annulé.

## Résultats exécutés

- Premier API :20réussis/5échecs,56,38s. Prérequis corrigés : comptabiliser les
  factures après validation ; créer les brouillons/proformas par API ; injecter
  le défaut dans un règlement fictif non comptabilisé, sans désactiver les
  protections des factures définitives ; respecter le refus423 de clôture.
- API corrigée :25réussis,54,27s.
- Première UI :1échec42,16s, confirmation native du Journal non acceptée par le banc.
- API/Edge :30réussis,103,13s après acceptation de cette confirmation.
- Interactions :7réussis,26désélectionnés,30,31s.
- Connexes :108réussis,26avertissements,346,51s,code0. Comprend création individuelle,
  édition, captures RAS, lecture historique, oracle et interactions ci-dessus.
- Dernière UI :3réussis/1échec71,14s, clic Journal avant chargement des cinq lignes.
  Synchronisation du banc ajoutée sur les cinq boutons de validation.
- UI finale :4réussis,26avertissements,57,40s,code0, ordinateur/mobile et absence de
  débordement. Sur mobile, `crypto.randomUUID` est volontairement indisponible :
  la génération utilise `getRandomValues`. Cette suite suit la dernière modification UI.
- Build final :code0,5,01s, avertissements xlsx/taille de bundle préexistants.
  Compilation des deux fichiers backend et des deux tests :code0. Aucune réussite
  globale déduite de ces suites ciblées. Les suites ne s'additionnent pas.

Preuves XML locales : `.codex-tests/reglements372_{api,api_final,final,
interactions,connexes,ui_final,ui_stable}.xml`. Les échecs antérieurs restent conservés.

## Limites explicites

Modes immédiats seulement ; chèques/effets conservent leur traitement individuel.
Maximum50factures par opération. Les historiques sans tiers natif ne sont pas
reliés arbitrairement. Chaque ventilation produit un règlement et une écriture ;
la contrepassation est individuelle. Un instrument bancaire unique regroupé,
l'annulation globale d'un groupe et son rapprochement en une seule ligne ne
sont pas ajoutés par ce lot. Aucune nouvelle table, migration ou modification de
modèle/main ; leurs empreintes sont conservées. Aucun test sur PostgreSQL réel.
Recette humaine et préparation de production restent distinctes.
