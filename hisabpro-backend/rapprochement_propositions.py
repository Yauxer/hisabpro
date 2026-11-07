"""Correspondances exactes proposées; aucun choix arbitraire ou changement comptable."""
from collections import defaultdict
from decimal import Decimal,InvalidOperation
import hashlib,json

def montant(v):
    if isinstance(v,bool):return None
    try:
        n=Decimal(str(v))
        if not n.is_finite() or n<0 or n!=n.quantize(Decimal('0.01')):return None
        return n
    except (ValueError,TypeError,InvalidOperation):return None

def construire(situation):
    """L'unicité porte sur tous les candidats, y compris ceux des lignes ambiguës."""
    sources=[]
    for e in situation['ecritures']:
        d,c=montant(e['debit']),montant(e['credit'])
        if e.get('rapprochee') or d is None or c is None or not e.get('reference'):continue
        sens='credit' if d>0 and c==0 else 'debit' if c>0 and d==0 else None
        if sens:
            sources.append({'cle':'L:'+str(e['ligne_id']),'date':e['date'],'reference':e['reference'].strip(),
                'sens':sens,'montant':d+c,'ecriture_ligne_ids':[e['ligne_id']],
                'ecriture_ligne_id':e['ligne_id'],'operation_id':None,'libelle':e['numero_ecriture']})
    par_id={e['ligne_id']:e for e in situation['ecritures']}
    for v in situation.get('ventilations',[]):
        ids=v['ecriture_ligne_ids'];n=montant(v['montant'])
        if n is None or n<=0 or not v.get('reference') or not ids or any(i not in par_id or par_id[i].get('rapprochee') for i in ids):continue
        sources.append({'cle':'VT:'+v['operation_id'],'date':v['date'],'reference':v['reference'].strip(),
            'sens':v['sens'],'montant':n,'ecriture_ligne_ids':ids,'ecriture_ligne_id':None,
            'operation_id':v['operation_id'],'libelle':f"Ventilation — {v['nb_reglements']} règlements"})
    correspondances={};utilisations=defaultdict(set);releves={};sans=[]
    for r in situation['lignes_releve']:
        if r['rapprochee']:continue
        releves[r['id']]=r;n=montant(r['montant']);ref=(r.get('libelle') or '').strip()
        matchs=[s for s in sources if n is not None and n>0 and ref and s['date']==r['date']
            and s['sens']==r['sens'] and s['montant']==n and s['reference']==ref]
        correspondances[r['id']]=matchs
        for s in matchs:
            for lid in s['ecriture_ligne_ids']:utilisations[lid].add(r['id'])
        if not matchs:sans.append({'releve_id':r['id'],'raison':'reference_absente' if not ref else 'aucune_correspondance_exacte'})
    propositions=[];ambigues=[]
    for rid,matchs in correspondances.items():
        if not matchs:continue
        if len(matchs)!=1 or any(len(utilisations[lid])!=1 for s in matchs for lid in s['ecriture_ligne_ids']):
            ambigues.append({'releve_id':rid,'nb_candidats':len(matchs),'raison':'correspondance_non_unique'});continue
        r=releves[rid];s=matchs[0]
        propositions.append({'releve_id':rid,'date':r['date'],'reference':s['reference'],
            'montant':float(s['montant']),'sens':s['sens'],'ecriture_ligne_id':s['ecriture_ligne_id'],
            'ecriture_ligne_ids':s['ecriture_ligne_ids'],'operation_id':s['operation_id'],'libelle':s['libelle']})
    empreinte=hashlib.sha256(json.dumps(situation,sort_keys=True,ensure_ascii=False,default=str).encode('utf-8')).hexdigest()
    return {'compte':situation['compte'],'date_debut':situation['date_debut'],'date_fin':situation['date_fin'],
        'empreinte':empreinte,'lecture_seule':situation['lecture_seule'],
        'propositions':propositions,'ambigues':ambigues,'sans_correspondance':sans}
