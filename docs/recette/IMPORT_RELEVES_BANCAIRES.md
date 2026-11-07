# Import de relevés bancaires Excel et CSV

Dans **Rapprochement bancaire → Import Excel / CSV**, choisir le compte bancaire
et la période, déposer le fichier, vérifier chaque ligne dans l'aperçu, puis
cliquer sur **Enregistrer le relevé**. Aucun fichier ne génère d'écriture comptable.

Excel : première feuille XLSX/XLS. CSV : UTF-8, UTF-8 avec BOM ou Windows-1252 ;
séparateur point-virgule, virgule ou tabulation. La directive Excel `sep=;` est
acceptée. Les guillemets, virgules/points-virgules à l'intérieur d'un champ et
libellés multilignes suivent le format CSV avec doublement des guillemets.

L'en-tête doit se trouver dans les dix premières lignes. La date d'opération
est fournie dans **Date** ou **Date opération**, au format `JJ/MM/AAAA` ou
`AAAA-MM-JJ`. Une **Date valeur** seule n'est pas convertie en date d'opération.
Le libellé est facultatif. Les colonnes supplémentaires, dont **Solde**, ne sont
pas transformées en opérations ou en soldes confirmés.

Trois formats explicites sont disponibles :

```csv
Date;Libellé;Débit;Crédit
03/04/2025;002;;1 234,56
04/04/2025;Frais;34,56;
```

Une seule colonne Débit ou Crédit porte un montant positif par ligne ; la case
opposée peut être vide ou zéro. Convention de relevé : Crédit = entrée bancaire,
Débit = sortie bancaire.

```csv
Date;Libellé;Montant
03/04/2025;Virement;1234,56
04/04/2025;Frais;-34,56
```

Sans colonne Sens, Montant est signé : positif = entrée, négatif = sortie.

```csv
Date;Libellé;Montant;Sens
03/04/2025;Virement;1234,56;Crédit
04/04/2025;Frais;34,56;Débit
```

Avec Sens, Montant est positif. Débit/Crédit ou D/C sont acceptés dans Sens.
Le montant doit avoir au plus deux décimales : `1234,56`, `1 234,56` ou `1234.56`.
Les espaces ordinaires ou insécables entre groupes de milliers sont acceptés.
Les ponctuations ambiguës et les textes monétaires tels que `1,234.56` ou
`12 MAD` sont refusés ; reformater explicitement les montants avant import.

Une ligne invalide refuse **tout l'aperçu** avec son numéro : aucune ligne n'est
silencieusement omise. Un exercice clôturé refuse l'enregistrement de tout le
lot. Les soldes d'ouverture/clôture se saisissent séparément à partir du relevé.

Le backend conserve sa règle de doublon existante : même société, compte,
date, libellé, montant et sens = ligne ignorée. Deux opérations bancaires réelles
strictement identiques sur ces champs ne sont pas distinguables avec ce contrat.
Vérifier le nombre de lignes et les totaux ; en cas de justificatifs de deux
opérations distinctes, utiliser leur référence bancaire explicite dans le libellé
avant import, sans inventer de référence.

Jeu fictif ci-dessus : solde initial **10 000,00 MAD**, entrée **1 234,56 MAD**,
sortie **34,56 MAD**, solde final calculé **11 200,00 MAD**. Le solde bancaire
déclaré reste un contrôle indépendant, saisi depuis le relevé.
