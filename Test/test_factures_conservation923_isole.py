"""Conservation réelle du PDF, PostgreSQL natif sous LOGIN limité, jamais base utilisateur."""
from pathlib import Path
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4
import hashlib,json
import httpx,pytest
from pypdf import PdfReader
from sqlalchemy import text,create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from test_balance_documents691_isole import (
 application as application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,client,ok)
from test_avances_salaries_isole import appliquer
from recette_restauration_consolidee_084 import empreintes_tables
from postgres_isole import verifier_cible_isolee
from test_logo_societe import image_data

R=Path(__file__).resolve().parents[1]
def path(f):return f'/api/factures/{f["id"]}/copie-conservee'
def demande(motif='Conservation FICTIVE923 <copie> & contrôle'):return {'motif':motif,'conservation_confirmee':True}

def creer_facture(api,*,valider=True,type='vente',proforma=False):
 t=ok(api.post('/api/tiers',json={'nom':'Tiers copie FICTIF923 '+uuid4().hex[:6],'type':'client' if type=='vente' else 'fournisseur'}),201)
 f=ok(api.post('/api/factures',json={'type':type,'date':'2026-01-20','tiers':t['nom'],'tiers_id':t['id'],'reference':'PIECE-FICTIVE923','est_proforma':proforma,'lignes':[{'description':'Prestation <fictive> &923','quantite':1,'prix_unitaire':1000,'tva':20}]}),201)
 if valider and not proforma:ok(api.post(f'/api/factures/{f["id"]}/valider'))
 return f

@pytest.fixture(scope='module')
def application(application104):
 a=application104;avant=empreintes_tables(a['engine']);appliquer(a,'125_factures_copies_conservees.sql');appliquer(a,'125_factures_copies_conservees.sql');apres=empreintes_tables(a['engine']);assert all(apres[k]==v for k,v in avant.items());yield a

def comptabilite(app,sid):
 with app['engine'].connect() as db:
  result={t:list(db.scalars(text(f'SELECT row_to_json(t)::text FROM {t} t WHERE societe_id=:s ORDER BY id'),{'s':sid})) for t in ['factures','ecritures','reglements']}
  for t,parent,fk in [('lignes_facture','factures','facture_id'),('lignes_ecriture','ecritures','ecriture_id')]:result[t]=list(db.scalars(text(f'SELECT row_to_json(t)::text FROM {t} t JOIN {parent} p ON p.id=t.{fk} WHERE p.societe_id=:s ORDER BY t.id'),{'s':sid}))
  return result

def test_923_pdf_exact_logo_source_audit_rejeu_et_comptabilite(application):
 with closing(client(application)[0]) as api:
  ok(api.patch('/api/societe/moi',json={'logo_url':image_data()}));f=creer_facture(api);u=ok(api.get('/api/auth/me'));avant=comptabilite(application,u['societe_id']);assert ok(api.get(path(f)))=={'copie':None,'disponible':True}
  a=ok(api.post(path(f),json=demande()),201);pdf=api.get(path(f)+'/pdf');assert pdf.status_code==200 and pdf.headers['cache-control']=='no-store' and pdf.headers['x-content-type-options']=='nosniff'
  assert hashlib.sha256(pdf.content).hexdigest()==a['pdf_sha256']==pdf.headers['x-document-sha256'];d=PdfReader(BytesIO(pdf.content));assert sum(len(p.images) for p in d.pages)==1 and '1200' in ''.join(''.join(p.extract_text() or '' for p in d.pages).split())
  assert a['auteur_id']==u['id'] and a['source']['facture_id']==f['id'] and not a['reutilise'];b=ok(api.post(path(f),json=demande('Autre motif FICTIF non substitué')),201);assert b=={**a,'reutilise':True}
  ok(api.patch('/api/societe/moi',json={'raison_sociale':'Identité courante changée FICTIF923','logo_url':None}));assert api.get(path(f)+'/pdf').content==pdf.content
  assert ok(api.get(path(f)))['copie']==a and comptabilite(application,u['societe_id'])==avant
  avant_tables=empreintes_tables(application['engine']);appliquer(application,'125_factures_copies_conservees.sql');assert empreintes_tables(application['engine'])==avant_tables
  (R/'.codex-tests/conservation923_chaine.json').write_text(json.dumps({'copie':a,'octets_identiques_apres_changement_societe':True,'logo_incorpore':True,'comptabilite_inchangee':True,'rejeu_sans_remplacement':True},ensure_ascii=False,indent=2,default=str),encoding='utf8')

