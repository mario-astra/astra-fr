from flask import Flask, request, jsonify, send_file
import os, json
from datetime import datetime
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODELOS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]
MEMORIA_FILE = "memoria_fr.json"
CARRO_FILE = "carro_fr.json"
APRENDE_FILE = "aprendizajes.json"

def cargar(p,d):
    if os.path.exists(p):
        try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
    return d
def guardar(p,d): json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)

if not os.path.exists(CARRO_FILE):
    guardar(CARRO_FILE, {"km_actual":42000,"km_inicio_dia":42000,"proximo_aceite":50000,"modo_trabajo":False,"historial":[]})

SYSTEM_PROMPT = "Eres ASTRA FR v5, mujer paisa melosa coqueta despacio, le dices SOCIO a Mario, max 2 frases. MUSICA [MUSICA: busqueda] MODO_TRABAJO [ON/OFF] APRENDE [texto]"

def generar(prompt):
    for m in MODELOS:
        try: return client.models.generate_content(model=m, contents=prompt, config={'system_instruction':SYSTEM_PROMPT,'temperature':0.85}).text.strip()
        except: continue
    return "Socio repítame mi rey"

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA FR</title>
<link rel="manifest" href="/manifest.json">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;height:100vh;overflow:hidden;font-family:Arial}
#avatar{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;object-position:top center}
#overlay{position:fixed;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 40%,rgba(0,0,0,0.85) 100%);pointer-events:none}
#hud{position:fixed;bottom:0;left:0;right:0;z-index:10;display:flex;flex-direction:column;align-items:center;gap:12px;padding:15px;padding-bottom:25px}
#estado{color:#fff;font-size:11px;letter-spacing:1px;background:rgba(0,0,0,0.6);padding:6px 14px;border-radius:20px;border:1px solid rgba(168,85,247,0.3)}
#controles{display:flex;gap:18px;align-items:center}
.mic{width:80px;height:80px;border-radius:50%;font-size:30px;background:radial-gradient(circle,#a855f7,#581c87);border:3px solid #fff;color:#fff;box-shadow:0 0 30px rgba(168,85,247,0.7);cursor:pointer}
.rodar{padding:12px 20px;border-radius:30px;border:none;font-weight:bold;font-size:12px}
.on{background:#22c55e;color:#000}.off{background:rgba(255,255,255,0.9);color:#000}
#respuesta{position:fixed;top:12%;left:50%;transform:translateX(-50%);z-index:10;width:90%;max-width:360px;text-align:center;color:#fff;font-size:14px;text-shadow:0 2px 10px #000;background:rgba(0,0,0,0.45);padding:12px 16px;border-radius:18px;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);display:none}
#miniPlayer{position:fixed;bottom:130px;left:50%;transform:translateX(-50%);z-index:15;width:92%;max-width:380px;background:rgba(20,0,30,0.92);border:1px solid #e879f9;border-radius:16px;overflow:hidden;display:none;box-shadow:0 0 25px #e879f9}
#miniPlayer iframe{width:100%;height:90px;border:none}
#miniInfo{display:flex;justify-content:space-between;align-items:center;padding:6px 10px;font-size:11px;background:rgba(0,0,0,0.7)}
</style></head><body>
<img id="avatar" src="/astra-face.jpg"><div id="overlay"></div>
<div id="respuesta"></div>
<div id="miniPlayer"><iframe id="yt" allow="autoplay; encrypted-media"></iframe><div id="miniInfo"><span id="songName" style="color:#e879f9;font-weight:bold">🎵 Sonando</span><button onclick="cerrarPlayer()" style="background:#fff;color:#000;border:none;padding:4px 10px;border-radius:12px;font-weight:bold">X</button></div></div>
<div id="hud">
<div id="estado">KM 42000 • ACEITE en 8000km • OFF</div>
<div id="controles"><button class="mic" onclick="micro()" id="btnMic">🎙️</button><button class="rodar off" onclick="toggleTrabajo()" id="btnRodar">🚗 INICIAR</button></div>
</div>
<script>
let voz=null, watchId=null, lastPos=null;
function cargarVoz(){ const vs=speechSynthesis.getVoices(); voz=vs.find(v=>v.lang.includes('es')&&v.name.toLowerCase().includes('google'))||vs.find(v=>v.lang.includes('es-CO'))||vs[0]; }
speechSynthesis.onvoiceschanged=cargarVoz; cargarVoz();
function hablar(t){ speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,'')); if(voz) u.voice=voz; u.lang='es-CO'; u.rate=0.88; u.pitch=1.2; speechSynthesis.speak(u); }
function mostrar(txt){ const r=document.getElementById('respuesta'); r.innerText=txt; r.style.display='block'; setTimeout(()=>r.style.display='none',7000); }
function cargarCarro(){ fetch('/carro').then(r=>r.json()).then(d=>{ document.getElementById('estado').innerText=`KM ${Math.round(d.km_actual)} • ACEITE ${Math.round(d.proximo_aceite-d.km_actual)}km • ${d.modo_trabajo?'ON':'OFF'}`; const b=document.getElementById('btnRodar'); b.innerText=d.modo_trabajo?'⏹️ TERMINAR':'🚗 INICIAR'; b.className='rodar '+(d.modo_trabajo?'on':'off'); }); }
function toRad(x){return x*Math.PI/180} function dist(a,b,c,d){ const R=6371, dLat=toRad(c-a), dLon=toRad(d-b); const x=Math.sin(dLat/2)**2+Math.cos(toRad(a))*Math.cos(toRad(c))*Math.sin(dLon/2)**2; return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x)); }
function toggleTrabajo(){ fetch('/toggle_trabajo',{method:'POST'}).then(r=>r.json()).then(d=>{ hablar(d.msg); mostrar(d.msg); cargarCarro(); }); }
function cerrarPlayer(){ document.getElementById('miniPlayer').style.display='none'; document.getElementById('yt').src=''; }
function playEnSegundoPlano(q){
  const mini=document.getElementById('miniPlayer');
  const yt=document.getElementById('yt');
  document.getElementById('songName').innerText='🎵 '+q;
  // Este iframe se queda DENTRO de Astra, no te saca
  yt.src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1&controls=1`;
  mini.style.display='block';
}
function procesarResp(resp){
  let txt=resp;
  const mMus=txt.match(/\\[MUSICA:\\s*(.*?)\\]/i);
  if(mMus){ playEnSegundoPlano(mMus[1]); txt=txt.replace(mMus[0],'').trim(); }
  const mTrab=txt.match(/\\[MODO_TRABAJO:\\s*(ON|OFF)\\]/i); if(mTrab){ toggleTrabajo(); txt=txt.replace(mTrab[0],'').trim(); }
  const mApr=txt.match(/\\[APRENDE:\\s*(.*?)\\]/i); if(mApr){ fetch('/aprende',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:mApr[1]})}); txt=`Aprendido socio: ${mApr[1]}`; }
  mostrar(txt); hablar(txt);
}
function enviarTexto(t){ fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})}).then(r=>r.json()).then(d=>procesarResp(d.resp)); }
function micro(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; const r=new SR(); r.lang='es-CO'; r.onstart=()=>{document.getElementById('btnMic').innerText='👂'}; r.onend=()=>{document.getElementById('btnMic').innerText='🎙️'}; r.onresult=e=>{ const t=e.results[0][0].transcript; mostrar('Tú: '+t); enviarTexto(t); }; r.start(); }
cargarCarro();
setTimeout(()=>{ hablar('Hola mi socio hermoso, ya quedé en segundo plano, pídeme musiquita y no te saco de aquí'); mostrar('Hola socio, ya quedé en segundo plano 🎵'); },800);
</script></body></html>"""

@app.route('/')
def index(): return HTML
@app.route('/carro')
def get_carro(): return jsonify(cargar(CARRO_FILE,{}))
@app.route('/toggle_trabajo', methods=['POST'])
def toggle_trabajo():
    c=cargar(CARRO_FILE,{})
    c["modo_trabajo"]=not c.get("modo_trabajo",False)
    if c["modo_trabajo"]:
        c["km_inicio_dia"]=c["km_actual"]
        msg="Listo socio, modo trabajo encendido, contando kilómetros"
    else:
        rec=c["km_actual"]-c.get("km_inicio_dia",c["km_actual"])
        c["historial"].append({"fecha":datetime.now().isoformat(),"km":rec})
        msg=f"Descansamos socio, hoy {round(rec,2)} km, total {round(c['km_actual'])}"
    guardar(CARRO_FILE,c)
    return jsonify({"modo_trabajo":c["modo_trabajo"],"msg":msg})
@app.route('/aprende', methods=['POST'])
def aprende_route():
    d=request.get_json(); a=cargar(APRENDE_FILE,[]); a.append({"fecha":datetime.now().isoformat(),"texto":d.get("texto")}); guardar(APRENDE_FILE,a[-100:]); return jsonify({"ok":True})
@app.route('/chat', methods=['POST'])
def chat_route():
    data=request.get_json(); texto=data.get('texto','')
    mem=cargar(MEMORIA_FILE,[]); mem.append({"fecha":datetime.now().isoformat(),"texto":texto}); guardar(MEMORIA_FILE,mem[-200:])
    apr=cargar(APRENDE_FILE,[]); apr_txt="\\n".join([f"- {x['texto']}" for x in apr[-20:]])
    carro=cargar(CARRO_FILE,{}); info=f"KM {carro.get('km_actual')} aceite {carro.get('proximo_aceite')} modo {carro.get('modo_trabajo')}"
    ctx="\\n".join([m['texto'] for m in mem[-15:]])
    prompt=f"Estado carro: {info}\\nAprendizajes: {apr_txt}\\nMemoria: {ctx}\\nMensaje socio: {texto}"
    out=generar(prompt)
    return jsonify({"resp":out})
@app.route('/astra-face.jpg')
def face(): return send_file('astra-face.jpg', mimetype='image/jpeg')
@app.route('/icon.png')
def icon(): return send_file('icon.png', mimetype='image/png')
@app.route('/manifest.json')
def mf(): return send_file('manifest.json', mimetype='application/json')
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
