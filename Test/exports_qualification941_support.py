"""Vrais téléchargements individuels du snapshot,avec montant et logo."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib
from pypdf import PdfReader
from openpyxl import load_workbook

def verifier_exports(page,panel,feuille,libelle,montant,texte_pdf):
 preuves={}
 for format,label in [('pdf','Exporter la préparation PDF'),('xlsx','Exporter la préparation Excel')]:
  with page.expect_download() as dl:panel.get_by_role('button',name=label,exact=True).click()
  raw=Path(dl.value.path()).read_bytes()
  if format=='pdf':
   pdf=PdfReader(BytesIO(raw));assert texte_pdf in '\n'.join(p.extract_text() or '' for p in pdf.pages) and any(p.images for p in pdf.pages)
  else:
   w=load_workbook(BytesIO(raw));assert dict(list(w[feuille].values)[1:])[libelle]==montant;w.close()
   with ZipFile(BytesIO(raw)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
  preuves[format]={'sha256':hashlib.sha256(raw).hexdigest(),'montant_et_logo_verifies':True}
 return preuves
