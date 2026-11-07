from pathlib import Path
import hashlib,importlib.util
from uuid import uuid4
from sqlalchemy import text
from test_paie909_bases_isole import (
    application,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite)
from test_paie901_ir_annuel_isole import F,demande
from services.paie_ir_annuel_schemas import Simulation
from services.paie_campagnes_service import canonique,empreinte

R=Path(__file__).resolve().parents[1]


def test_911_comparaison_annuelle_api_sources_et_absence_versement(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid']);r=ok(eq['a'].post(F,json=demande(revenu_net_imposable_annuel='40000.01',personnes_charge=0)),201);c=r['contenu']
    assert c['ir_annuel_arithmetique']=='0.0010' and c['controle_arrondi_base']['ir_apres_reduction']=='1.0000'
    assert c['controle_arrondi_base']['base_arrondie']=='40010.00' and c['controle_arrondi_base']['versement'] is None
    assert c['referentiel']['arrondi_base_annuelle']['reference']=='CGI2026, article167, page imprimée317'
    assert ok(eq['a'].get(f'{F}/{r["id"]}'))['contenu']==c and comptabilite(application,eq['sid'])==avant


def test_911_snapshot901_authentique_reprise_identique_et_pas_de_recalcul(application,equipe):
    p=R/'Test/fixtures/paie_ir_annuel_901_legacy.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='88a38ff5f10d70ddf035b09787ec8bdc3d5427df4313532db43fbf624e02e39f'
    spec=importlib.util.spec_from_file_location('moteur901historique',p);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    eq=equipe;d=demande(revenu_net_imposable_annuel='40000.01',personnes_charge=0);data=Simulation.model_validate(d);ancien=legacy.calculer(data)
    assert 'controle_arrondi_base' not in ancien
    with application['engine'].begin() as db:
        ident=db.scalar(text('INSERT INTO paie_controles_ir_annuels(societe_id,annee,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,2026,:k,:d,CAST(:c AS jsonb),:h,:u,:m) RETURNING id'),
          {'s':eq['sid'],'k':d['cle_idempotence'],'d':empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'})),'c':canonique(ancien),'h':empreinte(ancien),'u':eq['uid'],'m':d['motif']})
    reprise=ok(eq['a'].post(F,json=d),201);assert reprise['id']==ident and reprise['reutilise'] and reprise['contenu']==ancien
    d['cle_idempotence']=str(uuid4());nouveau=ok(eq['a'].post(F,json=d),201)
    assert nouveau['id']!=ident and nouveau['contenu']['controle_arrondi_base']['ir_apres_reduction']=='1.0000'
    assert ok(eq['a'].get(f'{F}/{ident}'))['contenu']==ancien and ok(eq['a'].get(f'{F}/{ident}'))['empreinte']==empreinte(ancien)
