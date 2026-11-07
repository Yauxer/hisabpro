"""Matériel du cahier : formulaires réels, oracle indépendant, base native nonce isolée."""
from decimal import Decimal as D
import pytest
import re
from playwright.sync_api import expect
from sqlalchemy.orm import Session
import models
from cahier_formulaires773_support import laboratoire, DATA, ok, champ
from cahier_cycle775_support import identifiants, nouvelle_ecriture, valider_journal, OPS
from cahier_suite777_support import core
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)


def capital(page,app,sid,preuve):
 page.goto(app['web_url']+'/journal');page.get_by_role('button',name='Nouvelle écriture',exact=True).click();m=page.get_by_role('dialog')
 for label,val in [('Date comptable *','2025-01-01'),('Référence du justificatif','CAP-01'),("Libellé de l'écriture *",'Apport associé Recette')]:champ(m,label).fill(val)
 champ(m,'Journal *','select').select_option('BQ');rows=m.locator('tbody tr')
 for i,compte,colonne in [(0,'5141','Débit (MAD)'),(1,'1111','Crédit (MAD)')]:
  rows.nth(i).get_by_placeholder('Ex: 6111',exact=True).fill(compte);rows.nth(i).locator(f'td[data-label="{colonne}"] input').fill('200000')
 m.get_by_label('Valider immédiatement',exact=False).uncheck()
 with page.expect_response(lambda r:r.url.endswith('/api/ecritures') and r.request.method=='POST') as r:m.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
 ok(r.value,201);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,set(),'CAP-01',preuve);valider_journal(page,app,1)


def acquisition(api,page,app,sid,fournisseur,preuve):
 avant=identifiants(app,sid);page.goto(app['web_url']+'/immobilisations');page.get_by_role('button',name='Nouvelle immobilisation',exact=True).click();m=page.locator('[class*="modalOverlay"]').first
 m.get_by_placeholder('Ex: Serveur Dell PowerEdge',exact=True).fill('Ordinateur de recette');champ(m,'Référence / n° série').fill('IMMO-01');champ(m,'Catégorie','select').select_option('Matériel informatique')
 m.get_by_placeholder('Rechercher ou saisir un nouveau fournisseur').fill(fournisseur['nom']);m.get_by_role('button').filter(has_text=fournisseur['nom']).click()
 for label,val in [('Date d’acquisition *','2025-01-01'),('Date de mise en service *','2025-01-01'),('Prix d’acquisition HT *','24000'),('Durée (années)','5'),('Valeur résiduelle','0')]:champ(m,label).fill(val)
 champ(m,'Méthode','select').select_option('lineaire');m.get_by_label('Acquisition déjà payée').check();champ(m,'Date de paiement').fill('2025-01-01');champ(m,'Compte de trésorerie','select').select_option('5141')
 m.get_by_role('button',name='Modifier les comptes',exact=True).click()
 for label,val in [('Immobilisation','2355'),('Amortissement','28355'),('Dotation','61935'),('TVA immobilisation','34551'),('Dette acquisition','4481')]:expect(m.locator('label').filter(has_text=re.compile('^'+re.escape(label)+'$')).locator('..').locator('select')).to_have_value(val)
 with page.expect_response(lambda r:r.url.endswith('/api/immobilisations') and r.request.method=='POST') as r:m.get_by_role('button',name='Créer',exact=True).click()
 immo=ok(r.value,201);m.wait_for(state='hidden');assert immo['reference']=='IMMO-01' and immo['fournisseur_tiers_id']==fournisseur['id'];assert [D(str(immo[k])) for k in ['valeur_brute','tva_recuperable','total_ttc']]==[D('24000'),D('4800'),D('28800')]
 ids=identifiants(app,sid)-avant;assert ids=={immo['ecriture_acquisition_id'],immo['ecriture_paiement_id']}
 for cle,reference in [('ecriture_acquisition_id','IMMO-ACQ'),('ecriture_paiement_id','IMMO-PAY')]:
  nouvelle_ecriture(app,sid,identifiants(app,sid)-{immo[cle]},reference,preuve)
  with Session(app['engine']) as db:
   e=db.get(models.Ecriture,immo[cle]);ligne=next(l for l in e.lignes if l.compte=='4481');assert ligne.tiers_id==fournisseur['id'] and ligne.compte_auxiliaire_snapshot==fournisseur['code_aux_fournisseur'];assert str(e.date_piece)=='2025-01-01' and e.reference
 valider_journal(page,app,2);preuve['cas'].extend([{'id':'HP-IMM-001','statut':'Réussi'},{'id':'HP-IMM-002','statut':'Réussi'}]);return immo


