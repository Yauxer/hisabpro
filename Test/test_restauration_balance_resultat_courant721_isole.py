"""Restauration froide721 : B8/B9, financement, notes, versions et pièces conservés."""
from contextlib import contextmanager
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib,json
import httpx
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
import test_restauration_justificatifs_acl_isole as recette
from test_balance_documents691_isole import creer,demande,chemin,BASE,path,joindre,pdf_fictif
from test_logo_societe import image_data
from test_balance_etic_notes693_isole import notes,url as notes_url
from test_balance_financement695_isole import creer,flux,url as financement_url
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

from test_balance_etic_tables697_isole import tables,url as tables_url

from test_balance_etic_annexes699_isole import annexes,url as annexes_url

from test_balance_cpc703_isole import body as cpc_body, url as cpc_url

from test_balance_non_valeurs705_isole import creer as creer_nv, body as nv_body, url as nv_url

from test_balance_participations707_isole import creer as creer_b4, body as b4_body, url as b4_url

from test_balance_emetteurs709_isole import body as em_body, url as em_url

from test_balance_cessions711_isole import body as cs_body, url as cs_url

from test_balance_mouvements713_isole import body as mv_body, url as mv_url

from test_balance_raccords715_isole import creer as creer_rc, body as rc_body, url as rc_url

from test_balance_resultat_courant721_isole import body as courant_body, url as courant_url

ROOT=Path(__file__).resolve().parents[1]


