"""Fidélité des recettes existantes et absence de prévalidation humaine765."""
from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import re
import shutil
import socket
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pilotage765',ROOT/'docs/recette/generer_pilotage765.py')
pilotage=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilotage)


@pytest.fixture(scope='module')
def artefacts(tmp_path_factory):
    out=tmp_path_factory.mktemp('pilotage765')
    sources={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in pilotage.RECETTE.glob('*.xlsx')}
    resultat=pilotage.generer(out)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in sources.items())
    return out,resultat


def lignes(w):
    for domaine in pilotage.DOMAINES:
        for row in w[domaine].iter_rows(min_row=2,values_only=True):yield domaine,row


def test_cas_existants_et_statuts_humains_sans_succes_invente(artefacts):
    out,data=artefacts;w=load_workbook(out/(pilotage.STEM+'.xlsx'))
    rows=list(lignes(w))
    assert len(rows)==272
    assert Counter(v[0] for _,v in rows)=={'PRINCIPAL':218,'F755':14,'TIERS759':8,'TP761':8,'CR749':8,'AP751':8,'LIQ753':8}
    assert Counter(v[12] for _,v in rows)=={'Non testé':262,'Bloqué':10}
    assert all(all(v[i] is None for i in (13,14,17,18)) for _,v in rows)
    assert data['recette_utilisateur_executee'] is False and data['formules_office_executees'] is False
    assert w['Listes'].sheet_state=='hidden' and len(w.sheetnames)==20
    assert all(w[d].freeze_panes=='F2' for d in pilotage.DOMAINES)
    assert len({(v[0],v[2]) for _,v in rows})==272


def test_tous_les_champs_et_oracles_copies_sans_reinterpretation(artefacts):
    out,_=artefacts;w=load_workbook(out/(pilotage.STEM+'.xlsx'),read_only=True)
    sources={f:load_workbook(pilotage.RECETTE/f,read_only=True) for f in {v[19] for _,v in lignes(w)}}
    try:
        for _,v in lignes(w):
            f,onglet,n=v[19:22];raw=next(sources[f][onglet].iter_rows(min_row=n,max_row=n,values_only=True))
            if v[0]=='PRINCIPAL':
                assert tuple(v[1:13])==tuple(raw[:12])
                assert tuple(v[13:18])==(raw[12],raw[13],raw[14],raw[15],raw[16])
            else:
                assert tuple(v[2:13])==tuple(raw[:11])
                assert tuple(v[13:18])==(raw[11],raw[12],raw[14],raw[15],raw[13])
            assert v[18] is None
        main=next(v for _,v in lignes(w) if v[2]=='HP-FIS-001')
        assert '1 000' in main[6] and '200' in main[6]
    finally:
        for s in sources.values():s.close()
        w.close()


def test_liens_relatifs_pointent_vers_cas_et_sources_reels(artefacts):
    out,_=artefacts;w=load_workbook(out/(pilotage.STEM+'.xlsx'))
    for row in w['Ordre de passage'].iter_rows(min_row=2):
        lien=row[5].hyperlink
        assert lien and lien.target is None
        match=re.fullmatch(r"'(.+)'!A(\d+)",lien.location);assert match
        cible=w[match[1]];n=int(match[2]);assert cible.cell(n,1).value==row[0].value+'::'+row[2].value
        suivi=row[6].hyperlink;assert suivi and suivi.target is None
        match_suivi=re.fullmatch(r"'(.+)'!M(\d+)",suivi.location);assert match_suivi
        cible_suivi=w[match_suivi[1]];n_suivi=int(match_suivi[2])
        assert cible_suivi.cell(n_suivi,1).value==row[0].value and cible_suivi.cell(n_suivi,3).value==row[2].value
        assert cible.cell(n,3).hyperlink.location==suivi.location
    for d in pilotage.DOMAINES:
        for row in w[d].iter_rows(min_row=2):
            lien=row[19].hyperlink;assert lien.target==row[19].value
            assert lien.location==f"'{row[20].value}'!A{row[21].value}"
            assert (pilotage.RECETTE/lien.target).is_file()
            assert (pilotage.RECETTE/row[22].hyperlink.target).is_file()


