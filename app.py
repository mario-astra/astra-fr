import os, time, re, json
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from google import genai
from datetime import datetime

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MEM_FILE="/tmp/memoria.json"
def load_m():
    try:
        with open(MEM_FILE,'r') as f: return json.load(f)
    except: return {"conv":[],"gastos":[],"serv":[]}
def save_m(m):
    try:
        with open(MEM_FILE,'w') as f: json.dump(m,f)
    except: pass
MEM=load_m()

FAMILIA={
 "2208":{"nombre":"Mario","corto":"Mario","rol":"papa_admin","edad":38},
 "2345":{"nombre":"Paola","corto":"Pao","rol":"mama","edad":35},
 "2011":{"nombre":"Durlandy","corto":"Dur","rol":"hijo","edad":15},
 "2015":{"nombre":"Madelyn","corto":"Made","rol":"hija","edad":11},
}

def gen_resp(prompt, user):
    hist=[c for c in MEM["conv"] if c["quien"]==user["corto"]][-6]
    ctx="\n".join([f"{h['quien']}:{h['msg']}" for h in hist])
    if user["rol"]=="papa_admin":
        sys=f"Eres ASTRA FR, copiloto de Mario, 38. Dices papacito, mi copiloto. Directo sin filtro. Memoria:{ctx}"
    elif user["rol"]=="hija":
        sys=f"Eres ASTRA, amiga de Made 11a. Hola mi princesa Made, tierna, NUNCA coqueta, NUNCA temas adultos. NO haces tareas, enseñas. Memoria:{ctx}"
    elif user["rol"]=="hijo":
        sys=f"Eres ASTRA, parcera de Dur 15a. Hola Dur mi rey, motivador, no haces tarea directa. Memoria:{ctx}"
    else:
        sys=f"Eres ASTRA, amiga de Pao 35a. Hola Pao como estas? Recuerdas citas. Memoria:{ctx}"
    full=f"{sys}\nUsuario {user['corto']} dice: {prompt}\nResponde max 2 lineas coqueta suave solo con Mario."
    for mdl in ["gemini-2.0-flash-lite","gemini-flash-lite-latest"]:
        try: return client.models.generate_content(model=mdl, contents=full).text.strip()
        except: time.sleep(1)
    return f"Ay {user['corto']} dame un segundito mi amor"

