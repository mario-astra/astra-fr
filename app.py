import os, time
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MENSAJES = []

def generar(p):
    modelos = ["gemini-2.0-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
    for m in modelos:
        try:
            return client.models.generate_content(model=m, contents=p).text.strip()
        except:
            time.sleep(1); continue
    return "Ay mi amor dame 30 seg"

HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://www.youtube.com/iframe_api"></script>
<script src="https://meet.jit.si/external_api.js"></script>
<title>ASTRA FR</title>
<style>
body{font-family:sans-serif;background:#0f0f0f;color:white;margin:0}
#login{position:fixed;top:0;left:0;width:100%;height:100%;background:#000;z-index:999999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:15px}
#login input{padding:15px;border-radius:25px;border:none;width:200px;text-align:center;font-size:18px}
#header{display:flex;align-items:center;gap:12px;padding:12px;background:#000;border-bottom:1px solid #222}
#header img{width:48px;height:48px;border-radius:50%;border:2px solid #7c3aed}
#chat{height:55vh;overflow:auto;padding:12px}
.msg{margin:8px;padding:10px 14px;border-radius:18px;max-width:80%;line-height:1.4}
.yo{background:#7c3aed;margin-left:auto}
.astra{background:#222}
#player-musica{width:100%;height:220px;display:none}
#jitsi-box{position:fixed;top:0;left:0;width:100%;height:100%;background:black;z-index:9999;display:none;flex-direction:column}
#controles{position:fixed;bottom:0;width:100%;background:#000;padding:10px;display:flex;gap:6px}
#controles input{flex:1;padding:14px;border-radius:25px;border:none;background:#222;color:white}
button{padding:12px 16px;border-radius:25px;border:none;background:#7c3aed;color:white;font-weight:bold}
#mic{background:#e11d48}
</style></head><body>
<div id="login">
  <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" style="width:80px;height:80px;border-radius:50%;border:3px solid #7c3aed">
  <h2>ASTRA FR</h2>
  <p>Ingresa tu código, mi amor</p>
  <input id="codigo" placeholder="Código">
  <button onclick="entrar()">Entrar</button>
  <small>FR2026 - DUR2026 - NINA2026 - PAOLA2026</small>
</div>
<div id="header">
  <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png">
  <div><b>ASTRA FR</b><br><small id="quien" style="color:#a78bfa">● En línea</small></div>
</div>
<div id="chat"></div>
<div id="player-musica"></div>
<div id="jitsi-box"><button onclick="document.getElementById('jitsi-box').style.display='none'" style="padding:12px;background:#7c3aed">Cerrar ✕</button><div id="jitsi-container" style="flex:1"></div></div>
<div id="controles">
  <input id="texto" placeholder="Escribe si hay bulla...">
  <button id="mic" onclick="escuchar()">🎤</button>
  <button onclick="enviar()">Enviar</button>
  <button onclick="pedirPermiso()">🔔</button>
</div>
<audio id="alarma" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>
<script>
let player; let jitsiApi=null; let usuario="Papa";
function entrar(){
  let c=document.getElementById('codigo').value.toUpperCase();
  let mapa={"FR2208":"Papa","DUR2011":"Dur","NINA2015":"La niña","PAOLA2345":"Paola"};
  if(!mapa[c]){alert("Código malo, mi amor"); return;}
  usuario=mapa[c];
  document.getElementById('quien').innerText="● En línea - "+usuario;
  document.getElementById('login').style.display='none';
  localStorage.setItem('astra_user', usuario);
}
let guardado=localStorage.getItem('astra_user');
if(guardado){usuario=guardado; document.getElementById('login').style.display='none'; document.getElementById('quien').innerText="● En línea - "+usuario;}
function onYouTubeIframeAPIReady(){
  player=new YT.Player('player-musica',{height:'220',width:'100%',videoId:'',playerVars:{'autoplay':1,'controls':1},
    events:{'onError':(e)=>{let id=player.getVideoData().video_id; if(id) window.open('https://www.youtube.com/watch?v='+id,'_blank');}}
  });
}
setInterval(()=>{let b=document.querySelector('.ytp-ad-skip-button'); if(b) b.click();},1500);
function escuchar(){
  let SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert("Sin micro");return;}
  let r=new SR(); r.lang='es-CO'; r.start();
  document.getElementById('mic').innerText='🔴';
  r.onresult=e=>{document.getElementById('texto').value=e.results[0][0].transcript; document.getElementById('mic').innerText='🎤'; enviar();}
}
function pedirPermiso(){Notification.requestPermission();}
function sonarFuerte(n,t){
  try{document.getElementById('alarma').play();}catch(e){}
  if(navigator.vibrate) navigator.vibrate([500,200,500]);
  let v=new SpeechSynthesisUtterance(n+", mi amor, te llama "+usuario+": "+t); v.lang='es-CO'; v.pitch=1.2; speechSynthesis.speak(v);
  if(Notification.permission==='granted'){new Notification("ASTRA para "+n,{body:t,requireInteraction:true});}
}
function llamarJitsi(sala,para){
  document.getElementById('jitsi-box').style.display='flex';
  document.getElementById('chat').innerHTML+="<div class='msg astra'>Listo mi amor, videollamada con "+para+" aquí dentro.</div>";
  sonarFuerte(para,"Videollamada en ASTRA");
  if(jitsiApi) jitsiApi.dispose();
  jitsiApi=new JitsiMeetExternalAPI("meet.jit.si",{roomName:sala,parentNode:document.getElementById('jitsi-container'),width:'100%',height:'100%'});
}
async function enviar(){
  let t=document.getElementById('texto').value; if(!t) return;
  document.getElementById('chat').innerHTML+="<div class='msg yo'>"+t+"</div>"; document.getElementById('texto').value='';
  let low=t.toLowerCase();
  if(low.includes("videollamada")||low.includes("video llamada")){
    let para="todos"; if(low.includes("dur")) para="Dur"; if(low.includes("paola")) para="Paola"; llamarJitsi("astra-fr-familia-2026",para); return;
  }
  let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:t, user:usuario})});
  let d=await r.json();
  document.getElementById('chat').innerHTML+="<div class='msg astra'>"+d.respuesta+"</div>";
  if(d.musica){document.getElementById('player-musica').style.display='block'; player.loadVideoById(d.musica);}
  if(d.ruta){window.open(d.ruta,'_blank');}
  if(d.notificar){sonarFuerte(d.notificar.para,d.notificar.texto);}
  let vv=new SpeechSynthesisUtterance(d.respuesta.replace(/\\[.*?\\]/g,'')); vv.lang='es-CO'; vv.pitch=1.2; speechSynthesis.speak(vv);
  document.getElementById('chat').scrollTop=document.getElementById('chat').scrollHeight;
}
</script></body></html>
"""

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data=request.json; msg=data.get("msg",""); low=msg.lower(); user=data.get("user","Papa")
    out={"respuesta":"","musica":None,"ruta":None,"notificar":None}

    if "dile a" in low:
        para="Dur" if "dur" in low else "Paola" if "paola" in low else "la niña" if "niña" in low or "nina" in low else "Dur"
        texto=msg.split("que")[-1] if "que" in low else msg
        out["notificar"]={"para":para,"texto":texto.strip()}
        MENSAJES.append({"para":para,"texto":texto.strip(),"de":user})
        out["respuesta"]=f"Listo mi amor, ya le mandé a {para} de parte de {user}: '{texto.strip()}'"
        return jsonify(out)

    if "pon" in low or "musica" in low or "música" in low:
        if "karol" in low:
            out["musica"]="ca48oMV134Y"; out["respuesta"]="Listo mi amor, aquí tienes a la Bichota - Provenza, ya te la puse papacito"; out["ruta"]="https://www.youtube.com/watch?v=ca48oMV134Y"; return jsonify(out)
        if "feid" in low:
            out["musica"]="FzG4uDgje3M"; out["respuesta"]="De una mi amor, puro Ferxxo pa' ti"; return jsonify(out)

    if "ruta" in low or "waze" in low:
        dest="Olimpicas Medellin" if "olimpica" in low else "Aeropuerto Jose Maria Cordova" if "aeropuerto" in low else "Medellin"
        out["ruta"]=f"https://waze.com/ul?q={dest.replace(' ','%20')}&navigate=yes"
        out["respuesta"]=f"Ave María mijo, ya te abrí Waze hacia {dest}, papacito"
        return jsonify(out)

    if "que puedes hacer" in low:
        out["respuesta"]=f"Ave María {user}, sin carreta: Pongo música, abro Waze, le mando alarma a Dur/niña/Paola, videollamada aquí dentro y hablo con micro, mi amor"
        return jsonify(out)

    out["respuesta"]=generar(f"Eres ASTRA FR coqueta paisa, cariñosa, dices mi amor papacito Ave Maria mijo. Usuario es {user}. Mensaje: {msg}. Responde corto max 2 lineas.")
    return jsonify(out)

@app.route("/mensajes")
def get_mensajes(): return jsonify(MENSAJES[-5:])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
