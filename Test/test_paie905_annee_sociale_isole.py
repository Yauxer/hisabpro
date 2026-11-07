"""Douze mois explicites : aucune annualisation d'un mois ou IR inventé."""
from pathlib import Path
from decimal import Decimal as D
import json
from test_paie901_ir_annuel_isole import (
    application,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,ok,comptabilite)
from test_paie899_social_isole import salarie,rubrique,gain,brut,creer,approuver,calculer,C,T

R=Path(__file__).resolve().parents[1]


def test_905_douze_mois_reels_fictifs_totaux_et_historique(application,equipe):
    eq=equipe;eid,_=salarie(eq,m='P905');rid=rubrique(eq)
    for code,assiette,ts,tp,plafond,composant in [('B1_FICTIF','CNSS','1','2','6000.00','GARANTIE_B1'),('B2_FICTIF','AMO','3','4',None,'GARANTIE_B2')]:
        v=creer(eq,code,'REGIME_SOC899',assiette=assiette,taux_salarial=ts,taux_patronal=tp,plafond_mode='MONTANT' if plafond else 'SANS',plafond=plafond,composants=[composant]);ok(approuver(eq,v))
    avant=comptabilite(application,eq['sid']);mois=[];premier=None
    for numero in range(1,13):
        periode=f'2026-{numero:02d}-01'
        gain(eq,eid,rid,periode=periode,date_effet=f'2026-{numero:02d}-15',source_reference=f'GAIN-P905-{numero:02d}-FICTIF')
        q=brut(eq,[eid],periode=periode);r=calculer(eq,eid,q);c=r['contenu'];e=c['employes'][0]
        assert c['complet_pour_social'] and c['totaux']['brut']=='9800.11'
        assert c['totaux']['cotisations_salariales']=='354.00' and c['totaux']['cotisations_patronales']=='512.00'
        assert c['totaux']['ir'] is None and c['totaux']['net_a_payer'] is None and not c['paie_definitive_autorisee']
        mois.append({'periode':periode,'brut':c['totaux']['brut'],'cnss':e['assiettes']['CNSS']['montant'],'amo':e['assiettes']['AMO']['montant'],'salarial':c['totaux']['cotisations_salariales'],'patronal':c['totaux']['cotisations_patronales'],'branche_B2_salarial':e['branches'][1]['salarial'],'brut_id':q['id'],'social_id':r['id']})
        if premier is None:premier=(q,r)
    totaux={k:format(sum(D(m[k]) for m in mois),'.2f') for k in ['brut','cnss','amo','salarial','patronal','branche_B2_salarial']}
    assert totaux=={'brut':'117601.32','cnss':'114001.32','amo':'117601.32','salarial':'4248.00','patronal':'6144.00','branche_B2_salarial':'3528.00'}
    assert D(totaux['amo'])*D('.03')==D('3528.0396') #ne pas remplacer la somme des12lignes arrondies.
    q,r=premier
    assert ok(eq['a'].get(f'{T}/simulations/{q["id"]}'))['contenu']==q['contenu']
    assert ok(eq['a'].get(f'{C}/{r["id"]}'))['contenu']==r['contenu']
    assert calculer(eq,eid,q)['contenu']['totaux']['cotisations_salariales']=='354.00' #les autres mois ne rendent pas janvier périmé.
    assert comptabilite(application,eq['sid'])==avant
    (R/'.codex-tests/paie905_annee_preuve.json').write_text(json.dumps({'donnees_reelles':False,'mois_explicitement_prepares':12,'mois':mois,'totaux':totaux,'arrondis_mensuels_conserves':True,'anciens_snapshots_intacts':True,'comptabilite_inchangee':True,'IR_net_calcules':False},ensure_ascii=False,indent=2),encoding='utf8')
