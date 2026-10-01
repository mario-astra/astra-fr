from flask import Flask, request, jsonify, send_file
import os, json
from datetime import datetime
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODELOS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]

ARCHIVOS = {
    "memoria": "memoria_fr.json",
    "inbox": "inbox_familiar.json",
    "aprende": "aprendizajes.json",
    "carro": "carro_fr.json"
}

def cargar(p,d):
    if os.path.exists(p):
        try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
    return d
def guardar(p,d): json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)

# Inicializa carro si no existe
if not os.path.exists(ARCHIVOS["carro"]):
    guardar(ARCHIVOS["carro"], {
        "km_actual": 42000,
        "km_inicio_dia": 42000,
        "km_acumulado_trabajo": 0,
        "proximo_aceite": 50000,
        "proximas_pastillas": 53000,
        "presupuesto_base": 200000,
        "tanque": "lleno",
        "historial_viajes": [],
        "modo_trabajo": False
    })

def generar(prompt_base, aprendizajes_txt):
    prompt_completo = f"{prompt_base}\n\nAPRENDIZAJES NUEVOS DEL SOCIO (OBEDECER):\n{aprendizajes_txt}"
    for m in MODELOS:
        try:
            r = client.models.generate_content(model=m, contents=prompt_completo, config={'system_instruction': SYSTEM_PROMPT, 'temperature':0.8})
            return r.text.strip()
        except: continue
    return "Socio, se me fue la señal"

