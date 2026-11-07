"""Dossier interne partageable d'une seule version, sans dépôt ni archive fiscale."""
import csv
from datetime import datetime, timezone
import hashlib
import hmac
from io import BytesIO, StringIO
import json
from zipfile import ZipFile, ZIP_DEFLATED

from services.balance_import_service import empreinte_preparation
from services.balance_preparation_export_service import generer_preparation_xlsx
from services.balance_preparation_pdf import generer_preparation_pdf
from services.balance_echeances_service import presentation
from services.logo_export_service import image_logo


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf8')


def generer_dossier(dossier, societe, *, documents=None, fichiers_documents=None):
    """Tout vient du snapshot contrôlé ; noms d'entrées constants, jamais des imports."""
    contenu = dossier['contenu']
    if not hmac.compare_digest(empreinte_preparation(contenu), dossier['empreinte_sha256']):
        raise ValueError('Empreinte de préparation incohérente ; dossier non exporté.')
    maintenant = datetime.now(timezone.utc).isoformat(timespec='seconds')
    nom = societe.get('raison_sociale', '') if isinstance(societe, dict) else societe.raison_sociale
    identite = {'raison_sociale_actuelle': nom, 'logo_valide_integre_aux_pdf_xlsx': image_logo(societe) is not None,
                'portee': 'Identité et logo actuels à l’export, hors empreinte du contenu conservé.'}
    fichiers = {
        'preparation.json': json_bytes(dossier),
        'identite_export.json': json_bytes(identite),
        'preparation.pdf': generer_preparation_pdf(dossier, societe),
        'preparation.xlsx': generer_preparation_xlsx(dossier, societe),
    }
    absentes = []
    for cle, nom_fichier in [('n', 'balance_N.csv'), ('n1', 'balance_N1.csv')]:
        source = contenu.get('sources', {}).get(cle)
        if source is None:
            absentes.append(cle)
            continue
        texte = StringIO(newline='')
        w = csv.DictWriter(texte, fieldnames=['compte', 'debit', 'credit'], delimiter=';', lineterminator='\n')
        w.writeheader()
        w.writerows({k: r[k] for k in ('compte', 'debit', 'credit')} for r in source)
        fichiers[nom_fichier] = texte.getvalue().encode('utf8')
    if contenu.get('echeances_documentaires'):
        fichiers['echeances_documentaires.json'] = json_bytes(presentation(dossier))
    if contenu.get('notes_etic_documentaires'):
        from services.balance_etic_notes_service import presentation as notes_etic
        fichiers['notes_etic_documentaires.json'] = json_bytes(notes_etic(dossier))
    if contenu.get('tables_etic_documentaires'):
        from services.balance_etic_tables_service import presentation as tables_etic
        fichiers['tables_etic_documentaires.json'] = json_bytes(tables_etic(dossier))
    if contenu.get('annexes_etic_documentaires'):
        from services.balance_etic_annexes_service import presentation as annexes_etic
        fichiers['annexes_etic_documentaires.json'] = json_bytes(annexes_etic(dossier))
    if contenu.get('detail_cpc_documentaire'):
        from services.balance_cpc_detail_service import presentation as detail_cpc
        fichiers['detail_cpc_documentaire.json'] = json_bytes(detail_cpc(dossier))
    if contenu.get('non_valeurs_documentaires'):
        from services.balance_non_valeurs_service import presentation as non_valeurs
        fichiers['non_valeurs_documentaires.json'] = json_bytes(non_valeurs(dossier))
    if contenu.get('extra_c3_documentaire'):
        from services.balance_c3_extra_service import presentation as extra_c3
        fichiers['extra_c3_documentaire.json']=json_bytes(extra_c3(dossier))
    if contenu.get('comparatif_n2_documentaire'):
        from services.balance_comparatif_n2_service import presentation as comparatif_n2
        vue_n2=comparatif_n2(dossier)
        fichiers['comparatif_n2_documentaire.json']=json_bytes(vue_n2)
        texte=StringIO(newline='');w=csv.DictWriter(texte,fieldnames=['compte','debit','credit'],delimiter=';',lineterminator='\n')
        w.writeheader();w.writerows({k:r[k] for k in ('compte','debit','credit')} for r in vue_n2['sources_n2'])
        fichiers['balance_N2.csv']=texte.getvalue().encode('utf8')
    if contenu.get('indicateurs_comptables_documentaires'):
        from services.balance_indicateurs_service import presentation as indicateurs
        fichiers['indicateurs_comptables_documentaires.json'] = json_bytes(indicateurs(dossier))
    if contenu.get('tva_documentaire'):
        from services.balance_tva_documentaire_service import presentation as tva_documentaire
        fichiers['tva_documentaire.json'] = json_bytes(tva_documentaire(dossier))
    if contenu.get('passage_fiscal_documentaire'):
        from services.balance_passage_fiscal_service import presentation as passage_fiscal
        fichiers['passage_fiscal_documentaire.json'] = json_bytes(passage_fiscal(dossier))
    if contenu.get('liquidation_is_documentaire'):
        from services.balance_liquidation_is_service import presentation as liquidation_is
        fichiers['liquidation_is_documentaire.json'] = json_bytes(liquidation_is(dossier))
    if contenu.get('acomptes_is_documentaires'):
        from services.balance_acomptes_is_service import presentation as acomptes_is
        fichiers['acomptes_is_documentaires.json'] = json_bytes(acomptes_is(dossier))
    if contenu.get('taxe_professionnelle_documentaire'):
        from services.balance_taxe_professionnelle_service import presentation as tp
        fichiers['taxe_professionnelle_documentaire.json'] = json_bytes(tp(dossier))
    if contenu.get('remunerations_tiers_documentaires'):
        from services.balance_remunerations_tiers_service import presentation as remunerations_tiers
        fichiers['remunerations_tiers_documentaires.json'] = json_bytes(remunerations_tiers(dossier))
    if contenu.get('credits_is_documentaires'):
        from services.balance_credits_is_service import presentation as credits_is
        fichiers['credits_is_documentaires.json'] = json_bytes(credits_is(dossier))
    if contenu.get('css_documentaire'):
        from services.balance_css_service import presentation as css_documentaire
        fichiers['css_documentaire.json'] = json_bytes(css_documentaire(dossier))
    if contenu.get('cotisation_minimale_documentaire'):
        from services.balance_cotisation_minimale_service import presentation as cotisation_minimale
        fichiers['cotisation_minimale_documentaire.json'] = json_bytes(cotisation_minimale(dossier))
    if contenu.get('contexte_fiscal_documentaire'):
        from services.balance_contexte_fiscal_service import presentation as contexte_fiscal
        fichiers['contexte_fiscal_documentaire.json'] = json_bytes(contexte_fiscal(dossier))
    if contenu.get('resultat_courant_documentaire'):
        from services.balance_resultat_courant_service import presentation as resultat_courant
        fichiers['resultat_courant_documentaire.json'] = json_bytes(resultat_courant(dossier))
    if contenu.get('participations_documentaires'):
        from services.balance_participations_service import presentation as participations
        fichiers['participations_documentaires.json'] = json_bytes(participations(dossier))
    if contenu.get('raccords_mouvements_documentaires'):
        from services.balance_raccords_mouvements_service import presentation as raccords
        fichiers['raccords_mouvements.json'] = json_bytes(raccords(dossier))
    if contenu.get('mouvements_documentaires'):
        from services.balance_mouvements_service import presentation as mouvements
        fichiers['mouvements_documentaires.json'] = json_bytes(mouvements(dossier))
    if contenu.get('cessions_documentaires'):
        from services.balance_cessions_service import presentation as cessions
        fichiers['cessions_documentaires.json'] = json_bytes(cessions(dossier))
    if contenu.get('declarations_emetteurs'):
        from services.balance_emetteurs_service import presentation as emetteurs
        fichiers['declarations_emetteurs.json'] = json_bytes(emetteurs(dossier))
    if contenu.get('financement_documentaire'):
        from services.balance_financement_service import presentation as financement
        fichiers['financement_documentaire.json'] = json_bytes(financement(dossier))
    if documents is not None:
        fichiers['justificatifs.json'] = json_bytes(documents)
        fichiers.update(fichiers_documents or {})
    lignes = [
        'HISABPRO — DOSSIER INTERNE DE PRÉPARATION DE BALANCES',
        f"Exercice {dossier['exercice']} — version {dossier['version']} — ID {dossier['id']}",
        f"Période conservée : {contenu['periode']['debut']} au {contenu['periode']['fin']}",
        'Empreinte du contenu conservé : ' + dossier['empreinte_sha256'],
        'Généré le : ' + maintenant,
        '',
        'Ce ZIP ne constitue ni une archive fiscale annuelle définitive, ni une liasse complète prête à déposer.',
        'Il ne contient pas de XML/EDI officiel et ne prouve aucun dépôt ni paiement fiscal.',
        'Aucune écriture ni version supplémentaire n’est créée par son téléchargement.',
        '',
        'preparation.json contient le snapshot conservé et son empreinte.',
        'PDF et XLSX présentent cette même version avec le logo et l’identité actuels, hors empreinte historique.',
        'Les CSV sont les balances normalisées conservées, pas les fichiers binaires d’origine.',
        'Les noms de fichiers déclarés à l’import restent des métadonnées ; aucun chemin importé n’est extrait.',
        'Un N-1 absent reste absent. Les montants et échéances inconnus ne sont pas remplacés par zéro.',
        'Les compléments documentaires éventuels ne valent pas ETIC officielle complète.',
        '',
        'Sources détaillées absentes : ' + (', '.join(absentes) if absentes else 'aucune'),
        'Logo valide intégré : ' + ('oui' if identite['logo_valide_integre_aux_pdf_xlsx'] else 'non — absent ou historique incompatible'),
        '',
        'Restant à compléter selon la préparation :',
        *['- ' + str(v) for v in contenu['preparation']['a_completer']],
        '',
        'Contrôle technique : MANIFESTE_SHA256.json donne la taille et le SHA-256 de chaque autre fichier.',
        'Vérifier après extraction la liste exacte, les tailles et empreintes. Le manifeste ne s’auto-hache pas.',
        'Ces empreintes permettent de contrôler la cohérence du paquet ; ce ne sont pas une signature ou certification officielle.',
    ]
    if documents is not None:
        lignes += ['', 'Justificatifs complémentaires : ' + documents['statut'], documents['note']]
    fichiers['LIRE_MOI.txt'] = ('\n'.join(lignes) + '\n').encode('utf8')
    manifeste = {'schema_version': 1, 'type': 'preparation_interne_balances', 'pret_a_deposer': False,
        'genere_le_utc': maintenant, 'preparation': {k: dossier[k] for k in ('id','exercice','version','empreinte_sha256')},
        'sources_absentes': absentes, 'identite_export': 'identite_export.json',
        'fichiers': {n: {'taille': len(v), 'sha256': hashlib.sha256(v).hexdigest()} for n,v in fichiers.items()}}
    fichiers['MANIFESTE_SHA256.json'] = json_bytes(manifeste)
    out = BytesIO()
    with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
        for n,v in fichiers.items():
            archive.writestr(n, v)
    return out.getvalue()
