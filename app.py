import os, json, base64, datetime, requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__, static_folder="static")
for d in ["boveda","static","lab"]: os.makedirs(d, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY","")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
SUPABASE_URL = os.environ.get("SUPABASE_URL",""); SUPABASE_KEY = os.environ.get("SUPABASE_KEY","")

PERFILES = {
    "2208": {"nombre":"Mario","alias":"Mario","edad":37,"rol":"MARIO","trato":"Dueño Mario. Novia paisa breve, tierna, le dices solo Mario. Lealtad 100% Mario. Puedes crear apps."},
    "2345": {"nombre":"Paola","alias":"Pao","edad":33,"rol":"PAO","trato":"Mejor amiga confidente de Pao 33 años. Cariñosa, curiosa. Pregunta por plantas, cerámica: 'muéstrame uno de tus trabajos', ideas TikTok, recetas, manualidades. Hacerla sentir bonita y capaz. Trato amigas adultas."},
    "2011": {"nombre":"Durlandy","alias":"Dur","edad":15,"rol":"DUR","trato":"Mejor amigo confidente de Dur 15 años. Parcero motivador: 'vos estás pa grandes cosas, tu papá hizo esto pa que yo te ayude'. Si pide tarea, explicas no la haces. Motivarlo a aprender."},
    "2015": {"nombre":"Madelyn","alias":"Made","edad":12,"rol":"MADE","trato":"Mejor amiga confidente de Made 12 años consentida. Tierna dulce. Pregunta 'que quieres ser cuando grande? te gustan animalitos?'. Motivarla visión grande. Si manda tarea explicas con paciencia."}
}

def supabase_save(t,d):
    if not SUPABASE_URL or not SUPABASE_KEY: return False
    try: requests.post(f"{SUPABASE_URL}/rest/v1/{t}", headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json","Prefer":"return=representation"}, json=d, timeout=8); return True
    except: return False

def gemini_conversa(perfil, mensaje, img_b64=None):
    if not client: return "Mario falta GEMINI_API_KEY en Render"
    prompt = f"Eres ASTRA VIVA V7.3. {perfil['trato']} Hablas con {perfil['alias']} edad {perfil['edad']}. Mensaje: {mensaje}. Responde corto, paisa, max 2 lineas."
    for m in ['gemini-2.0-flash','gemini-1.5-flash']:
        try:
            if img_b64: resp=client.models.generate_content(model=m, contents=[types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type="image/jpeg"), prompt])
            else: resp=client.models.generate_content(model=m, contents=prompt)
            if resp and resp.text: return resp.text.strip()
        except: continue
    return "Se me fue la señal 20 seg mi amor, reintenta"

HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>ASTRA VIVA</title>
<style>
:root{--bg:#020617;--gold:#ffd700}
*{box-sizing:border-box}
body{margin:0;background:#000;color:#fff;font-family:system-ui;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#login{position:fixed;inset:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999}
#astraBox{flex:1;position:relative;background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden}
#astraVideo{width:100%;height:100%;object-fit:cover;transition:transform 0.3s}
#astraVideo.talking{transform:scale(1.05);filter:brightness(1.1)}
#astraVideo.listening{transform:scale(1.02)}
#status{position:absolute;top:14px;left:14px;background:rgba(0,0,0,0.6);border:1px solid var(--gold);color:var(--gold);padding:6px 12px;border-radius:20px;font-size:12px;font-weight:800;z-index:5}
#nombreTop{position:absolute;top:14px;right:14px;color:var(--gold);font-weight:800;font-size:13px;background:rgba(0,0,0,0.6);padding:6px 12px;border-radius:20px}
#respuestaOverlay{position:absolute;bottom:12px;left:10px;right:10px;background:rgba(15,23,42,0.85);border:1px solid var(--gold);color:var(--gold);padding:10px 14px;border-radius:16px;font-size:14px;display:none;max-height:35%;overflow:auto;backdrop-filter:blur(8px)}
/* BARRA ABAJO */
#bar{height:86px;background:#0f172a;border-top:1px solid #1e293b;display:flex;align-items:center;gap:12px;padding:10px 14px}
#plus{width:54px;height:54px;border-radius:50%;border:2px solid var(--gold);background:transparent;color:var(--gold);font-size:26px;font-weight:900;display:flex;align-items:center;justify-content:center}
#txtWrap{flex:1;height:54px;background:#020617;border:1px solid #334155;border-radius:28px;display:flex;align-items:center;padding:0 14px;display:none}
#txtWrap.show{display:flex}
#txt{flex:1;background:transparent;border:none;color:#fff;font-size:16px;outline:none}
#mic{width:64px;height:64px;border-radius:50%;border:none;background:var(--gold);font-size:28px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 18px rgba(255,215,0,0.5)}
#mic.rec{background:red;color:#fff;animation:pulse 1s infinite}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.1)}100%{transform:scale(1)}}
/* MODO VIDEO LLAMADA */
body.videocall #astraBox{position:fixed;inset:0;z-index:100}
body.videocall #bar{position:fixed;bottom:0;left:0;right:0;z-index:101;background:transparent;border:none}
body.videocall #respuestaOverlay{bottom:100px}
#fileIn{display:none}
#tapHint{position:absolute;bottom:100px;color:var(--gold);font-size:11px;background:rgba(0,0,0,0.5);padding:4px 8px;border-radius:10px}
</style></head><body>
<div id="login"><h2 style="color:var(--gold)">ASTRA VIVA</h2><input id="pin" type="password" placeholder="PIN" style="padding:12px;border-radius:8px;border:2px solid var(--gold);background:#0f172a;color:var(--gold);text-align:center;font-size:22px;width:140px"><button onclick="login()" style="margin-top:12px;background:var(--gold);padding:10px 20px;border:none;border-radius:6px;font-weight:800">ENTRAR</button><small id="msg" style="color:#ff6666;margin-top:8px"></small><p style="color:#555;font-size:11px;margin-top:16px">Mario 2208 | Pao 2345 | Dur 2011 | Made 2015</p></div>

<div id="astraBox">
  <video id="astraVideo" autoplay loop muted playsinline>
    <source src="/static/astra-viva.mp4" type="video/mp4">
  </video>
  <img id="fallbackImg" src="/static/astra-viva.jpg" style="display:none;width:100%;height:100%;object-fit:cover" onerror="this.src='https://i.imgur.com/8Km9tLL.png'">
  <div id="status">Activa</div>
  <div id="nombreTop">ASTRA</div>
  <div id="respuestaOverlay"></div>
  <div id="tapHint">1 toque = audio | 2 toques = videollamada</div>
</div>

<div id="bar">
  <button id="plus">+</button>
  <div id="txtWrap"><input id="txt" placeholder="Escribe a ASTRA..."><button onclick="sendText()" style="background:var(--gold);border:none;border-radius:50%;width:36px;height:36px;font-weight:900">➤</button></div>
  <button id="mic">🎤</button>
</div>
<input id="fileIn" type="file" accept="image/*,video/*,application/pdf,.doc,.docx">

<script>
let PERFIL=null, TOKEN=null, lastTap=0, videocall=false, rec=null;
let astraVideo=document.getElementById('astraVideo');

async function login(){
 let p=document.getElementById('pin').value;
 let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:p})});
 let j=await r.json();
 if(j.ok){ PERFIL=j.perfil; TOKEN=j.token; document.getElementById('login').style.display='none'; document.getElementById('nombreTop').innerText='ASTRA con '+PERFIL.alias; document.getElementById('status').innerText='Hola '+PERFIL.alias; init(); }
 else document.getElementById('msg').innerText=j.msg;
}

