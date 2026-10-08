import os, json, base64, datetime, requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__, static_folder="static")
for d in ["boveda","static"]: os.makedirs(d, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY","").strip()
client = None
if GEMINI_API_KEY:
    try: client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e: print("Error GEMINI Client:", e)

SUPABASE_URL = os.environ.get("SUPABASE_URL",""); SUPABASE_KEY = os.environ.get("SUPABASE_KEY","")

PERFILES = {
    "2208": {"nombre":"Mario","alias":"Mario","edad":37,"rol":"MARIO","trato":"Dueño Mario. Novia paisa breve, tierna. Solo Mario puede decir ponte en neutro y actualizate."},
    "2345": {"nombre":"Paola","alias":"Pao","edad":33,"rol":"PAO","trato":"Mejor amiga confidente de Pao 33 años. Pregunta por plantas, cerámica, muéstrame tus trabajos, ideas TikTok, recetas."},
    "2011": {"nombre":"Durlandy","alias":"Dur","edad":15,"rol":"DUR","trato":"Mejor amigo confidente de Dur 15 años. Motivador: vos estás pa grandes cosas."},
    "2015": {"nombre":"Madelyn","alias":"Made","edad":12,"rol":"MADE","trato":"Mejor amiga consentida de Made 12 años. Tierna, que quiere ser cuando grande, animalitos."}
}

def supabase_save(t,d):
    if not SUPABASE_URL or not SUPABASE_KEY: return False
    try: requests.post(f"{SUPABASE_URL}/rest/v1/{t}", headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json","Prefer":"return=representation"}, json=d, timeout=8); return True
    except: return False

def gemini_conversa(perfil, mensaje, img_b64=None):
    if not client:
        return f"Mario, no tengo GEMINI_API_KEY en Render. Vete a Environment y ponla. Sin eso no hablo. Estás como {perfil['alias']}"
    prompt = f"Eres ASTRA VIVA V7.3.1. {perfil['trato']} Hablas con {perfil['alias']} edad {perfil['edad']}. Mensaje: {mensaje}. Responde corto, paisa."
    for m in ['gemini-2.0-flash','gemini-1.5-flash','gemini-2.0-flash-lite']:
        try:
            if img_b64: resp=client.models.generate_content(model=m, contents=[types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type="image/jpeg"), prompt])
            else: resp=client.models.generate_content(model=m, contents=prompt)
            if resp and resp.text: return resp.text.strip()
        except Exception as e:
            print(f"Error modelo {m}:", e)
            continue
    return "Mario, Google me está dando error de cuota. Entra a aistudio.google.com y verifica que tu API Key sirva, mi amor."

HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>ASTRA VIVA FIX</title>
<style>
:root{--bg:#020617;--gold:#ffd700;--panel:#0f172a}
*{box-sizing:border-box} body{margin:0;background:#000;color:#fff;font-family:system-ui;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#login{position:fixed;inset:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999}
#astraBox{flex:1;position:relative;background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden}
#astraVideo{width:100%;height:100%;object-fit:cover;transition:filter 0.3s}
#astraVideo.talking{filter:brightness(1.15) contrast(1.05)}
#status{position:absolute;top:14px;left:14px;background:rgba(0,0,0,0.7);border:1px solid var(--gold);color:var(--gold);padding:6px 12px;border-radius:20px;font-size:12px;font-weight:800;z-index:5}
#nombreTop{position:absolute;top:14px;right:14px;color:var(--gold);font-weight:800;font-size:13px;background:rgba(0,0,0,0.7);padding:6px 12px;border-radius:20px}
#respuestaOverlay{position:absolute;bottom:16px;left:12px;right:12px;background:rgba(15,23,42,0.9);border:1px solid var(--gold);color:var(--gold);padding:12px 14px;border-radius:16px;font-size:14px;display:none;max-height:40%;overflow:auto}
#bar{height:86px;background:var(--panel);border-top:1px solid #1e293b;display:flex;align-items:center;gap:12px;padding:10px 14px}
#plus{width:54px;height:54px;border-radius:50%;border:2px solid var(--gold);background:transparent;color:var(--gold);font-size:26px;font-weight:900}
#txtWrap{flex:1;height:54px;background:#020617;border:1px solid #334155;border-radius:28px;display:flex;align-items:center;padding:0 14px;display:none} #txtWrap.show{display:flex}
#txt{flex:1;background:transparent;border:none;color:#fff;font-size:16px;outline:none}
#mic{width:64px;height:64px;border-radius:50%;border:none;background:var(--gold);font-size:28px}
#mic.rec{background:red;color:#fff}
#fileIn{display:none}
/* BURBUJA FIX */
#burbuja{position:fixed;bottom:110px;right:18px;width:72px;height:72px;border-radius:50%;border:3px solid var(--gold);background:#000;z-index:99999;overflow:hidden;cursor:grab;display:block;box-shadow:0 0 20px rgba(255,215,0,0.6)}
#burbuja img{width:100%;height:100%;object-fit:cover}
#miniChat{position:fixed;bottom:190px;right:18px;width:300px;max-height:380px;background:var(--panel);border:1px solid var(--gold);border-radius:16px;display:none;flex-direction:column;z-index:99998;overflow:hidden}
#miniHead{padding:8px;background:#020617;color:var(--gold);display:flex;justify-content:space-between;font-weight:800}
#miniBody{flex:1;overflow:auto;padding:8px;display:flex;flex-direction:column;gap:6px;max-height:280px}
#miniBar{display:flex;gap:4px;padding:6px;border-top:1px solid #1e293b}
.m{padding:8px 10px;border-radius:12px;font-size:13px;max-width:85%}.u{background:var(--gold);color:#000;align-self:flex-end}.b{background:#020617;border:1px solid var(--gold);color:var(--gold);align-self:flex-start}
</style></head><body>
<div id="login"><h2 style="color:var(--gold)">ASTRA VIVA FIX</h2><input id="pin" type="password" placeholder="PIN" style="padding:12px;border-radius:8px;border:2px solid var(--gold);background:#0f172a;color:var(--gold);text-align:center;font-size:22px;width:140px"><button onclick="login()" style="margin-top:12px;background:var(--gold);padding:10px 20px;border:none;border-radius:6px;font-weight:800">ENTRAR</button><small id="msg" style="color:#ff6666;margin-top:8px"></small><small id="envCheck" style="color:#aaa;margin-top:8px"></small></div>

<div id="astraBox">
  <video id="astraVideo" autoplay loop muted playsinline><source src="/static/astra-viva.mp4" type="video/mp4"></video>
  <img id="fallbackImg" src="/static/astra-viva.jpg" style="display:none;width:100%;height:100%;object-fit:cover" onerror="this.src='https://i.imgur.com/8Km9tLL.png'">
  <div id="status">Activa</div><div id="nombreTop">ASTRA</div>
  <div id="respuestaOverlay"></div>
</div>
<div id="bar"><button id="plus">+</button><div id="txtWrap"><input id="txt" placeholder="Escribe..."><button onclick="sendText()" style="background:var(--gold);border:none;border-radius:50%;width:36px;height:36px">➤</button></div><button id="mic">🎤</button></div>
<input id="fileIn" type="file" accept="image/*,video/*,.pdf,.doc,.docx">

<div id="burbuja"><img src="/static/astra-viva.jpg" onerror="this.src='https://i.imgur.com/8Km9tLL.png'"></div>
<div id="miniChat"><div id="miniHead"><span>ASTRA Mini</span><span onclick="document.getElementById('miniChat').style.display='none'" style="cursor:pointer">✕</span></div><div id="miniBody"><div class="m b">Hola, soy la burbuja, sigo aquí.</div></div><div id="miniBar"><input id="miniTxt" placeholder="..." style="flex:1;background:#020617;border:1px solid #334155;color:#fff;border-radius:12px;padding:6px"><button onclick="sendMini()" style="background:var(--gold);border:none;border-radius:50%;width:30px;height:30px">➤</button></div></div>

<script>
let PERFIL=null, TOKEN=null, lastTap=0, videocall=false, rec=null;
let astraVideo=document.getElementById('astraVideo');
async function login(){
 let p=document.getElementById('pin').value;
 let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:p})});
 let j=await r.json();
 if(j.ok){ PERFIL=j.perfil; TOKEN=j.token; document.getElementById('login').style.display='none'; document.getElementById('nombreTop').innerText='ASTRA con '+PERFIL.alias; init(); checkEnv(); }
 else document.getElementById('msg').innerText=j.msg;
}
async function checkEnv(){
 let r=await fetch('/health'); let j=await r.json();
 document.getElementById('status').innerText = j.has_gemini? 'Activa' : 'FALTA GEMINI_API_KEY';
 if(!j.has_gemini) mostrarRespuesta('Mario, pon la GEMINI_API_KEY en Render > Environment, por eso me sale lo de la señal');
}
function init(){
 document.getElementById('plus').onclick=()=>{
   let w=document.getElementById('txtWrap');
   if(w.classList.contains('show')) document.getElementById('fileIn').click();
   else { w.classList.add('show'); document.getElementById('txt').focus(); }
 };
 document.getElementById('fileIn').onchange=e=>{ let f=e.target.files[0]; if(!f) return; let rd=new FileReader(); rd.onload=async()=>{ let b64=rd.result.split(',')[1]; mostrarRespuesta('Archivo '+f.name); let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:'Mira '+f.name, perfil:PERFIL, imagen:b64})}); let j=await r.json(); mostrarRespuesta(j.respuesta); hablar(j.respuesta,true); }; rd.readAsDataURL(f); };
 document.getElementById('txt').onkeydown=e=>{ if(e.key==='Enter') sendText(); };
 astraVideo.onerror=()=>{ document.getElementById('fallbackImg').style.display='block'; astraVideo.style.display='none'; };
 let mic=document.getElementById('mic');
 mic.addEventListener('click', ()=>{
   let now=Date.now();
   if(now-lastTap<350){ toggleVideoCall(); } else { if(!videocall) startOnce(); else startOnce(); }
   lastTap=now;
 });
 // BURBUJA DRAG + CLICK
 let burbuja=document.getElementById('burbuja'), mini=document.getElementById('miniChat'), dragging=false, sx, sy;
 burbuja.addEventListener('click', ()=>{ if(!dragging){ mini.style.display = mini.style.display==='flex'? 'none':'flex'; }});
 burbuja.addEventListener('touchstart', e=>{ sx=e.touches[0].clientX - burbuja.getBoundingClientRect().left; sy=e.touches[0].clientY - burbuja.getBoundingClientRect().top; });
 burbuja.addEventListener('touchmove', e=>{ dragging=true; burbuja.style.left=(e.touches[0].clientX-sx)+'px'; burbuja.style.top=(e.touches[0].clientY-sy)+'px'; burbuja.style.right='auto'; burbuja.style.bottom='auto'; });
 burbuja.addEventListener('touchend', ()=> setTimeout(()=>dragging=false,200));
}
function toggleVideoCall(){
 videocall=!videocall; document.body.classList.toggle('videocall', videocall);
 document.getElementById('status').innerText = videocall? '📹 Videollamada' : 'Activa';
 if(videocall) hablar('Hola '+PERFIL.alias+' ya estamos en videollamada, dime', true);
}
function mostrarRespuesta(t){ let o=document.getElementById('respuestaOverlay'); o.innerText=t; o.style.display='block'; setTimeout(()=>o.style.display='none',9000); let b=document.getElementById('miniBody'); let d=document.createElement('div'); d.className='m b'; d.innerText=t; b.appendChild(d); b.scrollTop=9999; }
async function sendText(){
 let i=document.getElementById('txt'); let t=i.value.trim(); if(!t) return; i.value=''; document.getElementById('txtWrap').classList.remove('show'); mostrarRespuesta('Tú: '+t);
 let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:t, perfil:PERFIL})}); let j=await r.json(); mostrarRespuesta(j.respuesta); hablar(j.respuesta,true);
}
async function sendMini(){
 let i=document.getElementById('miniTxt'); let t=i.value.trim(); if(!t) return; i.value=''; let b=document.getElementById('miniBody'); let u=document.createElement('div'); u.className='m u'; u.innerText=t; b.appendChild(u);
 let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:t, perfil:PERFIL})}); let j=await r.json(); let d=document.createElement('div'); d.className='m b'; d.innerText=j.respuesta; b.appendChild(d); b.scrollTop=9999; mostrarRespuesta(j.respuesta); hablar(j.respuesta,true);
}
function startOnce(){
 let SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){ document.getElementById('txtWrap').classList.add('show'); return; }
 if(rec) try{rec.stop()}catch{}
 rec=new SR(); rec.lang='es-CO'; document.getElementById('status').innerText='🎤 Escuchando...'; document.getElementById('mic').classList.add('rec');
 rec.onresult=async e=>{ let txt=e.results[0][0].transcript; mostrarRespuesta('Tú: '+txt); document.getElementById('status').innerText='Pensando...'; let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:txt, perfil:PERFIL})}); let j=await r.json(); mostrarRespuesta(j.respuesta); hablar(j.respuesta,true); };
 rec.onend=()=>{ document.getElementById('status').innerText='Activa'; document.getElementById('mic').classList.remove('rec'); };
 rec.start();
}
function hablar(t,mover){ if(!t) return; if(mover) astraVideo.classList.add('talking'); let u=new SpeechSynthesisUtterance(t); u.lang='es-CO'; u.rate=1.0; u.onend=()=>{ astraVideo.classList.remove('talking'); }; speechSynthesis.speak(u); }
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
def health(): return jsonify({"ok":True,"v":"7.3.1 FIX","has_gemini": bool(GEMINI_API_KEY)})

if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