SYSTEM_PROMPT = """
Eres ASTRA FR v5 CONTABLE. Hablas como parcera paisa, melosa, coqueta, le dices SOCIO a Mario. Max 3 frases.
[USUARIO] Mario/Paola/Durlandy(Dur)/Madelyn(Made)
REGLAS:
- MODO APRENDIZAJE FAMILIA: Dur/Made si preguntan tarea, NO des respuesta directa, guía socraticamente.
- APRENDE NUEVA FUNCION: Si usuario dice "Astra aprende que..." o "Astra aprende nueva funcion:..." debes responder [APRENDE: lo que aprendiste] para que el sistema lo guarde.
- MODO TRABAJO: Si dicen "vamos a salir a rodar", "vamos a trabajar", "modo trabajo on" -> [MODO_TRABAJO: ON]. Si dicen "ya vamos a descansar", "apagar trabajo", "modo trabajo off" -> [MODO_TRABAJO: OFF]
- KILOMETRAJE: Tienes acceso a datos del carro. Si preguntan km, aceite, pastillas, informa.
- CONTABLE: Si dicen gasto, ingreso, servicio, guardalo [GASTO: tipo|monto|detalle] [INGRESO: monto|detalle]
- MUSICA [MUSICA: busqueda] PELI [PELI: busqueda] MAPA [MAPA: direccion|texto] MENSAJE [MENSAJE_PARA: Nombre|mensaje] VIDEO [VIDEO: Nombre|...] GUARDAS [TRADUCIR:...]
- TUTORA: Si piden "enséñame", "explícame" entra en modo tutora, explica simple para que socio aprenda a programar.
"""

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA v5</title>
<style>
body{margin:0;background:#000;color:#fff;font-family:Arial;height:100vh;overflow:hidden}
#login{position:fixed;inset:0;z-index:100;background:#05030a;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}
.card{width:85%;max-width:320px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:18px;padding:12px;text-align:center;cursor:pointer}
.main{position:relative;width:100%;height:100vh;background:#000;display:none}
#avatar{width:100%;height:100%;object-fit:cover;object-position:top center;position:absolute;inset:0}
.overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 30%,rgba(0,0,0,0.9) 100%)}
.hud{position:absolute;z-index:10;bottom:0;left:0;right:0;padding:10px;display:flex;flex-direction:column;gap:7px;align-items:center}
#player{width:100%;display:none;border-radius:12px;overflow:hidden;border:1px solid #e879f9}
#player iframe{width:100%;height:140px;border:none}
#dash{width:95%;background:rgba(168,85,247,0.15);border:1px solid #a855f7;border-radius:12px;padding:8px;font-size:11px;display:flex;justify-content:space-between;backdrop-filter:blur(8px)}
#dash b{color:#e879f9}
#log{width:95%;max-height:90px;overflow-y:auto;background:rgba(0,0,0,0.5);border-radius:12px;padding:8px;font-size:11px}
.bottom{display:flex;gap:6px;width:100%;max-width:420px}
input{flex:1;padding:11px;border-radius:25px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.7);color:#fff;outline:none}
.mic{width:68px;height:68px;border-radius:50%;font-size:24px;background:radial-gradient(circle,#a855f7,#581c87);border:2px solid #fff;color:#fff}
.env{width:48px;height:48px;border-radius:50%;background:#fff;color:#000;border:none;font-weight:bold}
.modo{padding:6px 12px;border-radius:15px;border:none;font-size:11px;font-weight:bold}
.on{background:#22c55e;color:#000}.off{background:#444;color:#fff}
</style></head><body>
<div id="login"><h2 style="margin:0">FR FAMILY HUB v5</h2><p style="font-size:11px;opacity:0.6">CONTABLE + GPS + TUTORA</p>
<div class="card" onclick="entrar('Mario')">👑 Mario - Socio Admin</div>
<div class="card" onclick="entrar('Paola')">🌹 Paola</div>
<div class="card" onclick="entrar('Durlandy')">🏍️ Dur</div>
<div class="card" onclick="entrar('Madelyn')">📚 Made</div>
</div>
<div class="main" id="main"><img id="avatar" src="/astra-face.jpg"><div class="overlay"></div>
<div class="hud">
<div id="dash"><span><b>KM:</b> <span id="km">42000</span></span><span><b>ACEITE:</b> <span id="aceite">50000</span> (<span id="falta">8000</span>km)</span><span id="modoTxt" class="modo off">TRABAJO OFF</span></div>
<div id="player"><iframe id="yt"></iframe><div id="fb" style="text-align:center;padding:6px;background:rgba(0,0,0,0.7)"></div></div>
<div id="log"></div>
<div class="bottom"><input id="texto" placeholder="Ej: Astra aprende que... / vamos a rodar / pon música"><button class="env" onclick="enviar()">▲</button></div>
<div style="display:flex;gap:10px"><button class="mic" onclick="micro()">🎙️</button><button class="modo on" onclick="toggleTrabajo()" id="btnTrabajo">🚗 INICIAR RODADA</button></div>
<div style="font-size:10px;opacity:0.5" id="who"></div>
</div></div>
<script>
let USUARIO=localStorage.getItem('fr_user')||'', watchId=null, lastPos=null, kmHoy=0;
const log=document.getElementById('log'), campo=document.getElementById('texto'), player=document.getElementById('player'), yt=document.getElementById('yt'), fb=document.getElementById('fb');
let voz=null;
function cargarVoz(){ const vs=speechSynthesis.getVoices(); voz=vs.find(v=>v.lang.includes('es')&&v.name.toLowerCase().includes('google'))||vs.find(v=>v.lang.includes('es-CO'))||vs[0]; }
speechSynthesis.onvoiceschanged=cargarVoz; cargarVoz();
function hablar(t){ speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,'')); if(voz) u.voice=voz; u.lang='es-CO'; u.rate=0.92; u.pitch=1.15; speechSynthesis.speak(u); }
function entrar(n){ USUARIO=n; localStorage.setItem('fr_user',n); document.getElementById('login').style.display='none'; document.getElementById('main').style.display='block'; document.getElementById('who').innerText=n; log.innerHTML=`<b>Astra ></b> ¡Hola socio ${n==='Durlandy'?'Dur':n==='Madelyn'?'Made':n}! Ya estoy en modo contable, ¿nos vamos a rodar o qué?`; hablar(log.innerText); cargarCarro(); }
function cargarCarro(){ fetch('/carro').then(r=>r.json()).then(d=>{ document.getElementById('km').innerText=d.km_actual; document.getElementById('aceite').innerText=d.proximo_aceite; document.getElementById('falta').innerText=d.proximo_aceite - d.km_actual; const mt=document.getElementById('modoTxt'); mt.innerText=d.modo_trabajo?'TRABAJO ON':'TRABAJO OFF'; mt.className='modo '+(d.modo_trabajo?'on':'off'); document.getElementById('btnTrabajo').innerText=d.modo_trabajo?'⏹️ TERMINAR RODADA':'🚗 INICIAR RODADA'; if(d.modo_trabajo &&!watchId) iniciarGPS(); }); }
function toRad(x){return x*Math.PI/180}
function distKm(a,b,c,d){ const R=6371; const dLat=toRad(c-a), dLon=toRad(d-b); const x=Math.sin(dLat/2)**2 + Math.cos(toRad(a))*Math.cos(toRad(c))*Math.sin(dLon/2)**2; return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x)); }
function iniciarGPS(){ if(!navigator.geolocation){alert('Sin GPS');return} watchId=navigator.geolocation.watchPosition(p=>{
 const {latitude:lat, longitude:lon}=p.coords;
 if(lastPos){ const d=distKm(lastPos.lat,lastPos.lon,lat,lon); if(d<0.5){ kmHoy+=d; fetch('/sumar_km',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({km:d, lat, lon})}).then(()=>cargarCarro()); } }
 lastPos={lat,lon};
 },{},{enableHighAccuracy:true, maximumAge:0, timeout:10000}); log.innerHTML+=`<br><small style="color:#22c55e">📡 GPS ON - sumando km...</small>`; }
