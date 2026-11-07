# Préparation annuelle interne des ventes —418

Nouvel onglet Comptabilité→Liasse fiscale→Préparation ventes,API GET authentifiée et service de lecture seule. Aucun schéma,migration,paramètre fiscal ou document comptable modifié. L'exercice doit exister ;ses dates réelles définissent les bornes inclusives. Factures de vente définitives et avoirs actifs à leur propre date, y compris avoir sur facture d'exercice antérieur. Achats,brouillons,proformas et pièces annulées exclus etcomptés explicitement.

Pièces détaillées avec nature/ID/numéro/date,client etICE/IF figés,HT commercial avant escompte,TVA/TTC selon le moteur existant,signe négatif de l'avoir,état comptabilisé etdiagnostics. Aucun rattachement depuis un nom voisin ou la fiche tiers actuelle. Sources inconnues etexercice incohérent restent visibles ;total complet inconnu,partie certaine séparée. Aucun zéro de remplacement ni réparation historique. Les écritures manuelles etventes hors facturation ne sont pas incluses :ce n'est ni le CAcomptable ni une déclarationDGI.

CSV avecBOM,données de la préparation effectivement affichée,montants décimaux exacts,empreinte etpérimètre ;échappement des textes assimilables à une formule. Cette préparation courante est extérieure aux archives de liasse ;l'ancien export Excel/PDF consolidé et les snapshots fiscaux restent inchangés. UI avec styles de la liasse,tableaux consultables bureau/mobile,périmètre dépliable,actualisation etprotection contre réponses tardives après changement année/société/token.

## Preuves réelles

Oracle :factures100+200,avoir30 à sa propre date ⇒HT270/TVA54/TTC324. CSV téléchargé réellement identique à la réponse source. ICE historique conservé après changement du tiers. Lecture autorisée au rôle consultation ;aucune route de mutation,authentification etisolation société vérifiées. Période décalée juillet→juin,avoir surN−1,NaN/Inf/−Inf/NULL,incohérence d'exercice et conservation des données testés. Edge1365/390 etréponse réelle retardée puis ignorée après changement d'année ;captures inspectées. Bilans détaillés,ancienne numérotation interne,exports etfinalisation d'archive connexes réellement rejoués.

ventes418_final2:14réussis,51.603s ; ventes418_lecture_role:1réussis,17.840s ; ventes418_edge_final:3réussis,28.172s ; ventes418_connexes:8réussis,65.030s ; suites recouvrantes non additionnées ;compilation0,build141modules4.79s.

## Échecs intermédiaires conservés

PremierAPI7passes/1échec sur méthodePATCHtiers inexistante,oracle adapté àPUT réel. PremiersEdge3échecs :lecture de CSV normalisantCRLF etattente de banc ne garantissant pas la réception retenue ;lecture en octets etsignal de synchronisation explicite corrigés. Suite suivante11passes/3échecs de constitution des données fictives :facture définitive sans numéro et tentative de modifier l'exercice d'une pièce déjà validée refusées par les vrais triggers. Banc corrigé en constituant le legacy avant état définitif avec numéro fictif ;aucune protection désactivée. Nouveaujeu14passes, puis rôlelecture et3Edge finaux réussis. Aucun assouplissement d'assertion financière.

## Limites

09E devient partiel :préparation documentaire disponible,format officiel,DGI,ventilations fiscales exhaustives etrapprochement auCAcomptable restent à qualifier. Pas deXML,formulaire fiscal fabriqué ou nouveaux champs obligatoires. Word/recette humaine restent distincts. Aucun PostgreSQL réel ni donnée comptable réelle ;point6 en attente. Nouvelle globale419 sur les sources finales à exécuter avant toute conclusion globale.
