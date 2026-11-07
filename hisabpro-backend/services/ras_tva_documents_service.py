"""Métadonnées documentaires existantes des OD, sans qualification fiscale."""
import models

NOTE_DOCUMENTS = ('Documents complémentaires rattachés aux OD de capture ou de contrepassation. '
    'Les références et noms de fichiers sont déclarés dans le Journal ; leur présence ne vaut ni '
    'attestation fiscale contrôlée, ni preuve de versement, ni crédit imputable. '
    'Le contenu des fichiers n’est pas incorporé dans cet export ni dans son empreinte de données.')


def completer_documents(db, sid, lignes):
    """Même session RO/RR ; aucun accès au disque ou nouvelle donnée présumée."""
    ids = sorted({e for r in lignes for e in (r['ecriture_id'],r['od_annulation_id']) if e is not None})
    documents = {}
    # Lots bornés : pas de requête par capture ni de liste de paramètres géante.
    for debut in range(0,len(ids),1000):
        rows = db.query(models.EcritureJustificatif).filter(
            models.EcritureJustificatif.societe_id==sid,
            models.EcritureJustificatif.ecriture_id.in_(ids[debut:debut+1000]),
        ).order_by(models.EcritureJustificatif.id).all()
        for j in rows:
            documents.setdefault(j.ecriture_id,[]).append({
                'id':j.id,'reference':j.reference,'source_type':j.source_type,
                'date_piece':j.date_piece.isoformat() if j.date_piece else None,
                'fichier_nom':j.fichier_nom,'prioritaire':bool(j.prioritaire),
                'created_at':j.created_at.isoformat() if j.created_at else None,
            })
    for r in lignes:
        r['documents_od'] = documents.get(r['ecriture_id'],[])
        r['documents_annulation'] = documents.get(r['od_annulation_id'],[])


def lignes_documents(data):
    """Une ligne par référence complémentaire, avec sa vraie OD et phase."""
    for r in data['lignes']:
        for cle,phase,eid in [('documents_od','Capture',r['ecriture_id']),
                              ('documents_annulation','Contrepassation',r['od_annulation_id'])]:
            for j in r.get(cle) or []:
                yield {'capture_id':r['capture_id'],'nature':r['nature'],'phase':phase,
                    'ecriture_id':eid,**j}
