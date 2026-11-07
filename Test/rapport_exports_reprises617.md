# Lot617 — exports du suivi des reprises

Le panneau Clôture permet de télécharger le suivi de la source sélectionnée
en PDF et Excel, y compris en consultation seule. Les documents portent
l’identité et le logo courants de la société, les comptes/libellés, montants
exacts, références déclarées, statuts des originaux/inverses et effets sur
la capacité liée. Les sources historiques à vérifier restent exportables avec
leurs diagnostics ; aucune anomalie n’est effacée ou reclassée.

Une préparation RO/RR sur la même connexion que l’authentification fige les
faits et l’identité. Le téléchargement exige son empreinte SHA-256 et refuse409
si validation, annulation, identité, logo ou libellé de compte ont changé.
Le navigateur relit la préparation, actualise le suivi local et ignore une
réponse devenue étrangère à son contexte société/exercice/saisie. Aucun nouveau
schéma, calcul fiscal ou mouvement comptable ;100 reste la dépendance de615.

L’Excel utilise des cellules texte pour les valeurs dépassant sa précision
et pour tous les libellés/références commençant par un caractère de formule.
Les hauteurs de lignes suivent les textes ; logo sur une feuille distincte,
table filtrable et en-têtes figés. Le PDF échappe les textes saisis et précise
le périmètre interne. L’empreinte identifie les données, sans prétendre être
une signature ni l’empreinte du fichier PDF.

## Tests

15tests API/Edge/concurrence réussis en65.389s ;40connexes purs/UUID/Edge615 en58.033s (recouvrent des cas615, ne pas additionner comme couverture unique) ;1restauration native77tables en53.707s. Aucun échec/ignoré final. Build Vite5,00s et compilation Python réussis.

Les contrôles couvrent fichiers réellement téléchargés, images embarquées,
montants/statuts et SHA, texte littéral/formules Excel, grand montant exact,
isolation des sociétés, lecture seule, sources orphelines, snapshots concurrents,
connexion unique, et Edge admin/comptable/lecture1440/390. Le cas de contexte
tardif retarde une vraie réponse de préparation, sans modifier son corps ni
remplacer une API métier.

La restauration utilise deux PostgreSQL natifs jetables et compare données,
texte/images PDF, valeurs/types des cellules et images Excel avant/après. Les
octets complets PDF/Excel ne sont pas prétendus identiques : métadonnées de
génération des fichiers susceptibles de varier. Schéma/données/ACL/séquences
et les77tables sont contrôlés par le banc615 conservé.

Mise au point : un essai9cas avec1échec de scénario (logo=null est ignoré
par le contrat PATCH, effacement explicite avec chaîne vide), puis14cas avec
3échecs et14cas avec2échecs d’authentification du banc local. Les deux serveurs
avaient des clés de test différentes : le banc se connecte maintenant à chaque
serveur via son vrai login, sans contourner l’authentification.

## Limites

Suivi courant lié à une dotation, pas un solde global de compte, une archive
annuelle, une déclaration DGI ou une preuve de déductibilité. Identité/logo
courants explicitement indiqués. Aucun accès à PostgreSQL utilisateur ; recette
humaine, installation100 réelle et recalcul/ouverture Excel du partenaire
à effectuer. Aucune intervention sur RH/paie.
