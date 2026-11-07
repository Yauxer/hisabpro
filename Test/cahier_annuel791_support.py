"""Suite annuelle : vrais formulaires, mêmes montants indépendants que le cahier."""
from collections import defaultdict
from decimal import Decimal as D
from sqlalchemy.orm import Session
from playwright.sync_api import expect
import models
from cahier_formulaires773_support import DATA,ok,champ
from cahier_cycle775_support import identifiants,nouvelle_ecriture,valider_journal,stock,OPS
from cahier_suite777_support import core
from cahier_semestre789_support import manuelle,facture_service


def inventaire_annuel(api,page,app,sid,article,preuve):
 initial=core(app,sid);page.goto(app['web_url']+'/inventaire');page.locator('input[type="date"]').fill('2025-12-31');page.get_by_placeholder('Référence inventaire',exact=True).fill('STOCK-FIN');page.locator('tbody tr').filter(has_text=article['designation']).locator('input[type="number"]').fill('60')
 with page.expect_response(lambda r:'/api/inventaire/simuler' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Vérifier',exact=True).click()
 sim=ok(r.value);assert sim['total_perte']==0 and sim['valeur_stock_compte']==6600
 with page.expect_response(lambda r:'/api/inventaire/valider' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Valider l’inventaire',exact=True).click()
 inv=ok(r.value);assert inv['total_valeur']==6600 and inv['total_perte']==0 and inv['nb_regularises']==0 and core(app,sid)==initial
 avant=identifiants(app,sid);page.get_by_role('button',name='Rapprochement comptable',exact=True).click()
 with page.expect_response(lambda r:'/api/inventaire/comptabiliser-stock' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Générer l’écriture de stock',exact=True).click()
 ok(r.value);nouvelle_ecriture(app,sid,avant,'STOCK-FIN',preuve);valider_journal(page,app,1);stock(app,article['id'],60,110);preuve['cas'].append({'id':'HP-STK-001','statut':'Réussi'})


def dotation_annuelle(page,app,sid,immo,preuve):
 avant=identifiants(app,sid);page.goto(app['web_url']+'/immobilisations');page.locator('tbody tr').filter(has_text='Ordinateur de recette').first.click();table=page.locator('table').filter(has=page.get_by_role('columnheader',name='Prorata',exact=True)).last;ligne=table.locator('tbody tr').filter(has=page.get_by_role('cell',name='2025',exact=True));expect(ligne).to_have_count(1)
 with page.expect_response(lambda r:f'/api/immobilisations/{immo["id"]}/generer-ecriture?annee=2025' in r.url) as r:ligne.get_by_role('button',name='Générer',exact=True).click()
 assert D(str(ok(r.value)['dotation']))==D('4800');nouvelle_ecriture(app,sid,avant,'AMORT-2025',preuve);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-IMM-003','statut':'Réussi'})


def ajuster(api,page,app,sid,ref,type_,montant,compte,contrepartie,libelle,cas,preuve):
 avant=core(app,sid);page.goto(app['web_url']+'/cloture');page.get_by_role('button',name='Ajouter un ajustement',exact=True).click();page.get_by_label('Type d’ajustement',exact=True).select_option(type_);form=page.locator('form').filter(has=page.get_by_label('Type d’ajustement',exact=True));form.get_by_label('Montant HT / comptable (MAD)',exact=True).fill(str(montant));form.get_by_label('Libellé / justification',exact=True).fill(libelle);form.get_by_label('Compte de charge / dotation',exact=True).fill(compte)
 if type_ in ['provision_risque','depreciation_client']:form.get_by_label('Compte de contrepartie',exact=True).fill(contrepartie)
 else:expect(form.get_by_label('Compte de contrepartie',exact=True)).to_have_value(contrepartie)
 with page.expect_response(lambda r:'/api/cloture/ajustements/apercu?' in r.url and r.request.method=='POST') as r:form.get_by_role('button',name='Vérifier l’écriture',exact=True).click()
 ok(r.value);expect(form.get_by_role('button',name='Créer l’écriture',exact=True)).to_be_enabled()
 with page.expect_response(lambda r:'/api/cloture/ajustements?' in r.url and r.request.method=='POST') as r:form.get_by_role('button',name='Créer l’écriture',exact=True).click()
 a=ok(r.value);form.wait_for(state='hidden');nouvelle_ecriture(app,sid,identifiants(app,sid)-{a['ecriture_id']},ref,preuve);valider_journal(page,app,1);apres=core(app,sid);assert all(e in apres for e in avant)
 if type_ in ['cca','fnp']:
  assert a['contrepassation_id']
  with Session(app['engine']) as db:
   cp=db.get(models.Ecriture,a['contrepassation_id']);assert cp.exercice==2026 and str(cp.date)=='2026-01-01' and not cp.est_validee
   assert {l.compte:(D(str(l.debit)),D(str(l.credit))) for l in cp.lignes}=={l['compte']:(D(l['credit']),D(l['debit'])) for l in OPS[ref]['lignes']}
 else:assert not a['contrepassation_id']
 preuve.setdefault('ajustements791',[]).append({'reference':ref,'id':a['id'],'ecriture':a['ecriture_id'],'contrepassation2026':a['contrepassation_id']});preuve['cas'].append({'id':cas,'statut':'Réussi'})


def annuel(api,page,app,sid,tiers,articles,banque,immo,preuve,avant_is=None):
 initial=core(app,sid);assert len(initial)==len([o for o in DATA['operations'] if o['date']<='2025-06-30'])
 for ref in ['TVA-06-PAY','INT-PPRF','ASS-01']:manuelle(page,app,sid,ref,preuve)
 for ref,litteral,cas in [('REF-02','02','HP-FAC-009'),('REF-002','002','HP-FAC-010')]:
  controle=facture_service(api,page,app,sid,tiers['F-CONTROLE'],articles['S-ACH'],ref,200,'2025-12-02','2025-12-31',preuve,cas,reference_piece=litteral);assert controle['date_echeance']=='2025-12-31'
 refs=[f['reference'] for f in ok(api.get('/api/factures',params={'exercice':2025})) if f['tiers_id']==tiers['F-CONTROLE']['id']];assert sorted(refs)==['002','02']
 impayee=facture_service(api,page,app,sid,tiers['C-IMPAYE'],articles['S-VTE'],'VENTE-IMPAYEE',12000,'2025-12-10','2025-12-20',preuve,'HP-FAC-011');assert impayee['date_echeance']=='2025-12-20';avant=identifiants(app,sid);page.goto(app['web_url']+'/factures');page.locator('tbody tr').filter(has_text=impayee['numero']).get_by_title('Encaisser le client',exact=True).click();m=page.get_by_role('dialog');champ(m,'Montant *').fill('2000');champ(m,'Date *').fill('2025-12-12');champ(m,'Mode','select').select_option('cheque');champ(m,'Banque','select').select_option(banque['banque']);m.get_by_placeholder('N° chèque, virement...').fill('CHQ-REJET')
 with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as r:m.get_by_role('button',name='Enregistrer',exact=True).click()
 reg=ok(r.value,201);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'CHQ-REJET',preuve);valider_journal(page,app,1);preuve['cas'].append({'id':'HP-PAY-018','statut':'Réussi'})
 avant=identifiants(app,sid);page.goto(app['web_url']+'/effets');champ(page,'Statut','select').select_option('tous');page.locator('tbody tr').filter(has_text='CHQ-REJET').get_by_title('Déclarer impayé',exact=True).click();m=page.get_by_role('dialog');m.locator('input[type="date"]').fill('2025-12-15');m.get_by_placeholder('0.00',exact=True).fill('0')
 with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{reg["id"]}/transition') and r.request.method=='POST') as r:m.get_by_role('button',name="Déclarer l'impayé",exact=True).click()
 ok(r.value);m.wait_for(state='hidden');nouvelle_ecriture(app,sid,avant,'CHQ-REJET-INV',preuve);valider_journal(page,app,1);assert ok(api.get(f'/api/factures/{impayee["id"]}/reglements'))['solde_restant']==14400;preuve['cas'].append({'id':'HP-PAY-019','statut':'Réussi'})
 for ref in ['AMENDE','FRAIS-BQ']:manuelle(page,app,sid,ref,preuve)
 inventaire_annuel(api,page,app,sid,articles['M-01'],preuve);dotation_annuelle(page,app,sid,immo,preuve)
 for args in [('CCA-2025','cca',11000,'6134','3491','Assurance ASS-01,11 mois 2026','HP-CLO-001'),('FNP-2025','fnp',3000,'6125','4417','Service livré décembre, contrat FNP-01','HP-CLO-002'),('PROV-RISQUE','provision_risque',1500,'61955','1518','Litige REC-LIT01 probable, conditions fiscales non satisfaites','HP-CLO-003'),('DEPR-CLIENT','depreciation_client',2000,'61964','3942','Dépréciation VENTE-IMPAYEE selon REC-DEP01','HP-CLO-004')]:ajuster(api,page,app,sid,*args,preuve)
 if 'TVA-12' in OPS:manuelle(page,app,sid,'TVA-12',preuve)
 if avant_is is not None:avant_is()
 for ref in ['IS-2025','PPRF-IMP']:manuelle(page,app,sid,ref,preuve)
 refs=[o['reference'] for o in preuve['operations']];assert len(refs)==len(set(refs))==50 and set(refs)==set(OPS);assert [o['date'] for o in preuve['operations']]==sorted(o['date'] for o in preuve['operations'])
 attendu=defaultdict(lambda:D(0));reel=defaultdict(lambda:D(0))
 for o in DATA['operations']:
  for l in o['lignes']:attendu[l['compte']]+=D(l['debit'])-D(l['credit'])
 with Session(app['engine']) as db:
  es=db.query(models.Ecriture).filter_by(societe_id=sid,exercice=2025).all();assert len(es)==50 and all(e.est_validee for e in es);ls=[l for e in es for l in e.lignes];assert len(ls)==118
  for l in ls:reel[l.compte]+=D(str(l.debit))-D(str(l.credit))
  assert {k:v for k,v in reel.items() if v}=={k:v for k,v in attendu.items() if v};total=sum(D(str(l.debit)) for l in ls);assert total==sum(D(str(l.credit)) for l in ls)==sum(D(l['debit']) for o in DATA['operations'] for l in o['lignes'])
  cps=db.query(models.Ecriture).filter_by(societe_id=sid,exercice=2026).all();assert len(cps)==2 and all(not e.est_validee and e.reference.startswith('CP-INV-') for e in cps);assert sum(len(e.lignes) for e in cps)==4
  assert db.query(models.MouvementStock).filter_by(societe_id=sid,article_id=articles['M-01']['id']).count()==5
 apres=core(app,sid);assert all(e in apres for e in initial)
 etats=ok(api.get('/api/etats/liasse/2025'))['etats'];att=DATA['attendus'];valeurs={'banque':reel['5141'],'stock_valeur':reel['3111'],'total_actif_net':D(str(etats['bilan']['actif']['total']['net'])),'total_passif_net':D(str(etats['bilan']['passif']['total'])),'resultat_net':D(str(etats['cpc']['resultat_net'])),'caf':D(str(etats['esg']['caf']))}
 for k,v in valeurs.items():assert v==D(att[k]),(k,v,att[k])
 assert etats['bilan']['equilibre'];imm=next(l for l in etats['bilan']['actif']['immobilise'] if l['code']=='23');assert [D(str(imm[k])) for k in ['brut','amort_prov','net']]==list(map(D,['24000','4800','19200']))
 # Contrôles réels conservés, sans masquer les éventuels justificatifs manquants.
 cloture=ok(api.get('/api/cloture/etat',params={'exercice':2025}));preuve['controle_cloture791']=cloture
 preuve['annuel791']={'ecritures2025':50,'lignes2025':118,'debit_credit':str(total),'contrepassations2026_brouillon':2,'lignes2026':4,'resultats':{k:str(v) for k,v in valeurs.items()},'soldes':{k:str(v) for k,v in sorted(reel.items()) if v},'stock':60,'cmup':110,'originaux_semestre_inchanges':True,'limite':'États annuels et flux produits testés, pas clôture définitive, déclarations fiscales ni recette humaine ;contrôles réels non contournés.'}
 for c in DATA['cas_recette']:
  if c['id'] in ['HP-CPT-002','HP-FIS-001','HP-FIS-002','HP-FIS-020','HP-FIS-025','HP-FIS-026']:preuve['cas'].append({'id':c['id'],'statut':'Réussi'})
 page.goto(app['web_url']+'/cloture')
