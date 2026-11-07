"""069 — un service ne déclenche ni alerte de stock ni mouvement physique."""
import ast
import json
import subprocess
import shutil
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'hisabpro-backend' / 'routers'


def _fonction_depuis_source(fichier, nom, contexte):
    """Charge la vraie fonction sans initialiser FastAPI ni demander PostgreSQL."""
    tree = ast.parse((BACKEND / fichier).read_text(encoding='utf-8'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == nom)
    ns = dict(contexte)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(BACKEND / fichier), 'exec'), ns)
    return ns[nom]


class _ErreurHTTP(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _article(stockable, stock, id):
    return types.SimpleNamespace(id=id, is_stockable=stockable, stock_actuel=stock, designation=f'Article {id}')


def _ligne(article, qte=2):
    return types.SimpleNamespace(
        id=article.id, article_id=article.id, description=article.designation,
        quantite=qte, quantite_livree=qte, quantite_prevue=qte,
    )


@pytest.mark.parametrize('stockable,stock,attendus', [
    (False, 0, 0),  # prestation : zéro stock physique, aucune sortie
    (True, 0, -1),  # article stockable : garde-fou préservé
    (True, 3, 1),   # article stockable disponible : une sortie
])
def test_069_livraison_stock_physique_seulement(stockable, stock, attendus):
    art = _article(stockable, stock, 10)
    mouvements = []
    class Requete:
        def filter_by(self, **kwargs): return self
        def first(self): return types.SimpleNamespace(stock_declencheur_vente='bl')
    db = types.SimpleNamespace(query=lambda model: Requete(), rollback=lambda: None)
    fn = _fonction_depuis_source('commercial.py', '_mouvement_stock_bon_livre', {
        'models': types.SimpleNamespace(Societe=object()),
        '_article_ligne': lambda db, sid, aid, description: art,
        'valorisation': types.SimpleNamespace(enregistrer_mouvement=lambda *args, **kwargs: mouvements.append((args, kwargs))),
        'HTTPException': _ErreurHTTP,
    })
    bl = types.SimpleNamespace(statut='livre', type='vente', lignes=[_ligne(art)],
                               numero='BL-TEST', tiers='Client', facture_id=None, date='2026-09-20', id=18)
    if attendus == -1:
        with pytest.raises(_ErreurHTTP, match='Stock insuffisant pour livrer') as exc:
            fn(db, 1, bl, 'en_preparation')
        assert exc.value.status_code == 400
    else:
        fn(db, 1, bl, 'en_preparation')
        assert len(mouvements) == attendus
        if mouvements:
            assert mouvements[0][0][3:5] == ('sortie', 2)


@pytest.mark.parametrize('stockable,stock,attendus', [(False, 0, 0), (True, 0, -1), (True, 5, 1)])
def test_069_validation_facture_stock_physique_seulement(stockable, stock, attendus):
    art = _article(stockable, stock, 11)
    mouvements = []
    fn = _fonction_depuis_source('factures.py', '_mouvements_stock_validation_facture', {
        '_verifier_conformite_tva_facture': lambda facture: None,
        '_stock_sur_facture': lambda db, sid, vente: True,
        '_article_facture': lambda db, sid, aid, description: art,
        'valorisation': types.SimpleNamespace(enregistrer_mouvement=lambda *args, **kwargs: mouvements.append((args, kwargs))),
        'HTTPException': _ErreurHTTP,
    })
    facture = types.SimpleNamespace(type='vente', lignes=[_ligne(art)], numero='FA-TEST',
                                    tiers='Client', id=19, date='2026-09-20')
    if attendus == -1:
        with pytest.raises(_ErreurHTTP, match='Stock insuffisant pour valider') as exc:
            fn(None, 1, facture)
        assert exc.value.status_code == 409
    else:
        fn(None, 1, facture)
        assert len(mouvements) == attendus
        if mouvements:
            assert mouvements[0][0][3:5] == ('sortie', 2)


def test_069_avertissement_devis_article_stockable_uniquement():
    if not shutil.which('node'):
        pytest.skip('Node.js absent')
    js = '''import {stockInsuffisantPourDevis as f} from "./src/utils/stockWarnings.js";
const base={article_id:1,quantite:2,stock_actuel:0};
const result=[f({...base,is_stockable:false}),f({...base,is_stockable:true}),
 f({...base,is_stockable:true,stock_actuel:3}),f({...base,is_stockable:true,stock_actuel:null}),
 f({...base,is_stockable:true,article_id:null}),f({...base,is_stockable:true,stock_actuel:"0"})];
console.log(JSON.stringify(result));'''
    proc = subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT,
                          capture_output=True, text=True, check=True)
    assert json.loads(proc.stdout.strip()) == [False, True, False, False, False, True]


def test_069_alertes_et_parcours_commerciaux_respectent_nature_article():
    commercial = (BACKEND / 'commercial.py').read_text(encoding='utf-8')
    factures = (BACKEND / 'factures.py').read_text(encoding='utf-8')
    articles = (BACKEND / 'articles.py').read_text(encoding='utf-8')
    frontend = (ROOT / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
    # Le diagnostic des devis utilise maintenant le cumul lu par API (lot 241),
    # vérifié en création et édition par la recette Edge du lot 242.
    assert 'is_stockable: art.is_stockable === true' in frontend
    assert 'a.is_stockable === true && a.stock_actuel' in frontend
    assert 'if stock_a_la_facture and art is not None and art.is_stockable:' in commercial
    assert 'if article is not None and article.is_stockable and qte > 0:' in commercial
    assert 'if article is not None and article.is_stockable:' in factures  # édition brouillon
    assert 'if article is not None and article.is_stockable and (article.stock_actuel or 0) < l.quantite:' in factures  # proforma
    assert 'if est_vente and article is not None and article.is_stockable and (article.stock_actuel or 0)' in factures
    alertes = articles.split('def alertes_stock(', 1)[1].split('@router.get(', 1)[0]
    assert 'actif=True, is_stockable=True' in alertes
