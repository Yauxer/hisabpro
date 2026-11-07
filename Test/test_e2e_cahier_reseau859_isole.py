"""SEC005/009 : vraie coupure du transport Journal, reprise et paiement sansF5."""
import re,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from test_e2e_administration_isole import ouvrir_navigation
from test_e2e_cahier_plafonds843_isole import facture843,valider843
from navigation823_support import navigations_completes823
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def naviguer859(page,path,section):
 ouvrir_navigation(page);l=page.locator(f'a[href="{path}"]')
 if not l.is_visible():page.get_by_role('button',name=section,exact=True).click()
 l.click();expect(page.get_by_role('main')).to_be_visible()

@pytest.mark.parametrize('largeur',[1440,390])
def test_859_reseau_erreur_reprise_et_paiement_refresh(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'reseau859') as (api,page,sid,preuve):
  b=DATA['banque'];banque=ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201);t=next(t for t in DATA['tiers'] if t['code']=='F-CONTROLE');t=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'fournisseur','compte_fournisseur':'4411'}),201);e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':'TEMOIN-859','libelle':'Témoin fictif reprise859','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201);ok(api.post(f'/api/ecritures/{e["id"]}/valider'));f=facture843(api,t,'achat','2025-12-02',200,'02');valider843(api);avant=core(application,sid);aborts=[];post=[];page.on('request',lambda r:post.append(r.url) if r.method=='POST' and r.url.endswith('/api/reglements') else None)
  pattern=re.compile(re.escape(application['api_url'])+r'/api/ecritures(?:\?.*)?$')
  def couper(route):aborts.append({'methode':route.request.method,'chemin':'/api/ecritures'});route.abort('failed')
  page.context.route(pattern,couper);page.goto(application['web_url']+'/journal');alerte=page.get_by_role('alert').filter(has=page.get_by_text('Connexion au serveur',exact=False));expect(alerte).to_be_visible();expect(alerte.get_by_role('button',name='Réessayer',exact=True)).to_be_visible();expect(page.get_by_role('button',name='Nouvelle écriture',exact=True)).to_have_count(0);assert aborts and core(application,sid)==avant and not post
  page.context.unroute(pattern,couper)
  with page.expect_response(lambda r:'/api/ecritures?' in r.url and r.request.method=='GET') as rr:alerte.get_by_role('button',name='Réessayer',exact=True).click()
  assert rr.value.status==200;expect(page.get_by_text('TEMOIN-859',exact=True)).to_be_visible();assert core(application,sid)==avant;origine=page.evaluate('performance.timeOrigin');preuve['reseau859']={'transport_coupe':aborts,'message_francais_visible':True,'aucune_action_financiere_pendant_coupure':True,'reprise_200':True,'journal_conserve':True,'limite':'Coupure ciblée du transportGET Journal,autres API et actifs locaux réels disponibles ;aucune réponse métier fabriquée.'}
  naviguer859(page,'/factures','Facturation');row=page.locator('tbody tr').filter(has_text=t['nom']);row.get_by_title('Payer le fournisseur',exact=True).click();m=page.get_by_role('dialog');champ(m,'Montant *').fill('120');champ(m,'Date *').fill('2025-12-03');champ(m,'Banque','select').select_option(b['banque']);m.get_by_placeholder('N° chèque, virement...').fill('PAY-859')
  with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as rr:m.get_by_role('button',name='Enregistrer',exact=True).click()
  ok(rr.value,201);m.wait_for(state='hidden');expect(row.get_by_text('Part. payée',exact=True)).to_be_visible();assert ok(api.get(f'/api/factures/{f["id"]}/reglements'))['solde_restant']==120
  naviguer859(page,'/journal','Comptabilité');expect(page.get_by_role('main')).to_contain_text('PAY-859');assert page.evaluate('performance.timeOrigin')==origine and len(post)==1;apres=core(application,sid);n=[e for e in apres if e[0] not in {e[0] for e in avant}];assert len(n)==1 and {(l[1],l[2],l[3]) for l in n[0][8]}=={('4411',120,0),('5141',0,120)} and all(e in apres for e in avant);preuve['refresh859']={'paiement':120,'solde_restant':120,'statut_partiel_visible':True,'reference_journal_visible':True,'POST_unique':1,'document_non_recharge':True,'originaux_conserves':True};preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in ['HP-SEC-005','HP-SEC-009']]
