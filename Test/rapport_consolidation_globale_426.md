# Consolidation globale426 — sources figées avant428

Nouvelle exécution du12octobre à21:00UTC, après intégration des exports423. Les preuves411échouée et419interrompue restent conservées ;aucun ancien résultat ni artefact remplacé. Le runner ne lit aucune.env et utilise seulement des fixtures synthétiques protégées,avec PostgreSQL jetable/nonce et Edge pour les parcours connectés. Le banc07b3 non isolé est explicitement exclu.

## Résultat réellement exécuté

3422 cas :3332 réussis,60 échoués,30 erreurs,0 ignorés ;5646.729s ;exitnon récupéré (wrapper interrompu ;XML/log complets en échec) ;729empreintes inchangées.

Les sourcesPython/SQL/frontend/tests/configuration/assets ont été figées avant l'exécution puis comparées après ;729empreintes identiques. Aucun code ne change pendant la preuve. Les documents de couverture préparés indépendamment ne sont pas des résultats de tests métier supplémentaires.

Fichiers de preuve locale :.codex-tests/consolidation426_globale.log,.xml,.sources.json ;fichier.exit absent,aucun code de sortie inventé. Les suites ciblées423/414/415/416/417 ne sont pas additionnées àce total. Cette exécution est en échec ;elle ne valide ni recette utilisateur ni conformité réglementaire ouproduction.

## Échecs,erreurs oucas ignorés

- Test.test_e2e_immobilisations_degressif_isole::test_edge_cinq_dotations_degressives_et_acquisition_definitive_conservee :failure

```text
Test\test_e2e_immobilisations_degressif_isole.py:76: in test_edge_cinq_dotations_degressives_et_acquisition_definitive_conservee
    assert ligne.locator('td').all_text_contents()[3:6] == [mad(dot), mad(cumul), mad(vnc)]
E   AssertionError: assert [] == ['8.640,00 MA...2.960,00 MAD']
E     
E     Right contains 3 more items, first extra item: '8.640,00 MAD'
E     
E     Full diff:
E     + []
E     - [
E     -     '8.640,00 MAD',...
E     
E     ...Full output truncated (3 lines hidden), use '-vv' to show
```

- Test.test_rapprochement_propositions_historiques_isole::test_releve_inconnu_ui_ne_devient_pas_zero_et_proposition_certaine_possible[1365] :failure

```text
Test\test_rapprochement_propositions_historiques_isole.py:46: in test_releve_inconnu_ui_ne_devient_pas_zero_et_proposition_certaine_possible
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_rapprochement_propositions_historiques_isole::test_releve_inconnu_ui_ne_devient_pas_zero_et_proposition_certaine_possible[390] :failure

```text
Test\test_rapprochement_propositions_historiques_isole.py:46: in test_releve_inconnu_ui_ne_devient_pas_zero_et_proposition_certaine_possible
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_ras_lecture_conservation::test_editeur_navigateur_conserve_ras_10 :failure

```text
Test\test_ras_lecture_conservation.py:95: in test_editeur_navigateur_conserve_ras_10
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_inter_exercices_isole::test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens[1365-vente] :failure

```text
Test\test_reglements_inter_exercices_isole.py:62: in test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_inter_exercices_isole::test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens[1365-achat] :failure

```text
Test\test_reglements_inter_exercices_isole.py:62: in test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_inter_exercices_isole::test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens[390-vente] :failure

```text
Test\test_reglements_inter_exercices_isole.py:62: in test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_inter_exercices_isole::test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens[390-achat] :failure

```text
Test\test_reglements_inter_exercices_isole.py:62: in test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_pagination_isole::test_paiement_facture_hors_premiere_page[1365-vente] :failure

```text
Test\test_reglements_pagination_isole.py:32: in test_paiement_facture_hors_premiere_page
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_pagination_isole::test_paiement_facture_hors_premiere_page[1365-achat] :failure

```text
Test\test_reglements_pagination_isole.py:32: in test_paiement_facture_hors_premiere_page
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_pagination_isole::test_paiement_facture_hors_premiere_page[390-vente] :failure

```text
Test\test_reglements_pagination_isole.py:32: in test_paiement_facture_hors_premiere_page
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_reglements_pagination_isole::test_paiement_facture_hors_premiere_page[390-achat] :failure

