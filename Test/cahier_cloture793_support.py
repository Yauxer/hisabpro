"""Fiscalité documentée du jeu fictif, clôture et ouverture : aucun chiffre inventé."""
from collections import defaultdict
from decimal import Decimal as D
from sqlalchemy.orm import Session
from playwright.sync_api import expect
import models
from cahier_formulaires773_support import DATA,ok
from cahier_cycle775_support import valider_journal
from cahier_suite777_support import core


def cloturer_cahier(api,page,app,sid,preuve):
 origine=[e for e in core(app,sid) if e[1].year==2025];assert len(origine)==50
 avant=ok(api.get('/api/fiscalite/is/2025'));assert not avant['comptabilisation_is']['coherente'] and D(str(avant['calcul']['resultat_comptable_avant_is']))==D('129830')
 page.goto(app['web_url']+'/cloture');expect(page.get_by_role('button',name="Clôturer l'exercice 2025",exact=True)).to_be_disabled();page.goto(app['web_url']+'/fiscalite-is')
 form=page.locator('form').filter(has=page.get_by_placeholder('Libellé du retraitement',exact=True))
 for compte,montant,libelle in [('61955','1500','Litige REC-LIT01 : provision non admise, hypothèse explicite du scénario'),('61964','2000','Dépréciation REC-DEP01 : non admise, hypothèse explicite du scénario')]:
  form.locator('select').nth(0).select_option('reintegration');form.locator('select').nth(1).select_option('provisions_non_deductibles');form.get_by_placeholder('Libellé du retraitement',exact=True).fill(libelle);form.get_by_placeholder('Compte (optionnel)',exact=True).fill(compte);form.get_by_placeholder('Montant MAD',exact=True).fill(montant)
  with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2025/retraitements') and r.request.method=='POST') as r:form.get_by_role('button',name='Ajouter',exact=True).click()
  retrait=ok(r.value);expect(page.get_by_text(libelle,exact=True)).to_be_visible()
 situation=ok(api.get('/api/fiscalite/is/2025'));calcul=situation['calcul'];assert D(str(calcul['reintegrations']))==D('4000') and D(str(calcul['benefice_fiscal_imposable']))==D('133830') and D(str(calcul['is_theorique']))==D('23420.25');preuve['cas'].append({'id':'HP-FIS-021','statut':'Réussi'})
 credit=page.locator('form').filter(has=page.get_by_placeholder('Montant retenu',exact=True));credit.locator('select').select_option('pprf');credit.get_by_placeholder('Montant retenu',exact=True).fill('200');credit.get_by_placeholder('Déjà imputé acomptes',exact=True).fill('0');credit.locator('input[type="date"]').fill('2025-11-30');credit.get_by_placeholder('Référence justificative',exact=True).fill('INT-PPRF')
 with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2025/credits') and r.request.method=='POST') as r:credit.get_by_role('button',name='Ajouter',exact=True).click()
 ok(r.value);expect(page.get_by_text('INT-PPRF',exact=True)).to_be_visible();situation=ok(api.get('/api/fiscalite/is/2025'));assert D(str(situation['liquidation']['solde_a_payer']))==D('23220.25');preuve['cas'].append({'id':'HP-FIS-022','statut':'Réussi'})
 cm=situation['cotisation_minimale'];assert D(str(cm['base_comptable_brute']))==D('170500') and D(str(cm['cm_calculee']))==D('426.25') and D(str(cm['cm_exigible']))==D('3000')
 cb=page.get_by_label('Exonération totale de cotisation minimale pour cet exercice',exact=True);cb.check();page.get_by_label("Justification de l'exonération CM",exact=True).fill("CGI article 144-I-C-1 ; constitution et exploitation 01/01/2025 ; hors concession de service public ; justificatif fictif REC-CM 01")
 section=page.locator('section').filter(has=cb)
 with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2025/parametres') and r.request.method=='PUT') as r:section.get_by_role('button',name='Enregistrer',exact=True).click()
 ok(r.value);situation=ok(api.get('/api/fiscalite/is/2025'));assert D(str(situation['cotisation_minimale']['cm_exigible']))==0;assert situation['acomptes']['reference']['non_applicable'];assert all(a['statut']=='non_applicable' and D(str(a['montant_verse']))==0 for a in situation['acomptes']['acomptes']);assert not situation['contribution_solidarite']['disponible'];expect(page.get_by_text('Non applicable',exact=True).first).to_be_visible();expect(page.get_by_text('Référence manquante',exact=True).first).to_be_visible();preuve['cas'].append({'id':'HP-FIS-023','statut':'Réussi'});preuve['cas'].append({'id':'HP-FIS-024','statut':'Partiel','limite':'Base/calcul/minimum etexonération du scénario testés ;variation nonexonérée observée avantparamétrage, pas surune copie dédiée.'})
 assert all(e in core(app,sid) for e in origine);page.reload();expect(page.get_by_label('Exonération totale de cotisation minimale pour cet exercice',exact=True)).to_be_checked()
 controle=ok(api.get('/api/cloture/etat',params={'exercice':2025}));assert controle['fiscalite_is']['coherente'] and controle['equilibre'] and controle['nb_dotations_manquantes']==controle['nb_ecritures_brouillon']==0 and controle['fec_controle']['conforme'];assert controle['stock_cloture']['stock_rapproche'] and controle['immobilisations_rapprochement']['rapproche'];preuve['controle_avant_cloture793']=controle
 page.goto(app['web_url']+'/cloture');bouton=page.get_by_role('button',name="Clôturer l'exercice 2025",exact=True);expect(bouton).to_be_enabled()
 with page.expect_response(lambda r:'/api/cloture/cloturer?exercice=2025' in r.url and r.request.method=='POST') as r:bouton.click()
 ferme=ok(r.value);assert D(str(ferme['resultat_net']))==D('106409.75') and ferme['a_nouveaux_sur']==2026;expect(page.get_by_text('Exercice 2025 clôturé définitivement',exact=False)).to_be_visible()
 attendu=defaultdict(lambda:D(0))
 for o in DATA['operations']:
  for l in o['lignes']:
   if l['compte'][0] in '12345':attendu[l['compte']]+=D(l['debit'])-D(l['credit'])
 attendu['1191']-=D(DATA['attendus']['resultat_net']);attendu={k:v for k,v in attendu.items() if v}
 with Session(app['engine']) as db:
  ex=db.query(models.ExerciceComptable).filter_by(societe_id=sid,annee=2025).one();assert ex.statut=='cloture' and all(p.statut=='fermee' for p in ex.periodes)
  trace=db.query(models.ClotureExercice).filter_by(societe_id=sid,exercice=2025).one();an=db.get(models.Ecriture,trace.ecriture_an_id);assert an.est_validee and an.exercice==2026 and an.journal==models.JournalEnum.AN;reel=defaultdict(lambda:D(0))
  for l in an.lignes:reel[l.compte]+=D(str(l.debit))-D(str(l.credit))
  assert dict(reel)==attendu;assert sum(D(str(l.debit)) for l in an.lignes)==sum(D(str(l.credit)) for l in an.lignes)==D('343810')
  resultat=defaultdict(lambda:D(0))
  for e in db.query(models.Ecriture).filter_by(societe_id=sid,exercice=2025):
   for l in e.lignes:
    if l.compte.startswith(('6','7','8')):resultat[l.compte]+=D(str(l.debit))-D(str(l.credit))
  assert all(v==0 for v in resultat.values());anid=an.id
 assert all(e in core(app,sid) for e in origine);interdit=api.post('/api/ecritures',json={'date':'2025-12-31','journal':'BQ','reference':'INTERDIT-CLOS793','libelle':'Tentative fictive refusée','lignes':[{'compte':'5141','debit':1},{'compte':'1111','credit':1}]});assert interdit.status_code==423,interdit.text;assert api.post('/api/cloture/cloturer',params={'exercice':2025}).status_code==400;preuve['cas'].append({'id':'HP-CLO-006','statut':'Réussi'})
 page.get_by_label('Exercice actif',exact=True).select_option('2026');region=page.get_by_role('region',name='Contrepassations d’ouverture',exact=True);expect(region).to_contain_text('2 liée(s)');expect(region).to_contain_text('2 à valider');valider_journal(page,app,2)
 page.goto(app['web_url']+'/cloture');expect(page.get_by_role('region',name='Contrepassations d’ouverture',exact=True)).to_contain_text('2 validée(s)')
 with Session(app['engine']) as db:
  cps=db.query(models.Ecriture).filter_by(societe_id=sid,exercice=2026).all();assert len(cps)==3 and all(e.est_validee for e in cps);assert {e.id for e in cps if e.journal==models.JournalEnum.AN}=={anid}
 assert all(e in core(app,sid) for e in origine);preuve['cas'].append({'id':'HP-CLO-007','statut':'Réussi'})
 page.get_by_label('Exercice actif',exact=True).select_option('2025');page.goto(app['web_url']+'/fiscalite-is');expect(page.get_by_role('button',name='Confirmer la liquidation',exact=True)).to_be_enabled();avant_confirmation=core(app,sid)
 with page.expect_response(lambda r:r.url.endswith('/api/fiscalite/is/2025/liquidation/confirmer') and r.request.method=='POST') as r:page.get_by_role('button',name='Confirmer la liquidation',exact=True).click()
 snapshot=ok(r.value);assert D(str(snapshot['solde_a_payer']))==D('23220.25') and D(str(snapshot['impot_du']))==D('23420.25');page.reload();expect(page.get_by_text('Photographie confirmée le',exact=False)).to_be_visible();assert page.get_by_role('button',name='Confirmer la liquidation',exact=True).count()==0 and core(app,sid)==avant_confirmation
 fige=ok(api.get('/api/fiscalite/is/2025'));assert fige['liquidation']['confirmee'] and D(str(fige['liquidation']['snapshot']['solde_a_payer']))==D('23220.25');assert api.post('/api/fiscalite/is/2025/liquidation/confirmer').status_code==409;assert api.post('/api/fiscalite/is/2025/credits',json={'type':'pprf','montant':1,'reference':'INTERDIT-FIGE793'}).status_code==409;assert core(app,sid)==avant_confirmation;preuve['cas'].append({'id':'HP-FIS-027','statut':'Réussi'})
 preuve['cloture793']={'resultat_net':'106409.75','reintegrations':'4000.00','benefice_fiscal':'133830.00','is':'23420.25','credit':'200.00','solde':'23220.25','an2026_id':anid,'total_an':'343810.00','soldes_an':{k:str(v) for k,v in sorted(attendu.items())},'contrepassations2026_validees':2,'cinquante_originaux2025_inchanges':True,'ecriture_sur_clos_refusee':423,'liquidation_figee':True,'cm_scenario':'0.00','cm_avant_parametrage':'3000.00','css_reference_manquante_visible':True,'limite':'Hypothèses fiscales explicites du jeu fictif, pas validation réglementaire ;CMsanscopiecontrôle dédiée restePartiel. DéclarationsTVA/exportsannuels etrecettehumaine restentàqualifier.'}
