"""Compléments ETIC documentés du cahier, sans inventer les reliquats."""
from decimal import Decimal as D
import re,hashlib
from pypdf import PdfReader
from openpyxl import load_workbook
from cahier_etats803_support import telecharger
from playwright.sync_api import expect
from cahier_formulaires773_support import DATA,ok
from cahier_suite777_support import core
GROUPES={'A':'A — Principes et méthodes comptables','B':'B — Compléments au Bilan et au CPC','C':'C — Autres informations complémentaires'}
CAS={'A1':'HP-ETA-004','A2':'HP-ETA-005','A3':'HP-ETA-006','B1':'HP-ETA-007','B2':'HP-ETA-008','B2bis':'HP-ETA-009','B3':'HP-ETA-010','B4':'HP-ETA-011','B5':'HP-ETA-012','B8':'HP-ETA-013','B9':'HP-ETA-014','B10':'HP-ETA-015','B11':'HP-ETA-016','B12':'HP-ETA-017','C1':'HP-ETA-020','C2':'HP-ETA-021','C3':'HP-ETA-022','C4':'HP-ETA-023','C5':'HP-ETA-024'}
TEXTES={c['id']:c['donnees'] for c in DATA['cas_recette'] if c['id'] in CAS.values()}

def lire(api):return ok(api.get('/api/etats/etic/2025'))
def section(api,code):return next(x for x in lire(api)['sections'] if x['code']==code)
def ouvrir(page,code):
 page.get_by_role('button',name=GROUPES[code[0]],exact=True).click();p=page.locator('#etic-'+code);expect(p).to_be_visible();return p

def sauvegarder(api,page,app,code,complet):
 p=page.locator('#etic-'+code)
 with page.expect_response(lambda r:r.url.endswith('/api/etats/etic/2025') and r.request.method=='GET') as relecture:
  with page.expect_response(lambda r:r.url.endswith('/api/etats/etic/2025/'+code) and r.request.method=='PUT') as mutation:p.get_by_role('button',name='Enregistrer',exact=True).click()
 ok(mutation.value);ok(relecture.value);expect(p.get_by_text('Complet' if complet else 'À compléter',exact=True)).to_be_visible();s=section(api,code);assert s['complete'] is complet
 page.reload(wait_until='domcontentloaded');p=ouvrir(page,code);expect(p.get_by_text('Complet' if complet else 'À compléter',exact=True)).to_be_visible();return s

