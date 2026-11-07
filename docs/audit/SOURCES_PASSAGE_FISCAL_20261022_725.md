# Sources et périmètre725

Source de code : dépôt local, moteur fiscalite_is_service.calculer_is existant,
base pure extraite sans changement des formules ou taux historiques. Détail B11
et garde119 partagés. Nouvel usage : taux explicitement déclaré, sans choix
juridique automatique ; disponible de déficit explicitement justifié et revu.

Source officielle recherchée : https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf
L’index officiel renvoie des extraits de l’article19. Ouverture directe et
httpx timeout : PDF intégral non obtenu, non lu intégralement, aucun hash de
source disponible. Ne pas présenter cette tentative comme validation officielle.
Aucune nouvelle règle fiscale, délai de report, taux ou avantage n’a été codé.
La qualification des déficits, leur millésime et le taux applicable restent à
justifier humainement. Toute extension normative exige la source officielle
complète applicable. Aucun XML/EDI inventé.

Oracles indépendants dans generer_passage725.py et tests725, aucune importation
du moteur fiscal dans le générateur documentaire. Taux20 et19,999 fictifs pour
vérifier l’arithmétique, pas une recommandation pour une société réelle.