@pytest.mark.parametrize('params',[{'valider':False},{'proforma':True},{'type':'achat'}])
def test_923_brouillon_proforma_achat_non_acceptes(application,params):
 with closing(client(application)[0]) as api:
  f=creer_facture(api,**params);assert api.post(path(f),json=demande()).status_code==409 and ok(api.get(path(f)))['copie'] is None and api.get(path(f)+'/pdf').status_code==404

def test_923_societes_lecture_et_revocation(application):
 with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
  f=creer_facture(a);ok(a.post(path(f),json=demande()),201);ua=ok(a.get('/api/auth/me'));ub=ok(b.get('/api/auth/me'))
  assert b.get(path(f)).status_code==404 and b.get(path(f)+'/pdf').status_code==404 and b.post(path(f),json=demande()).status_code==404
  ok(a.post(f'/api/societes/{ua["societe_id"]}/inviter',params={'email':ub['email'],'role':'lecture'}));token=ok(b.post(f'/api/societes/switcher/{ua["societe_id"]}'))['access_token'];b.headers['Authorization']='Bearer '+token
  assert b.get(path(f)).status_code==200 and b.get(path(f)+'/pdf').status_code==200 and b.post(path(f),json=demande()).status_code==403
  ok(a.patch(f'/api/utilisateurs/{ub["id"]}',json={'actif':False}));assert b.get(path(f)).status_code==403 and b.get(path(f)+'/pdf').status_code==403

def test_923_double_clic_concurrent_et_payload_non_substituable(application):
 with closing(client(application)[0]) as api:
  f=creer_facture(api)
  def creer(_):
   with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as c:return ok(c.post(path(f),json=demande()),201)
  with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(creer,range(2)))
  assert a['id']==b['id'] and a['pdf_sha256']==b['pdf_sha256'] and a['reutilise']!=b['reutilise']
  for body in [{'motif':' ' ,'conservation_confirmee':True},{'motif':'FICTIF','conservation_confirmee':1},{**demande(),'document_pdf':'faux'},{**demande(),'auteur_id':999}]:assert api.post(path(f),json=body).status_code==422

def test_923_gardes_sql_role_limite_et_aucune_substitution(application):
 with closing(client(application)[0]) as api:
  f=creer_facture(api);ok(api.post(path(f),json=demande()),201)
  runtime=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'))
  try:
   for engine in [application['engine'],runtime]:
    for commande in ['DELETE FROM factures_copies_conservees','UPDATE factures_copies_conservees SET motif=motif','TRUNCATE factures_copies_conservees']:
     with pytest.raises(DBAPIError) as err:
      with engine.begin() as db:db.execute(text(commande))
     assert err.value.orig.pgcode in {'23514','42501'}
    with pytest.raises(DBAPIError) as err:
     with engine.begin() as db:db.execute(text("INSERT INTO factures_copies_conservees(societe_id,facture_id,auteur_id,motif,document_pdf,pdf_sha256,source,source_sha256) SELECT societe_id,facture_id,auteur_id,'FICTIF',document_pdf,repeat('a',64),source,source_sha256 FROM factures_copies_conservees LIMIT 1"))
    assert err.value.orig.pgcode=='23514'
  finally:runtime.dispose()

def test_923_absence_migration_n_empeche_pas_pdf_habituel(application):
 with closing(client(application)[0]) as api:
  f=creer_facture(api);c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
  try:
   with application['engine'].begin() as db:db.execute(text('ALTER TABLE factures_copies_conservees RENAME TO factures_copies_conservees_test923'))
   vue=ok(api.get(path(f)));assert not vue['disponible'] and '125' in vue['message'];assert api.post(path(f),json=demande()).status_code==503 and api.get(f'/api/factures/{f["id"]}/pdf').status_code==200
  finally:
   with application['engine'].begin() as db:db.execute(text('ALTER TABLE factures_copies_conservees_test923 RENAME TO factures_copies_conservees'))
