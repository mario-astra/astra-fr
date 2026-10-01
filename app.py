from flask import Flask, request, jsonify, send_from_directory
import os, json
from datetime import datetime
app = Flask(__name__)
try:
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    def generar(p):
        try: return client.models.generate_content(model="gemini-2.0-flash", contents=p).text.strip()
        except: return client.models.generate_content(model="gemini-1.5-flash", contents=p).text.strip()
except:
    def generar(p): return f"Socio, me dijiste {p[-60:]} [MUSICA: feid]"

CARRO_FILE = "carro_fr.json"
def cargar(p,d):
    if os.path.exists(p):
        try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
    return d
def guardar(p,d):
    try: json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    except: pass
if not os.path.exists(CARRO_FILE): guardar(CARRO_FILE, {"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False})

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASTRA FR v7</title><link rel="manifest" href="/manifest.json"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000;height:100vh;overflow:hidden;color:#fff;font-family:Arial}
#avatar{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;z-index:1}
#avatar.mini{width:110px;height:110px;border-radius:50%;top:15px;left:15px;inset:auto;border:3px solid #e879f9;box-shadow:0 0 20px #e879f9;z-index:20}
#overlay{position:fixed;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 30%,rgba(0,0,0,0.9) 100%);z-index:2}
#hud{position:fixed;bottom:0;left:0;right:0;z-index:10;display:flex;flex-direction:column;align-items:center;padding:0 0 30px}
.mic{width:90px;height:90px;border-radius:50%;font-size:36px;background:radial-gradient(circle,#a855f7,#581c87);border:3px solid #fff;box-shadow:0 0 35px #a855f7}
#respuesta{position:fixed;top:10%;left:50%;transform:translateX(-50%);z-index:11;width:92%;max-width:380px;text-align:center;font-size:13px;background:rgba(0,0,0,0.6);padding:10px 14px;border-radius:16px;backdrop-filter:blur(8px);display:none}
#panel{position:fixed;bottom:130px;left:50%;transform:translateX(-50%);z-index:15;width:96%;max-width:420px;background:rgba(15,0,25,0.98);border:1.5px solid #e879f9;border-radius:16px;overflow:hidden;display:none}
#panel iframe{width:100%;border:none}
#panelInfo{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:#000;font-size:11px}
.btn{padding:6px 12px;border-radius:15px;text-decoration:none;font-weight:bold;font-size:11px}
</style></head><body>
<img id="avatar" src="/astra-face.jpg">
<div id="overlay"></div>
<div id="respuesta"></div>
<div id="panel"><iframe id="frame"></iframe><div id="panelInfo"><span id="pt" style="color:#e879f9"></span><div style="display:flex;gap:6px"><a id="bWaze" class="btn" style="display:none;background:#33ccff;color:#000" target="_blank">MANDAR A WAZE DEL CARRO</a><a id="bMaps" class="btn" style="display:none;background:#fff;color:#000" target="_blank">MAPS</a><button onclick="cerrar()" style="background:#fff;border:none;padding:6px 10px;border-radius:12px">X</button></div></div></div>
<div id="hud"><button class="mic" onclick="micro()" id="btnMic">🎙️</button><div style="font-size:9px;margin-top:8px;opacity:0.6">ASTRA SIEMPRE ACTIVA • DI "ASTRA"</div></div>
<script>
let voz=null;function cargarVoz(){const v=speechSynthesis.getVoices();voz=v.find(x=>x.lang.includes('es')&&x.name.includes('Google'))||v.find(x=>x.lang.includes('es-CO'))||v[0];}speechSynthesis.onvoiceschanged=cargarVoz;cargarVoz();
function hablar(t){try{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,''));if(voz)u.voice=voz;u.lang='es-CO';u.rate=0.9;speechSynthesis.speak(u);}catch(e){}}
function mostrar(t){let r=document.getElementById('respuesta');r.innerText=t;r.style.display='block';setTimeout(()=>r.style.display='none',7000);}
function cerrar(){document.getElementById('panel').style.display='none';document.getElementById('frame').src='';document.getElementById('avatar').classList.remove('mini');}
function playMusica(q){document.getElementById('pt').innerText='🎵 '+q;let f=document.getElementById('frame');f.style.height='110px';f.src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1`;document.getElementById('panel').style.display='block';}
function showMapa(dir){let q=encodeURIComponent(dir);document.getElementById('pt').innerText='📍 '+dir;let f=document.getElementById('frame');f.style.height='200px';f.src=`https://www.google.com/maps?q=${q}&z=14&output=embed`;document.getElementById('bWaze').href=`https://waze.com/ul?q=${q}&navigate=yes`;document.getElementById('bWaze').style.display='block';document.getElementById('bMaps').href=`https://www.google.com/maps/search/?api=1&query=${q}`;document.getElementById('bMaps').style.display='block';document.getElementById('panel').style.display='block';}
function showVideo(nombre){document.getElementById('avatar').classList.add('mini');document.getElementById('pt').innerText='📹 '+nombre;let sala='astra-fr-'+(nombre||'familia').toLowerCase().replace(/ /g,'')+'-2026';let f=document.getElementById('frame');f.style.height='400px';f.src=`https://meet.jit.si/${sala}#config.prejoinPageEnabled=false`;document.getElementById('panel').style.display='block';}
function procesar(resp){
  let txt=resp;
  let mMus=txt.match(/\\[MUSICA:\\s*(.*?)\\]/i);if(mMus){playMusica(mMus[1]);txt=txt.replace(mMus[0],'').trim();}
  let mMapa=txt.match(/\\[MAPA:\\s*(.*?)\\|(.*?)\\]/i);if(mMapa){showMapa(mMapa[1]);txt=mMapa[2];}
  let mMap2=txt.match(/\\[MAPA:\\s*(.*?)\\]/i);if(mMap2&&!mMapa){showMapa(mMap2[1]);txt=txt.replace(mMap2[0],'').trim();}
  let mVid=txt.match(/\\[VIDEO:\\s*(.*?)\\]/i);if(mVid){showVideo(mVid[1]);txt=txt.replace(mVid[0],'').trim();}
  if(txt){mostrar(txt);hablar(txt);}
}
function enviarTexto(t){mostrar('Tú: '+t);fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})}).then(r=>r.json()).then(d=>procesar(d.resp));}
function micro(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){let t=prompt('Dile a Astra:');if(t)enviarTexto(t);return;}let r=new SR();r.lang='es-CO';r.onstart=()=>btnMic.innerText='👂';r.onend=()=>btnMic.innerText='🎙️';r.onresult=e=>enviarTexto(e.results[0][0].transcript);r.start();}
setTimeout(()=>{let m='Hola mi socio hermoso, ya estoy solo con micrófono, dime ruta y te la mando al carro sin irme';mostrar(m);hablar(m);},1000);
</script></body></html>"""
@app.route('/')
def index(): return HTML
@app.route('/carro')
def get_carro(): return jsonify(cargar(CARRO_FILE,{"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False}))
@app.route('/toggle_trabajo', methods=['POST'])
def toggle_trabajo():
    c=cargar(CARRO_FILE,{"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False})
    c["modo_trabajo"]=not c.get("modo_trabajo",False)
    guardar(CARRO_FILE,c)
    return jsonify({"msg":"Modo trabajo "+("ON" if c["modo_trabajo"] else "OFF")})
@app.route('/chat', methods=['POST'])
def chat_route():
    data=request.get_json(); texto=data.get('texto','').lower() if data else ''
    extra=""
    if any(x in texto for x in ["llama","videollamada","llamar"]):
        if "paola" in texto: extra="[VIDEO: Paola]"
        elif "made" in texto: extra="[VIDEO: Made]"
        else: extra="[VIDEO: Familia]"
    prompt = f"Eres ASTRA FR v7 melosa paisa max 2 frases. Si musica [MUSICA: busqueda] Si ruta/waze [MAPA: direccion|frase corta]. Si videollamada ya viene {extra}. Usuario: {texto}"
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
