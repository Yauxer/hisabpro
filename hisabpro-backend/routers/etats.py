# -*- coding: utf-8 -*-
"""
États de synthèse CGNC.

Depuis le Patch 09.1, la source comptable (soldes par compte) est agrégée
directement en PostgreSQL à partir des écritures validées. Le frontend conserve
le moteur de présentation Bilan/CPC/ESG/TF. L'endpoint PDF rend la structure
affichée ; les exports réglementaires figés seront traités au Patch 09.3.
"""
from typing import List, Optional, Dict, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, requiert_ecriture
import models

router = APIRouter(prefix="/api/etats", tags=["etats"])
from routers.balance_documents import router as balance_documents_router
router.include_router(balance_documents_router)


def lecture_ventes(db: Session = Depends(get_db)):
    from services.ventes_preparation_service import preparer_lecture
    return preparer_lecture(db)


@router.get('/ventes/preparation/{exercice}')
def preparation_ventes(exercice: int, db: Session = Depends(lecture_ventes), current_user=Depends(get_current_user)):
    # Cette dépendance doit précéder l'authentification : même session cachée,
    # transaction READ ONLY/REPEATABLE READ avant le premier SELECT utilisateur.
    from services.ventes_preparation_service import construire
    return construire(db, current_user['societe_id'], exercice)


@router.get('/ventes/preparation/{exercice}/export/{format}')
def exporter_preparation_ventes(exercice: int, format: Literal['pdf','xlsx'],
                               empreinte: str=Query(...,pattern=r'^[a-f0-9]{64}$'),
                               db: Session=Depends(lecture_ventes),current_user=Depends(get_current_user)):
    from services.ventes_preparation_service import construire
    from services.ventes_preparation_export_service import pdf,xlsx
    data=construire(db,current_user['societe_id'],exercice)
    if data['empreinte_sha256'] != empreinte:
        raise HTTPException(409,'Les sources ont changé depuis cette préparation. Actualisez les ventes avant de les exporter.')
    societe=db.query(models.Societe).filter_by(id=current_user['societe_id']).one()
    contenu=pdf(data,societe) if format=='pdf' else xlsx(data,societe)
    media='application/pdf' if format=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return Response(contenu,media_type=media,headers={
        'Content-Disposition':f'attachment; filename="VENTES_PREPARATION_INTERNE_{exercice}.{format}"',
        'Access-Control-Expose-Headers':'Content-Disposition',
    })


class BalancePreparationIn(BaseModel):
    lignes_n: List[Dict[str, Any]]
    lignes_n1: Optional[List[Dict[str, Any]]] = None


@router.post("/liasse/balance/preview")
def preparer_liasse_balance(data: BalancePreparationIn,
                           current_user=Depends(requiert_ecriture), db: Session = Depends(get_db)):
    """Valide des balances externes sans modifier la comptabilité de la société."""
    from services.balance_import_service import preparer_balance_liasse
    comptes = {row.numero for row in db.query(models.CompteSociete).filter_by(
        societe_id=current_user["societe_id"]).all()}
    try:
        return preparer_balance_liasse(data.lignes_n, data.lignes_n1, comptes)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


class BalanceDossierIn(BalancePreparationIn):
    exercice: int
    fichier_n: Optional[str] = Field(default=None, max_length=200)
    fichier_n1: Optional[str] = Field(default=None, max_length=200)


@router.post('/liasse/balance/dossiers', status_code=201)
def conserver_preparation_balance(data: BalanceDossierIn, current_user=Depends(requiert_ecriture),
                                  db: Session = Depends(get_db)):
    from services.balance_import_service import enregistrer_preparation
    noms = {k: v for k, v in {'n': data.fichier_n, 'n1': data.fichier_n1}.items() if v}
    if data.fichier_n1 and data.lignes_n1 is None:
        raise HTTPException(422, 'Fichier N-1 déclaré sans balance N-1 fournie.')
    try:
        return enregistrer_preparation(db, current_user['societe_id'], data.exercice,
            data.lignes_n, data.lignes_n1, noms, current_user.get('id'))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc))


