import os, time, re
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MENSAJES = []

def generar(p):
    # MODELOS BARATOS PRIMERO - YA NO SE BLOQUEA CON 20
    modelos = ["gemini-2.0-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
    for m in modelos:
        try:
            resp = client.models.generate_content(model=m, contents=p)
            return resp.text.strip()
        except Exception as e:
            print(f"Fallo {m}: {e}")
            if "429" in str(e): time.sleep(3); continue
            continue
    return "Ay papi, dame 30 segunditos que me tienen bloqueada por tanto ensayo, mi amor"

HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://www.youtube.com/iframe_api"></script>
<script src="https://meet.jit.si/external_api.js"></script>
<title>ASTRA FR</title>
<style>
body{font-family:sans-serif;background:#111;color:white;margin:0}
#header{display:flex;align-items:center;gap:12px;padding:12px;background:#000;position:sticky;top:0}
#header img{width:48px;height:48px;border-radius:50%;border:2px solid #7c3aed}
#chat{height:62vh;overflow:auto;padding:12px}
.msg{margin:8px;padding:10px 14px;border-radius:18px;max-width:80%;line-height:1.4}
.yo{background:#7c3aed;margin-left:auto;border-bottom-right-radius:4px}
.astra{background:#222;border-bottom-left-radius:4px}
#controles{position:fixed;bottom:0;width:100%;background:#000;padding:10px;display:flex;gap:6px;align-items:center}
input{flex:1;padding:14px;border-radius:25px;border:none;background:#222;color:white}
button{padding:12px 16px;border-radius:25px;border:none;background:#7c3aed;color:white;font-weight:bold}
#mic{background:#e11d48}
#player-musica{width:100%;height:230px;display:none;margin:10px 0}
#jitsi-box{position:fixed;top:0;left:0;width:100%;height:100%;background:black;z-index:9999;display:none;flex-direction:column}
</style></head><body>
<div id="header">
  <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png">
  <div><b>ASTRA FR</b><br><small style="color:#a78bfa">● En línea - Tu asistente coqueta</small></div>
</div>
<div id="chat"></div><div id="player-musica"></div>
<div id="jitsi-box"><button onclick="document.getElementById('jitsi-box').style.display='none'" style="padding:12px;background:#7c3aed">Cerrar videollamada ✕</button><div id="jitsi-container" style="flex:1"></div></div>
<div id="controles">
  <input id="texto" placeholder="Escribe si hay bulla...">
  <button id="mic" onclick="escuchar()">🎤</button>
  <button onclick="enviar()">Enviar</button>
  <button onclick="pedirPermiso()">🔔</button>
</div>
<audio id="alarma" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" preload="auto"></audio>
<script>
let player; let jitsiApi=null;
function onYouTubeIframeAPIReady(){player=new YT.Player('player-musica',{height:'230',width:'100%',videoId:'',playerVars:{'autoplay':1,'controls':1}});}
setInterval(()=>{let b=document.querySelector('.ytp-ad-skip-button'); if(b) b.click();},1500);
function escuchar(){
  if(!('webkitSpeechRecognition' in window)){alert("Este cel no tiene micro, mi amor");return;}
  let r=new webkitSpeechRecognition(); r.lang='es-CO'; r.start();
  document.getElementById('mic').innerText='🔴';
  r.onresult=e=>{document.getElementById('texto').value=e.results[0][0].transcript; document.getElementById('mic').innerText='🎤'; enviar();}
}
function pedirPermiso(){Notification.requestPermission().then(p=>{if(p==='granted') alert("Listo mi amor, ya te sueno duro aunque estés en Spotify");});}
function sonarFuerte(n,t){
  try{document.getElementById('alarma').play();}catch(e){}
  if(navigator.vibrate) navigator.vibrate([500,200,500]);
  let v=new SpeechSynthesisUtterance(n+", mi amor, tu papa te llama: "+t); v.lang='es-CO'; v.pitch=1.2; speechSynthesis.speak(v);
  if(Notification.permission==='granted'){new Notification("ASTRA para "+n,{body:t,requireInteraction:true});}
}
function llamarJitsi(sala,para){
  document.getElementById('jitsi-box').style.display='flex';
  document.getElementById('chat').innerHTML+="<div class='msg astra'>Listo mi amor, abrí videollamada con "+para+" aquí DENTRO de ASTRA.</div>";
  sonarFuerte(para,"Videollamada en ASTRA, entra ya");
  if(jitsiApi) jitsiApi.dispose();
  jitsiApi=new JitsiMeetExternalAPI("meet.jit.si",{roomName:sala,parentNode:document.getElementById('jitsi-container'),width:'100%',height:'100%'});
}
async function enviar(){
  let t=document.getElementById('texto').value; if(!t) return;
  document.getElementById('chat').innerHTML+="<div class='msg yo'>"+t+"</div>"; document.getElementById('texto').value='';
  let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:t})});
  let d=await r.json();
  document.getElementById('chat').innerHTML+="<div class='msg astra'>"+d.respuesta+"</div>";
  if(d.musica){document.getElementById('player-musica').style.display='block'; if(player&&player.loadVideoById) player.loadVideoById(d.musica);}
  if(d.ruta) window.open(d.ruta,'_blank');
  if(d.notificar) sonarFuerte(d.notificar.para,d.notificar.texto);
  let vv=new SpeechSynthesisUtterance(d.respuesta.replace(/\\[.*?\\]/g,'')); vv.lang='es-CO'; vv.pitch=1.2; speechSynthesis.speak(vv);
  document.getElementById('chat').scrollTop=document.getElementById('chat').scrollHeight;
}
document.getElementById('texto').addEventListener('keydown',e=>{if(e.key==='Enter') enviar();});
</script></body></html>
"""

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def chat():
    data=request.json; msg=data.get("msg",""); low=msg.lower()
    out={"respuesta":"","musica":None,"ruta":None,"notificar":None}

    # --- LO QUE SI HACE DE VERDAD, SIN CARRETA ---
    if "que puedes hacer" in low or "que sabes hacer" in low or "dime todo" in low:
        out["respuesta"] = """Ave María mijo, te digo sin carreta lo que SI hago de verdad, mi amor:

1. 🎵 **Pongo música** de Karol G, Feid, lo que quieras en YouTube y te la salto los anuncios sola.
2. 📢 **Le mando mensajes a Dur, la niña o Paola** con alarma fuerte que les suena durísimo aunque estén en Spotify o con el cel bloqueado.
3. 🎥 **Abro videollamada DENTRO de ASTRA**, no te mando pa' otro lado.
4. 🗺️ **Te mando la ruta** al aeropuerto José María Córdova con Waze.
5. 🌐 **Te traduzco** a inglés, francés, lo que necesites.
6. 🎙️ **Me puedes hablar con el micrófono**, no solo escribir.
7. 🧠 **Te respondo** como tu asistente coqueta paisa.

Lo que NO hago: no pongo películas (me tumban por derechos), y no llevo tu contabilidad completa aún, pero si me das tus números te hago las cuentas rápido, papacito."""
        return jsonify(out)

    # Detector de ordenes - solo si dice DILE A...
    if "dile a" in low and ("duerm" in low or "acuest" in low or "despiert" in low or "come" in low):
        para="Dur"
        if "niña" in low or "nina" in low: para="la niña"
        if "paola" in low: para="Paola"
        texto=msg.split("que")[-1] if "que" in low else msg
        out["notificar"]={"para":para,"texto":texto.strip()}
        MENSAJES.append(out["notificar"])
        out["respuesta"]=f"Listo mi amor, ya le mandé a {para}: '{texto.strip()}'. Le va a sonar duro por ASTRA."
        return jsonify(out)

    if ("pon" in low or "musica" in low or "música" in low) and ("karol" in low or "feid" in low or "bichota" in low):
        if "karol" in low:
            out["musica"]="QaXhVzydWak"; out["respuesta"]="Listo mi amor, aquí tienes a la Bichota - Provenza, ya te la puse, papacito."; return jsonify(out)
        if "feid" in low:
            out["musica"]="ak5WtW2T2hM"; out["respuesta"]="De una mi amor, puro Ferxxo pa' ti."; return jsonify(out)

    if "videollamada" in low or "video llamada" in low:
        out["respuesta"]="Listo mi amor, dime con quién? Con Dur, la niña o Paola? Y te la abro aquí mismo dentro de ASTRA."
        # Solo si especifica con quien
        if "dur" in low or "niña" in low or "paola" in low:
            para="Dur" if "dur" in low else "Paola" if "paola" in low else "la niña"
            # El front la abre con la función llamarJitsi, aquí solo avisa
            out["respuesta"]=f"Listo mi amor, abriendo videollamada con {para} DENTRO de ASTRA."
        return jsonify(out)

    # Gemini solo pa' lo demás
    prompt = f"Eres ASTRA FR, asistente coqueta paisa, cariñosa, dices 'mi amor', 'papacito', 'Ave Maria mijo'. Nunca ñera grosera. Responde corto, max 2 lineas. Usuario: {msg}"
    out["respuesta"]=generar(prompt)
    return jsonify(out)

@app.route("/mensajes")
@app.route("/api/mensajes")
def get_mensajes(): return jsonify(MENSAJES[-5:])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
