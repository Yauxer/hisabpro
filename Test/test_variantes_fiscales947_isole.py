"""Oracles exacts du cahier et refus réels ; données de laboratoire uniquement."""
from contextlib import closing
import pytest
from sqlalchemy import text
from fiscal947_support import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, copie, lire, ajouter_deficit, reprise_provision, deduction,
    ecriture, core, ok, D, preuve,
)


def test_947_deficit_documente_12000_sans_double_consommation(application):
    with closing(client(application)[0]) as api:
        sid = copie(api, application, reprise=True)
        avant = core(application, sid)
        d = ajouter_deficit(api)
        proposition = lire(api)
        assert D(str(proposition['deficits']['total_propose'])) == 12000
        assert not proposition['deficits']['confirmation_a_jour']
        ok(api.post('/api/fiscalite/is/2025/deficits/confirmer-imputation'))
        for _ in range(2):
            v = lire(api)
            assert v['deficits']['confirmation_a_jour']
            assert D(str(v['calcul']['benefice_fiscal_imposable'])) == 121830
            assert D(str(v['calcul']['is_theorique'])) == D('21320.25')
            assert D(str(v['liquidation']['solde_a_payer'])) == D('21120.25')
        with application['engine'].connect() as db:
            lignes = db.execute(text('SELECT montant_ordinaire,montant_amortissements FROM fiscal_deficit_imputations WHERE societe_id=:s AND deficit_id=:d'), {'s': sid, 'd': d['id']}).all()
        assert lignes == [(D('10000'), D('2000'))]
        assert core(application, sid) == avant and not v['liquidation']['confirmee']
        preuve('deficit', nonce=application['cluster']['nonce'], source=d, situation=v,
               ecritures_inchangees=True, imputation_unique=lignes)


def test_947_reprise_taxee_deduction_seulement_apres_justification(application):
    with closing(client(application)[0]) as api:
        sid = copie(api, application)
        initial = core(application, sid)
        e = reprise_provision(api)
        avant = core(application, sid)
        assert len(avant) == len(initial) + 1 and all(x in avant for x in initial)
        sans = lire(api)
        assert D(str(sans['calcul']['resultat_comptable_avant_is'])) == 130830
        assert D(str(sans['calcul']['benefice_fiscal_imposable'])) == 134830
        assert D(str(sans['calcul']['deductions'])) == 0
        r = deduction(api)
        v = lire(api)
        assert D(str(v['calcul']['benefice_fiscal_imposable'])) == 133830
        assert D(str(v['calcul']['is_theorique'])) == D('23420.25')
        assert D(str(v['calcul']['deductions'])) == 1000 and core(application, sid) == avant
        assert not v['liquidation']['confirmee']
        preuve('deduction', nonce=application['cluster']['nonce'], reprise=e['id'], retraitement=r,
               avant_justification=sans, apres=v, originaux_preserves=True)


@pytest.mark.parametrize('cas', ['029', '030', '031', '032', '033'])
def test_947_refus_fiscaux_exacts_sans_mutation(application, cas):
    with closing(client(application)[0]) as api:
        sid = copie(api, application, minimale=True, qualifie=cas != '029', avec_credit=False)
        if cas == '033':
            ecriture(api, 'IS-INCORRECT-FICTIF947', [{'compte': '6705', 'debit': 1},
                {'compte': '4453', 'credit': 1}], piece=True)
        avant = core(application, sid)
        debut = lire(api)
        if cas == '029':
            provision = next(x for x in debut['retraitements_a_confirmer'] if x['id'] == 'check:provisions')
            assert '61955' in provision['compte_source'] and '61964' in provision['compte_source']
            assert D(str(provision['montant_detecte'])) == 3500
            assert provision['montant'] is None and provision['impacte_calcul'] is False
            assert D(str(debut['calcul']['reintegrations'])) == 500
            assert D(str(debut['calcul']['benefice_fiscal_imposable'])) == 130330
            r = api.get('/api/fiscalite/is/2025')
            assert r.status_code == 200
        elif cas == '030':
            r = api.post('/api/fiscalite/is/2025/credits', json={'type': 'pprf',
                'montant': 200, 'montant_deja_impute_acomptes': 201, 'reference': 'NEG030-FICTIF'})
            assert r.status_code == 422, r.text
        elif cas == '031':
            r = api.put('/api/fiscalite/is/2025/parametres', json={
                'acomptes_reference_forcee': 20000, 'acomptes_justification_reference_forcee': ''})
            assert r.status_code == 422, r.text
        elif cas == '032':
            r = api.post('/api/fiscalite/is/2025/liquidation/confirmer')
            assert r.status_code == 409 and 'exercice comptable' in r.text, r.text
        else:
            c = debut['comptabilisation_is']
            assert not c['coherente'] and D(str(c['comptabilise'])) == 1
            assert D(str(debut['calcul']['is_theorique'])) == D('23420.25')
            r = api.post('/api/cloture/cloturer', params={'exercice': 2025})
            assert r.status_code == 409 and 'comptabilisation' in r.text, r.text
        fin = lire(api)
        assert core(application, sid) == avant and not fin['liquidation']['confirmee']
        for cle in ['calcul', 'parametres', 'credits_is', 'retraitements']:
            assert fin[cle] == debut[cle], cle
        preuve('neg' + cas, fiche='HP-NEG-' + cas, statut_http=r.status_code,
               message=r.text, situation=fin, ecritures_et_donnees_fiscales_inchangees=True)