@router.get('/liasse/balance/dossiers')
def preparations_balance(exercice: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(models.LiasseBalancePreparation).filter_by(
        societe_id=current_user['societe_id'], exercice=exercice).order_by(
        models.LiasseBalancePreparation.version.desc()).limit(200).all()
    return [{'id': r.id, 'version': r.version, 'exercice': r.exercice,
             'created_at': r.created_at.isoformat(), 'empreinte_sha256': r.empreinte_sha256} for r in rows]


@router.get('/liasse/balance/dossiers/{preparation_id}')
def preparation_balance(preparation_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from services.balance_import_service import lire_preparation
    row = db.query(models.LiasseBalancePreparation).filter_by(
        id=preparation_id, societe_id=current_user['societe_id']).first()
    if not row:
        raise HTTPException(404, 'Préparation introuvable dans cette société.')
    try:
        return lire_preparation(row)
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.get('/liasse/balance/dossiers/{preparation_id}/pdf')
def preparation_balance_pdf(preparation_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from services.balance_preparation_pdf import generer_preparation_pdf
    dossier = preparation_balance(preparation_id, current_user, db)
    societe = db.query(models.Societe).filter_by(id=current_user['societe_id']).one()
    content = generer_preparation_pdf(dossier, societe)
    return Response(content, media_type='application/pdf', headers={'Content-Disposition':
        f'attachment; filename="HisabPro_Preparation_{dossier["exercice"]}_v{dossier["version"]}.pdf"',
        'Access-Control-Expose-Headers': 'Content-Disposition'})


@router.get('/liasse/balance/dossiers/{preparation_id}/xlsx')
def preparation_balance_xlsx(preparation_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from services.balance_preparation_export_service import generer_preparation_xlsx
    dossier = preparation_balance(preparation_id, current_user, db)
    societe = db.query(models.Societe).filter_by(id=current_user['societe_id']).one()
    return Response(generer_preparation_xlsx(dossier, societe),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':
            f'attachment; filename="HisabPro_Preparation_{dossier["exercice"]}_v{dossier["version"]}.xlsx"',
            'Access-Control-Expose-Headers': 'Content-Disposition'})


@router.get('/liasse/balance/dossiers/{preparation_id}/detail')
def preparation_balance_detail(preparation_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from services.balance_preparation_export_service import presentation_bilan, NOTE_DETAIL
    dossier = preparation_balance(preparation_id, current_user, db)
    sources = dossier['contenu']['sources']
    return {'id': dossier['id'], 'exercice': dossier['exercice'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], 'bilan': presentation_bilan(dossier),
            'balances': {k: sources.get(k) for k in ('n', 'n1')}, 'note': NOTE_DETAIL}


@router.get('/liasse/balance/dossiers/{preparation_id}/zip')
def preparation_balance_dossier(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_preparation_dossier_service import generer_dossier
    from services.balance_documents_service import paquet
    dossier = preparation_balance(preparation_id, current_user, db)
    societe = db.query(models.Societe).filter_by(id=current_user['societe_id']).one()
    try:
        documents,fichiers = paquet(db,current_user['societe_id'],preparation_id)
        contenu = generer_dossier(dossier, societe, documents=documents, fichiers_documents=fichiers)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return Response(contenu, media_type='application/zip', headers={
        'Content-Disposition': f'attachment; filename="HisabPro_Dossier_Preparation_{dossier["exercice"]}_v{dossier["version"]}.zip"',
        'Access-Control-Expose-Headers': 'Content-Disposition',
        'Cache-Control': 'no-store',
    })


class BalanceEcheanceLigneIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    section: Literal['B6', 'B7']
    compte: str = Field(pattern=r'^[1-7][0-9]{3,9}$')
    plus_un_an: Any = None
    moins_un_an: Any = None
    echues: Any = None
    devises: Any = None
    etat_organismes_publics: Any = None
    entreprises_liees: Any = None
    effets: Any = None
    justification: str = Field(default='', max_length=2000)


class BalanceEcheancesIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    empreinte_parent: str = Field(pattern=r'^[a-f0-9]{64}$')
    cle: UUID
    lignes: List[BalanceEcheanceLigneIn] = Field(min_length=1, max_length=10000)


@router.get('/liasse/balance/dossiers/{preparation_id}/echeances')
def preparation_echeances(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_echeances_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/echeances', status_code=201)
def conserver_echeances(preparation_id: int, data: BalanceEcheancesIn,
                       current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_echeances_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceFinancementLigneIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    code: str = Field(min_length=2, max_length=100)
    n: Any = None
    n1: Any = None
    justification_n: str = Field(default='', max_length=2000)
    justification_n1: str = Field(default='', max_length=2000)


class BalanceFinancementIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    empreinte_parent: str = Field(pattern=r'^[a-f0-9]{64}$')
    cle: UUID
    lignes: List[BalanceFinancementLigneIn] = Field(min_length=1, max_length=100)


@router.get('/liasse/balance/dossiers/{preparation_id}/financement')
def preparation_financement(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_financement_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/financement', status_code=201)
def conserver_financement(preparation_id: int, data: BalanceFinancementIn,
                         current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_financement_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceEticNoteIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    code: str = Field(min_length=2, max_length=10)
    statut: Literal['a_completer', 'renseigne', 'non_applicable']
    texte: str = Field(default='', max_length=10000)
    justification: str = Field(default='', max_length=2000)


class BalanceEticNotesIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    empreinte_parent: str = Field(pattern=r'^[a-f0-9]{64}$')
    cle: UUID
    lignes: List[BalanceEticNoteIn] = Field(min_length=1, max_length=100)


@router.get('/liasse/balance/dossiers/{preparation_id}/notes-etic')
def preparation_notes_etic(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_etic_notes_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/notes-etic', status_code=201)
def conserver_notes_etic(preparation_id: int, data: BalanceEticNotesIn,
                        current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_etic_notes_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceEticTableIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    code: Literal['B8', 'B9']
    statut: Literal['a_completer', 'documente', 'neant_declare']
    justification: str = Field(default='', max_length=2000)
    lignes: List[Dict[str, Any]] = Field(default_factory=list, max_length=100)


class BalanceEticTablesIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    empreinte_parent: str = Field(pattern=r'^[a-f0-9]{64}$')
    cle: UUID
    tables: List[BalanceEticTableIn] = Field(min_length=2, max_length=2)


@router.get('/liasse/balance/dossiers/{preparation_id}/tables-etic')
def preparation_tables_etic(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_etic_tables_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/tables-etic', status_code=201)
def conserver_tables_etic(preparation_id: int, data: BalanceEticTablesIn,
                         current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_etic_tables_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceEticAnnexeIn(BalanceEticTableIn):
    code: Literal['A2', 'A3', 'B10', 'C1', 'C2', 'C4']


class BalanceEticAnnexesIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    empreinte_parent: str = Field(pattern=r'^[a-f0-9]{64}$')
    cle: UUID
    tables: List[BalanceEticAnnexeIn] = Field(min_length=6, max_length=6)


@router.get('/liasse/balance/dossiers/{preparation_id}/annexes-etic')
def preparation_annexes_etic(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_etic_annexes_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/annexes-etic', status_code=201)
def conserver_annexes_etic(preparation_id: int, data: BalanceEticAnnexesIn,
                         current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_etic_annexes_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceCpcDetailIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    empreinte_parent: str = Field(pattern=r'^[a-f0-9]{64}$')
    cle: UUID


@router.get('/liasse/balance/dossiers/{preparation_id}/detail-cpc')
def preparation_detail_cpc(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_cpc_detail_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/detail-cpc', status_code=201)
def conserver_detail_cpc(preparation_id: int, data: BalanceCpcDetailIn,
                        current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_cpc_detail_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceNonValeursIn(BalanceCpcDetailIn):
    pass


@router.get('/liasse/balance/dossiers/{preparation_id}/non-valeurs')
def preparation_non_valeurs(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_non_valeurs_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/non-valeurs', status_code=201)
def conserver_non_valeurs(preparation_id: int, data: BalanceNonValeursIn,
                          current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_non_valeurs_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceParticipationsIn(BalanceCpcDetailIn):
    pass


@router.get('/liasse/balance/dossiers/{preparation_id}/participations')
def preparation_participations(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_participations_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/participations', status_code=201)
def conserver_participations(preparation_id: int, data: BalanceParticipationsIn,
                             current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_participations_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceC3ExtraTableIn(BalanceEticTableIn):
    code: Literal['C3-N','C3-N1','C3-N2']


class BalanceC3ExtraIn(BalanceEticTablesIn):
    tables: List[BalanceC3ExtraTableIn] = Field(min_length=3,max_length=3)


@router.get('/liasse/balance/dossiers/{preparation_id}/c3-extra')
def preparation_c3_extra(preparation_id: int,current_user=Depends(get_current_user),db: Session=Depends(get_db)):
    from services.balance_c3_extra_service import presentation
    dossier=preparation_balance(preparation_id,current_user,db)
    return {'id':dossier['id'],'version':dossier['version'],'empreinte_sha256':dossier['empreinte_sha256'],**presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/c3-extra',status_code=201)
def conserver_c3_extra(preparation_id: int,data: BalanceC3ExtraIn,
                       current_user=Depends(requiert_ecriture),db: Session=Depends(get_db)):
    from services.balance_c3_extra_service import conserver
    return conserver(db,current_user,preparation_id,data)


class BalanceComparatifN2In(BalanceCpcDetailIn):
    source_preparation_id: int = Field(strict=True, gt=0)
    source_empreinte_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reference_source: str = Field(min_length=1, max_length=2000)


@router.get('/liasse/balance/dossiers/{preparation_id}/comparatif-n2')
def preparation_comparatif_n2(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_comparatif_n2_service import presentation,candidats
    dossier=preparation_balance(preparation_id,current_user,db)
    return {'id':dossier['id'],'version':dossier['version'],'empreinte_sha256':dossier['empreinte_sha256'],
            **presentation(dossier),'candidats':candidats(db,current_user,dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/comparatif-n2',status_code=201)
def conserver_comparatif_n2(preparation_id: int,data: BalanceComparatifN2In,
                           current_user=Depends(requiert_ecriture),db: Session=Depends(get_db)):
    from services.balance_comparatif_n2_service import conserver
    return conserver(db,current_user,preparation_id,data)


class BalanceIndicateursIn(BalanceCpcDetailIn):
    pass


@router.get('/liasse/balance/dossiers/{preparation_id}/indicateurs-c3')
def preparation_indicateurs(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_indicateurs_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/indicateurs-c3', status_code=201)
def conserver_indicateurs(preparation_id: int, data: BalanceIndicateursIn,
                         current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_indicateurs_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceTvaTableIn(BalanceEticTableIn):
    code: Literal['B14-N']


class BalanceTvaIn(BalanceEticTablesIn):
    tables: List[BalanceTvaTableIn] = Field(min_length=1, max_length=1)


@router.get('/liasse/balance/dossiers/{preparation_id}/tva-documentaire')
def preparation_tva_documentaire(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_tva_documentaire_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/tva-documentaire', status_code=201)
def conserver_tva_documentaire(preparation_id: int, data: BalanceTvaIn,
                              current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_tva_documentaire_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalancePassageFiscalTableIn(BalanceEticTableIn):
    code: Literal['B12-N']


class BalancePassageFiscalIn(BalanceEticTablesIn):
    tables: List[BalancePassageFiscalTableIn] = Field(min_length=1, max_length=1)


@router.get('/liasse/balance/dossiers/{preparation_id}/passage-fiscal')
def preparation_passage_fiscal(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_passage_fiscal_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/passage-fiscal', status_code=201)
def conserver_passage_fiscal(preparation_id: int, data: BalancePassageFiscalIn,
                              current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_passage_fiscal_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceLiquidationIsTableIn(BalanceEticTableIn):
    code: Literal['LIQ-N']


class BalanceLiquidationIsIn(BalanceEticTablesIn):
    tables: List[BalanceLiquidationIsTableIn] = Field(min_length=1, max_length=1)


@router.get('/liasse/balance/dossiers/{preparation_id}/liquidation-is')
def preparation_liquidation_is(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_liquidation_is_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/liquidation-is', status_code=201)
def conserver_liquidation_is(preparation_id: int, data: BalanceLiquidationIsIn,
                            current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_liquidation_is_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceAcomptesIsTableIn(BalanceEticTableIn):
    code: Literal['AP-PROFIL', 'AP-LIGNES']


class BalanceAcomptesIsIn(BalanceEticTablesIn):
    tables: List[BalanceAcomptesIsTableIn] = Field(min_length=2, max_length=2)


@router.get('/liasse/balance/dossiers/{preparation_id}/acomptes-is')
def preparation_acomptes_is(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_acomptes_is_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/acomptes-is', status_code=201)
def conserver_acomptes_is(preparation_id: int, data: BalanceAcomptesIsIn,
                         current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_acomptes_is_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceTaxeProfessionnelleTableIn(BalanceEticTableIn):
    code: Literal['TP-P', 'TP-E']


class BalanceTaxeProfessionnelleIn(BalanceEticTablesIn):
    tables: List[BalanceTaxeProfessionnelleTableIn] = Field(min_length=2, max_length=2)


@router.get('/liasse/balance/dossiers/{preparation_id}/taxe-professionnelle')
def preparation_taxe_professionnelle(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_taxe_professionnelle_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'], 'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/taxe-professionnelle', status_code=201)
def conserver_taxe_professionnelle(preparation_id: int, data: BalanceTaxeProfessionnelleIn,
                                  current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_taxe_professionnelle_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceRemunerationsTiersTableIn(BalanceEticTableIn):
    code: Literal['T151-P', 'T151-B', 'T151-M']


class BalanceRemunerationsTiersIn(BalanceEticTablesIn):
    tables: List[BalanceRemunerationsTiersTableIn] = Field(min_length=3, max_length=3)


@router.get('/liasse/balance/dossiers/{preparation_id}/remunerations-tiers')
def preparation_remunerations_tiers(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_remunerations_tiers_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/remunerations-tiers', status_code=201)
def conserver_remunerations_tiers(preparation_id: int, data: BalanceRemunerationsTiersIn,
                                current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_remunerations_tiers_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceCreditsIsTableIn(BalanceEticTableIn):
    code: Literal['CR-PROFIL', 'CR-LIGNES']


class BalanceCreditsIsIn(BalanceEticTablesIn):
    tables: List[BalanceCreditsIsTableIn] = Field(min_length=2, max_length=2)


@router.get('/liasse/balance/dossiers/{preparation_id}/credits-is')
def preparation_credits_is(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_credits_is_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/credits-is', status_code=201)
def conserver_credits_is(preparation_id: int, data: BalanceCreditsIsIn,
                        current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_credits_is_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceCssTableIn(BalanceEticTableIn):
    code: Literal['CSS-N']


class BalanceCssIn(BalanceEticTablesIn):
    tables: List[BalanceCssTableIn] = Field(min_length=1, max_length=1)


@router.get('/liasse/balance/dossiers/{preparation_id}/css-documentaire')
def preparation_css(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_css_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/css-documentaire', status_code=201)
def conserver_css(preparation_id: int, data: BalanceCssIn,
                  current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_css_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceCotisationMinimaleTableIn(BalanceEticTableIn):
    code: Literal['CM-N']


class BalanceCotisationMinimaleIn(BalanceEticTablesIn):
    tables: List[BalanceCotisationMinimaleTableIn] = Field(min_length=1, max_length=1)


@router.get('/liasse/balance/dossiers/{preparation_id}/cotisation-minimale')
def preparation_cotisation_minimale(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_cotisation_minimale_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/cotisation-minimale', status_code=201)
def conserver_cotisation_minimale(preparation_id: int, data: BalanceCotisationMinimaleIn,
                                current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_cotisation_minimale_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceContexteFiscalTableIn(BalanceEticTableIn):
    code: Literal['CF-CM', 'CF-CSS', 'CF-CREDITS', 'CF-ACOMPTES']


class BalanceContexteFiscalIn(BalanceEticTablesIn):
    tables: List[BalanceContexteFiscalTableIn] = Field(min_length=4, max_length=4)


@router.get('/liasse/balance/dossiers/{preparation_id}/contexte-fiscal')
def preparation_contexte_fiscal(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_contexte_fiscal_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/contexte-fiscal', status_code=201)
def conserver_contexte_fiscal(preparation_id: int, data: BalanceContexteFiscalIn,
                              current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_contexte_fiscal_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceResultatCourantTableIn(BalanceEticTableIn):
    code: Literal['B13-N', 'B13-N1']


class BalanceResultatCourantIn(BalanceEticTablesIn):
    tables: List[BalanceResultatCourantTableIn] = Field(min_length=2, max_length=2)


@router.get('/liasse/balance/dossiers/{preparation_id}/resultat-courant')
def preparation_resultat_courant(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_resultat_courant_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/resultat-courant', status_code=201)
def conserver_resultat_courant(preparation_id: int, data: BalanceResultatCourantIn,
                              current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_resultat_courant_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceEmetteurTableIn(BalanceEticTableIn):
    code: Literal['B4-N', 'B4-N1']


class BalanceEmetteursIn(BalanceEticTablesIn):
    tables: List[BalanceEmetteurTableIn] = Field(min_length=2, max_length=2)


@router.get('/liasse/balance/dossiers/{preparation_id}/emetteurs')
def preparation_emetteurs(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_emetteurs_service import presentation
    dossier = preparation_balance(preparation_id, current_user, db)
    return {'id': dossier['id'], 'version': dossier['version'],
            'empreinte_sha256': dossier['empreinte_sha256'], **presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/emetteurs', status_code=201)
def conserver_emetteurs(preparation_id: int, data: BalanceEmetteursIn,
                        current_user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from services.balance_emetteurs_service import conserver
    return conserver(db, current_user, preparation_id, data)


class BalanceCessionTableIn(BalanceEticTableIn):
    code: Literal['B3']


class BalanceCessionsIn(BalanceEticTablesIn):
    tables: List[BalanceCessionTableIn] = Field(min_length=1,max_length=1)


@router.get('/liasse/balance/dossiers/{preparation_id}/cessions')
def preparation_cessions(preparation_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    from services.balance_cessions_service import presentation
    dossier=preparation_balance(preparation_id,current_user,db)
    return {'id':dossier['id'],'version':dossier['version'],
            'empreinte_sha256':dossier['empreinte_sha256'],**presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/cessions',status_code=201)
def conserver_cessions(preparation_id: int,data: BalanceCessionsIn,
                        current_user=Depends(requiert_ecriture),db: Session=Depends(get_db)):
    from services.balance_cessions_service import conserver
    return conserver(db,current_user,preparation_id,data)


class BalanceMouvementTableIn(BalanceEticTableIn):
    code: Literal['B2','B2bis','B5']


class BalanceMouvementsIn(BalanceEticTablesIn):
    tables: List[BalanceMouvementTableIn] = Field(min_length=3,max_length=3)


@router.get('/liasse/balance/dossiers/{preparation_id}/mouvements')
def preparation_mouvements(preparation_id: int,current_user=Depends(get_current_user),db: Session=Depends(get_db)):
    from services.balance_mouvements_service import presentation
    dossier=preparation_balance(preparation_id,current_user,db)
    return {'id':dossier['id'],'version':dossier['version'],'empreinte_sha256':dossier['empreinte_sha256'],**presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/mouvements',status_code=201)
def conserver_mouvements(preparation_id: int,data: BalanceMouvementsIn,current_user=Depends(requiert_ecriture),db: Session=Depends(get_db)):
    from services.balance_mouvements_service import conserver
    return conserver(db,current_user,preparation_id,data)


class BalanceRaccordLigneIn(BaseModel):
    model_config = {'extra':'forbid'}
    ligne: int = Field(strict=True,ge=1,le=100)
    compte: str = Field(max_length=50)


class BalanceRaccordTableIn(BaseModel):
    model_config = {'extra':'forbid'}
    code: Literal['B2','B2bis','B5']
    lignes: List[BalanceRaccordLigneIn] = Field(max_length=100)


class BalanceRaccordsMouvementsIn(BalanceCpcDetailIn):
    tables: List[BalanceRaccordTableIn] = Field(min_length=3,max_length=3)


@router.get('/liasse/balance/dossiers/{preparation_id}/raccords-mouvements')
def preparation_raccords_mouvements(preparation_id: int,current_user=Depends(get_current_user),db: Session=Depends(get_db)):
    from services.balance_raccords_mouvements_service import presentation
    dossier=preparation_balance(preparation_id,current_user,db)
    return {'id':dossier['id'],'version':dossier['version'],'empreinte_sha256':dossier['empreinte_sha256'],**presentation(dossier)}


@router.post('/liasse/balance/dossiers/{preparation_id}/raccords-mouvements',status_code=201)
def conserver_raccords_mouvements(preparation_id: int,data: BalanceRaccordsMouvementsIn,current_user=Depends(requiert_ecriture),db: Session=Depends(get_db)):
    from services.balance_raccords_mouvements_service import conserver
    return conserver(db,current_user,preparation_id,data)


@router.get("/source/{exercice}")
def source_etats(
    exercice: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Source comptable officielle des états de synthèse de l'exercice.

    Agrégation complète PostgreSQL des écritures validées, indépendante de la
    pagination du Journal. Les brouillons et écritures techniques de clôture
    sont exclus et signalés dans les métadonnées de contrôle.
    """
    from services.etats_synthese_service import source_etats_synthese
    return source_etats_synthese(db, current_user["societe_id"], exercice)




def _verifier_etic_modifiable(db: Session, societe_id: int, exercice: int):
    """Une ETIC intégrée à une liasse finalisée appartient à l'archive immuable."""
    archive = db.query(models.LiasseFiscaleArchive).filter_by(
        societe_id=societe_id, exercice=exercice
    ).first()
    if archive:
        raise HTTPException(
            409,
            "ETIC verrouillée : la liasse fiscale de cet exercice est déjà finalisée et archivée."
        )

class ETICSectionIn(BaseModel):
    contenu: Dict[str, Any]


@router.get("/etic/{exercice}")
def etic_exercice(
    exercice: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ETIC modèle normal : sections A1-A3, B1-B14 et C1-C5."""
    from services.etic_service import construire_etic
    try:
        data = construire_etic(db, current_user["societe_id"], exercice)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    archive = db.query(models.LiasseFiscaleArchive).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice
    ).order_by(models.LiasseFiscaleArchive.version.desc()).first()
    data["verrouillee"] = bool(archive)
    data["motif_verrouillage"] = (
        "Liasse fiscale finalisée : l'ETIC appartient désormais à l'archive immuable."
        if archive else None
    )
    return data


@router.put("/etic/{exercice}/{code}")
def enregistrer_section_etic(
    exercice: int,
    code: str,
    data: ETICSectionIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Enregistre uniquement les compléments extra-comptables d'une section ETIC."""
    _verifier_etic_modifiable(db, current_user["societe_id"], exercice)
    import json
    from services.etic_service import CODES_ETIC, valider_contenu_etic
    code = code.strip()
    if code not in CODES_ETIC:
        raise HTTPException(404, "Section ETIC inconnue")
    erreurs = valider_contenu_etic(db, current_user["societe_id"], exercice, code, data.contenu)
    if erreurs:
        raise HTTPException(422, f"Section {code} incomplète : " + " ".join(erreurs))
    # Garde-fou contre un JSON accidentellement énorme dans une cellule.
    if len(json.dumps(data.contenu, ensure_ascii=False, default=str)) > 100_000:
        raise HTTPException(413, "Contenu ETIC trop volumineux pour une section")

    rec = db.query(models.ETICSectionExercice).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice, code=code
    ).first()
    if not rec:
        rec = models.ETICSectionExercice(
            societe_id=current_user["societe_id"], exercice=exercice, code=code
        )
        db.add(rec)
    rec.contenu = data.contenu
    rec.updated_by = current_user.get("id")
    db.commit()
    db.refresh(rec)
    return {"message": f"Section {code} enregistrée", "code": code, "updated_at": rec.updated_at}


@router.delete("/etic/{exercice}/{code}")
def reinitialiser_section_etic(
    exercice: int,
    code: str,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    from services.etic_service import CODES_ETIC
    _verifier_etic_modifiable(db, current_user["societe_id"], exercice)
    if code not in CODES_ETIC:
        raise HTTPException(404, "Section ETIC inconnue")
    rec = db.query(models.ETICSectionExercice).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice, code=code
    ).first()
    if rec:
        db.delete(rec)
        db.commit()
    return {"message": f"Section {code} réinitialisée"}


class LigneEtat(BaseModel):
    type:    str = "ligne"          # titre | ligne | total
    label:   str
    valeurs: List[Optional[float]] = []
    niveau:  int = 0
    numero:  Optional[str] = None


class EtatPdfIn(BaseModel):
    titre:      str                 # ex: "BILAN — ACTIF"
    sous_titre: Optional[str] = None
    exercice:   int
    colonnes:   List[str]           # en-têtes des colonnes numériques
    lignes:     List[LigneEtat]
    nom_fichier: Optional[str] = None


@router.get("/pdf-officiel/{etat}/{exercice}")
def exporter_etat_pdf_officiel(
    etat: str,
    exercice: int,
    comparatif: bool = Query(False),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PDF recalculé côté serveur depuis la comptabilité officielle en base."""
    from pdf_generator import generer_etat_financier
    from services.etats_pdf_service import construire_etat_pdf_officiel

    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    if not societe:
        raise HTTPException(404, "Société introuvable")
    try:
        data = construire_etat_pdf_officiel(
            db, current_user["societe_id"], exercice, etat, comparatif=comparatif
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    pdf_bytes = generer_etat_financier(
        societe,
        titre=data["titre"],
        sous_titre=data.get("sous_titre"),
        exercice=exercice,
        colonnes=data["colonnes"],
        lignes=data["lignes"],
        periode_debut=data.get("periode_debut"),
        periode_fin=data.get("periode_fin"),
        paysage=data.get("paysage", False),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{data["nom_fichier"]}"',
            "X-HisabPro-Source": "comptabilite-serveur",
        },
    )


@router.post("/pdf")
def exporter_etat_pdf(
    data: EtatPdfIn,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compatibilité historique : les montants reçus du navigateur sont ignorés.

    Depuis le patch 054, un PDF financier HisabPro est toujours reconstruit en
    base afin qu'une requête modifiée ne puisse pas fabriquer un état officiel
    portant des montants arbitraires.
    """
    from pdf_generator import generer_etat_financier
    from services.etats_pdf_service import construire_etat_pdf_officiel, etat_depuis_titre

    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    if not societe:
        raise HTTPException(404, "Société introuvable")
    try:
        etat = etat_depuis_titre(data.titre)
        # Les anciens écrans indiquaient le comparatif par une colonne N-1.
        comparatif = any(str(data.exercice - 1) in str(c) for c in (data.colonnes or []))
        officiel = construire_etat_pdf_officiel(
            db, current_user["societe_id"], data.exercice, etat, comparatif=comparatif
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    pdf_bytes = generer_etat_financier(
        societe,
        titre=officiel["titre"],
        sous_titre=officiel.get("sous_titre"),
        exercice=data.exercice,
        colonnes=officiel["colonnes"],
        lignes=officiel["lignes"],
        periode_debut=officiel.get("periode_debut"),
        periode_fin=officiel.get("periode_fin"),
        paysage=officiel.get("paysage", False),
    )
    nom = officiel["nom_fichier"]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nom}"',
            "X-HisabPro-Source": "comptabilite-serveur",
        },
    )


# ── Patch 09.3 : liasse fiscale consolidée / archive / PDF ───────────────────

@router.get("/liasse/{exercice}")
def liasse_exercice(
    exercice: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Construit la liasse live et ses contrôles croisés.

    L'endpoint reste consultable avant clôture afin de préparer le dossier ;
    seuls les contrôles bloquants empêchent la finalisation immuable.
    """
    import json
    # Une liasse finalisée doit toujours être relue depuis son instantané immuable.
    # Cela évite qu'une modification ultérieure d'ETIC ou de paramétrage affiche
    # des chiffres "live" différents du PDF/Excel officiellement archivé.
    rec = db.query(models.LiasseFiscaleArchive).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice
    ).order_by(models.LiasseFiscaleArchive.version.desc()).first()
    if rec:
        data = json.loads(rec.contenu_json)
        data["archive"] = {
            "id": rec.id, "version": rec.version, "empreinte_sha256": rec.empreinte_sha256,
            "date_finalisation": rec.date_finalisation, "finalisee_par": rec.finalisee_par,
        }
        data["statut"] = "finalisee"
        return data

    from services.liasse_service import construire_liasse
    try:
        return construire_liasse(db, current_user["societe_id"], exercice)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.get("/liasse/{exercice}/archive")
def archive_liasse(
    exercice: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json
    rec = db.query(models.LiasseFiscaleArchive).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice
    ).order_by(models.LiasseFiscaleArchive.version.desc()).first()
    if not rec:
        raise HTTPException(404, "Aucune liasse fiscale finalisée pour cet exercice.")
    data = json.loads(rec.contenu_json)
    data["archive"] = {
        "id": rec.id, "version": rec.version, "empreinte_sha256": rec.empreinte_sha256,
        "date_finalisation": rec.date_finalisation, "finalisee_par": rec.finalisee_par,
    }
    data["statut"] = "finalisee"
    return data


@router.post("/liasse/{exercice}/finaliser")
def finaliser_liasse(
    exercice: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Fige la première version de la liasse si tous les contrôles bloquants passent."""
    from services.liasse_service import construire_liasse, contenu_canonique, empreinte_liasse
    existante = db.query(models.LiasseFiscaleArchive).filter_by(
        societe_id=current_user["societe_id"], exercice=exercice
    ).first()
    if existante:
        raise HTTPException(409, "La liasse de cet exercice est déjà finalisée et immuable.")
    try:
        data = construire_liasse(db, current_user["societe_id"], exercice)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    if not data.get("controles", {}).get("pret_a_finaliser"):
        raise HTTPException(409, detail={
            "message": "Finalisation bloquée : corrigez les contrôles de la liasse.",
            "controles": data.get("controles", {}),
        })
    canonical = contenu_canonique(data)
    digest = empreinte_liasse(data)
    rec = models.LiasseFiscaleArchive(
        societe_id=current_user["societe_id"], exercice=exercice, version=1,
        contenu_json=canonical, empreinte_sha256=digest,
        finalisee_par=current_user.get("id"),
    )
    db.add(rec)
    try:
        db.commit(); db.refresh(rec)
    except Exception:
        db.rollback()
        raise HTTPException(409, "Impossible de finaliser : une archive concurrente existe peut-être déjà.")
    return {
        "message": "Liasse fiscale finalisée et archivée.",
        "id": rec.id, "version": rec.version, "empreinte_sha256": rec.empreinte_sha256,
        "date_finalisation": rec.date_finalisation,
    }


@router.get("/liasse/{exercice}/pdf")
def exporter_liasse_pdf(
    exercice: int,
    archive: bool = Query(False, description="Exporter l'archive finale plutôt que le calcul live"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json
    from services.liasse_service import construire_liasse
    from services.liasse_pdf import generer_liasse_pdf

    societe_id = current_user["societe_id"]
    if archive:
        rec = db.query(models.LiasseFiscaleArchive).filter_by(
            societe_id=societe_id, exercice=exercice
        ).order_by(models.LiasseFiscaleArchive.version.desc()).first()
        if not rec:
            raise HTTPException(404, "Aucune archive finale de liasse n'est disponible.")
        data = json.loads(rec.contenu_json)
        data["archive"] = {
            "id": rec.id, "version": rec.version, "empreinte_sha256": rec.empreinte_sha256,
            "date_finalisation": rec.date_finalisation.isoformat() if rec.date_finalisation else None,
            "finalisee_par": rec.finalisee_par,
        }
        data["statut"] = "finalisee"
        suffixe = "FINAL"
    else:
        try:
            data = construire_liasse(db, societe_id, exercice)
        except ValueError as exc:
            raise HTTPException(404, str(exc))
        # Un recalcul live demandé explicitement reste provisoire, même si une
        # archive finale existe déjà. Seul archive=true exporte le document figé.
        suffixe = "PROVISOIRE"
    pdf = generer_liasse_pdf(data)
    ice = str(data.get("societe", {}).get("ice") or societe_id).replace(" ", "")
    nom = f"{ice}_LIASSE_{exercice}_{suffixe}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nom}"',
            "X-HisabPro-Liasse-Statut": suffixe,
        },
    )