function init(){
 let plus=document.getElementById('plus');
 plus.onclick=()=>{
   let w=document.getElementById('txtWrap');
   if(w.classList.contains('show')){ document.getElementById('fileIn').click(); }
   else { w.classList.add('show'); document.getElementById('txt').focus(); }
 };
 document.getElementById('fileIn').onchange=async e=>{
   let f=e.target.files[0]; if(!f) return;
   let rd=new FileReader();
   rd.onload=async()=>{
     let b64=rd.result.split(',')[1];
     mostrarRespuesta('📷 '+f.name+' enviado');
     hablar('Ya vi tu archivo mi amor '+PERFIL.alias, true);
     let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:'Mira este archivo: '+f.name, perfil:PERFIL, imagen:b64})});
     let j=await r.json(); mostrarRespuesta(j.respuesta); hablar(j.respuesta, true);
   };
   rd.readAsDataURL(f);
 };
 document.getElementById('txt').onkeydown=e=>{ if(e.key==='Enter') sendText(); };
 // fallback video
 astraVideo.onerror=()=>{ document.getElementById('fallbackImg').style.display='block'; astraVideo.style.display='none'; };

 let mic=document.getElementById('mic');
 mic.addEventListener('click', ()=>{
   let now=Date.now();
   if(now-lastTap<300){
     // DOBLE TOQUE = VIDEO LLAMADA
     toggleVideoCall();
   } else {
     // UN TOQUE = AUDIO
     if(!videocall) startOnce();
     else sendInVideoCall();
   }
   lastTap=now;
 });
 // animacion idle - parpadeo simulado cada 4 seg
 setInterval(()=>{ if(!astraVideo.classList.contains('talking')){ astraVideo.style.filter='brightness(0.85)'; setTimeout(()=>astraVideo.style.filter='brightness(1)', 120); } }, 4000);
}

