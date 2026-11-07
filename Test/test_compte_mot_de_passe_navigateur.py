"""Formulaire React réel, requêtes API interceptées ; aucune donnée réelle."""
import subprocess
from pathlib import Path
import pytest
from browser_support import chromium_executable

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def bundle(tmp_path_factory):
    target = tmp_path_factory.mktemp('compte-react') / 'compte.js'
    js = '''const esbuild=require('esbuild'); esbuild.buildSync({stdin:{contents:`
    import React from 'react';import {createRoot} from 'react-dom/client';
    import CompteSecurite from './src/components/CompteSecurite.jsx';
    createRoot(document.getElementById('root')).render(<CompteSecurite/>);`,
    loader:'jsx',resolveDir:process.cwd()},bundle:true,jsx:'automatic',format:'iife',platform:'browser',outfile:process.argv[1],
    loader:{'.module.css':'local-css'},define:{'import.meta.env.VITE_API_URL':'"http://recette.test"',
    'import.meta.env.VITE_APP_VERSION':'"recette"'}});'''
    run = subprocess.run(['node', '-e', js, str(target)], cwd=ROOT, capture_output=True, text=True,
                         encoding='utf-8', timeout=30)
    assert run.returncode == 0, run.stderr
    return target.read_text(encoding='utf-8')


@pytest.mark.parametrize('reponse', [204, 400])
def test_confirmation_envoi_et_secret_efface_uniquement_si_succes(bundle, reponse):
    executable = chromium_executable()
    if not executable:
        pytest.skip('Chromium/Edge requis')
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            page = browser.new_page(viewport={'width':390,'height':900})
            calls = []; errors = []
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            page.route('http://recette.test/', lambda r: r.fulfill(body='<div id="root"></div>', content_type='text/html'))
            def api(route):
                calls.append(route.request.post_data_json)
                if reponse == 204:
                    route.fulfill(status=204)
                else:
                    route.fulfill(status=400, json={'detail':'Le mot de passe actuel est incorrect.'})
            page.route('**/api/auth/mot-de-passe', api)
            page.goto('http://recette.test/')
            page.evaluate("localStorage.setItem('hisabpro_token','recette');localStorage.setItem('hisabpro_role','lecture')")
            page.add_script_tag(content=bundle)
            page.get_by_label('Mot de passe actuel', exact=True).fill('AncienSecret133!')
            page.get_by_label('Nouveau mot de passe', exact=True).fill('NouveauSecret133!')
            page.get_by_label('Confirmer le nouveau mot de passe').fill('DifferentSecret133!')
            page.get_by_role('button',name='Modifier mon mot de passe').click()
            page.get_by_role('alert').filter(has_text='confirmation').wait_for()
            assert not calls
            page.get_by_label('Confirmer le nouveau mot de passe').fill('NouveauSecret133!')
            page.get_by_role('button',name='Modifier mon mot de passe').click()
            if reponse == 204:
                page.get_by_role('status').wait_for()
                assert page.locator('input[type=password]').count() == 0
                assert page.evaluate("localStorage.getItem('hisabpro_token')") is None
            else:
                page.get_by_role('alert').filter(has_text='actuel est incorrect').wait_for()
                assert page.evaluate("localStorage.getItem('hisabpro_token')") == 'recette'
            assert calls == [{'mot_de_passe_actuel':'AncienSecret133!', 'nouveau_mot_de_passe':'NouveauSecret133!'}]
            assert not errors
        finally:
            browser.close()
