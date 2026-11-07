"""Inventaire final du sous-parcours : vrai comptage et vraie écriture3111/6114."""
from decimal import Decimal
from sqlalchemy.orm import Session
from playwright.sync_api import expect
import models
from cahier_formulaires773_support import DATA,ok
from cahier_cycle775_support import identifiants,nouvelle_ecriture,valider_journal,stock
from cahier_suite777_support import core
D=Decimal

def inventaire(api,page,app,sid,articles,preuve):
 a=articles['M-01'];initial=core(app,sid);assert len(initial)==13
 page.goto(app['web_url']+'/inventaire');page.locator('input[type="date"]').fill('2025-12-31');page.get_by_placeholder('Référence inventaire',exact=True).fill('STOCK-FIN');row=page.locator('tbody tr').filter(has_text=a['designation']);row.locator('input[type="number"]').fill('60')
 with page.expect_response(lambda r:'/api/inventaire/simuler' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Vérifier',exact=True).click()
 ap=ok(r.value);assert ap['total_perte']==0 and ap['valeur_stock_compte']==6600
 with page.expect_response(lambda r:'/api/inventaire/valider' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Valider l’inventaire',exact=True).click()
 inv=ok(r.value);assert inv['total_valeur']==6600 and inv['total_perte']==0 and inv['nb_articles']==1 and inv['nb_regularises']==0
 assert core(app,sid)==initial;stock(app,a['id'],60,110)
 avant=identifiants(app,sid);page.get_by_role('button',name='Rapprochement comptable',exact=True).click()
 with page.expect_response(lambda r:'/api/inventaire/comptabiliser-stock' in r.url and r.request.method=='POST') as r:page.get_by_role('button',name='Générer l’écriture de stock',exact=True).click()
 result=ok(r.value);assert result['ecriture_id'] and not result['deja_rapproche'];nouvelle_ecriture(app,sid,avant,'STOCK-FIN',preuve);valider_journal(page,app,1)
 etat=ok(api.get('/api/inventaire/stock/cloture',params={'exercice':2025}));assert etat['stock_rapproche'] and etat['ecriture_stock_validee'];assert etat['valeur_physique_brute']==etat['valeur_comptable_brute']==6600 and etat['ecart_brut']==0
 page.goto(app['web_url']+'/inventaire');page.get_by_role('button',name='Rapprochement comptable',exact=True).click();expect(page.get_by_role('button',name='Générer l’écriture de stock',exact=True)).to_be_disabled();stable=core(app,sid)
 second=api.post('/api/inventaire/comptabiliser-stock',params={'exercice':2025});assert second.status_code==409 and 'déjà définitive' in second.json()['detail'];assert core(app,sid)==stable and stable[:13]==initial
 liasse=ok(api.get('/api/etats/liasse/2025'));etats=liasse['etats'];assert D(str(etats['cpc']['resultat_net']))==D(DATA['attendus']['marge_brute'])==D('22100');assert D(str(etats['bilan']['actif']['total']['net']))==D(str(etats['bilan']['passif']['total']))==D('44000') and etats['bilan']['equilibre']
 stock_bilan=next(l for l in etats['bilan']['actif']['circulant'] if l['code']=='31');assert stock_bilan['brut']==stock_bilan['net']==6600 and stock_bilan['amort_prov']==0
 with Session(app['engine']) as db:
  es=db.query(models.Ecriture).filter_by(societe_id=sid).all();assert len(es)==14 and all(e.est_validee for e in es);assert sum(len(e.lignes) for e in es)==33
  assert sum(D(str(l.debit)) for e in es for l in e.lignes)==sum(D(str(l.credit)) for e in es for l in e.lignes)==D('177000')
  assert db.query(models.MouvementStock).filter_by(societe_id=sid,article_id=a['id']).count()==5
 preuve['cas'].append({'id':'HP-STK-001','statut':'Réussi'});preuve['cas'].append({'id':'HP-ADM-013','statut':'Réussi','controle':'Création article773 +stock réel777 +comptabilisation finale3111/6114 viaformulaire inventaire779'})
 preuve['inventaire779']={'inventaire':inv['inventaire_id'],'ecriture_stock':result['ecriture_id'],'valeur_physique_comptable':6600,'stock':60,'cmup':110,'ecritures':14,'lignes':33,'debit_credit':'177000.00','bilan_provisoire':44000,'resultat_provisoire':22100,'anti_doublon':True,'prefixe_valide_inchange':True,'limite':'États du sous-parcours marchandises uniquement ;capital,immobilisation,services,provisions,fiscalité etautresopérations annuelles non rejoués.'}