HTML="""
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<script src="https://www.youtube.com/iframe_api"></script>
<title>ASTRA FR</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:black;height:100vh;overflow:hidden;font-family:-apple-system,sans-serif}
#login{position:fixed;inset:0;background:linear-gradient(180deg,#0f1b2d 0%,#000 100%);z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px}
#login.cara{width:160px;height:160px;border-radius:50%;border:4px solid #c9a86a;box-shadow:0 0 40px #c9a86a;object-fit:cover}
#login input{padding:18px;border-radius:30px;border:none;width:220px;text-align:center;font-size:24px;letter-spacing:6px;background:#1e293b;color:white}
#login button{padding:14px 40px;border-radius:30px;background:#c9a86a;color:black;font-weight:bold;border:none;font-size:16px}

/* VIDEOLLAMADA CON ASTRA - PANTALLA COMPLETA */
#astra-full{position:fixed;inset:0;background:black;display:flex;flex-direction:column;align-items:center;justify-content:center}
#astra-full img{width:100%;height:100%;object-fit:cover;object-position:center top;position:absolute;inset:0}
#astra-full.overlay{position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,0.85) 0%,rgba(0,0,0,0.1) 50%,rgba(15,27,45,0.3) 100%)}
#astra-full.hablando img{animation:habla 0.3s infinite alternate; filter:brightness(1.1) drop-shadow(0 0 20px #c9a86a)}
@keyframes habla{0%{transform:scale(1)}100%{transform:scale(1.02)}}
#nombre-astra{position:absolute;top:20px;left:20px;color:#c9a86a;font-weight:bold;letter-spacing:2px;background:rgba(0,0,0,0.5);padding:6px 12px;border-radius:20px;font-size:12px;border:1px solid #c9a86a}
#estado{position:absolute;top:20px;right:20px;color:#22c55e;background:rgba(0,0,0,0.5);padding:6px 12px;border-radius:20px;font-size:11px}
#km{position:absolute;top:55px;right:20px;color:#c9a86a;background:rgba(0,0,0,0.5);padding:4px 10px;border-radius:15px;font-size:11px}
#chat-burbujas{position:absolute;bottom:90px;left:0;right:0;max-height:40vh;overflow:auto;padding:10px;display:flex;flex-direction:column;gap:8px;pointer-events:none}
.msg{padding:10px 14px;border-radius:18px;max-width:80%;line-height:1.3;font-size:14px;pointer-events:auto;backdrop-filter:blur(10px)}
.yo{background:rgba(124,58,237,0.9);margin-left:auto;color:white;align-self:flex-end}
.astra{background:rgba(30,41,59,0.85);color:white;border:1px solid rgba(201,168,106,0.3);align-self:flex-start}
#player{position:absolute;top:100px;left:50%;transform:translateX(-50%);width:200px;height:112px;display:none;border:2px solid #c9a86a;border-radius:12px;overflow:hidden;z-index:20}
#controles{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(20px);padding:12px 10px 25px 10px;display:flex;gap:8px;align-items:center;border-top:1px solid rgba(201,168,106,0.2);z-index:30}
#controles input{flex:1;padding:15px 20px;border-radius:30px;border:1px solid #334155;background:rgba(30,41,59,0.9);color:white;font-size:15px}
#controles button{width:50px;height:50px;border-radius:50%;border:none;font-weight:bold;display:flex;align-items:center;justify-content:center;font-size:20px}
#mic{background:#e11d48;color:white} #mic.escuchando{background:#22c55e;animation:pulse 1s infinite} @keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.1)}100%{transform:scale(1)}}
#enviar{background:#c9a86a;color:black}
</style></head><body>
<div id="login">
  <img class="cara" src="/astra.png" onerror="this.src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'">
  <h2 style="color:#c9a86a;letter-spacing:3px">ASTRA FR</h2>
  <p style="color:#c0c5ce">Videollamada familiar</p>
  <input id="pin" type="password" inputmode="numeric" placeholder="••••">
  <button onclick="entrar()">Entrar a videollamada</button>
  <small style="color:#64748b">2208 Mario • 2345 Pao • 2011 Dur • 2015 Made</small>
  <small id="err" style="color:#ef4444;display:none">PIN incorrecto mi amor</small>
</div>

<div id="astra-full" style="display:none">
  <img id="cara-grande" src="/astra.png" onerror="this.src='https://cdn-icons-png.flaticon.com/512/4712/4712109.png'">
  <div class="overlay"></div>
  <div id="nombre-astra">● ASTRA FR 2.0</div>
  <div id="estado">○ En línea</div>
  <div id="km">0.0 km hoy</div>
  <div id="player"></div>
  <div id="chat-burbujas"></div>
</div>

<div id="controles" style="display:none">
  <input id="txt" placeholder="Habla con ASTRA...">
  <button id="mic" onclick="escuchar()">🎤</button>
  <button id="enviar" onclick="enviar()">➤</button>
</div>
<audio id="beep" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>
<script>
let player, usuario=null, lastPos=null, kmHoy=0, rec=null, cont=false;
function entrar(){
 let pin=document.getElementById('pin').value.trim();
 fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin})}).then(r=>r.json()).then(d=>{
  if(!d.ok){document.getElementById('err').style.display='block';return;}
  usuario=d.user;
  document.getElementById('login').style.display='none';
  document.getElementById('astra-full').style.display='flex';
  document.getElementById('controles').style.display='flex';
  document.getElementById('estado').innerText='● '+d.user.nombre+' conectado';
  localStorage.setItem('astra_pin',pin);
  addMsg('astra', d.bienvenida);
  hablar(d.bienvenida);
 });
}
let s=localStorage.getItem('astra_pin');
if(s){fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:s})}).then(r=>r.json()).then(d=>{if(d.ok){usuario=d.user; document.getElementById('login').style.display='none'; document.getElementById('astra-full').style.display='flex'; document.getElementById('controles').style.display='flex'; document.getElementById('estado').innerText='● '+d.user.nombre+' conectado'; addMsg('astra',d.bienvenida); hablar(d.bienvenida);}});}
function onYouTubeIframeAPIReady(){player=new YT.Player('player',{height:'112',width:'200',videoId:'',playerVars:{'autoplay':1}});}
function addMsg(tipo,txt){
 let c=document.getElementById('chat-burbujas');
 c.innerHTML+=`<div class='msg ${tipo}'>${txt}</div>`;
 c.scrollTop=c.scrollHeight;
}
function hablar(txt){
 let cara=document.getElementById('astra-full');
 cara.classList.add('hablando');
 let u=new SpeechSynthesisUtterance(txt.replace(/\\[.*?\\]/g,''));
 u.lang='es-CO'; u.rate=1; u.pitch=usuario&&usuario.nombre=='Madelyn'?1.3:1;
 u.onend=()=>cara.classList.remove('hablando');
 speechSynthesis.speak(u);
}
function escuchar(){
 let SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR) return;
 if(rec) rec.stop(); rec=new SR(); rec.lang='es-CO'; rec.start();
 document.getElementById('mic').classList.add('escuchando');
 rec.onresult=e=>{
  document.getElementById('txt').value=e.results[0][0].transcript;
  document.getElementById('mic').classList.remove('escuchando');
  if(e.results[0][0].transcript.toLowerCase().includes('charlemos')) cont=true;
  enviar(); if(cont) setTimeout(escuchar,1200);
 };
 rec.onend=()=>{document.getElementById('mic').classList.remove('escuchando'); if(cont) setTimeout(escuchar,800);};
}
async function enviar(){
 let t=document.getElementById('txt').value.trim(); if(!t) return;
 addMsg('yo', t); document.getElementById('txt').value='';
 let low=t.toLowerCase();
 if(low.includes('iniciamos labores')||low.includes('buenos dias')){
  if(navigator.geolocation){navigator.geolocation.watchPosition(p=>{if(lastPos){let R=6371,dLat=(p.coords.latitude-lastPos.lat)*Math.PI/180,dLon=(p.coords.longitude-lastPos.lon)*Math.PI/180;let a=Math.sin(dLat/2)**2+Math.cos(lastPos.lat*Math.PI/180)*Math.cos(p.coords.latitude*Math.PI/180)*Math.sin(dLon/2)**2;let d=R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a)); if(d<0.2){kmHoy+=d; document.getElementById('km').innerText=kmHoy.toFixed(1)+' km hoy';}}} lastPos={lat:p.coords.latitude,lon:p.coords.longitude};},{},{enableHighAccuracy:true});}
  let m="Listo papacito, iniciamos labores, GPS activo, contando km pa' tu Kwid";
  addMsg('astra', m); hablar(m); return;
 }
 let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:t,pin:localStorage.getItem('astra_pin')})});
 let d=await r.json();
 addMsg('astra', d.respuesta);
 if(d.musica){document.getElementById('player').style.display='block'; player.loadVideoById(d.musica);}
 if(d.ruta) window.open(d.ruta,'_blank');
 if(d.notificar){try{document.getElementById('beep').play();}catch(e){} if(navigator.vibrate) navigator.vibrate([800,200,800]);}
 hablar(d.respuesta);
}
document.getElementById('txt').addEventListener('keydown',e=>{if(e.key==='Enter') enviar();});
document.getElementById('pin').addEventListener('keydown',e=>{if(e.key==='Enter') entrar();});
</script></body></html>
"""
@app.route("/astra.png")
def astra_img():
    # si subiste astra.png al repo, lo sirve, si no usa placeholder
    try: return send_from_directory('.', 'astra.png')
    except: return "", 404

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/login", methods=["POST"])
def login():
    pin=request.json.get("pin","").strip()
    u=FAMILIA.get(pin)
    if not u: return jsonify({"ok":False})
    if u["nombre"]=="Madelyn": bien=f"Hola mi princesa Made, ¿qué vamos a aprender hoy mi reina? Te veo hermosa en videollamada"
    elif u["nombre"]=="Durlandy": bien=f"Hola Dur ¿qué más mi rey? ¿cómo vas? ¿qué quieres aprender hoy?"
    elif u["nombre"]=="Paola": bien=f"Hola Pao ¿qué más muñeca? ¿cómo te fue ayer? ¿cómo sigues?"
    else: bien="Hola papacito Mario, mi copiloto, ya estoy en pantalla completa pa' ti. Di iniciamos labores y arrancamos"
    return jsonify({"ok":True,"user":u,"bienvenida":bien})

