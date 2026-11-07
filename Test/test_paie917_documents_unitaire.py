from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
import pytest
from pypdf import PdfReader
from openpyxl import load_workbook
from fastapi import HTTPException
from services import paie_ir_documents_service as doc
from services.paie_ir_annuel_moteur import calculer,REFERENTIEL
from services.paie_ir_annuel_schemas import Simulation
from services.paie_frais_annuels_moteur import calculer as frais
from services.paie_frais_annuels_schemas import Simulation as Frais
from services.personnel_profil_service import exiger_chemin_personnel
from test_paie901_ir_annuel_unitaire import demande
from test_paie913_frais_annuels_unitaire import demande as demande_frais,sources
from test_logo_societe import image_data


def jeu(inconnu=False,logo=None,famille=True):
    c=calculer(Simulation.model_validate(demande(revenu_net_imposable_annuel='83890.00',personnes_charge=None if inconnu else 2,eligibilite_famille_confirmee=famille)))
    c['source_frais_annuels']={'nom':'=HYPERLINK("https://interdit.invalid") <b>Salarié</b>','matricule':'P917','rni_avant_arrondis':'83881.0200','base_annuelle_utilisee':'83890.00','regle_arrondi':deepcopy(REFERENTIEL['arrondi_base_annuelle'])}
    d=demande_frais();f=frais(Frais.model_validate(d),sources());f['declaration']=d
    f['sources']=[{'periode':f'2026-{m:02d}-01','preparation_id':m,'social_id':m,'brut_id':m,'empreinte':'b'*64} for m in range(1,13)]
    return {'id':1,'empreinte':'c'*64,'contenu':c},{'id':2,'empreinte':'d'*64,'contenu':f},{'raison_sociale':'=1+1 Société <b>fictive</b>','ice':None,'identifiant_fiscal':None,'logo_url':logo}


@pytest.mark.parametrize('logo',[None,'PNG','JPEG','https://interdit.invalid/logo.png'])
def test_917_pdf_logo_exactitude_injection_et_snapshots_intacts(logo):
    a,b,s=jeu(logo=image_data(logo) if logo in {'PNG','JPEG'} else logo);avant=deepcopy((a,b,s));p=PdfReader(BytesIO(doc.pdf(a,b,s)));t='\n'.join(x.extract_text() or '' for x in p.pages)
    assert all(x in t for x in ['83881.0200','83890.00','5967.0000','2026-01-01','2026-12-01','<b>Salarié</b>','Non déterminé'])
    assert 'Préparation fiscale :' in t and 'Simulation sociale :' in t and 'Simulation brute :' in t and 'Impôt arithmétique (MAD) :' in t
    assert sum(len(x.images) for x in p.pages)==(1 if logo in {'PNG','JPEG'} else 0)
    assert (a,b,s)==avant


def test_917_excel_texte_exact_aucune_formule_ou_lien_externe_et_inconnues():
    a,b,s=jeu(True, image_data());avant=deepcopy((a,b,s));w=load_workbook(BytesIO(doc.xlsx(a,b,s)),data_only=False)
    assert len(w['Logo société']._images)==1 and w['Sources mensuelles'].max_row==13
    assert w['Identite']['B3'].value.startswith('=1+1') and w['Identite']['B3'].data_type=='s'
    valeurs={r[0]:r[1] for r in w['IR annuel'].iter_rows(min_row=2,values_only=True)}
    assert valeurs['RNI source avant arrondis']=='83881.0200' and valeurs['IR annuel arithmétique']=='À compléter' and valeurs['Personnes à charge déclarées']=='À compléter'
    assert not w._external_links and all(c.data_type!='f' for sh in w for row in sh for c in row)
    portee=next(row for row in w['Identite'] if row[0].value=='Portée');assert w['Identite'].row_dimensions[portee[0].row].height>=80
    assert (a,b,s)==avant


def test_917_nombre_declare_ne_vaut_pas_eligibilite_confirmee():
    a,b,s=jeu(famille=False);lignes=dict(doc.sections(a,b,s)['IR annuel'][1:])
    assert lignes['Personnes à charge déclarées']=='2' and lignes['Éligibilité familiale confirmée']=='Non'
    assert lignes['IR annuel arithmétique']=='À compléter' and lignes['IR avant réduction']=='7167.0000'


@pytest.mark.parametrize('methode,suffixe,ok',[('GET','/1/export/pdf',True),('GET','/1/export/xlsx',True),('POST','/1/export/pdf',False),('GET','/1/export/csv',False),('GET','/0/export/pdf',False),('GET','/1/export/pdf/autre',False)])
def test_917_export_personnel_chemins_fermes(methode,suffixe,ok):
    q=SimpleNamespace(method=methode,url=SimpleNamespace(path='/api/employes/personnel/fiscalite'+suffixe))
    if ok:exiger_chemin_personnel('personnel',q)
    else:
        with pytest.raises(HTTPException):exiger_chemin_personnel('personnel',q)
