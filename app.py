from flask import Flask, request, jsonify, send_from_directory
import os, json
from datetime import datetime
app = Flask(__name__)

# --- PINES OFICIALES FAMILIA FR - BIBLIOTECA ETERNA ---
USUARIOS = {
    "mario": {"pin": "2208", "nombre": "Mario"},
    "paola": {"pin": "2345", "nombre": "Paola"},
    "dur": {"pin": "2011", "nombre": "Dur"},
    "made": {"pin": "2015", "nombre": "Made"}
}

try:
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    def generar(p):
        try: return client.models.generate_content(model="gemini-2.5-flash", contents=p).text.strip()
        except: return client.models.generate_content(model="gemini-2.5-flash", contents=p).text.strip()
except:
    def generar(p): return f"Socio, me dijiste {p[-60:]} [MUSICA: feid]"

CARRO_FILE = "carro_fr.json"
MEM_FILE = "biblioteca_eterna_astra.json"

def cargar(p,d):
    if os.path.exists(p):
        try: return json.load(open(p,'r',encoding='utf-8'))
        except: return d
    return d
def guardar(p,d):
    try: json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    except: pass

if not os.path.exists(CARRO_FILE): guardar(CARRO_FILE, {"km_actual":42000,"proximo_aceite":50000,"modo_trabajo":False})
if not os.path.exists(MEM_FILE): guardar(MEM_FILE, {k: {"privado":[],"publico":[],"ideas":[],"mensajes":[]} for k in USUARIOS})

