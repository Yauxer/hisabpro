"""Contrat de lecture du détail : snapshot vérifié, droits, pas de mutation."""
from copy import deepcopy
from sqlalchemy import text, update
import models
from services.balance_preparation_export_service import presentation_bilan
from test_balance_preparations import api, donnees


def test_679_detail_reprend_snapshot_et_presentation_des_exports(api):
    client, engine, identity = api
    row = client.post('/api/etats/liasse/balance/dossiers',json=donnees()).json()
    avant = deepcopy(row)
    identity['role'] = 'lecture'
    path = f'/api/etats/liasse/balance/dossiers/{row["id"]}/detail'
    response = client.get(path)
    assert response.status_code == 200,response.text
    detail = response.json()
    assert detail['id'] == row['id'] and detail['empreinte_sha256'] == row['empreinte_sha256']
    assert detail['bilan'] == presentation_bilan(row)
    assert detail['balances'] == {'n':row['contenu']['sources']['n'],'n1':None}
    assert detail['bilan']['actif'][-1]['valeurs'] == [100,0,100,None]
    assert client.get(path.removesuffix('/detail')).json() == avant
    identity.update(id=2,societe_id=2)
    assert client.get(path).status_code == 404


def test_679_detail_refuse_snapshot_altere(api):
    client, engine, _ = api
    row = client.post('/api/etats/liasse/balance/dossiers',json=donnees()).json()
    contenu = row['contenu']; contenu['preparation']['etats']['bilan']['actif']['total']['net']=99
    with engine.begin() as db:
        db.execute(update(models.LiasseBalancePreparation).values(contenu=contenu))
    response = client.get(f'/api/etats/liasse/balance/dossiers/{row["id"]}/detail')
    assert response.status_code == 409 and 'Empreinte' in response.text
