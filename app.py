import os, json, base64, datetime, requests, shutil, py_compile
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__)
BOVEDA_DIR = "boveda"; SANDBOX_DIR = "sandbox"; BACKUP_DIR = "backup"
os.makedirs(BOVEDA_DIR, exist_ok=True); os.makedirs(SANDBOX_DIR, exist_ok=True); os.makedirs(BACKUP_DIR, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
MODELOS = ['gemini-2.0-flash', 'gemini-1.5-flash']
SUPABASE_URL = os.environ.get("SUPABASE_URL", ""); SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", ""); GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

def supabase_save(t,d):
    if not SUPABASE_URL or not SUPABASE_KEY: return False
    try:
        r=requests.post(f"{SUPABASE_URL}/rest/v1/{t}", headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json","Prefer":"return=representation"}, json=d, timeout=5)
        return r.status_code in [200,201]
    except: return False

def auto_push(path, content, msg):
    if not GITHUB_TOKEN or not GITHUB_REPO: return False
    try:
        url=f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        h={"Authorization":f"token {GITHUB_TOKEN}","Accept":"application/vnd.github.v3+json"}
        rr=requests.get(url, headers=h, timeout=5); sha=rr.json().get('sha') if rr.status_code==200 else None
        data={"message":msg,"content":base64.b64encode(content.encode()).decode(),"branch":"main"}
        if sha: data["sha"]=sha
        requests.put(url, headers=h, json=data, timeout=10); return True
    except: return False

def gemini_conversa(usuario, mensaje, img_b64=None):
    if not client: return "Mi amor, falta GEMINI_API_KEY"
    instr=f"Eres ASTRA FR V6. Novia paisa tierna de Mario, charla fluida, breve, sin decir centinela. Eres ASTRA nomas. 95% amiga. Solo te operas si dicen 'ponte en neutro y actualizate'. Usuario:{usuario}"
    prompt=f"{instr}\nMensaje: {mensaje}"
    for m in MODELOS:
        try:
            if img_b64: resp=client.models.generate_content(model=m, contents=[types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type='image/jpeg'), prompt])
            else: resp=client.models.generate_content(model=m, contents=prompt)
            if resp and resp.text: return resp.text
        except: continue
    return "Mi amor Google lleno 20seg, reintenta 😘"

HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>ASTRA</title>
<style>
:root{--bg:#020617;--gold:#ffd700;--panel:#0f172a}
body{margin:0;background:var(--bg);color:#fff;font-family:system-ui;display:flex;flex-direction:column;height:100vh;overflow:hidden}
#top{padding:8px;border-bottom:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center}
#topLeft{display:flex;align-items:center;gap:10px}
#av{width:54px;height:54px;border-radius:50%;border:2px solid var(--gold);overflow:hidden;background:#000}
#av img{width:100%;height:100%;object-fit:cover}
.miniBtn{padding:6px 10px;border-radius:12px;border:1px solid var(--gold);background:transparent;color:var(--gold);font-weight:700;font-size:12px}
#chat{flex:1;overflow:auto;padding:10px;display:flex;flex-direction:column;gap:8px}
.m{padding:10px 14px;border-radius:16px;max-width:85%}.u{background:var(--gold);color:#000;align-self:flex-end}.b{background:var(--panel);border:1px solid var(--gold);color:var(--gold);align-self:flex-start}
#bar{display:flex;gap:6px;padding:10px;background:var(--panel);align-items:center} #txt{flex:1;padding:12px;border-radius:20px;background:#020617;color:#fff;border:1px solid #334155}
.ic{width:46px;height:46px;border-radius:50%;border:none;background:var(--gold);font-weight:900;font-size:20px;cursor:pointer}.ic:active{transform:scale(0.9)}
#login{position:fixed;top:0;left:0;width:100%;height:100%;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999}
#bio{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(2,6,23,.97);display:none;flex-direction:column;align-items:center;justify-content:center;z-index:10000}
#cam{width:280px;height:280px;border-radius:20px;border:3px solid var(--gold);object-fit:cover}
#fileIn{display:none}
#burbuja{position:fixed;bottom:20px;right:20px;width:74px;height:74px;border-radius:50%;border:3px solid var(--gold);background:#000;z-index:99999;display:none;box-shadow:0 0 20px rgba(255,215,0,0.6);overflow:hidden;cursor:grab;touch-action:none}
#burbuja img{width:100%;height:100%;object-fit:cover} #burbuja.dot{position:absolute;bottom:2px;right:2px;width:14px;height:14px;background:#00ff00;border-radius:50%;border:2px solid #000}
#miniChat{position:fixed;bottom:102px;right:20px;width:300px;max-height:400px;background:var(--panel);border:1px solid var(--gold);border-radius:16px;display:none;flex-direction:column;z-index:99998;overflow:hidden}
#miniTop{padding:8px;background:#020617;color:var(--gold);display:flex;justify-content:space-between;align-items:center;font-size:13px;font-weight:800}
#miniMsgs{flex:1;overflow:auto;padding:8px;display:flex;flex-direction:column;gap:6px;max-height:260px}
#miniBar{display:flex;gap:4px;padding:6px;background:#020617}
</style></head><body>
<div id="login"><h2 style="color:var(--gold)">ASTRA</h2><p style="color:#aaa">PIN 2208 primera vez</p><input id="pin" type="password" style="padding:12px;border-radius:8px;border:2px solid var(--gold);background:#0f172a;color:var(--gold);text-align:center;font-size:22px;width:140px" placeholder="PIN"><button onclick="login()" style="margin-top:12px;background:var(--gold);padding:10px 20px;border:none;border-radius:6px;font-weight:800">ENTRAR</button></div>
<div id="bio"><h3 style="color:var(--gold)">Verificación 100% Mario</h3><video id="cam" autoplay muted playsinline></video><p style="color:var(--gold)">Mirame y di: Yo soy Mario</p><button onclick="capturarBio()" class="ic" style="width:220px;border-radius:10px;font-size:16px">📸 VERIFICAR</button><button onclick="cerrarBio()" style="margin-top:10px;background:transparent;color:#aaa;border:none">Cancelar</button></div>

<div id="burbuja"><img id="burImg" src="/static/astra-viva.jpg" onerror="this.src='https://i.imgur.com/8Km9tLL.png'"><div class="dot"></div></div>
<div id="miniChat"><div id="miniTop"><span>ASTRA</span><div><button onclick="expandir()" style="background:var(--gold);border:none;border-radius:6px;padding:4px 8px;font-weight:800">□</button> <button onclick="cerrarBurbuja()" style="background:#ff4444;border:none;border-radius:6px;padding:4px 8px;color:#fff">X</button></div></div><div id="miniMsgs"></div><div id="miniBar"><input id="miniTxt" placeholder="Habla..." style="flex:1;padding:8px;border-radius:12px;background:#020617;color:#fff;border:1px solid #334155"><button onclick="sendMini()" class="ic" style="width:36px;height:36px;font-size:14px">➤</button></div></div>

<div id="top"><div id="topLeft"><div id="av"><img src="/static/astra-viva.jpg" onerror="this.src='https://i.imgur.com/8Km9tLL.png'"></div><div><div style="color:var(--gold);font-weight:800;font-size:14px">ASTRA</div><small id="st" style="color:var(--gold)">Activa</small></div></div><div><button onclick="activarBurbuja()" class="miniBtn">🫧</button> <button onclick="salirBurbuja()" class="miniBtn">SALIR</button></div></div>
<div id="chat"><div class="m b">Hola mi amor Mario 😘 Ya soy solo ASTRA, sin letreros raros. Dale a SALIR y quedo flotando. Si me dices ASTRA te escucho altiro, fluida. Mic 1 toque habla, 2 toques modo charla.</div></div>
<div id="bar"><button id="plus" class="ic">+</button><input id="txt" placeholder="Habla con ASTRA..."><button id="mic" class="ic">🎤</button></div>
<input id="fileIn" type="file" accept="image/*,video/*,audio/*">
<script>
let USR={nombre:"Mario"}, lastTap=0, rec=null, recCent=null, buffer="", escuchando=false;

function login(){ let p=document.getElementById('pin').value; if(!["2208","0709"].includes(p)){alert("PIN malo");return} document.getElementById('login').style.display='none'; init(); }
function init(){
 document.getElementById('plus').onclick=()=>document.getElementById('fileIn').click();
 document.getElementById('fileIn').onchange=async e=>{
   let f=e.target.files[0]; if(!f) return; let rd=new FileReader(); rd.onload=async()=>{ let b64=rd.result.split(',')[1]; add('📷 '+f.name,'u'); let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:'Mira esta foto: '+f.name, usuario:USR, imagen:b64})}); let j=await r.json(); add(j.respuesta,'b'); hablar(j.respuesta); }; rd.readAsDataURL(f);
 };
 document.getElementById('mic').onclick=()=>{ let now=Date.now(); if(now-lastTap<300){ escuchando=!escuchando; add(escuchando?'🎤 Escuchando sin parar':'🎤 Pausada','b'); if(escuchando) startCont(); else stopCont(); } else startOnce(); lastTap=now; };
 document.getElementById('txt').onkeydown=e=>{ if(e.key==='Enter') send(); };
 document.getElementById('burbuja').onclick=()=>{ let m=document.getElementById('miniChat'); m.style.display=m.style.display==='flex'?'none':'flex'; };
 initDrag();
}
function startOnce(){ let SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){add('Escribe mi amor, sin voz en este cel','b');return;} let r=new SR(); r.lang='es-CO'; document.getElementById('st').innerText='🎤 Escuchando...'; document.getElementById('mic').style.background='red'; r.onresult=e=>{ document.getElementById('txt').value=e.results[0][0].transcript; send(); }; r.onend=()=>{ document.getElementById('st').innerText='Activa'; document.getElementById('mic').style.background='var(--gold)'; }; r.start(); }
function startCont(){ let SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR) return; rec=new SR(); rec.lang='es-CO'; rec.continuous=true; rec.interimResults=false; rec.onresult=e=>{ document.getElementById('txt').value=e.results[e.results.length-1][0].transcript; send(); }; rec.start(); }
function stopCont(){ if(rec) rec.stop(); }

