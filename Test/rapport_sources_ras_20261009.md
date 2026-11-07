# Retenues à la source : preuves primaires et limites d’applicabilité

Lot documentaire 294 — 9 octobre 2026. Ce complément consigne la recherche
bornée de la précédente exécution, vers 16:51–16:58 UTC. Il ne recommence pas
l’[audit RAS 208](../docs/audit/AUDIT_RAS_HISABPRO_20261007.md) et ne constitue
ni une certification fiscale ni une validation d’un dossier réel.

La rédaction reprend à 19:47 UTC après consignation du lot. Les accès web décrits
ci-dessous sont ceux de la recherche précédente, pas de nouvelles consultations
prétendues à cette heure. Aucune base, donnée comptable, migration ou source
applicative n’a été modifiée dans ce lot.

## Source primaire effectivement accessible

[Bulletin officiel n° 7465 bis, édition de traduction officielle, 16 décembre 2025](https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7465-bis_fr.pdf).
Le lecteur web a ouvert un PDF de **107 pages** sur le domaine du SGG. Les
passages ciblés ont été lus dans son extraction ; cela ne signifie pas que
les 107 pages ont été examinées une à une. Le sommaire et la page imprimée 3810
identifient le dahir n° 1-25-67 du 10 décembre 2025 promulguant la loi de
finances n° 50-25 pour 2026. Aucun exemplaire téléchargé ni SHA de ce PDF
n’est produit dans ce lot.

| Passage ciblé | Page imprimée / page PDF, comptée depuis 1 | Portée de la lecture |
|---|---|---|
| Modification de l’article 117-V-c | 3834 / 26 | Extension conditionnelle ; versement et attestation. |
| Modification des articles 151 et 157-I | 3837 / 29 | 151-V concerne un état de produits de location ; 157 distingue versement, mise à disposition et inscription en compte. |
| Article 247-XXXXVI et article 7-IV de la LF | 3841 / 33, suite 3842 / 34 | Dispositions transitoires et dates d’effet, distinctes de la publication. Les paragraphes 5 et 13 visent le 1er juillet 2026 pour les extensions considérées. |
| Décret n° 2-25-1041 du 15 décembre 2025 | 3915 / 107 | Modification du rattachement de la liste B à l’article 117-V-b/c ; pas reproduction exhaustive des prestations. |

Le texte de cette loi modificative contient des pointillés et renvois à la suite
inchangée. Il ne remplace donc pas le CGI consolidé : article 151-I complet,
calendrier intégral de l’article 157, règles intégrales de l’article 117 et
qualification des opérations restent à obtenir. Aucune assiette, liste ou
retenue universelle ne peut être déduite de ces seuls amendements.

## Autres références et résultat réel des accès

