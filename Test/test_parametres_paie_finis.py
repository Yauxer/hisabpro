"""Paramètres sociaux : bornes déjà requises par le moteur, API/PG isolés."""
import json
import uuid
import math
import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session
import models
from routers.parametres import TauxCotisationUpdate
from test_e2e_facturation_isole import application
from postgres_isole import verifier_cible_isolee
from test_paie_grh_service import parametres_laboratoire


COMMUNS = [float('nan'), float('inf'), float('-inf'), 'NaN', 'Infinity', True, False, {}, [], 'invalide']
INVALIDES = [(champ, valeur) for champ in ('taux_sal','taux_pat','plafond') for valeur in COMMUNS]
INVALIDES += [('taux_sal',-.01),('taux_sal',1.01),('taux_pat',-.01),('taux_pat',1.01),('plafond',-1),('plafond',0)]


@pytest.mark.parametrize('champ,valeur',INVALIDES)
def test_schema_refuse_parametres_invalides(champ,valeur):
    with pytest.raises(ValidationError):
        TauxCotisationUpdate(**{champ:valeur})


@pytest.fixture(scope='module')
def api_admin(application):
    with httpx.Client(base_url=application['api_url']) as api:
        suffix=uuid.uuid4().hex[:8]
        r=api.post('/api/auth/register',json={'nom':'Admin fictif','email':suffix+'@example.com',
                   'password':'CotisationsFinies2026!','raison_sociale':'Paramètres fictifs '+suffix})
        assert r.status_code==200,r.text
        api.headers['Authorization']='Bearer '+r.json()['access_token']
        yield api


