from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services.dashboard_service import _net_ligne, _article_cout


def test_net_ligne_prend_toutes_les_reductions_en_compte():
    ligne = SimpleNamespace(quantite=2, prix_unitaire=100, remise=10, remise2=25, rabais=5)
    assert _net_ligne(ligne) == 125.0


def test_cout_estime_priorise_cmup_pour_article_stockable():
    article = SimpleNamespace(is_stockable=True, cmup=72, prix_achat_ht=80)
    assert _article_cout(article) == 72.0
    service = SimpleNamespace(is_stockable=False, cmup=0, prix_achat_ht=95)
    assert _article_cout(service) == 95.0


def test_route_dashboard_commercial_est_branchee():
    main = (BACK / 'main.py').read_text(encoding='utf-8')
    route = (BACK / 'routers' / 'dashboard.py').read_text(encoding='utf-8')
    assert 'app.include_router(dashboard.router)' in main
    assert '@router.get("/commercial")' in route
    assert 'construire_dashboard_commercial' in route


def test_dashboard_utilise_les_avoirs_et_le_recouvrement_fact7_8():
    src = (BACK / 'services' / 'dashboard_service.py').read_text(encoding='utf-8')
    assert 'ventilation_avoir' in src
    assert 'construire_situation' in src
    assert 'est_proforma.is_(False)' in src
    assert 'StatutFactureEnum.annulee' in src


def test_front_dashboard_affiche_kpis_et_classements_commerciaux():
    src = (ROOT / 'src' / 'components' / 'DashboardCommercial.jsx').read_text(encoding='utf-8')
    for label in (
        "Chiffre d’affaires HT", 'Achats HT', 'Marge commerciale estimée',
        'Encours clients', 'Taux de recouvrement', 'Top clients',
        'Top fournisseurs', 'Top articles / services', 'Évolution mensuelle',
    ):
        assert label in src


def test_dashboard_ne_depend_plus_des_listes_front_limitees_pour_le_pilotage():
    dashboard = (ROOT / 'src' / 'components' / 'DashboardCommercial.jsx').read_text(encoding='utf-8')
    api = (ROOT / 'src' / 'services' / 'api.js').read_text(encoding='utf-8')
    assert 'dashboardAPI.commercial(exercice)' in dashboard
    assert '/api/dashboard/commercial?' in api
    assert 'limit=100' not in dashboard
