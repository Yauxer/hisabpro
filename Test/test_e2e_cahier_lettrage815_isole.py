"""Lettrage de quatre auxiliaires soldés et contrôles négatifs indépendants."""
from pathlib import Path
from decimal import Decimal as D
import csv,io,re,hashlib
import pytest
from playwright.sync_api import expect
from cahier_formulaires773_support import laboratoire,DATA,ok,champ
from cahier_suite777_support import core
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

R=Path(__file__).resolve().parents[1]

def tiers_sources(api):
 return {t['code']:ok(api.post('/api/tiers',json={'nom':t['nom'],'type':t['type'],('compte_client' if t['type']=='client' else 'compte_fournisseur'):t['compte']}),201) for t in DATA['tiers']}

def poster(api,jour,journal,reference,libelle,lignes):
 e=ok(api.post('/api/ecritures',json={'date':jour,'date_piece':jour,'journal':journal,'libelle':libelle,'reference':reference,'lignes':lignes,'est_validee':False}),201)
 validation=ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
 return {**e,**validation}

def lire(api,compte):return ok(api.get('/api/lettrage/comptable',params={'exercice':2025,'compte':compte}))

def choisir(page,compte,nom):
 champ(page,'Compte','select').select_option(compte);expect(champ(page,'Tiers','select').locator('option').filter(has_text=nom)).to_have_count(1);champ(page,'Tiers','select').select_option(label=nom)

@pytest.mark.parametrize('largeur',[1440,390])
def test_815_lettrage_annuel_quatre_tiers_persistant_et_impayes_ouverts(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'lettrage815r') as (api,page,sid,preuve):
  tiers=tiers_sources(api)
  for o in sorted(DATA['operations'],key=lambda x:x['date']):
   lignes=[{'compte':l['compte'],'debit':l['debit'],'credit':l['credit'],'libelle':o['description'],**({'tiers_id':tiers[l['tiers']]['id']} if l['tiers'] else {})} for l in o['lignes']];piece={'REF-02':'02','REF-002':'002'}.get(o['reference_recette'],o['reference_recette']);poster(api,o['date'],o['journal'],piece,o['description'],lignes)
  avant=core(application,sid);assert len(avant)==50;etats=ok(api.get('/api/etats/liasse/2025'))['etats'];codes={};preuve['lettrage815']={'groupes':[]};page.goto(application['web_url']+'/lettrage')
  for compte,cle in [('3421','C-MARCH'),('3421','C-SERVICE'),('4411','F-MARCH'),('4411','F-SERVICE')]:
   nom=tiers[cle]['nom'];lignes=[l for l in lire(api,compte) if l['tiers']==nom];assert len(lignes)>=2 and not any(l['code_lettrage'] for l in lignes)
   debit=sum(D(str(l['debit'])) for l in lignes);credit=sum(D(str(l['credit'])) for l in lignes);assert debit==credit and debit>0
   choisir(page,compte,nom);boxes=page.locator('tbody input[type=checkbox]');expect(boxes).to_have_count(len(lignes))
   for box in boxes.all():box.check()
   expect(page.get_by_text('Sélection équilibrée',exact=True)).to_be_visible()
   with page.expect_response(lambda r:r.url.endswith('/api/lettrage/comptable/lettrer') and r.request.method=='POST') as r:page.get_by_role('button',name=f'Lettrer {len(lignes)} lignes',exact=True).click()
   lettre=ok(r.value);assert lettre['nb']==len(lignes) and set(lettre['ligne_ids'])=={l['ligne_id'] for l in lignes} and re.fullmatch('[A-Z]{3,10}',lettre['code'])
   codes[cle]=lettre['code'];expect(page.get_by_text(f'{len(lignes)} lettrée(s)',exact=True)).to_be_visible();page.reload(wait_until='domcontentloaded');choisir(page,compte,nom);expect(page.get_by_text(f'{len(lignes)} lettrée(s)',exact=True)).to_be_visible();relues=[l for l in lire(api,compte) if l['tiers']==nom];assert all(l['code_lettrage']==lettre['code'] and l['date_lettrage'] for l in relues)
   preuve['lettrage815']['groupes'].append({'tiers':cle,'compte':compte,'nb_lignes':len(lignes),'debit':str(debit),'credit':str(credit),'code':lettre['code'],'lignes':relues})
  assert len(set(codes.values()))==4
  for compte,cle,solde in [('3421','C-IMPAYE','14400'),('4411','F-CONTROLE','-480')]:
   nom=tiers[cle]['nom'];choisir(page,compte,nom);ls=[l for l in lire(api,compte) if l['tiers']==nom];assert not any(l['code_lettrage'] for l in ls) and sum((D(str(l['debit']))-D(str(l['credit'])) for l in ls),D(0))==D(solde);expect(page.get_by_text(f'{len(ls)} non lettrée(s)',exact=True)).to_be_visible()
   if cle=='F-CONTROLE':assert {l['reference'] for l in ls}=={'02','002'}
  assert core(application,sid)==avant and ok(api.get('/api/etats/liasse/2025'))['etats']==etats
  fec=api.get('/api/fec/export',params={'exercice':2025});assert fec.status_code==200;rows=list(csv.DictReader(io.StringIO(fec.text),delimiter='\t'));assert len(rows)==118
  for groupe in preuve['lettrage815']['groupes']:
   nom=tiers[groupe['tiers']]['nom'];lignes=[r for r in rows if r['Num_Compte']==groupe['compte'] and r['Libelle_Compte_Aux']==nom];assert len(lignes)==groupe['nb_lignes'] and all(r['Lettrage_Ecriture']==groupe['code'] for r in lignes)
  f=tmp_path/f'fec_lettrage815_{largeur}.txt';f.write_bytes(fec.content);preuve['fichier815']={'chemin':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};preuve['lettrage815'].update(journal_et_etats_inchanges=True,impayes_conserves={'client':'14400','fournisseur':'480'},codes=codes);preuve['cas'].append({'id':'HP-CPT-003','statut':'Réussi'})

