# Annuler un règlement ou une ventilation comptabilisée

Dans **Cycle commercial → Achat ou Vente → Règlements**, ouvrir l’action
**Annuler par contrepassation** sur la ligne concernée.

1. Vérifier le tiers et le montant affichés.
2. Choisir la **Date d’annulation**. La date du jour est proposée ; elle reste
   modifiable. Le serveur contrôle la date et l’ouverture de la période.
3. Renseigner, si nécessaire, un **Motif** de 500 caractères maximum.
4. Cliquer sur **Confirmer l’annulation**. En cas de refus, l’alerte reste
   visible dans le formulaire et les valeurs saisies sont conservées.
5. Après succès, la liste et la situation des factures se rafraîchissent.
   Contrôler et valider les nouvelles contrepassations dans le **Journal**.

Les écritures d’origine sont conservées. Une RAS liée est également
contrepassée ; aucune déclaration, imputation ou preuve fiscale n’est déduite.
Les protections existantes contre le lettrage, les cycles bancaires engagés
et les périodes fermées continuent de s’appliquer.

Depuis le lot659, l’action **Annuler toute la ventilation** ouvre aussi ce
formulaire. Vérifier le total, le nombre et les numéros de tous les règlements
affichés : le lot entier est concerné, même si des filtres masquent des lignes
dans la liste principale. La date choisie et le motif seront transmis pour
tout le lot. Le serveur recontrôle l’ensemble au moment de la confirmation ;
si une ligne ne peut plus être annulée, l’opération collective est refusée.
Les règlements non comptabilisés relèvent toujours de leur action distincte.

La recette RDO-008 du [cahier Word](recette/ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.docx)
peut désormais renseigner la date et le motif dans ce formulaire. La recette
humaine reste à effectuer sur un dossier de test isolé.

Si la liste des règlements indique **Chargement des règlements impossible**,
aucun total n’est présenté comme disponible. Utiliser **Réessayer** après
rétablissement du service. **Actualiser** relit aussi une liste déjà affichée.
Une réponse vide correctement chargée reste indiquée par « Aucun règlement
trouvé » ; ce message n’est pas utilisé pour masquer une erreur de lecture.

En consultation seule, la liste, son actualisation et le dossier RAS restent
accessibles. Les commandes Modifier, Supprimer, Annuler et Ventiler ne sont
pas proposées. Un rôle autorisé doit effectuer ces opérations selon les
contrôles du serveur ; la lecture ne crée pas automatiquement d’OD.
