from contextlib import nullcontext
from types import SimpleNamespace
import pytest
import sqlalchemy
import sqlalchemy.orm
from recette09a_lecture_seule import session_lecture_seule, READ_ONLY_OPTIONS


def test_refuse_sqlite_sans_connexion(monkeypatch):
    monkeypatch.setattr(sqlalchemy, 'create_engine', lambda *a, **k: pytest.fail('Connexion interdite'))
    with pytest.raises(ValueError, match='PostgreSQL'):
        with session_lecture_seule('sqlite://'):
            pytest.fail('Session interdite')


@pytest.mark.parametrize('flags,body_error', [(['on', 'on'], False), (['on', 'on'], True), (['on', 'off'], False)])
def test_protection_et_fermeture(monkeypatch, flags, body_error):
    calls = []
    values = iter(flags)
    db = SimpleNamespace(execute=lambda stmt: SimpleNamespace(scalar=lambda: next(values)),
                         rollback=lambda: calls.append('rollback'))
    engine = SimpleNamespace(connect=lambda: nullcontext(object()), dispose=lambda: calls.append('dispose'))
    def create(url, **kwargs):
        assert kwargs['isolation_level'] == 'REPEATABLE READ'
        assert kwargs['connect_args']['options'] == READ_ONLY_OPTIONS
        assert 'default_transaction_read_only=on' in READ_ONLY_OPTIONS
        return engine
    monkeypatch.setattr(sqlalchemy, 'create_engine', create)
    monkeypatch.setattr(sqlalchemy.orm, 'Session', lambda **kwargs: nullcontext(db))
    if flags != ['on', 'on'] or body_error:
        with pytest.raises(RuntimeError):
            with session_lecture_seule('postgresql://localhost/test'):
                assert body_error
                raise RuntimeError('Erreur de recette simulée')
    else:
        with session_lecture_seule('postgresql://localhost/test') as actual:
            assert actual is db
    assert calls[-1] == 'dispose'
    if flags == ['on', 'on']:
        assert calls == ['rollback', 'dispose']
