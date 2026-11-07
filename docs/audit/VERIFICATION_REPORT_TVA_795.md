# Vérification du report TVA — correctif795

Source primaire consultée le24octobre2026 :[CGI2025 publié par le CRI Casablanca-Settat](https://casainvest.ma/sites/default/files/2025-02/cgi-2025-fr.pdf),[page de publication](https://casainvest.ma/fr/node/664).

Article101§2 (page182 imprimée) :le reliquat de taxe déductible non imputé est reporté à la période suivante. Article112I7et9 (pages194–195) :la déclaration distingue crédit antérieur et montant à verser ou crédit reportable.

Portée de la correction :aucun taux,faitgénérateur oucritère d'éligibilité modifié. Lesfactures/avoirs et leursdates restent traités en amont par le routeur existant. Le calcul du solde conserve maintenant les deux nets signés qui lui sont fournis. Seuls le montant final à payer et le crédit final sont positifs ou nuls.

Preuve indépendante du cahier :crédit antérieur1800,TVAcollectée-500 etTVArécupérable2400 donnent crédit final4700. L'ancien calcul remplaçait-500 par0 etproduisait4200. Il masquait aussi une récupération nette négative ;cinq tests couvrent ces signes et un cas positif inchangé.

Aucun remboursement automatique n'est ajouté. Aucune déclaration n'est déposée,aucune écriture ou pièce historique modifiée. Lesconditions propres aux justificatifs etaux dossiersréels restent distinctes de ce correctifarithmétique.
