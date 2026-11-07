"""Préparation documentaire des ventes : API réelle/PGnonce, aucune écriture créée."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import csv, io, uuid
import pytest
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible
from test_validation_facture_montants_historiques_postgres import photographie


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def facture(api, montant=100, type='vente', date_piece=None, valider=True, proforma=False, nom=None):
    nom = nom or 'Client préparation fictif '+uuid.uuid4().hex[:8]
    tiers = ok(api.post('/api/tiers', json={'nom':nom,'type':'les_deux','ice':'001234567890123'}),201)
    f = ok(api.post('/api/factures', json={'type':type,'tiers':nom,'tiers_id':tiers['id'],
        'date':date_piece or f'{date.today().year}-01-15','est_proforma':proforma,
        'reference':'FICT-'+uuid.uuid4().hex[:8],
        'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':montant,'tva':20}]}),201)
    if valider and not proforma:
        ok(api.post(f"/api/factures/{f['id']}/valider"))
    return f, tiers


def preparation(api, annee=None):
    return api.get(f'/api/etats/ventes/preparation/{annee or date.today().year}')


def test_preparation_vide_zero_documentaire_et_lecture_sans_mutation(application):
    with closing(client(application)[0]) as api:
        avant=photographie(application)
        data=ok(preparation(api))
        assert data['documents']==[] and data['totaux']=={'ht':'0.00','tva':'0.00','ttc':'0.00'}
        assert 'ni le chiffre d’affaires comptable' in data['note']
        assert len(data['empreinte_sha256'])==64
        assert photographie(application)==avant


def test_factures_avoirs_exclusions_snapshots_et_csv_exact(application):
    with closing(client(application)[0]) as api:
        f,tiers=facture(api,100,nom='=Client fictif export')
        facture(api,200)
        facture(api,500,type='achat')
        facture(api,400,valider=False)
        facture(api,300,proforma=True)
        annule,_=facture(api,600,valider=False)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text("UPDATE factures SET statut='annulee' WHERE id=:id"),{'id':annule['id']})
        avoir=ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':f'{date.today().year}-03-15',
            'motif':'Correction fictive','lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':0.3}]}),201)
        # La préparation doit conserver l'identité au moment de la pièce.
        ok(api.put(f"/api/tiers/{tiers['id']}",json={'ice':'009876543210987'}))
        avant=photographie(application)
        data=ok(preparation(api))
        assert data['totaux']=={'ht':'270.00','tva':'54.00','ttc':'324.00'},data
        assert data['exclusions']=={'brouillons':1,'proformas':1,'annules':1}
        assert len(data['documents'])==3
        source=next(r for r in data['documents'] if r['nature']=='facture' and r['id']==f['id'])
        assert source['ice']=='001234567890123'
        credit=next(r for r in data['documents'] if r['nature']=='avoir')
        assert credit['date']==f'{date.today().year}-03-15' and credit['ht']=='-30.00'
        assert credit['id']==avoir['id'] and credit['facture_id']==f['id']
        rows=list(csv.reader(io.StringIO(data['csv']),delimiter=';'))
        assert any("'=Client fictif export" in r for r in rows)
        assert any(r[0]=='Total complet' and r[7:10]==['270.00','54.00','324.00'] for r in rows)
        assert photographie(application)==avant


@pytest.mark.parametrize('valeur',[float('nan'),float('inf'),float('-inf'),None])
def test_montant_historique_inconnu_conserve_piece_et_ne_devient_pas_zero(application,valeur):
    with closing(client(application)[0]) as api:
        sain,_=facture(api,100)
        historique,_=facture(api,50,valider=False)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE lignes_facture SET quantite=:v WHERE facture_id=:id'),{'v':valeur,'id':historique['id']})
            db.execute(text("UPDATE factures SET est_validee=true,numero=:n WHERE id=:id"),{'n':'HIST-FICT-'+uuid.uuid4().hex[:8],'id':historique['id']})
        avant=photographie(application)
        data=ok(preparation(api))
        assert len(data['documents'])==2 and data['nb_montants_inconnus']==1
        assert data['totaux'] is None and data['totaux_partie_connue']=={'ht':'100.00','tva':'20.00','ttc':'120.00'}
        r=next(r for r in data['documents'] if r['id']==historique['id'])
        assert r['ht'] is r['tva'] is r['ttc'] is None and r['diagnostics']
        assert 'À vérifier' in data['csv']
        assert photographie(application)==avant


def test_isolation_societes_exercice_absent_pas_creation_et_auth(application):
    api,_,_=client(application)
    autre,_,_=client(application)
    try:
        f,_=facture(api,100)
        facture(autre,500)
        avant=photographie(application)
        assert [r['id'] for r in ok(preparation(api))['documents']]==[f['id']]
        assert ok(preparation(autre))['totaux']['ht']=='500.00'
        assert preparation(api,1900).status_code==404
        assert api.get('/api/etats/ventes/preparation/2026',headers={'Authorization':''}).status_code==401
        assert photographie(application)==avant
    finally:
        api.close();autre.close()


def test_periode_decalee_utilise_dates_reelles_pas_annee_civile(application):
    with closing(client(application)[0]) as api:
        annee=date.today().year
        dedans,_=facture(api,100,date_piece=f'{annee}-01-15')
        dehors,_=facture(api,200,date_piece=f'{annee}-09-15')
        sid=ok(api.get('/api/societe/moi'))['id']
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE exercices_comptables SET date_debut=:d,date_fin=:f WHERE societe_id=:s AND annee=:a'),
                {'d':date(annee-1,7,1),'f':date(annee,6,30),'s':sid,'a':annee})
        avant=photographie(application)
        data=ok(preparation(api))
        assert (data['date_debut'],data['date_fin'])==(f'{annee-1}-07-01',f'{annee}-06-30')
        assert [r['id'] for r in data['documents']]==[dedans['id']]
        assert data['totaux']['ttc']=='120.00'
        assert photographie(application)==avant


def test_avoir_annee_courante_sur_facture_anterieure_a_sa_propre_date(application):
    with closing(client(application)[0]) as api:
        annee=date.today().year
        ok(api.post('/api/exercices',json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-12-31'}),201)
        ancien,_=facture(api,100,date_piece=f'{annee-1}-10-15')
        credit=ok(api.post('/api/avoirs',json={'facture_id':ancien['id'],'date':f'{annee}-01-15',
            'motif':'Correction fictive autre exercice','lignes':[{'facture_ligne_id':ancien['lignes'][0]['id'],'quantite':0.2}]}),201)
        avant=photographie(application)
        courant=ok(preparation(api))
        assert [(r['nature'],r['id']) for r in courant['documents']]==[('avoir',credit['id'])]
        assert courant['totaux']=={'ht':'-20.00','tva':'-4.00','ttc':'-24.00'}
        precedent=ok(preparation(api,annee-1))
        assert len(precedent['documents'])==1 and precedent['totaux']['ht']=='100.00'
        assert photographie(application)==avant


def test_avoir_historique_nan_signale_sans_effacer_facture_saine(application):
    with closing(client(application)[0]) as api:
        f,_=facture(api,100)
        credit=ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':f'{date.today().year}-02-15',
            'motif':'Historique synthétique','lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':0.2}]}),201)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text("UPDATE lignes_avoir SET prix_unitaire='NaN' WHERE avoir_id=:id"),{'id':credit['id']})
        avant=photographie(application)
        data=ok(preparation(api))
        assert len(data['documents'])==2 and data['nb_montants_inconnus']==1 and data['totaux'] is None
        assert data['totaux_partie_connue']['ttc']=='120.00'
        assert next(r for r in data['documents'] if r['nature']=='avoir')['ttc'] is None
        assert photographie(application)==avant


def test_reference_exercice_incoherente_visible_sans_reclassement(application):
    with closing(client(application)[0]) as api:
        # Constituer le legacy avant son état définitif ; aucune protection
        # d'une facture déjà validée n'est désactivée ou contournée.
        f,_=facture(api,100,valider=False)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE factures SET exercice=exercice-1,est_validee=true,numero=:n WHERE id=:id'),
                {'id':f['id'],'n':'HIST-FICT-'+uuid.uuid4().hex[:8]})
        avant=photographie(application)
        data=ok(preparation(api))
        assert len(data['documents'])==1 and data['totaux'] is None
        assert 'Référence d’exercice incohérente' in ' '.join(data['documents'][0]['diagnostics'])
        assert photographie(application)==avant


def test_lecture_autorisee_sans_droit_ecriture_et_aucune_route_mutation(application):
    with closing(client(application)[0]) as api:
        facture(api,100)
        email='lecture-ventes-'+uuid.uuid4().hex[:8]+'@example.com'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture ventes fictive','email':email,
            'mot_de_passe':'LectureVentes2026!','role':'lecture'}),201)
        token=ok(api.post('/api/auth/login',json={'email':email,'password':'LectureVentes2026!'}))['access_token']
        avant=photographie(application)
        path=f'/api/etats/ventes/preparation/{date.today().year}'
        headers={'Authorization':'Bearer '+token}
        assert ok(api.get(path,headers=headers))['totaux']['ht']=='100.00'
        assert api.post(path,headers=headers,json={}).status_code==405
        assert photographie(application)==avant
