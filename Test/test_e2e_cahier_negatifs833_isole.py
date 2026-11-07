"""NEG001–008 : refus réels et absence de mutation sur copies isolées."""
import re
from sqlalchemy import text
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_administration_isole import observer
from test_e2e_cahier_avant_is823_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def comptes833(app):
 with app['engine'].connect() as db:return tuple(db.scalar(text('SELECT count(*) FROM '+t)) for t in ['societes','utilisateurs'])

def refus833(r,attendus):
 statut=r.status_code if hasattr(r,'status_code') else r.status;assert statut in attendus,(r.text if hasattr(r,'status_code') else r.text());return {'status':statut,'corps':r.json()}

@pytest.mark.parametrize('largeur',[1440,390])
def test_833_identite_exercices_et_saisies_invalides(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'negatifs833') as (api,page,sid,preuve):
  resultats={};preuve['negatifs833']=resultats;me=ok(api.get('/api/auth/me'));nb=comptes833(application);identite=ok(api.get('/api/societe/moi'));calendrier=ok(api.get('/api/exercices'));assert core(application,sid)==()
  ctx=page.context.browser.new_context(viewport={'width':largeur,'height':1050});gp=ctx.new_page();gp.set_default_timeout(15000);erreurs,serveur=observer(gp,application['api_url'])
  try:
   gp.goto(application['web_url']+'/login');gp.get_by_role('button',name='Créer un compte',exact=True).click();champ(gp,'Votre nom').fill('Copie Faible');champ(gp,'Raison sociale').fill('Copie négative fictive');champ(gp,'Email').fill(me['email']);pwd=champ(gp,'Mot de passe');assert pwd.get_attribute('minlength')=='8';pwd.fill(DATA['societe']['password_test'])
   with gp.expect_response(lambda r:r.url.endswith('/api/auth/register') and r.request.method=='POST') as r:gp.get_by_role('button',name='Créer mon compte',exact=True).click()
   resultats['HP-NEG-001']=refus833(r.value,{400});expect(gp.get_by_text('Email déjà utilisé',exact=True)).to_be_visible();assert comptes833(application)==nb
   champ(gp,'Email').fill(f'faible833-{sid}@hisabpro-recette.example');pwd.fill('court');assert not pwd.evaluate('e=>e.checkValidity()');resultats['HP-NEG-002']=refus833(api.post('/api/auth/register',json={'nom':'Copie Faible','email':f'faible833-{sid}@hisabpro-recette.example','password':'court','raison_sociale':'Copie Faible'}),{400});assert '8' in str(resultats['HP-NEG-002']['corps']) and comptes833(application)==nb and not erreurs and not serveur
  finally:ctx.close()
  page.goto(application['web_url']+'/parametres');champ(page,'ICE').fill('12345678901234')
  with page.expect_response(lambda r:r.url.endswith('/api/societe/moi') and r.request.method=='PATCH') as r:page.get_by_role('button',name='Enregistrer',exact=True).click()
  resultats['HP-NEG-003']=refus833(r.value,{400,422});expect(page.locator('[class*="cardHeader"]').filter(has_text='Informations de la société')).to_contain_text('15');assert ok(api.get('/api/societe/moi'))==identite
  page.goto(application['web_url']+'/cloture');page.get_by_role('button',name='Créer un exercice',exact=True).click();form=page.locator('form').filter(has=page.get_by_label('Année de clôture du nouvel exercice',exact=True))
  for annee,debut,fin,cas in [('2026','2025-07-01','2026-06-30','HP-NEG-004'),('2028','2027-01-01','2028-01-31','HP-NEG-005')]:
   form.get_by_label('Année de clôture du nouvel exercice',exact=True).fill(annee);form.get_by_label('Date de début du nouvel exercice',exact=True).fill(debut);form.get_by_label('Date de clôture du nouvel exercice',exact=True).fill(fin)
   with page.expect_response(lambda r:r.url.endswith('/api/exercices') and r.request.method=='POST') as r:form.get_by_role('button',name='Créer cet exercice',exact=True).click()
   resultats[cas]=refus833(r.value,{400,409});expect(page.get_by_role('alert').first).to_be_visible();assert ok(api.get('/api/exercices'))==calendrier
  chevauche=refus833(api.patch('/api/exercices/2026',json={'date_debut':'2025-07-01','date_fin':'2026-06-30'}),{409});assert 'chevauch' in str(chevauche['corps']).lower();resultats['HP-NEG-004']['controle_chevauchement']=chevauche;assert ok(api.get('/api/exercices'))==calendrier
  page.goto(application['web_url']+'/journal');page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog');champ(m,'Date comptable *').fill('2025-01-01');champ(m,'Journal *','select').select_option('BQ');champ(m,"Libellé de l'écriture *").fill('Refus fictif déséquilibre1MAD');champ(m,'Référence du justificatif').fill('NEG-006');rows=m.locator('tbody tr');rows.nth(0).get_by_placeholder('Ex: 6111',exact=True).fill('5141');rows.nth(0).locator('td[data-label="Débit (MAD)"] input').fill('100');rows.nth(1).get_by_placeholder('Ex: 6111',exact=True).fill('1111');rows.nth(1).locator('td[data-label="Crédit (MAD)"] input').fill('99');expect(m.get_by_role('button',name="Enregistrer l'écriture",exact=True)).to_be_disabled();expect(m.get_by_text(re.compile('^Écart :'))).to_be_visible()
  resultats['HP-NEG-006']=refus833(api.post('/api/ecritures',json={'date':'2025-01-01','journal':'BQ','reference':'NEG-006','libelle':'Écart1fictif','est_validee':True,'lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':99}]}),{422});assert core(application,sid)==()
  t=next(t for t in DATA['tiers'] if t['code']=='C-SERVICE');tiers=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':'client','compte_client':'3421'}),201);a=ok(api.post('/api/articles',json={'code':'NEG-SERVICE','designation':'Service fictif négatifs833','is_stockable':False,'prix_vente_ht':1000,'tva':20,'compte_vente':'7124'}),201)
  page.goto(application['web_url']+'/factures');page.get_by_role('button',name='Nouvelle facture',exact=True).click();m=page.get_by_role('dialog',name='Nouvelle facture',exact=True);champ(m,'Date *').fill('2025-04-01');m.get_by_placeholder('Rechercher un',exact=False).fill(tiers['nom']);m.get_by_text(tiers['nom'],exact=True).click();m.get_by_placeholder('Description ou article...').fill(a['designation']);m.locator('li').filter(has_text=a['designation']).click();ed=m.locator('.hp-invoice-line-editor');ed.locator('input[type=number]').nth(0).fill('1');ed.locator('input[type=number]').nth(1).fill('-10');m.get_by_role('button',name='Enregistrer en brouillon',exact=False).click();m.get_by_role('button',name='Enregistrer le brouillon',exact=True).click();expect(m.get_by_text('Ligne 1 : le prix unitaire ne peut pas être négatif.',exact=True)).to_be_visible();expect(m).to_be_visible()
  base={'type':'vente','date':'2025-04-01','tiers':tiers['nom'],'tiers_id':tiers['id']};resultats['HP-NEG-007']=refus833(api.post('/api/factures',json={**base,'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':-10,'tva':20}]}),{422});ed.locator('input[type=number]').nth(1).fill('1000');expect(ed.locator('select option[value="101"]')).to_have_count(0);resultats['HP-NEG-008']=refus833(api.post('/api/factures',json={**base,'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':1000,'tva':101}]}),{422})
  assert core(application,sid)==() and ok(api.get('/api/factures',params={'exercice':2025}))==[] and ok(api.get('/api/exercices'))==calendrier and ok(api.get('/api/societe/moi'))==identite and comptes833(application)==nb and len(resultats)==8
  preuve['absence_mutation833']={'ecritures':0,'factures':0,'identite_conservee':True,'calendrier_conserve':True,'aucune_societe_utilisateur_orphelin':True};preuve['cas'] += [{'id':c,'statut':'Réussi'} for c in resultats]