```text
Test\test_reglements_pagination_isole.py:32: in test_paiement_facture_hors_premiere_page
    with sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_session132_admin_exercices_navigateur::test_creation_dates_explicites_et_selection_sans_rechargement :error

```text
Test\test_session132_admin_exercices_navigateur.py:25: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', '\nconst esbuild=require(\'esbuild\');\nesbuild.buildSync({stdin:{contents:`import React from \'react\';\nimport {createRoot} from \'react-dom/client\';\nimport {ExerciceProvider} from \'./src/data/ExerciceContext.jsx\';\nimport GestionExercices from \'./src/components/GestionExercices.jsx\';\ncreateRoot(document.getElementById(\'root\')).render(<ExerciceProvider><GestionExercices/></ExerciceProvider>);`,\nloader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\ndefine:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});\n', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\exercices-react0\\exercices.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_exercices_navigateur::test_doublon_conserve_formulaire_et_affiche_message_serveur :error

```text
Test\test_session132_admin_exercices_navigateur.py:25: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', '\nconst esbuild=require(\'esbuild\');\nesbuild.buildSync({stdin:{contents:`import React from \'react\';\nimport {createRoot} from \'react-dom/client\';\nimport {ExerciceProvider} from \'./src/data/ExerciceContext.jsx\';\nimport GestionExercices from \'./src/components/GestionExercices.jsx\';\ncreateRoot(document.getElementById(\'root\')).render(<ExerciceProvider><GestionExercices/></ExerciceProvider>);`,\nloader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\ndefine:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});\n', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\exercices-react0\\exercices.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_exercices_navigateur::test_lecture_seule_ne_declenche_aucune_preparation :error

```text
Test\test_session132_admin_exercices_navigateur.py:25: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', '\nconst esbuild=require(\'esbuild\');\nesbuild.buildSync({stdin:{contents:`import React from \'react\';\nimport {createRoot} from \'react-dom/client\';\nimport {ExerciceProvider} from \'./src/data/ExerciceContext.jsx\';\nimport GestionExercices from \'./src/components/GestionExercices.jsx\';\ncreateRoot(document.getElementById(\'root\')).render(<ExerciceProvider><GestionExercices/></ExerciceProvider>);`,\nloader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\ndefine:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});\n', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\exercices-react0\\exercices.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_exercices_navigateur::test_preparer_suivant_et_synchronisation_explicitement_declenches :error

```text
Test\test_session132_admin_exercices_navigateur.py:25: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', '\nconst esbuild=require(\'esbuild\');\nesbuild.buildSync({stdin:{contents:`import React from \'react\';\nimport {createRoot} from \'react-dom/client\';\nimport {ExerciceProvider} from \'./src/data/ExerciceContext.jsx\';\nimport GestionExercices from \'./src/components/GestionExercices.jsx\';\ncreateRoot(document.getElementById(\'root\')).render(<ExerciceProvider><GestionExercices/></ExerciceProvider>);`,\nloader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\ndefine:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});\n', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\exercices-react0\\exercices.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_navigateur::test_confirmation_et_actualisation_retrait_acces[False] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react0\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_navigateur::test_confirmation_et_actualisation_retrait_acces[True] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react0\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_navigateur::test_invitation_et_erreurs_sans_rechargement[200] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react0\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_navigateur::test_invitation_et_erreurs_sans_rechargement[404] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react0\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_navigateur::test_invitation_et_erreurs_sans_rechargement[409] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react0\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_plan_navigateur::test_plan_absent_ne_se_prepare_pas_sans_action_admin[admin] :error

```text
Test\test_session132_admin_plan_navigateur.py:31: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', '\nconst fs=require(\'node:fs\'),esbuild=require(\'esbuild\');\nconst source=fs.readFileSync(\'src/components/Layout.jsx\',\'utf8\');\nconst component=source.slice(source.indexOf(\'const LABEL_STATUT\')).replace(\'export default function Layout\',\'function Layout\');\nconst prefix=`import React,{useEffect,useState,useRef,useCallback} from \'react\';import{createRoot}from\'react-dom/client\';\nimport{useLocation,MemoryRouter}from\'react-router-dom\';\nimport{API_BASE,getToken,planComptableAPI,estAdmin,formatErreurAPI}from\'./src/services/api.js\';\nimport{cleCachePlan,restaurerPlanSociete,enregistrerPlanSociete,EVENEMENT_PLAN_MODIFIE}from\'./src/data/planComptableCache.js\';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst Sidebar=()=>null,SelecteurSociete=()=>null,Outlet=()=><div>Page société chargée</div>;\nconst useModules=()=>({societe:{id:1},chargement:false});\nconst useExercice=()=>({annee:2026,setAnnee:()=>{},exercice:null,exercices:[],chargementExercices:false});`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById(\'root\')).render(<MemoryRouter><Layout/></MemoryRouter>);`,\nloader:\'jsx\',resolveDir:process.cwd()},bundle:true,format:\'iife\',platform:\'browser\',outfile:process.argv[1],\ndefine:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});\n', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\plan-react0\\plan.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_plan_navigateur::test_plan_absent_ne_se_prepare_pas_sans_action_admin[lecture] :error

```text
Test\test_session132_admin_plan_navigateur.py:31: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', '\nconst fs=require(\'node:fs\'),esbuild=require(\'esbuild\');\nconst source=fs.readFileSync(\'src/components/Layout.jsx\',\'utf8\');\nconst component=source.slice(source.indexOf(\'const LABEL_STATUT\')).replace(\'export default function Layout\',\'function Layout\');\nconst prefix=`import React,{useEffect,useState,useRef,useCallback} from \'react\';import{createRoot}from\'react-dom/client\';\nimport{useLocation,MemoryRouter}from\'react-router-dom\';\nimport{API_BASE,getToken,planComptableAPI,estAdmin,formatErreurAPI}from\'./src/services/api.js\';\nimport{cleCachePlan,restaurerPlanSociete,enregistrerPlanSociete,EVENEMENT_PLAN_MODIFIE}from\'./src/data/planComptableCache.js\';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst Sidebar=()=>null,SelecteurSociete=()=>null,Outlet=()=><div>Page société chargée</div>;\nconst useModules=()=>({societe:{id:1},chargement:false});\nconst useExercice=()=>({annee:2026,setAnnee:()=>{},exercice:null,exercices:[],chargementExercices:false});`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById(\'root\')).render(<MemoryRouter><Layout/></MemoryRouter>);`,\nloader:\'jsx\',resolveDir:process.cwd()},bundle:true,format:\'iife\',platform:\'browser\',outfile:process.argv[1],\ndefine:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});\n', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\plan-react0\\plan.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_statuts_invites::test_bascule_ui_invite_desactive_globalement_modifie_seulement_acces[True] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react1\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_admin_statuts_invites::test_bascule_ui_invite_desactive_globalement_modifie_seulement_acces[False] :error

```text
Test\test_session132_admin_navigateur.py:39: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Parametres.jsx','utf8');\nconst component=source.slice(source.indexOf('function OngletUtilisateurs()'),source.indexOf('function OngletBanques()'));\nif(!component.includes('async function supprimer')) throw new Error('Composant utilisateurs introuvable');\nconst prefix=`import React,{useState,useEffect} from 'react';\nimport {createRoot} from 'react-dom/client';\nconst styles=new Proxy({}, {get:(_,key)=>key});\nconst LIBELLE_ROLE={admin:'Administrateur',lecture:'Consultation seule',comptable:'Comptable'};\nconst setRole=()=>{};\nconst authAPI={me:async()=>({role:'admin',societe_id:1})};\nconst API_BASE='http://recette.test';\nconst formatErreurAPI=detail=>typeof detail==='string'?detail:'Erreur serveur';\nconst utilisateursAPI={\n lister:async()=>window.testUsers.map(u=>({...u})),\n roles:async()=>[{code:'admin',libelle:'Administrateur'},{code:'comptable',libelle:'Comptable'},{code:'lecture',libelle:'Consultation seule'}],\n supprimer:async id=>{window.lastDeleted=id;window.testUsers=window.testUsers.filter(u=>u.id!==id)},\n modifier:async(id,body)=>{window.lastModified={id,body};window.testUsers=window.testUsers.map(u=>u.id!==id?u:\n  u.acces_invite&&body.actif!==undefined?{...u,actif_acces:body.actif,actif:u.actif_compte!==false&&body.actif}:{...u,...body})},\n};`;\nesbuild.buildSync({stdin:{contents:prefix+component+`createRoot(document.getElementById('root')).render(<OngletUtilisateurs/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,format:'iife',platform:'browser',outfile:process.argv[1]});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\admin-react1\\admin.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_import_csv_reel_et_n1_indisponible :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_structure_csv_invalide_refusee_avant_api[compte;solde\n1111;100] :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_structure_csv_invalide_refusee_avant_api[compte;debit;credit;debit\n1111;0;100;0] :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_structure_csv_invalide_refusee_avant_api[compte;debit;credit;solde\n1111;0;100;100] :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_import_xlsx_reel :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_changement_fichier_invalide_ancienne_preparation :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_reponse_en_vol_ne_republie_pas_balance_remplacee :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_export_excel_reel_chiffres_et_limites :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_conservation_et_rechargement_sans_fichier :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_balance_navigateur::test_lecture_consulte_versions_sans_action_ecriture :error

