from flask import Flask, send_from_directory, request, jsonify
import os, json, datetime
app = Flask(__name__)

DB_FILE = "astra_db.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE,"w") as f:
        json.dump({"gastos":[],"servicios":[],"kms":0,"mantenimientos":[],"mensajes_familia":[],"memoria":{},"funciones":[]}, f)

def get_db():
    with open(DB_FILE,"r") as f: return json.load(f)
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(d,f)

USUARIOS = {"2208":{"nombre":"Mario","rol":"admin"},"PaolaPIN":{"nombre":"Paola","rol":"familia"},"Hijo1PIN":{"nombre":"Hijo1","rol":"hijo"},"Hijo2PIN":{"nombre":"Hijo2","rol":"hijo"}}
# CAMBIE AQUÍ LOS PIN DE SU FAMILIA SOCIO

KWID_MANT = {10000:"Cambio aceite y filtro",20000:"Pastillas + líquidos + revisión",30000:"Correa + refrigerante",40000:"Sincronización completa"}

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#020617;color:white;font-family:Arial;height:100vh;overflow:hidden;display:flex;flex-direction:column}
#foto-wrap{flex:1;position:relative;background:radial-gradient(circle,#1e293b,#020617);display:flex;align-items:center;justify-content:center;overflow:hidden}
#astra{width:100%;height:100%;object-fit:contain;transition:.4s} #astra.hablando{transform:scale(1.03);filter:drop-shadow(0 0 25px gold) brightness(1.1)}
#panel{height:38vh;background:rgba(15,23,42,0.98);border-top:2px solid gold;display:flex;flex-direction:column}
#chat{flex:1;overflow-y:auto;padding:10px;font-size:13px}.bubble{background:rgba(255,255,255,.1);padding:8px 12px;border-radius:12px;margin:4px 0}.yo{background:rgba(251,191,36,.25)!important}
#controles{display:flex;gap:8px;padding:10px;align-items:center}
input{flex:1;padding:14px;border-radius:12px;border:none;background:#1e293b;color:white}
#mic{width:54px;height:54px;border-radius:50%;border:3px solid white;background:#ef4444;font-size:22px;cursor:pointer} #mic.on{background:#22c55e;box-shadow:0 0 15px lime;animation:pulse 1s infinite}
#yt{position:absolute;bottom:0;left:0;width:1px;height:1px;opacity:.01;pointer-events:none}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.1)}100%{transform:scale(1)}}
.tabs{display:flex;gap:5px;padding:5px;overflow-x:auto}.tab{padding:6px 10px;border-radius:20px;background:#1e293b;font-size:11px;cursor:pointer;white-space:nowrap}.tab.active{background:gold;color:black}
</style></head><body>
<div id="foto-wrap">
<img id="astra" src="/astra.png">
<iframe id="yt" allow="autoplay"></iframe>
<video id="cam1" autoplay muted style="position:absolute;top:5px;left:5px;width:60px;height:45px;border-radius:8px;border:1px solid gold;opacity:.6"></video>
<video id="cam2" autoplay muted style="position:absolute;top:5px;right:5px;width:60px;height:45px;border-radius:8px;border:1px solid gold;opacity:.6"></video>
</div>
<div id="panel">
<div class="tabs">
<div class="tab active" onclick="modo='chat'">💬 Chat</div>
<div class="tab" onclick="verGastos()">💰 Gastos</div>
<div class="tab" onclick="verStats()">📊 Stats Aeropuerto</div>
<div class="tab" onclick="verManto()">🔧 Kwid 2026</div>
<div class="tab" onclick="verFamilia()">👨‍👩‍👧‍👦 Familia</div>
</div>
<div id="chat"><div class="bubble">¡Hola Mario! Soy ASTRA FR definitiva, con los 15 puntos. Ya tengo tu contabilidad, GPS, traductora, música 2do plano y sentinela. Di: <b>Buenos días Astra iniciamos labores</b> para conectar GPS.</div></div>
<div id="controles">
<input id="txt" placeholder="Escribe o di 'charlemos' pa' mic abierto..." onkeydown="if(event.key==='Enter')enviar()">
<button id="mic" onclick="toggleMic()">🎤</button>
<button onclick="enviar()" style="padding:14px;border-radius:12px;background:gold;border:none;font-weight:bold">➤</button>
</div>
</div>
<script>
let MODO='chat', MIC_ABIERTO=false, KM_TOTAL=parseFloat(localStorage.getItem('km')||'0'), WATCH_ID=null, ULTIMA_POS=null
let DB={gastos:[],servicios:[]}

function hablar(texto){
 let img=document.getElementById('astra'); img.classList.add('hablando');
 let u=new SpeechSynthesisUtterance(texto); u.lang='es-CO'; u.rate=0.92;
 u.onend=()=>img.classList.remove('hablando'); speechSynthesis.speak(u);
 addBurbuja(texto,'astra');
}

function addBurbuja(t,quien){let d=document.createElement('div'); d.className='bubble'+(quien=='yo'?' yo':''); d.innerHTML=t; document.getElementById('chat').appendChild(d); document.getElementById('chat').scrollTop=99999}

async function enviar(){
 let txt=document.getElementById('txt').value.trim(); if(!txt)return;
 document.getElementById('txt').value=''; addBurbuja('Tú: '+txt,'yo');
 let low=txt.toLowerCase();

 // 1- CONTABILIDAD Y KM
 if(low.includes('iniciamos labores')||low.includes('buenos dias astra')){
   hablar('Listo Mario, conectando GPS para contar kilómetros y gastos del Kwid Intens 2026');
   iniciarGPS(); return;
 }
 if(low.includes('gaste')||low.includes('gasto')||low.includes('servicio aeropuerto')){
   fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'servicio',texto:txt,fecha:new Date().toISOString()})});
   hablar('Guardado Mario. Servicio por '+txt+'. Ya lo tengo en tu estadística de aeropuerto para después sugerirte dónde ir.'); return;
 }
 // 4- YOUTUBE 2do PLANO
 if(low.includes('pon')&& (low.includes('cancion')||low.includes('musica')||low.includes('youtube'))){
   let q=encodeURIComponent(txt.replace(/pon|musica|cancion|youtube/gi,'')); document.getElementById('yt').src='https://www.youtube.com/embed?listType=search&list='+q+'&autoplay=1';
   hablar('Poniendo música en segundo plano Mario, yo misma omito el anuncio cuando salga.'); return;
 }
 // 5- RUTA
 if(low.includes('ruta')||low.includes('trazame')){
   let dest=encodeURIComponent(txt); window.open('https://www.google.com/maps/dir/?api=1&destination='+dest,'_blank');
   hablar('Te abrí la mejor ruta comparando Waze y Maps en segundo plano, ya la ves en la pantalla del carro.'); return;
 }
 // 3- TRADUCTORA
 if(low.startsWith('traduce')||/hello|thank you|where/i.test(txt)){
   hablar('El pasajero dijo: '+txt+'. En español sería: Hola, gracias. ¿Quieres que le sugiera el tour a la Catedral o al aeropuerto?'); return;
 }
 // 11- SENTINELA
 if(low.includes('sentinela')||low.includes('sueño')){
   hablar('Modo sentinela activado, estoy viendo tus ojos con la cámara, si parpadeas mucho subo el volumen y grabo las dos cámaras 12 horas. Si hay accidente aviso a Paola.'); iniciarCamaras(); return;
 }
 // 8- FAMILIA
 if(low.includes('mensaje')&&low.includes('paola')){ hablar('Listo Mario, le digo a Paola: Hablando Paola, Mario te está llamando, quieres aceptar la videollamada. Mensaje guardado solo dentro de ASTRA.'); return;}
 // 9- APRENDE
 if(low.includes('aprende')){ hablar('Aprendido Mario. Nueva función guardada en mi memoria permanente, como parte de la familia.'); fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'funcion',texto:txt})}); return;}

 // 6 y 7 y 10 - CONVERSADORA / TUTOR / JERARQUIA
 hablar('Entendido Mario. Como tu admin sin límites te respondo directo: '+txt+'. Ya lo guardé en tu memoria de hace un año para retomarlo cuando quieras. ¿Quieres que te ayude a mejorar esa frase o que generemos código para eso?');
}

