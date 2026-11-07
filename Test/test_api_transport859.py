"""ClientJS réel sous Node ;transport synthétique pour distinguer réseau/HTTP/abort."""
from pathlib import Path
import json,subprocess,pytest
R=Path(__file__).resolve().parents[1]
@pytest.fixture(scope='module')
def bundle859(tmp_path_factory):
 p=tmp_path_factory.mktemp('client859')/'api.cjs'
 script="require('esbuild').buildSync({entryPoints:[process.argv[2]],outfile:process.argv[1],bundle:true,platform:'node',format:'cjs',define:{'import.meta.env':JSON.stringify({VITE_API_URL:'http://transport859.invalid'})}})"
 r=subprocess.run(['node','-e',script,str(p),str(R/'src/services/api.js')],cwd=R,text=True,capture_output=True);assert r.returncode==0,r.stderr;return p

@pytest.mark.parametrize('mode',['json','pdf'])
@pytest.mark.parametrize('scenario',['network','abort','401','403','422','success'])
def test_859_transport_et_semantique_http(bundle859,mode,scenario):
 script=r'''
function stockage(){const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k),key:i=>[...m.keys()][i]||null,get length(){return m.size}}}
global.localStorage=stockage();global.sessionStorage=stockage();let reload=0;global.window={location:{reload:()=>reload++}};
const api=require(process.argv[1]);const mode=process.argv[2],scenario=process.argv[3];api.setToken('session-fictive-test859');api.setRole('lecture');sessionStorage.setItem('hisabpro_plan_societe_v1:copie','cache');sessionStorage.setItem('autre','conserver');
global.fetch=async()=>{
 if(scenario==='network')throw new TypeError('Failed to fetch');
 if(scenario==='abort')throw new DOMException('Annulation de contrôle','AbortError');
 if(scenario==='success')return mode==='json'?new Response('[]',{status:200,headers:{'Content-Type':'application/json'}}):new Response('%PDF',{status:200,headers:{'Content-Disposition':'attachment; filename="recette.pdf"'}});
 const detail=scenario==='422'?[{loc:['body','lignes',0,'debit'],msg:'Montant invalide'}]:'Consultation seule';return new Response(JSON.stringify({detail}),{status:Number(scenario),headers:{'Content-Type':'application/json'}});
};
(async()=>{let out;try{const data=await (mode==='json'?api.ecrituresAPI.lister(2025):api.etatsAPI.telechargerLiassePDF(2025));out={ok:true,data:mode==='json'?data:{filename:data.filename,taille:data.blob.size}}}catch(e){out={ok:false,nom:e.name,message:e.message,cause:e.cause?.name||null}}out.reload=reload;out.session_presente=!!api.getToken();out.role_present=!!localStorage.getItem('hisabpro_role');out.cache_presente=!!sessionStorage.getItem('hisabpro_plan_societe_v1:copie');out.autre_preserve=sessionStorage.getItem('autre')==='conserver';process.stdout.write(JSON.stringify(out))})().catch(e=>{process.stderr.write(String(e));process.exitCode=1});
'''
 r=subprocess.run(['node','-e',script,str(bundle859),mode,scenario],cwd=R,text=True,capture_output=True);assert r.returncode==0,r.stderr;d=json.loads(r.stdout);assert d['autre_preserve']
 if scenario=='success':assert d['ok'] and d['data']==([] if mode=='json' else {'filename':'recette.pdf','taille':4})
 elif scenario=='network':assert not d['ok'] and d['message']=='Connexion au serveur indisponible. Vérifiez votre connexion puis réessayez.' and d['cause']=='TypeError'
 elif scenario=='abort':assert not d['ok'] and d['nom']=='AbortError' and d['message']=='Annulation de contrôle'
 elif scenario=='401':assert not d['ok'] and d['message']=='Session expirée : reconnectez-vous.' and d['reload']==1 and not d['session_presente'] and not d['role_present'] and not d['cache_presente']
 elif scenario=='403':assert not d['ok'] and d['message']=='Consultation seule'
 elif scenario=='422':assert not d['ok'] and d['message']=='lignes.0.debit : Montant invalide'
 if scenario!='401':assert d['reload']==0 and d['session_presente'] and d['role_present'] and d['cache_presente']
