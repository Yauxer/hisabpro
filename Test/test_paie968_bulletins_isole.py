"""968 — bulletins, avances, comptabilisation, paiements et états de paie. PostgreSQL nonce, données fictives."""
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_paie919_rattachement_isole import (
    application122,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,ok)
from test_paie921_mensuel_isole import application as application124, application123, preparation, M
from test_paie921_mensuel_unitaire import demande
from postgres_isole import verifier_cible_isolee

R = Path(__file__).resolve().parents[1]
B = '/api/employes/personnel/paie'


def installer(app):
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    raw = app['engine'].raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cur:
            cur.execute((R / 'hisabpro-backend/131_paie_bulletins.sql').read_text(encoding='utf8'))
    finally:
        raw.close()


@pytest.fixture(scope='module')
def application(application124):
    installer(application124)
    installer(application124)  # rejouable
    yield application124


def source(eq):
    eid, _, p = preparation(eq)
    return eid, ok(eq['a'].post(M, json=demande(p['id'], eid)), 201)


def corps(controle_id, **kw):
    return {'controle_id': controle_id, 'ir_retenu': '497.02', 'retenues_avances': [], 'cle_idempotence': str(uuid4()),
            'motif': 'Bulletin fictif968', **kw}


def lignes(app, ecriture_id):
    with app['engine'].connect() as db:
        e = db.execute(text('SELECT journal,est_validee,source FROM ecritures WHERE id=:i'), {'i': ecriture_id}).mappings().one()
        rows = db.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:i'), {'i': ecriture_id}).mappings().all()
    total = {}
    for r in rows:
        total[r['compte']] = total.get(r['compte'], Decimal(0)) + Decimal(str(r['debit'])) - Decimal(str(r['credit']))
    return e, total


def test_968_bulletin_avance_comptabilisation_paiement_etats(application, equipe):
    eq = equipe
    eid, c = source(eq)
    ap = ok(eq['a'].get(B + '/bulletins/apercu', params={'controle_id': c['id']}))
    assert ap['brut_imposable'] == '9300.11' and ap['ir_propose'] == '497.02'
    net_sans_avance = Decimal(ap['brut']) - Decimal(ap['cotisations_salariales']) - Decimal('497.02')
    assert net_sans_avance > 400
    assert ap['ir_arithmetique'] == '497.0240' and ap['deja_etabli'] is None
    # 977 : la caisse est alimentée avant le versement de l'avance en espèces.
    ok(eq['a'].post('/api/ecritures', json={'date': '2026-11-01', 'journal': 'CA', 'libelle': 'Apport en caisse FICTIF968', 'est_validee': True,
        'lignes': [{'compte': '5161', 'libelle': 'Caisse', 'debit': 5000, 'credit': 0}, {'compte': '1111', 'libelle': 'Apport', 'debit': 0, 'credit': 5000}]}), 201)
    av = ok(eq['a'].post(B + '/avances', json={'employe_id': eid, 'nature': 'AVANCE', 'date_octroi': '2026-11-03', 'montant': '1000.00',
                                                'retenue_mensuelle': '400.00', 'mode_versement': 'especes', 'motif': 'Avance fictive968'}), 201)
    va = ok(eq['a'].post(f'{B}/avances/{av["id"]}/comptabiliser'), 201)
    e, t = lignes(application, va['ecriture_id'])
    assert e['journal'] == 'CA' and not e['est_validee'] and t == {'3431': Decimal('1000.00'), '5161': Decimal('-1000.00')}
    # IR différent du calcul sans justification, retenue supérieure au solde, valeurs non exactes : refusés.
    assert eq['a'].post(B + '/bulletins', json=corps(c['id'], ir_retenu='500.00')).status_code == 400
    assert eq['a'].post(B + '/bulletins', json=corps(c['id'], retenues_avances=[{'avance_id': av['id'], 'montant': '1000.01'}])).status_code == 409
    for bad in [{'ir_retenu': 497.02}, {'ir_retenu': '497.021'}, {'net_a_payer': '1.00'}]:
        assert eq['a'].post(B + '/bulletins', json=corps(c['id'], **bad)).status_code == 422
    d = corps(c['id'], retenues_avances=[{'avance_id': av['id'], 'montant': '400.00'}])
    b = ok(eq['a'].post(B + '/bulletins', json=d), 201)
    k = b['contenu']
    assert Decimal(k['net_a_payer']) == net_sans_avance - 400 and k['total_avances'] == '400.00' and k['ir_retenu'] == '497.02'
    assert Decimal(k['cout_employeur']) == Decimal(k['brut']) + Decimal(k['cotisations_patronales'])
    assert k['sources']['controle'] == {'id': c['id'], 'empreinte': c['empreinte']}
    assert ok(eq['a'].post(B + '/bulletins', json=d), 201)['reutilise'] is True
    assert eq['a'].post(B + '/bulletins', json=corps(c['id'])).status_code == 409  # un seul bulletin valide par mois
    assert eq['l'].post(B + '/bulletins', json=corps(c['id'])).status_code == 403
    solde = next(a for a in ok(eq['a'].get(B + '/avances'))['elements'] if a['id'] == av['id'])
    assert Decimal(solde['solde']) == Decimal('600.00') and Decimal(solde['rembourse']) == Decimal('400.00')
    assert eq['a'].post(f'{B}/avances/{av["id"]}/annuler', json={'motif': 'Essai fictif'}).status_code == 409
    # Bulletin figé en base.
    for sql in ["UPDATE paie_bulletins SET net_a_payer=1 WHERE id=:i", "DELETE FROM paie_bulletins WHERE id=:i"]:
        with pytest.raises(DBAPIError), application['engine'].begin() as db:
            db.execute(text(sql), {'i': b['id']})
    # Paiement impossible avant comptabilisation.
    assert eq['a'].post(B + '/paiements', json={'bulletin_ids': [b['id']], 'date_paiement': '2026-12-02', 'mode': 'virement'}).status_code == 409
    r = ok(eq['a'].post(B + '/comptabiliser', json={'periode': '2026-11-01', 'date_ecriture': '2026-11-30'}), 201)
    e, t = lignes(application, r['ecriture_id'])
    pat = Decimal(k['cotisations_patronales'])
    assert e['journal'] == 'SA' and e['source'] == 'paie' and not e['est_validee'] and sum(t.values()) == 0
    attendu = {'6171': Decimal(r['totaux']['brut']), '6174': Decimal(r['totaux']['patronal']), '4441': -(Decimal(r['totaux']['salarial']) + Decimal(r['totaux']['patronal'])),
               '44525': -Decimal(r['totaux']['ir']), '3431': -Decimal(r['totaux']['avances']), '4432': -Decimal(r['totaux']['net'])}
    assert t == {c_: v for c_, v in attendu.items() if v}
    assert Decimal(r['totaux']['net']) >= Decimal(k['net_a_payer']) and Decimal(r['totaux']['patronal']) >= pat
    assert eq['a'].post(B + '/comptabiliser', json={'periode': '2026-11-01', 'date_ecriture': '2026-11-30'}).status_code == 409
    assert eq['a'].post(f'{B}/bulletins/{b["id"]}/annuler', json={'motif': 'Essai fictif'}).status_code == 409
    p = ok(eq['a'].post(B + '/paiements', json={'bulletin_ids': [b['id']], 'date_paiement': '2026-12-02', 'mode': 'virement', 'reference': 'VIR-FICTIF968'}), 201)
    e, t = lignes(application, p['ecriture_id'])
    net = Decimal(k['net_a_payer'])
    assert p['total'] == k['net_a_payer'] and e['journal'] == 'BQ' and t == {'4432': net, '5141': -net}
    assert eq['a'].post(B + '/paiements', json={'bulletin_ids': [b['id']], 'date_paiement': '2026-12-02', 'mode': 'virement'}).status_code == 409
    lu = ok(eq['a'].get(f'{B}/bulletins/{b["id"]}'))
    assert lu['contenu'] == k and lu['paiement_mode'] == 'virement' and lu['societe']['raison_sociale']
    etats = ok(eq['a'].get(B + '/etats', params={'annee': 2026}))
    nov = next(m for m in etats['mois'] if m['periode'] == '2026-11')
    assert nov['payes'] >= 1 and nov['comptabilises'] >= 1 and any(x['id'] == b['id'] for x in etats['bulletins'])
    assert Decimal(nov['organismes_sociaux']) == Decimal(nov['cotisations_salariales']) + Decimal(nov['cotisations_patronales'])
    assert eq['a'].get(B + '/etats', params={'annee': 2026}).headers['cache-control'] == 'no-store'


