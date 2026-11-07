"""Variante de cession du cahier, avec écart d'oracle source rendu explicite."""
from decimal import Decimal as D, ROUND_HALF_UP
import pytest
from playwright.sync_api import expect
from sqlalchemy.orm import Session
import models
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_cycle775_support import valider_journal
from cahier_suite777_support import core
from test_e2e_cahier_immobilisation785_isole import capital,acquisition,amortissement
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_787_cession_2026_cahier_prorata_independant_et_2025_immuable(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'cession787') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='F-IMMO');f=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],'compte_fournisseur':t['compte']}),201);b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,f,preuve);amortissement(api,page,application,sid,immo,preuve);avant=core(application,sid);bilan2025=ok(api.get('/api/etats/liasse/2025'))['etats'];ids={e[0] for e in avant}
  # Calcul indépendant de l'implémentation : convention déjà documentée 30/360 inclusive.
  dot=(D('24000')/5/360).quantize(D('0.01'),rounding=ROUND_HALF_UP);cumul=D('4800')+dot;vnc=D('24000')-cumul;gain=D('20000')-vnc
  assert (dot,cumul,vnc,gain)==tuple(map(D,['13.33','4813.33','19186.67','813.33']))
  page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2026');page.goto(application['web_url']+'/immobilisations');row=page.locator('tbody tr').filter(has_text='Ordinateur de recette').first;row.get_by_title('Cession / mise au rebut',exact=True).click();m=page.locator('[class*="modalOverlay"]').filter(has_text='Sortie — Ordinateur de recette')
  champ(m,'Date de sortie').fill('2026-01-01');champ(m,'Prix de cession HT').fill('20000');champ(m,'TVA cession (%)','select').select_option('20');m.get_by_label('Cession encaissée immédiatement',exact=True).check();champ(m,'Date d’encaissement').fill('2026-01-01');champ(m,'Compte trésorerie').fill('5141')
  with page.expect_response(lambda r:r.url.endswith(f'/api/immobilisations/{immo["id"]}/sortie') and r.request.method=='POST') as r:m.get_by_role('button',name='Comptabiliser la sortie',exact=True).click()
  resultat=ok(r.value);preuve['resultat_cession_brut']=resultat;m.wait_for(state='hidden')
  for k,v in {'cumul_amortissement':cumul,'vnc':vnc,'prix_cession_ht':D('20000'),'tva_cession':D('4000'),'ttc_cession':D('24000'),'resultat_cession':gain}.items():assert D(str(resultat[k]))==v,(k,resultat[k],v)
  with Session(application['engine']) as db:
   nouvelles=[e for e in db.query(models.Ecriture).filter_by(societe_id=sid) if e.id not in ids];assert len(nouvelles)==4
   reel={e.journal:{l.compte:(D(str(l.debit)),D(str(l.credit))) for l in e.lignes} for e in nouvelles};assert reel=={'AM':{'61935':(dot,D(0)),'28355':(D(0),dot)},'OD':{'28355':(cumul,D(0)),'6513':(vnc,D(0)),'2355':(D(0),D('24000'))},'VT':{'3481':(D('24000'),D(0)),'7513':(D(0),D('20000')),'4455':(D(0),D('4000'))},'BQ':{'5141':(D('24000'),D(0)),'3481':(D(0),D('24000'))}}
   assert all(str(e.date)=='2026-01-01' and not e.est_validee for e in nouvelles);assert all(sum(D(str(l.debit)) for l in e.lignes)==sum(D(str(l.credit)) for l in e.lignes) for e in nouvelles)
  valider_journal(page,application,4);apres=core(application,sid);assert all(e in apres for e in avant) and len(apres)==8;assert ok(api.get('/api/etats/liasse/2025'))['etats']==bilan2025
  # Les doublons sont refusés, sans aucune modification des écritures définitives.
  requete=r.value.request.post_data_json;refus=api.post(f'/api/immobilisations/{immo["id"]}/sortie',json=requete);assert refus.status_code in [400,409],refus.text;assert core(application,sid)==apres
  page.goto(application['web_url']+'/immobilisations');expect(page.locator('tbody tr').filter(has_text='Ordinateur de recette').first).to_contain_text('Cédé');page.reload();expect(page.locator('tbody tr').filter(has_text='Ordinateur de recette').first).to_contain_text('Cédé')
  with Session(application['engine']) as db:
   obj=db.get(models.Immobilisation,immo['id']);assert not obj.actif and str(obj.date_sortie)=='2026-01-01' and str(obj.date_encaissement_cession)=='2026-01-01'
  preuve['cession787']={'date':'2026-01-01','dotation2026':str(dot),'cumul':str(cumul),'vnc':str(vnc),'gain':str(gain),'banque':'24000.00','ecritures2026':4,'originaux2025_inchanges':True,'bilan2025_inchange':True,'doublon_refuse':refus.status_code,'ecart_source':{'vnc_source':'19200.00','gain_source':'800.00','cause':'Le cahier omet le jour de sortie 01/01/2026 inclus dans la convention du moteur existant. Aucun calcul produit modifié.'},'statut_fiche':'Partiel','limite':'Parcours technique réussi ; oracle initial du cahier divergent et qualification/régularisation TVA de cession non validée automatiquement.'}
  preuve['cas'].append({'id':'HP-IMM-004','statut':'Partiel'})
