"""Reprises explicites : cumul à l'ouverture réelle, sans historique inventé."""
from contextlib import closing
from datetime import date, timedelta
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_registre_immobilisations_cloture_isole import acquisition
from test_dotations_concurrentes_isole import generer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_avances_salaries_isole import originaux
from recette_restauration_consolidee_084 import empreintes_tables


@pytest.mark.parametrize('debut,precedent,ouverture,dotation', [
    ('01-01', None, 4000, 2000),
    ('01-01', '12-31', 4000, 2000),
    ('07-01', None, 3000, 2000),
    ('04-01', None, 4500, 1500),
    ('01-01', '03-31', 4000, 2000),
])
def test_reprise_utilise_ouverture_reelle_sans_dependre_exercice_precedent(
        application, debut, precedent, ouverture, dotation):
    with closing(client(application)[0]) as api:
        annee = date.today().year - 1
        decale = debut == '07-01'
        date_debut = f'{annee - 1 if decale else annee}-{debut}'
        date_fin = f"{annee}-{'06-30' if decale else '12-31'}"
        ok(api.post('/api/exercices', json={
            'annee': annee, 'date_debut': date_debut, 'date_fin': date_fin}), 201)
        if precedent:
            ok(api.post('/api/exercices', json={'annee': annee-1,
                'date_debut': f'{annee-1}-01-01', 'date_fin': f'{annee-1}-{precedent}'}), 201)
        # Acquisition historique dans le registre uniquement. Aucune pièce ancienne
        # n'est fabriquée ; la contrepartie de reprise sera choisie explicitement.
        immo = ok(api.post('/api/immobilisations', params={'generer_ecriture': False},
                           json=acquisition(annee-2)), 201)
        iid = immo['id']; sid = ok(api.get('/api/societe/moi'))['id']
        avant = originaux(application, sid)
        diagnostic = ok(api.get('/api/immobilisations/reconciliation-historique',
                                params={'exercice': annee}))['items'][0]
        assert diagnostic['acquisition']['statut'] == 'manquante_anterieure'
        assert diagnostic['acquisition']['amortissement_ouverture_suggere'] == ouverture
        assert diagnostic['acquisition']['vnc_ouverture_suggeree'] == 10000-ouverture
        assert originaux(application, sid) == avant  # Lire ne crée aucune reprise.
        r = ok(api.post('/api/immobilisations/reconciliation-historique/reconstituer-acquisitions',
                        json={'exercice': annee, 'items': [{'immo_id': iid,
                            'mode': 'reprise_anterieure', 'compte_contrepartie': '4481'}]}))
        eid = r['generees'][0]['ecriture_id']
        with application['engine'].connect() as c:
            e = c.execute(text('SELECT date,exercice,est_validee,reference FROM ecritures WHERE id=:id'), {'id': eid}).one()
            assert e == (date.fromisoformat(date_debut), annee, False, f'RECON-OPEN-{annee}-{iid}')
            lignes = c.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id ORDER BY compte'), {'id': eid}).all()
            assert lignes == [('2355',10000,0), ('28355',0,ouverture), ('4481',0,10000-ouverture)]
        ok(api.post(f'/api/ecritures/{eid}/valider'))
        am = ok(generer(api, 'unitaire', annee, iid))
        assert am['dotation'] == dotation
        ok(api.post(f"/api/ecritures/{am['ecriture_id']}/valider"))
        apres = ok(api.get('/api/immobilisations/reconciliation-historique', params={'exercice': annee}))['items'][0]
        assert apres['amortissement']['ecart_cumule'] == 0
        assert apres['amortissement']['comptabilise_cumule'] == ouverture+dotation
        assert apres['amortissement']['comptabilise_exercice'] == dotation
        # Répéter l'assistant ne duplique ni l'ouverture ni une dette.
        sources = originaux(application,sid)
        refus = api.post('/api/immobilisations/reconciliation-historique/reconstituer-acquisitions',
                         json={'exercice':annee,'items':[{'immo_id':iid,'mode':'reprise_anterieure','compte_contrepartie':'4481'}]})
        assert refus.status_code == 409, refus.text
        assert originaux(application,sid) == sources
        if decale:
            # L'inscription a déjà créé N+1 civil. La clôture doit refuser le
            # trou de juillet à décembre, sans déplacer silencieusement N+1.
            tables_avant = empreintes_tables(application['engine'])
            r = api.post('/api/cloture/cloturer', params={'exercice':annee})
            assert r.status_code == 409 and 'Continuité' in r.text, r.text
            tables_apres = empreintes_tables(application['engine'])
            assert {k:v for k,v in tables_avant.items() if k!='audit_actions'} == {k:v for k,v in tables_apres.items() if k!='audit_actions'}
            assert originaux(application,sid) == sources
            # Décision explicite sur l'exercice suivant encore vide, via l'API
            # administrateur existante ; aucune donnée comptable déplacée.
            ok(api.patch(f'/api/exercices/{annee+1}', json={
                'date_debut':f'{annee}-07-01','date_fin':f'{annee+1}-06-30'}))
        cloture = ok(api.post('/api/cloture/cloturer', params={'exercice':annee}))
        # Le laboratoire applique sa CM existante3000 : aucun paramètre fiscal
        # n'est neutralisé pour faire réussir la clôture.
        assert cloture['resultat_net'] == -dotation-3000
        assert cloture['a_nouveaux_sur'] == annee+1
        assert api.get('/api/fec/export', params={'exercice':annee}).status_code == 200
        avec_cloture = originaux(application,sid)
        for table,lignes in sources.items():
            assert all(l in avec_cloture[table] for l in lignes)
        with application['engine'].connect() as c:
            an = c.execute(text('SELECT id,date FROM ecritures WHERE societe_id=:s AND reference=:r'),
                           {'s':sid,'r':f'AN-{annee+1}'}).one()
            assert an.date == date.fromisoformat(date_fin)+timedelta(days=1)
            report = c.execute(text("SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:id AND compte IN ('2355','28355','4481') ORDER BY compte"), {'id':an.id}).all()
            assert report == [('2355',10000,0),('28355',0,ouverture+dotation),('4481',0,10000-ouverture)]