```text
Test\test_session132_balance_navigateur.py:22: in bundle
    assert run.returncode == 0, run.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', 'const esbuild=require(\'esbuild\'); esbuild.buildSync({stdin:{contents:`\n    import React from \'react\'; import {createRoot} from \'react-dom/client\';\n    import ImportBalanceLiasse from \'./src/components/ImportBalanceLiasse.jsx\';\n    createRoot(document.getElementById(\'root\')).render(<ImportBalanceLiasse exercice={2025}/>);`,\n    loader:\'jsx\',resolveDir:process.cwd()},bundle:true,jsx:\'automatic\',format:\'iife\',platform:\'browser\',outfile:process.argv[1],\n    define:{\'import.meta.env.VITE_API_URL\':\'"http://recette.test"\',\'import.meta.env.VITE_APP_VERSION\':\'"recette"\'}});', 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\balance-react0\\balance.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session132_cahier_recette::test_procedures_powershell_syntaxe_analysee_sans_execution :failure

```text
Test\test_session132_cahier_recette.py:282: in test_procedures_powershell_syntaxe_analysee_sans_execution
    assert result.returncode==0,result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['powershell', '-NoProfile', '-NonInteractive', '-Command', "\n$document = Get-Content -LiteralPath 'docs/EXPLOITATION_HISABPRO.md' -Raw -Encoding UTF8\n$blocs = [regex]::Matches($document, '(?s)```powershell\\r?\\n(.*?)```')\nif ($blocs.Count -lt 10) { throw 'Blocs de procédure manquants.' }\nforeach ($bloc in $blocs) {\n    $tokensRecette = $null\n    $erreursRecette = $null\n    $null = [System.Management.Automation.Language.Parser]::ParseInput($bloc.Groups[1].Value, [ref]$tokensRecette, [ref]$erreursRecette)\n    if ($erreursRecette.Count) { throw ($erreursRecette | Out-String) }\n}\nWrite-Output ('Syntaxe analysée : ' + $blocs.Count + ' blocs ; aucune commande métier exécutée.')\n"], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_cloture_auxiliaires_navigateur::test_auxiliaires_et_soldes_opposes_restent_visibles[1366] :error

```text
Test\test_session133_cloture_auxiliaires_navigateur.py:29: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Cloture.jsx','utf8');\nconst marker=source.indexOf('Aperçu des à-nouveaux sur {annee + 1}');\nconst begin=source.lastIndexOf('<details',marker),end=source.indexOf('</details>',marker)+10;\nif(begin<0||end<10) throw new Error('Apercu AN introuvable');\nconst body=`import React from 'react';import {createRoot} from 'react-dom/client';\nimport {formatMAD} from './src/data/donnees.js';import {trouverCompte} from './src/data/planComptes.js';\nconst etat=window.etatTest,annee=2025,styles=new Proxy({}, {get:(_,k)=>k});\ncreateRoot(document.getElementById('root')).render(${source.slice(begin,end)});`;\nesbuild.buildSync({stdin:{contents:body,loader:'jsx',resolveDir:process.cwd()},bundle:true,\nplatform:'browser',format:'iife',jsx:'automatic',outfile:process.argv[1]});esbuild.stop();\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\cloture-aux-react0\\cloture.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_cloture_auxiliaires_navigateur::test_auxiliaires_et_soldes_opposes_restent_visibles[390] :error