def test_fiches_verticales_conservent_tous_les_caracteres_des_champs(artefacts):
    out,_=artefacts;w=load_workbook(out/(pilotage.STEM+'.xlsx'))
    attendus={(v[0]+'::'+v[2]):v for _,v in lignes(w)}
    groupes={};courant=None
    for a,b,_ in w['Fiches de lecture'].iter_rows(min_row=2,values_only=True):
        if a in attendus:
            courant=a;groupes[courant]={};continue
        if a and courant:
            champ=a.removesuffix(' (suite)');groupes[courant].setdefault(champ,[]);groupes[courant][champ].append(b)
    assert set(groupes)==set(attendus)
    for cle,v in attendus.items():
        for i in (0,1,2,3,5,6,7,8,9,10,11,15,16,19,20,21,22):
            assert ''.join(groupes[cle].get(pilotage.COLONNES[i],[]))==str(v[i] if v[i] is not None else '—')
    assert all(d.height is None or d.height<=380 for d in w['Fiches de lecture'].row_dimensions.values())


def test_ordre_principal_et_campagnes_separees(artefacts):
    out,_=artefacts;w=load_workbook(out/(pilotage.STEM+'.xlsx'))
    rows=list(w['Ordre de passage'].values)[1:]
    assert [r[1] for r in rows if r[0]=='PRINCIPAL']==list(range(1,219))
    campagnes=[r[0] for r in rows]
    for camp in set(campagnes):
        indices=[i for i,c in enumerate(campagnes) if c==camp]
        assert indices==list(range(min(indices),max(indices)+1))
    plan=' '.join(str(c.value or '') for row in w['Campagnes'] for c in row)
    assert '1425' not in plan and '1 425' in plan and '3 650' in plan
    assert 'Ne pas les assimiler aux honoraires 21 500 de 755' in plan


def test_formules_et_liste_de_statuts_referencent_les_plages_reelles(artefacts):
    out,_=artefacts;w=load_workbook(out/(pilotage.STEM+'.xlsx'))
    assert w.calculation.fullCalcOnLoad and w.calculation.forceFullCalc
    assert w.defined_names['StatutsRecette'].attr_text=="'Listes'!$A$1:$A$4"
    for i,d in enumerate(pilotage.DOMAINES,2):
        ws=w[d];dv=list(ws.data_validations.dataValidation);assert len(dv)==1
        assert dv[0].formula1=='StatutsRecette' and dv[0].showErrorMessage and dv[0].errorStyle=='stop'
        assert len(dv[0].sqref.ranges)==1
        plage=next(iter(dv[0].sqref.ranges))
        assert (plage.min_col,plage.min_row,plage.max_col,plage.max_row)==(13,2,13,ws.max_row)
        assert w['Synthèse'].cell(i,2).value==f'=COUNTIF(\'{d}\'!$M$2:$M${ws.max_row},B$1)'
        assert w['Synthèse'].cell(i,7).value==f'=IF(F{i}=E{i},0,(C{i}+D{i})/(F{i}-E{i}))'
    assert w['Synthèse']['F16'].value=='=SUM(F2:F15)'
    assert all(c.data_type!='f' for d in pilotage.DOMAINES for row in w[d] for c in row)


def test_source_commencant_par_egal_reste_un_texte(tmp_path):
    cas,preuves=pilotage.charger();cas[0]['valeurs'][6]='=HYPERLINK("https://example.invalid","source")'
    pilotage.classeur(tmp_path,cas,preuves);w=load_workbook(tmp_path/(pilotage.STEM+'.xlsx'))
    cellule=next(w[d].cell(n,7) for d in pilotage.DOMAINES for n in range(2,w[d].max_row+1) if w[d].cell(n,3).value==cas[0]['valeurs'][2])
    assert cellule.value.startswith('=HYPERLINK') and cellule.data_type=='s'


def copier_sources(tmp_path):
    for _,stem,*_ in pilotage.SOURCES:shutil.copy2(pilotage.RECETTE/(stem+'.xlsx'),tmp_path/(stem+'.xlsx'))
    return tmp_path


