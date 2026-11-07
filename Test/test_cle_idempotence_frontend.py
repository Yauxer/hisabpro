"""Vrai WebCrypto Node, randomUUID absent comme sur un contexte HTTP distant."""
from pathlib import Path
import json
import re
import subprocess


def test_cles_uuid_v4_sans_random_uuid():
    script="""
import {webcrypto} from 'node:crypto';
import {cleIdempotence} from './src/utils/cleIdempotence.js';
Object.defineProperty(globalThis,'crypto',{value:{getRandomValues:webcrypto.getRandomValues.bind(webcrypto)}});
console.log(JSON.stringify(Array.from({length:1000},()=>cleIdempotence())));
"""
    r=subprocess.run(['node','--input-type=module','-e',script],cwd=Path(__file__).resolve().parents[1],
        text=True,encoding='utf8',capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr
    cles=json.loads(r.stdout)
    assert len(set(cles))==1000
    assert all(re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',c) for c in cles)
