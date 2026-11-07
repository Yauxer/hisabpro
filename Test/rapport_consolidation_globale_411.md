# Globale finale des sources404/405/406 — preuve411

Exécution démarrée le11octobre2026 à21:21UTC, résultat complet récupéré le12octobre à00:49UTC. Aucun runner de cette commande encore actif à la reprise. La preuve est conservée en échec ; un rejeu ultérieur ne la réécrit pas.

3390 cas :3385 réussis,5 échecs,0 erreur,0 ignoré ;4301.675 s,33warnings,exit1 ;721empreintes identiques après exécution.

Commande réelle : `python -X utf8 Test/run_unit_tests.py Test -vv --tb=short --junitxml=.codex-tests/consolidation411_globale.xml`, via le wrapper d'empreintes. Tests PostgreSQLnonce/Edge seulement ; banc07b3 non isolé exclu par le lanceur existant. Aucun PostgreSQL réel ni donnée comptable réelle. Logs/XML locaux non inclus au ZIP.

## Échecs observés

- Test.test_e2e_articles_historique_nombres_isole::test_article_historique_lecture_edition_partielle_et_documents_sans_zero[390]

```text
Test\test_e2e_articles_historique_nombres_isole.py:189: in test_article_historique_lecture_edition_partielle_et_documents_sans_zero
    assert len(diagnostics_stock) > lectures and len(mutations) == n
E   AssertionError: assert (1 > 1)
E    +  where 1 = len([<Request url='http://127.0.0.1:52467/api/devis/diagnostic-stock' method='POST'>])
```

- Test.test_e2e_factures_erreur_lecture_isole::test_liste_vide_chargee_conserve_zero_et_export_disponible[390]

```text
Test\test_e2e_factures_erreur_lecture_isole.py:90: in test_liste_vide_chargee_conserve_zero_et_export_disponible
    connexion(page, application['web_url'], email, password)
Test\test_e2e_administration_isole.py:31: in connexion
    page.wait_for_url("**/dashboard")
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_generated.py:10057: in wait_for_url
    self._sync(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_page.py:590: in wait_for_url
    return await self._main_frame.wait_for_url(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_frame.py:289: in wait_for_url
    async with self.expect_navigation(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_event_context_manager.py:33: in __aexit__
    await self._future
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_frame.py:265: in continuation
    event = await waiter.result()
            ^^^^^^^^^^^^^^^^^^^^^
E   playwright._impl._errors.TimeoutError: Timeout 15000ms exceeded.
E   =========================== logs ===========================
E   waiting for navigation to "**/dashboard" until 'load'
E   ============================================================
```

- Test.test_factD_reglements_delais::test_factD_frais_bancaires_sont_bornes

