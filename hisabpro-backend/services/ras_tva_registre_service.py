"""Registre descriptif des captures099 ; aucun crédit fiscal ou reversement présumé."""
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from sqlalchemy import text
from fastapi import HTTPException
import models
from services.ras_tva_reglement_service import disponible
from services.ventes_preparation_service import preparer_lecture
from services.ras_tva_documents_service import completer_documents, NOTE_DOCUMENTS

NOTE = ('Registre interne des retenues déclarées, opérées sur achats et subies sur ventes, sans compensation entre ces catégories. '
    'Captures TVA guidées uniquement ; les captures libres et retenues historiques ne sont pas qualifiées ici. '
    'État des OD et annulations à ce jour. Périmètre par année civile entière, distinct des dates d’un exercice décalé. Totaux des captures de paiements de l’année ; annulations de l’année présentées séparément. '
    'Le mois de reversement provient du calcul conservé et ne prouve aucun versement. '
    'Ce registre ne détermine ni crédit imputable, ni solde de déclaration et ne vaut pas bordereau officiel.')


def argent(v):
    if v is None or isinstance(v, bool):
        raise ValueError('Montant absent')
    try:
        d = Decimal(str(v))
        if not d.is_finite() or d < 0 or d >= Decimal('1e16') or d != d.quantize(Decimal('.01')):
            raise ValueError('Montant non fini ou non représentable au centime')
        return format(d, '.2f')
    except InvalidOperation:
        raise ValueError('Montant non représentable')


def totaux(lignes):
    resultat = {}
    for nature in ('achat','vente'):
        choix = [r for r in lignes if r['nature']==nature]
        groupes = {
            'declarees': [r for r in choix if r['capture_dans_annee']],
            'actives': [r for r in choix if r['capture_dans_annee'] and not r['annulation_id']],
            'actives_validees': [r for r in choix if r['capture_dans_annee'] and not r['annulation_id'] and r['od_validee']],
            'annulees': [r for r in choix if r['capture_dans_annee'] and r['annulation_id']],
            'annulations_annee': [r for r in choix if r['annulation_dans_annee']],
        }
        resultat[nature] = {}
        for cle, rows in groupes.items():
            connus = [Decimal(r['retenue_tva']) for r in rows if r['retenue_tva'] is not None]
            somme = format(sum(connus, Decimal(0)), '.2f')
            resultat[nature][cle] = {'montant': somme if len(connus)==len(rows) else None,
                'partie_certaine': somme, 'nombre': len(rows)}
    return resultat


def construire(db, sid, annee):
    preparer_lecture(db)
    societe = db.get(models.Societe, sid)
    if not societe:
        raise HTTPException(404, 'Société introuvable')
    identite = {'raison_sociale':societe.raison_sociale or '', 'ice':societe.ice or '',
        'identifiant_fiscal':societe.identifiant_fiscal or '',
        'logo_sha256':hashlib.sha256((societe.logo_url or '').encode()).hexdigest()}
    actif = disponible(db)
    data = {'annee':annee,'societe_id':sid,'societe':identite,'disponible':actif,
        'migration_requise':None if actif else '099_ras_tva_details.sql',
        'note':NOTE,'note_documents':NOTE_DOCUMENTS,'lignes':[],'totaux':None}
    if actif:
        rows = db.execute(text('''SELECT c.*,d.dossier,f.type AS nature,f.numero AS numero_facture,
            f.tiers,e.est_validee AS od_validee,e.numero_ecriture,
            a.id AS annulation_id,a.date_operation AS date_annulation,a.ecriture_id AS od_annulation_id
            FROM public.ras_tva_reglement_details d
            JOIN public.ras_reglement_captures c ON c.id=d.capture_id AND c.societe_id=d.societe_id
            JOIN public.factures f ON f.id=c.facture_id AND f.societe_id=c.societe_id
            JOIN public.ecritures e ON e.id=c.ecriture_id AND e.societe_id=c.societe_id
            LEFT JOIN public.ras_reglement_annulations a ON a.capture_id=c.id AND a.societe_id=c.societe_id
            WHERE d.societe_id=:s AND (EXTRACT(YEAR FROM c.date_operation)=:a
                OR EXTRACT(YEAR FROM a.date_operation)=:a) ORDER BY c.id DESC'''), {'s':sid,'a':annee}).mappings()
        for row in rows:
            d = row['dossier']
            faits, calcul = d.get('faits') or {}, d.get('simulation') or {}
            ligne = {k:row[k] for k in ('reglement_id','facture_id','reference','compte_destination','ecriture_id',
                'nature','numero_facture','tiers','od_validee','numero_ecriture','annulation_id','od_annulation_id')}
            ligne.update(capture_id=row['id'],date_paiement=row['date_operation'].isoformat(),
                date_annulation=row['date_annulation'].isoformat() if row['date_annulation'] else None,
                capture_dans_annee=row['date_operation'].year==annee,
                annulation_dans_annee=bool(row['date_annulation'] and row['date_annulation'].year==annee),
                mois_reversement_prevu=calcul.get('mois_reversement'),
                justification_quote_part=d.get('justification_quote_part') or '',
                reference_attestation=faits.get('reference_attestation') or '',diagnostics=[],
                dossier_sha256=hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
            for cle, valeur in [('retenue_tva',row['montant']),('quote_part_ttc',faits.get('montant_paiement_ttc')),
                               ('quote_part_tva',faits.get('tva_paiement')),('net_reglement',calcul.get('net_apres_cette_ras_tva'))]:
                try:ligne[cle]=argent(valeur)
                except (ValueError,TypeError):
                    libelle={'retenue_tva':'Retenue TVA','quote_part_ttc':'Quote-part TTC','quote_part_tva':'TVA de la quote-part','net_reglement':'Net du règlement'}[cle]
                    ligne[cle]=None;ligne['diagnostics'].append(f'{libelle} : source à vérifier')
            data['lignes'].append(ligne)
        data['totaux']=totaux(data['lignes'])
        completer_documents(db,sid,data['lignes'])
    data['empreinte_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return data
