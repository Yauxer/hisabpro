from contextlib import closing
from io import BytesIO
from copy import deepcopy
import httpx
from sqlalchemy import text
from pypdf import PdfReader
from openpyxl import load_workbook
from test_paie915_ir_source_isole import (
    application,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,source_annuelle,demande,S,F,I,gain)
from test_logo_societe import image_data
from test_paie901_ir_annuel_unitaire import demande as manuelle
from recette_restauration_consolidee_084 import empreintes_tables


def exporter(eq,ident,fmt):return eq['a'].get(f'{I}/{ident}/export/{fmt}')


def test_917_exports_prives_logos_provenance_audit_sans_recalcul(application,equipe):
    eq=equipe;eid,rid,source=source_annuelle(eq);r=ok(eq['a'].post(S,json=demande(source['id'])),201)
    for logo in [None,'PNG','JPEG']:
        if logo:ok(eq['a'].patch('/api/societe/moi',json={'logo_url':image_data(logo)}))
        else:assert not ok(eq['a'].get('/api/societe/moi'))['logo_url']
        avant=empreintes_tables(application['engine']);compta=comptabilite(application,eq['sid'])
        for fmt in ['pdf','xlsx']:
            a=exporter(eq,r['id'],fmt);assert a.status_code==200,a.text[:500] if a.status_code!=200 else ''
            assert a.headers['cache-control']=='no-store' and a.headers['pragma']=='no-cache' and a.headers['x-content-type-options']=='nosniff'
            assert a.headers['content-disposition']==f'attachment; filename="controle_ir_annuel_{r["id"]}.{fmt}"'
            if fmt=='pdf':
                p=PdfReader(BytesIO(a.content));t='\n'.join(x.extract_text() or '' for x in p.pages)
                assert all(v in t for v in ['83881.0200','83890.00','5967.0000',source['empreinte'],'2026-01-01','2026-12-01','Non déterminé'])
                assert sum(len(x.images) for x in p.pages)==(1 if logo else 0)
            else:
                w=load_workbook(BytesIO(a.content));assert w['Sources mensuelles'].max_row==13
                assert ('Logo société' in w.sheetnames)==bool(logo) and all(c.data_type!='f' for sh in w for row in sh for c in row)
                vals={x[0]:x[1] for x in w['IR annuel'].iter_rows(min_row=2,values_only=True)};assert vals['IR annuel arithmétique']=='5967.0000'
        apres=empreintes_tables(application['engine']);assert all(apres[t]==h for t,h in avant.items() if t not in {'personnel_evenements','audit_actions'})
        assert apres['personnel_evenements']['nombre']==avant['personnel_evenements']['nombre']+2 and comptabilite(application,eq['sid'])==compta
        assert ok(eq['a'].get(f'{I}/{r["id"]}'))['contenu']==r['contenu'] and ok(eq['a'].get(f'{F}/{source["id"]}'))['contenu']==source['contenu']
    inconnu=ok(eq['a'].post(S,json=demande(source['id'],personnes_charge=None)),201)
    w=load_workbook(BytesIO(exporter(eq,inconnu['id'],'xlsx').content))
    vals={x[0]:x[1] for x in w['IR annuel'].iter_rows(min_row=2,values_only=True)}
    assert vals['IR annuel arithmétique']=='À compléter' and vals['Personnes à charge déclarées']=='À compléter' and vals['IR avant réduction']=='7167.0000'
    gain(eq,eid,rid,montant='100.00',source_reference='APRES-SNAPSHOT-FICTIF917')
    assert eq['a'].post(S,json=demande(source['id'])).status_code==409
    assert exporter(eq,r['id'],'pdf').status_code==200 # Ancien document consultable, sans recalcul.


def test_917_societes_permissions_revocation_et_controle_manuel(application,equipe):
    eq=equipe;_,_,source=source_annuelle(eq);r=ok(eq['a'].post(S,json=demande(source['id'])),201)
    assert eq['l'].get(f'{I}/{r["id"]}/export/pdf').status_code==403
    assert httpx.get(application['api_url']+f'{I}/{r["id"]}/export/pdf').status_code==401
    with closing(client(application)[0]) as autre:
        u=ok(autre.get('/api/auth/me'))
        for cap in CAPS:grant(autre,u['id'],cap)
        activer(autre);assert autre.get(f'{I}/{r["id"]}/export/pdf').status_code==404
    role,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(role):
        for cap in CAPS:
            g=grant(eq['a'],u['id'],cap)
            if cap=='personnel.lire_remuneration':droit=g['id']
        assert role.get(f'{I}/{r["id"]}/export/xlsx').status_code==200
        ok(eq['a'].post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin export FICTIF917'}))
        assert role.get(f'{I}/{r["id"]}/export/xlsx').status_code==403
    ancien=ok(eq['a'].post(I,json=manuelle()),201);assert exporter(eq,ancien['id'],'pdf').status_code==409
    assert exporter(eq,r['id'],'csv').status_code==422
