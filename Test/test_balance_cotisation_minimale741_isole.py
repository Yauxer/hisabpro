"""CM externe2026 : oracles, API native, droits, versions et exports."""
from contextlib import closing
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_contexte_fiscal735_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier,source,
    creer as creer_base,b12_body,b12_url,image_data)


def url(v): return BASE+f'/{v["id"]}/cotisation-minimale'
def creer(api,b12=True): return creer_base(api,b12)
def body(v):
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
        {'code':'CM-N','statut':'documente','justification':'Qualification fictive741, régime et absence d’exonération explicitement justifiés',
         'lignes':[{'nature':'CM fictive2026','regime':'IS hors forfait non-résident','base_exclue':'0','base_reduite':'0',
             'exoneration_totale':'non','minimum_exonere':'non','reference_source':'NOTE-CM741, justificatifs fictifs revus'}]}]}
def controles(v): return v['contenu']['cotisation_minimale_documentaire']['controle_cm']


@pytest.mark.parametrize('cas',['normal','reduit','exclusions','exonere','minimum_exonere','sans_b12','incomplet','neant','vide','absent','technique','legacy119','ancien','futur','inverse','grand'])
def test_741_oracles_exactitude_sources_et_inconnus(cas):
    from services.balance_cotisation_minimale_service import calculer_controles
    d=source();d['exercice']=2026;q=body({'empreinte_sha256':'a'*64});r=q['tables'][0]['lignes'][0]
    d['contenu']['passage_fiscal_documentaire']={'cle':'b12-fictif','controle_passage_fiscal':{'montants':{'is_theorique_taux_declare':'1460.00'}}}
    if cas in ('reduit','exclusions'):
        d['contenu']['sources']['n'][0]['credit']='2000000';r['base_reduite']='1000000' if cas=='reduit' else '500000'
        if cas=='exclusions':r['base_exclue']='200000'
    elif cas=='exonere':r['exoneration_totale']='oui'
    elif cas=='minimum_exonere':r['minimum_exonere']='oui'
    elif cas=='sans_b12':d['contenu'].pop('passage_fiscal_documentaire')
    elif cas=='incomplet':r['base_reduite']=None
    elif cas in ('neant','vide'):q['tables'][0].update(statut='neant_declare' if cas=='neant' else 'a_completer',lignes=[])
    elif cas=='absent':d['contenu']['sources']['n']=None
    elif cas=='technique':d['contenu']['preparation']['etats']['cpc']['disponible']=False
    elif cas=='legacy119':d['contenu']['sources']['n']=[{'compte':'1191','debit':'0','credit':'6400'}]
    elif cas=='ancien':d['exercice']=2025
    elif cas=='futur':d['exercice']=2027
    elif cas=='inverse':d['contenu']['sources']['n'][0].update(debit='20000',credit='0')
    elif cas=='grand':d['contenu']['sources']['n'][0]['credit']='9999999999999.99'
    avant=deepcopy(d);c=calculer_controles(d,q);m=c['montants']
    assert d==avant and c['solde_final'] is c['css'] is c['credits'] is c['acomptes'] is None
    assert not any(c[k] for k in ('liquidation_confirmee','paiement_confirme','pret_a_deposer'))
    json.dumps(c,allow_nan=False)
    if cas in ('incomplet','neant','vide','absent','technique','legacy119','ancien','futur'):
        assert m['cm_exigible'] is m['impot_avant_imputations_propose'] is None
    else:
        assert m['cm_exigible']=={'reduit':'4000.00','exclusions':'4000.00','exonere':'0.00','minimum_exonere':'25.00','grand':'25000000000.00'}.get(cas,'3000.00')
        if cas=='sans_b12':assert m['is_theorique_b12'] is m['impot_avant_imputations_propose'] is None
        else:assert m['impot_avant_imputations_propose']=={'exonere':'1460.00','minimum_exonere':'1460.00'}.get(cas,m['cm_exigible'])
    if cas=='normal':
        assert m['base_comptable_brute']=='10000.00'
        assert next(x for x in c['lignes_sources'] if x['compte']=='7581')['retenu_base'] is False
    assert c['reference_juridique']['sha256']=='fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1'


