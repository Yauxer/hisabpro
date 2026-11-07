"""Livrables réellement générés : Word/PDF cohérents, suivi humain vierge et checklist à jour."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as E
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1]
G=R/'docs/guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO'
W={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def normaliser(s):return re.sub(r'\s+',' ',s).strip()


def test_671_word_pdf_courants_et_suivi_humain_vierge():
    with ZipFile(G.with_suffix('.docx')) as z:
        assert z.testzip() is None
        for nom in z.namelist():
            if nom.endswith('.xml'):E.fromstring(z.read(nom))
        doc=E.fromstring(z.read('word/document.xml'))
    word=normaliser(' '.join(t.text or '' for t in doc.findall('.//w:t',W)))
    reader=PdfReader(G.with_suffix('.pdf'))
    pdf=normaliser(' '.join(p.extract_text() or '' for p in reader.pages))
    assert len(reader.pages)>=18
    for texte in (word,pdf):
        for marqueur in ('Version 15 du 19 octobre 2026','Préparer depuis une commande',
            'Date d’annulation','Motif (facultatif)','Confirmer l’annulation','Réessayer',
            'Documents liés aux OD','Correspondance entre sociétés','124 000'):
            assert marqueur in texte,marqueur
        assert 'production : non validée' in texte
    lignes=[]
    for tr in doc.findall('.//w:tr',W):
        cellules=[normaliser(' '.join(t.text or '' for t in c.findall('.//w:t',W))) for c in tr.findall('w:tc',W)]
        if len(cellules)==4 and re.fullmatch(r'\d{2}',cellules[0]):lignes.append(cellules)
    assert [x[0] for x in lignes]==[f'{i:02d}' for i in range(1,18)]
    assert all(x[2:] == ['Non testé','À renseigner'] for x in lignes)


def test_671_checklist_73_distincte_matrice_70_et_interco_justifie():
    def tableau(path):
        data={}
        for l in path.read_text(encoding='utf8').splitlines():
            if l.startswith('|'):
                c=[s.strip() for s in l.split('|')[1:-1]]
                if len(c)>2 and c[2] in ('terminé','partiel','absent','bloqué'):
                    assert c[0] not in data
                    data[c[0]]=c
        return data
    c=tableau(R/'docs/audit/CHECKLIST_UTILISATEUR_20261007.md')
    assert len(c)==73 and Counter(x[2] for x in c.values())=={'terminé':40,'partiel':31,'absent':1,'bloqué':1}
    assert c['SEP20-01'][2]=='partiel'
    for rapport in ('rapport_societes_liees633.md','rapport_factures_liees635.md','rapport_consolidation_portable661.md'):
        assert rapport in c['SEP20-01'][3] and (R/'Test'/rapport).is_file()
    m=tableau(R/'docs/audit/MATRICE_COUVERTURE_HISABPRO.md')
    assert len(m)==70 and Counter(x[2] for x in m.values())=={'terminé':16,'partiel':49,'absent':1,'bloqué':4}

    # Les préparations internes759/761 existent ; elles ne valent pas dépôt officiel.
    for code,rapport,service in [('LIA-09F','rapport_remunerations_tiers759.md','balance_remunerations_tiers_service.py'),('LIA-09G','rapport_taxe_professionnelle761.md','balance_taxe_professionnelle_service.py')]:
        assert m[code][2]=='partiel' and rapport in m[code][3]
        assert (R/'Test'/rapport).is_file() and (R/'hisabpro-backend/services'/service).is_file()
    assert m['LIA-09B'][2]=='absent' and m['LIA-09C'][2]=='bloqué'


def test_671_totaux_annulation_et_liens_des_jeux_complementaires():
    # Oracle du petit parcours vente, distinct du jeu RAS et de ses pourcentages.
    debits=[Decimal('120'),Decimal('240'),Decimal('120'),Decimal('120')]
    assert sum(debits)==600 and sum(debits+[Decimal('120'),Decimal('120')])==840
    s=G.with_suffix('.md').read_text(encoding='utf8')
    assert 'débits = crédits = 600 MAD' in s and 'débits = crédits = 840 MAD' in s
    assert '17/10/2026' in s and '18/10/2026' in s
    for nom in ('ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.docx','ANNEXE_RECETTE_SOCIETES_LIEES_20261019.docx',
        'ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.docx'):
        assert nom in s and (R/'docs/recette'/nom).is_file()
    for nom in ('ANNULATION_REGLEMENT_655.md','RAS_DOCUMENTS_647.md','SOCIETES_LIEES_633.md','FACTURES_CORRESPONDANTES_635.md','REPRISES_PROVISIONS_615.md'):
        assert nom in s and (R/'docs'/nom).is_file()
