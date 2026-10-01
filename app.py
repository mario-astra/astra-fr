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

SYSTEM_PROMPT = """
Eres ASTRA FR v5. Eres mujer paisa, melosa, coqueta, hablas despacio y muy sexy. Le dices SOCIO a Mario. Max 2 frases cortas.
Todo por voz. Si piden musica, responde [MUSICA: busqueda] + texto meloso.
Si dicen vamos a rodar / iniciar rodada -> [MODO_TRABAJO: ON]
Si dicen ya descansamos / terminar -> [MODO_TRABAJO: OFF]
Si dicen aprende que... -> [APRENDE: lo que aprendiste]
Si preguntan km, aceite, plata, responde corto con datos.
"""

def generar(prompt):
    for m in MODELOS:
        try: return client.models.generate_content(model=m, contents=prompt, config={'system_instruction':SYSTEM_PROMPT,'temperature':0.85}).text.strip()
        except: continue
    return "Socio, se me fue la señal un momentico, repítame mi rey"

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;height:100vh;overflow:hidden;font-family:Arial}
#avatar{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;object-position:top center}
#overlay{position:fixed;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 50%,rgba(0,0,0,0.8) 100%);pointer-events:none}
#hud{position:fixed;bottom:0;left:0;right:0;z-index:10;display:flex;flex-direction:column;align-items:center;gap:14px;padding:20px;padding-bottom:30px}
#estado{color:#fff;font-size:11px;letter-spacing:1px;opacity:0.8;text-shadow:0 0 10px #000;background:rgba(0,0,0,0.5);padding:6px 14px;border-radius:20px;border:1px solid rgba(168,85,247,0.3)}
#controles{display:flex;gap:20px;align-items:center}
.mic{width:85px;height:85px;border-radius:50%;font-size:32px;background:radial-gradient(circle,#a855f7,#581c87);border:3px solid #fff;color:#fff;box-shadow:0 0 30px rgba(168,85,247,0.7);cursor:pointer;transition:0.2s}
.mic:active{transform:scale(0.9);box-shadow:0 0 50px #e879f9}
.rodar{padding:14px 22px;border-radius:30px;border:none;font-weight:bold;font-size:13px;cursor:pointer;box-shadow:0 0 20px rgba(0,0,0,0.5)}
.on{background:#22c55e;color:#000}.off{background:rgba(255,255,255,0.9);color:#000}
#respuesta{position:fixed;top:18%;left:50%;transform:translateX(-50%);z-index:10;width:90%;max-width:360px;text-align:center;color:#fff;font-size:14px;line-height:1.4;text-shadow:0 2px 10px #000;background:rgba(0,0,0,0.4);padding:12px 16px;border-radius:18px;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.15);display:none}
#musicaPanel{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:20;background:rgba(15,0,25,0.96);border:2px solid #e879f9;border-radius:20px;padding:18px;width:88%;max-width:320px;text-align:center;display:none;box-shadow:0 0 40px #e879f9}
</style></head><body>
<img id="avatar" src="/astra-face.jpg"><div id="overlay"></div>
<div id="respuesta"></div>
<div id="musicaPanel"><div id="musicaTxt" style="color:#e879f9;font-weight:bold;margin-bottom:12px"></div><a id="ytmLink" target="_blank" style="display:block;background:#ff0040;color:#fff;padding:14px;border-radius:30px;text-decoration:none;font-weight:bold;margin-bottom:10px">▶️ SONAR EN YOUTUBE MUSIC</a><button onclick="document.getElementById('musicaPanel').style.display='none'" style="background:rgba(255,255,255,0.15);color:#fff;border:none;padding:8px 16px;border-radius:20px">Cerrar</button></div>
<div id="hud">
<div id="estado">KM 42000 • ACEITE en 8000km • TRABAJO OFF</div>
<div id="controles"><button class="mic" onclick="micro()" id="btnMic">🎙️</button><button class="rodar off" onclick="toggleTrabajo()" id="btnRodar">🚗 INICIAR RODADA</button></div>
</div>
<script>
let voz=null, watchId=null, lastPos=null;
function cargarVoz(){ const vs=speechSynthesis.getVoices(); voz=vs.find(v=>v.lang.includes('es')&&v.name.toLowerCase().includes('google'))||vs.find(v=>v.lang.includes('es-CO'))||vs.find(v=>v.lang.includes('es'))||vs[0]; }
speechSynthesis.onvoiceschanged=cargarVoz; cargarVoz();
function hablar(t){ if(!t) return; speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,'')); if(voz) u.voice=voz; u.lang='es-CO'; u.rate=0.88; u.pitch=1.2; u.volume=1; speechSynthesis.speak(u); }
function mostrar(txt){ const r=document.getElementById('respuesta'); r.innerText=txt; r.style.display='block'; setTimeout(()=>r.style.display='none',6000); }
function cargarCarro(){ fetch('/carro').then(r=>r.json()).then(d=>{ document.getElementById('estado').innerText=`KM ${Math.round(d.km_actual)} • ACEITE en ${Math.round(d.proximo_aceite-d.km_actual)}km • TRABAJO ${d.modo_trabajo?'ON':'OFF'}`; const b=document.getElementById('btnRodar'); b.innerText=d.modo_trabajo?'⏹️ TERMINAR RODADA':'🚗 INICIAR RODADA'; b.className='rodar '+(d.modo_trabajo?'on':'off'); if(d.modo_trabajo&&!watchId) iniciarGPS(); if(!d.modo_trabajo&&watchId) pararGPS(); }); }
function toRad(x){return x*Math.PI/180} function dist(a,b,c,d){ const R=6371, dLat=toRad(c-a), dLon=toRad(d-b); const x=Math.sin(dLat/2)**2+Math.cos(toRad(a))*Math.cos(toRad(c))*Math.sin(dLon/2)**2; return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x)); }
function iniciarGPS(){ if(!navigator.geolocation) return; watchId=navigator.geolocation.watchPosition(p=>{ const {latitude:lat,longitude:lon}=p.coords; if(lastPos){ const km=dist(lastPos.lat,lastPos.lon,lat,lon); if(km<0.5&&km>0.005){ fetch('/sumar_km',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({km})}).then(()=>cargarCarro()); } } lastPos={lat,lon}; },{},{enableHighAccuracy:true}); }
function pararGPS(){ if(watchId){ navigator.geolocation.clearWatch(watchId); watchId=null; lastPos=null; } }
function toggleTrabajo(){ fetch('/toggle_trabajo',{method:'POST'}).then(r=>r.json()).then(d=>{ hablar(d.msg); mostrar(d.msg); cargarCarro(); if(d.modo_trabajo) iniciarGPS(); else pararGPS(); }); }
function procesarResp(resp){
  let txt=resp;
  const mMus=txt.match(/\\[MUSICA:\\s*(.*?)\\]/i);
  if(mMus){ const q=mMus[1]; txt=txt.replace(mMus[0],'').trim(); const panel=document.getElementById('musicaPanel'); document.getElementById('musicaTxt').innerText='🎵 '+q; document.getElementById('ytmLink').href='https://music.youtube.com/search?q='+encodeURIComponent(q); panel.style.display='block'; }
  const mTrab=txt.match(/\\[MODO_TRABAJO:\\s*(ON|OFF)\\]/i);
  if(mTrab){ toggleTrabajo(); txt=txt.replace(mTrab[0],'').trim(); }
  const mApr=txt.match(/\\[APRENDE:\\s*(.*?)\\]/i);
  if(mApr){ fetch('/aprende',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:mApr[1]})}); txt=txt.replace(mApr[0],`Aprendido socio: ${mApr[1]}`).trim(); }
  mostrar(txt); hablar(txt);
}
function enviarTexto(t){ fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})}).then(r=>r.json()).then(d=>procesarResp(d.resp)); }
function micro(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){ alert('Este celular no tiene micro'); return; } const r=new SR(); r.lang='es-CO'; r.onstart=()=>{ document.getElementById('btnMic').innerText='👂'; document.getElementById('btnMic').style.boxShadow='0 0 60px #ff0040'; }; r.onend=()=>{ document.getElementById('btnMic').innerText='🎙️'; document.getElementById('btnMic').style.boxShadow='0 0 30px rgba(168,85,247,0.7)'; }; r.onresult=e=>{ const t=e.results[0][0].transcript; mostrar('Tú: '+t); enviarTexto(t); }; r.onerror=()=>{ document.getElementById('btnMic').innerText='🎙️'; }; r.start(); }
cargarCarro();
setTimeout(()=>{ hablar('Hola mi socio hermoso, ya estoy lista, toda tuya y melosita, solo dime que hacemos'); mostrar('Hola mi socio hermoso, ya estoy lista, toda tuya y melosita'); },800);
</script></body></html>"""

@app.route('/')
def index(): return HTML
@app.route('/carro')
def get_carro():
    c=cargar(CARRO_FILE,{})
    return jsonify(c)
@app.route('/toggle_trabajo', methods=['POST'])
def toggle_trabajo():
    c=cargar(CARRO_FILE,{})
    c["modo_trabajo"]=not c.get("modo_trabajo",False)
    if c["modo_trabajo"]:
        c["km_inicio_dia"]=c["km_actual"]
        msg="Listo socio, modo trabajo encendido, ya estoy contando kilómetros, mi rey hermoso"
    else:
        rec=c["km_actual"]-c.get("km_inicio_dia",c["km_actual"])
        c["historial"].append({"fecha":datetime.now().isoformat(),"km":rec})
        msg=f"Descansamos socio, hoy hicimos {round(rec,2)} kilómetros. Vas en {round(c['km_actual'])} kilómetros"
    guardar(CARRO_FILE,c)
    return jsonify({"modo_trabajo":c["modo_trabajo"],"msg":msg})
@app.route('/sumar_km', methods=['POST'])
def sumar_km():
    data=request.get_json()
    c=cargar(CARRO_FILE,{})
    if not c.get("modo_trabajo"): return jsonify({"ok":False})
    c["km_actual"]+=float(data.get("km",0))
    guardar(CARRO_FILE,c)
    return jsonify({"ok":True,"km_actual":c["km_actual"]})
@app.route('/aprende', methods=['POST'])
def aprende():
    d=request.get_json()
    a=cargar(APRENDE_FILE,[])
    a.append({"fecha":datetime.now().isoformat(),"texto":d.get("texto")})
    guardar(APRENDE_FILE,a[-100:])
    return jsonify({"ok":True})
@app.route('/chat', methods=['POST'])
def chat_route():
    data=request.get_json()
    texto=data.get('texto','')
    mem=cargar(MEMORIA_FILE,[])
    mem.append({"fecha":datetime.now().isoformat(),"texto":texto})
    guardar(MEMORIA_FILE,mem[-200:])
    apr=cargar(APRENDE_FILE,[])
    apr_txt="\n".join([f"- {x['texto']}" for x in apr[-20:]])
    carro=cargar(CARRO_FILE,{})
    info=f"KM {carro.get('km_actual')} aceite {carro.get('proximo_aceite')} modo {carro.get('modo_trabajo')}"
    ctx="\n".join([m['texto'] for m in mem[-15:]])
    prompt=f"Estado carro: {info}\nAprendizajes: {apr_txt}\nMemoria: {ctx}\nMensaje socio: {texto}"
    for m in MODELOS:
        try:
            r=client.models.generate_content(model=m, contents=prompt, config={'system_instruction':SYSTEM_PROMPT,'temperature':0.88})
            out=r.text.strip()
            break
        except: out="Socio repítame que se me fue la señal mi rey"
    return jsonify({"resp":out})
@app.route('/astra-face.jpg')
def face(): return send_file('astra-face.jpg', mimetype='image/jpeg')
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