```text
Test\test_factD_reglements_delais.py:87: in test_factD_frais_bancaires_sont_bornes
    assert 'Les frais bancaires ne peuvent pas être négatifs' in src
E   assert 'Les frais bancaires ne peuvent pas être négatifs' in 'from fastapi import APIRouter, Depends, HTTPException, Query\nfrom sqlalchemy.orm import Session, joinedload\nfrom typing import List, Optional, Literal\nfrom datetime import date as _date, timedelta\nimport json\nimport math\nimport hashlib\nimport re\nfrom uuid import UUID\nfrom sqlalchemy import text\nfrom pydantic import BaseModel, field_validator\nfrom decimal import Decimal, InvalidOperation\nfrom services.devis_stock_service import diagnostic_stock_devis\nfrom database import get_db\nfrom auth import get_current_user, requiert_ecriture\nimport models, schemas\nimport valorisation\nfrom routers.factures import _libelle_ecriture\nfrom services.commercial_numero_service import reserver_numero_commercial\nfrom services.compta_mapping_service import compte_tiers, compte_tiers_facture, compte_tresorerie\nfrom services.auxiliaire_service import rattacher_tiers_aux_lignes\nfrom services.tva_regles_service import valider_tva\nfrom services.exercices_service import trouver_exercice_pour_date\n\nrouter_devis = APIRouter(prefix="/api/devis",          tags=["commercial"])\nrouter_bc    = APIRouter(prefix="/api/bons-commande",  tags=["commercial"])\nrouter_bl    = APIRouter(prefix="/ap...d=societe_id).first()\n    if not reglement:\n        raise HTTPException(404, "Règlement introuvable")\n    _verifier_montant_reglement_historique(reglement)\n\n    if getattr(reglement, "est_comptabilisee", False):\n        raise HTTPException(400, "Ce règlement est déjà comptabilisé.")\n\n    from routers.cloture import exercice_est_clos\n    ex_ref = _exercice_ref(db, societe_id, reglement.date)\n    if exercice_est_clos(db, societe_id, ex_ref):\n        raise HTTPException(423,\n            f"Exercice {ex_ref} clôturé : impossible de comptabiliser ce règlement.")\n\n    module = db.query(models.ModuleActif).filter_by(\n        societe_id=societe_id, module="comptabilite", actif=True).first()\n    if not module:\n        raise HTTPException(400, "Module Comptabilité inactif.")\n\n    facture = None\n    if reglement.facture_id:\n        facture = db.query(models.Facture).filter_by(\n            id=reglement.facture_id, societe_id=societe_id).first()\n\n    _ecriture_reception_reglement(db, societe_id, reglement, facture)\n    reglement.est_comptabilisee = True\n    db.commit()\n    return {"message": f"Écriture générée pour le règlement {reglement.numero or reglement.id}."}\n'
```

- Test.test_patch083_soldes_rapprochement::test_reprise_debut_octobre_calculee_sur_lignes_releve_uniquement

```text
Test\test_patch083_soldes_rapprochement.py:74: in test_reprise_debut_octobre_calculee_sur_lignes_releve_uniquement
    assert calcul(db, 1, '5141', date(2026, 10, 1)) == Decimal('500.00')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_patch083_soldes_rapprochement.py:49: in calcul
    return ns['_solde_initial_periode_suivante'](db, sid, compte, debut)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\routers\rapprochement.py:295: in _solde_initial_periode_suivante
    if any(not _montant_releve_exploitable(m) for _, m in mouvements):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\routers\rapprochement.py:295: in <genexpr>
    if any(not _montant_releve_exploitable(m) for _, m in mouvements):
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   NameError: name '_montant_releve_exploitable' is not defined
```

- Test.test_patch083_soldes_rapprochement::test_releve_annuel_reconstitue_solde_octobre_sans_utiliser_cloture_decembre

```text
Test\test_patch083_soldes_rapprochement.py:106: in test_releve_annuel_reconstitue_solde_octobre_sans_utiliser_cloture_decembre
    assert calcul(db, 1, '5141', date(2026, 10, 1)) == Decimal('500.00')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_patch083_soldes_rapprochement.py:49: in calcul
    return ns['_solde_initial_periode_suivante'](db, sid, compte, debut)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\routers\rapprochement.py:295: in _solde_initial_periode_suivante
    if any(not _montant_releve_exploitable(m) for _, m in mouvements):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\routers\rapprochement.py:295: in <genexpr>
    if any(not _montant_releve_exploitable(m) for _, m in mouvements):
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   NameError: name '_montant_releve_exploitable' is not defined
```

## Analyse initiale et suite

L'oracle frais teste la présence d'un ancien message au lieu du comportement. Le banc AST083 isole une fonction sans sa nouvelle dépendance de qualification des montants ; les appels réels importent le module complet. Ces causes doivent être corrigées dans les tests, sans supprimer les assertions financières ni modifier le produit pour faire passer un oracle obsolète.

Les deux échecs Edge mobiles restent à reproduire : rafraîchissement du diagnostic de stock et délai de navigation après connexion. Aucune cause produit ou environnementale présumée. La suite411 n'est pas déclarée validée. Après correction ciblée : suites connexes, compilation et nouvelle preuve globale sur sources figées, puis couverture et cumulatif.

Recette utilisateur et production non validées ;point6 reste en attente. Paie définitive etEDI dépendent toujours des qualifications officielles documentées.
