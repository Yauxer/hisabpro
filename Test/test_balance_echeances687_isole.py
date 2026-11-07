"""Compléments de balances : vrais API et PostgreSQL nonce, aucune base utilisateur."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from datetime import date
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from test_ras_rapprochements681_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,
    application087,migration,client,ok,donnees_metier,catalogue_acl)

BASE = '/api/etats/liasse/balance/dossiers'


def creer(api):
    return ok(api.post(BASE,json={'exercice':date.today().year,'fichier_n':'balance-fictive687.csv',
        'lignes_n':[{'compte':'1111','credit':'6000'}, {'compte':'3421','debit':'8000'},
                    {'compte':'4411','credit':'3000'}, {'compte':'5141','debit':'1000'}]}),201)


def demande(dossier, **champs):
    ligne={'section':'B6','compte':'3421','plus_un_an':'2000.00','echues':'1000.00',
           'etat_organismes_publics':'0','entreprises_liees':'500','effets':'4000',
           'justification':'État clients fictif687 — références à vérifier',**champs}
    return {'empreinte_parent':dossier['empreinte_sha256'],'cle':str(uuid4()),'lignes':[ligne]}


def chemin(v):return BASE+f'/{v["id"]}/echeances'


def test_687_soldes_inverses_visibles_et_sources_historiques_absentes():
    from services.balance_echeances_service import presentation,normaliser
    from routers.etats import BalanceEcheanceLigneIn
    dossier={'contenu':{'sources':{'n':[{'compte':'3421','debit':'0.00','credit':'80.00'}]}}}
    r=presentation(dossier)['lignes'][0]
    assert r['total']=='-80.00' and not r['ventilable'] and r['reliquat'] is None
    with pytest.raises(ValueError,match='absent'):
        normaliser(dossier,[BalanceEcheanceLigneIn(section='B6',compte='3421',echues='80',justification='Source fictive')])
    ancien={'contenu':{'sources':{}}}
    assert presentation(ancien)['sources_disponibles'] is False
    with pytest.raises(ValueError,match='Sources détaillées absentes'):normaliser(ancien,[])


def test_687_centimes_exacts_et_analyses_ne_se_somment_pas():
    from services.balance_echeances_service import presentation,normaliser
    from routers.etats import BalanceEcheanceLigneIn
    d={'contenu':{'sources':{'n':[{'compte':'3421','debit':'1234567890123.45','credit':'0'}]}}}
    rows=normaliser(d,[BalanceEcheanceLigneIn(section='B6',compte='3421',plus_un_an='1234567890123.44',echues='0.01',
        devises='1234567890123.45',effets='1234567890123.45',justification='Deux analyses de la même créance fictive')])
    d['contenu']['echeances_documentaires']={'lignes':rows}
    r=presentation(d)['lignes'][0]
    assert r['reliquat']=='0.00' and r['qualifie']=='1234567890123.45' and r['moins_un_an'] is None


def test_687_partiel_version_rejeu_et_sources_comptables_preservees(application):
    with closing(client(application)[0]) as api:
        v=creer(api);avant=donnees_metier(application);acl=catalogue_acl(application['engine'])
        body=demande(v)
        r=ok(api.post(chemin(v),json=body),201)
        assert r['version']==2 and r['id']!=v['id'] and r['empreinte_sha256']!=v['empreinte_sha256']
        assert r['contenu']['preparation']==v['contenu']['preparation']
        assert r['contenu']['sources']==v['contenu']['sources']
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        vue=ok(api.get(chemin(r)));a,b=vue['lignes']
        assert a['compte']=='3421' and a['reliquat']=='5000.00' and a['qualifie']=='3000.00'
        assert a['moins_un_an'] is None and a['devises'] is None and a['etat_organismes_publics']=='0.00'
        assert b['compte']=='4411' and b['reliquat']=='3000.00' and b['echues'] is None
        assert vue['parent']=={'id':v['id'],'version':1,'empreinte_sha256':v['empreinte_sha256']}
        assert ok(api.post(chemin(v),json=body),201)==r
        body['lignes'][0]['echues']='2000'
        assert api.post(chemin(v),json=body).status_code==409
        apres=donnees_metier(application)
        assert all(apres[k]==value for k,value in avant.items() if k!='liasse_balances_preparation')
        assert catalogue_acl(application['engine'])==acl


@pytest.mark.parametrize('field,value',[
    ('echues','NaN'),('echues','Infinity'),('echues','-Infinity'),('echues','-1'),
    ('echues','0.001'),('echues',True),('echues',{}),('echues','7000'),
    ('devises','8000.01'),('justification',' '),('compte','5141'),('section','B7')])
def test_687_entree_invalide_sans_version_creee(application,field,value):
    with closing(client(application)[0]) as api:
        v=creer(api);body=demande(v,**{field:value})
        assert api.post(chemin(v),json=body).status_code==422
        rows=ok(api.get(BASE,params={'exercice':date.today().year}))
        assert [r['id'] for r in rows]==[v['id']]


def test_687_dettes_analyses_recouvrantes_et_suppression_dans_nouvelle_version(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=demande(v)
        body['lignes']=[{'section':'B7','compte':'4411','plus_un_an':'1000','moins_un_an':'1000','echues':'1000',
                        'devises':'3000','entreprises_liees':'3000','justification':'Même dette : devise et entreprise liée, sources fictives687'}]
        v2=ok(api.post(chemin(v),json=body),201)
        assert ok(api.get(chemin(v2)))['lignes'][1]['reliquat']=='0.00'
        body=demande(v2);body['lignes']=[{'section':'B7','compte':'4411','justification':'Classement à revoir : aucune échéance présumée'}]
        v3=ok(api.post(chemin(v2),json=body),201)
        assert v3['version']==3 and ok(api.get(chemin(v3)))['lignes'][1]['echues'] is None
        assert ok(api.get(chemin(v2)))['lignes'][1]['echues']=='1000.00'


def test_687_rejets_doublon_empreinte_devise_lecture_et_societe(application):
    admin,email,password=client(application)
    with closing(admin),closing(client(application)[0]) as autre:
        v=creer(admin);body=demande(v)
        body['lignes']*=2;assert admin.post(chemin(v),json=body).status_code==422
        body=demande(v);body['empreinte_parent']='0'*64
        assert admin.post(chemin(v),json=body).status_code==409
        assert autre.get(chemin(v)).status_code==404
        assert autre.post(chemin(v),json=demande(v)).status_code==404
        ok(admin.patch('/api/societe/moi',json={'devise':'EUR'}))
        assert admin.post(chemin(v),json=demande(v)).status_code==409
        ok(admin.patch('/api/societe/moi',json={'devise':'MAD'}))
        sid=ok(admin.get('/api/auth/me'))['societe_id'];ae=ok(autre.get('/api/auth/me'))['email']
        ok(admin.post(f'/api/societes/{sid}/inviter',params={'email':ae,'role':'lecture'}))
        token=ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        autre.headers['Authorization']='Bearer '+token
        assert autre.get(chemin(v)).status_code==200
        assert autre.post(chemin(v),json=demande(v)).status_code==403


def test_687_concurrence_versions_et_rejeu_atomique(application):
    api,email,password=client(application)
    with closing(api):
        v=creer(api);body=demande(v)
        def creer_version(b):
            import httpx
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as c:
                return ok(c.post(chemin(v),json=b),201)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a,b=list(pool.map(creer_version,[body,deepcopy(body)]))
        assert a==b and a['version']==2
        with ThreadPoolExecutor(max_workers=2) as pool:
            a,b=list(pool.map(creer_version,[demande(v),demande(v,echues='0')]))
        assert {a['version'],b['version']}=={3,4}


def test_687_exports_logo_texte_literal_et_immutabilite_sql(application):
    from test_logo_societe import image_data
    with closing(client(application)[0]) as api:
        v=creer(api);body=demande(v,justification='=HYPERLINK("faux") <preuve687> & source')
        r=ok(api.post(chemin(v),json=body),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG',(20,12))}))
        x=api.get(BASE+f'/{r["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));ws=wb['Échéances documentaires']
        rows=list(ws.values);assert rows[1][0:3]==('B6','3421',8000)
        assert rows[1][4]=='Indisponible' and rows[1][10:12]==(3000,5000)
        assert ws['M2'].data_type=='s' and ws['M2'].value==body['lignes'][0]['justification']
        with ZipFile(BytesIO(x.content)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
        p=api.get(BASE+f'/{r["id"]}/pdf');assert p.status_code==200
        pdf=PdfReader(BytesIO(p.content));texte=' '.join(t.extract_text() for t in pdf.pages)
        assert '<preuve687> & source' in texte and '5 000,00' in texte
        assert v['empreinte_sha256'] in texte and r['empreinte_sha256'] in texte
        assert any(page.images for page in pdf.pages)
        with application['engine'].connect() as db:
            for sql in ('UPDATE liasse_balances_preparation SET version=999 WHERE id=:v','DELETE FROM liasse_balances_preparation WHERE id=:v'):
                with pytest.raises(DBAPIError):db.execute(text(sql),{'v':r['id']})
                db.rollback()
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
