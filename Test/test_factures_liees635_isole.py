"""Vente validée -> achat brouillon, transactions et deux Journaux natifs isolés."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_societes_liees633_isole import (
    application as application101,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,paire,PATH)
from test_avances_salaries_isole import appliquer
from recette_restauration_consolidee_084 import empreintes_tables
from test_restauration_runtime_acl_089 import catalogue_acl
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_prorata_inventaire_isole import photo
from test_journal_cloture_concurrente_isole import moteur


@pytest.fixture(scope='module')
def application(application101):
    app=application101
    a,b,d,ids=paire(app)
    try:assert a.get(f'{PATH}/factures/1/correspondance').status_code==503
    finally:a.close();b.close()
    avant=empreintes_tables(app['engine']);acl=catalogue_acl(app['engine'])
    appliquer(app,'102_factures_correspondantes.sql')
    apres=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    assert all(apres[k]==v for k,v in avant.items())
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    appliquer(app,'102_factures_correspondantes.sql')
    assert empreintes_tables(app['engine'])==apres and catalogue_acl(app['engine'])==droits
    yield app
    avant=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    appliquer(app,'102_factures_correspondantes.sql')
    assert empreintes_tables(app['engine'])==avant and catalogue_acl(app['engine'])==droits


def vente(app,*,valider=True,ras=0,frais=False,logos=False):
    a,b,d,ids=paire(app)
    l=ok(a.post(PATH,json=d),201)
    if logos:
        from test_logo_societe import image_data
        ok(a.patch('/api/societe/moi',json={'logo_url':image_data('PNG',(20,12))}))
        ok(b.patch('/api/societe/moi',json={'logo_url':image_data('PNG',(23,17))}))
    for api in (a,b):ok(api.patch('/api/societe/moi',json={'stock_declencheur_vente':'facture','stock_declencheur_achat':'facture'}))
    def art(api,nom,stock):
        return ok(api.post('/api/articles',json={'code':uuid4().hex[:10],'designation':nom,'stock_actuel':stock,'is_stockable':True,'compte_achat':'6111','compte_vente':'71243','tva':20}),201)['id']
    av=art(a,'Article du vendeur fictif635',10);aa=art(b,'Référence acheteur fictive635',20)
    f=ok(a.post('/api/factures',json={'type':'vente','date':date.today().isoformat(),'tiers':'Acheteur fictif','tiers_id':d['client_id'],'ras_taux':ras,
        'frais_transport_ht':40 if frais else 0,'frais_emballage_ht':20 if frais else 0,
        'lignes':[{'article_id':av,'description':'Lot A facturé fictif635','quantite':2,'prix_unitaire':100,'tva':20},
                  {'article_id':av,'description':'Lot B facturé fictif635','quantite':3,'prix_unitaire':100,'tva':20}]}),201)
    if valider:ok(a.post(f'/api/factures/{f["id"]}/valider'))
    corps={'nature_tva_achat':'charge','tva_deductible_pct':'100','lignes':[{'source_ligne_id':x['id'],'article_id':aa} for x in f['lignes']]}
    ids.update({'liaison':l['id'],'fid':f['id'],'av':av,'aa':aa,'corps':corps})
    return a,b,ids


def chemin(ids,suffix=''):
    return f'{PATH}/{ids["liaison"]}/factures/{ids["fid"]}'+suffix


def demande(a,ids,corps=None):
    d=corps or ids['corps'];p=ok(a.post(chemin(ids,'/apercu'),json=d))
    return {**d,'empreinte':p['empreinte'],'cle':str(uuid4()),'correspondance_verifiee':True}


def test_635_creation_rejeu_stock_journaux_auxiliaires_fec_et_registre(application):
    a,b,ids=vente(application)
    try:
        before=donnees_metier(application)
        c=demande(a,ids)
        assert donnees_metier(application)==before
        with application['engine'].connect() as db:
            src=db.scalar(text('SELECT numero FROM factures WHERE id=:id'),{'id':ids['fid']})
            assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:id'),{'id':ids['av']})==5
        suivi=ok(a.post(chemin(ids),json=c),201);fid=suivi['facture_achat_id']
        assert suivi['ecarts']==[] and not suivi['achat']['validee'] and not suivi['achat']['comptabilisee']
        assert suivi['achat']['numero'] is None and suivi['achat']['reference']==src
        assert ok(a.post(chemin(ids),json={**c,'tva_deductible_pct':'100.00'}),201)==suivi
        assert ok(b.get(f'{PATH}/factures/{fid}/correspondance'))==suivi
        assert a.post(chemin(ids),json={**c,'cle':str(uuid4())}).status_code==409
        assert a.post(chemin(ids),json={**c,'tva_deductible_pct':'50'}).status_code==409
        assert b.delete(f'/api/factures/{fid}').status_code==409
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:id'),{'id':ids['aa']})==20
            assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id IN (:a,:b)'),{'a':ids['sid'],'b':ids['bid']})==0
        # Chaque société utilise ensuite le flux métier ordinaire, séparément.
        ok(b.post(f'/api/factures/{fid}/valider'))
        for api,f,compte,montant in ((a,ids['fid'],'3421',600),(b,fid,'4411',-600)):
            eid=ok(api.post(f'/api/factures/{f}/comptabiliser'))['ecriture_id']
            ok(api.post(f'/api/ecritures/{eid}/valider'))
            with application['engine'].connect() as db:
                ls=db.execute(text('SELECT compte,debit,credit,tiers_id,compte_auxiliaire_snapshot FROM lignes_ecriture WHERE ecriture_id=:id'),{'id':eid}).mappings().all()
                assert sum(x['debit'] for x in ls)==sum(x['credit'] for x in ls)==Decimal(600)
                x=next(x for x in ls if x['compte']==compte)
                assert x['debit']-x['credit']==Decimal(montant) and x['tiers_id'] and x['compte_auxiliaire_snapshot']
                attendus={'3421':(600,0),'4455':(0,100),'71243':(0,500)} if api is a else {'4411':(0,600),'34552':(100,0),'6111':(500,0)}
                assert {x['compte']:(x['debit'],x['credit']) for x in ls}==attendus
            fec=api.get('/api/fec/export',params={'exercice':date.today().year});assert fec.status_code==200 and src in fec.text
        fin=ok(a.get(f'{PATH}/factures/{ids["fid"]}/correspondance'))
        assert fin['ecarts']==[] and fin['vente']['comptabilisee'] and fin['achat']['comptabilisee']
        with application['engine'].connect() as db:assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:id'),{'id':ids['aa']})==25
    finally:a.close();b.close()


def test_635_exercice_decale_acheteur_deduit_du_calendrier(application):
    a,b,ids=vente(application)
    try:
        y=date.today().year
        ok(b.patch(f'/api/exercices/{y}',json={'date_debut':f'{y-1}-07-01','date_fin':f'{y}-06-30'}))
        ok(b.post('/api/exercices',json={'annee':y+1,'date_debut':f'{y}-07-01','date_fin':f'{y+1}-06-30'}),201)
        s=ok(a.post(chemin(ids),json=demande(a,ids)),201)
        cible=y+(date.today().month>=7)
        assert s['vente']['exercice']==y and s['achat']['exercice']==cible
        fid=s['facture_achat_id'];ok(b.post(f'/api/factures/{fid}/valider'))
        eid=ok(b.post(f'/api/factures/{fid}/comptabiliser'))['ecriture_id'];ok(b.post(f'/api/ecritures/{eid}/valider'))
        with application['engine'].connect() as db:assert db.scalar(text('SELECT exercice FROM ecritures WHERE id=:id'),{'id':eid})==cible
        assert b.get('/api/fec/export',params={'exercice':cible}).status_code==200
    finally:a.close();b.close()


def test_635_logos_societes_distinctes_dans_les_deux_pdf(application):
    from io import BytesIO
    from PIL import Image
    from pypdf import PdfReader
    a,b,ids=vente(application,logos=True)
    try:
        s=ok(a.post(chemin(ids),json=demande(a,ids)),201);fid=s['facture_achat_id'];ok(b.post(f'/api/factures/{fid}/valider'))
        for api,f,size in ((a,ids['fid'],(20,12)),(b,fid,(23,17))):
            r=api.get(f'/api/factures/{f}/pdf');assert r.status_code==200,r.text
            p=PdfReader(BytesIO(r.content))
            assert any(Image.open(BytesIO(i.data)).size==size for page in p.pages for i in page.images)
            assert s['achat']['reference'] in '\n'.join(page.extract_text() for page in p.pages)
    finally:a.close();b.close()


def test_635_avoir_signale_sans_miroir_ou_modification_silencieuse(application):
    a,b,ids=vente(application)
    try:
        s=ok(a.post(chemin(ids),json=demande(a,ids)),201)
        ok(a.post('/api/avoirs',json={'facture_id':ids['fid'],'date':date.today().isoformat(),'motif':'Correction fictive635','lignes':[{'facture_ligne_id':ids['corps']['lignes'][0]['source_ligne_id'],'quantite':1}]}),201)
        fin=ok(b.get(f'{PATH}/factures/{s["facture_achat_id"]}/correspondance'))
        assert 'avoir_a_traiter_separement' in fin['ecarts']
        with application['engine'].connect() as db:assert db.scalar(text('SELECT count(*) FROM avoirs WHERE societe_id=:s'),{'s':ids['bid']})==0
    finally:a.close();b.close()


def test_635_tva_achat_inconnue_reste_diagnostic(application):
    a,b,ids=vente(application)
    try:
        s=ok(a.post(chemin(ids),json=demande(a,ids)),201)
        with application['engine'].begin() as db:db.execute(text('UPDATE factures SET tva_deductible_pct=NULL WHERE id=:id'),{'id':s['facture_achat_id']})
        avant=donnees_metier(application)
        fin=ok(a.get(f'{PATH}/factures/{ids["fid"]}/correspondance'))
        assert 'tva_deductible_pct_inconnu' in fin['ecarts']
        assert donnees_metier(application)==avant
        # La contrainte existante refuse NaN : ne jamais la contourner pour un test.
        with pytest.raises(DBAPIError):
            with application['engine'].begin() as db:db.execute(text('UPDATE factures SET tva_deductible_pct=:v WHERE id=:id'),{'v':Decimal('NaN'),'id':s['facture_achat_id']})
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_635_achat_non_deductible_choix_explicite_et_ecriture_ordinaire(application):
    a,b,ids=vente(application)
    try:
        corps={**ids['corps'],'nature_tva_achat':'non_deductible','tva_deductible_pct':'0'}
        s=ok(a.post(chemin(ids),json=demande(a,ids,corps)),201);fid=s['facture_achat_id']
        ok(b.post(f'/api/factures/{fid}/valider'));eid=ok(b.post(f'/api/factures/{fid}/comptabiliser'))['ecriture_id']
        ok(b.post(f'/api/ecritures/{eid}/valider'))
        with application['engine'].connect() as db:
            rows=db.execute(text('SELECT compte,sum(debit),sum(credit) FROM lignes_ecriture WHERE ecriture_id=:id GROUP BY compte'),{'id':eid}).all()
            assert {c:(d,k) for c,d,k in rows}=={'6111':(Decimal(600),Decimal(0)),'4411':(Decimal(0),Decimal(600))}
    finally:a.close();b.close()


def test_635_sens_inverse_explicite_deuxieme_vendeur(application):
    a,b,ids=vente(application)
    try:
        client=ok(b.post('/api/tiers',json={'nom':'Client A inverse fictif635','type':'client'}),201)['id']
        fournisseur=ok(a.post('/api/tiers',json={'nom':'Fournisseur B inverse fictif635','type':'fournisseur'}),201)['id']
        l=ok(b.post(PATH,json={'acheteur_id':ids['sid'],'client_id':client,'fournisseur_id':fournisseur,'cle':str(uuid4()),'justification':'Sens inverse explicitement qualifié','association_verifiee':True}),201)
        f=ok(b.post('/api/factures',json={'type':'vente','date':date.today().isoformat(),'tiers':'Client A','tiers_id':client,'lignes':[{'article_id':ids['aa'],'description':'Vente inverse fictive635','quantite':1,'prix_unitaire':100,'tva':20}]}),201)
        ok(b.post(f'/api/factures/{f["id"]}/valider'))
        inverse={**ids,'liaison':l['id'],'fid':f['id'],'corps':{'nature_tva_achat':'charge','tva_deductible_pct':'100','lignes':[{'source_ligne_id':f['lignes'][0]['id'],'article_id':ids['av']}]}}
        s=ok(b.post(chemin(inverse),json=demande(b,inverse)),201)
        assert s['acheteur_id']==ids['sid'] and s['vendeur_id']==ids['bid'] and not s['ecarts']
    finally:a.close();b.close()


def test_635_frais_copies_exactement_et_source_preservee(application):
    a,b,ids=vente(application,frais=True)
    try:
        with application['engine'].connect() as db:
            avant=db.execute(text('SELECT row_to_json(f)::text FROM factures f WHERE id=:id'),{'id':ids['fid']}).scalar()
        s=ok(a.post(chemin(ids),json=demande(a,ids)),201)
        achat=next(x for x in ok(b.get('/api/factures',params={'exercice':date.today().year})) if x['id']==s['facture_achat_id'])
        assert (achat['total_ht'],achat['total_tva'],achat['total_ttc'])==(560,112,672)
        with application['engine'].connect() as db:assert db.execute(text('SELECT row_to_json(f)::text FROM factures f WHERE id=:id'),{'id':ids['fid']}).scalar()==avant
    finally:a.close();b.close()


@pytest.mark.parametrize('changement',[{'tva_deductible_pct':'NaN'},{'tva_deductible_pct':'Infinity'},{'tva_deductible_pct':True},{'tva_deductible_pct':'100.001'},{'tva_deductible_pct':'101'},{'nature_tva_achat':'immobilisation'},{'nature_tva_achat':'non_deductible','tva_deductible_pct':'100'},{'lignes':[]}])
def test_635_parametres_invalides_sans_mutation(application,changement):
    a,b,ids=vente(application)
    try:
        avant=donnees_metier(application)
        assert a.post(chemin(ids,'/apercu'),json={**ids['corps'],**changement}).status_code==422
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_635_selection_explicite_et_empreinte_perimee(application):
    a,b,ids=vente(application)
    try:
        c=demande(a,ids);avant=donnees_metier(application)
        ls=ids['corps']['lignes']
        for lignes in ([ls[0]],[ls[0],ls[0]],[{**x,'article_id':ids['av']} for x in ls]):
            assert a.post(chemin(ids,'/apercu'),json={**ids['corps'],'lignes':lignes}).status_code==422
            assert donnees_metier(application)==avant
        with application['engine'].begin() as db:db.execute(text("UPDATE articles SET designation='Désignation modifiée fictive635' WHERE id=:id"),{'id':ids['aa']})
        avant=donnees_metier(application)
        assert a.post(chemin(ids),json=c).status_code==409
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_635_brouillon_et_ras_et_periode_fermee_refuses(application):
    for param,code in (({'valider':False},409),({'ras':10},422)):
        a,b,ids=vente(application,**param)
        try:
            avant=donnees_metier(application)
            assert a.post(chemin(ids,'/apercu'),json=ids['corps']).status_code==code
            assert donnees_metier(application)==avant
        finally:a.close();b.close()
    a,b,ids=vente(application)
    try:
        c=demande(a,ids)
        with application['engine'].begin() as db:db.execute(text("UPDATE periodes_comptables p SET statut='fermee' FROM exercices_comptables e WHERE p.exercice_id=e.id AND e.societe_id=:s AND :d BETWEEN p.date_debut AND p.date_fin"),{'s':ids['bid'],'d':date.today()})
        avant=donnees_metier(application)
        assert a.post(chemin(ids),json=c).status_code==423
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_635_permissions_retrait_et_cloture_en_cours(application):
    a,b,ids=vente(application)
    try:
        c=demande(a,ids);avant=donnees_metier(application)
        assert b.post(chemin(ids),json=c).status_code==403
        assert donnees_metier(application)==avant
        with application['engine'].begin() as db:
            db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))'),{'k':f'hisabpro:tva-cloture:{ids["bid"]}:{date.today().year}'})
            assert a.post(chemin(ids),json=c).status_code==409
        assert donnees_metier(application)==avant
        with application['engine'].begin() as db:db.execute(text("UPDATE utilisateurs_societes SET role='lecture' WHERE societe_id=:s AND utilisateur_id=:u"),{'s':ids['bid'],'u':ids['uid']})
        avant=donnees_metier(application)
        assert a.post(chemin(ids),json=c).status_code==403
        assert donnees_metier(application)==avant
        with application['engine'].begin() as db:db.execute(text("UPDATE utilisateurs_societes SET role='admin' WHERE societe_id=:s AND utilisateur_id=:u"),{'s':ids['bid'],'u':ids['uid']})
        ok(a.post(f'{PATH}/{ids["liaison"]}/retirer',json={'motif':'Consentement fictif retiré'}))
        avant=donnees_metier(application)
        assert a.post(chemin(ids),json=c).status_code==409
        assert donnees_metier(application)==avant
    finally:a.close();b.close()


def test_635_atomicite_aucun_brouillon_orphelin(application):
    a,b,ids=vente(application)
    try:
        c=demande(a,ids);avant=donnees_metier(application)
        with application['engine'].begin() as db:
            db.execute(text("CREATE FUNCTION test_refus635() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Refus fictif635' USING ERRCODE='23514'; END $$"))
            db.execute(text('CREATE TRIGGER test_refus635 BEFORE INSERT ON factures_correspondantes FOR EACH ROW EXECUTE FUNCTION test_refus635()'))
        try:assert a.post(chemin(ids),json=c).status_code==409
        finally:
            with application['engine'].begin() as db:
                db.execute(text('DROP TRIGGER test_refus635 ON factures_correspondantes'));db.execute(text('DROP FUNCTION test_refus635()'))
        assert donnees_metier(application)==avant
        assert ok(a.post(chemin(ids),json=c),201)['ecarts']==[]
    finally:a.close();b.close()


def test_635_concurrence_ecarts_et_historique_immutable(application):
    a,b,ids=vente(application)
    try:
        c=demande(a,ids)
        with ThreadPoolExecutor(2) as p:rs=list(p.map(lambda _:a.post(chemin(ids),json=c),range(2)))
        s=[ok(r,201) for r in rs];assert s[0]==s[1]
        fid=s[0]['facture_achat_id']
        # Modification volontaire d'un brouillon : jamais synchronisée silencieusement.
        achat=next(x for x in ok(b.get('/api/factures',params={'exercice':date.today().year})) if x['id']==fid)
        achat['lignes'][0]['prix_unitaire']=101
        ok(b.patch(f'/api/factures/{fid}',json={'lignes':achat['lignes']}))
        suivi=ok(a.get(f'{PATH}/factures/{ids["fid"]}/correspondance'))
        assert any(x.startswith('ligne_source_') for x in suivi['ecarts'])
        e=moteur(application)
        try:
            for sql in ('UPDATE factures_correspondantes SET faits=faits WHERE id=:id','DELETE FROM factures_correspondantes WHERE id=:id','TRUNCATE factures_correspondantes'):
                with pytest.raises(DBAPIError):
                    with e.begin() as db:db.execute(text(sql),{'id':s[0]['id']})
        finally:e.dispose()
    finally:a.close();b.close()