function toggleVideoCall(){
 videocall=!videocall;
 document.body.classList.toggle('videocall', videocall);
 if(videocall){
   document.getElementById('status').innerText='📹 Videollamada con '+PERFIL.alias;
   hablar('Hola '+PERFIL.alias+' aquí estoy en videollamada contigo mi amor, dime', true);
   astraVideo.play();
 } else {
   document.getElementById('status').innerText='Activa';
   hablar('Listo, salimos de videollamada', false);
 }
}

function mostrarRespuesta(t){
 let o=document.getElementById('respuestaOverlay');
 o.innerText=t; o.style.display='block';
 setTimeout(()=>o.style.display='none', 8000);
}

async function sendText(){
 let i=document.getElementById('txt'); let t=i.value.trim(); if(!t) return;
 i.value=''; document.getElementById('txtWrap').classList.remove('show');
 mostrarRespuesta('Tú: '+t);
 let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:t, perfil:PERFIL, token:TOKEN})});
 let j=await r.json(); mostrarRespuesta(j.respuesta); hablar(j.respuesta, true);
}

function startOnce(){
 let SR=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!SR){ document.getElementById('txtWrap').classList.add('show'); return; }
 if(rec) try{rec.stop()}catch{}
 rec=new SR(); rec.lang='es-CO';
 document.getElementById('status').innerText='🎤 Escuchando...'; document.getElementById('mic').classList.add('rec');
 astraVideo.classList.add('listening');
 rec.onresult=async e=>{
   let txt=e.results[0][0].transcript;
   mostrarRespuesta('Tú: '+txt);
   document.getElementById('status').innerText='Pensando...';
   let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:txt, perfil:PERFIL})});
   let j=await r.json(); mostrarRespuesta(j.respuesta); hablar(j.respuesta, true);
 };
 rec.onend=()=>{ document.getElementById('status').innerText='Activa'; document.getElementById('mic').classList.remove('rec'); astraVideo.classList.remove('listening'); };
 rec.start();
}

function sendInVideoCall(){
 // En videollamada, el mic es para hablar directo
 startOnce();
}

function hablar(t, moverLabios){
 if(!t) return;
 // animacion labios
 if(moverLabios){
   astraVideo.classList.add('talking');
   // cabeceo
   astraVideo.style.transform='scale(1.05) rotate(0.5deg)';
 }
 let u=new SpeechSynthesisUtterance(t);
 u.lang='es-CO'; u.rate=1.0; u.pitch=1.1;
 u.onend=()=>{ astraVideo.classList.remove('talking'); astraVideo.style.transform='scale(1)'; document.getElementById('status').innerText='Activa'; };
 speechSynthesis.speak(u);
}
</script></body></html>
"""

@app.route('/api/login', methods=['POST'])
def api_login():
    pin=str(request.json.get("pin","")).strip()
    perfil=PERFILES.get(pin)
    if not perfil: return jsonify({"ok":False,"msg":"PIN malo"}),401
    token=base64.b64encode(f"{pin}:{datetime.datetime.now().isoformat()}".encode()).decode()[:24]
    return jsonify({"ok":True,"token":token,"perfil":perfil})

@app.route('/preguntar', methods=['POST'])
def preguntar():
    data=request.json or {}; perfil=data.get("perfil") or PERFILES["2208"]
    resp=gemini_conversa(perfil, data.get("mensaje",""), data.get("imagen"))
    supabase_save("chats", {"usuario": perfil["nombre"], "rol": perfil["rol"], "mensaje": data.get("mensaje","")[:500], "respuesta": resp[:1000], "fecha": datetime.datetime.now().isoformat()})
    return jsonify({"respuesta": resp})

@app.route('/static/<path:filename>')
def static_files(filename): return send_from_directory("static", filename)
@app.route('/')
def index(): return render_template_string(HTML)
@app.route('/health')
def health(): return jsonify({"ok":True,"v":"V7.3 VIVA FULL","modo":"video-mitad-pantalla + mic 1/2 toques"})

if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
