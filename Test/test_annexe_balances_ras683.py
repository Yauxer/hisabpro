"""Documents683, suivi humain vierge et confrontation du jeu750 aux vraies API."""
from pathlib import Path
from zipfile import ZipFile
from decimal import Decimal
from contextlib import closing
import csv,json,xml.etree.ElementTree as E
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text
from generer_annexe_balances_ras683 import jeu,cas,NOM,JSON_NOM,OUT,CHAMPS
from test_ras_rapprochements681_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,application087,migration,
    client,ok,corps,chemin,photo)


def test_683_oracles_et_csv_independants_du_moteur():
    d=jeu();o=d['oracle_balances'];r=d['oracle_ras']
    assert o['total_debit']==o['total_credit']=='51000.00'
    assert o['brut']=='50000.00' and o['amortissements']=='300.00' and o['actif_net']==o['passif']=='49700.00'
    assert o['cpc']=='5000.00' and o['n1_actif_net']=='24850.00'
    assert r['avant_versement']['debit']=='118000.00' and r['apres_versement']['debit']=='118750.00'
    assert r['apres_versement']['banque']=='94000.00' and r['apres_versement']['bilan']=='96000.00'
    for cle in ('n','n1'):
        with (OUT/d['fichiers'][cle]).open(encoding='utf8',newline='') as f:
            rows=list(csv.DictReader(f,delimiter=';'))
        assert rows==d['balance_'+cle] and len(rows)==13
        assert sum(Decimal(x['debit']) for x in rows)==sum(Decimal(x['credit']) for x in rows)
    publie=json.loads((OUT/JSON_NOM).read_text(encoding='utf8'))
    assert publie=={**d,'cas':cas()}


def test_683_word_pdf_ids_chiffres_et_statuts_humains():
    stem=OUT/NOM
    with ZipFile(stem.with_suffix('.docx')) as z:
        assert z.testzip() is None
        for n in z.namelist():
            if n.endswith('.xml'):E.fromstring(z.read(n))
        doc=E.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    word=' '.join(t.text or '' for t in doc.findall('.//w:t',ns))
    reader=PdfReader(stem.with_suffix('.pdf'));pdf=' '.join(p.extract_text() or '' for p in reader.pages)
    assert len(reader.pages)>=18
    for contenu in (word,pdf):
        assert 'Version 1 du 20 octobre 2026' in contenu and 'production : non validée' in contenu
        for t in cas():assert t['id'] in contenu,t['id']
        for reference in jeu()['ras']['references'].values():assert reference in contenu,reference
        assert contenu.count('Statut humain : Non testé')==15
        assert '118750' in contenu and '94000' in contenu and '96000' in contenu
        assert 'n’est pas un reste fiscal à payer' in contenu


def test_683_excel_resultats_vierges_formules_et_ordre():
    w=load_workbook(OUT/(NOM+'.xlsx'),data_only=False)
    assert set(w.sheetnames)=={'Synthèse','Balances','Rapprochements RAS','Ordre de passage','Données','Oracle','Anomalies','Preuves','Limites'}
    assert len(w['Synthèse']._charts)==1 and w.calculation.fullCalcOnLoad
    trouve=[]
    for n,nb in [('Balances',7),('Rapprochements RAS',8)]:
        ws=w[n];assert ws.max_row==nb+1 and ws.freeze_panes=='D2'
        assert len(ws.data_validations.dataValidation)==1
        for row in ws.iter_rows(min_row=2):
            trouve.append(row[0].value)
            assert row[10].value=='Non testé'
            for i in (11,12,14,15):assert row[i].value is None
    assert trouve==[t['id'] for t in cas()]
    assert all(r[4]=='Non testé' for r in list(w['Ordre de passage'].values)[1:])
    assert w['Anomalies'].max_row==1
    assert all(r[2] is None and r[3] is None for r in list(w['Preuves'].values)[1:])
    assert 'COUNTIF' in w['Synthèse']['B4'].value and w['Synthèse']['G6'].value=='=IF(F6=0,0,C6/F6)'