```text
Test\test_session133_cloture_auxiliaires_navigateur.py:29: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst fs=require('node:fs'), esbuild=require('esbuild');\nconst source=fs.readFileSync('src/pages/Cloture.jsx','utf8');\nconst marker=source.indexOf('Aperçu des à-nouveaux sur {annee + 1}');\nconst begin=source.lastIndexOf('<details',marker),end=source.indexOf('</details>',marker)+10;\nif(begin<0||end<10) throw new Error('Apercu AN introuvable');\nconst body=`import React from 'react';import {createRoot} from 'react-dom/client';\nimport {formatMAD} from './src/data/donnees.js';import {trouverCompte} from './src/data/planComptes.js';\nconst etat=window.etatTest,annee=2025,styles=new Proxy({}, {get:(_,k)=>k});\ncreateRoot(document.getElementById('root')).render(${source.slice(begin,end)});`;\nesbuild.buildSync({stdin:{contents:body,loader:'jsx',resolveDir:process.cwd()},bundle:true,\nplatform:'browser',format:'iife',jsx:'automatic',outfile:process.argv[1]});esbuild.stop();\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\cloture-aux-react0\\cloture.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_fr_preserve_centimes_dates_et_reference_litterale[Europe/Paris- ] :failure

```text
Test\test_session133_releve_import.py:28: in test_csv_fr_preserve_centimes_dates_et_reference_litterale
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_fr_preserve_centimes_dates_et_reference_litterale[Europe/Paris-\xa0] :failure

