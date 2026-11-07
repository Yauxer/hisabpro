"""Cohabitation719 : cycle annuel connecté et préparations sans pollution du Journal."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from decimal import Decimal
import hashlib,json
from test_balance_raccords715_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,ok,creer,body,url,BASE)
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_annee_connectee_isole import lignes_comptables
from test_e2e_annee_ventilation_inter_exercices_isole import test_oracle_independant_ventilations_soldes_et_an as oracle_annuel
import test_e2e_annee_rapprochement_ventilation_isole as annuel
from postgres_isole import verifier_cible_isolee
ROOT=Path(__file__).resolve().parents[1]


def empreintes():
 paths=list((ROOT/'src').rglob('*'))+list((ROOT/'hisabpro-backend').glob('*.py'))+list((ROOT/'hisabpro-backend').glob('*.sql'))
 for d in ('services','routers'):paths+=list((ROOT/'hisabpro-backend'/d).rglob('*.py'))
 paths+=list((ROOT/'Test').glob('*.py'))
 return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def test_719_oracle_annuel_independant():oracle_annuel()


def test_719_cycle_annuel_et_preparation_independante_meme_societe(application,migration,tmp_path,monkeypatch):
 c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
 initiales=empreintes();original=annuel.scenario;preuve={'erreur':None,'cohabitation_verifiee':False,
   'source_cluster':str(c['directory']),'source_application':str(application['directory']),'role_sql':application['role_sql'],'schema':104}
 def scenario_avec_preparation(app,dest,controle_banque):
  def controle(phase,api,page,paiements,sid,appli):
   controle_banque(phase,api,page,paiements,sid,appli)
   if phase!='apres_paiements':return
   params={'date_debut':'2026-01-01','date_fin':'2026-12-31'}
   banque=ok(api.get('/api/rapprochement/5141/situation',params=params))
   assert Decimal(str(banque['solde_comptable_final']))==Decimal('1000')
   avant=donnees_metier(appli);lignes=lignes_comptables(appli,sid)
   v=creer(api);v=ok(api.post(url(v),json=body(v)),201)
   vue=ok(api.get(url(v)));assert vue['actuel']
   controls=vue['snapshot']['controle_raccords']['tableaux']
   assert controls['B2']['comptes'][0]['solde_source']=='11000.00' and controls['B2']['comptes'][0]['ecart']=='0.00'
   assert controls['B2bis']['comptes'][0]['solde_source']=='4500.00' and controls['B5']['comptes'][0]['solde_source']=='700.00'
   source_banque=next(r for r in v['contenu']['sources']['n'] if r['compte']=='5141')
   assert Decimal(source_banque['debit'])-Decimal(source_banque['credit'])==Decimal('4200')
   paquet=api.get(BASE+f'/{v["id"]}/zip');assert paquet.status_code==200
   with ZipFile(BytesIO(paquet.content)) as z:
    assert z.testzip() is None and json.loads(z.read('raccords_mouvements.json'))['snapshot']==vue['snapshot']
    m=json.loads(z.read('MANIFESTE_SHA256.json'))
    for n,p in m['fichiers'].items():assert len(z.read(n))==p['taille'] and hashlib.sha256(z.read(n)).hexdigest()==p['sha256']
   assert ok(api.get(BASE+f'/{v["id"]}'))==v
   apres=donnees_metier(appli);autorise={'liasse_balances_preparation'}
   assert set(avant)==set(apres) and all(apres[t]==h for t,h in avant.items() if t not in autorise)
   assert apres['liasse_balances_preparation']!=avant['liasse_balances_preparation']
   assert lignes_comptables(appli,sid)==lignes
   assert Decimal(str(ok(api.get('/api/rapprochement/5141/situation',params=params))['solde_comptable_final']))==Decimal('1000')
   preuve.update(cohabitation_verifiee=True,tables_metier_hors_preparation_inchangees=True,
      lignes_comptables_definitives_inchangees=True,banque_journal_2026='1000.00',banque_source_externe='4200.00',
      controles_source_externe={'B2':'11000.00','B2bis':'4500.00','B5':'700.00'},
      preparation_id=v['id'],preparation_version=v['version'],preparation_sha256=v['empreinte_sha256'],
      manifeste_exports_verifie=True,fec_et_balance_annuels_verifies_apres_callback=False)
  original(app,dest,controle)
 monkeypatch.setattr(annuel,'scenario',scenario_avec_preparation)
 try:
  annuel.test_annee_banque_1000_ventilations240_cloture_an_paiements120(application,migration,tmp_path)
  assert preuve['cohabitation_verifiee']
  preuve['fec_et_balance_annuels_verifies_apres_callback']=True
  assert initiales==empreintes();preuve['empreintes_sources_et_scripts']=initiales
  preuve['sources_et_scripts_figes']=True
 except BaseException as exc:preuve['erreur']=repr(exc);raise
 finally:(ROOT/'.codex-tests/cohabitation719_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
