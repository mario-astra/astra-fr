import os, time, json
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MENSAJES = []

def generar(p):
    modelos = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.0-flash-lite"]
    for modelo in modelos:
        try:
            resp = client.models.generate_content(model=modelo, contents=p)
            return resp.text.strip()
        except Exception as e:
            print(f"Fallo {modelo}: {e}")
            if "429" in str(e):
                time.sleep(3)
                continue
            continue
    return "Socio deme 1 minutico que Google me bloqueo por tantas pruebas, vuelva a intentar en 30 seg"

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://www.youtube.com/iframe_api"></script>
<script src="https://meet.jit.si/external_api.js"></script>
<title>ASTRA FR</title>
<style>
body{font-family:sans-serif;background:#111;color:white;margin:0}
#chat{height:70vh;overflow:auto;padding:10px}
.msg{margin:8px;padding:10px;border-radius:12px;max-width:80%}
.yo{background:#7c3aed;margin-left:auto}
.astra{background:#222}
#controles{position:fixed;bottom:0;width:100%;background:#000;padding:10px;display:flex;gap:5px}
input{flex:1;padding:12px;border-radius:20px;border:none}
button{padding:12px;border-radius:20px;border:none;background:#7c3aed;color:white}
#player-musica{width:100%;height:220px;display:none;margin-top:10px}
#jitsi-box{position:fixed;top:0;left:0;width:100%;height:100%;background:black;z-index:9999;display:none;flex-direction:column}
#jitsi-container{flex:1}
#minimizar{padding:10px;background:#7c3aed}
#astra-bolita{position:fixed;bottom:80px;right:10px;background:#7c3aed;padding:12px;border-radius:50%;z-index:10000;display:none;cursor:pointer}
</style>
</head>
<body>
<div id="chat"></div>
<div id="player-musica"></div>
<div id="jitsi-box">
  <button id="minimizar" onclick="minimizarJitsi()">Minimizar ASTRA</button>
  <div id="jitsi-container"></div>
</div>
<div id="astra-bolita" onclick="maximizarJitsi()">ASTRA</div>
<div id="controles">
  <input id="texto" placeholder="Escribe si hay bulla...">
  <button onclick="enviar()">Enviar</button>
  <button onclick="pedirPermiso()">🔔</button>
</div>
<audio id="alarma" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" preload="auto"></audio>
<script>
let player;
let jitsiApi = null;
function onYouTubeIframeAPIReady(){
  player = new YT.Player('player-musica', {
    height:'220', width:'100%', videoId:'',
    playerVars:{'autoplay':1,'controls':1},
    events:{'onStateChange': onPlayerState}
  });
}
function onPlayerState(e){
  let btn = document.querySelector('.ytp-ad-skip-button,.ytp-ad-overlay-close-button');
  if(btn) btn.click();
}
setInterval(()=>{
  let btn = document.querySelector('.ytp-ad-skip-button,.ytp-skip-button,.ytp-ad-overlay-close-button');
  if(btn) btn.click();
}, 1500);
function pedirPermiso(){
  Notification.requestPermission().then(p=>{
    if(p==='granted'){ alert("Listo socio, ya suena duro aunque esten en Spotify"); }
  });
}
function sonarFuerte(nombre, texto){
  try{ document.getElementById('alarma').play(); }catch(e){}
  if(navigator.vibrate) navigator.vibrate([500,200,500,200,1000]);
  let voz = new SpeechSynthesisUtterance(nombre + ", su papa lo esta llamando: " + texto);
  voz.lang='es-CO'; speechSynthesis.speak(voz);
  if(Notification.permission==='granted'){
    new Notification("ASTRA - Para " + nombre, {body: texto, requireInteraction: true});
  }
}
function llamarJitsi(sala, para){
  document.getElementById('jitsi-box').style.display='flex';
  document.getElementById('chat').innerHTML+="<div class='msg astra'>Listo socio, abri videollamada con "+para+" DENTRO de ASTRA.</div>";
  sonarFuerte(para, "Su papa pide videollamada, entren a ASTRA YA");
  if(jitsiApi) jitsiApi.dispose();
  jitsiApi = new JitsiMeetExternalAPI("meet.jit.si", {roomName: sala, parentNode: document.getElementById('jitsi-container'), width:'100%', height:'100%'});
  jitsiApi.addListener('videoConferenceLeft', ()=>{ minimizarJitsi(); });
}
function minimizarJitsi(){ document.getElementById('jitsi-box').style.display='none'; document.getElementById('astra-bolita').style.display='block'; }
function maximizarJitsi(){ document.getElementById('jitsi-box').style.display='flex'; document.getElementById('astra-bolita').style.display='none'; }
async function enviar(){
  let t = document.getElementById('texto').value;
  if(!t) return;
  document.getElementById('chat').innerHTML+="<div class='msg yo'>"+t+"</div>";
  document.getElementById('texto').value='';
  let txt = t.toLowerCase();
  if(txt.includes("video llamada") || txt.includes("videollamada")){
    let para = "todos";
    if(txt.includes("dur")) para="Dur";
    else if(txt.includes("niña") || txt.includes("nina")) para="la nina";
    else if(txt.includes("paola")) para="Paola";
    llamarJitsi("astra-fr-familia-2026", para);
    return;
  }
  try{
    let r = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:t})});
    let data = await r.json();
    document.getElementById('chat').innerHTML+="<div class='msg astra'>"+data.respuesta+"</div>";
    if(data.musica){
      document.getElementById('player-musica').style.display='block';
      if(player && player.loadVideoById) player.loadVideoById(data.musica);
    }
    if(data.ruta){ window.open(data.ruta, '_blank'); }
    if(data.notificar){ sonarFuerte(data.notificar.para, data.notificar.texto); }
    let v = new SpeechSynthesisUtterance(data.respuesta.replace(/\\[.*?\\]/g,''));
    v.lang='es-CO'; speechSynthesis.speak(v);
  }catch(e){ document.getElementById('chat').innerHTML+="<div class='msg astra'>Socio se me cayo 1 seg, dele enviar de nuevo</div>"; }
}
setInterval(async()=>{
  try{
    let r = await fetch('/mensajes');
    let msgs = await r.json();
  }catch(e){}
}, 5000);
document.getElementById('texto').addEventListener('keydown', e=>{ if(e.key==='Enter') enviar(); });
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/sw.js")
def sw():
    return """self.addEventListener('push', e=>{ self.registration.showNotification('ASTRA', {body:e.data.text(), requireInteraction:true}); });""", 200, {'Content-Type':'application/javascript'}