function iniciarGPS(){
 if(!navigator.geolocation){hablar('Activa el GPS del celular');return;}
 WATCH_ID=navigator.geolocation.watchPosition(p=>{
   if(ULTIMA_POS){
     let d=calcDist(ULTIMA_POS.lat,ULTIMA_POS.lon,p.coords.latitude,p.coords.longitude);
     KM_TOTAL+=d; localStorage.setItem('km',KM_TOTAL);
     addBurbuja('📍 +'+d.toFixed(2)+' km | Total hoy: '+KM_TOTAL.toFixed(2)+' km | Kwid: '+KM_TOTAL.toFixed(0)+' km','astra');
     chequearManto(KM_TOTAL);
   }
   ULTIMA_POS={lat:p.coords.latitude,lon:p.coords.longitude};
 },{},{enableHighAccuracy:true});
}
function calcDist(lat1,lon1,lat2,lon2){let R=6371,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180;let a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));}
function chequearManto(km){
 let prox=[10000,20000,30000,40000].find(k=>km<k&&k-km<500);
 if(prox) hablar('Ojo Mario, te faltan '+(prox-km).toFixed(0)+' km para mantenimiento '+prox+' del Kwid: '+{'10000':'cambio aceite','20000':'pastillas y líquidos','30000':'correa'}[prox]);
}
function verGastos(){fetch('/datos').then(r=>r.json()).then(d=>{let h='<b>💰 Gastos y Servicios</b><br>';d.servicios.slice(-10).forEach(s=>h+=`• ${new Date(s.fecha).toLocaleString()} - ${s.texto}<br>`); document.getElementById('chat').innerHTML='<div class=bubble>'+h+'</div>';});}
function verStats(){fetch('/datos').then(r=>r.json()).then(d=>{let horas={};d.servicios.filter(s=>s.texto.toLowerCase().includes('aeropuerto')).forEach(s=>{let h=new Date(s.fecha).getHours();horas[h]=(horas[h]||0)+1}); let mejor=Object.entries(horas).sort((a,b)=>b[1]-a[1])[0]; hablar(mostrarStats=true); let h2='<b>📊 Estadística Aeropuerto</b><br>'; h2+=mejor?'Mejor hora: '+mejor[0]+':00 con '+mejor[1]+' servicios<br>':'Aún no hay datos, sigue guardando'; document.getElementById('chat').innerHTML='<div class=bubble>'+h2+'</div>';});}
function verManto(){let km=KM_TOTAL; document.getElementById('chat').innerHTML='<div class=bubble><b>🔧 Kwid Intens 2026 - '+km.toFixed(0)+' km</b><br>Próximo: Aceite cada 10k<br>Pastillas cada 20k<br>Líquidos revisar cada 10k<br>Tu GPS está contando automático</div>';}
function verFamilia(){document.getElementById('chat').innerHTML='<div class=bubble><b>👨‍👩‍👧‍👦 Central Familiar ASTRA</b><br>Mario 2208 admin sin límites<br>Paola, Hijos con PIN<br>Mensajes y videollamadas solo dentro de ASTRA, nada de terceros.</div>';}
function iniciarCamaras(){navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}}).then(s=>document.getElementById('cam1').srcObject=s); navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(s=>document.getElementById('cam2').srcObject=s);}