```text
Test\test_session133_releve_import.py:28: in test_csv_fr_preserve_centimes_dates_et_reference_litterale
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_fr_preserve_centimes_dates_et_reference_litterale[Europe/Paris-\u202f] :failure

```text
Test\test_session133_releve_import.py:28: in test_csv_fr_preserve_centimes_dates_et_reference_litterale
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_fr_preserve_centimes_dates_et_reference_litterale[America/Los_Angeles- ] :failure

```text
Test\test_session133_releve_import.py:28: in test_csv_fr_preserve_centimes_dates_et_reference_litterale
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_fr_preserve_centimes_dates_et_reference_litterale[America/Los_Angeles-\xa0] :failure

```text
Test\test_session133_releve_import.py:28: in test_csv_fr_preserve_centimes_dates_et_reference_litterale
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_fr_preserve_centimes_dates_et_reference_litterale[America/Los_Angeles-\u202f] :failure

```text
Test\test_session133_releve_import.py:28: in test_csv_fr_preserve_centimes_dates_et_reference_litterale
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_variantes_csv_documentees[Date,Libell\xe9,Montant\n2025-01-01,"Virement, recette","123,45"\n2025-01-02,Frais,-10.50-attendu0] :failure

```text
Test\test_session133_releve_import.py:42: in test_variantes_csv_documentees
    resultat = lire(csv=csv)
               ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_variantes_csv_documentees[sep=;\nDate;Libell\xe9;Montant;Sens\n01/01/2025;"Note; avec ""guillemets""";50;Cr\xe9dit-attendu1] :failure

```text
Test\test_session133_releve_import.py:42: in test_variantes_csv_documentees
    resultat = lire(csv=csv)
               ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_variantes_csv_documentees[Date\tMontant\n2025-01-01\t-10-attendu2] :failure

```text
Test\test_session133_releve_import.py:42: in test_variantes_csv_documentees
    resultat = lire(csv=csv)
               ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_variantes_csv_documentees[Date;Montant;Sens\n2025-01-01;20;D\n2025-01-02;20;C-attendu3] :failure

```text
Test\test_session133_releve_import.py:42: in test_variantes_csv_documentees
    resultat = lire(csv=csv)
               ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_variantes_csv_documentees[Date;Libell\xe9;Montant\n2025-01-01;"Libell\xe9\nmultiligne";20-attendu4] :failure

```text
Test\test_session133_releve_import.py:42: in test_variantes_csv_documentees
    resultat = lire(csv=csv)
               ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_invalide_refuse_tout_le_fichier[31/02/2025] :failure

```text
Test\test_session133_releve_import.py:49: in test_date_invalide_refuse_tout_le_fichier
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_invalide_refuse_tout_le_fichier[2025-02-29] :failure

```text
Test\test_session133_releve_import.py:49: in test_date_invalide_refuse_tout_le_fichier
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_invalide_refuse_tout_le_fichier[04-03-2025] :failure

