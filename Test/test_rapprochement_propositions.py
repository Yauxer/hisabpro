"""Unicité des références/date/sens/centimes, sans base ni mutation."""
from copy import deepcopy
import pytest
from rapprochement_propositions import construire

def dossier():
    return {'compte':'5141','date_debut':'2026-01-01','date_fin':'2026-12-31','lecture_seule':False,
        'lignes_releve':[{'id':1,'date':'2026-06-01','libelle':'REF-EXACTE','montant':120,'sens':'credit','rapprochee':False}],
        'ecritures':[{'ligne_id':2,'date':'2026-06-01','reference':'REF-EXACTE','debit':120,'credit':0,'rapprochee':False,'numero_ecriture':'BQ0001'}],
        'ventilations':[]}

def test_lecture_pure_une_proposition_et_empreinte_stable():
    data=dossier();avant=deepcopy(data);p=construire(data)
    assert len(p['propositions'])==1 and p['propositions'][0]['ecriture_ligne_id']==2
    assert construire(deepcopy(data))==p and data==avant

@pytest.mark.parametrize('champ,valeur',[('date','2026-06-02'),('libelle','ref-exacte'),('libelle','REF'),
 ('libelle',None),('sens','debit'),('montant',120.01),('montant',float('nan')),('montant',float('inf')),('montant',True),('montant',0.001)])
def test_aucune_interpretation_arbitraire(champ,valeur):
    data=dossier();data['lignes_releve'][0][champ]=valeur
    assert not construire(data)['propositions']

def test_deux_sources_identiques_restent_ambigues():
    data=dossier();e=deepcopy(data['ecritures'][0]);e['ligne_id']=3;data['ecritures'].append(e)
    p=construire(data);assert not p['propositions'] and len(p['ambigues'])==1

def test_deux_releves_pour_une_source_ne_sont_pas_attribues_arbitrairement():
    data=dossier();r=deepcopy(data['lignes_releve'][0]);r['id']=3;data['lignes_releve'].append(r)
    p=construire(data);assert not p['propositions'] and len(p['ambigues'])==2

def test_source_partagee_avec_ligne_ambigue_bloque_tous_candidats():
    data=dossier();data['ecritures'][0]['debit']=60
    e=deepcopy(data['ecritures'][0]);e['ligne_id']=3;data['ecritures'].append(e)
    data['ventilations']=[{'operation_id':'op','date':'2026-06-01','reference':'REF-EXACTE','montant':120,
        'sens':'credit','ecriture_ligne_ids':[2,3],'nb_reglements':2}]
    r=deepcopy(data['lignes_releve'][0]);r.update(id=4,montant=60);data['lignes_releve'].append(r)
    p=construire(data);assert not p['propositions'] and len(p['ambigues'])==2

def test_ligne_deja_pointee_ailleurs_exclue():
    data=dossier();data['ecritures'][0]['rapprochee']=True
    assert not construire(data)['propositions']

def test_modification_reference_change_empreinte():
    data=dossier();before=construire(data)['empreinte'];data['lignes_releve'][0]['libelle']='AUTRE'
    assert construire(data)['empreinte']!=before
