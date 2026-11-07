"""Bornes de rendu pur : aucun accès SQL, droits et paie inchangés."""
from datetime import date,datetime
from io import BytesIO
from types import SimpleNamespace
import pytest
from pypdf import PdfReader
from services.grh_registre_pdf import generer_registre_absences_pdf


@pytest.mark.parametrize('motif',[
    '\n'*970+'FIN_MOTIF_FICTIF',
    '<preuve & source> '*50+'FIN_MOTIF_FICTIF',
],ids=['nombreux_sauts','texte_echappe'])
def test_registre_sans_logo_ne_tronque_pas_motif_et_historique(motif):
    assert len(motif)<=1000
    a={'id':1,'nom_employe':'Salarié fictif '+'N'*150,'type_absence':'conge',
       'date_debut':date(2026,11,1),'date_fin':date(2026,11,3),'jours_calendaires':3,
       'statut':'demande','motif':motif,'commentaire_decision':None,
       'historique':[{'created_at':datetime(2026,10,18),'ancien_statut':None,
           'nouveau_statut':'demande','acteur_id':1,'commentaire':motif}]}
    societe=SimpleNamespace(raison_sociale='Société fictive sans logo',logo_url=None)
    pdf=PdfReader(BytesIO(generer_registre_absences_pdf(societe,[a])))
    texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert texte.count('FIN_MOTIF_FICTIF')==2
    assert not any(p.images for p in pdf.pages)
    if motif.startswith('\n'):assert len(pdf.pages)>1
    else:assert ' '.join(texte.split()).count('<preuve & source>')==100
