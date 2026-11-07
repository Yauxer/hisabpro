"""Capital701 : arithmétique exacte, snapshots et exports sur bases jetables."""
from contextlib import closing
from copy import deepcopy
from decimal import Decimal, localcontext
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from test_balance_etic_annexes699_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,annexes,url,BASE,donnees_metier)


def body(v):
    data=annexes(v);data['tables'][3]['lignes'][0]['pourcentage']='100'
    return data


@pytest.mark.parametrize('cas',['connus','nominal_inconnu','capital_inconnu','pourcentage_inconnu',
    'source_absente','neant','zero_explicite','ecarts_centimes','grand_produit','111_sens_inverse'])
def test_701_calcul_exact_inconnus_et_aucune_reparation(cas):
    from services.balance_capital_controle_service import calculer
    d={'contenu':{'sources':{'n':[{'compte':'1111','credit':'10000.00','debit':'0.00'}]}}}
    demande=body({'id':1,'empreinte_sha256':'a'*64});r=demande['tables'][3]['lignes'][0]
    if cas=='nominal_inconnu':r['nominal']=None
    elif cas=='capital_inconnu':r['capital']=None
    elif cas=='pourcentage_inconnu':r['pourcentage']=None
    elif cas=='source_absente':d['contenu']['sources']['n']=None
    elif cas=='neant':demande['tables'][3].update(statut='neant_declare',lignes=[])
    elif cas=='zero_explicite':r.update(titres='0',nominal='0.00',capital='0.00',pourcentage='0')
    elif cas=='ecarts_centimes':r.update(capital='9999.99',pourcentage='99.99')
    elif cas=='grand_produit':r.update(titres='999999999999999999',nominal='9999999999999.99',capital='0.00')
    elif cas=='111_sens_inverse':d['contenu']['sources']['n']=[{'compte':'1111','credit':'0.00','debit':'20.00'}]
    avant=deepcopy((d,demande));c=calculer(d,demande);assert (d,demande)==avant
    json.dumps(c,allow_nan=False);assert c['pret_a_deposer'] is False
    if cas=='connus':assert Decimal(c['ecart_capital_balance'])==Decimal(c['ecart_pourcentages_100'])==Decimal(c['lignes'][0]['ecart_capital'])==0
    elif cas=='nominal_inconnu':assert c['lignes'][0]['capital_calcule'] is c['lignes'][0]['ecart_capital'] is None
    elif cas=='capital_inconnu':assert c['somme_capital_declare'] is c['ecart_capital_balance'] is c['lignes'][0]['ecart_capital'] is None
    elif cas=='pourcentage_inconnu':assert c['somme_pourcentages'] is c['ecart_pourcentages_100'] is None
    elif cas=='source_absente':assert c['capital_balance_111'] is c['ecart_capital_balance'] is None and not c['source_n_disponible']
    elif cas=='neant':assert not c['lignes'] and c['somme_capital_declare'] is c['somme_pourcentages'] is None
    elif cas=='zero_explicite':assert Decimal(c['somme_capital_declare'])==0 and Decimal(c['ecart_pourcentages_100'])==-100
    elif cas=='ecarts_centimes':assert all(Decimal(v)==Decimal('-0.01') for v in (c['ecart_capital_balance'],c['ecart_pourcentages_100'],c['lignes'][0]['ecart_capital']))
    elif cas=='grand_produit':
        with localcontext() as ctx:
            ctx.prec=80;assert Decimal(c['lignes'][0]['capital_calcule'])==Decimal(r['titres'])*Decimal(r['nominal'])
    elif cas=='111_sens_inverse':assert Decimal(c['capital_balance_111'])==-20 and Decimal(c['ecart_capital_balance'])==10020


def test_701_snapshot_fige_rejeu_sans_recalcul_et_ancienne_version(application,monkeypatch):
    from services import balance_capital_controle_service as moteur
    from services.balance_etic_annexes_service import presentation,conserver
    from routers.etats import BalanceEticAnnexesIn
    with closing(client(application)[0]) as api:
        v=creer(api);assert 'controle_capital' not in ok(api.get(url(v)))
        data=body(v);before=donnees_metier(application);r=ok(api.post(url(v),json=data),201)
        vue=ok(api.get(url(r)));c=vue['controle_capital']
        assert c==r['contenu']['annexes_etic_documentaires']['controle_capital']
        assert Decimal(c['somme_capital_declare'])==Decimal(c['capital_balance_111'])==10000
        assert Decimal(c['ecart_capital_balance'])==Decimal(c['ecart_pourcentages_100'])==0
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        after=donnees_metier(application);assert all(after[k]==val for k,val in before.items() if k!='liasse_balances_preparation')
        old=deepcopy(r);old['contenu']['annexes_etic_documentaires'].pop('controle_capital')
        assert 'controle_capital' not in presentation(old)
        def interdit(*a,**kw):raise AssertionError('Un ancien contrôle ou un rejeu ne doit pas être recalculé')
        monkeypatch.setattr(moteur,'calculer',interdit)
        assert presentation(r)['controle_capital']==c
        user=ok(api.get('/api/auth/me'))
        with Session(application['engine']) as db:
            assert conserver(db,user,v['id'],BalanceEticAnnexesIn.model_validate(data))==r
        # Une déclaration incohérente reste affichée, sans changer le snapshot précédent.
        monkeypatch.undo()
        d=body(r);d['tables'][3]['lignes'][0].update(capital='9999.99',pourcentage='99.99')
        r2=ok(api.post(url(r),json=d),201);c2=ok(api.get(url(r2)))['controle_capital']
        assert Decimal(c2['ecart_capital_balance'])==Decimal(c2['ecart_pourcentages_100'])==Decimal('-0.01')
        assert ok(api.get(url(r)))['controle_capital']==c


def test_701_exports_controles_et_grands_produits_exacts(application):
    with closing(client(application)[0]) as api:
        v=creer(api);data=body(v);data['tables'][3]['lignes'][0].update(titres='999999999999999999',nominal='9999999999999.99',capital='0.00')
        v=ok(api.post(url(v),json=data),201);c=ok(api.get(url(v)))['controle_capital'];avant=donnees_metier(application)
        x=api.get(BASE+f'/{v["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));ws=wb['Contrôles capital'];rows=list(ws.values)
        row=next(r for r in rows if r[0] and 'Produit titres' in r[0]);assert row[1]==c['lignes'][0]['capital_calcule']
        cell=next(cell for row in ws for cell in row if cell.value==c['lignes'][0]['capital_calcule']);assert cell.data_type=='s'
        pdf=api.get(BASE+f'/{v["id"]}/pdf');assert pdf.status_code==200
        t='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf.content)).pages)
        assert c['lignes'][0]['capital_calcule'] in t and 'Contrôles arithmétiques du capital déclaré' in t
        z=api.get(BASE+f'/{v["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert json.loads(zip.read('annexes_etic_documentaires.json'))['controle_capital']==c
            assert json.loads(zip.read('preparation.json'))==v
        assert donnees_metier(application)==avant
