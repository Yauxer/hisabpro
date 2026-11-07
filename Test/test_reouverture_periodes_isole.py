"""CPT11 : calendrier réel, rôles, audit append-only et exercice définitif."""
from contextlib import closing
from pathlib import Path
import httpx
import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_ajustements_inventaire_isole import exercice
from test_complements_structure_postgres import refuser
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


def piece(api, reference='CAPITAL-FICTIF557', valide=True):
    return api.post('/api/ecritures', json={'date': '2025-01-15', 'journal': 'BQ',
        'reference': reference, 'libelle': 'Capital fictif calendrier557', 'est_validee': valide,
        'lignes': [{'compte': '5141', 'debit': 1000}, {'compte': '1111', 'credit': 1000}]})


def etat(app, sid):
    with app['engine'].connect() as c:
        return {
            'pieces': c.execute(text('SELECT row_to_json(e)::text FROM ecritures e WHERE societe_id=:s ORDER BY id'), {'s': sid}).scalars().all(),
            'lignes': c.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s ORDER BY l.id'), {'s': sid}).scalars().all(),
            'periodes': c.execute(text('SELECT row_to_json(p)::text FROM periodes_comptables p JOIN exercices_comptables e ON e.id=p.exercice_id WHERE e.societe_id=:s ORDER BY p.id'), {'s': sid}).scalars().all(),
            'audit': c.execute(text('SELECT row_to_json(a)::text FROM audit_periodes_comptables a JOIN exercices_comptables e ON e.id=a.exercice_id WHERE e.societe_id=:s ORDER BY a.id'), {'s': sid}).scalars().all(),
        }


def test_fermeture_reouverture_admin_trace_et_definitifs_intacts(application):
    with closing(client(application)[0]) as api:
        ex = exercice(api); sid = ok(api.get('/api/societe/moi'))['id']
        uid = ok(api.get('/api/auth/me'))['id']
        e = ok(piece(api), 201)
        initial = etat(application, sid)
        ok(api.patch('/api/exercices/2025/periodes/1', json={'statut': 'fermee'}))
        ferme = etat(application, sid)
        refus = piece(api, 'REFUS-FICTIF557')
        assert refus.status_code in (400, 409, 423), refus.text
        assert etat(application, sid) == ferme
        ok(api.patch('/api/exercices/2025/periodes/1', json={'statut': 'ouverte'}))
        rouvert = etat(application, sid)
        assert rouvert['pieces'] == initial['pieces'] and rouvert['lignes'] == initial['lignes']
        with application['engine'].connect() as c:
            audit = c.execute(text('SELECT ancien_statut,nouveau_statut,acteur_id,motif FROM audit_periodes_comptables '
                'WHERE exercice_id=:i AND numero=1 ORDER BY id'), {'i': ex['id']}).all()
            assert [(a.ancien_statut, a.nouveau_statut, a.acteur_id) for a in audit] == [
                ('ouverte', 'fermee', uid), ('fermee', 'ouverte', uid)]
            assert all(a.motif for a in audit) and 'administrative' in audit[-1].motif
        # Réouverture et nouvelle saisie ne rendent pas modifiable l'original validé.
        modification = api.patch(f"/api/ecritures/{e['id']}", json={'libelle': 'Interdit557'})
        assert modification.status_code in (400, 409, 423), modification.text
        assert etat(application, sid) == rouvert
        nouveau = ok(piece(api, 'APRES-REOUVERTURE557', False), 201)
        assert nouveau['id'] != e['id']
        # Le brouillon interdit la fermeture ; aucune suppression pour passer le test.
        avant = etat(application, sid)
        assert api.patch('/api/exercices/2025/periodes/1', json={'statut': 'fermee'}).status_code == 409
        assert etat(application, sid) == avant


@pytest.mark.parametrize('role', ['comptable', 'lecture'])
def test_reouvertures_reservees_admin_sans_effet_secondaire(application, role):
    api, email, password = client(application)
    with closing(api):
        exercice(api); sid = ok(api.get('/api/societe/moi'))['id']
        ok(api.patch('/api/exercices/2025/periodes/1', json={'statut': 'fermee'}))
        email = email.replace('@', '-' + role + '@')
        ok(api.post('/api/utilisateurs', json={'nom': 'Calendrier fictif557', 'email': email,
            'mot_de_passe': password, 'role': role}), 201)
        with httpx.Client(base_url=application['api_url']) as autre:
            autre.headers['Authorization'] = 'Bearer ' + ok(autre.post('/api/auth/login', json={
                'email': email, 'password': password}))['access_token']
            avant = etat(application, sid)
            assert autre.patch('/api/exercices/2025/periodes/1', json={'statut': 'ouverte'}).status_code == 403
            assert autre.post('/api/exercices/2025/periodes/ouvrir-toutes').status_code == 403
            assert etat(application, sid) == avant


