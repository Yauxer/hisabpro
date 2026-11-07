"""089 : identité native et gardes de lettrage, vrai SQL LOGIN/API sur nonce."""
from datetime import date
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from routers import exercices

from recette_installation_vierge import BACK
from test_permissions_banque_releves_postgres import (
    cible as cible_banque, cible_commerciale, cible_documents,
)
from test_permissions_documents_commerciaux_postgres import inscrire, ok, acl
from test_permissions_acomptes_avoirs_postgres import originaux
from test_complements_structure_postgres import refuser
from recette_restauration_consolidee_084 import empreintes_tables

SQL = '089_lettrage_identite_auxiliaire.sql'


@pytest.fixture(scope='module')
def cible(cible_banque):
    c = cible_banque
    c['client'].app.include_router(exercices.router)
    def triggers():
        with c['owner'].connect() as db:
            return db.execute(text("SELECT tgname,tgenabled,tgdeferrable,tginitdeferred,pg_get_triggerdef(oid) "
                "FROM pg_trigger WHERE tgrelid='lettrages_comptables'::regclass AND NOT tgisinternal ORDER BY tgname")).all()
    before, tables = acl(c['owner']), empreintes_tables(c['owner'])
    gardes = triggers()
    c['migration'](SQL)
    c['migration'](SQL)
    assert acl(c['owner']) == before
    assert empreintes_tables(c['owner']) == tables and triggers() == gardes
    c['triggers089'] = gardes
    yield c


def tiers(api, nature='client'):
    return ok(api.post('/api/tiers', json={'nom': 'Tiers fictif089-' + uuid.uuid4().hex[:8],
        'type': nature, 'categorie_fiscale': 'particulier'}), 201)


def piece(api, tid, label, *, montant=120, credit=False, compte='3421', annee=None, definitive=True):
    jour = date.today() if annee is None else date(annee, 6, 15)
    e = ok(api.post('/api/ecritures', json={'date': jour.isoformat(), 'journal': 'OD',
        'reference': 'TEST089-' + uuid.uuid4().hex[:10], 'libelle': 'Pièce technique fictive089',
        'est_validee': definitive, 'lignes': [
            {'compte': compte, 'tiers_id': tid, 'libelle': label,
             'debit': 0 if credit else montant, 'credit': montant if credit else 0},
            {'compte': '5141', 'debit': montant if credit else 0,
             'credit': 0 if credit else montant}]}), 201)
    return next(l['id'] for l in e['lignes'] if l['compte'] == compte)


def nouveau(cible, tag):
    _, user = inscrire(cible, tag)
    return cible['client'], user


def inserer_groupe(cible, sid, uid, ids, code):
    # Le commit réel déclenche aussi le contrôle différé d'équilibre049.
    with cible['runtime'].begin() as db:
        for lid in ids:
            db.execute(text('INSERT INTO lettrages_comptables '
                '(societe_id,ligne_ecriture_id,code,date_lettrage,created_by,actif) '
                'VALUES(:sid,:lid,:code,now(),:uid,true)'),
                {'sid': sid, 'lid': lid, 'code': code, 'uid': uid})


@pytest.mark.parametrize('nature,compte', [('client','3421'), ('fournisseur','4411')])
def test089_meme_tiers_libelles_distincts_et_delettrage_sans_modifier_origines(cible,nature,compte):
    api, user = nouveau(cible, 'identite089-' + nature)
    t = tiers(api, nature)
    ids = [piece(api,t['id'],'Report à nouveau du tiers',compte=compte),
           piece(api,t['id'],'Règlement avec libellé distinct',credit=True,compte=compte)]
    before = originaux(cible,user['societe_id'])
    result = ok(api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids': ids,'code':'NAT'}))
    assert result['nb'] == 2
    assert originaux(cible,user['societe_id']) == before
    ok(api.post('/api/lettrage/comptable/delettrer/NAT'))
    assert originaux(cible,user['societe_id']) == before
    with cible['runtime'].connect() as db:
        rows = db.execute(text("SELECT actif,date_delettrage,delettre_par FROM lettrages_comptables "
                               "WHERE societe_id=:sid AND code='NAT'"), {'sid':user['societe_id']}).all()
        assert len(rows)==2 and all(not r.actif and r.date_delettrage and r.delettre_par==user['id'] for r in rows)
    assert api.post('/api/lettrage/comptable/lettrer', json={'ligne_ids':ids,'code':'NAT'}).status_code==409


@pytest.mark.parametrize('cas', ['tiers_distincts','comptes_distincts','exercices_distincts',
                                'desequilibre','brouillon','exercice_clos','societe_distincte'])
def test089_sql_refuse_groupe_invalide_et_transaction_atomique(cible,cas):
    api,user = nouveau(cible, cas+'089')
    t = tiers(api)
    annee=None
    if cas=='exercices_distincts':
        annee=date.today().year-1
        ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01',
                                         'date_fin':f'{annee}-12-31'}),201)
    autre = tiers(api,'fournisseur' if cas=='comptes_distincts' else 'client')
    id1=piece(api,t['id'],'Même libellé pour tester la vraie identité')
    id2=piece(api,autre['id'] if cas in {'tiers_distincts','comptes_distincts'} else t['id'],
        'Même libellé pour tester la vraie identité',credit=True,
        compte='4411' if cas=='comptes_distincts' else '3421',annee=annee,
        montant=119 if cas=='desequilibre' else 120,definitive=cas!='brouillon')
    sid=user['societe_id']
    if cas=='societe_distincte':
        _, autre_user=nouveau(cible,'societe-etrangere089')
        sid=autre_user['societe_id']
    if cas=='exercice_clos':
        # État synthétique de garde, distinct du vrai parcours annuel444.
        with cible['owner'].begin() as db:
            db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:sid AND annee=:an"),
                       {'sid':sid,'an':date.today().year})
    before=empreintes_tables(cible['owner'])
    with pytest.raises(DBAPIError) as error:
        inserer_groupe(cible,sid,user['id'],[id1,id2],'NEG')
    assert error.value.orig.pgcode=='23514'
    assert empreintes_tables(cible['owner'])==before


def test089_rejeu_sur_groupes_existants_conserve_toutes_les_tables_et_acl(cible):
    api,user=nouveau(cible,'rejeu089')
    t=tiers(api)
    ids=[piece(api,t['id'],'Source initiale'),piece(api,t['id'],'Source bancaire',credit=True)]
    ok(api.post('/api/lettrage/comptable/lettrer',json={'ligne_ids':ids,'code':'REP'}))
    before=empreintes_tables(cible['owner']),acl(cible['owner'])
    cible['migration'](SQL)
    assert (empreintes_tables(cible['owner']),acl(cible['owner']))==before
    refuser(cible['runtime'],"UPDATE lettrages_comptables SET code='AUTRE' WHERE code='REP'",'23514')
    refuser(cible['runtime'],"DELETE FROM lettrages_comptables WHERE code='REP'",'42501')
    assert (empreintes_tables(cible['owner']),acl(cible['owner']))==before
