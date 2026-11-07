"""Compatibilité HTTP multipart / configuration après correctifs dépendances."""
from io import StringIO
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.testclient import TestClient
from dotenv import dotenv_values


def test_fastapi_upload_multipart_et_champ_formulaire_restent_compatibles():
    app = FastAPI()

    @app.post("/upload")
    async def upload(document: UploadFile = File(...), reference: str = Form(...)):
        data = await document.read()
        await document.close()
        return {"nom": document.filename, "contenu": data.decode("utf-8"), "reference": reference}

    with TestClient(app) as client:
        response = client.post("/upload", files={"document": ("justificatif.txt", b"Preuve synthetique", "text/plain")},
                               data={"reference": "002"})
    assert response.status_code == 200
    assert response.json() == {"nom": "justificatif.txt", "contenu": "Preuve synthetique", "reference": "002"}


def test_dotenv_lit_configuration_synthetique_sans_reecrire_fichier(monkeypatch):
    monkeypatch.setenv("BASE_RECETTE", "http://recette.test")
    valeurs = dotenv_values(stream=StringIO('APP_ENV=production\nCORS_ORIGINS="${BASE_RECETTE}"\nSECRET_KEY="secret-fictif-de-recette"\n'))
    assert valeurs["APP_ENV"] == "production"
    assert valeurs["CORS_ORIGINS"] == "http://recette.test"
    assert valeurs["SECRET_KEY"] == "secret-fictif-de-recette"