def test_exercice_clos_api_sql_audit_et_autre_societe(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        exercice(api); exercice(autre)
        sid = ok(api.get('/api/societe/moi'))['id']; autre_sid = ok(autre.get('/api/societe/moi'))['id']
        ok(piece(api), 201)
        original = etat(application, sid)
        r = ok(api.post('/api/cloture/cloturer?exercice=2025'))
        assert r['a_nouveaux_sur'] == 2026 and r['resultat_net'] == -3000
        # CM existante du laboratoire : aucun régime fiscal réel qualifié ici.
        apres = etat(application, sid)
        assert all(e in apres['pieces'] for e in original['pieces'])
        assert all(l in apres['lignes'] for l in original['lignes'])
        for url, body, method in [('/api/exercices/2025/periodes/1', {'statut': 'ouverte'}, 'patch'),
                                  ('/api/exercices/2025/periodes/ouvrir-toutes', {}, 'post')]:
            refus = getattr(api, method)(url, json=body)
            assert refus.status_code == 423, refus.text
            assert etat(application, sid) == apres
        with application['engine'].connect() as c:
            pid = c.scalar(text('SELECT p.id FROM periodes_comptables p JOIN exercices_comptables e ON e.id=p.exercice_id '
                'WHERE e.societe_id=:s AND e.annee=2025 AND p.numero=1'), {'s': sid})
        refuser(application['runtime088'], f"UPDATE periodes_comptables SET statut='ouverte' WHERE id={int(pid)}", '23514')
        assert etat(application, sid) == apres
        autre_avant = etat(application, autre_sid)
        ok(autre.patch('/api/exercices/2025/periodes/1', json={'statut': 'fermee'}))
        ok(autre.post('/api/exercices/2025/periodes/ouvrir-toutes'))
        assert etat(application, sid) == apres
        assert etat(application, autre_sid)['pieces'] == autre_avant['pieces']
        # L'historique de période ne peut être réécrit par le rôle applicatif.
        refuser(application['runtime088'], 'UPDATE audit_periodes_comptables SET motif=motif', '42501')
        assert etat(application, sid) == apres


@pytest.mark.parametrize('role', ['admin', 'lecture'])
def test_periode_reouverture_navigateur_role_et_refresh(application, role):
    playwright = pytest.importorskip('playwright.sync_api')
    api, email, password = client(application)
    with closing(api), playwright.sync_playwright() as p:
        exercice(api)
        if role != 'admin':
            email = email.replace('@', '-lecture@')
            ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur calendrier557', 'email': email,
                'mot_de_passe': password, 'role': role}), 201)
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': 390, 'height': 1000})
            page.set_default_timeout(20000)
            erreurs, serveurs = observer(page, application['api_url'])
            page.on('dialog', lambda dialog: dialog.accept())
            connexion(page, application['web_url'], email, password)
            page.goto(application['web_url'] + '/cloture', wait_until='domcontentloaded')
            page.get_by_label('Exercice actif', exact=True).select_option('2025')
            janvier = page.get_by_role('button').filter(has=page.get_by_text('Janvier 2025', exact=True))
            playwright.expect(janvier).to_contain_text('Ouverte')
            if role == 'lecture':
                playwright.expect(janvier).to_be_disabled()
                assert page.get_by_role('button', name='Ouvrir toutes les périodes', exact=False).count() == 0
            else:
                janvier.click()
                playwright.expect(janvier).to_contain_text('Fermée (réouvrable)')
                janvier.click()
                playwright.expect(janvier).to_contain_text('Ouverte')
                page.reload(wait_until='domcontentloaded')
                playwright.expect(janvier).to_contain_text('Ouverte')
            assert not erreurs and not serveurs, (erreurs, serveurs)
            page.screenshot(path=str(Path(__file__).resolve().parents[1] / '.codex-tests' / f'calendrier557_{role}.png'), full_page=True)
        finally:
            browser.close()
