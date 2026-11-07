# Paie marocaine : preuves primaires et limites du référentiel 2026

Analyse du **8 octobre 2026 UTC**, lot `PAIE-SOURCES-PRIMAIRES-20261008`. Lecture seule de l’application ; aucune migration, donnée, règle ou écriture modifiée. Ce document ne valide pas une paie complète et ne constitue pas une certification.

## Conclusion

Le volet IR général dispose de preuves officielles indexées explicitement dans le CGI 2026 et la LF 2026. Plusieurs règles sociales sont également documentées par l’ACAPS, autorité publique compétente. Cependant, la confirmation complète **pour 2026** des branches CNSS, de leurs parts exactes et des conditions d’application n’est pas acquise : portail CNSS indisponible, fiche synthétique ancienne et guide institutionnel 2020 non actualisé. Ne pas activer une paie définitive ou mettre silencieusement à jour les taux historiques à partir de cette analyse.

## Sources consultées et niveau de preuve

| Référence primaire | Accès réellement obtenu | Ce qu’elle permet d’établir / limite |
|---|---|---|
| [CGI 2026, DGI/MEF](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf), articles 59, 73, 74 | Extraits du PDF officiel renvoyés par recherches ciblées, pages imprimées 98, 119 et 125. Ouverture directe via navigateur outil : erreur interne ; tentative Python `requests.get(timeout=12)` : ConnectTimeout, aucun PDF téléchargé. | Règles IR générales ci-dessous vérifiables dans l’index primaire ; aucune prétention de lecture intégrale du PDF. Conditions particulières et règles de retenue mensuelle restent à instruire. |
| [LF 2026, BO 7465 bis](https://www.finances.gov.ma/Publication/db/2025/BO_7465-bis_fr.pdf), page imprimée 3833 | Passage officiel indexé : modification de l’article 74 | Confirme modification familiale 2026 ; ne documente pas l’ensemble de la paie. |
| [ACAPS — AMO](https://www.acaps.ma/fr/grand-public/sante/couverture-medicale-de-base-amo) | Page officielle ouverte intégralement ; passage « Secteur privé », lignes 166–170 de l’extraction web | Actifs privés : 4,52 % partagé également salarié/employeur, majoration patronale 1,85 %. Soit arithmétiquement 2,26 % salarié et 4,11 % employeur. Taux spécifiques pêcheurs distincts. Page sans date d’effet normative explicite. |
| [ACAPS — fiche synthétique CNSS](https://acaps.ma/sites/default/files/fiche_synthetique_cnss.pdf) | PDF officiel ouvert, 3 pages ; page 2, lignes 47–53 | Allocations familiales 6,40 % salaire réel employeur ; CT 1,57 % et LT 11,89 %, plafond mensuel 6 000, partage 2/3–1/3. Fiche non millésimée 2026 : ne pas convertir ce partage en parts arrondies juridiquement confirmées. |
| [Décret 2-73-633, version publiée par ACAPS](https://www.acaps.ma/sites/default/files/publication_documents/decret_ndeg_2-73-633.pdf), articles 2–5 | PDF officiel ouvert, 3 pages ; page 1 | TFP 1,6 % des rémunérations brutes mensuelles, charge exclusive employeur ; champ d’assujettissement défini. Version historique consolidée, modifications citées 1986/1995/2002 ; pas preuve d’une revue exhaustive des textes jusqu’à octobre 2026. |
| [AMDIE — Guide des affaires 2020, hébergé par Maroc PME](https://marocpme.gov.ma/wp-content/uploads/2021/12/AMDIE_Guide-des-affaires-au-Maroc_2020.pdf), page 72 | Tableau institutionnel renvoyé par index ; ouverture directe timeout | Donne CT 1,05 % patronal / 0,52 % salarial, LT 7,93 % / 3,96 %, AF 6,4 %, AMO 4,11 % / 2,26 %, TFP 1,6 %. Source explicitement **2020**, elle ne valide pas les paramètres 2026. Signale des exceptions AMO et TFP. |
| [CNSS — paiement des cotisations](https://www.cnss.ma/fr/content/paiement-de-vos-cotisations-sociales) | Ouverture erreur interne, recherches ciblées CNSS sans extrait exploitable | Taux et actualité 2026 non directement confirmés. |
| [Ma CNSS](https://macnss.ma/), lien fourni par la page officielle ACAPS | Clic réel : timeout | Aucun document exploitable ; aucun accès authentifié tenté. |

Les sites privés apparus dans les résultats n’ont pas été utilisés comme preuves normatives. La date de crawl d’une page n’est pas la date d’entrée en vigueur de son contenu.

## IR général : éléments documentés, sans automatiser les conditions

CGI 2026 : article 59-I-A, frais professionnels 35 % jusqu’à 78 000 MAD de revenu brut annuel imposable ; au-delà, 25 % plafonnés à 35 000 MAD. Ce cadre général ne couvre pas les catégories professionnelles particulières des paragraphes B/C. L’assiette des avantages et les autres déductions nécessitent une qualification séparée.

Article 73-I : barème annuel par tranches : jusqu’à 40 000 : 0 % ; 40 001–60 000 : 10 % ; 60 001–80 000 : 20 % ; 80 001–100 000 : 30 % ; 100 001–180 000 : 34 % ; surplus : 37 %. Les déductions fixes présentes dans le dépôt sont une traduction arithmétique de la progressivité, pas des taux supplémentaires.

Article 74 : réduction annuelle 600 MAD par personne à charge, plafond 3 600 MAD. L’existence d’un conjoint ou d’un enfant ne suffit pas : l’éligibilité dépend des conditions légales, notamment du revenu des enfants. Le compteur confirmé `personnes_charge_ir` est préférable à une déduction automatique depuis la situation familiale. La vérification exhaustive des autres conditions, dont âge et situations particulières, reste nécessaire avant paie définitive. [Sources : CGI 2026](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf), [modification LF 2026](https://www.finances.gov.ma/Publication/db/2025/BO_7465-bis_fr.pdf).

## Constat dans le dépôt

- `hisabpro-backend/services/paie_service.py` : simulation fixe sur mois complet, Decimal, contrôles de finitude et de présence/doublons ; cinq codes attendus dont `amo_participation`. Cotisations sur assiette brute simplifiée, plafonds annuels divisés par 12, frais professionnels généraux, compteur IR explicitement confirmé. Aucun bulletin définitif, écriture, déclaration, variables ou proratisation. Avertissement social non vérifié affiché.
- `hisabpro-backend/routers/employes.py` : simulation annuelle/mensuelle sur paramètres de l’année exacte ; absence de référentiel et entrées/sorties en cours de mois bloquées, pas de repli vers une autre année. Total absent si simulation incomplète.
- `hisabpro-backend/donnees_fiscales.sql` : barème IR général 2025/2026 et réduction familiale 600 en 2026 déjà présents. Les taux sociaux historiques affichent patronal `cnss_retraite=0.0798`, `cnss_prest_fam=0.0692` avec plafond 72 000 annuel, aucune ligne `amo_participation`, accident contractuel fixé à 1 %. Ces paramètres ne sont pas justifiés par les sources obtenues ; le moteur bloque déjà le code manquant. **Ne pas exécuter ce script**, qui remplace les lignes annuelles par DELETE/INSERT, pour « réparer » une base réelle.
- `hisabpro-backend/models.py` : `BaremeIR`, `TauxCotisation`, `DeductionIR` stockent année et valeurs, sans provenance, date d’effet, version, statut de confirmation ou pièce source. Une année seule ne prouve pas la validité d’un taux.
- `hisabpro-backend/080_dossiers_employes.sql` : ajoute le dossier salarié et le compteur nullable de personnes à charge, sans nouveaux taux. `025_css_credits_is.sql` concerne IS/CSS, et non un référentiel paie : ne pas lui attribuer une fonction inexistante.
- `hisabpro-backend/routers/parametres.py` contient encore deux helpers historiques avec valeurs de secours, calcul float et hypothèses familiales. Recherche des références : aucun appel depuis les routes actuelles en dehors de leur appel interne. Ne pas réintroduire ces helpers dans le flux de paie ; leur présence n’est pas une validation de leur formule.

## Prochain lot proposé, sous réserve de preuves complémentaires

Priorité indépendante : concevoir la traçabilité annuelle du référentiel (source, article, date d’effet, date de vérification, périmètre/régime, version et confirmation) et des snapshots de simulations. Toute migration éventuelle doit être additive et ne doit ni réécrire les années existantes ni activer des taux non confirmés. Les paramètres historiques restent signalés ; aucun « barème complet validé 2026 » ne doit être annoncé.

Pour débloquer les calculs sociaux définitifs : obtenir une preuve CNSS/texte consolidé applicable 2026 des branches CT/LT et parts exactes ; confirmer les exceptions AMO/TFP, assiettes et arrondis ; qualifier les éléments de rémunération et les régimes particuliers. Les bulletins, variables, avances, déclarations, journal de rémunération et clôture de paie restent des travaux distincts après ces validations.

## Vérification documentaire

Les commandes de cette étape ont uniquement lu les fichiers et consulté les sources. Aucun test métier n’a été déclaré réussi par cet audit. Les accès web réussis, indexés et échoués sont distingués ci-dessus. Contrôle documentaire Python réellement exécuté : UTF-8 lisible, huit URL primaires uniques et six chemins de fichiers cités présents, mention explicite d’absence de test métier validé. Le fichier du présent rapport est le seul différentiel ; le journal et son ZIP seront vérifiés par l’agent principal.