def test_683_jeu750_rapprochements_et_retrait_sans_modification_comptable(application):
    d=jeu();r=d['ras'];y=2026
    with closing(client(application)[0]) as api:
        sid=ok(api.get('/api/auth/me'))['societe_id']
        ok(api.patch('/api/societe/moi',json={'capital_social':100000,'regime_tva':'encaissement'}))
        ok(api.put('/api/tva/parametres/2026',json={'credit_ouverture':0,'prorata_deduction_pct':100}))
        def ecriture(compte_d,compte_c,m,ref):
            e=ok(api.post('/api/ecritures',json={'date':r['date_operation'],'journal':'BQ','reference':ref,'libelle':'Recette fictive683',
                'lignes':[{'compte':compte_d,'debit':m},{'compte':compte_c,'credit':m}]}),201)
            ok(api.post(f'/api/ecritures/{e["id"]}/valider'));return e
        ecriture('5141','1111',100000,r['references']['capital'])
        t=ok(api.post('/api/tiers',json={'nom':r['fournisseur'],'type':'fournisseur'}),201)
        f=ok(api.post('/api/factures',json={'type':'achat','date':r['date_operation'],'reference':r['references']['facture'],
            'tiers_id':t['id'],'tiers':t['nom'],'nature_tva_achat':'charge','tva_deductible_pct':100,
            'lignes':[{'description':r['article'],'quantite':1,'prix_unitaire':10000,'tva':20}]}),201)
        ok(api.post(f'/api/factures/{f["id"]}/valider'))
        eid=ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))['ecriture_id'];ok(api.post(f'/api/ecritures/{eid}/valider'))
        reg=ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':t['nom'],'tiers_id':t['id'],'date':r['date_operation'],
            'montant':r['cash'],'mode':'virement','reference':r['references']['cash'],'comptabiliser':True}),201)
        with application['engine'].connect() as db:cash=db.scalar(text('SELECT ecriture_id FROM reglements WHERE id=:r'),{'r':reg['id']})
        ok(api.post(f'/api/ecritures/{cash}/valider'))
        demande={'simulation':r['simulation'],'justification_quote_part':r['justification_quote_part']}
        p=ok(api.post(f'/api/reglements/{reg["id"]}/ras-tva/apercu',json=demande))
        cap=ok(api.post(f'/api/reglements/{reg["id"]}/ras-tva',json={**demande,'reference':r['references']['capture'],
            'compte_destination':r['compte_capture_choisi'],'empreinte_apercu':p['empreinte_apercu'],'pieces_verifiees':True}))
        cid=cap['capture']['id'];eid=cap['capture']['ecriture_id'];ok(api.post(f'/api/ecritures/{eid}/valider'))
        assert cap['dossier']['simulation']['retenue_tva']=='750.00'
        def verifier(phase):
            o=d['oracle_ras'][phase]
            with application['engine'].connect() as db:
                pieces=db.execute(text('SELECT count(*),bool_and(est_validee) FROM ecritures WHERE societe_id=:s'),{'s':sid}).one()
                total=db.execute(text('SELECT count(*),sum(l.debit),sum(l.credit) FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s'),{'s':sid}).one()
                assert tuple(pieces)==(o['pieces'],True)
                assert tuple(total)==(o['lignes'],Decimal(o['debit']),Decimal(o['credit']))
                banque=db.scalar(text("SELECT sum(l.debit-l.credit) FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s AND l.compte='5141'"),{'s':sid})
                assert banque==Decimal(o['banque'])
            etats=ok(api.get('/api/etats/liasse/2026'))['etats']
            assert Decimal(str(etats['cpc']['resultat_net']))==Decimal(o['cpc'])
            assert Decimal(str(etats['bilan']['actif']['total']['net']))==Decimal(o['bilan'])
            assert Decimal(str(etats['bilan']['passif']['total']))==Decimal(o['bilan'])
        verifier('avant_versement')
        e=ecriture('4457','5141',750,r['references']['versement']);verifier('apres_versement')
        avant=photo(application)
        b1,b2=corps(e,'300.00'),corps(e,'450.00')
        a=ok(api.post(chemin(cid),json=b1),201);assert a['capacite_documentaire']=='450.00'
        a=ok(api.post(chemin(cid),json=b2),201);assert a['total_rapproche']=='750.00' and a['capacite_documentaire']=='0.00'
        rid=a['items'][0]['id'];a=ok(api.post(chemin(cid)+f'/{rid}/retirer',json={'motif':'ERREUR DOCUMENTAIRE FICTIVE RR683'}))
        assert a['total_rapproche']=='300.00' and a['capacite_documentaire']=='450.00'
        assert photo(application)==avant
        verifier('apres_versement')