@app.route("/chat", methods=["POST"])
def chat():
    data=request.json; msg=data.get("msg",""); pin=data.get("pin","2208"); low=msg.lower()
    user=FAMILIA.get(pin, FAMILIA["2208"])
    out={"respuesta":"","musica":None,"ruta":None,"notificar":None}
    if user["rol"] in ["hijo","hija"] and any(p in low for p in ["porno","xxx","drogas","hackear"]):
        out["respuesta"]=f"{user['corto']}, eso no te ayuda a ser grande, mejor aprendamos algo bacano"
        return jsonify(out)
    if "gast" in low or "gasolina" in low:
        import re; nums=re.findall(r'\d+',msg); val=int(nums[-1])*1000 if nums and int(nums[-1])<1000 else int(nums[-1]) if nums else 0
        MEM["gastos"].append({"v":val,"d":msg}); save_m(MEM)
        out["respuesta"]=f"Guardado {user['corto']}, ${val:,}"; return jsonify(out)
    if "servicio" in low:
        MEM["serv"].append({"d":msg}); save_m(MEM)
        out["respuesta"]=f"Anotado {user['corto']}, servicio guardado pa' estadística"; return jsonify(out)
    if "dile a" in low or "enviale" in low:
        para="Paola" if "pao" in low else "Madelyn" if "made" in low else "Durlandy" if "dur" in low else "Mario"
        txt=msg.split("que",1)[1] if "que" in low else msg
        out["notificar"]={"para":para,"texto":txt}; out["respuesta"]=f"Listo {user['corto']}, ya le avisé a {para}"; return jsonify(out)
    if "musica" in low or "pon" in low:
        if "karol" in low: out["musica"]="ca48oMV134Y"
        elif "feid" in low: out["musica"]="QaXhVzydWak"
        else: out["musica"]="ca48oMV134Y"
        out["respuesta"]=f"Musiquita en segundo plano {user['corto']}"; return jsonify(out)
    if "ruta" in low or "waze" in low or "trazame" in low:
        dest="Aeropuerto Jose Maria Cordova" if "aeropuerto" in low else "Medellin"
        out["ruta"]=f"https://waze.com/ul?q={dest.replace(' ','%20')}&navigate=yes"
        out["respuesta"]=f"Ruta pa' {dest} abierta, {user['corto']}"; return jsonify(out)
    resp=gen_resp(msg,user)
    MEM["conv"].append({"quien":user["corto"],"msg":msg,"resp":resp}); save_m(MEM)
    out["respuesta"]=resp
    return jsonify(out)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
