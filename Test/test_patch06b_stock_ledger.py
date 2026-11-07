from types import SimpleNamespace

from services.stock_ledger_service import auditer_mouvements_article


def art(stock=6, cmup=100):
    return SimpleNamespace(id=1, code="A1", designation="Article", stock_actuel=stock, cmup=cmup)


def m(i, typ, qte, avant, apres, cout, cmup):
    return SimpleNamespace(id=i, type=typ, quantite=qte, stock_avant=avant, stock_apres=apres,
                           cout_unitaire=cout, cmup_apres=cmup)


def test_chaine_cmup_ok():
    r = auditer_mouvements_article(art(), [
        m(1, "entree", 10, 0, 10, 100, 100),
        m(2, "sortie", 4, 10, 6, 100, 100),
    ])
    assert r["statut"] == "ok"
    assert r["nb_erreurs"] == 0


def test_rupture_continuite_detectee():
    r = auditer_mouvements_article(art(stock=5), [
        m(1, "entree", 10, 0, 10, 100, 100),
        m(2, "sortie", 5, 9, 4, 100, 100),
    ])
    assert any(a["code"] == "rupture_continuite" for a in r["anomalies"])


def test_sortie_mauvais_cmup_detectee():
    r = auditer_mouvements_article(art(), [
        m(1, "entree", 10, 0, 10, 100, 100),
        m(2, "sortie", 4, 10, 6, 80, 90),
    ])
    codes = {a["code"] for a in r["anomalies"]}
    assert "cout_sortie_cmup" in codes
    assert "cmup_modifie_sortie" in codes


def test_stock_sans_historique_warning():
    r = auditer_mouvements_article(art(stock=3, cmup=50), [])
    assert r["statut"] == "warning"
    assert any(a["code"] == "stock_sans_historique" for a in r["anomalies"])


if __name__ == "__main__":
    test_chaine_cmup_ok()
    test_rupture_continuite_detectee()
    test_sortie_mauvais_cmup_detectee()
    test_stock_sans_historique_warning()
    print("OK — 4 tests Patch 06B audit mouvements & CMUP")
