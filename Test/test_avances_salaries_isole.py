"""Registre 095 : HTTP/Edge et SQL natif, clusters PostgreSQL nonce uniquement."""
from contextlib import closing
from datetime import date
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import uuid
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from playwright.sync_api import sync_playwright, expect
from test_permissions_tva_runtime_isole import (
    application as application093, application092, application091, application090,
    application089, application087, migration,
)
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import empreintes_tables
from test_restauration_runtime_acl_089 import catalogue_acl
from postgres_isole import verifier_cible_isolee
from test_multi_societes_runtime_isole import ok
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable

PATH='/api/employes/avances'


def appliquer(app,nom):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((BACK/nom).read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application093):
    app=application093
    appliquer(app,'094_protection_parametres_tva_clotures.sql')
    with closing(client(app)[0]) as api:
        r=api.get(PATH);assert r.status_code==503 and '095' in r.text
    avant=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    appliquer(app,'095_registre_avances_salaries.sql')
    apres=empreintes_tables(app['engine'])
    assert all(apres[t]==h for t,h in avant.items())
    acl=catalogue_acl(app['engine'])
    assert all(all(v in acl[k] for v in vals) for k,vals in droits.items())
    appliquer(app,'095_registre_avances_salaries.sql')
    assert empreintes_tables(app['engine'])==apres and catalogue_acl(app['engine'])==acl
    yield app
    assert catalogue_acl(app['engine'])==acl


def employe(api,nom='Salarié avances fictif'):
    return ok(api.post('/api/employes',json={'nom':nom,'salaire_brut':6000,'personnes_charge_ir':0}),201)['id']


def mouvement(api,montant=1000,credit=False,valide=True,compte='3431',jour=None):
    e=ok(api.post('/api/ecritures',json={'date':jour or date.today().isoformat(),'journal':'BQ',
        'libelle':'Avance fictive registre 482','reference':'AV-'+uuid.uuid4().hex[:10],
        'est_validee':valide,'lignes':[{'compte':compte,'debit':0 if credit else montant,'credit':montant if credit else 0},
        {'compte':'5141','credit':0 if credit else montant,'debit':montant if credit else 0}]}),201)
    return e,next(l['id'] for l in e['lignes'] if l['compte']==compte)


def affecter(api,p,l,status=201):
    return ok(api.post(PATH,json={'employe_id':p,'ligne_id':l,'motif':'Pièce fictive contrôlée'}),status)


def originaux(app,sid):
    with app['engine'].connect() as db:
        return {t:db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t WHERE '+
          ('societe_id=:s' if t=='ecritures' else 'ecriture_id IN (SELECT id FROM ecritures WHERE societe_id=:s)')+
          ' ORDER BY id'),{'s':sid}).scalars().all() for t in ('ecritures','lignes_ecriture')}


def test_cycle_affectation_recuperation_annulation_reaffectation_sans_ecriture(application):
    with closing(client(application)[0]) as api:
        p=employe(api);p2=employe(api,'Autre salarié fictif')
        _,d=mouvement(api,1200);_,c=mouvement(api,300,credit=True)
        sid=ok(api.get('/api/societe/moi'))['id'];avant=originaux(application,sid)
        fec=api.get('/api/fec/export',params={'exercice':date.today().year});assert fec.status_code==200
        a=affecter(api,p,d)['id'];b=affecter(api,p,c)['id']
        r=ok(api.get(PATH));assert r['non_affectes']==0
        assert [(s['debit'],s['credit'],s['solde']) for s in r['soldes']]==[(1200,300,900)]
        assert api.post(PATH+f'/{a}/annuler',json={'motif':'Erreur fictive'}).status_code==409
        ok(api.post(PATH+f'/{b}/annuler',json={'motif':'Mauvais bénéficiaire fictif'}))
        ok(api.post(PATH+f'/{a}/annuler',json={'motif':'Correction fictive'}))
        a2=affecter(api,p2,d)['id'];assert a2!=a
        affecter(api,p2,c)
        r=ok(api.get(PATH));assert len(r['historique'])==4
        assert len([h for h in r['historique'] if h['annule_at']])==2
        assert r['soldes'][0]['nom']=='Autre salarié fictif' and r['soldes'][0]['solde']==900
        assert originaux(application,sid)==avant
        assert api.get('/api/fec/export',params={'exercice':date.today().year}).content==fec.content
        avant=empreintes_tables(application['engine']);appliquer(application,'095_registre_avances_salaries.sql')
        assert empreintes_tables(application['engine'])==avant