@pytest.mark.parametrize('colonne,valeur',[(11,'Réussi'),(12,'Résultat humain déjà noté'),(14,'preuve.png')])
def test_source_renseignee_refusee_sans_reinitialiser_les_reponses(tmp_path,colonne,valeur):
    rep=copier_sources(tmp_path);p=rep/'MODE_EMPLOI_TIERS759.xlsx';w=load_workbook(p);w['Fiscalité'].cell(2,colonne).value=valeur;w.save(p)
    avant=p.read_bytes();sortie=rep/'sortie'
    with pytest.raises(ValueError,match='déjà renseignée'):pilotage.generer(sortie,rep)
    assert p.read_bytes()==avant and not sortie.exists()


@pytest.mark.parametrize('erreur',['id_duplique','entete_inconnu','cas_supprime','statut_inconnu'])
def test_source_incoherente_refusee_avant_toute_sortie(tmp_path,erreur):
    rep=copier_sources(tmp_path);p=rep/'MODE_EMPLOI_TIERS759.xlsx';w=load_workbook(p);s=w['Fiscalité']
    if erreur=='id_duplique':s['A3']=s['A2'].value
    elif erreur=='entete_inconnu':s['A1']='Colonne ambiguë'
    elif erreur=='cas_supprime':s.delete_rows(2)
    else:s['K2']='Probablement OK'
    w.save(p);sortie=rep/'sortie'
    with pytest.raises(ValueError):pilotage.generer(sortie,rep)
    assert not sortie.exists()


def test_sortie_existante_refusee_avant_ecrasement(tmp_path):
    p=tmp_path/(pilotage.STEM+'.xlsx');p.write_bytes(b'RESULTATS HUMAINS A CONSERVER');avant=p.read_bytes()
    with pytest.raises(FileExistsError):pilotage.generer(tmp_path)
    assert p.read_bytes()==avant and len(list(tmp_path.iterdir()))==1


def test_generation_sans_connexion_reseau(artefacts,tmp_path,monkeypatch):
    def interdit(*a,**k):raise AssertionError('Connexion réseau interdite au générateur')
    monkeypatch.setattr(socket,'create_connection',interdit)
    result=pilotage.generer(tmp_path)
    assert result['base_consultee'] is False and result['nouvelles_regles_fiscales'] is False


def test_word_pdf_reels_et_liens_locaux(artefacts):
    out,_=artefacts
    with ZipFile(out/(pilotage.STEM+'.docx')) as z:
        assert z.testzip() is None
        for f in z.namelist():
            if f.endswith('.xml') or f.endswith('.rels'):ET.fromstring(z.read(f))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        doc=ET.fromstring(z.read('word/document.xml'));assert len(doc.findall('.//w:hyperlink',ns))>=20
        rels=ET.fromstring(z.read('word/_rels/document.xml.rels'))
        for rel in rels:
            if rel.attrib['Type'].endswith('/hyperlink'):
                cible=rel.attrib['Target'];assert not re.match(r'\w+://',cible)
                assert (pilotage.RECETTE/cible).resolve().is_file()
    pdf=PdfReader(out/(pilotage.STEM+'.pdf'));texte=' '.join(p.extract_text() or '' for p in pdf.pages)
    assert 6<=len(pdf.pages)<=12
    for phrase in ['262 Non testé','10 Bloqué','218','54','3 650','1 425','point 6','production non validée','275']:
        if phrase=='275':assert phrase not in texte
        else:assert phrase in texte,phrase
    assert sum(len(p.get('/Annots',[])) for p in pdf.pages)>=20
    assert '272 nouveaux tests' not in texte


def test_reference_guide_tp_corrigee_sans_statut_prevalide():
    w=load_workbook(pilotage.RECETTE/'MODE_EMPLOI_TP761.xlsx')
    rows=list(w['Fiscalité'].values)[1:]
    assert len(rows)==8 and all('guide761' in r[3] and 'guide759' not in r[3] for r in rows)
    assert all(r[10]=='Non testé' and all(v is None for v in r[11:15]) for r in rows)