| Référence primaire | Résultat constaté pendant la recherche |
|---|---|
| [Catalogue MEF des publications](https://www.finances.gov.ma/fr/Pages/publications.aspx) | Extrait indexé consulté : CGI 2026 annoncé le 05/01/2026 ; note circulaire 737 annoncée le 10/03/2026. Ouverture directe : timeout. Ces dates de catalogue ne sont pas des dates d’effet des règles. |
| [CGI 2026, publication MEF](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf) | Extraits indexés trouvés ; ouverture du PDF complet : timeout. Tentative HTTP Python en mémoire sur MEF : ConnectTimeout, limite de connexion 12 secondes. Pas de texte consolidé complet ni d’empreinte obtenus. |
| [Adresse DGI du CGI 2026](https://tax.gov.ma/wps/wcm/connect/08712531-1e81-4e28-a38b-2bd9edf8e09e/CGI+2026+FR.pdf) | L’adresse repérée dans une référence de navigation a été essayée directement ; erreur du lecteur web. Son contenu n’a pas été utilisé comme preuve. |
| [Note circulaire DGI 735, LF 2024](https://www.finances.gov.ma/Publication/dgi/2024/Note-Circulaire735LF2024.pdf) | Extrait primaire indexé, page imprimée 24, consulté : modalités de versement des retenues TVA concernées au mois suivant chaque paiement. Ouverture complète en échec. Référence historique, pas validation exhaustive de son articulation avec 2026. |
| Note circulaire DGI 737, LF 2026 | Présence confirmée dans le catalogue primaire indexé ; PDF primaire complet et lien de téléchargement exact non obtenus. Les copies et commentaires commerciaux ne servent pas de support normatif. |
| [Publication MEF Al Maliya, spécial LF 2026](https://www.finances.gov.ma/Maliya%20tawassol/SLF2026-Fr.pdf) | Déjà référencée dans l’audit 208 ; nouvelle ouverture directe en timeout. Aucune nouvelle lecture complète déclarée. |

La version MEF du BO a également rencontré un timeout ; c’est l’[adresse SGG](https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7465-bis_fr.pdf)
qui a permis la lecture ciblée réelle. L’échec d’un accès ne signifie pas que le
texte ou la règle n’existe pas. Un extrait indexé ne vaut pas lecture intégrale.

## Conséquence pour les travaux techniques indépendants

La qualification automatique complète des retenues HT IS/IR et TVA reste
**bloquée faute de preuve consolidée suffisante**. Ce constat n’interdit pas les
travaux indépendants, mais impose de conserver explicitement leurs limites :

- Une estimation calculée sur une facture n’établit pas, à elle seule, une
  retenue effectivement opérée, son bénéficiaire fiscal, sa justification ou
  son admissibilité en crédit d’impôt.
- Le versement, la mise à disposition et l’inscription en compte ne sont pas
  interchangeables avec une simple date de facture ou le premier règlement.
- L’extrait TVA cité ne démontre pas un prorata universel de RAS HT pour toute
  facture, tout paiement partiel, chèque, effet ou acompte. Aucun taux ou
  automatisme fiscal nouveau n’est prescrit ici.

Le lot **291**, consigné mais encore en cours au moment de cette rédaction,
vise une correction technique : séparer l’estimation du montant effectivement
comptabilisé dans le solde et supprimer l’assimilation automatique de toute
l’estimation au premier règlement. Son succès et ses résultats de tests ne
sont pas déclarés par ce rapport ; ils appartiennent à son propre compte rendu.
Une écriture RAS historique existante ne devient pas, du seul fait de sa prise
en compte technique, une retenue juridiquement justifiée.

Le lot **293**, envisagé pour une capture explicite, devra conserver l’événement,
le montant effectivement déclaré par l’opérateur et son justificatif sans
inventer les faits manquants. Cette capture ne vaudra pas validation fiscale
automatique, preuve d’un reversement au Trésor ou autorisation d’imputer un
crédit. Il ne s’agit pas d’une fonctionnalité déjà testée ou livrée dans ce lot.

## Vérifications et prochaine action

Seul ce fichier Markdown est ajouté. Contrôle local réellement exécuté par
Python en ligne de commande, code 0 : décodage UTF-8 strict, absence de caractères
de remplacement, syntaxe de sept liens HTTPS et existence du chemin vers
l’audit 208 ; références de pages et limites d’accès également contrôlées. Ce contrôle
documentaire ne certifie pas l’accessibilité actuelle de toutes les URL.
Aucun test API, PostgreSQL ou navigateur applicatif n’est exécuté dans le lot
294 ; les résultats des autres lots ne sont pas réattribués à celui-ci.

Prochaine action normative précise : obtenir le CGI 2026 et la note 737 complets
depuis DGI/MEF, relire les articles 15 bis, 19, 73, 117, 151, 157, 171/174 et
247 avec leurs dates d’effet et les listes réglementaires applicables ; définir
ensuite un cas fiscal qualifié avec le payeur, le bénéficiaire, l’opération,
l’événement et les justificatifs. En attendant, poursuivre uniquement les
corrections techniques et la traçabilité explicite, sans réparation de données
comptables réelles ni présentation de conformité automatiquement validée.