def amortissement(api,page,app,sid,immo,preuve):
 avant=core(app,sid);ids=identifiants(app,sid);page.goto(app['web_url']+'/immobilisations');row=page.locator('tbody tr').filter(has_text='Ordinateur de recette').first;row.click()
 table=page.locator('table').filter(has=page.get_by_role('columnheader',name='Prorata',exact=True)).last;ligne=table.locator('tbody tr').filter(has=page.get_by_role('cell',name='2025',exact=True));expect(ligne).to_have_count(1);assert ligne.locator('td').all_text_contents()[3:6]==['4.800,00 MAD','4.800,00 MAD','19.200,00 MAD']
 with page.expect_response(lambda r:f'/api/immobilisations/{immo["id"]}/generer-ecriture?annee=2025' in r.url) as r:ligne.get_by_role('button',name='Générer',exact=True).click()
 resultat=ok(r.value);assert D(str(resultat['dotation']))==D('4800');nouvelle_ecriture(app,sid,ids,'AMORT-2025',preuve);valider_journal(page,app,1)
 bilan=ok(api.get('/api/etats/liasse/2025'))['etats'];b=bilan['bilan'];imm=next(l for l in b['actif']['immobilise'] if l['code']=='23');assert [D(str(imm[k])) for k in ['brut','amort_prov','net']]==[D('24000'),D('4800'),D('19200')];detail=next(l for l in b['detail']['actif'] if l.get('numero')=='235');assert D(str(detail['valeurs'][0]))==D('24000');assert b['actif']['total']['net']==b['passif']['total']==195200 and bilan['cpc']['resultat_net']==-4800
 apres=core(app,sid);assert all(e in apres for e in avant) and len(apres)==4
 # Route normale forcée pour vérifier aussi le verrou serveur, sans contourner l'interface.
 r=api.post(f'/api/immobilisations/{immo["id"]}/generer-ecriture',params={'annee':2025});assert r.status_code==409,r.text;assert core(app,sid)==apres
 page.goto(app['web_url']+'/immobilisations')
 with page.expect_response(lambda r:'/api/immobilisations/generer-dotations-annee?annee=2025' in r.url) as r:page.get_by_role('button',name='Dotations 2025',exact=True).click()
 batch=ok(r.value);assert batch['nb_generees']==0 and batch['nb_ignorees']==1 and batch['total_dotation']==0;assert core(app,sid)==apres
 page.reload();row.wait_for();expect(page.get_by_text(re.compile(r'Valeurs théoriques au \d{2}/\d{2}/\d{4}'))).to_be_visible()
 # Le registre est à aujourd'hui, le plan et le bilan2025 sont au31/12/2025.
 courant=next(i for i in ok(api.get('/api/immobilisations')) if i['id']==immo['id'])
 fmt=lambda v:format(D(str(v)),',.2f').replace(',','X').replace('.',',').replace('X','.')
 assert '24.000,00 MAD' in row.inner_text() and fmt(courant['vnc_actuelle'])+' MAD' in row.inner_text()
 preuve['registre_date_du_jour']={'cumul':str(courant['cumul_amortissement']),'net':str(courant['vnc_actuelle']),'date_explicitement_affichee':True}
 with Session(app['engine']) as db:
  es=db.query(models.Ecriture).filter_by(societe_id=sid).all();assert len(es)==4 and all(e.est_validee for e in es);ls=[l for e in es for l in e.lignes];assert len(ls)==9 and sum(D(str(l.debit)) for l in ls)==sum(D(str(l.credit)) for l in ls)==D('262400');assert sum(D(str(l.debit))-D(str(l.credit)) for l in ls if l.compte=='4481')==0
 preuve['cas'].append({'id':'HP-IMM-003','statut':'Réussi'});preuve['immobilisation785']={'ecritures':4,'lignes':9,'debit_credit':'262400.00','brut':'24000.00','amortissement':'4800.00','net':'19200.00','bilan':'195200.00','resultat':'-4800.00','anti_double_409':True,'tiers_auxiliaire_4481':True,'detail_bilan':detail,'limite':'Sous-parcours capital et immobilisation dans une nouvelle société ; pas le scénario annuel complet.'}


@pytest.mark.parametrize('largeur',[1440,390])
def test_785_ordinateur_cahier_acquisition_paiement_amortissement_bilan(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'immobilisation785') as (api,page,sid,preuve):
  t=next(t for t in DATA['tiers'] if t['code']=='F-IMMO');f=ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],'compte_fournisseur':t['compte']}),201)
  b=DATA['banque'];ok(api.post('/api/banques',json={'banque':b['banque'],'rib':b['rib'],'compte_comptable':'5141','devise':'MAD'}),201)
  preuve['preconditions']+=' Fournisseur F-IMMO et banque préparés par API, formulaires déjà vérifiés 773/771.'
  capital(page,application,sid,preuve);immo=acquisition(api,page,application,sid,f,preuve);amortissement(api,page,application,sid,immo,preuve)
