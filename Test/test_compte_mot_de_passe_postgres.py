"""Le verrou relit le hash courant, même si la session ORM l'a déjà chargé."""
from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import models
from auth import hash_password, verify_password
from routers.auth import changer_mot_de_passe, ChangementMotDePasse
from postgres_isole import cluster_isole, verifier_cible_isolee


def test_hash_deja_charge_relit_secret_apres_changement_postgres():
    with cluster_isole() as cluster:
        verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        engine = create_engine(cluster['url'])
        try:
            for table in (models.Societe.__table__, models.Utilisateur.__table__):
                table.create(engine)
            with Session(engine) as db:
                db.add(models.Societe(id=1, raison_sociale='Compte fictif PostgreSQL'))
                db.flush()
                db.add(models.Utilisateur(id=1, societe_id=1, nom='Compte fictif',email='test@example.com',
                                          hashed_password=hash_password('AncienSecret133!'),role='lecture',actif=True))
                db.commit()
            with Session(engine) as premiere, Session(engine) as ancienne:
                copie = ancienne.get(models.Utilisateur, 1)
                assert verify_password('AncienSecret133!', copie.hashed_password)
                changer_mot_de_passe(ChangementMotDePasse(mot_de_passe_actuel='AncienSecret133!',
                    nouveau_mot_de_passe='PremierNouveau133!'), {'id':1}, premiere)
                with pytest.raises(HTTPException) as exc:
                    changer_mot_de_passe(ChangementMotDePasse(mot_de_passe_actuel='AncienSecret133!',
                        nouveau_mot_de_passe='DeuxiemeNouveau133!'), {'id':1}, ancienne)
                assert exc.value.status_code == 400
            with Session(engine) as db:
                assert verify_password('PremierNouveau133!', db.get(models.Utilisateur,1).hashed_password)
        finally:
            engine.dispose()
