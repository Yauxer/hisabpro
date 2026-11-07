"""Calcul de la paie du mois en un clic (lot 976).

Enchaîne les services existants, avec leurs contrôles, leurs snapshots et leur
historique : brut → cotisations → bases fiscales → IR du mois → bulletins.
Rien n'est recalculé ici ; seules les déclarations que l'utilisateur saisissait
écran par écran sont préremplies, selon les choix validés par l'utilisateur :
- salaire de base soumis à 100 % CNSS/AMO et imposable à 100 % (les primes gardent
  la règle de leur rubrique) ;
- frais professionnels du mois : CGI 2026 art. 59-I-A (35 % si le revenu brut annuel
  imposable n'excède pas 78 000 DH, sinon 25 %), plafond annuel 35 000 DH ramené au
  mois (2 916,66 DH, arrondi inférieur pour ne jamais dépasser le plafond annuel) ;
- personnes à charge reprises de la fiche du salarié.
Un salarié incomplet est écarté avec la raison ; les autres continuent.
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from uuid import uuid4
from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import text
from services import (paie_campagnes_service as brut_service, paie_social_calcul_service as social_service,
                      paie_bases_fiscales_service as bases_service, paie_ir_mensuel_service as ir_service,
                      paie_bulletins_service as bulletins)
from services.paie_campagnes_schemas import Simulation as SimBrut
from services.paie_social_calcul_schemas import Simulation as SimSocial, Declaration as DeclSociale
from services.paie_bases_fiscales_schemas import Simulation as SimBases, Declaration as DeclBases
from services.paie_ir_mensuel_schemas import Simulation as SimIR
from services.paie_catalogue_schemas import Base

D = Decimal
SEUIL_ANNUEL = D('78000')
PLAFOND_MENSUEL = (D('35000') / 12).quantize(D('0.01'), rounding=ROUND_DOWN)
REFERENCE = 'Calcul du mois HisabPro'


class Demande(Base):
    periode: date
    regime: str | None = Field(default=None, pattern=r'^[A-Z][A-Z0-9_]{1,79}$')
    hypotheses_confirmees: bool = Field(strict=True)


def frais_professionnels(brut_imposable, base_frais):
    """CGI 2026 art. 59-I-A ramené au mois ; montants exacts à deux décimales."""
    taux = D('35') if D(brut_imposable) * 12 <= SEUIL_ANNUEL else D('25')
    frais = (D(base_frais) * taux / 100).quantize(D('0.01'), rounding=ROUND_HALF_UP)
    return min(frais, PLAFOND_MENSUEL), taux


def salaries_actifs(db, sid, debut, fin):
    return [dict(r) for r in db.execute(text(
        "SELECT d.employe_id,e.nom,e.personnes_charge_ir FROM personnel_dossiers d JOIN employes e ON e.id=d.employe_id AND e.societe_id=d.societe_id "
        "WHERE d.societe_id=:s AND d.statut IN ('ACTIF','SORTI') AND (d.date_sortie_approuvee IS NULL OR d.date_sortie_approuvee>:f) "
        "ORDER BY e.nom,d.employe_id LIMIT 50"), {'s': sid, 'f': fin}).mappings()]


def regime_unique(db, sid, demande):
    regimes = list(db.scalars(text("SELECT DISTINCT b.regime FROM paie_branches_sociales b JOIN paie_branche_sociale_versions v "
                                   "ON v.branche_id=b.id AND v.societe_id=b.societe_id AND v.statut='APPROUVEE' WHERE b.societe_id=:s ORDER BY 1"), {'s': sid}))
    if demande:
        if demande not in regimes:
            raise HTTPException(409, f'Aucune cotisation approuvée dans le régime {demande}.')
        return demande
    if not regimes:
        raise HTTPException(409, 'Aucune cotisation sociale approuvée : chargez et approuvez vos cotisations dans Charges sociales.')
    if len(regimes) > 1:
        raise HTTPException(409, 'Plusieurs régimes de cotisations approuvés : choisissez celui à appliquer (' + ', '.join(regimes) + ').')
    return regimes[0]


def calculer_mois(db, user, data):
    if not data.hypotheses_confirmees:
        raise HTTPException(400, 'Confirmez les hypothèses de calcul (bases, frais professionnels, personnes à charge).')
    bulletins.autoriser(db, user, 'proposer')
    sid = user['societe_id']
    debut = data.periode.replace(day=1)
    fin = debut.replace(day=monthrange(debut.year, debut.month)[1])
    regime = regime_unique(db, sid, data.regime)
    tous = salaries_actifs(db, sid, debut, fin)
    if not tous:
        raise HTTPException(409, 'Aucun salarié actif pour ce mois.')
    rapport = {e['employe_id']: {'employe_id': e['employe_id'], 'nom': e['nom'], 'statut': 'en_cours', 'raison': None, 'bulletin_id': None, 'net_a_payer': None}
               for e in tous}

    def ecarter(eid, raison):
        rapport[eid].update(statut='bloque', raison=raison)

    deja = {r['employe_id']: r for r in db.execute(text("SELECT employe_id,id,net_a_payer FROM paie_bulletins WHERE societe_id=:s AND periode=:p AND statut='VALIDE'"),
                                                   {'s': sid, 'p': debut}).mappings()}
    for eid, b in deja.items():
        if eid in rapport:
            rapport[eid].update(statut='deja_etabli', bulletin_id=b['id'], net_a_payer=format(b['net_a_payer'], '.2f'))
    a_calculer = [e['employe_id'] for e in tous if e['employe_id'] not in deja]
    motif = f'{REFERENCE} — {debut:%m/%Y}'

    # 1. Brut ; un salarié en anomalie est écarté puis le brut est recalculé sans lui.
    gross = None
    while a_calculer:
        gross = brut_service.simuler(db, user, SimBrut(periode=debut, employe_ids=a_calculer, mois_complets_confirmes=True, cle_idempotence=uuid4(), motif=motif))
        incomplets = [x for x in gross['contenu']['employes'] if x['anomalies']]
        if not incomplets:
            break
        for x in incomplets:
            ecarter(x['employe_id'], 'Salaire brut : ' + ' ; '.join(a['message'] for a in x['anomalies']))
        a_calculer = [i for i in a_calculer if i not in {x['employe_id'] for x in incomplets}]
    if a_calculer:
        lignes_brut = {x['employe_id']: x for x in gross['contenu']['employes']}
        # 2. Cotisations : salaire de base soumis à 100 %.
        social = social_service.simuler(db, user, SimSocial(brut_id=gross['id'], regime=regime, mode_pedagogique_confirme=True, cle_idempotence=uuid4(), motif=motif,
            declarations=[DeclSociale(employe_id=i, base_cnss=lignes_brut[i]['base'], base_amo=lignes_brut[i]['base'], conditions_confirmees=True,
                                      reference_controle=REFERENCE + ' : salaire de base soumis à 100 %') for i in a_calculer]))
        for x in social['contenu']['employes']:
            if x['anomalies'] or x['salarial'] is None:
                ecarter(x['employe_id'], 'Cotisations : ' + ' ; '.join(a['message'] for a in x['anomalies'] or [{'message': 'incomplètes'}]))
        # 3. Bases fiscales : salaire de base imposable à 100 %, déductions intégrales qualifiées.
        prep = bases_service.simuler(db, user, SimBases(social_id=social['id'], mode_pedagogique_confirme=True, cle_idempotence=uuid4(), motif=motif,
            declarations=[DeclBases(employe_id=i, base_imposable=lignes_brut[i]['base'], base_frais=lignes_brut[i]['base'], conditions_confirmees=True,
                                    deductibilite_integrale_confirmee=True, reference_controle=REFERENCE + ' : salaire de base imposable à 100 %')
                          for i in a_calculer]))
        fiche = {e['employe_id']: e for e in tous}
        for x in prep['contenu']['employes']:
            eid = x['employe_id']
            if rapport[eid]['statut'] == 'bloque':
                continue
            if x['anomalies'] or x['brut_imposable'] is None:
                ecarter(eid, 'Bases fiscales : ' + ' ; '.join(a['message'] for a in x['anomalies']))
                continue
            personnes = fiche[eid]['personnes_charge_ir']
            if personnes is None:
                ecarter(eid, 'Personnes à charge non renseignées dans la fiche du salarié.')
                continue
            # 4. IR du mois.
            frais, taux = frais_professionnels(x['brut_imposable'], x['base_frais_professionnels'])
            ctrl = ir_service.simuler(db, user, SimIR(preparation_id=prep['id'], employe_id=eid,
                frais_professionnels_declares=frais, reference_frais=f'CGI 2026 art. 59-I-A : {taux} %, plafond mensuel {PLAFOND_MENSUEL} DH',
                autres_deductions_declarees=D('0.00'), reference_autres_deductions='Aucune autre déduction', deductions_confirmees=True,
                cadre_mensuel_general_confirme=True, reference_controle_mensuel=motif, personnes_charge=int(personnes),
                eligibilite_famille_confirmee=True, reference_famille='Fiche salarié : personnes à charge', mode_pedagogique_confirme=True,
                cle_idempotence=uuid4(), motif=motif))
            if ctrl['contenu']['anomalies'] or ctrl['contenu']['ir_mensuel_arithmetique'] is None:
                ecarter(eid, 'IR : ' + ' ; '.join(a['message'] for a in ctrl['contenu']['anomalies']))
                continue
            # 5. Bulletin (IR arrondi au centime, retenues d'avances prévues).
            apercu = bulletins.apercu(db, user, ctrl['id'])
            retenues = []
            for av in apercu['avances']:
                if av['retenue_mensuelle']:
                    retenues.append(bulletins.Retenue(avance_id=av['id'], montant=min(D(av['retenue_mensuelle']), D(av['solde']))))
            b = bulletins.creer(db, user, bulletins.Creation(controle_id=ctrl['id'], ir_retenu=D(apercu['ir_propose']), retenues_avances=retenues,
                                                             cle_idempotence=uuid4(), motif=motif))
            rapport[eid].update(statut='etabli', bulletin_id=b['id'], net_a_payer=b['contenu']['net_a_payer'])
    lignes = sorted(rapport.values(), key=lambda r: (r['statut'] != 'bloque', r['nom']))
    return {'periode': debut.isoformat(), 'regime': regime, 'salaries': lignes,
            'etablis': sum(r['statut'] == 'etabli' for r in lignes), 'deja_etablis': sum(r['statut'] == 'deja_etabli' for r in lignes),
            'bloques': sum(r['statut'] == 'bloque' for r in lignes),
            'hypotheses': {'base_soumise': '100 % du salaire de base (primes selon leur rubrique)',
                           'frais_professionnels': f'CGI 2026 art. 59-I-A, plafond mensuel {PLAFOND_MENSUEL} DH',
                           'personnes_a_charge': 'fiche du salarié'}}
