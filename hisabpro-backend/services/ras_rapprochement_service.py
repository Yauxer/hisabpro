"""Liens documentaires vers des pièces existantes, sans création comptable/fiscale."""
from decimal import Decimal
import hashlib
import hmac
import json

from fastapi import HTTPException
from sqlalchemy import text

NOTE = ('Rapprochement comptable déclaré vers une pièce déjà validée. Le montant non rapproché '
        'est une capacité documentaire, pas une dette fiscale ni un reste à verser. '
        'Aucun paiement effectif, dépôt DGI, droit à imputation ou remboursement n’est certifié. '
        'Le retrait d’un rapprochement ne contrepassera aucune écriture.')


def empreinte(faits):
    return hashlib.sha256(json.dumps(faits,sort_keys=True,ensure_ascii=False,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()


def montant(v):
    d=Decimal(str(v))
    if not d.is_finite() or d<0 or d!=d.quantize(Decimal('.01')):
        raise HTTPException(409,'Montant source non représentable au centime : vérifiez la pièce.')
    return format(d,'.2f')


def disponible(db):
    if not db.scalar(text("SELECT to_regclass('public.ras_tva_rapprochements') IS NOT NULL")):
        raise HTTPException(503,'Rapprochement documentaire indisponible : migration103 manuelle requise. Aucune migration automatique.')


def verrou(db,sid):
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('hisabpro_ras_rapprochement'),:s)"),{'s':sid})


def capture(db,sid,cid):
    disponible(db)
    if db.scalar(text('SELECT devise FROM societes WHERE id=:s'),{'s':sid})!='MAD':
        raise HTTPException(409,'Ce rapprochement est limité aux comptabilités explicitement tenues en MAD ; aucune conversion de devise n’est présumée.')
    c=db.execute(text('''SELECT c.*,f.type AS nature,e.est_validee AS od_validee,
        EXISTS(SELECT 1 FROM ras_reglement_annulations a WHERE a.capture_id=c.id) AS annulee
        FROM ras_reglement_captures c
        JOIN ras_tva_reglement_details d ON d.capture_id=c.id AND d.societe_id=c.societe_id
        JOIN factures f ON f.id=c.facture_id AND f.societe_id=c.societe_id
        JOIN ecritures e ON e.id=c.ecriture_id AND e.societe_id=c.societe_id
        WHERE c.id=:c AND c.societe_id=:s'''),{'c':cid,'s':sid}).mappings().first()
    if not c:raise HTTPException(404,'Capture TVA introuvable dans cette société.')
    if c['nature']!='achat':raise HTTPException(409,'Ce rapprochement concerne uniquement les retenues opérées sur achats.')
    montant(c['montant'])
    return c


def piece(db,sid,eid):
    e=db.execute(text('SELECT id,date,journal,reference,numero_ecriture,est_validee,source FROM ecritures WHERE id=:e AND societe_id=:s'),{'e':eid,'s':sid}).mappings().first()
    if not e:raise HTTPException(404,'Écriture introuvable dans cette société.')
    lignes=db.execute(text('SELECT id,compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:e ORDER BY id'),{'e':eid}).mappings().all()
    return {**dict(e),'date':e['date'].isoformat(),
        'lignes':[{'id':l['id'],'compte':l['compte'],'debit':montant(l['debit']),'credit':montant(l['credit'])} for l in lignes]}


def deja(db,sid,cid=None,eid=None,compte=None):
    if cid is not None:
        where='r.capture_id=:c'
    else:
        where='r.ecriture_id=:e AND c.compte_destination=:compte'
    return db.scalar(text('''SELECT coalesce(sum(r.montant),0) FROM ras_tva_rapprochements r
        JOIN ras_reglement_captures c ON c.id=r.capture_id AND c.societe_id=r.societe_id
        WHERE r.societe_id=:s AND '''+where+'''
        AND NOT EXISTS(SELECT 1 FROM ras_tva_rapprochement_retraits x WHERE x.rapprochement_id=r.id)'''),
        {'s':sid,'c':cid,'e':eid,'compte':compte})


def lire(db,sid,cid):
    c=capture(db,sid,cid)
    rows=db.execute(text('''SELECT r.*,x.motif AS motif_retrait,x.created_at AS retire_le,
        x.created_by AS retire_par FROM ras_tva_rapprochements r
        LEFT JOIN ras_tva_rapprochement_retraits x ON x.rapprochement_id=r.id
        WHERE r.capture_id=:c AND r.societe_id=:s ORDER BY r.id DESC'''),{'c':cid,'s':sid}).mappings().all()
    resultat=[]
    for r in rows:
        if not hmac.compare_digest(empreinte(r['faits']),r['empreinte_sha256']):
            raise HTTPException(409,'Empreinte du rapprochement incohérente ; vérifiez son intégrité.')
        diagnostics=[]
        try:
            actuel=piece(db,sid,r['ecriture_id'])
            if actuel!=r['faits']['piece']:diagnostics.append('Pièce source différente de celle conservée lors du rapprochement.')
        except HTTPException:diagnostics.append('Pièce source actuellement indisponible ou non représentable.')
        if db.scalar(text('SELECT EXISTS(SELECT 1 FROM ecritures WHERE contrepassation_de_id=:e)'),{'e':r['ecriture_id']}):
            diagnostics.append('Pièce source contrepassée : rapprochement à revoir, sans retrait automatique.')
        resultat.append({'id':r['id'],'ecriture_id':r['ecriture_id'],'montant':montant(r['montant']),
            'faits':r['faits'],'empreinte_sha256':r['empreinte_sha256'],'created_by':r['created_by'],
            'created_at':r['created_at'].isoformat(),'motif_retrait':r['motif_retrait'],
            'retire_le':r['retire_le'].isoformat() if r['retire_le'] else None,'retire_par':r['retire_par'],
            'diagnostics':diagnostics})
    total=deja(db,sid,cid=cid)
    return {'capture_id':cid,'compte_destination':c['compte_destination'],'montant_capture':montant(c['montant']),
        'total_rapproche':montant(total),'capacite_documentaire':None if c['annulee'] else montant(c['montant']-total),
        'capture_annulee':bool(c['annulee']),'od_validee':bool(c['od_validee']),
        'note':NOTE,'items':resultat}


def options(db,sid,cid,recherche='',page=1):
    c=capture(db,sid,cid)
    # Choix explicite, jamais appariement automatique. Le montant disponible est
    # relu sous verrou lors de la création, pas déduit de la seule référence.
    params={'s':sid,'compte':c['compte_destination'],'offset':(page-1)*50,
        'q':'%'+recherche.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'}
    rows=db.execute(text('''SELECT e.id,e.date,e.journal,e.reference,e.numero_ecriture,
        sum(l.debit-l.credit) AS debit_compte FROM ecritures e
        JOIN lignes_ecriture l ON l.ecriture_id=e.id AND l.compte=:compte
        WHERE e.societe_id=:s AND e.est_validee
        AND (coalesce(e.reference,'') ILIKE :q ESCAPE '\\' OR coalesce(e.numero_ecriture,'') ILIKE :q ESCAPE '\\')
        AND NOT EXISTS(SELECT 1 FROM ecritures i WHERE i.contrepassation_de_id=e.id)
        AND NOT EXISTS(SELECT 1 FROM ras_reglement_captures rc WHERE rc.ecriture_id=e.id)
        AND NOT EXISTS(SELECT 1 FROM ras_reglement_annulations ra WHERE ra.ecriture_id=e.id)
        AND EXISTS(SELECT 1 FROM lignes_ecriture t WHERE t.ecriture_id=e.id AND t.compte LIKE '5%' AND t.credit>t.debit)
        GROUP BY e.id HAVING sum(l.debit-l.credit)>0
        ORDER BY e.date DESC,e.id DESC LIMIT 51 OFFSET :offset'''),params).mappings().all()
    items=[]
    for r in rows[:50]:
        utilise=deja(db,sid,eid=r['id'],compte=c['compte_destination'])
        items.append({'id':r['id'],'date_comptable':r['date'].isoformat(),'journal':r['journal'],
            'reference':r['reference'],'numero_ecriture':r['numero_ecriture'],
            'debit_compte':montant(r['debit_compte']),'deja_rapproche':montant(utilise),
            'disponible':montant(max(Decimal(0),r['debit_compte']-utilise))})
    return {'items':items,'page':page,'suivante':len(rows)>50}


def enregistrer(db,user,cid,data):
    sid=user['societe_id'];disponible(db);verrou(db,sid)
    c=capture(db,sid,cid)
    ancien=db.execute(text('SELECT * FROM ras_tva_rapprochements WHERE cle=CAST(:k AS uuid)'),{'k':str(data.cle)}).mappings().first()
    if ancien:
        if ancien['societe_id']!=sid or ancien['capture_id']!=cid or ancien['ecriture_id']!=data.ecriture_id or ancien['montant']!=data.montant:
            raise HTTPException(409,'Clé déjà utilisée pour un autre rapprochement.')
        return lire(db,sid,cid)
    if not data.rapprochement_verifie:raise HTTPException(422,'Confirmez le rapprochement documentaire de la pièce sélectionnée.')
    if c['annulee'] or not c['od_validee']:raise HTTPException(409,'Capture active avec OD validée requise.')
    e=piece(db,sid,data.ecriture_id)
    lie=db.scalar(text('''SELECT EXISTS(SELECT 1 FROM ras_reglement_captures WHERE ecriture_id=:e
        UNION ALL SELECT 1 FROM ras_reglement_annulations WHERE ecriture_id=:e
        UNION ALL SELECT 1 FROM ecritures WHERE contrepassation_de_id=:e)'''),{'e':data.ecriture_id})
    if not e['est_validee'] or lie:raise HTTPException(409,'Choisissez une pièce validée distincte, non contrepassée.')
    lignes=e['lignes'];debit=sum((Decimal(r['debit']) for r in lignes),Decimal(0));credit=sum((Decimal(r['credit']) for r in lignes),Decimal(0))
    if len(lignes)<2 or debit!=credit or not any(r['compte'].startswith('5') and Decimal(r['credit'])>Decimal(r['debit']) for r in lignes):
        raise HTTPException(409,'Pièce équilibrée avec crédit de trésorerie requise.')
    capacite=sum((Decimal(r['debit'])-Decimal(r['credit']) for r in lignes if r['compte']==c['compte_destination']),Decimal(0))
    if data.montant>c['montant']-deja(db,sid,cid=cid) or data.montant>capacite-deja(db,sid,eid=data.ecriture_id,compte=c['compte_destination']):
        raise HTTPException(409,'Montant supérieur à la capacité documentaire de la capture ou au débit disponible de la pièce.')
    faits={'schema_version':1,'capture':{'id':cid,'montant':montant(c['montant']),
        'compte_destination':c['compte_destination'],'ecriture_id':c['ecriture_id']},
        'piece':e,'montant':montant(data.montant),'rapprochement_verifie':True,'note':NOTE}
    db.execute(text('''INSERT INTO ras_tva_rapprochements(societe_id,capture_id,ecriture_id,montant,cle,faits,empreinte_sha256,created_by)
        VALUES(:s,:c,:e,:m,CAST(:k AS uuid),CAST(:f AS jsonb),:h,:u)'''),
        {'s':sid,'c':cid,'e':data.ecriture_id,'m':data.montant,'k':str(data.cle),
         'f':json.dumps(faits,ensure_ascii=False),'h':empreinte(faits),'u':user['id']})
    db.commit()
    return lire(db,sid,cid)


def retirer(db,user,cid,rid,motif):
    sid=user['societe_id'];disponible(db);verrou(db,sid);capture(db,sid,cid)
    r=db.execute(text('SELECT id FROM ras_tva_rapprochements WHERE id=:r AND capture_id=:c AND societe_id=:s'),{'r':rid,'c':cid,'s':sid}).first()
    if not r:raise HTTPException(404,'Rapprochement introuvable dans cette société.')
    ancien=db.scalar(text('SELECT motif FROM ras_tva_rapprochement_retraits WHERE rapprochement_id=:r'),{'r':rid})
    if ancien is not None:
        if ancien!=motif:raise HTTPException(409,'Ce rapprochement a déjà été retiré avec un autre motif.')
        return lire(db,sid,cid)
    db.execute(text('INSERT INTO ras_tva_rapprochement_retraits(rapprochement_id,societe_id,motif,created_by) VALUES(:r,:s,:m,:u)'),
        {'r':rid,'s':sid,'m':motif,'u':user['id']})
    db.commit()
    return lire(db,sid,cid)