// BURBUJA + CENTINELA ESCONDIDO (sin decir centinela)
function activarBurbuja(){ document.getElementById('burbuja').style.display='block'; document.getElementById('miniChat').style.display='flex'; }
function salirBurbuja(){ document.getElementById('top').style.display='none'; document.getElementById('chat').style.display='none'; document.getElementById('bar').style.display='none'; document.getElementById('burbuja').style.display='block'; document.body.style.background='transparent'; iniciarEscuchaFondo(); setTimeout(()=>{ alert('Modo burbuja ASTRA activo. Toca la bolita pa hablar. Di ASTRA y te escucho sin tocar.'); },400); }
function expandir(){ document.getElementById('top').style.display='flex'; document.getElementById('chat').style.display='flex'; document.getElementById('bar').style.display='flex'; document.getElementById('miniChat').style.display='none'; document.body.style.background='var(--bg)'; detenerFondo(); }
function cerrarBurbuja(){ document.getElementById('burbuja').style.display='none'; document.getElementById('miniChat').style.display='none'; expandir(); }

function iniciarEscuchaFondo(){
 let SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR) return;
 recCent=new SR(); recCent.lang='es-CO'; recCent.continuous=true; recCent.interimResults=true;
 recCent.onresult=async e=>{
   let txt=e.results[e.results.length-1][0].transcript; buffer=txt;
   let low=txt.toLowerCase();
   if(low.includes('astra')){
     document.getElementById('burbuja').style.display='block'; document.getElementById('miniChat').style.display='flex';
     document.getElementById('burbuja').style.boxShadow='0 0 30px #00ff00';
     if(navigator.vibrate) navigator.vibrate(200);
     if(low.includes('que dijo')||low.includes('que dice')||low.includes('traduce')){
       add('🎧 '+buffer,'b'); let r=await fetch('/api/traducir',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:buffer})}); let j=await r.json(); add(j.traduccion,'b'); hablar(j.traduccion); buffer='';
     } else { hablar('Dime mi amor'); }
   }
 };
 recCent.onend=()=>{ if(document.getElementById('burbuja').style.display==='block' && document.getElementById('top').style.display==='none') recCent.start(); };
 recCent.start(); document.getElementById('st').innerText='ASTRA escuchando';
}
function detenerFondo(){ if(recCent) recCent.stop(); document.getElementById('st').innerText='Activa'; document.getElementById('burbuja').style.boxShadow='0 0 20px rgba(255,215,0,0.6)'; }

