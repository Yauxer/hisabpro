# Comparaison de la base annuelle arrondie — 911

Dans **05 · Fiscalité salariale → Contrôle annuel IR**, un nouveau contrôle conserve deux calculs distincts : le calcul mathématique sur le RNI annuel déclaré et une comparaison après arrondi de cette base annuelle à la dizaine supérieure. Les tranches et la réduction familiale utilisent la même fonction métier.

La règle de base est vérifiée dans le [CGI2026 publié par la DGI, copie duCRI](https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf), article167, page imprimée317. Le PDF téléchargé compte765pages et6417906octets, SHA-256 `fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1`. Le passage concerné a été lu ; aucune lecture intégrale des765pages n'est revendiquée.

## Utilisation

Créer un contrôle annuel comme dans le [guide901](CONTROLE_IR_ANNUEL_901.md). Saisir un RNI annuel déjà établi, les références et les personnes fiscalement éligibles ; confirmer le cadre général, l'éligibilité et le périmètre arithmétique. Aucun nouveau champ obligatoire n'a été ajouté.

Exemple fictif : RNI **40000.01**, personnes **0**, référenceRNI `RNI-FICTIF911`, référencefamille `FAMILLE-FICTIVE911`, motif `Contrôle annuel FICTIF911`, confirmations cochées après contrôle du jeu fictif. Le calcul sans arrondi reste **0.0010**. La comparaison affiche base **40010.00**, impôt avant réduction **1.0000**, réduction **0.0000**, impôt comparatif **1.0000**, écart **0.9990**. Une base déjà multiple de10 n'est pas augmentée.

Une famille inconnue laisse le résultat après réduction inconnu. Un RNI non confirmé ne produit pas une base zéro. La réduction reste plafonnée à l'impôt, sans crédit fictif. Le référentiel, la règle, la source et son empreinte restent attachés au nouveau contrôle.

## Périmètre à respecter

Ce calcul concerne **une base annuelle déclarée dans le cadre général2026**. Il ne détermine pas une retenue mensuelle, les imputations déjà effectuées ou une somme à verser. L'arrondi d'un versement prévu par le même article n'est pas appliqué à un versement inconnu. Aucun résultat n'est transformé en net de paie ou déclaration automatiquement.

Les contrôles historiques conservent leurs contenus, empreintes et référentiels. Ils n'acquièrent pas rétroactivement la comparaison911. Reprendre exactement une ancienne requête avec sa clé conserve son ancien résultat ; créer un nouveau contrôle pour obtenir une nouvelle comparaison. Aucune migration n'est nécessaire pour911 ; le socle119/120 demeure nécessaire aux bases fiscales909.

Les frais professionnels, les autres déductions et la mensualisation restent à terminer selon [la reprise909](REPRISE_PAIE_APRES_BASES_909.md). Cette étape ne constitue pas une certification ou une recette utilisateur validée.