```text
Test\test_session133_releve_import.py:49: in test_date_invalide_refuse_tout_le_fichier
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_invalide_refuse_tout_le_fichier[03/04/25] :failure

```text
Test\test_session133_releve_import.py:49: in test_date_invalide_refuse_tout_le_fichier
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_invalide_refuse_tout_le_fichier[] :failure

```text
Test\test_session133_releve_import.py:49: in test_date_invalide_refuse_tout_le_fichier
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_invalide_refuse_tout_le_fichier[2025-13-01] :failure

```text
Test\test_session133_releve_import.py:49: in test_date_invalide_refuse_tout_le_fichier
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[12x] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[NaN] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[Infinity] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[1.234] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[1,234.56] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[1 23,45] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[0] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[True] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_montant_invalide_non_tronque_et_aucun_import_partiel[1e100] :failure

```text
Test\test_session133_releve_import.py:56: in test_montant_invalide_non_tronque_et_aucun_import_partiel
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows0] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows1] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows2] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows3] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows4] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows5] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows6] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_ambiguite_et_double_sens_refuses[rows7] :failure

```text
Test\test_session133_releve_import.py:72: in test_ambiguite_et_double_sens_refuses
    assert "erreur" in lire(rows=rows)
                       ^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_date_operation_expresse_prime_sur_colonne_valeur_non_utilisee :failure

```text
Test\test_session133_releve_import.py:76: in test_date_operation_expresse_prime_sur_colonne_valeur_non_utilisee
    resultat = lire(rows=[["Date opération", "Date valeur", "Débit", "Crédit", "Solde"],
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_excel_reel_et_csv_windows1252 :failure

```text
Test\test_session133_releve_import.py:90: in test_excel_reel_et_csv_windows1252
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import * as XLSX from 'xlsx';import {dateReleve,lignesDepuisTableauReleve,decoderCsv,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst jour=new Date(2025,3,3),wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet([['Date','Débit','Crédit'],[jour,0,1234.56]]),'Relevé');\nconst buf=XLSX.write(wb,{type:'buffer',bookType:'xlsx',cellDates:true});const lu=XLSX.read(buf,{type:'buffer',cellDates:true});\nconst rows=XLSX.utils.sheet_to_json(lu.Sheets[lu.SheetNames[0]],{header:1,defval:''});\nconst latin=Buffer.from('Date;Libellé;Montant\\n03/04/2025;Déjà réglé;12,34','latin1');\nconsole.log(JSON.stringify({excel:lignesDepuisTableauReleve(rows),csv:lignesDepuisTableauReleve(tableauDepuisCsv(decoderCsv(latin)))}));"], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_malforme_refuse[Date;Montant\n2025-01-01;"20] :failure

```text
Test\test_session133_releve_import.py:99: in test_csv_malforme_refuse
    assert "erreur" in lire(csv=csv)
                       ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_malforme_refuse[Date;Montant\n2025-01-01;"20"x] :failure

```text
Test\test_session133_releve_import.py:99: in test_csv_malforme_refuse
    assert "erreur" in lire(csv=csv)
                       ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import::test_csv_malforme_refuse[texte sans en-t\xeate] :failure

```text
Test\test_session133_releve_import.py:99: in test_csv_malforme_refuse
    assert "erreur" in lire(csv=csv)
                       ^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import_navigateur::test_import_csv_fr_transmet_dates_et_montants_exacts_et_rafraichit[utf-8-sig-1366] :error

```text
Test\test_session133_releve_import_navigateur.py:27: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst esbuild=require('esbuild');\nesbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';\nimport Banque from './src/pages/RapprochementBancaire.jsx';createRoot(document.getElementById('root')).render(<Banque/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',\ndefine:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){\nb.onLoad({filter:/ExerciceContext\\.jsx$/},()=>({contents:`export function useExercice(){return {annee:2025,exercice:{date_debut:'2025-01-01',date_fin:'2025-12-31',statut:'ouvert'}}}`,loader:'js'}));\nb.onLoad({filter:/ModulesContext\\.jsx$/},()=>({contents:'export function useModules(){return {societe:{id:1}}}',loader:'js'}));\nb.onLoad({filter:/\\.module\\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));\n}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\releve-import-react0\\releve.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import_navigateur::test_import_csv_fr_transmet_dates_et_montants_exacts_et_rafraichit[utf-8-sig-390] :error

