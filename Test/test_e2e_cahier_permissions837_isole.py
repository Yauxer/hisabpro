"""NEG042–045 : droits réels, pièces privées, déconnexion et absence de mutation."""
from pathlib import Path
import hashlib,httpx,pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok
from cahier_suite777_support import core
from navigation823_support import navigations_completes823
from test_e2e_administration_isole import connexion,deconnexion,observer
from test_e2e_cahier_securite835_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

def ecriture837(api,reference):
 e=ok(api.post('/api/ecritures',json={'date':'2025-01-01','date_piece':'2025-01-01','journal':'BQ','reference':reference,'libelle':'Témoin privé fictif','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201)
 ok(api.post(f'/api/ecritures/{e["id"]}/valider'));return e

def facture837(api,nom):
 t=ok(api.post('/api/tiers',json={'nom':nom,'type':'client','compte_client':'3421'}),201)
 data={'type':'vente','date':'2025-04-01','tiers':nom,'tiers_id':t['id'],'lignes':[{'description':'Service fictif privé','quantite':1,'prix_unitaire':1000,'tva':20}]}
 return ok(api.post('/api/factures',json=data),201),data

@pytest.mark.parametrize('largeur',[1440,390])
def test_837_lecture_isolation_pieces_deconnexion(application,largeur,tmp_path,navigations_completes823):
 with laboratoire(application,largeur,tmp_path,'permissions837') as (api,page,sid,preuve):
  me=ok(api.get('/api/auth/me'));ecriture837(api,'TEMOIN-A-837');fa,payload=facture837(api,'Client A fictif837');initial=core(application,sid)
  with httpx.Client(base_url=application['api_url'],timeout=30) as b:
   email=f'admin-b837-{sid}@hisabpro-recette.example';r=b.post('/api/auth/register',json={'nom':'Propriétaire B fictif','email':email,'password':DATA['societe']['password_test'],'raison_sociale':'Société B fictive837'});assert r.status_code==200;b.headers['Authorization']='Bearer '+r.json()['access_token']
   s=DATA['societe'];sb=ok(b.patch('/api/societe/moi',json={k:s[k] for k in ['forme_juridique','ville','adresse','capital_social','devise','identifiant_fiscal','ice','rc','patente','exercice_debut','regime_fiscal','regime_tva','periodicite_tva']}))['id'];eb=ecriture837(b,'TEMOIN-B-837');fb,_=facture837(b,'Client B fictif837');initial_b=core(application,sb)
   fb={**fb,**ok(b.post(f'/api/factures/{fb["id"]}/valider'))};pdf=b.get(f'/api/factures/{fb["id"]}/pdf');assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
   contenu=(Path(__file__).resolve().parents[1]/'docs/recette/justificatifs/ACH-01.pdf').read_bytes();piece=ok(b.post(f'/api/attachments/ecriture/{eb["id"]}',files={'file':('ACH-01.pdf',contenu,'application/pdf')}));url=piece['url'];owner=b.get(url);assert owner.status_code==200 and owner.content==contenu
   fb=next(f for f in ok(b.get('/api/factures',params={'exercice':2025})) if f['id']==fb['id']);statuts={}
   for nom,r in [('facture_pdf',api.get(f'/api/factures/{fb["id"]}/pdf')),('facture_modification',api.patch(f'/api/factures/{fb["id"]}',json={'reference':'TENTATIVE-A-837'})),('piece',api.get(url))]:
    assert r.status_code in {403,404};statuts[nom]=r.status_code
   assert b.get(url).content==contenu and next(f for f in ok(b.get('/api/factures',params={'exercice':2025})) if f['id']==fb['id'])==fb
   lecteur=ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif837','email':f'lecteur837-{sid}@hisabpro-recette.example','mot_de_passe':s['password_test'],'role':'lecture'}),201)
   ctx=page.context.browser.new_context(viewport={'width':largeur,'height':1050});lp=ctx.new_page();lp.set_default_timeout(15000);erreurs,serveur=observer(lp,application['api_url'])
   try:
    connexion(lp,application['web_url'],lecteur['email'],s['password_test']);lp.goto(application['web_url']+'/cloture');lp.get_by_label('Exercice actif',exact=True).select_option('2025');token=lp.evaluate("localStorage.getItem('hisabpro_token')")
    with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token},timeout=30) as lecture:
     lp.goto(application['web_url']+'/factures');expect(lp.get_by_role('button',name='Nouvelle facture',exact=True)).to_be_disabled();expect(lp.get_by_text('Client A fictif837',exact=True).first).to_be_visible()
     lp.goto(application['web_url']+'/journal');expect(lp.get_by_text('TEMOIN-A-837',exact=True)).to_be_visible();expect(lp.get_by_role('button',name='Nouvelle écriture',exact=True)).to_be_disabled()
     lp.goto(application['web_url']+'/etic');expect(lp.get_by_role('button',name='Enregistrer',exact=True)).to_have_count(0)
     refus={}
     for nom,r in [('facture',lecture.post('/api/factures',json=payload)),('ecriture',lecture.post('/api/ecritures',json={'date':'2025-01-01','journal':'BQ','reference':'LECTURE-REFUS','libelle':'Refus lecture fictif','lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]})),('etic',lecture.put('/api/etats/etic/2025/A1',json={'contenu':{}}))]:
      assert r.status_code==403;refus[nom]=r.status_code
     assert lecture.get('/api/etats/etic/2025').status_code==200
    deconnexion(lp);expect(lp.get_by_role('button',name='Se connecter',exact=True)).to_be_visible();assert lp.evaluate("localStorage.getItem('hisabpro_token')") is None;lp.goto(application['web_url']+'/factures');expect(lp.get_by_role('button',name='Se connecter',exact=True)).to_be_visible();assert not erreurs and not serveur
   finally:ctx.close()
   with httpx.Client(base_url=application['api_url'],timeout=30) as anonyme:assert anonyme.get('/api/factures').status_code==401 and anonyme.get('/api/ecritures').status_code==401
   admins={}
   for nom,r in [('desactivation',api.patch(f'/api/utilisateurs/{me["id"]}',json={'actif':False})),('retrogradation',api.patch(f'/api/utilisateurs/{me["id"]}',json={'role':'lecture'})),('suppression',api.delete(f'/api/utilisateurs/{me["id"]}'))]:
    assert r.status_code==400;admins[nom]=r.status_code
   assert ok(api.get('/api/auth/me'))==me and core(application,sid)==initial and core(application,sb)==initial_b and len(ok(api.get('/api/factures',params={'exercice':2025})))==1
   preuve['permissions837']={'lecture_refus':refus,'isolation':statuts,'piece_proprietaire_200':True,'piece_sha256':hashlib.sha256(contenu).hexdigest(),'dernier_admin':admins,'deconnexion_locale_et_anonyme_401':True,'A_B_comptabilite_conservee':True,'facture_B_conservee':True,'jetons_et_secrets_exclus':True};preuve['cas'] += [{'id':f'HP-NEG-{n:03d}','statut':'Réussi'} for n in range(42,46)]
  page.goto(application['web_url']+'/journal');expect(page.get_by_text('TEMOIN-A-837',exact=True)).to_be_visible()
