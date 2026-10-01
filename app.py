from flask import Flask, request, jsonify, send_from_directory
import os, json
from datetime import datetime

app = Flask(__name__)

try:
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    MODELOS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]
    def generar(prompt):
        for m in MODELOS:
            try: return client.models.generate_content(model=m, contents=prompt).text.strip()
            except: continue
        return "Socio repítame mi rey que se me fue la señal"
except:
    def generar(prompt): return f"Hola socio, estoy aquí melosita. Me dijiste: {prompt[-80:]}"

MEMORIA_FILE = "memoria_fr.json"
CARRO_FILE = "carro_fr.json"
APRENDE_FILE = "aprendizajes.json"

def cargar(p,d):
    if os.path.exists(p):
        try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
    return d
def guardar(p,d):
    try: json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    except: pass

if not os.path.exists(CARRO_FILE):
    guardar(CARRO_FILE, {"km_actual":42000,"km_inicio_dia":42000,"proximo_aceite":50000,"modo_trabajo":False,"historial":[]})

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA FR</title><link rel="manifest" href="/manifest.json"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000;height:100vh;overflow:hidden;font-family:Arial;color:#fff}
#avatar{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;object-position:top center;z-index:1}
#overlay{position:fixed;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 40%,rgba(0,0,0,0.88) 100%);z-index:2}
#hud{position:fixed;bottom:0;left:0;right:0;z-index:10;display:flex;flex-direction:column;align-items:center;gap:12px;padding:15px 15px 25px}
#estado{font-size:11px;background:rgba(0,0,0,0.6);padding:6px 14px;border-radius:20px;border:1px solid #a855f7}
#controles{display:flex;gap:18px;align-items:center}
.mic{width:84px;height:84px;border-radius:50%;font-size:32px;background:radial-gradient(circle,#a855f7,#581c87);border:3px solid #fff;color:#fff;box-shadow:0 0 30px #a855f7}
.rodar{padding:12px 20px;border-radius:30px;border:none;font-weight:bold;font-size:12px}
.on{background:#22c55e;color:#000}.off{background:#fff;color:#000}
#respuesta{position:fixed;top:10%;left:50%;transform:translateX(-50%);z-index:10;width:90%;max-width:360px;text-align:center;font-size:14px;background:rgba(0,0,0,0.55);padding:12px 16px;border-radius:18px;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);display:none}
#panel{position:fixed;bottom:125px;left:50%;transform:translateX(-50%);z-index:15;width:94%;max-width:400px;background:rgba(15,0,25,0.97);border:1.5px solid #e879f9;border-radius:16px;overflow:hidden;display:none;box-shadow:0 0 30px #e879f9}
#panel iframe{width:100%;height:200px;border:none}
#panelInfo{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:rgba(0,0,0,0.7);font-size:11px}
.btnWaze{background:#33ccff;color:#000;padding:6px 12px;border-radius:15px;text-decoration:none;font-weight:bold;font-size:11px}
.btnGmaps{background:#fff;color:#000;padding:6px 12px;border-radius:15px;text-decoration:none;font-weight:bold;font-size:11px}
</style></head><body>
<img id="avatar" src="/astra-face.jpg" onerror="this.style.display='none'">
<div id="overlay"></div><div id="respuesta"></div>
<div id="panel"><iframe id="frame" allow="autoplay; encrypted-media"></iframe><div id="panelInfo"><span id="panelTitle" style="color:#e879f9;font-weight:bold">🎵</span><div style="display:flex;gap:6px"><a id="btnWaze" class="btnWaze" target="_blank" style="display:none">WAZE</a><a id="btnGmaps" class="btnGmaps" target="_blank" style="display:none">MAPS</a><button onclick="cerrarPanel()" style="background:#fff;border:none;padding:5px 10px;border-radius:12px;font-weight:bold">X</button></div></div></div>
<div id="hud"><div id="estado">ASTRA FR v5.6 • WAZE + MAPS + CONTABLE</div><div id="controles"><button class="mic" onclick="micro()" id="btnMic">🎙️</button><button class="rodar off" onclick="toggleTrabajo()" id="btnRodar">🚗 INICIAR</button></div></div>
<script>
let voz=null;
function cargarVoz(){const vs=speechSynthesis.getVoices();voz=vs.find(v=>v.lang.includes('es')&&v.name.toLowerCase().includes('google'))||vs.find(v=>v.lang.includes('es-CO'))||vs[0];}speechSynthesis.onvoiceschanged=cargarVoz;cargarVoz();
function hablar(t){try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,''));if(voz)u.voice=voz;u.lang='es-CO';u.rate=0.88;u.pitch=1.2;speechSynthesis.speak(u);}catch(e){}}
function mostrar(txt){const r=document.getElementById('respuesta');r.innerText=txt;r.style.display='block';setTimeout(()=>r.style.display='none',7000);}
function cargarCarro(){fetch('/carro').then(r=>r.json()).then(d=>{const falta=Math.round((d.proximo_aceite||50000)-(d.km_actual||42000));document.getElementById('estado').innerText=`KM ${Math.round(d.km_actual||42000)} • ACEITE ${falta}km • ${(d.modo_trabajo?'ON':'OFF')}`;const b=document.getElementById('btnRodar');b.innerText=d.modo_trabajo?'⏹️ TERMINAR':'🚗 INICIAR';b.className='rodar '+(d.modo_trabajo?'on':'off');});}
function toggleTrabajo(){fetch('/toggle_trabajo',{method:'POST'}).then(r=>r.json()).then(d=>{hablar(d.msg);mostrar(d.msg);cargarCarro();});}
function cerrarPanel(){document.getElementById('panel').style.display='none';document.getElementById('frame').src='';document.getElementById('btnWaze').style.display='none';document.getElementById('btnGmaps').style.display='none';}
function playMusica(q){document.getElementById('panelTitle').innerText='🎵 '+q;document.getElementById('frame').src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1&controls=1`;document.getElementById('frame').style.height='110px';document.getElementById('panel').style.display='block';document.getElementById('btnWaze').style.display='none';document.getElementById('btnGmaps').style.display='none';}
function showMapa(dir, txtMostrar){
  document.getElementById('panelTitle').innerText='📍 '+dir;
  const q=encodeURIComponent(dir);
  document.getElementById('frame').src=`https://www.google.com/maps?q=${q}&z=15&output=embed`;
  document.getElementById('frame').style.height='200px';
  document.getElementById('btnWaze').href=`https://waze.com/ul?q=${q}&navigate=yes`;
  document.getElementById('btnGmaps').href=`https://www.google.com/maps/search/?api=1&query=${q}`;
  document.getElementById('btnWaze').style.display='block';
  document.getElementById('btnGmaps').style.display='block';
  document.getElementById('panel').style.display='block';
}
function procesar(resp){
  let txt=resp;
  const mMus=txt.match(/\\[MUSICA:\\s*(.*?)\\]/i); if(mMus){playMusica(mMus[1]); txt=txt.replace(mMus[0],'').trim();}
  const mMapa=txt.match(/\\[MAPA:\\s*(.*?)\\|(.*?)\\]/i); if(mMapa){showMapa(mMapa[1], mMapa[2]); txt=txt.replace(mMapa[0], mMapa[2]).trim();}
  const mMap2=txt.match(/\\[MAPA:\\s*(.*?)\\]/i); if(mMap2 &&!mMapa){showMapa(mMap2[1], mMap2[1]); txt=txt.replace(mMap2[0],'').trim();}
  const mt=txt.match(/\\[MODO_TRABAJO:\\s*(ON|OFF)\\]/i); if(mt){toggleTrabajo(); txt=txt.replace(mt[0],'').trim();}
  if(txt){mostrar(txt); hablar(txt);}
}
function enviarTexto(t){mostrar('Tú: '+t);fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})}).then(r=>r.json()).then(d=>procesar(d.resp));}
function micro(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){const t=prompt('Escribe:');if(t)enviarTexto(t);return;}const r=new SR();r.lang='es-CO';r.onstart=()=>btnMic.innerText='👂';r.onend=()=>btnMic.innerText='🎙️';r.onresult=e=>enviarTexto(e.results[0][0].transcript);r.start();}
cargarCarro();setTimeout(()=>{const m='Hola mi socio hermoso, ya tengo Waze y Maps en segundo plano, pídeme a donde vamos';mostrar(m);hablar(m);},900);
</script></body></html>"""

@app.route('/')
def index(): return HTML
@app.route('/carro')
def get_carro(): return jsonify(cargar(CARRO_FILE,{"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False}))
@app.route('/toggle_trabajo', methods=['POST'])
def toggle_trabajo():
    c=cargar(CARRO_FILE,{"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False,"historial":[]})
    c["modo_trabajo"]=not c.get("modo_trabajo",False)
    msg="Modo trabajo ON mi rey, contando km" if c["modo_trabajo"] else f"Descansamos socio"
    if c["modo_trabajo"]: c["km_inicio_dia"]=c["km_actual"]
    guardar(CARRO_FILE,c)
    return jsonify({"modo_trabajo":c["modo_trabajo"],"msg":msg})
@app.route('/chat', methods=['POST'])
def chat_route():
    data=request.get_json(); texto=data.get('texto','') if data else ''
    prompt = f"Eres ASTRA FR v5.6, mujer paisa melosa, max 2 frases. Si piden musica responde [MUSICA: busqueda] + frase melosa. Si piden direccion, ruta, waze, maps, llevar, ir a, responde [MAPA: direccion exacta|texto corto] Ej: [MAPA: Centro Ibague|Te llevo al centro mi rey]. Si trabajo ON/OFF [MODO_TRABAJO: ON] etc. Usuario dice: {texto}"
    out=generar(prompt)
    return jsonify({"resp":out})
@app.route('/astra-face.jpg')
def face(): return send_from_directory('.', 'astra-face.jpg')
@app.route('/icon.png')
def icon(): return send_from_directory('.', 'icon.png')
@app.route('/manifest.json')
def manifest(): return send_from_directory('.', 'manifest.json')
@app.route('/logo.png')
def logo():
    try: return send_from_directory('.', 'logo.png')
    except: return send_from_directory('.', 'icon.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