# --- AQUI ESTABA EL ERROR 404 DE LA FOTO, AHORA ESCUCHA EN LAS 2 RUTAS ---
@app.route("/chat", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data.get("msg","")
    prompt = f"""
    Eres ASTRA FR, asistente paisa de Medellin, hablas bacano.
    Usuario dice: {msg}
    Responde corto, paisa.
    Si pide musica, responde con el nombre y pon al final [MUSICA: id_youtube]. Usa ids reales Karol G, Feid. Ej: Karol G Poblado Remix es QaXhVzydWak
    Si pide ruta al aeropuerto Jose Maria Cordova (MDE), pon al final [RUTA: https://waze.com/ul?q=Aeropuerto%20Jose%20Maria%20Cordova]
    Si dice que le mande mensaje a Dur, la nina o Paola, pon al final [NOTIFICAR: Dur|texto del mensaje]
    Si pide videollamada, di que ya la abriste dentro de ASTRA.
    """
    respuesta = generar(prompt)
    out = {"respuesta": respuesta, "musica": None, "ruta": None, "notificar": None}
    if "[MUSICA:" in respuesta:
        try:
            id_yt = respuesta.split("[MUSICA:")[1].split("]")[0].strip()
            if "karol" in msg.lower() or "poblado" in msg.lower(): id_yt = "QaXhVzydWak"
            if "feid" in msg.lower(): id_yt = "ak5WtW2T2hM"
            out["musica"] = id_yt
            out["respuesta"] = respuesta.split("[MUSICA:")[0]
        except: pass
    if "[RUTA:" in respuesta:
        try:
            out["ruta"] = respuesta.split("[RUTA:")[1].split("]")[0].strip()
            out["respuesta"] = respuesta.split("[RUTA:")[0]
        except: pass
    if "[NOTIFICAR:" in respuesta:
        try:
            contenido = respuesta.split("[NOTIFICAR:")[1].split("]")[0]
            para, texto = contenido.split("|",1)
            out["notificar"] = {"para": para.strip(), "texto": texto.strip()}
            MENSAJES.append({"para": para.strip(), "texto": texto.strip()})
            out["respuesta"] = respuesta.split("[NOTIFICAR:")[0] + f" Listo, le mande por ASTRA a {para}: {texto}. Le suena duro, no por WhatsApp."
        except: pass
    return jsonify(out)

@app.route("/mensajes")
@app.route("/api/mensajes")
def get_mensajes():
    return jsonify(MENSAJES[-5:])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
