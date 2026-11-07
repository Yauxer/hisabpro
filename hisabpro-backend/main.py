from dotenv import load_dotenv
load_dotenv()  # ← DOIT être en premier avant tout os.getenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from services.api_validation_service import erreur_validation_json
import os
import uuid
from sqlalchemy import text

from database import engine, Base, SessionLocal
import models
from auth import decode_token

from routers import auth, ecritures, factures, employes, parametres, societe, tiers, modeles, references, multi_societes, articles, etats, fec, cloture, utilisateurs, inventaire, tva, exercices, fiscalite, recouvrement, echeanciers, dashboard, production, delais_paiement, plan_comptable
from routers import commercial
from routers import banque
from routers import rapprochement
from routers import immobilisations
from routers import grh
from routers import ras_reglements

# En production, les migrations sont exécutées séparément avec le rôle dédié.
from services.production_bootstrap_service import creation_schema_au_demarrage
if creation_schema_au_demarrage():
    from services.grh_bootstrap_service import initialiser_schema_developpement
    initialiser_schema_developpement(engine, Base.metadata)

app = FastAPI(
    title="HisabPro API",
    description="API de comptabilité marocaine — CGNC, TVA, CNSS, Liasse fiscale",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_exception_handler(RequestValidationError, erreur_validation_json)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# FACT.11 — journalisation applicative des actions modifiantes.
# Aucun corps de requête n'est conservé afin de ne pas dupliquer de données
# sensibles dans la piste d'audit. Les erreurs d'audit ne doivent jamais rendre
# indisponible l'application métier.
@app.middleware("http")
async def audit_actions_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    status_code = 500
    response = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
            db = SessionLocal()
            try:
                acteur_id = societe_id = None
                acteur_role = ""
                auth_header = request.headers.get("Authorization", "")
                if auth_header.lower().startswith("bearer "):
                    try:
                        payload = decode_token(auth_header.split(" ", 1)[1])
                        acteur_id = int(payload.get("sub")) if payload.get("sub") is not None else None
                        societe_id = int(payload.get("societe_id")) if payload.get("societe_id") is not None else None
                        if acteur_id is not None:
                            user = db.query(models.Utilisateur).filter_by(id=acteur_id).first()
                            if user:
                                if societe_id == user.societe_id:
                                    acteur_role = user.role or ""
                                else:
                                    liaison = db.query(models.UtilisateurSociete).filter_by(
                                        utilisateur_id=acteur_id, societe_id=societe_id, actif=True
                                    ).first()
                                    acteur_role = (liaison.role if liaison else "") or ""
                    except Exception:
                        pass
                db.execute(text("""
                    SELECT hisabpro_journaliser_action(
                        :sid, :uid, :role, :methode, :chemin, :statut, :succes, :ip, :rid
                    )
                """), {
                    "sid": societe_id, "uid": acteur_id, "role": acteur_role,
                    "methode": request.method, "chemin": request.url.path,
                    "statut": status_code, "succes": 200 <= status_code < 400,
                    "ip": request.client.host if request.client else None, "rid": request_id,
                })
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

# Routers
app.include_router(auth.router)
app.include_router(ecritures.router)
app.include_router(factures.router)
app.include_router(tva.router)
app.include_router(fiscalite.router)
app.include_router(employes.router)
app.include_router(grh.router)
app.include_router(parametres.router)
app.include_router(societe.router)
app.include_router(tiers.router)
app.include_router(modeles.router)
app.include_router(references.router_ref)
app.include_router(multi_societes.router)
app.include_router(articles.router)
app.include_router(articles.router_familles)
app.include_router(commercial.router_devis)
app.include_router(commercial.router_bc)
app.include_router(commercial.router_bl)
app.include_router(commercial.router_regl)
app.include_router(ras_reglements.router)
app.include_router(commercial.router_br)
app.include_router(banque.router)
app.include_router(rapprochement.router)
app.include_router(immobilisations.router)
import attachments
import lettrage
import avoirs
import acomptes
app.include_router(attachments.router)
app.include_router(avoirs.router)
app.include_router(acomptes.router)
app.include_router(etats.router)
app.include_router(fec.router)
app.include_router(cloture.router)
app.include_router(exercices.router)
app.include_router(utilisateurs.router)
app.include_router(inventaire.router)
app.include_router(lettrage.router)
app.include_router(recouvrement.router)
app.include_router(echeanciers.router)
app.include_router(dashboard.router)
app.include_router(production.router)
app.include_router(delais_paiement.router)
app.include_router(plan_comptable.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "HisabPro", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
