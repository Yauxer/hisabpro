"""Restauration conjointe DB/pièces : deux clusters nonce et API HTTP réelles."""
from datetime import date
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import httpx
from PIL import Image
from pypdf import PdfReader
import pytest
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import models
from e2e_isole_support import (application_isolee, arreter_processus_cree,
    attendre_http, port_loopback_libre)
from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops.postgres_sauvegarde import sauvegarder, restaurer_isole

TABLES = ('societes', 'utilisateurs', 'utilisateurs_societes', 'articles',
          'bons_livraison', 'lignes_bon_livraison', 'mouvements_stock', 'ecritures', 'lignes_ecriture')


def instantane(engine):
    with engine.connect() as c:
        return {table: c.exec_driver_sql(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id').all()
                for table in TABLES}


def manifeste(racine):
    return {p.relative_to(racine).as_posix(): (p.stat().st_size, sha256(p.read_bytes()).hexdigest())
            for p in sorted(racine.rglob('*')) if p.is_file()}


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def pdf_fictif(texte):
    buffer = BytesIO()
    doc = canvas.Canvas(buffer)
    doc.drawString(40, 800, 'DOCUMENT FICTIF : AUCUNE RECEPTION REELLE')
    doc.drawString(40, 760, texte)
    doc.save()
    contenu = buffer.getvalue()
    assert texte in ''.join(p.extract_text() for p in PdfReader(BytesIO(contenu)).pages)
    return contenu


def login(api, email, password):
    token = ok(api.post('/api/auth/login', json={'email': email, 'password': password}))['access_token']
    api.headers['Authorization'] = 'Bearer ' + token


def test_dump_restore_db_et_pieces_bl_homonymes_permissions_reelles():
    with application_isolee() as source, cluster_isole() as cible:
        verifier_cible_isolee(source['cluster']['url'], source['cluster']['directory'], source['cluster']['nonce'])
        verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        assert cible['port'] != source['cluster']['port'] and cible['nonce'] != source['cluster']['nonce']
        uploads_source = Path(source['uploads_dir']).resolve()
        uploads_cible = (cible['directory'] / 'uploads_restaures').resolve()
        backup = (source['directory'] / 'sauvegarde_conjointe').resolve()
        assert uploads_source.is_relative_to(source['directory'].resolve())
        assert uploads_cible.is_relative_to(cible['directory'].resolve())
        assert backup.is_relative_to(source['directory'].resolve())
        reel = (ROOT / 'hisabpro-backend/uploads').resolve()
        assert not uploads_source.is_relative_to(reel) and not uploads_cible.is_relative_to(reel)
        assert not uploads_cible.exists() and not backup.exists()
        suffix = uuid.uuid4().hex[:8]
        admin_email, lecteur_email = f'backup-doc-{suffix}@example.com', f'lecture-doc-{suffix}@example.com'
        autre_email, password = f'autre-doc-{suffix}@example.com', 'SauvegardePieces2026!'
        with Session(source['engine']) as db:
            db.add_all([models.CompteCGNCReference(numero=n, libelle=label, classe=int(n[0]), type_compte='SP')
                        for n, label in [('7111', 'Ventes de marchandises'), ('6111', 'Achats de marchandises')]])
            db.commit()
        with httpx.Client(base_url=source['api_url']) as api:
            token = ok(api.post('/api/auth/register', json={'nom': 'Admin sauvegarde fictive', 'email': admin_email,
                'password': password, 'raison_sociale': 'Sauvegarde pièces fictive ' + suffix}))['access_token']
            api.headers['Authorization'] = 'Bearer ' + token
            sid = ok(api.get('/api/societe/moi'))['id']
            client = ok(api.post('/api/tiers', json={'nom': 'Client sauvegarde fictif', 'type': 'client'}), 201)
            article = ok(api.post('/api/articles', json={'code': 'BACKUP-' + suffix,
                'designation': 'Article sauvegarde fictif', 'is_stockable': True, 'stock_actuel': 5,
                'prix_achat_ht': 40, 'prix_vente_ht': 100, 'tva': 20}), 201)
            bl = ok(api.post('/api/bons-livraison', json={'numero': 'BL-BACKUP-' + suffix,
                'date': date.today().isoformat(), 'type': 'vente', 'tiers': client['nom'], 'tiers_id': client['id'],
                'lignes': [{'description': article['designation'], 'article_id': article['id'],
                    'quantite_prevue': 2, 'quantite_livree': 2, 'prix_unitaire': 100, 'tva': 20}]}), 201)
            assert bl['statut'] == 'en_preparation'
            ok(api.post('/api/utilisateurs', json={'nom': 'Lecteur sauvegarde fictif', 'email': lecteur_email,
                'mot_de_passe': password, 'role': 'lecture'}), 201)
            with httpx.Client(base_url=source['api_url']) as autre:
                ok(autre.post('/api/auth/register', json={'nom': 'Autre admin fictif', 'email': autre_email,
                    'password': password, 'raison_sociale': 'Autre sauvegarde fictive ' + suffix}))
            avant = instantane(source['engine'])
            image = BytesIO()
            Image.new('RGB', (60, 40), color='white').save(image, format='PNG')
            contenus = [('Reception client.pdf', pdf_fictif('RECEPTION FICTIVE A ' + bl['numero']), 'application/pdf'),
                        ('Reception client.pdf', pdf_fictif('RECEPTION FICTIVE B ' + bl['numero']), 'application/pdf'),
                        ('Reception client.png', image.getvalue(), 'image/png')]
            fichiers = []
            for nom, contenu, mime in contenus:
                piece = ok(api.post(f'/api/attachments/bl/{bl["id"]}', files={'file': (nom, contenu, mime)}))
                fichiers.append((piece['nom'], contenu, mime))
                assert instantane(source['engine']) == avant
            assert len({f[0] for f in fichiers}) == 3
            assert fichiers[0][0] != fichiers[1][0] and sha256(fichiers[0][1]).digest() != sha256(fichiers[1][1]).digest()
            assert len(ok(api.get(f'/api/attachments/bl/{bl["id"]}'))) == 3
        # Fenêtre cohérente : arrêter uniquement le processus API créé par ce
        # contexte, avant pg_dump et copie. Aucun auteur de mutation ne subsiste.
        arreter_processus_cree(source['processus'][0])
        assert source['processus'][0].poll() is not None
        backup.mkdir()
        manifeste_initial = manifeste(uploads_source)
        assert len(manifeste_initial) == 3
        chemin_pieces = backup / 'pieces'
        shutil.copytree(uploads_source, chemin_pieces)  # Destination neuve, jamais d'écrasement.
        assert manifeste(chemin_pieces) == manifeste_initial
        dump = sauvegarder(source['cluster']['url'], backup / 'database.dump', source['cluster']['bin'])
        assert dump.is_file() and dump.stat().st_size > 0
        assert instantane(source['engine']) == avant
        verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        restaurer_isole(cible['url'], dump, cible['bin'], cible['directory'], cible['nonce'])
        cible_engine = create_engine(cible['url'])
        processus = None
        try:
            assert instantane(cible_engine) == avant
            shutil.copytree(chemin_pieces, uploads_cible)
            assert manifeste(uploads_cible) == manifeste_initial
            for nom, contenu, _ in fichiers:
                piece = uploads_cible / str(sid) / 'bl' / str(bl['id']) / nom
                assert piece.is_file() and sha256(piece.read_bytes()).digest() == sha256(contenu).digest()
            port = port_loopback_libre()
            api_url = f'http://127.0.0.1:{port}'
            log = cible['directory'] / 'api_restaures.log'
            env = os.environ.copy()
            env.update(DATABASE_URL=cible['url'], APP_ENV='test', HISABPRO_CREATE_TABLES='false',
                SECRET_KEY='secret-fictif-restauration-' + cible['nonce'], PYTHON_DOTENV_DISABLED='1',
                PYTHONUTF8='1', HISABPRO_UPLOAD_DIR=str(uploads_cible), CORS_ORIGINS='http://127.0.0.1:1')
            verifier_cible_isolee(env['DATABASE_URL'], cible['directory'], cible['nonce'])
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
            with log.open('w', encoding='utf-8') as sortie:
                processus = subprocess.Popen([sys.executable, '-X', 'utf8', '-m', 'uvicorn', 'main:app',
                    '--host', '127.0.0.1', '--port', str(port), '--log-level', 'warning'], cwd=ROOT/'hisabpro-backend',
                    env=env, stdout=sortie, stderr=subprocess.STDOUT, **options)
                attendre_http(api_url + '/api/health', processus, log)
                with httpx.Client(base_url=api_url) as api:
                    login(api, admin_email, password)
                    assert ok(api.get('/api/societe/moi'))['id'] == sid
                    assert any(b['id'] == bl['id'] and b['numero'] == bl['numero']
                               for b in ok(api.get(f'/api/bons-livraison?exercice={date.today().year}')))
                    for email in (admin_email, lecteur_email):
                        login(api, email, password)
                        liste = ok(api.get(f'/api/attachments/bl/{bl["id"]}'))
                        assert {p['nom'] for p in liste} == {f[0] for f in fichiers}
                        for nom, original, _ in fichiers:
                            response = api.get(f'/api/attachments/bl/{bl["id"]}/download/{nom}')
                            assert response.status_code == 200, response.text
                            assert sha256(response.content).digest() == sha256(original).digest()
                        if email == lecteur_email:
                            assert api.post(f'/api/attachments/bl/{bl["id"]}', files={'file': ('refus.pdf', contenus[0][1], 'application/pdf')}).status_code == 403
                            assert api.delete(f'/api/attachments/bl/{bl["id"]}/{fichiers[0][0]}').status_code == 403
                    login(api, autre_email, password)
                    assert api.get(f'/api/attachments/bl/{bl["id"]}').status_code == 404
                    assert api.get(f'/api/attachments/bl/{bl["id"]}/download/{fichiers[0][0]}').status_code == 404
                    assert api.post(f'/api/attachments/bl/{bl["id"]}', files={'file': ('refus.pdf', contenus[0][1], 'application/pdf')}).status_code == 404
                assert instantane(cible_engine) == avant
                assert manifeste(uploads_cible) == manifeste_initial
                assert instantane(source['engine']) == avant
                with pytest.raises(ValueError, match='doit être vide'):
                    restaurer_isole(cible['url'], dump, cible['bin'], cible['directory'], cible['nonce'])
                assert instantane(cible_engine) == avant
        finally:
            if processus is not None:
                arreter_processus_cree(processus)
            cible_engine.dispose()
        assert processus.poll() is not None
    assert not source['directory'].exists() and not source['cluster']['directory'].exists()
    assert not cible['directory'].exists()
