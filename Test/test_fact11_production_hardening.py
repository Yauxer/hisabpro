from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'


def test_role_est_revalide_en_base_a_chaque_requete():
    src = (BACK / 'auth.py').read_text(encoding='utf-8')
    assert 'db.query(models.Utilisateur)' in src
    assert 'if not user or not user.actif' in src
    assert 'models.UtilisateurSociete' in src
    assert 'Accès à cette société révoqué' in src
    assert 'role = "lecture"' in src  # fail closed sur rôle inconnu


def test_routes_metier_modifiantes_sont_protegees_par_rbac():
    exceptions = {
        ('routers/auth.py', '/register'),
        ('routers/auth.py', '/login'),
        ('routers/etats.py', '/pdf'),          # génération lecture seule
        ('routers/inventaire.py', '/simuler'), # simulation lecture seule
        ('routers/multi_societes.py', '/switcher/{societe_id}'), # changement de contexte, pas de donnée
    }
    files = list(BACK.glob('*.py')) + list((BACK / 'routers').glob('*.py'))
    manquantes = []
    for p in files:
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        rel = p.relative_to(BACK).as_posix()
        for i, line in enumerate(lines):
            m = re.search(r'@(?:router\w*|router)\.(post|put|patch|delete)\("([^"]*)"', line)
            if not m:
                continue
            chemin = m.group(2)
            if (rel, chemin) == ('routers/cloture.py', '/ajustements/apercu'):
                # POST de lecture : rester authentifié et sans commande d'écriture.
                # Complété par test_apercu_inventaire_isole sur PostgreSQL natif.
                arbre = ast.parse(p.read_text(encoding='utf-8'))
                fn = next(n for n in arbre.body if isinstance(n, ast.FunctionDef)
                          and n.name == 'apercu_ajustement_inventaire')
                assert 'Depends(get_current_user)' in ast.unparse(fn.args)
                appels = {ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
                assert not appels & {'ensure_exercice', 'preparer_exercice_suivant', 'db.add',
                                      'db.add_all', 'db.delete', 'db.flush', 'db.commit', 'db.execute'}
                continue
            if (rel, chemin) in exceptions:
                continue
            chunk = '\n'.join(lines[i:i + 20])
            if (rel, chemin) == ('routers/auth.py', '/mot-de-passe'):
                # Chaque rôle peut gérer son propre secret ; l'authentification
                # reste obligatoire, indépendamment du droit d'écriture métier.
                assert 'current_user=Depends(get_current_user)' in chunk
                assert 'id=current_user["id"]' in chunk
                continue
            if 'requiert_ecriture' not in chunk and 'requiert_admin' not in chunk:
                manquantes.append(f'{rel}:{i+1} {m.group(1).upper()} {chemin}')
    assert not manquantes, 'Routes mutantes sans contrôle RBAC : ' + ', '.join(manquantes)


def test_avoirs_acomptes_lettrage_et_pieces_jointes_bloquent_lecture_seule():
    for nom in ('acomptes.py', 'avoirs.py', 'lettrage.py', 'attachments.py'):
        src = (BACK / nom).read_text(encoding='utf-8')
        assert 'requiert_ecriture' in src


def test_pieces_jointes_sont_bornees_au_tenant_et_protegees_du_path_traversal():
    src = (BACK / 'attachments.py').read_text(encoding='utf-8')
    assert 'DOCUMENTS = {' in src
    assert 'modele.societe_id == societe_id' in src
    assert 'os.path.commonpath' in src
    assert 'os.path.basename(filename) != filename' in src
    assert 'MAX_UPLOAD_BYTES' in src
    assert 'HTTPException(413' in src


def test_rapprochement_refuse_un_reglement_dune_autre_societe():
    src = (BACK / 'lettrage.py').read_text(encoding='utf-8')
    assert 'id=reglement_id, societe_id=current_user["societe_id"]' in src
    assert 'Règlement introuvable' in src


def test_audit_applicatif_est_append_only_et_journalise_toutes_les_mutations_http():
    sql = (BACK / '036_production_hardening.sql').read_text(encoding='utf-8')
    main = (BACK / 'main.py').read_text(encoding='utf-8')
    assert 'CREATE TABLE IF NOT EXISTS audit_actions' in sql
    assert 'hisabpro_audit_actions_append_only' in sql
    assert 'SECURITY DEFINER' in sql
    assert 'REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit_actions FROM hisabpro' in sql
    assert 'hisabpro_journaliser_action' in main
    assert '{"POST", "PUT", "PATCH", "DELETE"}' in main
    assert 'X-Request-ID' in main


def test_controle_production_couvre_les_incoherences_critiques():
    src = (BACK / 'services' / 'production_audit_service.py').read_text(encoding='utf-8')
    for code in (
        'FACTURE_VALIDEE_INCOMPLETE', 'FACTURE_VALIDEE_SANS_LIGNE',
        'NUMERO_FACTURE_DUPLIQUE', 'REF_FOURNISSEUR_DUPLIQUE',
        'ECRITURE_VALIDEE_DESEQUILIBREE', 'LIEN_REGLEMENT_AUTRE_SOCIETE',
        'LIEN_AVOIR_AUTRE_SOCIETE', 'LIEN_IMPUTATION_AUTRE_SOCIETE',
        'ACOMPTE_SURIMPUTE', 'ECHEANCIER_NON_RECONCILIE', 'STOCK_NEGATIF',
    ):
        assert code in src


def test_controle_production_et_journal_sont_reserves_admin():
    route = (BACK / 'routers' / 'production.py').read_text(encoding='utf-8')
    main = (BACK / 'main.py').read_text(encoding='utf-8')
    assert '@router.get("/controle")' in route
    assert '@router.get("/audit-actions")' in route
    assert route.count('Depends(requiert_admin)') >= 2
    assert 'app.include_router(production.router)' in main


def test_migration_verrouille_les_roles_et_donne_les_droits_audit_necessaires():
    sql = (BACK / '036_production_hardening.sql').read_text(encoding='utf-8')
    assert "role IN ('admin','comptable','lecture')" in sql
    assert 'ck_utilisateurs_role_hisabpro' in sql
    assert 'ck_utilisateurs_societes_role_hisabpro' in sql
    assert 'GRANT SELECT ON audit_actions TO hisabpro' in sql
    assert 'GRANT EXECUTE ON FUNCTION hisabpro_journaliser_action' in sql


def test_get_modules_et_periodes_ne_font_plus_decriture_sur_get():
    soc = (BACK / 'routers' / 'societe.py').read_text(encoding='utf-8')
    ex = (BACK / 'routers' / 'exercices.py').read_text(encoding='utf-8')
    # Pas d'initialisation DB dans la branche GET /modules.
    bloc = soc.split('@router.get("/modules")', 1)[1].split('@router.patch("/modules")', 1)[0]
    assert 'db.commit()' not in bloc
    assert 'activer_modules_defaut' not in bloc
    # GET périodes ne doit plus appeler ensure_exercice (qui crée les périodes).
    bloc_ex = ex.split('@router.get("/{annee}/periodes")', 1)[1].split('@router.patch("/{annee}/periodes/{numero}")', 1)[0]
    assert 'ensure_exercice' not in bloc_ex
    assert 'db.commit()' not in bloc_ex


def test_production_refuse_secrets_db_par_defaut_en_prod():
    src = (BACK / 'database.py').read_text(encoding='utf-8')
    assert 'DATABASE_URL manquante en production' in src
    assert 'pool_pre_ping=True' in src

def test_parametres_expose_controle_production_et_piste_audit_admin():
    src = (ROOT / 'src' / 'pages' / 'Parametres.jsx').read_text(encoding='utf-8')
    assert 'Sécurité & contrôle' in src
    assert '/api/production/controle' in src
    assert '/api/production/audit-actions?limit=100' in src
    assert 'Piste d’audit applicative' in src
    assert 'estAdmin()' in src
