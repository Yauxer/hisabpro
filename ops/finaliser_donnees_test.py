"""Finalise une base de TEST HisabPro pour l'export FEC (963).

Usage : python -X utf8 ops/finaliser_donnees_test.py --url-env VAR --base-attendue NOM
        --valeurs-fictives-test "OUI-BASE-DE-TEST" [--rapport fichier.json]

À n'utiliser que sur une base de test, sur autorisation explicite : pour chaque
société/exercice dont l'aperçu FEC est bloqué, le script passe par les routes métier
de l'application, avec leurs contrôles :
  1. tente la récupération déterministe depuis les factures ;
  2. valide les brouillons par date croissante ; un brouillon refusé faute de tiers
     sur 3421/4411 reçoit le tiers fictif « TEST-À-REMPLACER » puis est revalidé ;
  3. complète les auxiliaires manquants (append-only) avec ce tiers fictif ;
  4. ajoute une référence de pièce « TEST-A-REMPLACER-<numéro> » aux écritures sans référence ;
  5. relance l'aperçu FEC et tente l'export.
Aucune écriture définitive n'est modifiée. Toutes les valeurs ajoutées sont marquées
« TEST-À-REMPLACER » et listées dans le rapport, pour être remplacées par les vraies.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION = 'OUI-BASE-DE-TEST'
MOTIF = 'Valeur fictive TEST-À-REMPLACER (base de test, lot 963) — à remplacer par la donnée réelle.'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--url-env', required=True)
    p.add_argument('--base-attendue', required=True)
    p.add_argument('--valeurs-fictives-test', required=True)
    p.add_argument('--rapport')
    a = p.parse_args(argv)
    if a.valeurs_fictives_test != CONFIRMATION:
        raise SystemExit(f'Confirmation requise : --valeurs-fictives-test "{CONFIRMATION}".')
    url = os.environ.get(a.url_env)
    if not url:
        raise SystemExit(f'Connexion absente de {a.url_env}.')
    os.environ['DATABASE_URL'] = url
    os.environ['HISABPRO_CREATE_TABLES'] = 'false'
    os.environ['PYTHON_DOTENV_DISABLED'] = '1'
    os.environ.setdefault('SECRET_KEY', 'finalisation-locale-' + os.urandom(8).hex())
    sys.path.insert(0, str(ROOT / 'hisabpro-backend'))
    os.chdir(ROOT / 'hisabpro-backend')
    from sqlalchemy import text
    from fastapi.testclient import TestClient
    import database
    with database.engine.connect() as db:
        if db.scalar(text('SELECT current_database()')) != a.base_attendue:
            raise SystemExit('Base connectée différente de --base-attendue.')
        admins = db.execute(text(
            "SELECT DISTINCT ON (s.sid) s.uid, s.sid FROM ("
            " SELECT id AS uid, societe_id AS sid, role FROM utilisateurs WHERE actif"
            " UNION ALL SELECT utilisateur_id, societe_id, role FROM utilisateurs_societes WHERE actif) s"
            " WHERE s.role='admin' ORDER BY s.sid, s.uid")).all()
        exercices = db.execute(text('SELECT DISTINCT societe_id, exercice FROM ecritures ORDER BY 1, 2')).all()
    import main as appli
    from auth import get_current_user
    rapport = {'societes': {}}
    client = TestClient(appli.app)
    for uid, sid in admins:
        appli.app.dependency_overrides[get_current_user] = lambda uid=uid, sid=sid: {'id': uid, 'societe_id': sid, 'role': 'admin'}
        tiers_fictifs = {}

        def tiers(nature):
            if nature not in tiers_fictifs:
                r = client.post('/api/tiers', json={'nom': f'TEST-À-REMPLACER {nature}', 'type': nature,
                                                    'categorie_fiscale': 'professionnel'})
                assert r.status_code in (200, 201), r.text
                tiers_fictifs[nature] = r.json()['id']
            return tiers_fictifs[nature]

        for s_, annee in exercices:
            if s_ != sid:
                continue
            cle = f'{sid}-{annee}'
            journal = {'ajouts': []}
            ap = client.get('/api/fec/apercu', params={'exercice': annee}).json()
            journal['avant'] = ap.get('nb_bloquants')
            if ap.get('conforme_export'):
                journal['statut'] = 'déjà conforme'
                rapport['societes'][cle] = journal
                continue
            journal['recuperation'] = client.post('/api/fec/reparer-sources-factures', params={'exercice': annee}).json()
            brouillons = [i for b in ap.get('bloquants', []) if b.get('code') == 'ECRITURES_BROUILLON'
                          for i in (b.get('details') or {}).get('ids', [])]
            fiches = sorted((client.get(f'/api/ecritures/{i}').json() for i in brouillons), key=lambda e: (e['date'], e['id']))
            for e in fiches:
                r = client.post(f"/api/ecritures/{e['id']}/valider")
                if r.status_code == 422 and 'Auxiliaire obligatoire' in r.text:
                    lignes = []
                    for l in e['lignes']:
                        l2 = {k: l.get(k) for k in ('compte', 'libelle', 'debit', 'credit', 'tiers_id')}
                        if str(l['compte']).startswith(('3421', '4411')) and not l.get('tiers_id'):
                            l2['tiers_id'] = tiers('client' if str(l['compte']).startswith('3421') else 'fournisseur')
                            journal['ajouts'].append({'type': 'tiers_brouillon', 'ecriture': e['id'], 'compte': l['compte']})
                        lignes.append(l2)
                    rp = client.patch(f"/api/ecritures/{e['id']}", json={'lignes': lignes})
                    r = client.post(f"/api/ecritures/{e['id']}/valider") if rp.status_code < 400 else rp
                journal.setdefault('validations', {})[e['id']] = [r.status_code, None if r.status_code < 400 else r.text[:200]]
            ap = client.get('/api/fec/apercu', params={'exercice': annee}).json()
            for b in ap.get('bloquants', []):
                det = b.get('details') or {}
                if b.get('code') == 'AUXILIAIRE_MANQUANT' and det.get('ligne_ecriture_id'):
                    nature = 'client' if str(det.get('compte', '')).startswith('3421') else 'fournisseur'
                    r = client.post(f"/api/ecritures/{b['ecriture_id']}/lignes/{det['ligne_ecriture_id']}/auxiliaire-complement",
                                    json={'tiers_id': tiers(nature), 'motif': MOTIF})
                    journal['ajouts'].append({'type': 'auxiliaire', 'ecriture': b.get('numero_ecriture'), 'ligne': det['ligne_ecriture_id'], 'code': r.status_code})
                elif b.get('code') == 'REFERENCE_PIECE_MANQUANTE' and b.get('ecriture_id'):
                    ref = f"TEST-A-REMPLACER-{b.get('numero_ecriture') or b['ecriture_id']}"[:100]
                    r = client.post(f"/api/ecritures/{b['ecriture_id']}/justificatifs", json={'reference': ref, 'motif': MOTIF})
                    journal['ajouts'].append({'type': 'reference', 'ecriture': b.get('numero_ecriture'), 'reference': ref, 'code': r.status_code})
            ap = client.get('/api/fec/apercu', params={'exercice': annee}).json()
            journal['apres'] = {'conforme_export': ap.get('conforme_export'), 'bloquants': [
                {'code': b.get('code'), 'ecriture': b.get('numero_ecriture'), 'message': b.get('message')} for b in ap.get('bloquants', [])]}
            journal['export'] = client.get('/api/fec/export', params={'exercice': annee}).status_code
            rapport['societes'][cle] = journal
    appli.app.dependency_overrides.clear()
    if a.rapport:
        Path(a.rapport).write_text(json.dumps(rapport, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    for cle, j in rapport['societes'].items():
        print(cle, j.get('statut') or f"bloquants {j['avant']} -> {len(j['apres']['bloquants'])}, export {j['export']}, ajouts {len(j['ajouts'])}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