@pytest.mark.parametrize('largeur',[1440,390])
def test_815_refus_cross_auxiliaires_et_ecart_100_99(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'neg_lettrage815r') as (api,page,sid,preuve):
  tiers=tiers_sources(api);m=tiers['C-MARCH']['id'];s=tiers['C-SERVICE']['id'];ls=[]
  for ref,compte,d,c,tid in [('DEBIT100','7124',100,0,m),('CREDIT100','5141',0,100,s),('CREDIT99','5141',0,99,m)]:
   e=poster(api,'2025-01-01','VT' if d else 'BQ',ref,'Contrôle négatif fictif815',[{'compte':'3421','debit':d,'credit':c,'tiers_id':tid},{'compte':compte,'debit':c,'credit':d}]);ls.append(next(l['id'] for l in e['lignes'] if l['compte']=='3421'))
  avant=core(application,sid);avant_lettres=lire(api,'3421');assert not any(l['code_lettrage'] for l in avant_lettres);page.goto(application['web_url']+'/lettrage')
  ligne=lambda ref:page.locator('tbody tr').filter(has=page.get_by_text(ref,exact=True))
  expect(page.locator('tbody input[type=checkbox]')).to_have_count(3);ligne('DEBIT100').locator('input').check();expect(ligne('CREDIT100').locator('input')).to_be_disabled()
  refus=api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':ls[:2]});assert refus.status_code==400 and 'seul client/fournisseur' in refus.json()['detail'];assert lire(api,'3421')==avant_lettres
  cross=tmp_path/f'cross_aux815_{largeur}.png';page.screenshot(path=str(cross),full_page=True);ligne('CREDIT99').locator('input').check();expect(page.get_by_role('button',name=re.compile('^Écart '))).to_be_disabled();expect(page.get_by_text('Sélection équilibrée',exact=True)).to_have_count(0)
  ecart=api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':[ls[0],ls[2]]});assert ecart.status_code==400 and 'non équilibrée' in ecart.json()['detail'];assert core(application,sid)==avant and lire(api,'3421')==avant_lettres
  preuve['negatifs815']={'cross_aux400':refus.json()['detail'],'ecart400':ecart.json()['detail'],'zero_lettrage':True,'journal_inchange':True,'capture_cross':str(cross),'capture_cross_sha256':hashlib.sha256(cross.read_bytes()).hexdigest()};preuve['cas'] += [{'id':'HP-NEG-021','statut':'Réussi'},{'id':'HP-NEG-022','statut':'Réussi'}]
