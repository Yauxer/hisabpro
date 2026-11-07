"""084 restaurée avec son relevé, son lot et ses gardes : deux PGnonce."""
from contextlib import closing
from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
from postgres_isole import cluster_isole,verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_rapprochement_ventilation_isole import migration,preparer,rapprocher
from test_ras_lecture_conservation import client
from routers import rapprochement as banque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ops.postgres_sauvegarde import sauvegarder,restaurer_isole

def instantane(engine):
    with engine.connect() as db:
        return {nom:db.execute(text(f'SELECT row_to_json(t)::text FROM public.{nom} t ORDER BY {ordre}')).scalars().all()
            for nom,ordre in [('societes','id'),('utilisateurs','id'),('factures','id'),('reglements','id'),
                ('ecritures','id'),('lignes_ecriture','id'),('rapprochement_lignes','id'),
                ('rapprochement_ventilations','releve_id,ecriture_ligne_id')]}

def test_dump_restore_liens84_origines_role_app_et_rejeu(application,migration):
    source=application['cluster']
    assert verifier_cible_isolee(source['url'],source['directory'],source['nonce'])
    with closing(client(application)[0]) as api:
        payload,rows,rid,lids=preparer(application,api)
        r=rapprocher(api,rid,payload);assert r.status_code==200,r.text
        with Session(application['engine']) as db:
            releve=db.get(banque.models.RapprochementLigne,rid)
            utilisateur={'societe_id':releve.societe_id,'id':releve.rapproche_par}
    avant=instantane(application['engine'])
    with cluster_isole() as cible:
        def garde():
            for c in (source,cible):assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        garde();assert cible['nonce']!=source['nonce'] and cible['port']!=source['port']
        archive=sauvegarder(source['url'],source['directory']/'ventilation84.dump',source['bin'])
        garde();restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],cible['nonce'])
        restauree=create_engine(cible['url']);runtime=None
        try:
            assert instantane(restauree)==avant==instantane(application['engine'])
            with restauree.connect() as db:
                assert db.execute(text('SELECT COUNT(*) FROM rapprochement_ventilations WHERE releve_id=:rid'),{'rid':rid}).scalar()==2
                names=['trg_hisabpro_rapprochement_ventilation','trg_hisabpro_releve_ventilation',
                    'trg_hisabpro_ventilation_commit','trg_hisabpro_no_truncate_ventilation',
                    'trg_hisabpro_guard_rapprochement_comptable','trg_hisabpro_rapprochement_exercice_cloture']
                triggers=db.execute(text('SELECT tgname,tgenabled FROM pg_trigger WHERE tgname=ANY(:names)'),{'names':names}).all()
                assert len(triggers)==6 and {r[1] for r in triggers}=={'O'}
                with pytest.raises(DBAPIError) as erreur:
                    db.execute(text('TRUNCATE rapprochement_ventilations'));db.commit()
                assert erreur.value.orig.pgcode=='23514';db.rollback()
            with restauree.begin() as db:
                db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
            sql=Path(__file__).resolve().parents[1]/'hisabpro-backend/084_rapprochement_ventilations.sql'
            garde();raw=restauree.raw_connection()
            try:
                with raw.cursor() as cur:cur.execute(sql.read_text(encoding='utf-8'))
                raw.commit()
            finally:raw.close()
            assert instantane(restauree)==avant
            runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
            with Session(runtime) as db:
                assert db.execute(text('SELECT current_user')).scalar()=='hisabpro'
                assert banque.rapprocher_ventilation(rid,banque.RapprocherVentilationIn(operation_id=payload['operation_id']),utilisateur,db)['ok']
                assert not banque.derapprocher_ligne(rid,utilisateur,db).rapprochee
                assert banque.rapprocher_ventilation(rid,banque.RapprocherVentilationIn(operation_id=payload['operation_id']),utilisateur,db)['ok']
            # Date/acteur de pointage peuvent être renouvelés ; les associations
            # et toutes les écritures sont les mêmes, pas les métadonnées du relevé.
            apres=instantane(restauree)
            assert all(apres[t]==avant[t] for t in avant if t!='rapprochement_lignes')
            with pytest.raises(ValueError,match='doit être vide'):
                garde();restaurer_isole(cible['url'],archive,cible['bin'],cible['directory'],cible['nonce'])
            assert instantane(application['engine'])==avant
        finally:
            if runtime is not None:runtime.dispose()
            restauree.dispose()
    assert not cible['directory'].exists()
