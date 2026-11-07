# Lot 561 — Ventes et raccordement au chiffre d'affaires comptable

La préparation annuelle des ventes compare désormais le HT documentaire signé
avec les comptes711/712 des écritures validées, hors clôtures techniques,
suivant le périmètre déjà utilisé par la source des états de synthèse.

Le contrôle expose les comptes, débits/crédits, origines techniques et mouvements
du Journal. Un écart global nul ne prouve pas le rattachement individuel d'une
facture ou d'un avoir. Les pièces non comptabilisées, opérations manuelles et
montants inconnus restent visibles ; aucune écriture ou source n'est réparée.
Les dates du Journal hors bornes de l'exercice sont signalées explicitement.

## Utilisation et exports

Comptabilité → Liasse fiscale → Préparation ventes → Préparer les ventes.
Lire le bloc « Raccordement avec la comptabilité » puis développer le détail
par compte et origine. Le CSV et la feuille Excel « Comptabilité » contiennent
les mouvements sources. Le PDF fournit les totaux et leur décomposition.
Les logos existants sont conservés par les générateurs partagés.

L'empreinte inclut désormais le Journal : une modification comptable seule
invalide un ancien export, même si aucune facture n'a changé. Actualiser la
préparation avant de télécharger la nouvelle version. Les archives fiscales
antérieures et leur contenu restent intacts.

## Cohérence de lecture

Une expérience concurrente réelle a reproduit un relevé mélangeant HT100 et
CA300, à cause d'une facture comptabilisée entre les lectures. La lecture finale
utilise une même transaction PostgreSQL `REPEATABLE READ`, en lecture seule,
initialisée avant l'authentification et partagée sur une connexion unique.
Le dossier antérieur reste100/100 ; une lecture suivante voit300/300.

Un prototype à connexion supplémentaire a été remplacé pour éviter la saturation
du pool. Un contrôle avec une seule place vérifie ce contrat sans simuler la
comptabilité. L'authentification de ce test s'effectue réellement dans son
processus : réutiliser le JWT d'un serveur à autre clé donnait401, ce qui était
un défaut de préparation du test et non la preuve d'un interblocage.

## Tests exécutés et échecs conservés

- Première série :3réussis/2échecs,38,67s. Une erreur de corps de test de
  validation par lot (422, `ids` requis), et la lecture concurrente100/300.
- Prototype cohérent :5réussis,29avertissements,35,61s.
- Contrôle de pool initial :401 dû aux clés distinctes, corrigé par login local.
- Première consolidation :37réussis/3échecs,152,68s. Deux sélecteurs d'exercice
  inadaptés à la page Liasse ; injection historique `-Infinity` déjà refusée
  par le CHECK de la migration043 dans le schéma courant.
- Le banc historique original est conservé et exécuté séparément :
  **12réussis,26avertissements,36,54s**, dont les quatre anomalies historiques.
  Aucune contrainte n'a été retirée pour injecter ces anomalies dans la base moderne.
- Consolidation suivante :26réussis/2échecs,98,44s. Les fichiers téléchargés par
  Edge portent un nom temporaire sans extension : sauvegarde réelle en`.xlsx`
  avant ouverture par Openpyxl. Aucune valeur métier attendue modifiée.

La série finale vérifie également des références comptables longues et leur
hauteur dans Excel, les formules neutralisées, les pièces non comptabilisées,
la clôture/à-nouveaux, l'isolation des sociétés et les téléchargements réels
admin/lecteur. Son résultat est ajouté au journal après achèvement.

## Limites

Raccordement arithmétique interne, pas une déclaration DGI ou un contrôle
exhaustif des justificatifs. Les ventes absentes de la facturation contribuent
au contrôle comptable mais ne deviennent pas de fausses factures dans le relevé.
Aucune nouvelle règle fiscale, migration ou connexion à la base réelle.
Recette utilisateur et production non validées ; RH/paie différées.

Qualification finale : **28 réussis, 29 avertissements, 97,89 s, code 0**.
Le test de pool unique passe avec login réel ; le test concurrent conserve
100/100 puis300/300. Les deux parcours Edge téléchargent et lisent les vrais
PDF/XLSX. Captures mobile et PDF d’une page inspectées.
Logos de deux sociétés distinctes dans PDF/Excel : **1 réussi,
29 avertissements, 27,88 s**. Historique12cas mentionné ci-dessus, exécuté
séparément avec son banc d’origine ; aucun test ignoré ou affaibli.
Build Vite6,01s, code0 ; huit fichiers Python compilés.

[Exemple PDF issu de la recette fictive](../docs/audit/exemples/VENTES_RACCORDEMENT_FICTIF_20261018.pdf).