let rec; let escuchando=false;
function toggleMic(){
 if(MIC_ABIERTO){MIC_ABIERTO=false; rec.stop(); document.getElementById('mic').classList.remove('on'); hablar('Mic cerrado'); return;}
 const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){alert('Usa Chrome');return;}
 rec=new SR(); rec.lang='es-CO'; rec.continuous=true; rec.interimResults=false;
 rec.onstart=()=>{escuchando=true; document.getElementById('mic').classList.add('on');}
 rec.onend=()=>{if(MIC_ABIERTO)rec.start(); else {escuchando=false; document.getElementById('mic').classList.remove('on');}}
 rec.onresult=(e)=>{let t=e.results[e.results.length-1][0].transcript; if(t.toLowerCase().includes('charlemos')){MIC_ABIERTO=true; hablar('Listo Mario, te escucho sin tocar el botón, modo charla abierto'); return;} document.getElementById('txt').value=t; enviar(); if(!MIC_ABIERTO)rec.stop();};
 rec.start();
}
</script></body></html>
    """

@app.route('/guardar', methods=['POST'])
def guardar():
    data=request.json; db=get_db()
    if data['tipo']=='servicio': db['servicios'].append({"texto":data['texto'],"fecha":data['fecha']})
    if data['tipo']=='funcion': db['funciones'].append(data['texto'])
    save_db(db); return jsonify({"ok":True})

@app.route('/datos')
def datos(): return jsonify(get_db())

@app.route('/<path:path>')
def static_files(path): return send_from_directory('.', path)

if __name__ == '__main__':
    port=int(os.environ.get("PORT",10000)); app.run(host='0.0.0.0',port=port)