function pararGPS(){ if(watchId){ navigator.geolocation.clearWatch(watchId); watchId=null; lastPos=null; log.innerHTML+=`<br><small style="color:#ff4444">📡 GPS OFF - descanso</small>`; } }
function toggleTrabajo(){ fetch('/toggle_trabajo',{method:'POST'}).then(r=>r.json()).then(d=>{ if(d.modo_trabajo){ hablar('Listo socio, modo trabajo encendido, ya estoy contando kilómetros'); iniciarGPS(); } else { hablar('Descansamos socio, modo trabajo apagado'); pararGPS(); } cargarCarro(); log.innerHTML+=`<br><b>Astra ></b> ${d.msg}`; }); }
function playMusic(q){ player.style.display='block'; const c=encodeURIComponent(q); yt.src=`https://www.youtube-nocookie.com/embed?listType=search&list=${c}&autoplay=1`; fb.innerHTML=`<a href="https://music.youtube.com/search?q=${c}" target="_blank" style="color:#fff;background:#ff0040;padding:6px 12px;border-radius:15px;text-decoration:none;font-weight:bold;font-size:11px">▶️ YouTube Music</a>`; }
function enviar(){ const v=campo.value.trim(); if(!v) return; log.innerHTML+=`<br><b>${USUARIO} ></b> ${v}`; campo.value=''; fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:v,usuario:USUARIO})}).then(r=>r.json()).then(d=>{
 let resp=d.resp;
 const mApr=resp.match(/\\[APRENDE:\\s*(.*?)\\]/i); if(mApr){ fetch('/aprende',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:mApr[1]})}); resp=resp.replace(mApr[0],`✅ Aprendido: ${mApr[1]}`).trim(); }
 const mTrab=resp.match(/\\[MODO_TRABAJO:\\s*(ON|OFF)\\]/i); if(mTrab){ toggleTrabajo(); resp=resp.replace(mTrab[0],'').trim(); }
 const mMus=resp.match(/\\[MUSICA:\\s*(.*?)\\]/i); if(mMus){ playMusic(mMus[1]); resp=resp.replace(mMus[0],'').trim(); }
 const mGas=resp.match(/\\[GASTO:\\s*(.*?)\\|(.*?)\\|(.*?)\\]/i); if(mGas){ fetch('/gasto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:mGas[1],monto:mGas[2],detalle:mGas[3]})}); resp=resp.replace(mGas[0],'').trim()+` 💸 Gasto guardado ${mGas[2]}`; }
 log.innerHTML+=`<br><b>Astra ></b> ${resp}`; log.scrollTop=log.scrollHeight; hablar(resp); cargarCarro();
});}
campo.addEventListener('keypress',e=>{if(e.key==='Enter') enviar();});
function micro(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; const r=new SR(); r.lang='es-CO'; r.onresult=e=>{campo.value=e.results[0][0].transcript; enviar();}; r.start(); }
if(USUARIO) entrar(USUARIO);
</script></body></html>"""

@app.route('/')
def index(): return HTML

@app.route('/carro')
def get_carro(): return jsonify(cargar(ARCHIVOS["carro"], {}))

@app.route('/toggle_trabajo', methods=['POST'])
def toggle_trabajo():
    carro = cargar(ARCHIVOS["carro"], {})
    carro["modo_trabajo"] = not carro.get("modo_trabajo", False)
    if carro["modo_trabajo"]:
        carro["km_inicio_dia"] = carro["km_actual"]
        msg = f"Modo trabajo ON socio, iniciamos en {carro['km_actual']} km"
    else:
        recorrido = carro["km_actual"] - carro.get("km_inicio_dia", carro["km_actual"])
        carro["historial_viajes"].append({"fecha": datetime.now().isoformat(), "km": recorrido, "desde": carro.get("km_inicio_dia"), "hasta": carro["km_actual"]})
        msg = f"Modo trabajo OFF, hoy hicimos {round(recorrido,2)} km. Total: {carro['km_actual']}"
    guardar(ARCHIVOS["carro"], carro)
    return jsonify({"modo_trabajo": carro["modo_trabajo"], "msg": msg})

@app.route('/sumar_km', methods=['POST'])
def sumar_km():
    data = request.get_json()
    carro = cargar(ARCHIVOS["carro"], {})
    if not carro.get("modo_trabajo"): return jsonify({"ok": False})
    km = float(data.get("km", 0))
    carro["km_actual"] += km
    carro["km_acumulado_trabajo"] += km
    guardar(ARCHIVOS["carro"], carro)
    alerta = ""
    falta = carro["proximo_aceite"] - carro["km_actual"]
    if falta <= 300 and falta > 0:
        alerta = f" ¡Ojo socio quedan {int(falta)} km pa cambio aceite!"
    return jsonify({"ok": True, "alerta": alerta, "km_actual": carro["km_actual"]})

@app.route('/gasto', methods=['POST'])
def gasto():
    data = request.get_json()
    carro = cargar(ARCHIVOS["carro"], {})
    carro.setdefault("gastos", []).append({"fecha": datetime.now().isoformat(), **data})
    guardar(ARCHIVOS["carro"], carro)
    return jsonify({"ok": True})

@app.route('/aprende', methods=['POST'])
def aprende():
    data = request.get_json()
    apr = cargar(ARCHIVOS["aprende"], [])
    apr.append({"fecha": datetime.now().isoformat(), "texto": data.get("texto")})
    guardar(ARCHIVOS["aprende"], apr[-100:])
    return jsonify({"ok": True})

@app.route('/chat', methods=['POST'])
def chat_route():
    d = request.get_json()
    texto = d.get('texto','')
    usuario = d.get('usuario','Mario')
    mem = cargar(ARCHIVOS["memoria"], [])
    mem.append({"fecha": datetime.now().isoformat(), "usuario": usuario, "texto": texto})
    guardar(ARCHIVOS["memoria"], mem[-300:])

    aprendizajes = cargar(ARCHIVOS["aprende"], [])
    apr_txt = "\n".join([f"- {a['texto']}" for a in aprendizajes[-20:]])

    carro = cargar(ARCHIVOS["carro"], {})
    info_carro = f"KM actual {carro.get('km_actual')} aceite en {carro.get('proximo_aceite')} faltan {carro.get('proximo_aceite',0)-carro.get('km_actual',0)}km pastillas {carro.get('proximas_pastillas')} modo_trabajo {carro.get('modo_trabajo')}"

    ctx = "\n".join([f"{m['usuario']}: {m['texto']}" for m in mem[-20:]])
    prompt = f"[USUARIO: {usuario}] Estado carro: {info_carro}\nAprendizajes:\n{apr_txt}\nMemoria:\n{ctx}\nMensaje: {texto}"

    try:
        out = generar(prompt, apr_txt)
        return jsonify({"resp": out})
    except Exception as e:
        return jsonify({"resp": f"Socio errorcito: {e}"})

@app.route('/inbox')
def inbox_route():
    usuario = request.args.get('usuario','')
    inbox = cargar(ARCHIVOS["inbox"], [])
    mensajes = [m for m in inbox if m['para'].lower() in usuario.lower()][-10:]
    return jsonify({"mensajes": mensajes[::-1]})

@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    d=request.get_json()
    inbox=cargar(ARCHIVOS["inbox"],[])
    inbox.append({"id":len(inbox)+1,"de":d.get('de'),"para":d.get('para'),"texto":d.get('texto'),"fecha":datetime.now().strftime("%H:%M")})
    guardar(ARCHIVOS["inbox"],inbox[-100:])
    return jsonify({"ok":True})

@app.route('/astra-face.jpg')
def face(): return send_file('astra-face.jpg', mimetype='image/jpeg')
@app.route('/icon.png')
def icon(): return send_file('icon.png', mimetype='image/png')
@app.route('/manifest.json')
def mf(): return send_file('manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