@pytest.mark.parametrize('cas',['doublon','exces','date_anterieure','brouillon','autre_compte','archive','autre_societe','cloture'])
def test_refus_metier_et_isolation(application,cas):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        p=employe(api)
        if cas=='date_anterieure':_,ancien=mouvement(api,100,credit=True,jour=f'{date.today().year}-01-01')
        e,d=mouvement(api,1000);a=affecter(api,p,d)['id']
        cible=d;status=409;beneficiaire=p
        if cas=='exces':_,cible=mouvement(api,1001,credit=True)
        elif cas=='date_anterieure':cible=ancien
        elif cas=='brouillon':_,cible=mouvement(api,20,valide=False);status=404
        elif cas=='autre_compte':_,cible=mouvement(api,20,compte='3438');status=404
        elif cas=='archive':
            ok(api.delete('/api/employes/'+str(p)),204);_,cible=mouvement(api,20)
        elif cas=='autre_societe':
            beneficiaire=employe(autre);status=404
        elif cas=='cloture':
            _,cible=mouvement(api,20)
            with application['engine'].begin() as db:
                db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s"),{'s':ok(api.get('/api/societe/moi'))['id']})
        avant=ok(api.get(PATH))
        r=api.post(PATH,json={'employe_id':beneficiaire,'ligne_id':cible,'motif':'Test négatif fictif'})
        assert r.status_code==status,r.text
        assert ok(api.get(PATH))==avant
        assert autre.post(PATH+f'/{a}/annuler',json={'motif':'Autre société'}).status_code==404
        assert ok(autre.get(PATH))['mouvements']==[]
        if cas=='cloture':assert api.post(PATH+f'/{a}/annuler',json={'motif':'Exercice clos'}).status_code==409


@pytest.mark.parametrize('payload',[{'employe_id':True,'ligne_id':1,'motif':'x'},
    {'employe_id':1,'ligne_id':1.5,'motif':'x'}, {'employe_id':1,'ligne_id':1,'motif':'   '},
    {'employe_id':1,'ligne_id':1,'motif':'x','montant':'NaN'}])
def test_saisie_stricte_aucun_montant_libre(application,payload):
    with closing(client(application)[0]) as api:
        assert api.post(PATH,json=payload).status_code==422


def test_lecture_seule_et_droits_sql_immutabilite(application):
    with closing(client(application)[0]) as api:
        p=employe(api);_,l=mouvement(api);a=affecter(api,p,l)['id']
        # Compte lecteur authentifié réel ; rôle métier modifié uniquement dans le laboratoire.
        uid=ok(api.get('/api/auth/me'))['id']
        with application['engine'].begin() as db:
            db.execute(text("UPDATE utilisateurs SET role='lecture' WHERE id=:u"),{'u':uid})
        assert api.get(PATH).status_code==200
        assert api.post(PATH,json={'employe_id':p,'ligne_id':l,'motif':'Refus'}).status_code==403
        assert api.post(PATH+f'/{a}/annuler',json={'motif':'Refus'}).status_code==403
        from sqlalchemy import create_engine
        from sqlalchemy.engine import make_url
        runtime=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'))
        try:
            with runtime.connect() as db:
                assert not db.scalar(text("SELECT has_table_privilege(current_user,'grh_avances_affectations','DELETE')"))
                assert not db.scalar(text("SELECT has_table_privilege(current_user,'grh_avances_affectations','TRUNCATE')"))
                assert not db.scalar(text("SELECT has_column_privilege(current_user,'grh_avances_affectations','employe_id','UPDATE')"))
                assert not db.scalar(text("SELECT has_sequence_privilege(current_user,'grh_avances_affectations_id_seq','UPDATE')"))
        finally:runtime.dispose()
        for sql in ['DELETE FROM grh_avances_affectations WHERE id=:i',
                    'TRUNCATE grh_avances_affectations',
                    'UPDATE grh_avances_affectations SET motif=\'réécrit\' WHERE id=:i']:
            with pytest.raises(DBAPIError) as err:
                with application['engine'].begin() as db:db.execute(text(sql),{'i':a})
            assert err.value.orig.pgcode=='23514'


def test_recuperations_concurrentes_une_seule_acceptee(application):
    with closing(client(application)[0]) as api:
        p=employe(api);_,d=mouvement(api,1000);affecter(api,p,d)
        _,c1=mouvement(api,700,credit=True);_,c2=mouvement(api,700,credit=True)
        gate=Barrier(2)
        def poster(ligne):
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=20) as c:
                gate.wait(timeout=10)
                return c.post(PATH,json={'employe_id':p,'ligne_id':ligne,'motif':'Concurrence fictive'}).status_code
        with ThreadPoolExecutor(2) as pool:codes=list(pool.map(poster,[c1,c2]))
        assert sorted(codes)==[201,409]
        r=ok(api.get(PATH));assert r['soldes'][0]['solde']==300 and r['non_affectes']==1