def completer_etic(api,page,app,sid,preuve,tmp_path):
 avant=core(app,sid);snapshot=ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'];page.goto(app['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2025');page.goto(app['web_url']+'/etic');expect(page.get_by_role('button',name=GROUPES['A'],exact=True)).to_be_visible();debut=lire(api);assert not debut['verrouillee'];preuve['etic805']={'avant':debut,'sections_verifiees':[]}
 for code,cas in CAS.items():
  s=section(api,code);p=ouvrir(page,code);texte=TEXTES[cas]
  if code=='C1':
   p.get_by_role('button',name='Ajouter une ligne',exact=False).click()
   valeurs={'Actionnaire / associé':'Associé Recette','Identifiant / adresse':'REC-ASSOC01','Nombre de titres / parts':'2000','Valeur nominale':'100','Montant du capital détenu':'200000','% capital':'100'}
   for label,v in valeurs.items():p.get_by_label(label,exact=True).fill(v)
  elif code=='C5':
   assert preuve['echeances795']['cloture_et_snapshot2025_inchanges']
   texte='État fictif du cahier préparé au 06/10/2026 ; contrôle automatisé exécuté le 25/10/2026. Événements N+1 effectivement enregistrés dans ce laboratoire : TVA décembre 2025 payée 2 400 MAD le 20/01/2026 ; IS 2025 payé 23 220,25 MAD le 31/03/2026. Acomptes 2026 : 6 691,50 MAD le 31/03 et 2 000 MAD le 30/06. Aucun événement réel n’est affirmé.'
   p.locator('textarea').fill(texte)
  elif s['mode']=='manuel' and (texte.startswith('Néant') or code=='C2'):
   p.get_by_role('checkbox',name="Néant pour l'exercice 2025",exact=True).check()
  else:p.locator('textarea').fill(texte)
  if s['mode']=='assiste':p.get_by_role('checkbox',name=re.compile("^J'ai contrôlé")).check()
  enregistre=sauvegarder(api,page,app,code,True);c=enregistre['contenu']
  if code=='C1':
   ligne=c['lignes'][0];assert ligne['associe']=='Associé Recette' and ligne['identifiant']=='REC-ASSOC01';assert [D(str(ligne[k])) for k in ['titres','nominal','capital','pourcentage']]==list(map(D,['2000','100','200000','100']))
  elif s['mode']=='manuel' and (TEXTES[cas].startswith('Néant') or code=='C2'):assert c['neant'] is True
  else:assert c.get('texte',c.get('notes'))==texte
  if code=='B2':assert any(D(str(x.get('fin_module',0)))==D('24000') and D(str(x.get('ecart',0)))==0 for x in enregistre['automatique']['lignes'])
  if code=='B2bis':assert sum(D(str(x['dotations'])) for x in enregistre['automatique']['lignes'])==D('4800')
  if code=='B5':assert {x['compte']:D(str(x['fin'])) for x in enregistre['automatique']['lignes']}=={'1518':D('1500'),'3942':D('2000')}
  if code=='B12':
   l={x['rubrique']:D(str(x['montant'])) for x in enregistre['automatique']['lignes']};assert l['Résultat net comptable']==D('106409.75') and l['Réintégrations fiscales (dont IS comptabilisé)']==D('27420.25') and l['Bénéfice fiscal imposable']==D('133830')
  if code=='C3':
   l=enregistre['automatique']['lignes'];assert all(x['resultat_net'] is None for x in l if x['exercice']<2025);assert next(D(str(x['resultat_net'])) for x in l if x['exercice']==2025)==D('106409.75')
  preuve['etic805']['sections_verifiees'].append(code);preuve['cas'].append({'id':cas,'statut':'Réussi'})
 # B7 : échéances documentées par les pièces et paiements N+1 réellement joués.
 s=section(api,'B7');p=ouvrir(page,'B7');a=next(x for x in s['automatique']['lignes'] if x['compte']=='4411');assert D(str(a['echeance_auto_total']))==D('480') and a['echeance_auto_nb_factures']>=2
 factures=[f for f in ok(api.get('/api/factures',params={'exercice':2025})) if f.get('reference') in ['02','002']];assert len(factures)==2 and all(f['date_echeance']=='2025-12-31' for f in factures);preuve['etic805']['sources_b7']={'factures_examinees':a['echeance_auto_nb_factures'],'references_impayees':[f['reference'] for f in factures],'echues_certaines':'480.00'}
 expect(p.get_by_label('4411 Échues et non payées',exact=True)).to_have_value('480')
 for compte,val in [('4417','3000'),('4453','23220.25'),('4456','2400')]:
  for lib,m in [('+ d’un an','0'),('- d’un an',val),('Échues et non payées','0')]:p.get_by_label(compte+' '+lib,exact=True).fill(m)
 p.get_by_role('checkbox',name=re.compile('^Autres analyses')).check();p.locator('textarea').fill('FNP-01 : échéance contractuelle au 31/01/2026 selon le cahier. IS de 23 220,25 payé le 31/03/2026 et TVA de 2 400 payée le 20/01/2026 : écritures N+1 effectivement jouées. Références 02 et 002 distinctes, échéances au 31/12/2025 ; autres analyses néant selon le cas fictif.');p.get_by_role('checkbox',name=re.compile("^J'ai contrôlé")).check();b7=sauvegarder(api,page,app,'B7',True)
 for compte,val in [('4453','23220.25'),('4456','2400')]:assert D(str(next(x for x in b7['ventilation'] if str(x['compte'])==compte)['etat_organismes_publics']))==D(val)
 # B6 : seules les créances clients sont certaines ;aucune tranche supposée pour80/11000.
 s=section(api,'B6');p=ouvrir(page,'B6');a=next(x for x in s['automatique']['lignes'] if x['compte']=='3421');assert D(str(a['echeance_auto_total']))==D('14400');assert a['echeance_auto_anomalies_sources'],a
 # Qualification manuelle justifiée par la pièce et le rejet réellement comptabilisé avant clôture.
 sources=ok(api.get('/api/factures',params={'exercice':2025}));impayees=[f for f in sources if f.get('numero')=='FA-2025-009'];assert len(impayees)==1 and impayees[0]['date_echeance']=='2025-12-20'
 rejets=[e for e in avant if str(e[1])=='2025-12-15' and e[4]=='CHQ-REJET' and 'Impayé' in e[5]];assert len(rejets)==1 and any(l[1]=='3421' and D(str(l[2]))==D('2000') for l in rejets[0][8])
 for lib,val in [('+ d’un an','0'),('- d’un an','0'),('Échues et non recouvrées','14400')]:p.get_by_label('3421 '+lib,exact=True).fill(val)
 preuve['etic805']['qualification_manuelle_3421']={'montant':'14400','echeance':'2025-12-20','rejet_comptabilise':'2025-12-15','alerte_automatique_conservee':a['echeance_auto_anomalies_sources']}
 p.get_by_role('checkbox',name=re.compile('^Autres analyses')).check();p.locator('textarea').fill('VENTE-IMPAYEE : échéance au 20/12/2025, solde de 14 400 qualifié manuellement depuis la facture et le rejet CHQ-REJET comptabilisé le 15/12/2025 ; alerte automatique conservée, pas de lien historique inventé. Lignes 34552 = 80 et 3491 = 11 000 : ventilation à qualifier depuis les pièces, aucune date supposée. Autres analyses néant selon les hypothèses du jeu.');p.get_by_role('checkbox',name=re.compile("^J'ai contrôlé")).uncheck();b6=sauvegarder(api,page,app,'B6',False);assert b6['erreurs_ventilation']
 p=page.locator('#etic-B6');p.get_by_role('checkbox',name=re.compile("^J'ai contrôlé")).check()
 with page.expect_response(lambda r:r.url.endswith('/api/etats/etic/2025/B6') and r.request.method=='PUT') as r:p.get_by_role('button',name='Enregistrer',exact=True).click()
 assert r.value.status==422,r.value.text();assert section(api,'B6')['contenu']==b6['contenu'];page.reload(wait_until='domcontentloaded')
 # Méthode d'impôt et rapprochement des déclarations restent des décisions à documenter.
 limites={'B13':"Méthode d'affectation de l'IS entre courant et non courant non fournie par le cahier. Résultat courant 130 330 ; total IS 23 420,25. Ne pas confirmer arbitrairement.",'B14':'Les liquidations du jeu sont passées en OD. Leur rapprochement avec le tableau automatique doit être vérifié avant confirmation. TVA collectée 33 900 / récupérable 11 600 / due fin N 2 400 selon le parcours des déclarations ; 34552 non payée 80. Rapprochement à documenter : ne pas confirmer un tableau automatique non recoupé.'}
 for code,texte in limites.items():
  p=ouvrir(page,code);p.locator('textarea').fill(texte);p.get_by_role('checkbox',name=re.compile("^J'ai contrôlé")).uncheck();sauvegarder(api,page,app,code,False)
 fin=lire(api);preuve['etic805'].update(apres=fin,b6_partiel=b6,b7_complet=b7,confirmation_b6_incomplete_refusee=422,limites=limites)
 assert fin['progression']['completes']==20 and fin['progression']['total']==23,fin['progression']
 for cas in ['HP-ETA-003','HP-ETA-018','HP-ETA-019']:preuve['cas'].append({'id':cas,'statut':'Partiel','limite':'B6échéancesnonqualifiées ;B7documentécomplet ;B13méthodeàdocumenter ;B14liquidationsOD àrapprocher.'})
 liasse=ok(api.get('/api/etats/liasse/2025'));assert not liasse['controles']['pret_a_finaliser'];page.goto(app['web_url']+'/liasse-fiscale');expect(page.get_by_role('button',name='Finaliser',exact=True)).to_be_disabled();refus=api.post('/api/etats/liasse/2025/finaliser');assert refus.status_code==409,refus.text();preuve['etic805']['archive_refusee']=409;preuve['etic805']['controles_archive']=liasse['controles']
 assert core(app,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==snapshot;preuve['etic805']['ecritures_et_snapshot_inchanges']=True

 excel=telecharger(page,'Excel',tmp_path,'liasse_etic805.xlsx');pdf=telecharger(page,'PDF',tmp_path,'liasse_etic805.pdf');wb=load_workbook(excel,data_only=True);assert any(v=='REC-ASSOC01' for row in wb['ETIC'].values for v in row);texte='\n'.join(p.extract_text() or '' for p in PdfReader(pdf).pages);assert 'REC-ASSOC01' in texte and '20/23' in texte and 'BLOQUANT' in texte
 preuve['fichiers805']=[{'chemin':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [excel,pdf]]
 assert core(app,sid)==avant and ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']==snapshot