def garde(application):
    c=application['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])


def ajouter_taux(application):
    garde(application)
    with Session(application['engine']) as db:
        t=models.TauxCotisation(annee=2099,code='LAB_'+uuid.uuid4().hex[:12],libelle='Paramètre de laboratoire',
                              taux_sal=.02,taux_pat=.04,plafond=72000)
        db.add(t);db.commit();db.refresh(t)
        return t.id


def instantane(application):
    garde(application)
    with Session(application['engine']) as db:
        return [(t.id,t.annee,t.code,t.libelle,repr(t.taux_sal),repr(t.taux_pat),repr(t.plafond))
                for t in db.query(models.TauxCotisation).order_by(models.TauxCotisation.id).all()]


@pytest.mark.parametrize('champ,valeur',INVALIDES)
def test_api_refuse_sans_modifier_referentiel(application,api_admin,champ,valeur):
    tid=ajouter_taux(application)
    avant=instantane(application)
    payload={'taux_sal':.5,'taux_pat':.6,'plafond':80000,champ:valeur}
    r=api_admin.patch(f'/api/parametres/taux-cotisations/{tid}',content=json.dumps(payload),headers={'Content-Type':'application/json'})
    apres=instantane(application)
    assert (r.status_code,apres)==(422,avant), {'HTTP':r.status_code,'corps':r.text,'avant':avant[-1],'apres':apres[-1]}


@pytest.mark.parametrize('champ,valeur',[('taux_sal',0),('taux_sal',1),('taux_pat',0),('taux_pat',1),('plafond',.01),('plafond',72000),('taux_sal','0.125')])
def test_api_parametre_valide_patch_partiel_preserve_autres_champs(application,api_admin,champ,valeur):
    tid=ajouter_taux(application)
    r=api_admin.patch(f'/api/parametres/taux-cotisations/{tid}',json={champ:valeur})
    assert r.status_code==200,r.text
    valeurs={'taux_sal':.02,'taux_pat':.04,'plafond':72000,champ:float(valeur)}
    assert {k:r.json()[k] for k in valeurs}==valeurs


@pytest.mark.parametrize('payload',[{}, {'taux_sal':None}, {'taux_pat':None}, {'plafond':None}, {'taux_sal':None,'taux_pat':None,'plafond':None}])
def test_api_none_et_omission_ne_suppriment_aucune_valeur(application,api_admin,payload):
    tid=ajouter_taux(application)
    avant=instantane(application)
    r=api_admin.patch(f'/api/parametres/taux-cotisations/{tid}',json=payload)
    assert r.status_code==200,r.text
    assert instantane(application)==avant


def test_api_admin_introuvable_et_non_authentifie(application,api_admin):
    avant=instantane(application)
    r=api_admin.patch('/api/parametres/taux-cotisations/2147483647',json={'taux_sal':.02})
    assert r.status_code==404,r.text
    with httpx.Client(base_url=application['api_url']) as api:
        r=api.patch('/api/parametres/taux-cotisations/2147483647',json={'taux_sal':.02})
        assert r.status_code==401,r.text
    assert instantane(application)==avant


@pytest.mark.parametrize('role',['lecture','comptable'])
def test_api_non_admin_lit_mais_ne_modifie_pas(application,api_admin,role):
    tid=ajouter_taux(application)
    email=uuid.uuid4().hex[:8]+'@example.com';password='LectureParametres2026!'
    r=api_admin.post('/api/utilisateurs',json={'nom':'Utilisateur fictif','email':email,'mot_de_passe':password,'role':role})
    assert r.status_code==201,r.text
    avant=instantane(application)
    with httpx.Client(base_url=application['api_url']) as api:
        r=api.post('/api/auth/login',json={'email':email,'password':password})
        assert r.status_code==200,r.text
        api.headers['Authorization']='Bearer '+r.json()['access_token']
        assert api.get('/api/parametres/taux-cotisations/2099').status_code==200
        r=api.patch(f'/api/parametres/taux-cotisations/{tid}',json={'taux_sal':.2})
        assert r.status_code==403,r.text
    assert instantane(application)==avant


HISTORIQUES = [(champ,valeur) for champ in ('taux_sal','taux_pat','plafond')
               for valeur in (float('nan'),float('inf'),float('-inf'))]
HISTORIQUES += [('taux_sal',None),('taux_pat',None),('taux_sal',1.5),('taux_pat',-.01),('plafond',-1),('plafond',0)]


@pytest.mark.parametrize('index,champ,valeur',[(i,c,v) for i,(c,v) in enumerate(HISTORIQUES)])
def test_api_historique_diagnostique_prep_bloquee_et_correction_explicite(application,api_admin,index,champ,valeur):
    annee=2030+index
    garde(application)
    taux,bareme,deductions=parametres_laboratoire()
    with Session(application['engine']) as db:
        lignes=[models.TauxCotisation(annee=annee,code=t.code,taux_sal=float(t.taux_sal),
                  taux_pat=float(t.taux_pat),plafond=None if t.plafond is None else float(t.plafond)) for t in taux]
        db.add_all(lignes)
        db.add_all([models.BaremeIR(annee=annee,tranche_min=float(t.tranche_min),
                   tranche_max=None if t.tranche_max is None else float(t.tranche_max),
                   taux=float(t.taux),deduction=float(t.deduction)) for t in bareme])
        db.add_all([models.DeductionIR(annee=annee,**vars(d)) for d in deductions])
        db.flush()
        cible=next(t for t in lignes if t.code=='cnss_retraite')
        tid=cible.id
        setattr(cible,champ,valeur)
        db.commit()
    r=api_admin.post('/api/employes',json={'nom':'Salarié laboratoire','poste':'Recette',
                  'salaire_brut':10000,'personnes_charge_ir':0,'date_embauche':'2025-01-01'})
    assert r.status_code==201,r.text
    r=api_admin.get(f'/api/parametres/taux-cotisations/{annee}')
    prep=api_admin.get('/api/employes/cotisations',params={'annee':annee,'mois':10})
    assert (r.status_code,prep.status_code)==(200,200), (r.status_code,r.text,prep.status_code,prep.text)
    lecture=next(t for t in r.json() if t['id']==tid)
    attendu=None if valeur is None or not math.isfinite(valeur) else valeur
    assert lecture[champ]==attendu
    assert any(champ in message for message in lecture['anomalies'])
    if valeur is not None and not math.isfinite(valeur):
        marqueur='NaN' if math.isnan(valeur) else ('Infinity' if valeur>0 else '-Infinity')
        assert any(marqueur in message for message in lecture['anomalies'])
    preparation=prep.json()
    assert preparation['statut']=='bloque' and preparation['totaux'] is None
    assert preparation['blocages'] and all(e['cotisations'] is None for e in preparation['employes'])
    lecture_prep=next(t for t in preparation['parametres']['taux'] if t['id']==tid)
    assert lecture_prep==lecture
    with Session(application['engine']) as db:
        stocke=getattr(db.get(models.TauxCotisation,tid),champ)
        assert math.isnan(stocke) if valeur is not None and math.isnan(valeur) else stocke==valeur
    valide=72000 if champ=='plafond' else .04
    corrige=api_admin.patch(f'/api/parametres/taux-cotisations/{tid}',json={champ:valide})
    assert corrige.status_code==200,corrige.text
    assert corrige.json()[champ]==valide and corrige.json()['anomalies']==[]
    prep=api_admin.get('/api/employes/cotisations',params={'annee':annee,'mois':10})
    assert prep.status_code==200,prep.text
    assert prep.json()['statut']=='simulation' and prep.json()['totaux'] is not None
