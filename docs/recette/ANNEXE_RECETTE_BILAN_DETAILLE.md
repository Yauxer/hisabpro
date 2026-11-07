# CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO

## Annexe bilan détaillé

Annexe bilan détaillé : quatre cas Non testé. Aucun résultat utilisateur prévalidé. Les preuves automatisées du lot 256 sont distinctes de cette recette à effectuer. Utiliser uniquement des sociétés fictives isolées ; aucune réparation de dossier réel. La présentation ne constitue pas une certification comptable ou fiscale.

## Jeu de données

- **Société A** : BILAN DETAIL RECETTE A ; dossier fictif vierge, début du premier exercice 2026 ; administrateur ; exercice ouvert du 01/01/2026 au 31/12/2026.
- **Client** : CLIENT BILAN RECETTE ; type Client ; rattacher explicitement ce tiers à la ligne 3421.
- **Reprise N** : Écriture OD au 01/01/2026, référence BILAN-REC-N, libellé Reprise fictive pour recette de présentation. Débits : 2311 = 1000,00 MAD; 2321 = 2000,00 MAD; 2331 = 3000,00 MAD; 2340 = 4000,00 MAD; 2351 = 5000,00 MAD; 2380 = 6000,00 MAD; 3111 = 7000,00 MAD; 3421 = 8000,00 MAD; 5141 = 9000,00 MAD. Crédits : 28321 = 300,00 ; 1111 = 44 700,00 MAD. Total débit = crédit = 45 000,00 MAD. Aucun compte 6/7.
- **Nature des données** : Reprise fictive de soldes de bilan, pas une acquisition ou une dotation fiscale. Aucune TVA ou déclaration n’est générée. Ne pas créer aussi des factures, immobilisations ou stocks correspondant à ces mêmes montants : cela doublerait les écritures.
- **Société B** : BILAN DETAIL RECETTE B ; société fictive séparée, début du premier exercice 2025 ; exercices 2025 et 2026 ouverts. Client CLIENT BILAN RECETTE B.
- **Comparatif B N-1** : Écriture OD au 01/01/2025, référence BILAN-B-N1 : débit 5141 = 75,00 ; crédit 1111 = 75,00 MAD. Valider. Ne pas clôturer ni générer d’à-nouveaux automatiquement pendant cette recette isolée de présentation.
- **Ouverture B N** : Écriture OD au 01/01/2026, référence BILAN-B-OUVERTURE : débit 5141 = 75,00 ; crédit 1111 = 75,00 MAD. Valider. Puis seconde écriture OD BILAN-B-N avec les débits de Reprise N sauf 5141 = 8 925,00 ; crédits 28321 = 300,00 et 1111 = 44 625,00 MAD. Débit = crédit = 44 925,00 ; total annuel identique à A. Rattacher le client B à 3421. Aucun doublon d’ouverture.
- **Archive ancienne** : Dossier fictif précédemment finalisé avant livraison du détail (lot 256), issu du cahier annuel. Relever société, exercice, version, empreinte et ancien export. Si aucun dossier de recette ne satisfait ce prérequis, classer BILAN-DET-04 Bloqué ; ne pas modifier ni fabriquer un snapshot.

## BILAN-DET-01 — Bilan détaillé sans comparatif

**module** : Bilan

**prerequis** : Créer la société A et le client du Jeu de données ; aucun autre mouvement. Vérifier que les comptes indiqués sont actifs.

**donnees** : Écriture OD au 01/01/2026, référence BILAN-REC-N, libellé Reprise fictive pour recette de présentation. Débits : 2311 = 1000,00 MAD; 2321 = 2000,00 MAD; 2331 = 3000,00 MAD; 2340 = 4000,00 MAD; 2351 = 5000,00 MAD; 2380 = 6000,00 MAD; 3111 = 7000,00 MAD; 3421 = 8000,00 MAD; 5141 = 9000,00 MAD. Crédits : 28321 = 300,00 ; 1111 = 44 700,00 MAD. Total débit = crédit = 45 000,00 MAD. Aucun compte 6/7.

**actions** : Sélectionner A / 2026. Journal → Nouvelle écriture : saisir date, journal OD, référence, libellé et les onze lignes exactes ; sélectionner le client sur 3421. Contrôler débit/crédit 45 000,00 puis enregistrer et Valider. Ouvrir Comptabilité → Liasse fiscale → T1 · Bilan. Lire les six immobilisations sous la rubrique Immobilisations corporelles, les stocks, clients et banque.

**attendu** : Brut immobilisé 21 000,00 ; amortissements 300,00 ; net 20 700,00. Brut général 45 000,00 ; net actif = passif 44 700,00. Sous-postes bruts 1 000/2 000/3 000/4 000/5 000/6 000 ; amortissement et net des sous-postes « — », sans ventilation arbitraire. N-1 absent, jamais transformé en zéro.

**ecritures** : Créer et valider uniquement les écritures fictives précisées dans ce cas. La consultation et les exports ne créent aucune écriture supplémentaire.

**fiscal** : Aucun calcul fiscal nouveau attendu ; cette reprise fictive ne justifie aucune TVA, amortissement fiscal ou liquidation.

**controles** : Vérifier société et exercice actifs ; comparer balance validée et total bilan ; les sous-postes sont pour mémoire, sans double addition.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Capture de l’écriture validée, balance et T1 incluant sous-postes, notice, totaux et absence de N-1.

**observations** : À renseigner pendant la recette.


## BILAN-DET-02 — Bilan détaillé avec N-1 disponible

