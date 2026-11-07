"""Droits réels des commandes du registre : Edge, HTTP et PostgreSQL nonce."""
from pathlib import Path
from decimal import Decimal
import json,httpx,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from navigation823_support import navigations_completes823
from test_e2e_administration_isole import connexion,observer
from test_immobilisations_apercu927_isole import (
 application,application104,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration,preparer,demande,url,photo)

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
@pytest.mark.parametrize('role',['lecture','comptable','admin'])
def test_929_registre_et_reconciliation_respectent_role(application,largeur,role,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,f'droits929_{role}') as (api,parent,sid,preuve):
  i=preparer(api);ok(api.patch(f'/api/immobilisations/{i["id"]}',json={'designation':'Bien ACTIF FICTIF929'}))
  c=preparer(api);ok(api.patch(f'/api/immobilisations/{c["id"]}',json={'designation':'Bien CEDE FICTIF929'}));ok(api.post(url(c),json=demande()))
  h=ok(api.post('/api/immobilisations',params={'generer_ecriture':False},json={'designation':'Bien HISTORIQUE FICTIF929','categorie':'Matériel informatique','date_acquisition':'2025-01-01','date_mise_en_service':'2025-01-01','prix_acquisition_ht':24000,'duree_amort':5,'methode':'lineaire','valeur_residuelle':0,'compte_immo':'2355','compte_amort':'28355','compte_dotation':'61935'}),201)
  email=f'{role}929-{sid}@hisabpro-recette.example';password=DATA['societe']['password_test']
  ok(api.post('/api/utilisateurs',json={'nom':f'Compte FICTIF929 {role}','email':email,'mot_de_passe':password,'role':role}),201)
  ctx=parent.context.browser.new_context(viewport={'width':largeur,'height':1050});page=ctx.new_page();page.set_default_timeout(15000);errors,server=observer(page,application['api_url'])
  try:
   connexion(page,application['web_url'],email,password);page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026')
   avant=photo(application,sid);mutations=[]
   page.on('request',lambda r:mutations.append((r.method,r.url)) if '/api/immobilisations' in r.url and r.method not in ['GET','OPTIONS'] else None)
   page.goto(application['web_url']+'/immobilisations');actif=page.locator('tbody tr').filter(has_text='Bien ACTIF FICTIF929');expect(actif).to_have_count(1)
   ecrire=role!='lecture';admin=role=='admin'
   for b in [page.get_by_role('button',name='Nouvelle immobilisation',exact=True),page.get_by_role('button',name='Dotations 2026',exact=True)]:
    (expect(b).to_be_enabled if ecrire else expect(b).to_be_disabled)()
   for title,nb in [('Modifier',2),('Cession / mise au rebut',2),('Marquer l’acquisition payée',1),('Encaisser la cession',1),('Archiver',1)]:
    expect(page.locator(f'tbody button[title="{title}"]')).to_have_count(nb if ecrire else 0)
   actif.click();expect(page.get_by_text('Tableau d’amortissement — Bien ACTIF FICTIF929',exact=True)).to_be_visible()
   generer=page.get_by_role('button',name='Générer',exact=True)
   if ecrire:expect(generer.first).to_be_enabled()
   else:expect(generer).to_have_count(0)
   page.get_by_role('button',name='Réconciliation historique',exact=True).click();modal=page.locator('[class*="modalOverlay"]').filter(has_text='Réconciliation historique — 2026')
   expect(modal.get_by_text('Bien HISTORIQUE FICTIF929',exact=True).first).to_be_visible()
   for name in ['Reclassements sûrs','Reconstituer acquisitions','Corriger amortissements 2026']:
    expect(modal.get_by_role('button',name=name,exact=True)).to_have_count(1 if admin else 0)
   if not admin:
    expect(modal.get_by_role('status')).to_contain_text('administrateur')
    for control in modal.locator('input,select,textarea').all():expect(control).to_be_disabled()
   d=R/'docs/recette/preuves';d.mkdir(exist_ok=True);page.screenshot(path=str(d/f'929_{largeur}_{role}_diagnostic.png'))
   modal.get_by_role('button',name='Fermer',exact=True).click()
   if ecrire:
    page.get_by_role('button',name='Nouvelle immobilisation',exact=True).click();page.get_by_role('button',name='Annuler',exact=True).click()
    actif.get_by_title('Modifier',exact=True).click();page.get_by_role('button',name='Annuler',exact=True).click()
   assert not mutations,mutations
   token=page.evaluate("localStorage.getItem('hisabpro_token')")
   with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token},timeout=30) as membre:
    refus={}
    if not ecrire:
     appels={'creation':lambda:membre.post('/api/immobilisations',json={'designation':'INTERDIT929','date_acquisition':'2025-01-01','date_mise_en_service':'2025-01-01','prix_acquisition_ht':100,'duree_amort':5}),
      'modifier':lambda:membre.patch(f'/api/immobilisations/{i["id"]}',json={'designation':'INTERDIT929'}),'archiver':lambda:membre.delete(f'/api/immobilisations/{h["id"]}'),
      'payer':lambda:membre.post(f'/api/immobilisations/{i["id"]}/payer',json={'date_paiement':'2026-01-01','compte_reglement':'5141'}),
      'sortie':lambda:membre.post(url(i),json=demande()),'encaisser':lambda:membre.post(f'/api/immobilisations/{c["id"]}/encaisser-cession',json={'date_encaissement':'2026-01-01','compte_tresorerie':'5141'}),
      'dotation':lambda:membre.post(f'/api/immobilisations/{i["id"]}/generer-ecriture',params={'annee':2026}),
      'lot':lambda:membre.post('/api/immobilisations/generer-dotations-annee',params={'annee':2026})}
     for nom,appel in appels.items():r=appel();assert r.status_code==403,r.text;refus[nom]=403
     assert membre.post(url(i)+'/apercu',json=demande()).status_code==200
    if not admin:
     for action in ['reclasser','reconstituer-acquisitions','corriger-amortissements']:
      r=membre.post('/api/immobilisations/reconciliation-historique/'+action,json={'exercice':2026,'items':[]});assert r.status_code==403,r.text;refus[action]=403
    assert membre.get('/api/immobilisations/reconciliation-historique',params={'exercice':2026}).status_code==200
   assert photo(application,sid)==avant and not errors and not server,(errors,server)
   reprise=None
   if admin:
    page.get_by_role('button',name='Réconciliation historique',exact=True).click()
    compte=modal.get_by_placeholder('Compte d’ouverture à confirmer',exact=True);expect(compte).to_be_enabled();compte.fill('4481')
    modal.locator('tbody tr').filter(has=page.get_by_placeholder('Compte d’ouverture à confirmer',exact=True)).get_by_role('checkbox').check()
    page.on('dialog',lambda d:d.accept())
    with page.expect_response(lambda r:r.url.endswith('/reconstituer-acquisitions') and r.request.method=='POST') as rr:
     modal.get_by_role('button',name='Reconstituer acquisitions',exact=True).click()
    rep=ok(rr.value);assert rep['nb_ecritures']==1
    expect(modal.get_by_placeholder('Compte d’ouverture à confirmer',exact=True)).to_have_count(0)
    apres=photo(application,sid)
    for t in ['ecritures','lignes_ecriture']:assert all(x in apres[t] for x in avant[t])
    nouvelles=[json.loads(x) for x in apres['ecritures'] if x not in avant['ecritures']];assert len(nouvelles)==1
    e=nouvelles[0];assert e['reference']==f'RECON-OPEN-2026-{h["id"]}' and e['date']=='2026-01-01' and not e['est_validee']
    lignes=[json.loads(x) for x in apres['lignes_ecriture'] if json.loads(x)['ecriture_id']==e['id']]
    assert sorted((l['compte'],Decimal(str(l['debit'])),Decimal(str(l['credit']))) for l in lignes)==[('2355',Decimal(24000),Decimal(0)),('28355',Decimal(0),Decimal(4800)),('4481',Decimal(0),Decimal(19200))]
    assert len(mutations)==1 and mutations[0][0]=='POST',mutations
    reprise={'ecriture_id':e['id'],'reference':e['reference'],'contrepartie_confirmee':'4481','brut':'24000','amortissement_ouverture':'4800','vnc':'19200','brouillon':True,'originaux_conserves':True}
   preuve['droits929']={'role':role,'consultation_registre_plan_diagnostic':True,'commandes_selon_role':True,'refus_API':refus,'consultation_sans_mutation_metier_ni_sequence':True,'aucune_mutation_emise_par_UI_pendant_consultation':True,'reprise_admin_reellement_executee':reprise,'recette_humaine':'Non effectuée automatiquement'}
  finally:ctx.close()