def test_721_restaurer_resultat_courant_et_tous_complements(monkeypatch,tmp_path):
    application_orig,client_orig,lancer_orig=recette.application_isolee,recette.client,recette.lancer_cible
    preparer_orig=recette.preparer091;memo={};preuve={'erreur':None};supplements={}
    historique=ROOT/'.codex-tests/restauration452_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None

    def preparer104(engine,c):
        preparer_orig(engine,c)
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        for p in sorted(recette.BACK.glob('*.sql')):
            if p.name[:3].isdigit() and 92<=int(p.name[:3])<=104:
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf8'))
                finally:raw.close()

    @contextmanager
    def application104(**kw):
        kw['preparer_runtime']=preparer104
        with application_orig(**kw) as app:yield app

    def situation(url):
        with httpx.Client(base_url=url,timeout=30) as api:
            recette.connecter(api,memo['email'],memo['password'])
            autre=recette.ok(api.get(BASE+f'/{memo["autre_b1"]["id"]}'))
            assert autre==memo['autre_b1'] and autre['contenu']['non_valeurs_documentaires']['vue']['periodes']['n']['net']=='3000.00'
            b4=recette.ok(api.get(BASE+f'/{memo["autre_b4"]["id"]}'))
            assert b4==memo['autre_b4'] and b4['contenu']['participations_documentaires']['vue']['periodes']['n']['participations']=='4000.00'
            em=recette.ok(api.get(em_url(b4)))
            assert em['tables'][0]['lignes'][0]['emetteur']=='Atlas Industrie fictive'
            assert em['controle_emetteurs']['periodes']['n']['comptes'][0]['ecart_brut']=='0.00'
            assert em['controle_emetteurs']['periodes']['n1']['comptes'][0]['solde_brut_source']=='3000.00'
            rc=recette.ok(api.get(BASE+f'/{memo["autre_raccord"]["id"]}'));assert rc==memo['autre_raccord']
            rcv=recette.ok(api.get(rc_url(rc)));assert rcv['actuel']
            assert rcv['snapshot']['controle_raccords']['tableaux']['B2']['comptes'][0]['solde_source']=='11000.00'
            assert rcv['snapshot']['controle_raccords']['tableaux']['B5']['comptes'][0]['ecart']=='0.00'
            d=recette.ok(api.get(path(memo['v'])));assert len(d['documents'])==1
            r=api.get(path(memo['v'])+f'/{memo["doc"]["id"]}');assert r.status_code==200 and r.content==memo['raw']
            z=api.get(BASE+f'/{memo["v"]["id"]}/zip');assert z.status_code==200,z.text
            with ZipFile(BytesIO(z.content)) as zip:
                assert zip.testzip() is None
                assert json.loads(zip.read('notes_etic_documentaires.json'))['comptage_notes']['renseigne']==1
                assert json.loads(zip.read('financement_documentaire.json'))['tableau']['ecart_controle']==0
                a=json.loads(zip.read('annexes_etic_documentaires.json'))
                assert a['tables'][2]['lignes'][0]['date_contrat']=='2025-12-15'
                assert a['tables'][3]['lignes'][0]['pourcentage']=='66.666666666667'
                assert a['controle_capital']['capital_balance_111']=='10000.00'
                assert a['controle_capital']['ecart_pourcentages_100']=='-33.333333333333'
                tableau=json.loads(zip.read('tables_etic_documentaires.json'))
                assert tableau['tables'][0]['lignes'][0]['montant_couvert']=='12345.67'
                assert tableau['tables'][0]['lignes'][0]['valeur_nette'] is None and len(tableau['alertes'])==1
                raccord=json.loads(zip.read('raccords_mouvements.json'))
                assert raccord['actuel'] and raccord['snapshot']['controle_raccords']['tableaux']['B2']['non_rattachees']==[1]
                courant=json.loads(zip.read('resultat_courant_documentaire.json'))
                n=courant['controle_resultat_courant']['periodes']['n']
                assert n['resultat_courant']=='2000.00' and n['base_courante_documentaire']=='2300.00'
                assert n['impots_comptabilises_67']=='0.00' and n['courant_apres_impot_declare']=='800.00'
                mv=json.loads(zip.read('mouvements_documentaires.json'))
                assert mv['controle_mouvements']['tableaux']['B2']['totaux']['fin_reconstituee']=='11000.00'
                assert mv['controle_mouvements']['tableaux']['B5']['totaux']['ecart_fin']=='0.00'
                cs=json.loads(zip.read('cessions_documentaires.json'))
                assert cs['controle_cessions']['total_difference_prix_vna']=='-1000.00'
                assert cs['tables'][0]['lignes'][0]['date_sortie']=='2026-06-30'
                b4=json.loads(zip.read('participations_documentaires.json'))
                assert b4['vue']['periodes']['n']['participations']=='0.00'
                nv=json.loads(zip.read('non_valeurs_documentaires.json'))
                assert nv['vue']['periodes']['n']['net']=='0.00'
                cpc=json.loads(zip.read('detail_cpc_documentaire.json'))
                assert cpc['vue']['periodes']['n']['resultat']=='2000.00'
                assert cpc['vue']['periodes']['n1']['resultat']=='0.00'
                m=json.loads(zip.read('MANIFESTE_SHA256.json'))
                assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
                for n,v in m['fichiers'].items():
                    assert len(zip.read(n))==v['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==v['sha256']
                nom='justificatifs/'+memo['doc']['nom_stockage'];assert zip.read(nom)==memo['raw']
                pdf=PdfReader(BytesIO(zip.read('preparation.pdf')));wb=load_workbook(BytesIO(zip.read('preparation.xlsx')))
                return {'documents':d,'sources':{n:zip.read(n).decode('utf8') for n in zip.namelist() if n.endswith(('.csv','.json')) and n!='MANIFESTE_SHA256.json'},
                    'pdf':'\n'.join(p.extract_text() or '' for p in pdf.pages),
                    'images':[hashlib.sha256(i.data).hexdigest() for p in pdf.pages for i in p.images],
                    'xlsx':{ws.title:list(ws.values) for ws in wb},'piece_sha256':hashlib.sha256(zip.read(nom)).hexdigest()}

    def dataset(app):
        if not memo:
            api,email,password=client_orig(app)
            try:
                v1=creer(api);v2=recette.ok(api.post(chemin(v1),json=demande(v1)),201)
                v3=recette.ok(api.post(notes_url(v2),json=notes(v2)),201)
                v4=recette.ok(api.post(financement_url(v3),json=flux(v3)),201)
                v5=recette.ok(api.post(tables_url(v4),json=tables(v4)),201)
                v6=recette.ok(api.post(annexes_url(v5),json=annexes(v5)),201)
                v7=recette.ok(api.post(cpc_url(v6),json=cpc_body(v6)),201)
                v8=recette.ok(api.post(nv_url(v7),json=nv_body(v7)),201)
                v=recette.ok(api.post(b4_url(v8),json=b4_body(v8)),201)
                v=recette.ok(api.post(cs_url(v),json=cs_body(v)),201)
                v=recette.ok(api.post(mv_url(v),json=mv_body(v)),201)
                v=recette.ok(api.post(rc_url(v),json=rc_body(v,vides=True)),201)
                v=recette.ok(api.post(courant_url(v),json=courant_body(v)),201);raw=pdf_fictif()
                doc=recette.ok(joindre(api,v,raw=raw),201)
                sid=recette.ok(api.get('/api/auth/me'))['societe_id']
                relatif=f'{sid}/balance_preparation_documents/{v["id"]}/{doc["nom_stockage"]}'
                supplements[relatif]=(len(raw),hashlib.sha256(raw).hexdigest())
                recette.ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
                autre=creer_nv(api);autre=recette.ok(api.post(nv_url(autre),json=nv_body(autre)),201)
                b4=creer_b4(api);b4=recette.ok(api.post(b4_url(b4),json=b4_body(b4)),201)
                b4=recette.ok(api.post(em_url(b4),json=em_body(b4)),201)
                rc=creer_rc(api);rc=recette.ok(api.post(rc_url(rc),json=rc_body(rc)),201)
                memo.update(email=email,password=password,v=v,doc=doc,raw=raw,autre_b1=autre,autre_b4=b4,autre_raccord=rc)
                avant=donnees_metier(app);memo['situation']=situation(app['api_url']);assert donnees_metier(app)==avant
            finally:api.close()
        return client_orig(app)

    def cible(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads);runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
        try:
            avant=donnees_metier({'engine':runtime});assert situation(url)==memo['situation']
            assert donnees_metier({'engine':runtime})==avant
            preuve['pieces_octets_traces_dossier_manifestes_logos_identiques']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:runtime.dispose()

    monkeypatch.setattr(recette,'application_isolee',application104)
    monkeypatch.setattr(recette,'client',dataset);monkeypatch.setattr(recette,'lancer_cible',cible)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path,fichiers_supplementaires=supplements)
        p=json.loads(historique.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['tables']==83 and p['source_preservee'] and p['cibles_supprimees']
        assert p['schema_donnees_acl_sequences_identiques']
        preuve.update(p,pieces_octets_traces_dossier_manifestes_logos_identiques=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/restauration721_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
        if ancien is not None:historique.write_bytes(ancien)
        elif historique.exists():historique.unlink()