def test_968_brouillon_supprime_libere_puis_annulation_et_refaire(application, equipe):
    eq = equipe
    eid, c = source(eq)
    b = ok(eq['a'].post(B + '/bulletins', json=corps(c['id'])), 201)
    with application['engine'].connect() as db:
        deja = db.scalar(text("SELECT count(*) FROM paie_bulletins WHERE periode='2026-11-01' AND statut='VALIDE' AND ecriture_id IS NULL"))
    assert deja >= 1
    r = ok(eq['a'].post(B + '/comptabiliser', json={'periode': '2026-11-01', 'date_ecriture': '2026-11-30'}), 201)
    assert eq['a'].delete(f'/api/ecritures/{r["ecriture_id"]}').status_code == 204
    assert ok(eq['a'].get(f'{B}/bulletins/{b["id"]}'))['ecriture_id'] is None
    ok(eq['a'].post(f'{B}/bulletins/{b["id"]}/annuler', json={'motif': 'Correction fictive968'}))
    assert eq['a'].post(f'{B}/bulletins/{b["id"]}/annuler', json={'motif': 'Encore'}).status_code == 409
    nouveau = ok(eq['a'].post(B + '/bulletins', json=corps(c['id'], ir_retenu='497.00', reference_ecart_ir='ARRONDI-FICTIF968')), 201)
    n = nouveau['contenu']
    assert n['reference_ecart_ir'] == 'ARRONDI-FICTIF968' and Decimal(n['net_a_payer']) == Decimal(n['brut']) - Decimal(n['cotisations_salariales']) - Decimal('497.00')
    statuts = {x['id']: x['statut'] for x in ok(eq['a'].get(B + '/bulletins', params={'annee': 2026}))['elements']}
    assert statuts[b['id']] == 'ANNULE' and statuts[nouveau['id']] == 'VALIDE'
