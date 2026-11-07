# Mode d’emploi des avancées — lot323 — 10 octobre2026

Demande utilisateur : fournir un document Word expliquant comment utiliser et
vérifier les avancées présentées au partenaire. Lot exclusivement documentaire,
sans modification frontend/backend, migration, connexion DB ni nouvelle recette
métier. Les travaux applicatifs318/320 restent en attente.

## Sources vérifiées

AGENTS.md, état réel de Sidebar.jsx, Layout.jsx, GestionExercices.jsx, Parametres.jsx,
Commercial.jsx, Factures.jsx, Acomptes.jsx, Inventaire.jsx, Immobilisations.jsx,
LiasseFiscale.jsx, CNSS.jsx, CompteSecurite.jsx, ImportBalanceLiasse.jsx et
RapprochementBancaire.jsx. Annexes commerciales, achats partiels, inventaire et
captureRAS relues, matrice/checklist et historique du journal consultés.

Une première rédaction plaçait la gestion des exercices sur le tableau de bord ;
la recherche du composant réel l’a corrigée en Comptabilité → Clôture d’exercice
→ Gestion des exercices. Une normalisation par pipeline PowerShell a introduit
des caractères « ? » dans une phrase : détectés lors de l’extractionPDF, corrigés
avant livraison par patchUTF-8. Les images finales sont issues de la version
regénérée, pas d’un brouillon.

## Livrables

- docs/guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx : vrai packageOOXML,
  styles titres, navigation par titres Word, en-tête, pied de page numéroté et
  tableau utilisateur éditable.
- Même guide enPDF :22pages,18fiches, parcours/manipulations/prérequis,
  montants/écritures attendus, preuves et limites.
- SourceMarkdown et générateur reproductible sans connexion DB. Le générateur
  Word utilise la bibliothèque standard ; le PDF utilise ReportLab et Arial
  Unicode de Windows. Aucun paquet installé.

## Vérifications réellement exécutées par le principal

1. Générateur docs/guide/generer_guide.py : code0,374blocs, Word/PDF produits.
2. py_compile du générateur : code0.
3. Vérificateur local .codex-tests/verifier_guide_323.py : code0. Toutes les
   partiesXML/relations et CRC duDOCX lus ;18chapitres et17lignes de suivi avec
   statutNon testé, destinations des relations présentes ; toutes les22pages
   PDF extraites, sans caractère de remplacement ;11chemins de références
   explicites présents.
4. Calculs indépendantsDecimal : vente1000+200=1200,400+800=1200,
   D=C2400 ; achat4×500+400=2400 et D=C4800 ; stock8×20=160,
   banque760, actif960 et D=C1640 ;3333,33+3333,33+3333,34=10000 ;
   captureRAS1200−400−30=770, puis−700−70=0. Aucune référence à un moteur
   métier pour valider ces arithmétiques.
5. Rendu réelPDF viaPyMuPDF : pages1/4/9/20 ; pages1/4/20 vues par le
   principal, titres, paragraphes et marges lisibles sans troncature observée.
6. Livraison ZIP : liste explicite, CRC et comparaison des octets de chaque
   fichier avec le dépôt avant remise.

## Limites conservées

Microsoft Word n’a pas été ouvert ici ; leDOCX est vérifié structurellement,
la pagination et le rendu Word restent à contrôler par l’utilisateur. La version
PDF a été rendue et contrôlée séparément. Aucun parcours de recette de ce guide
n’a été exécuté sur une base réelle. Tous les résultats utilisateur restent
Non testé ; les tests métier historiques ne sont pas requalifiés par ce guide.

La globale315 a terminé son écriturelog/XML pendant les échanges utilisateur :
2742passed/49failed/5errors en3410,26s,32warnings,653empreintes inchangées
vérifiées avant ce lot. Son code retour wrapper n’a pas encore été récupéré et
son analyse reste à faire ; elle n’est pas déclarée réussie. Ces résultats sont
distincts des vérifications documentaires323.

Prochaine tâche de développement : récupérer et analyser315, puis reprendre
les lots318/320 seulement après conservation de sa preuve. Pour l’utilisateur :
ouvrir leWord et suivre les fiches01–06 sur une installation de recette isolée.
