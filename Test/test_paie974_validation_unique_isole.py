"""974 — validation par une seule personne (petite entreprise). PostgreSQL nonce, données fictives."""
from pathlib import Path
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_paie968_bulletins_isole import (
    application as application131, application124, application123, application122, application121, application120, application119, application118,
    application117, application116, application115, application114, application113, application112, application111, application110, application109,
    application108, application107, application875, application873, application093, application092, application091, application090, application089,
    application087, migration, cles_coffre885, equipe, ok)
from test_paie909_bases_isole import E, S, dec, contenu_rubrique
from test_paie897_social_isole import contenu as contenu_branche
from test_paie893_campagnes_isole import salarie, gain
from test_paie968_bulletins_isole import installer as installer131
from postgres_isole import verifier_cible_isolee

R = Path(__file__).resolve().parents[1]
V = '/api/employes/securite/validation-unique'


def installer(app):
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    raw = app['engine'].raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cur:
            cur.execute((R / 'hisabpro-backend/132_personnel_validation_unique.sql').read_text(encoding='utf8'))
    finally:
        raw.close()


@pytest.fixture(scope='module')
def application(application131):
    installer(application131)
    installer(application131)  # rejouable
    yield application131


def rubrique(eq, code):
    v = ok(eq['a'].post(E, json={'code': code, 'contenu': contenu_rubrique(), 'motif': 'Création FICTIVE974'}), 201)
    return v, eq['a'].post(f'{E}/versions/{v["id"]}/approuver', json=dec())


def branche(eq, code):
    v = ok(eq['a'].post(S, json={'code': code, 'regime': 'REGIME_974', 'contenu': contenu_branche(), 'motif': 'Création FICTIVE974'}), 201)
    return v, eq['a'].post(f'{S}/versions/{v["id"]}/approuver', json=dec())


def test_974_double_validation_par_defaut_puis_validation_unique_tracee(application, equipe):
    a = equipe['a']
    seul = {**equipe, 'b': a}  # le même compte prépare puis décide
    assert ok(a.get('/api/employes/securite/acces'))['validation_unique'] is False
    # Le reste des contraintes historiques est conservé (bénéficiaire, justificatifs, chronologie).
    with application['engine'].connect() as db:
        defs = {t: ' '.join(db.scalars(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE contype='c' AND conrelid=to_regclass(:t)"), {'t': t}))
                for t in ['personnel_demandes', 'paie_variables']}
    assert 'decision_par <> beneficiaire_snapshot' in defs['personnel_demandes'] and 'decision_at >= soumis_at' in defs['personnel_demandes']
    assert 'justificatifs_verifies' in defs['paie_variables'] and 'beneficiaire_snapshot' in defs['paie_variables']
    assert 'decision_par <> prepare_par' not in ' '.join(defs.values())
    # Par défaut : refus côté service et côté base.
    _, r = rubrique(equipe, 'PRIME_SEULE_974A')
    assert r.status_code == 403
    _, r = branche(equipe, 'BRANCHE_SEULE_974A')
    assert r.status_code == 403
    with application['engine'].connect() as db:
        uid = db.scalar(text("SELECT prepare_par FROM paie_rubrique_versions WHERE contenu->>'libelle' IS NOT NULL ORDER BY id DESC LIMIT 1"))
    with pytest.raises(DBAPIError), application['engine'].begin() as db:
        db.execute(text("UPDATE paie_rubrique_versions SET statut='APPROUVEE',decision_par=prepare_par,decision_at=clock_timestamp(),"
                        "motif_decision='x',reference_controle='x' WHERE id=(SELECT max(id) FROM paie_rubrique_versions)"))
    # Seul l'administrateur active le mode ; un comptable est refusé.
    assert equipe['b'].post(V, json={'active': True, 'motif': 'Essai'}).status_code == 403
    ok(a.post(V, json={'active': True, 'motif': 'Petite entreprise FICTIVE974'}))
    assert ok(a.get('/api/employes/securite/acces'))['validation_unique'] is True
    # Le même compte prépare et valide : rubrique, cotisation, dossier salarié complet, variable.
    v, r = rubrique(equipe, 'PRIME_SEULE_974B')
    assert r.status_code == 200, r.text
    _, r = branche(equipe, 'BRANCHE_SEULE_974B')
    assert r.status_code == 200, r.text
    eid, _ = salarie(seul, m='P974')
    gain(seul, eid, v['rubrique_id'])
    with application['engine'].connect() as db:
        moi = db.scalar(text("SELECT decision_par FROM paie_rubrique_versions WHERE id=:i"), {'i': v['id']})
        assert moi == db.scalar(text("SELECT prepare_par FROM paie_rubrique_versions WHERE id=:i"), {'i': v['id']})
        assert db.scalar(text("SELECT count(*) FROM paie_variables WHERE employe_id=:e AND statut='APPROUVE' AND decision_par=prepare_par"), {'e': eid}) == 1
        assert db.scalar(text("SELECT activee_par FROM personnel_validation_unique WHERE societe_id=:s"), {'s': equipe['sid']}) == equipe['uid']
    # Retour à la double validation : de nouveau refusé.
    ok(a.post(V, json={'active': False, 'motif': 'Arrivée d’un second validateur FICTIF974'}))
    assert ok(a.get('/api/employes/securite/acces'))['validation_unique'] is False
    _, r = rubrique(equipe, 'PRIME_SEULE_974C')
    assert r.status_code == 403
    with pytest.raises(DBAPIError), application['engine'].begin() as db:
        db.execute(text('DELETE FROM personnel_validation_unique'))