```text
Test\test_session133_releve_import_navigateur.py:27: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst esbuild=require('esbuild');\nesbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';\nimport Banque from './src/pages/RapprochementBancaire.jsx';createRoot(document.getElementById('root')).render(<Banque/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',\ndefine:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){\nb.onLoad({filter:/ExerciceContext\\.jsx$/},()=>({contents:`export function useExercice(){return {annee:2025,exercice:{date_debut:'2025-01-01',date_fin:'2025-12-31',statut:'ouvert'}}}`,loader:'js'}));\nb.onLoad({filter:/ModulesContext\\.jsx$/},()=>({contents:'export function useModules(){return {societe:{id:1}}}',loader:'js'}));\nb.onLoad({filter:/\\.module\\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));\n}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\releve-import-react0\\releve.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import_navigateur::test_import_csv_fr_transmet_dates_et_montants_exacts_et_rafraichit[cp1252-1366] :error

```text
Test\test_session133_releve_import_navigateur.py:27: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst esbuild=require('esbuild');\nesbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';\nimport Banque from './src/pages/RapprochementBancaire.jsx';createRoot(document.getElementById('root')).render(<Banque/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',\ndefine:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){\nb.onLoad({filter:/ExerciceContext\\.jsx$/},()=>({contents:`export function useExercice(){return {annee:2025,exercice:{date_debut:'2025-01-01',date_fin:'2025-12-31',statut:'ouvert'}}}`,loader:'js'}));\nb.onLoad({filter:/ModulesContext\\.jsx$/},()=>({contents:'export function useModules(){return {societe:{id:1}}}',loader:'js'}));\nb.onLoad({filter:/\\.module\\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));\n}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\releve-import-react0\\releve.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import_navigateur::test_import_csv_fr_transmet_dates_et_montants_exacts_et_rafraichit[cp1252-390] :error

```text
Test\test_session133_releve_import_navigateur.py:27: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst esbuild=require('esbuild');\nesbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';\nimport Banque from './src/pages/RapprochementBancaire.jsx';createRoot(document.getElementById('root')).render(<Banque/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',\ndefine:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){\nb.onLoad({filter:/ExerciceContext\\.jsx$/},()=>({contents:`export function useExercice(){return {annee:2025,exercice:{date_debut:'2025-01-01',date_fin:'2025-12-31',statut:'ouvert'}}}`,loader:'js'}));\nb.onLoad({filter:/ModulesContext\\.jsx$/},()=>({contents:'export function useModules(){return {societe:{id:1}}}',loader:'js'}));\nb.onLoad({filter:/\\.module\\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));\n}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\releve-import-react0\\releve.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_import_navigateur::test_csv_invalide_affiche_ligne_fautive_et_ne_poste_rien :error

```text
Test\test_session133_releve_import_navigateur.py:27: in bundle
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '-e', "\nconst esbuild=require('esbuild');\nesbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';\nimport Banque from './src/pages/RapprochementBancaire.jsx';createRoot(document.getElementById('root')).render(<Banque/>);`,\nloader:'jsx',resolveDir:process.cwd()},bundle:true,platform:'browser',format:'iife',jsx:'automatic',\ndefine:{'import.meta.env':'{}'},outfile:process.argv[1],plugins:[{name:'isolated-fixtures',setup(b){\nb.onLoad({filter:/ExerciceContext\\.jsx$/},()=>({contents:`export function useExercice(){return {annee:2025,exercice:{date_debut:'2025-01-01',date_fin:'2025-12-31',statut:'ouvert'}}}`,loader:'js'}));\nb.onLoad({filter:/ModulesContext\\.jsx$/},()=>({contents:'export function useModules(){return {societe:{id:1}}}',loader:'js'}));\nb.onLoad({filter:/\\.module\\.css$/},()=>({contents:'export default new Proxy({}, {get:(_,key)=>key});',loader:'js'}));\n}}]}).then(()=>esbuild.stop()).catch(e=>{process.stderr.write(String(e));process.exitCode=1;esbuild.stop()});\n", 'C:\\Users\\Y_N_e\\AppData\\Local\\Temp\\pytest-of-Y_N_e\\pytest-205\\releve-import-react0\\releve.js'], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_session133_releve_postgres::test_api_pg_csv_fr_import_soldes_et_pointage_sont_coherents :failure