**module** : Comparatif

**prerequis** : Utiliser exclusivement la société B distincte, exercices 2025 et 2026 ouverts ; aucun autre mouvement, aucune clôture ou à-nouveaux automatique.

**donnees** : Écriture OD au 01/01/2025, référence BILAN-B-N1 : débit 5141 = 75,00 ; crédit 1111 = 75,00 MAD. Valider. Ne pas clôturer ni générer d’à-nouveaux automatiquement pendant cette recette isolée de présentation. Écriture OD au 01/01/2026, référence BILAN-B-OUVERTURE : débit 5141 = 75,00 ; crédit 1111 = 75,00 MAD. Valider. Puis seconde écriture OD BILAN-B-N avec les débits de Reprise N sauf 5141 = 8 925,00 ; crédits 28321 = 300,00 et 1111 = 44 625,00 MAD. Débit = crédit = 44 925,00 ; total annuel identique à A. Rattacher le client B à 3421. Aucun doublon d’ouverture.

**actions** : En B/2025, saisir puis valider BILAN-B-N1. Passer à B/2026, saisir puis valider BILAN-B-OUVERTURE et BILAN-B-N selon le Jeu. Vérifier les montants et le tiers. Ouvrir Liasse fiscale → T1 · Bilan. Comparer la colonne N-1 avec le bilan B/2025.

**attendu** : Total brut N 45 000,00 ; amortissements 300,00 ; net N 44 700,00. N-1 : banque et capital 75,00 ; total net actif/passif 75,00. Les autres rubriques N-1 connues sont nulles en montant, pas absentes. Aucun amortissement ou net de détail N n’est inventé.

**ecritures** : Créer et valider uniquement les écritures fictives précisées dans ce cas. La consultation et les exports ne créent aucune écriture supplémentaire.

**fiscal** : Aucun calcul fiscal nouveau attendu ; cette reprise fictive ne justifie aucune TVA, amortissement fiscal ou liquidation.

**controles** : Vérifier société et exercice actifs ; comparer balance validée et total bilan ; les sous-postes sont pour mémoire, sans double addition.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Écritures validées des deux exercices ; T1 B/2025 et B/2026 montrant 75,00 en comparatif.

**observations** : À renseigner pendant la recette.


## BILAN-DET-03 — Retrouver le détail dans Excel et PDF

**module** : Exports

**prerequis** : BILAN-DET-01 effectué sur A/2026 ; aucune autre mutation après la capture du bilan.

**donnees** : A/2026 ; mêmes soldes et montants que BILAN-DET-01.

**actions** : Dans la liasse A/2026, cliquer Excel et ouvrir T1 Bilan Actif puis T1 Bilan Passif. Cliquer PDF et l’ouvrir. Rechercher Constructions, Matériel de transport et TOTAL GÉNÉRAL. Comparer les lignes, chiffres et N-1 avec l’écran ; comparer à nouveau le journal.

**attendu** : Les six sous-postes figurent dans les deux exports. Construction brute 2 000,00, amortissement/net détaillés absents. Total brut 45 000,00, amortissements 300,00 et net 44 700,00 identiques ; Excel garde de vraies cellules numériques et des cellules vides pour montants indéterminés. Journal inchangé.

**ecritures** : Aucune nouvelle écriture : consultation et exports uniquement.

**fiscal** : Aucun calcul fiscal nouveau attendu ; cette reprise fictive ne justifie aucune TVA, amortissement fiscal ou liquidation.

**controles** : Vérifier société et exercice actifs ; comparer balance validée et total bilan ; les sous-postes sont pour mémoire, sans double addition.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Fichiers PDF/XLSX téléchargés, captures des six sous-postes et totaux ; journal avant/après.

**observations** : À renseigner pendant la recette.


## BILAN-DET-04 — Préserver une archive de l’ancien format

**module** : Archives

**prerequis** : Dossier fictif précédemment finalisé avant livraison du détail (lot 256), issu du cahier annuel. Relever société, exercice, version, empreinte et ancien export. Si aucun dossier de recette ne satisfait ce prérequis, classer BILAN-DET-04 Bloqué ; ne pas modifier ni fabriquer un snapshot.

**donnees** : Identifiants et montants effectivement relevés dans cette archive fictive ; aucune valeur arbitraire imposée.

**actions** : Sélectionner la société/exercice du prérequis et ouvrir Liasse fiscale. Relever version et empreinte de l’archive. Ouvrir T1 · Bilan, exporter Excel et PDF puis recharger. Comparer avec l’ancien snapshot/export disponible. Sans prérequis, inscrire Bloqué et expliquer quelle archive manque.

**attendu** : Version, empreinte et montants figés restent identiques. Les anciennes rubriques agrégées restent lisibles ; aucun détail n’est reconstitué depuis les écritures actuelles. La présence de détails ne doit pas être exigée sur cette archive ancienne.

**ecritures** : Aucune nouvelle écriture : consultation et exports uniquement.

**fiscal** : Aucun calcul fiscal nouveau attendu ; cette reprise fictive ne justifie aucune TVA, amortissement fiscal ou liquidation.

**controles** : Vérifier société et exercice actifs ; comparer balance validée et total bilan ; les sous-postes sont pour mémoire, sans double addition.

**statut** : Non testé

**resultat reel** : À renseigner pendant la recette.

**anomalies** : À renseigner pendant la recette.

**preuves** : Référence du dossier fictif, capture version/empreinte avant/après, anciens et nouveaux exports comparés.

**observations** : À renseigner pendant la recette.

