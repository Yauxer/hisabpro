"""Déploiement volontaire : mode historique inchangé, protection fermée par défaut.

Aucun cache des droits. Verrou partagé sur lecture/mutation historique, exclusif
sur activation/délégation/révocation, afin de sérialiser le basculement.
"""
from fastapi import HTTPException, Response
from sqlalchemy import text
import schemas

CAPACITES = frozenset({'personnel.lire_identite', 'personnel.lire_remuneration',
                       'personnel.lire_identifiants_sensibles', 'personnel.audit_lire',
                       'personnel.proposer', 'personnel.soumettre', 'personnel.approuver',
                       'personnel.valider_regles_paie'})


def reponse_privee(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'


def verrou(db, sid, *, exclusif=False):
    if db.bind.dialect.name == 'postgresql':
        fn = 'pg_advisory_xact_lock' if exclusif else 'pg_advisory_xact_lock_shared'
        db.execute(text(f'SELECT {fn}(hashtextextended(:cle,0))'),
                   {'cle': f'hisabpro:personnel:acces:{sid}'})


def validation_unique(db, sid):
    """Lot 974 : un même compte peut préparer et décider si l'administrateur l'a activé."""
    if db.bind.dialect.name != 'postgresql' or not db.scalar(text("SELECT to_regclass('public.personnel_validation_unique') IS NOT NULL")):
        return False
    return bool(db.scalar(text('SELECT hisabpro_validation_unique(:s)'), {'s': sid}))


def schema_installe(db):
    if db.bind.dialect.name != 'postgresql':
        return False
    a, b = db.execute(text("SELECT to_regclass('public.personnel_acces_societes') IS NOT NULL, "
                           "to_regclass('public.personnel_habilitations') IS NOT NULL")).one()
    if a != b:
        raise HTTPException(503, 'Installation des habilitations Personnel incomplète.')
    return a


def contexte(db, user):
    sid = user['societe_id']
    verrou(db, sid)
    installe = schema_installe(db)
    protege = installe and bool(db.scalar(text(
        'SELECT EXISTS(SELECT 1 FROM personnel_acces_societes WHERE societe_id=:s)'), {'s': sid}))
    caps = set()
    module = bool(db.scalar(text("SELECT EXISTS(SELECT 1 FROM modules_actifs WHERE societe_id=:s "
                                "AND module='paie_grh' AND actif)"), {'s': sid}))
    if protege:
        if module:
            caps = set(db.scalars(text('SELECT capacite FROM personnel_habilitations WHERE '
                                     'societe_id=:s AND utilisateur_id=:u AND revoquee_at IS NULL AND '
                                     'liaison_id_snapshot IS NOT DISTINCT FROM ('
                                     'SELECT a.id FROM utilisateurs p LEFT JOIN utilisateurs_societes a '
                                     'ON a.utilisateur_id=p.id AND a.societe_id=:s AND a.actif AND p.societe_id<>:s '
                                     'WHERE p.id=:u)'),
                                  {'s': sid, 'u': user['id']})) & CAPACITES
    return {'schema_installe': bool(installe), 'mode': 'protege' if protege else 'historique',
            'capacites': sorted(caps), 'module_actif': module,
            'modification_historique_autorisee': not protege and user['role'] in {'admin', 'comptable'},
            'peut_gerer_habilitations': user['role'] == 'admin',
            'validation_unique': validation_unique(db, sid)}


def exiger_lecture(db, user, *capacites):
    ctx = contexte(db, user)
    if ctx['mode'] == 'protege' and (not ctx['module_actif'] or not set(capacites) <= set(ctx['capacites'])):
        raise HTTPException(403, 'Habilitation Personnel requise pour cette consultation.')
    return ctx


def exiger_mutation_historique(db, user):
    ctx = contexte(db, user)
    if ctx['mode'] == 'protege':
        raise HTTPException(409, 'Cette opération historique est désactivée pour le Personnel protégé.')


def sortie_employe(emp, ctx):
    result = schemas.EmployeOut.model_validate(emp)
    if ctx['mode'] == 'protege':
        masque = {}
        if 'personnel.lire_remuneration' not in ctx['capacites']:
            masque.update(salaire_brut=None, situation_familiale=None,
                          nb_enfants=None, personnes_charge_ir=None)
        if 'personnel.lire_identifiants_sensibles' not in ctx['capacites']:
            masque['numero_cnss'] = None
        result = result.model_copy(update=masque)
    return result


def verifier_suppression_compte(db, uid):
    if schema_installe(db) and db.scalar(text(
        'SELECT EXISTS(SELECT 1 FROM personnel_acces_societes WHERE activee_par=:u) OR '
        'EXISTS(SELECT 1 FROM personnel_habilitations WHERE '
        'utilisateur_id=:u OR accordee_par=:u OR revoquee_par=:u)'), {'u': uid}):
        raise HTTPException(409, 'Ce compte possède un historique Personnel. Désactivez-le pour conserver sa traçabilité.')
    if db.bind.dialect.name == 'postgresql':
        # Les migrations sont déployées séparément. Une référence106 peut
        # exister même si cet acteur n'a plus (ou n'a jamais eu) de grant105.
        for table, colonnes in (
            ('personnel_dossiers', ('cree_par', 'utilisateur_beneficiaire_id')),
            ('personnel_demandes', ('prepare_par', 'beneficiaire_snapshot', 'decision_par')),
            ('personnel_contrats_versions', ('approuvee_par',)),
            ('personnel_remunerations_versions', ('approuvee_par',)),
            ('personnel_evenements', ('auteur_id',)),
        ):
            if db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'), {'t': 'public.'+table}):
                condition = ' OR '.join(c+'=:u' for c in colonnes)
                if db.scalar(text(f'SELECT EXISTS(SELECT 1 FROM public.{table} WHERE {condition})'), {'u': uid}):
                    raise HTTPException(409, 'Ce compte possède un historique Personnel. Désactivez-le pour conserver sa traçabilité.')
