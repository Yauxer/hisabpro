# Recette annuelle effet sur mobile — 413

Complément de vérification du [parcours 406](rapport_encaissement_frais_406.md), réellement exécuté sur les sources finales du dépôt. Aucun changement de code produit, aucune assertion métier assouplie. La globale 411 reste distincte, en cours ; ce cas temporaire n'a pas été ajouté à ses 3 390 cas figés.

## Parcours exécuté

Société fictive vierge, exercice 2025 ouvert, dates au 15 juin 2025. Facture de laboratoire HT 100 / TVA 20 / TTC 120 créée, validée et comptabilisée via API ; règlement par effet, remise, encaissement avec frais 10,01, validation des trois nouveaux brouillons, proposition de rapprochement puis confirmation, lettrage AAA et rechargement par Edge réel, largeur 390. Aucun appel métier simulé. La migration 084 a été rejouée uniquement dans le PostgreSQL nonce protégé du banc.

Quatre pièces / dix lignes, débit = crédit = 480 ; client et attentes soldés, banque 109,99 et frais 10,01. Contrôle et export FEC réels avant clôture ; annulation de l'instrument encaissé refusée 409, originaux inchangés.

Clôture 2025 par interface : résultat 89,99 avant impôt de laboratoire 3 000, résultat après impôt −2 910,01. À-nouveaux 2026 validés, quatre lignes, débit = crédit = 3 020 : 5141 débit 109,99 ; 1199 débit 2 910,01 ; 4455 crédit 20 ; 4453 crédit 3 000. Toutes les périodes 2025 fermées ; photographies des écritures originales identiques. FEC des deux exercices équilibrés. Pointage 2025 conservé en lecture seule ; tentative de dérapprochement 409 et bouton de proposition désactivé.

Ces chiffres qualifient un oracle de test du comportement actuel, pas l'applicabilité réglementaire d'un régime fiscal. Année réduite ; aucun résultat de recette humaine ou scénario annuel exhaustif annoncé. Aucun PostgreSQL réel ni donnée comptable réelle touchés. Le banc vérifie également l'arrêt de ses processus et la suppression de ses seuls répertoires nonce après exécution.

## Preuve et reproduction

Un test réussi, zéro échec/erreur/ignoré, durée XML 25.972 s ; sortie réelle pytest : 1 passed, 26 warnings in 25.98s, code 0. Les 721 empreintes des sources finales sont identiques après commande.

Commande exécutée :

```powershell
python -X utf8 Test/run_unit_tests.py .codex-tests/test_annuel413_temporaire.py -vv --tb=short --junitxml=.codex-tests/annuel413.xml
```

Le banc temporaire ci-dessous reprend exactement le contrôle de clôture du test annuel existant et appelle son parcours avec effet/mobile au lieu de chèque/bureau. Il ne remplace aucune API et ne modifie pas les sources. Il est reproduisible dans le dossier temporaire .codex-tests ; les caches et artefacts d'exécution sont exclus du ZIP.

```python
"""Variante indépendante : effet mobile, assertions annuelles existantes inchangées."""
from pathlib import Path
import sys,ast,inspect
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'Test'))
import test_e2e_encaissement_frais_rapprochement_isole as parcours
application=parcours.application
migration=parcours.migration

def test_annee_effet_mobile_2025_2026(application,migration):
    # Extraire seulement le contrôle après clôture ; aucune assertion modifiée.
    source=inspect.getsource(parcours.test_annee_frais_2025_cloture_an2026_pointage_archive_et_fec)
    arbre=ast.parse(source)
    fonction=arbre.body[0].body[0]
    assert isinstance(fonction,ast.FunctionDef) and fonction.name=='cloturer'
    module=ast.Module(body=[fonction],type_ignores=[])
    controles=dict(vars(parcours))
    exec(compile(ast.fix_missing_locations(module),'<controle_annuel_406_inchange>','exec'),controles)
    parcours.test_encaissement_frais_validation_proposition_et_lettrage(
        application,migration,'effet',390,annee=2025,controle_apres=controles['cloturer'])
```

Prochaine action : vérifier l'achèvement de la globale 411, ne pas la relancer si elle tourne encore. Ensuite intégrer cette variante à la suite persistante sous un lot distinct, après validation du gel actuel, puis étendre les instruments groupés et le scénario annuel exhaustif. Paie définitive / EDI et point 6 restent soumis aux limites déjà consignées.