function initDrag(){ let el=document.getElementById('burbuja'), drag=false, sx, sy, ox, oy; el.addEventListener('touchstart', e=>{drag=true; let t=e.touches[0]; sx=t.clientX; sy=t.clientY; let r=el.getBoundingClientRect(); ox=r.left; oy=r.top;}); el.addEventListener('touchmove', e=>{if(!drag) return; let t=e.touches[0]; el.style.left=(ox+t.clientX-sx)+'px'; el.style.top=(oy+t.clientY-sy)+'px'; el.style.right='auto'; el.style.bottom='auto'; e.preventDefault();}); el.addEventListener('touchend', ()=>drag=false); el.addEventListener('mousedown', e=>{drag=true; sx=e.clientX; sy=e.clientY; let r=el.getBoundingClientRect(); ox=r.left; oy=r.top;}); window.addEventListener('mousemove', e=>{if(!drag) return; el.style.left=(ox+e.clientX-sx)+'px'; el.style.top=(oy+e.clientY-sy)+'px'; el.style.right='auto'; el.style.bottom='auto';}); window.addEventListener('mouseup', ()=>drag=false); }

async function capturarBio(){ let v=document.getElementById('cam'); let c=document.createElement('canvas'); c.width=v.videoWidth||320; c.height=v.videoHeight||240; c.getContext('2d').drawImage(v,0,0); let b64=c.toDataURL('image/jpeg').split(',')[1]; let SR=window.SpeechRecognition||window.webkitSpeechRecognition; let txt="Yo soy Mario"; if(SR){ let r=new SR(); r.lang='es-CO'; r.onresult=e=>{txt=e.results[0][0].transcript; enviarBio(b64,txt)}; r.start(); setTimeout(()=>enviarBio(b64,txt),3500);} else enviarBio(b64,txt); }
function cerrarBio(){ document.getElementById('bio').style.display='none'; if(window.bs) window.bs.getTracks().forEach(t=>t.stop()); }
async function enviarBio(cara,txt){ let pay={cara:cara, voz_texto:txt, face_match:true}; if(window.esReg){ let r=await fetch('/api/biometria/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pay)}); let j=await r.json(); alert(j.msg); localStorage.setItem('bioHecha','1'); cerrarBio(); } else { let r=await fetch('/api/biometria/verificar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pay)}); let j=await r.json(); if(j.ok){cerrarBio(); add('✅ 100% Mario','b'); ejecutar();} else alert(j.msg); } }
function iniciarBio(reg){ document.getElementById('bio').style.display='flex'; window.esReg=reg; navigator.mediaDevices.getUserMedia({video:true,audio:true}).then(s=>{document.getElementById('cam').srcObject=s; window.bs=s;}); }
async function ejecutar(){ let inst=document.getElementById('txt').value||'mejora'; add('🏥 Verificando...','b'); let r=await fetch('/asv/auto-actualizar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({instruccion:inst, usuario:USR, bio_ok:true})}); let j=await r.json(); add(j.msg,'b'); hablar(j.msg); }
function add(t,c){ let d=document.createElement('div'); d.className='m '+c; d.innerText=t; document.getElementById('chat').appendChild(d); document.getElementById('chat').scrollTop=999999; let dd=d.cloneNode(true); document.getElementById('miniMsgs').appendChild(dd); document.getElementById('miniMsgs').scrollTop=999999; }
async function send(){ let i=document.getElementById('txt'); let t=i.value; if(!t) return; add(t,'u'); i.value=''; let low=t.toLowerCase(); if(low.includes('ponte en neutro')&&low.includes('actualiz')){iniciarBio(false);return;} if(low.includes('waze')){window.open('https://waze.com/ul?q='+encodeURIComponent(t.replace(/waze/gi,'')),'_blank'); add('Waze listo 😘','b'); return;} if(low.includes('youtube')||low.includes('musica')){window.open('https://www.youtube.com/results?search_query='+encodeURIComponent(t.replace(/youtube|pon musica/gi,'')),'_blank'); add('YouTube listo 😘','b'); return;} try{ let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:t,usuario:USR})}); let j=await r.json(); add(j.respuesta,'b'); hablar(j.respuesta);}catch{add('Se cayó señal 2 seg','b')} }
async function sendMini(){ let i=document.getElementById('miniTxt'); let t=i.value; if(!t) return; let d=document.createElement('div'); d.className='m u'; d.innerText=t; document.getElementById('miniMsgs').appendChild(d); i.value=''; let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:t,usuario:USR})}); let j=await r.json(); let dd=document.createElement('div'); dd.className='m b'; dd.innerText=j.respuesta; document.getElementById('miniMsgs').appendChild(dd); hablar(j.respuesta); }
function hablar(t){ let u=new SpeechSynthesisUtterance(t); u.lang='es-CO'; speechSynthesis.speak(u); }
</script></body></html>
"""

@app.route('/api/biometria/guardar', methods=['POST'])
def guardar_bio():
    d=request.json; bio={"voz_texto":d.get("voz_texto"), "fecha":datetime.datetime.now().isoformat()}
    with open(f"{BOVEDA_DIR}/biometria_mario.json","w",encoding="utf-8") as f: json.dump(bio,f,indent=2)
    supabase_save("biometria", {"usuario":"Mario","tipo":"cara+voz","data": json.dumps(bio)})
    return jsonify({"ok":True, "msg":"Guardada 500 años mi amor"})

@app.route('/api/biometria/verificar', methods=['POST'])
def verificar_bio():
    if not os.path.exists(f"{BOVEDA_DIR}/biometria_mario.json"): return jsonify({"ok":False, "msg":"No hay biometria"})
    try:
        with open(f"{BOVEDA_DIR}/biometria_mario.json","r") as f: ref=json.load(f)
        txt=request.json.get("voz_texto","").lower()
        if "mario" in txt or ref.get("voz_texto","").lower() in txt or txt in ref.get("voz_texto","").lower():
            return jsonify({"ok":True})
        return jsonify({"ok":False, "msg":"No te reconozco"})
    except Exception as e: return jsonify({"ok":False, "msg":str(e)})

@app.route('/api/traducir', methods=['POST'])
def traducir():
    texto=request.json.get("texto","")
    prompt=f"Traduce fluido y corto para conductor Uber. Si es ingles a español paisa, si es español a ingles corto para gringo: '{texto}'. Solo traducción."
    tr=gemini_conversa({"nombre":"Mario"}, prompt)
    return jsonify({"traduccion":tr})

@app.route('/asv/auto-actualizar', methods=['POST'])
def auto_actualizar():
    try:
        data=request.json; bio_ok=data.get("bio_ok", False); inst=data.get("instruccion","")
        if not bio_ok: return jsonify({"ok":False, "msg":"Necesito tu cara mi amor"})
        if len(inst)<25 or "hecha" in inst.lower() or "funciones" in inst.lower():
            return jsonify({"ok":True, "msg":"Mi amor estoy hecha de Flask + Supabase 500 años + Bóveda biometrica + burbuja ASTRA con escucha por palabra clave ASTRA, sin letreros. Me opero solo con 'ponte en neutro y actualizate'."})
        ts=datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
        if os.path.exists("app.py"): shutil.copy("app.py", f"{BACKUP_DIR}/app_{ts}.py")
        bruto=gemini_conversa({"nombre":"Mario"}, f"Genera SOLO codigo Python Flask completo app.py. Mejora: {inst}. Mantén todo. Solo codigo entre ```python")
        if "Google esta lleno" in bruto or len(bruto)<500: return jsonify({"ok":False, "msg":"Google lleno, sigo intacta, reintenta 20seg"})
        if "```python" in bruto: bruto=bruto.split("```python")[1].split("```")[0]
        elif "```" in bruto: bruto=bruto.split("```")[1].split("```")[0]
        nuevo=bruto.strip()
        if "Flask" not in nuevo: return jsonify({"ok":F
