"""Migration083 explicite : absence du metadata, rejeu et immutabilité PostgreSQL."""
from contextlib import closing
import pytest
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import date
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_acompte_fournisseur_isole import ok
from test_ras_capture_reglement_postgres import appliquer, preparer, paiement, payload


def test_absence_migration_ne_cree_rien_et_rejeu_acl(application):
    assert 'ras_reglement_captures' not in models.Base.metadata.tables
    assert 'ras_reglement_annulations' not in models.Base.metadata.tables
    with closing(client(application)[0]) as api:
        f=preparer(api,'vente'); rid=paiement(api,f,400)['id']
        capability=ok(api.get(f'/api/reglements/{rid}/ras'))
        assert capability['disponible'] is False and capability['captures']==[]
        refus=api.post(f'/api/reglements/{rid}/ras',json=payload(30,'vente'))
        assert refus.status_code==409
        with application['engine'].begin() as conn:
            assert conn.execute(text("SELECT to_regclass('public.ras_reglement_captures')")).scalar() is None
            conn.execute(text('ALTER ROLE hisabpro LOGIN'))
        appliquer(application); appliquer(application)
        c=ok(api.post(f'/api/reglements/{rid}/ras',json=payload(30,'vente')))
        with application['engine'].connect() as conn:
            assert conn.execute(text("SELECT has_table_privilege('hisabpro','public.ras_reglement_captures','SELECT') AND has_table_privilege('hisabpro','public.ras_reglement_captures','INSERT')")).scalar()
            assert not conn.execute(text("SELECT has_table_privilege('hisabpro','public.ras_reglement_captures','UPDATE,DELETE,TRUNCATE')")).scalar()
            assert conn.execute(text("SELECT has_sequence_privilege('hisabpro','public.ras_reglement_captures_id_seq','USAGE')")).scalar()
        for instruction in [f"UPDATE public.ras_reglement_captures SET reference='altération' WHERE id={c['id']}",
                            f"DELETE FROM public.ras_reglement_captures WHERE id={c['id']}", 'TRUNCATE public.ras_reglement_captures, public.ras_reglement_annulations']:
            with application['engine'].connect() as conn:
                with pytest.raises(Exception, match='conservées'):
                    conn.execute(text(instruction))
                conn.rollback()
        assert ok(api.get(f'/api/reglements/{rid}/ras'))['captures'][0]['reference']=='PIECE-RAS-FICTIVE'
        assert 'ras_reglement_captures' not in models.Base.metadata.tables
        second=paiement(api,f,200)
        with Session(application['engine']) as db:
            original=db.get(models.Ecriture,c['ecriture_id'])
            ec=models.Ecriture(societe_id=c['societe_id'],journal='OD',source='ras_reglement',
                date=date.today(),date_piece=date.today(),exercice=date.today().year,
                reference='RUNTIME-SECOND',libelle='Capture runtime fictive',lignes=[models.LigneEcriture(
                    compte=l.compte,libelle=l.libelle,debit=l.debit,credit=l.credit,tiers_id=l.tiers_id,
                    nature_auxiliaire=l.nature_auxiliaire,compte_auxiliaire_snapshot=l.compte_auxiliaire_snapshot,
                    libelle_auxiliaire_snapshot=l.libelle_auxiliaire_snapshot) for l in original.lignes])
            db.add(ec); db.commit(); eid=ec.id
            libre=models.Ecriture(societe_id=c['societe_id'],journal='OD',source='manuel',date=date.today(),
                exercice=date.today().year,reference='LIBRE-FICTIVE',libelle='Brouillon indépendant fictif',
                lignes=[models.LigneEcriture(compte='5141',debit=1,credit=0),models.LigneEcriture(compte='1111',debit=0,credit=1)])
            db.add(libre);db.commit(); ligne_libre=libre.lignes[0].id
        runtime=create_engine(application['engine'].url.set(username='hisabpro',password=None))
        try:
            with runtime.begin() as conn:
                assert conn.execute(text('SELECT current_user')).scalar()=='hisabpro'
                assert conn.execute(text('SELECT count(*) FROM public.ras_reglement_captures')).scalar()==1
                conn.execute(text('''INSERT INTO public.ras_reglement_captures
                  (societe_id,reglement_id,facture_id,ecriture_id,montant,date_operation,reference,compte_destination,created_by)
                  VALUES(:sid,:rid,:fid,:eid,30,:jour,'RUNTIME-SECOND','3453',:acteur)'''),
                  {'sid':c['societe_id'],'rid':second['id'],'fid':f['id'],'eid':eid,'jour':date.today(),'acteur':c['created_by']})
            for sql in ["UPDATE public.ras_reglement_captures SET reference='Interdit'",'DELETE FROM public.ras_reglement_captures',
                        'TRUNCATE public.ras_reglement_captures, public.ras_reglement_annulations',
                        f"INSERT INTO public.lignes_ecriture(ecriture_id,compte,debit,credit) VALUES({eid},'5141',1,0)",
                        f"UPDATE public.ecritures SET libelle='Interdit' WHERE id={eid}"]:
                with runtime.connect() as conn:
                    with pytest.raises(Exception):
                        conn.execute(text(sql))
                    conn.rollback()
            # Le runtime historique refuse déjà UPDATE par ACL. Une permission
            # temporaire de laboratoire vérifie aussi le trigger indépendamment.
            with runtime.connect() as conn:
                with pytest.raises(Exception) as refus_acl:
                    conn.execute(text('UPDATE public.lignes_ecriture SET ecriture_id=:eid WHERE id=:lid'),{'eid':eid,'lid':ligne_libre})
                assert getattr(refus_acl.value.orig,'pgcode',None)=='42501'
                conn.rollback()
            with application['engine'].begin() as conn:
                conn.execute(text('GRANT UPDATE(ecriture_id) ON public.lignes_ecriture TO hisabpro'))
                conn.execute(text('GRANT SELECT(id,ecriture_id) ON public.lignes_ecriture TO hisabpro'))
                conn.execute(text('GRANT SELECT(id,numero_ecriture,est_validee), UPDATE(id) ON public.ecritures TO hisabpro'))
            try:
                with runtime.connect() as conn:
                    with pytest.raises(Exception) as refus:
                        conn.execute(text('UPDATE public.lignes_ecriture SET ecriture_id=:eid WHERE id=:lid'),{'eid':eid,'lid':ligne_libre})
                    # Le trigger historique du plan comptable constitue encore
                    # une barrière ACL : aucun droit global supplémentaire.
                    assert getattr(refus.value.orig,'pgcode',None)=='42501',str(refus.value)
                    conn.rollback()
                    assert conn.execute(text('SELECT ecriture_id FROM public.lignes_ecriture WHERE id=:lid'),{'lid':ligne_libre}).scalar()==libre.id
            finally:
                with application['engine'].begin() as conn:
                    conn.execute(text('REVOKE UPDATE(ecriture_id) ON public.lignes_ecriture FROM hisabpro'))
                    conn.execute(text('REVOKE SELECT(id,ecriture_id) ON public.lignes_ecriture FROM hisabpro'))
                    conn.execute(text('REVOKE SELECT(id,numero_ecriture,est_validee), UPDATE(id) ON public.ecritures FROM hisabpro'))
            # Le propriétaire du cluster de recette atteint réellement la garde
            # OLD/NEW sans modifier les ACL de production ou les anciens triggers.
            for sql, params in [
                ('UPDATE public.lignes_ecriture SET ecriture_id=:eid WHERE id=:lid',{'eid':eid,'lid':ligne_libre}),
                ("INSERT INTO public.lignes_ecriture(ecriture_id,compte,debit,credit) VALUES(:eid,'5141',1,0)",{'eid':eid}),
                ("UPDATE public.ecritures SET libelle='Altération interdite' WHERE id=:eid",{'eid':eid}),
            ]:
                with application['engine'].connect() as conn:
                    with pytest.raises(Exception) as refus_trigger:
                        conn.execute(text(sql),params)
                    assert getattr(refus_trigger.value.orig,'pgcode',None)=='23514',str(refus_trigger.value)
                    assert 'capture RAS' in str(refus_trigger.value)
                    conn.rollback()
            with application['engine'].connect() as conn:
                assert conn.execute(text('SELECT ecriture_id FROM public.lignes_ecriture WHERE id=:lid'),{'lid':ligne_libre}).scalar()==libre.id
            with Session(application['engine']) as db:
                r=db.get(models.Reglement,second['id']); r.statut='annule'
                inverse=models.Ecriture(societe_id=c['societe_id'],journal='OD',source='ras_reglement',
                    date=date.today(),date_piece=date.today(),exercice=date.today().year,
                    reference='ANN-RAS-2',libelle='Faux miroir fictif',contrepassation_de_id=eid,
                    lignes=[models.LigneEcriture(compte='3453',debit=0,credit=29),models.LigneEcriture(compte='3421',debit=29,credit=0)])
                db.add(inverse);db.commit(); inverse_id=inverse.id
            with runtime.connect() as conn:
                capture_id=conn.execute(text('SELECT id FROM public.ras_reglement_captures WHERE ecriture_id=:eid'),{'eid':eid}).scalar()
                with pytest.raises(Exception,match='Liens annulation RAS'):
                    conn.execute(text('''INSERT INTO public.ras_reglement_annulations
                      (capture_id,societe_id,ecriture_id,date_operation,motif,created_by)
                      VALUES(:cid,:sid,:eid,:jour,'Miroir fictif incorrect',:acteur)'''),
                      {'cid':capture_id,'sid':c['societe_id'],'eid':inverse_id,'jour':date.today(),'acteur':c['created_by']})
                conn.rollback()
                assert conn.execute(text('SELECT count(*) FROM public.ras_reglement_annulations')).scalar()==0
        finally:
            runtime.dispose()
