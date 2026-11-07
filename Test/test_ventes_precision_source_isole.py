"""Préparation :somme Decimal de sources représentables,API réelle/PGnonce."""
from contextlib import closing
from datetime import date
from decimal import Decimal
import uuid
from io import BytesIO
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text
from test_ventes_preparation_isole import application,facture,ok,preparation,photographie,cible
from test_ras_lecture_conservation import client


@pytest.mark.parametrize('nature',['facture','avoir'])
def test_centime_grand_montant_source_conserve_sans_mutation(application,nature):
    with closing(client(application)[0]) as api:
        tiers=ok(api.post('/api/tiers',json={'nom':'Client fictif précision '+uuid.uuid4().hex[:8],
            'type':'client','ice':'001234567890123'}),201)
        f=ok(api.post('/api/factures',json={'type':'vente','tiers_id':tiers['id'],'tiers':tiers['nom'],
            'date':f'{date.today().year}-01-15','lignes':[
                {'description':'Grand montant entier fictif','quantite':1,'prix_unitaire':1000000000000000,'tva':20},
                {'description':'Centime fictif distinct','quantite':1,'prix_unitaire':0.01,'tva':20}]}),201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        # Vérifier d'abord les valeurs réellement stockées :aucun centime
        # déjà perdu au stockage n'est inventé ou reconstitué.
        cible(application)
        with application['engine'].connect() as db:
            prix=db.execute(text('SELECT prix_unitaire FROM lignes_facture WHERE facture_id=:id ORDER BY id'),{'id':f['id']}).scalars().all()
        assert [Decimal(str(v)) for v in prix]==[Decimal('1000000000000000'),Decimal('0.01')]
        if nature=='avoir':
            ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':f'{date.today().year}-03-15',
                'motif':'Avoir fictif précision','lignes':[{'facture_ligne_id':l['id'],'quantite':1} for l in f['lignes']]}),201)
        avant=photographie(application)
        data=ok(preparation(api))
        piece=next(r for r in data['documents'] if r['nature']==nature)
        signe='' if nature=='facture' else '-'
        assert {k:piece[k] for k in ('ht','tva','ttc')}=={
            'ht':signe+'1000000000000000.01','tva':signe+'200000000000000.00',
            'ttc':signe+'1200000000000000.01'}
        if nature=='avoir':assert data['totaux']=={'ht':'0.00','tva':'0.00','ttc':'0.00'}
        assert signe+'1000000000000000.01' in data['csv']
        for format in ('xlsx','pdf'):
            r=api.get(f"/api/etats/ventes/preparation/{data['exercice']}/export/{format}",
                params={'empreinte':data['empreinte_sha256']})
            assert r.status_code==200,r.text
            if format=='xlsx':
                w=load_workbook(BytesIO(r.content))
                row=next(row for row in w['Sources'].iter_rows(min_row=2) if row[0].value==nature)
                assert row[7].value==signe+'1000000000000000.01' and row[7].data_type=='s'
                assert row[9].value==signe+'1200000000000000.01' and row[9].data_type=='s'
            else:
                texte=''.join(''.join(p.extract_text().split()) for p in PdfReader(BytesIO(r.content)).pages)
                assert signe+'1000000000000000,01' in texte and signe+'1200000000000000,01' in texte
        assert photographie(application)==avant


def test_escompte_taux_mixtes_et_avoir_partiel_meme_moteur(application):
    # Taux de laboratoire,aucune qualification fiscale générale.
    with closing(client(application)[0]) as api:
        tiers=ok(api.post('/api/tiers',json={'nom':'Client fictif escompte '+uuid.uuid4().hex[:8],
            'type':'client','ice':'001234567890123'}),201)
        f=ok(api.post('/api/factures',json={'type':'vente','tiers_id':tiers['id'],'tiers':tiers['nom'],
            'date':f'{date.today().year}-01-15','escompte':10,'lignes':[
                {'description':'Prestation fictive100','quantite':1,'prix_unitaire':100,'tva':20},
                {'description':'Prestation fictive50','quantite':1,'prix_unitaire':50,'tva':10}]}),201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':f'{date.today().year}-03-15',
            'motif':'Moitié fictive','lignes':[{'facture_ligne_id':l['id'],'quantite':0.5} for l in f['lignes']]}),201)
        avant=photographie(application);data=ok(preparation(api))
        pieces={r['nature']:{k:r[k] for k in ('ht','tva','ttc')} for r in data['documents']}
        assert pieces=={'facture':{'ht':'150.00','tva':'22.50','ttc':'157.50'},
            'avoir':{'ht':'-75.00','tva':'-11.25','ttc':'-78.75'}}
        assert data['totaux']=={'ht':'75.00','tva':'11.25','ttc':'78.75'}
        assert photographie(application)==avant