def test_741_versions_rejeu_lecture_sans_recalcul(application,monkeypatch):
    from services import balance_cotisation_minimale_service as s
    from routers.etats import BalanceCotisationMinimaleIn
    with closing(client(application)[0]) as api:
        v=creer(api);avant=donnees_metier(application);b=body(v)
        assert ok(api.get(url(v)))['controle_cm'] is None
        r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
        assert controles(r)['montants']['cm_exigible']=='3000.00'
        assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
        def interdit(*a,**kw):raise AssertionError('Ancien calcul ne doit pas être recalculé')
        monkeypatch.setattr(s,'calculer_controles',interdit)
        with Session(application['engine']) as db:
            assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceCotisationMinimaleIn.model_validate(b))==r
        assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('champ,valeur',[
    ('base_exclue','NaN'),('base_exclue','Infinity'),('base_exclue',True),('base_reduite',False),
    ('base_exclue','-1'),('base_exclue','0.001'),('base_exclue','1e9999'),('base_exclue','10000000000000'),
    ('base_exclue','10001'),('base_reduite','10001'),('regime','IR'),('exoneration_totale','oui probablement'),
    ('minimum_exonere',True),('reference_source',''),('nature',''),('inconnu','0')])
def test_741_rejets_sans_mutation(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);b=body(v);b['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
        assert api.post(url(v),json=b).status_code==422 and donnees_metier(application)==avant


@pytest.mark.parametrize('cas',['omission','doublon','deux_lignes','solde_injecte','neant','incomplet','zero_sans_exoneration','base_reduite_apres_exclusion'])
def test_741_structures_et_parametres_inconnus(application,cas):
    with closing(client(application)[0]) as api:
        v=creer(api);b=body(v);t=b['tables'][0]
        if cas=='omission':b['tables']=[]
        elif cas=='doublon':b['tables']*=2
        elif cas=='deux_lignes':t['lignes']*=2
        elif cas=='solde_injecte':b['solde_final']='0'
        elif cas=='neant':t.update(statut='neant_declare',lignes=[])
        elif cas=='incomplet':t['lignes'][0]['exoneration_totale']=''
        elif cas=='zero_sans_exoneration':t['lignes'][0].update(base_exclue='10000',base_reduite='0')
        else:t['lignes'][0].update(base_exclue='5000',base_reduite='5000.01')
        avant=donnees_metier(application);rep=api.post(url(v),json=b)
        if cas in ('neant','incomplet','zero_sans_exoneration'):
            r=ok(rep,201);assert controles(r)['montants']['cm_exigible']==('3000.00' if cas=='zero_sans_exoneration' else None)
        else:assert rep.status_code==422 and donnees_metier(application)==avant


def test_741_b12_actualisation_explicite(application):
    with closing(client(application)[0]) as api:
        v=creer(api);b=body(v);b['tables'][0]['lignes'][0]['exoneration_totale']='oui'
        r=ok(api.post(url(v),json=b),201);ancien=deepcopy(controles(r))
        q=b12_body(r);q['tables'][0]['lignes'][0]['taux_is']='10'
        v2=ok(api.post(b12_url(r),json=q),201);vue=ok(api.get(url(v2)))
        assert vue['source_b12_modifiee'] and vue['controle_cm']==ancien
        v3=ok(api.post(url(v2),json=body(v2)),201)
        assert controles(v3)['montants']['is_theorique_b12']=='730.00'
        assert not ok(api.get(url(v3)))['source_b12_modifiee'] and controles(r)==ancien


def test_741_droits_societes_devise_hash_concurrence(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);b=body(v)
        assert autre.get(url(v)).status_code==autre.post(url(v),json=b).status_code==404
        assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        b['tables'][0]['lignes'][0]['base_reduite']='1';assert api.post(url(v),json=b).status_code==409
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200


def test_741_exports_logo_formules_sources_et_manifestes(application,tmp_path):
    with closing(client(application)[0]) as api:
        v=creer(api);b=body(v);b['tables'][0]['lignes'][0].update(reference_source='=NOTE741',nature='Source longue '+'justifiée '*100)
        r=ok(api.post(url(v),json=b),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        avant=donnees_metier(application);rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200,rep.text[:300] if rep.status_code!=200 else ''
        with ZipFile(BytesIO(rep.content)) as z:
            assert z.testzip() is None and json.loads(z.read('cotisation_minimale_documentaire.json'))['controle_cm']==controles(r)
            m=json.loads(z.read('MANIFESTE_SHA256.json'))
            assert set(z.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
            w=load_workbook(BytesIO(z.read('preparation.xlsx')));totaux=dict(list(w['Calcul CM'].values)[1:])
            assert totaux['CM proposée selon qualifications déclarées']==3000
            assert w['Qualification CM']['I2'].value=='=NOTE741' and w['Qualification CM']['I2'].data_type=='s'
            with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
            pdf=PdfReader(BytesIO(z.read('preparation.pdf')));texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert 'Cotisation minimale' in texte and '=NOTE741' in texte and '3 000,00' in texte
            assert any(p.images for p in pdf.pages)
            (tmp_path/'cm741.pdf').write_bytes(z.read('preparation.pdf'))
        assert donnees_metier(application)==avant
