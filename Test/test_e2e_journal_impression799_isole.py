"""Impression réelle d'un journal multipage, données fictives et PostgreSQL isolé."""
import hashlib,re
import pytest
from playwright.sync_api import expect
from pypdf import PdfReader
from cahier_formulaires773_support import laboratoire,ok
from cahier_suite777_support import core
from test_balance_etic_notes693_isole import (
 application,application103,application102,application101,application100,application099,
 application098,application097,application093,application092,application091,application090,
 application089,application087,migration)

@pytest.mark.parametrize('largeur',[1440,390])
def test_799_journal_impression_exhaustive_45_pieces_90_lignes(application,largeur,tmp_path):
 with laboratoire(application,largeur,tmp_path,'impression799') as (api,page,sid,preuve):
  refs={f'PRINT799-{i:03}' for i in range(45)}
  for ref in sorted(refs):
   ok(api.post('/api/ecritures',json={'date':'2025-01-02','journal':'BQ','reference':ref,'libelle':f'Pièce fictive impression {ref}','est_validee':True,'lignes':[{'compte':'5141','debit':100},{'compte':'1111','credit':100}]}),201)
  avant=core(application,sid);assert len(avant)==45
  page.goto(application['web_url']+'/journal');expect(page.get_by_role('button',name='Exporter CSV',exact=True)).to_be_enabled();expect(page.get_by_text('PRINT799-000',exact=True)).to_be_visible()
  page.emulate_media(media='print')
  preuve['impression799']={'pieces':45,'lignes':90,'total_debit':'4500.00','total_credit':'4500.00','geometrie':page.locator('main').evaluate('(el)=>({height:getComputedStyle(el).height,overflow:getComputedStyle(el).overflow,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight})')}
  chemin=tmp_path/f'journal799_{largeur}.pdf';page.pdf(path=str(chemin),prefer_css_page_size=True,print_background=True)
  pdf=PdfReader(chemin);texte='\n'.join(p.extract_text() or '' for p in pdf.pages);retrouvees=set(re.findall(r'PRINT799-\d{3}',texte))
  preuve['impression799'].update(pdf=str(chemin),sha256=hashlib.sha256(chemin.read_bytes()).hexdigest(),pages=len(pdf.pages),references_retrouvees=sorted(retrouvees),manquantes=sorted(refs-retrouvees))
  assert retrouvees==refs,preuve['impression799'];assert len(pdf.pages)>=2
  assert '4 500,00' in texte.replace('\u00a0',' ').replace('\u202f',' ') or '4.500,00' in texte
  assert not page.get_by_role('complementary',name='Navigation principale').is_visible()
  assert core(application,sid)==avant
  preuve['impression799']['ecritures_inchangees']=True
  page.emulate_media(media='screen');expect(page.get_by_role('button',name='Exporter CSV',exact=True)).to_be_enabled()
