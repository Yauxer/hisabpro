"""Politique de démarrage indépendante de toute connexion à la base."""
import os


def creation_schema_au_demarrage(environ=None):
    env = os.environ if environ is None else environ
    value = env.get('HISABPRO_CREATE_TABLES')
    if value is not None:
        if value.lower().strip() in {'1', 'true', 'yes'}:
            return True
        if value.lower().strip() in {'0', 'false', 'no'}:
            return False
        raise ValueError('HISABPRO_CREATE_TABLES doit valoir 0 ou 1 (false/true).')
    return env.get('APP_ENV', 'dev').lower().strip() not in {'prod', 'production'}