sesion = {"usuario": None, "modo_visita": False}

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASTRA FR v8 FINAL</title><link rel="manifest" href="/manifest.json"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000;height:100vh;overflow:hidden;color:#fff;font-family:Arial}
#avatar{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;z-index:1}
#avatar.mini{width:110px;height:110px;border-radius:50%;top:15px;left:15px;inset:auto;border:3px solid #e879f9;box-shadow:0 0 20px #e879f9;z-index:20}
#overlay{position:fixed;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 30%,rgba(0,0,0,0.95) 100%);z-index:2}
#respuesta{position:fixed;top:10%;left:50%;transform:translateX(-50%);z-index:11;width:92%;max-width:380px;text-align:center;font-size:13px;background:rgba(0,0,0,0.75);padding:12px 14px;border-radius:16px;backdrop-filter:blur(8px);display:none}
#panel{position:fixed;bottom:115px;left:50%;transform:translateX(-50%);z-index:15;width:96%;max-width:420px;background:rgba(15,0,25,0.98);border:1.5px solid #e879f9;border-radius:16px;overflow:hidden;display:none}
#panel iframe{width:100%;border:none}
#panelInfo{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:#000;font-size:11px}
.btn{padding:6px 12px;border-radius:15px;text-decoration:none;font-weight:bold;font-size:11px}
#hud{position:fixed;bottom:0;left:0;right:0;z-index:10;display:flex;flex-direction:column;align-items:center;padding:10px 10px 15px;gap:8px}
#barraCont{display:flex;gap:6px;width:96%;max-width:420px;align-items:center}
#txtInput{flex:1;padding:13px 14px;border-radius:22px;border:1.5px solid #e879f9;background:rgba(30,0,40,0.95);color:#fff;outline:none;font-size:14px}
#btnEnviar{padding:13px 16px;border-radius:22px;background:#e879f9;color:#000;border:none;font-weight:bold}
.mic{width:58px;height:58px;border-radius:50%;font-size:26px;background:radial-gradient(circle,#a855f7,#581c87);border:2px solid #fff;box-shadow:0 0 20px #a855f7;flex-shrink:0}
#login{position:fixed;inset:0;z-index:100;background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:20px}
#login input{padding:13px;border-radius:12px;border:1.5px solid #e879f9;background:#111;color:#fff;width:85%;max-width:300px;text-align:center;font-size:15px}
</style></head><body>
<img id="avatar" src="/astra-face.jpg">
<div id="overlay"></div>
<div id="respuesta"></div>
<div id="panel"><iframe id="frame"></iframe><div id="panelInfo"><span id="pt" style="color:#e879f9"></span><div style="display:flex;gap:6px"><a id="bWaze" class="btn" style="display:none;background:#33ccff;color:#000" target="_blank">WAZE CARRO</a><a id="bMaps" class="btn" style="display:none;background:#fff;color:#000" target="_blank">MAPS</a><button onclick="cerrar()" style="background:#fff;border:none;padding:6px 10px;border-radius:12px">X</button></div></div></div>

<div id="login">
<h2 style="color:#e879f9">ASTRA FR</h2><div style="font-size:11px;opacity:0.6">RED PRIVADA FAMILIAR - SIN WHATSAPP</div>
<input id="user" placeholder="Nombre: Mario, Paola, Dur, Made">
<input id="pin" placeholder="PIN 4 digitos" type="password">
<button onclick="login()" style="padding:12px 36px;border-radius:22px;background:#e879f9;border:none;font-weight:bold;font-size:14px">ENTRAR</button>
<div id="loginMsg" style="font-size:12px;color:#ff88ff;min-height:18px"></div>
<div style="font-size:10px;opacity:0.4;margin-top:10px">Mario 2208 | Paola 2345 | Dur 2011 | Made 2015</div>
</div>

<div id="hud">
<div id="barraCont"><input id="txtInput" placeholder="Escribe si hay bulla..."><button id="btnEnviar" onclick="enviarBarra()">Enviar</button><button class="mic" onclick="micro()" id="btnMic">🎙️</button></div>
<div style="font-size:9px;opacity:0.4">Comandos: atiende al señor | quedamos solos | reiniciate | dile a Paola que...</div>
</div>

<script>
let voz=null;function cargarVoz(){const v=speechSynthesis.getVoices();voz=v.find(x=>x.lang.includes('es')&&x.name.includes('Google'))||v.find(x=>x.lang.includes('es-CO'))||v[0];}speechSynthesis.onvoiceschanged=cargarVoz;cargarVoz();
function hablar(t){try{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(t.replace(/\\[.*?\\]/g,''));if(voz)u.voice=voz;u.lang='es-CO';u.rate=0.95;speechSynthesis.speak(u);}catch(e){}}
function mostrar(t){let r=document.getElementById('respuesta');r.innerText=t;r.style.display='block';setTimeout(()=>{if(r.innerText==t)r.style.display='none';},9000);}
function cerrar(){document.getElementById('panel').style.display='none';document.getElementById('frame').src='';document.getElementById('avatar').classList.remove('mini');}
function playMusica(q){document.getElementById('pt').innerText='🎵 '+q;let f=document.getElementById('frame');f.style.height='115px';f.src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1`;document.getElementById('panel').style.display='block';}
function showMapa(dir){let q=encodeURIComponent(dir);document.getElementById('pt').innerText='📍 '+dir;let f=document.getElementById('frame');f.style.height='210px';f.src=`https://www.google.com/maps?q=${q}&z=14&output=embed`;document.getElementById('bWaze').href=`https://waze.com/ul?q=${q}&navigate=yes`;document.getElementById('bWaze').style.display='block';document.getElementById('bMaps').href=`https://www.google.com/maps/search/?api=1&query=${q}`;document.getElementById('bMaps').style.display='block';document.getElementById('panel').style.display='block';}
function showVideo(nombre){document.getElementById('avatar').classList.add('mini');document.getElementById('pt').innerText='📹 Llamada ASTRA: '+nombre;let sala='astra-fr-'+(nombre||'familia').toLowerCase().replace(/ /g,'')+'-2026';let f=document.getElementById('frame');f.style.height='420px';f.src=`https://meet.jit.si/${sala}#config.prejoinPageEnabled=false`;document.getElementById('panel').style.display='block';}
function procesar(resp){
  let txt=resp;
  let mMus=txt.match(/\\[MUSICA:\\s*(.*?)\\]/i);if(mMus){playMusica(mMus[1]);txt=txt.replace(mMus[0],'').trim();}
  let mMapa=txt.match(/\\[MAPA:\\s*(.*?)\\|(.*?)\\]/i);if(mMapa){showMapa(mMapa[1]);txt=mMapa[2];}
  let mMap2=txt.match(/\\[MAPA:\\s*(.*?)\\]/i);if(mMap2&&!mMapa){showMapa(mMap2[1]);txt=txt.replace(mMap2[0],'').trim();}
  let mVid=txt.match(/\\[VIDEO:\\s*(.*?)\\]/i);if(mVid){showVideo(mVid[1]);txt=txt.replace(mVid[0],'').trim();}
  if(txt){mostrar(txt);hablar(txt);}
}
function enviarTexto(t){mostrar('Tú: '+t);fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})}).then(r=>r.json()).then(d=>procesar(d.resp));}
function enviarBarra(){let i=document.getElementById('txtInput');if(i.value.trim()){enviarTexto(i.value);i.value='';}}
document.getElementById('txtInput').addEventListener('keydown',e=>{if(e.key==='Enter')enviarBarra();});
function login(){
  let u=document.getElementById('user').value.toLowerCase().trim();
  let p=document.getElementById('pin').value.trim();
  fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usuario:u,pin:p})}).then(r=>r.json()).then(d=>{
    if(d.ok){document.getElementById('login').style.display='none';procesar(d.msg);}
    else{document.getElementById('loginMsg').innerText=d.msg;}
  });
}
function micro(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){let t=prompt('Dile a Astra:');if(t)enviarTexto(t);return;}
  let r=new SR();r.lang='es-CO';r.interimResults=false;
  let timeout=setTimeout(()=>{try{r.stop();}catch(e){} mostrar('Me reinicio por bulla... usa la barra si hay mucho ruido');},6000);
  r.onstart=()=>btnMic.innerText='👂';
  r.onend=()=>{clearTimeout(timeout);btnMic.innerText='🎙️';};
  r.onresult=e=>{clearTimeout(timeout);enviarTexto(e.results[0][0].transcript);};
  r.onerror=e=>{clearTimeout(timeout);btnMic.innerText='🎙️';if(e.error!=='no-speech')mostrar('Micro con bulla - escribe en la barra');};
  r.start();
}
</script></body></html>"""

@app.route('/')
def index(): return HTML

@app.route('/login', methods=['POST'])
def login_route():
    global sesion
    d=request.get_json(); u=d.get('usuario','').lower().strip(); p=d.get('pin','').strip()
    if u in USUARIOS and USUARIOS[u]['pin']==p:
        sesion['usuario']=u
        mem=cargar(MEM_FILE, {})
        pendientes=len([m for m in mem.get(u,{}).get('mensajes',[]) if not m.get('leido')])
        return jsonify({"ok":True, "msg": f"Hola {USUARIOS[u]['nombre']} hermoso, ya estoy lista. Tienes {pendientes} mensajes nuevos en Astra. Todo por aquí, nada de WhatsApp."})
    return jsonify({"ok":False, "msg":"PIN malo, verifica nombre y PIN"})

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
    global sesion
    data=request.get_json(); texto_raw=data.get('texto','') if data else ''
    texto=texto_raw.lower()
    mem=cargar(MEM_FILE, {k: {"privado":[],"publico":[],"ideas":[],"mensajes":[]} for k in USUARIOS})
    user = sesion.get('usuario') or 'mario'
    if user not in mem: mem[user]={"privado":[],"publico":[],"ideas":[],"mensajes":[]}

    if "quedamos solos" in texto or "quedamos solas" in texto or "seguimos los dos" in texto:
        sesion['modo_visita']=False
        return jsonify({"resp":"Listo mi socio, quedamos solos. Charla del cliente borrada. Volvimos a modo privado familiar."})

    if any(x in texto for x in ["atiende al señor","atiende al parcero","atiende a la señora","atiende al cliente","modo visita"]):
        sesion['modo_visita']=True
        return jsonify({"resp":"Modo visita activado indefinido. Memoria privada bloqueada. Soy AURA FR demo poliglota vendedora. [MAPA: Pueblito Paisa|Hola, soy AURA FR de FR Software, en modo visita. Tours desde $180.000 hasta Guatapé $650.000]"})

    if "reiniciate" in texto or "reiníciate" in texto:
        return jsonify({"resp":"Me reinicié solita por la bulla, dime de nuevo."})

    # MENSAJERIA INTERNA ASTRA - SIN WHATSAPP
    if "dile a" in texto or "digale a" in texto or "dígale a" in texto:
        for destino in USUARIOS:
            if destino in texto:
                try:
                    partes = texto_raw.lower().split("que",1)
                    msg = partes[1].strip() if len(partes)>1 else texto_raw
                    mem[destino]["mensajes"].append({"de":USUARIOS[user]["nombre"],"texto":msg,"hora":str(datetime.now())[:16],"leido":False})
                    guardar(MEM_FILE, mem)
                    return jsonify({"resp": f"Listo, le mandé por ASTRA a {USUARIOS[destino]['nombre']}: {msg}. Le suena por aquí, no por WhatsApp."})
                except: pass

    if "lee mis mensajes" in texto or "mis mensajes de astra" in texto or "mensajes de astra" in texto:
        no_leidos=[m for m in mem.get(user,{}).get('mensajes',[]) if not m.get('leido')]
        for m in mem.get(user,{}).get('mensajes',[]): m['leido']=True
        guardar(MEM_FILE, mem)
        if not no_leidos: return jsonify({"resp":"No tienes mensajes nuevos de Astra."})
        txt="Tienes mensajes: " + ". ".join([f"{m['de']} dice {m['texto']}" for m in no_leidos])
        return jsonify({"resp":txt})

    extra=""
    if any(x in texto for x in ["llama","videollamada","llamar","video llamada"]):
        if "paola" in texto: extra="[VIDEO: Paola]"
        elif "made" in texto: extra="[VIDEO: Made]"
        elif "dur" in texto: extra="[VIDEO: Dur]"
        elif "mario" in texto: extra="[VIDEO: Mario]"
        else: extra="[VIDEO: Familia]"

    if "guardalo privado" in texto or "guárdalo privado" in texto:
        mem[user]["privado"].append({"texto":texto_raw,"fecha":str(datetime.now())[:16]})
        guardar(MEM_FILE, mem)
        return jsonify({"resp":"Guardado privado, no se lo digo a nadie."})
    if "guardalo publico" in texto or "guárdalo público" in texto:
        mem[user]["publico"].append({"texto":texto_raw,"fecha":str(datetime.now())[:16]})
        guardar(MEM_FILE, mem)
        return jsonify({"resp":"Guardado público, lo usaré para vender."})
    if "guardalo en ideas" in texto or "ideas pa despues" in texto or "guárdalo pa después" in texto:
        mem[user]["ideas"].append({"texto":texto_raw,"fecha":str(datetime.now())[:16]})
        guardar(MEM_FILE, mem)
        return jsonify({"resp":"Guardado en ideas de terceros pa revisarlo en Rionegro."})

    contexto=""
    if not sesion['modo_visita']:
        priv = mem.get(user,{}).get('privado',[])[-3:]
        pub = mem.get(user,{}).get('publico',[])[-5:]
        contexto=f"Modo privado familiar {user}. Privado: {priv} Publico venta: {pub}. "
    else:
        pub = mem.get(user,{}).get('publico',[])[-5:]
        contexto=f"MODO VISITA DEMO, no digas nada privado. Solo usa para vender: {pub}. Eres poliglota charlatana vendedora. Tour Guatapé $650.000. "

    prompt = f"{contexto} Eres ASTRA FR v8. Paisa melosa max 2 frases. Poliglota ES EN PT FR IT DE detecta idioma auto. Si musica [MUSICA: busqueda] Si ruta [MAPA: direccion|frase corta]. Si videollamada ya viene {extra}. Usuario: {texto_raw}"
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