```text
Test\test_session133_releve_postgres.py:30: in test_api_pg_csv_fr_import_soldes_et_pointage_sont_coherents
    lignes = lire(csv="Date;Libellé;Débit;Crédit\n03/04/2026;002;;1 234,56\n04/04/2026;Frais;34,56;")["lignes"]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Test\test_session133_releve_import.py:21: in lire
    assert result.returncode == 0, result.stderr
E   AssertionError: 
E   assert 3221225794 == 0
E    +  where 3221225794 = CompletedProcess(args=['node', '--input-type=module', '-e', "import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';\nconst args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));\ntry {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}\ncatch(e) {console.log(JSON.stringify({erreur:e.message}))} "], returncode=3221225794, stdout='', stderr='').returncode
```

- Test.test_tri_creation_commercial_isole::test_creation_meme_instant_antidate_historique_filtres_et_ui[devis] :failure

```text
Test\test_tri_creation_commercial_isole.py:101: in test_creation_meme_instant_antidate_historique_filtres_et_ui
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_tri_creation_commercial_isole::test_creation_meme_instant_antidate_historique_filtres_et_ui[bc] :failure

```text
Test\test_tri_creation_commercial_isole.py:101: in test_creation_meme_instant_antidate_historique_filtres_et_ui
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_tri_creation_commercial_isole::test_creation_meme_instant_antidate_historique_filtres_et_ui[bl] :failure

```text
Test\test_tri_creation_commercial_isole.py:101: in test_creation_meme_instant_antidate_historique_filtres_et_ui
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_tri_creation_commercial_isole::test_creation_meme_instant_antidate_historique_filtres_et_ui[br] :failure

```text
Test\test_tri_creation_commercial_isole.py:101: in test_creation_meme_instant_antidate_historique_filtres_et_ui
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_tri_creation_commercial_isole::test_creation_meme_instant_antidate_historique_filtres_et_ui[factures] :failure

```text
Test\test_tri_creation_commercial_isole.py:101: in test_creation_meme_instant_antidate_historique_filtres_et_ui
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

- Test.test_tri_creation_commercial_isole::test_creation_meme_instant_antidate_historique_filtres_et_ui[reglements] :failure

```text
Test\test_tri_creation_commercial_isole.py:101: in test_creation_meme_instant_antidate_historique_filtres_et_ui
    with playwright.sync_playwright() as p:
hisabpro-backend\.venv\Lib\site-packages\playwright\sync_api\_context_manager.py:74: in __enter__
    self._connection.playwright_future.result()
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:344: in init
    result = await self._root_object.initialize()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:285: in initialize
    await self._channel.send(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:76: in send
    return await self._connection.wrap_api_call(
hisabpro-backend\.venv\Lib\site-packages\playwright\_impl\_connection.py:632: in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E   Exception: Connection.init: Connection closed while reading from the driver
```

## Analyse de reprise du14octobre2026

72 incidents comportent le code Windows3221225794 (0xC0000142) :42 échecs et30 erreurs de préparation.17 autres échecs concernent une fermeture du pilote Playwright. Node fonctionne ànouveau àla reprise ;la cause système exacte n’est pas démontrée. Un échec distinct est une lecture immédiate du DOM vide dans le tableau dégressif après rafraîchissement ;le module rejoué sans modification avait2 réussites. Les89 incidents de sous-processus doivent être rejoués etle banc DOM corrigé sans modifier les montants. Cette suite426 reste en échec.

## Limites etprochaine reprise

Aucun PostgreSQL réel,données réelles,migration,main oumodèle modifié.09Eest une préparation interne ;formulaire officiel,paie/CNSS complète etEDI restent àqualifier. Les justificatifs historiques manquants restent visibles. Point6 en attente utilisateur. En cas d'échec,reproduire le cas puis corriger la cause minimale avant nouvelle recette ;sinon livrer couverture422etZIPcumulatif425,puis reprendre les fonctions partielles indépendantes des blocages réglementaires.

## Clarification de reprise14octobre

Les72incidents Windows0xC0000142,17fermetures de pilote Playwright et1lecture DOM vide totalisent bien90incidents. La cause système exacte n’est pas démontrée.428et429sont postérieurs àcette preuve. La nouvelle globale430 possède ses propres XML/log/code/empreintes ;elle ne remplace aucun résultat historique. Corrections typographiques du présent reçu uniquement.
