from flask import Flask, request, jsonify, send_from_directory
import os, json
from datetime import datetime

app = Flask(__name__)

try:
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    def generar(prompt):
        try: return client.models.generate_content(model="gemini-2.0-flash", contents=prompt).text.strip()
        except: return client.models.generate_content(model="gemini-1.5-flash", contents=prompt).text.strip()
except:
    def generar(p): return f"Hola socio, [MUSICA: feid] soy Astra melosita. Me dijiste {p[-50:]}"

MEMORIA_FILE = "memoria_fr.json"
CARRO_FILE = "carro_fr.json"
MENSAJES_FILE = "mensajes_fr.json"

def cargar(p,d):
    if os.path.exists(p):
        try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
    return d
def guardar(p,d):
    try: json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    except: pass

if not os.path.exists(CARRO_FILE): guardar(CARRO_FILE, {"km_actual":42000,"km_inicio_dia":42000,"proximo_aceite":50000,"modo_trabajo":False,"historial":[]})
if not os.path.exists(MENSAJES_FILE): guardar(MENSAJES_FILE, [])

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASTRA FR v6</title><link rel="manifest" href="/manifest.json"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000;height:100vh;overflow:hidden;color:#fff;font-family:Arial}
#avatar{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;z-index:1}
#overlay{position:fixed;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 30%,rgba(0,0,0,0.9) 100%);z-index:2}
#hud{position:fixed;bottom:0;left:0;right:0;z-index:10;display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px 12px 22px}
#estado{font-size:10px;background:rgba(0,0,0,0.7);padding:6px 12px;border-radius:20px;border:1px solid #a855f7}
#controles{display:flex;gap:12px;align-items:center}
.mic{width:86px;height:86px;border-radius:50%;font-size:32px;background:radial-gradient(circle,#a855f7,#581c87);border:3px solid #fff;box-shadow:0 0 30px #a855f7}
.rodar{padding:10px 16px;border-radius:20px;border:none;font-weight:bold;font-size:11px}.on{background:#22c55e;color:#000}.off{background:#fff;color:#000}
#respuesta{position:fixed;top:9%;left:50%;transform:translateX(-50%);z-index:11;width:92%;max-width:380px;text-align:center;font-size:13px;background:rgba(0,0,0,0.6);padding:10px 14px;border-radius:16px;backdrop-filter:blur(8px);display:none}
#panel{position:fixed;bottom:120px;left:50%;transform:translateX(-50%);z-index:15;width:95%;max-width:420px;background:rgba(15,0,25,0.98);border:1.5px solid #e879f9;border-radius:16px;overflow:hidden;display:none;box-shadow:0 0 30px #e879f9}
#panel iframe{width:100%;border:none}#frameMusica{height:110px}#frameMapa{height:200px}#frameVideo{height:380px}
#panelInfo{display:flex;justify-content:space-between;align-items:center;padding:7px 10px;background:#000;font-size:11px}
.btn{padding:6px 12px;border-radius:15px;text-decoration:none;font-weight:bold;font-size:11px;border:none}
.btnWaze{background:#33ccff;color:#000}.btnGmaps{background:#fff;color:#000}
#inboxBtn{position:fixed;top:15px;right:15px;z-index:12;background:rgba(0,0,0,0.6);border:1px solid #e879f9;border-radius:20px;padding:8px 12px;font-size:11px}
#inbox{position:fixed;top:50px;right:10px;z-index:16;width:90%;max-width:340px;background:rgba(20,0,30,0.98);border:1px solid #e879f9;border-radius:14px;padding:10px;display:none;max-height:60vh;overflow:auto}
.msg{font-size:11px;padding:6px 8px;margin:4px 0;background:rgba(255,255,255,0.08);border-radius:10px}
</style></head><body>
<img id="avatar" src="/astra-face.jpg" onerror="this.style.display='none'"><div id="overlay"></div>
<button id="inboxBtn" onclick="toggleInbox()">📩 <span id="msgCount">0</span> Msjs</button>
<div id="inbox"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><b style="color:#e879f9">Mensajes Familia</b><button onclick="toggleInbox()" style="background:#fff;border:none;padding:2px 8px;border-radius:10px">X</button></div><div id="listaMsgs"></div><input id="inputMsg" placeholder="Escribe pa' Paola..." style="width:70%;padding:6px;border-radius:10px;border:none;margin-top:6px"><button onclick="enviarMsg()" style="padding:6px 10px;border-radius:10px;border:none;background:#e879f9;color:#000;font-weight:bold">Enviar</button></div>
<div id="respuesta"></div>
<div id="panel"><iframe id="frame"></iframe><div id="panelInfo"><span id="panelTitle" style="color:#e879f9"></span><div style="display:flex;gap:6px"><a id="bWaze" class="btn btnWaze" target="_blank" style="display:none">WAZE</a><a id="bMaps" class="btn btnGmaps" target="_blank" style="display:none">MAPS</a><button onclick="cerrarPanel()" class="btn" style="background:#fff">X</button></div></div></div>
<div id="hud"><div id="estado">ASTRA FR v6 • TODO EN UNO</div><div id="controles"><button class="mic" onclick="micro()" id="btnMic">🎙️</button><button class="rodar off" id="btnRodar" onclick="toggleTrabajo()">🚗 INICIAR</button><button class="rodar off" onclick="testVideo()" style="background:#e879f9">📹 VIDEO</button></div></div>
<script>
let voz=null;
function cargarVoz(){const vs=speechSynthesis.getVoices();voz=vs.find(v=>v.lang.includes('es')&&v.name.includes('Google'))||vs.find(v=>v.lang.includes('es-CO'))||vs[0];}speechSynthesis.onvoiceschanged=cargarVoz;cargarVoz();
function hablar(t){try{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,''));if(voz)u.voice=voz;u.lang='es-CO';u.rate=0.9;u.pitch=1.15;speechSynthesis.speak(u);}catch(e){}}
function mostrar(txt){let r=document.getElementById('respuesta');r.innerText=txt;r.style.display='block';setTimeout(()=>r.style.display='none',7000);}
function cargarCarro(){fetch('/carro').then(r=>r.json()).then(d=>{let f=Math.round((d.proximo_aceite||50000)-(d.km_actual||42000));document.getElementById('estado').innerText=`KM ${Math.round(d.km_actual||42000)} • ACEITE ${f}km • ${d.modo_trabajo?'ON':'OFF'}`;let b=document.getElementById('btnRodar');b.innerText=d.modo_trabajo?'⏹️ TERMINAR':'🚗 INICIAR';b.className='rodar '+(d.modo_trabajo?'on':'off');});}
function toggleTrabajo(){fetch('/toggle_trabajo',{method:'POST'}).then(r=>r.json()).then(d=>{hablar(d.msg);mostrar(d.msg);cargarCarro();});}
function cerrarPanel(){document.getElementById('panel').style.display='none';document.getElementById('frame').src='';document.getElementById('bWaze').style.display='none';document.getElementById('bMaps').style.display='none';}
function playMusica(q){document.getElementById('panelTitle').innerText='🎵 '+q;let f=document.getElementById('frame');f.id='frame';f.className='';f.style.height='110px';f.src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1`;document.getElementById('panel').style.display='block';}
function showMapa(dir){let q=encodeURIComponent(dir);document.getElementById('panelTitle').innerText='📍 '+dir;let f=document.getElementById('frame');f.style.height='200px';f.src=`https://www.google.com/maps?q=${q}&z=14&output=embed`;document.getElementById('bWaze').href=`https://waze.com/ul?q=${q}&navigate=yes`;document.getElementById('bWaze').style.display='block';document.getElementById('bMaps').href=`https://www.google.com/maps/search/?api=1&query=${q}`;document.getElementById('bMaps').style.display='block';document.getElementById('panel').style.display='block';}
function showVideo(nombre){let sala='astra-fr-'+(nombre||'familia').toLowerCase()+'-2026';document.getElementById('panelTitle').innerText='📹 Llamando a '+nombre;let f=document.getElementById('frame');f.style.height='380px';f.src=`https://meet.jit.si/${sala}#config.prejoinPageEnabled=false`;document.getElementById('panel').style.display='block';hablar('Conectando videollamada con '+nombre+' mi socio, espere que conteste');mostrar('📹 Llamando a '+nombre+'...');}
function testVideo(){showVideo('Familia');}
function toggleInbox(){let i=document.getElementById('inbox');i.style.display=i.style.display==='none'?'block':'none';cargarMsgs();}
function cargarMsgs(){fetch('/mensajes').then(r=>r.json()).then(d=>{document.getElementById('msgCount').innerText=d.length;let l=document.getElementById('listaMsgs');l.innerHTML='';d.slice(-20).reverse().forEach(m=>{l.innerHTML+=`<div class=msg><b>${m.de}:</b> ${m.texto} <small style=opacity:0.6>${m.fecha.slice(11,16)}</small></div>`;});});}
function enviarMsg(){let t=document.getElementById('inputMsg').value;if(!t)return;fetch('/mensaje',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({de:'Mario',texto:t})}).then(()=>{document.getElementById('inputMsg').value='';cargarMsgs();mostrar('Mensaje enviado socio');});}
function procesar(resp){
  let txt=resp;
  let mMus=txt.match(/\\[MUSICA:\\s*(.*?)\\]/i); if(mMus){playMusica(mMus[1]);txt=txt.replace(mMus[0],'').trim();}
  let mMapa=txt.match(/\\[MAPA:\\s*(.*?)\\|(.*?)\\]/i); if(mMapa){showMapa(mMapa[1]);txt=mMapa[2];}
  let mMap2=txt.match(/\\[MAPA:\\s*(.*?)\\]/i); if(mMap2 &&!mMapa){showMapa(mMap2[1]);txt=txt.replace(mMap2[0],'').trim();}
  let mVid=txt.match(/\\[VIDEO:\\s*(.*?)\\]/i); if(mVid){showVideo(mVid[1]);txt=txt.replace(mVid[0],'').trim();}
  let mT=txt.match(/\\[MODO_TRABAJO:\\s*(ON|OFF)\\]/i); if(mT){toggleTrabajo();txt=txt.replace(mT[0],'').trim();}
  if(txt){mostrar(txt);hablar(txt);}
}
function enviarTexto(t){mostrar('Tú: '+t);fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})}).then(r=>r.json()).then(d=>procesar(d.resp));}
function micro(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){let t=prompt('Dile a Astra:');if(t)enviarTexto(t);return;}let r=new SR();r.lang='es-CO';r.onstart=()=>btnMic.innerText='👂';r.onend=()=>btnMic.innerText='🎙️';r.onresult=e=>enviarTexto(e.results[0][0].transcript);r.start();}
cargarCarro();cargarMsgs();
setTimeout(()=>{let m='Hola mi socio hermoso, ya estoy completa, con videollamada, mensajes, Waze, Maps y musiquita en segundo plano, ¿nos vamos pa Medellín?';mostrar(m);hablar(m);},1000);
</script></body></html>"""

@app.route('/')
def index(): return HTML
@app.route('/carro')
def get_carro(): return jsonify(cargar(CARRO_FILE,{"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False}))
@app.route('/toggle_trabajo', methods=['POST'])
def toggle_trabajo():
    c=cargar(CARRO_FILE,{"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False,"historial":[]})
    c["modo_trabajo"]=not c.get("modo_trabajo",False)
    msg="Modo trabajo ON mi rey, contando km pa Medellín" if c["modo_trabajo"] else "Descansamos socio"
    if c["modo_trabajo"]: c["km_inicio_dia"]=c["km_actual"]
    guardar(CARRO_FILE,c)
    return jsonify({"modo_trabajo":c["modo_trabajo"],"msg":msg})
@app.route('/mensajes')
def get_mensajes(): return jsonify(cargar(MENSAJES_FILE,[]))
@app.route('/mensaje', methods=['POST'])
def post_mensaje():
    d=request.get_json(); msgs=cargar(MENSAJES_FILE,[]); msgs.append({"de":d.get("de","Mario"),"texto":d.get("texto"),"fecha":datetime.now().isoformat()}); guardar(MENSAJES_FILE,msgs[-100:]); return jsonify({"ok":True})
@app.route('/chat', methods=['POST'])
def chat_route():
    data=request.get_json(); texto=data.get('texto','').lower() if data else ''
    # LOGICA INTELIGENTE PARA VIDEO Y MAPA
    extra=""
    if any(x in texto for x in ["llama","videollamada","llamame","llamar"]):
        if "paola" in texto: extra="[VIDEO: Paola]"
        elif "made" in texto: extra="[VIDEO: Made]"
        elif "dur" in texto: extra="[VIDEO: Dur]"
        else: extra="[VIDEO: Familia]"
    prompt = f"Eres ASTRA FR v6, paisa melosa, max 2 frases. Usuario dice: {texto}. Responde: Si musica [MUSICA: busqueda] Si ruta/waze/maps [MAPA: direccion|frase corta] Si videollamada ya viene {extra} no repitas VIDEO. Si trabajo [MODO_TRABAJO: ON/OFF]. {extra}"
    out=generar(prompt)
    if extra and "[VIDEO" not in out: out+=f" {extra}"
    return jsonify({"resp":out})
@app.route('/astra-face.jpg')
def face(): return send_from_directory('.', 'astra-face.jpg')
@app.route('/icon.png')
def icon(): return send_from_directory('.', 'icon.png')
@app.route('/manifest.json')
def manifest(): return send_from_directory('.', 'manifest.json')

if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