@pytest.mark.parametrize('cas',['tiers_societe','source_societe','brouillon','autre_compte','exces','cloture','annulation_incomplete'])
def test_sql_natif_refuse_contournements_sans_muter_sources(application,cas):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        p=employe(api);sid=ok(api.get('/api/societe/moi'))['id'];uid=ok(api.get('/api/auth/me'))['id']
        if cas=='source_societe':_,l=mouvement(autre)
        elif cas=='brouillon':_,l=mouvement(api,valide=False)
        elif cas=='autre_compte':_,l=mouvement(api,compte='3438')
        elif cas=='exces':_,l=mouvement(api,100,credit=True)
        else:_,l=mouvement(api)
        if cas=='tiers_societe':p=employe(autre)
        if cas=='cloture':
            with application['engine'].begin() as db:
                db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s"),{'s':sid})
        avant=originaux(application,sid)
        params={'s':sid,'e':p,'l':l,'u':uid}
        if cas=='annulation_incomplete':
            a=affecter(api,p,l)['id'];params['a']=a
            sql='UPDATE grh_avances_affectations SET annule_par=:u,annule_at=now() WHERE id=:a'
        else:
            sql='''INSERT INTO grh_avances_affectations(societe_id,employe_id,ligne_id,created_by,motif)
                   VALUES(:s,:e,:l,:u,'Test négatif SQL fictif')'''
        with pytest.raises(DBAPIError) as err:
            with application['engine'].begin() as db:db.execute(text(sql),params)
        assert err.value.orig.pgcode=='23514'
        assert originaux(application,sid)==avant


def test_sql_recuperations_concurrentes_serializees(application):
    with closing(client(application)[0]) as api:
        p=employe(api);sid=ok(api.get('/api/societe/moi'))['id'];uid=ok(api.get('/api/auth/me'))['id']
        _,d=mouvement(api,1000);affecter(api,p,d)
        _,c1=mouvement(api,700,credit=True);_,c2=mouvement(api,700,credit=True)
        gate=Barrier(2)
        def inserer(ligne):
            try:
                with application['engine'].begin() as db:
                    gate.wait(timeout=10)
                    db.execute(text('''INSERT INTO grh_avances_affectations(societe_id,employe_id,ligne_id,created_by,motif)
                        VALUES(:s,:e,:l,:u,'Concurrence SQL fictive')'''),{'s':sid,'e':p,'l':ligne,'u':uid})
                return 'ok'
            except DBAPIError as exc:return exc.orig.pgcode
        with ThreadPoolExecutor(2) as pool:codes=list(pool.map(inserer,[c1,c2]))
        assert sorted(codes)==['23514','ok']
        assert ok(api.get(PATH))['soldes'][0]['solde']==300


@pytest.mark.parametrize('largeur',[1440,390])
def test_onglet_affectation_solde_actualise_annulation_edge(application,largeur):
    api,email,password=client(application)
    with closing(api):
        employe(api,'Salariée interface fictive');_,d=mouvement(api,1200);_,c=mouvement(api,300,credit=True)
        sid=ok(api.get('/api/societe/moi'))['id'];avant=originaux(application,sid)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1100});page.set_default_timeout(15000)
                errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/cnss')
                page.get_by_role('button',name='Avances des salariés',exact=True).click()
                zone=page.get_by_role('region',name='Avances des salariés',exact=True)
                expect(zone.get_by_text('2 mouvement(s) non affecté(s)',exact=False)).to_be_visible()
                for ligne in [d,c]:
                    row=zone.get_by_role('table',name='Mouvements des avances').get_by_role('row').filter(has_text=f'Ligne {ligne}')
                    row.get_by_role('button',name='Affecter',exact=True).click()
                    form=zone.get_by_role('form',name='Affecter un mouvement')
                    form.get_by_label('Salarié bénéficiaire').select_option(label='Salariée interface fictive')
                    form.get_by_label('Motif du rattachement').fill('Contrôle pièce fictive navigateur')
                    form.get_by_role('button',name='Confirmer l’affectation').click()
                    expect(form).not_to_be_visible()
                soldes=zone.get_by_role('table',name='Soldes des avances')
                expect(soldes).to_contain_text('900')
                row=zone.get_by_role('table',name='Mouvements des avances').get_by_role('row').filter(has_text=f'Ligne {c}')
                row.get_by_role('button',name='Annuler le rattachement').click()
                form=zone.get_by_role('form',name='Annuler une affectation')
                form.get_by_label('Motif du rattachement').fill('Annulation fictive contrôlée')
                form.get_by_role('button',name='Confirmer l’annulation').click()
                expect(form).not_to_be_visible();expect(soldes).to_contain_text('1.200,00 MAD')
                assert not errors and not server,(errors,server)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            finally:browser.close()
        assert originaux(application,sid)==avant
