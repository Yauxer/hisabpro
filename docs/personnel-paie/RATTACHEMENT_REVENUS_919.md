# Périodes de référence et versements déclarés des variables

Dans **02 · Éléments de paie → Variables mensuelles → Saisir une variable**, le panneau facultatif **Période de référence et versement déclaré** permet de conserver les faits nécessaires à l’analyse des primes et rappels :

- début et fin de la période à laquelle le revenu se rapporte, avec sa justification ;
- date de versement déclarée et référence documentaire associée.

Ces dates sont distinctes de la période de traitement et de la date d’effet de la variable. Aucun champ ne se remplit automatiquement à partir d’un autre. Quand les renseignements ne sont pas connus, laisser le panneau vide ; les anciennes variables conservent leur JSON et les anciennes simulations leurs empreintes.

Sur une **copie isolée** disposant du socle existant, appliquer `hisabpro-backend/123_paie_rattachement_revenus.sql`. Cette migration ajoute un gardeJSON et ne réécrit aucune ligne ou migration antérieure. Sans ce garde, la nouvelle saisie documentaire renvoie503 ; les saisies historiques sans rattachement restent disponibles. Aucun accès à la base habituelle n’a été utilisé.

Pour la recette fictive, saisir une variable de **800.01MAD**, traitée en **novembre2026**, avec effet **2026-11-15**, référence **2025-01-01 au2025-12-31**, justification **PRIME-ANNUELLE-FICTIVE919**, versement déclaré **2026-12-05**, référence **VERSEMENT-DECLARE-FICTIF919**. Le décalage est volontaire et ne doit pas être corrigé artificiellement. La rémunération mensuelle de recette est9000.10MAD ; le brut arithmétique reste9800.11MAD. Ce test ne détermine pas le traitement fiscal de ce rappel.

Soumettre, puis faire ouvrir le détail et approuver par un acteur indépendant. Les renseignements suivent le même workflow et deviennent immuables avec la variable ; une erreur passe par annulation/rejet puis nouvelle proposition, sans modification silencieuse d’une variable approuvée. Les références sont masquées aux lecteurs ne disposant pas des droits d’historique appropriés. Les snapshots bruts reprennent uniquement les dates, avec l’identifiant de la variable, sans recopier ses références de preuve.

Une période renseignée exige ses deux bornes ordonnées et sa justification. Une date de versement exige sa référence. Une durée supérieure à un an reste un fait enregistrable, sans présumer de sa méthode de taxation. Aucune date ne confirme un mouvement bancaire et aucune répartition fiscale/sociale ou régularisation n’est calculée par ce lot.

Le besoin de distinguer les périodes de référence est décrit dans la **noteDGI717, tome1, avril2011, pages360–361**. Une copie du document primaire a été récupérée via [Monexpert](https://www.monexpert.ma/download/documents/kAuCgJLbx5gugjWaPhYvhgvdW9zLB5HW4gFxNK2q.pdf) :547pages,4778116octets, SHA256`0c482ee28864fdbef8b451a5019f77a041b3b873f187ac1d6914a1a59a9de559`. L’hébergeur de cette copie n’est pas laDGI. Les valeurs fiscales historiques ne sont pas reprises comme règles2026 ; le rapprochement avec le CGI courant et la qualification de la retenue mensuelle restent nécessaires.

[RecettePDF](RECETTE_RATTACHEMENT_PAIE_919.pdf) · [SuiviExcel](SUIVI_RATTACHEMENT_PAIE_919.xlsx) · [Données exactes](JEU_RATTACHEMENT_PAIE_919.json) · [Guide des variables](VARIABLES_PAIE_891.md).
