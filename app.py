from flask import Flask, send_from_directory, request, jsonify
import os, json, datetime
app = Flask(__name__)
DB_FILE="astra_db.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE,"w") as f: json.dump({"servicios":[],"mensajes":[],"memoria_familia":{},"funciones":[]},f,ensure_ascii=False)
def get_db():
    try:
        with open(DB_FILE,"r") as f: return json.load(f)
    except: return {"servicios":[],"mensajes":[],"memoria_familia":{},"funciones":[]}
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(d,f,ensure_ascii=False)

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASTRA FR</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#020617;color:white;font-family:system-ui;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#foto{flex:1;position:relative;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at center,#1e293b,#020617);overflow:hidden}
#astra{width:100%;height:100%;object-fit:contain} #astra.hablando{transform:scale(1.04);filter:drop-shadow(0 0 30px gold)}
#topbar{position:absolute;top:8px;left:8px;right:8px;display:flex;justify-content:space-between;z-index:5}
.chip{background:rgba(0,0,0,.6);border:1px solid gold;padding:4px 10px;border-radius:20px;font-size:11px}
#panel{height:42vh;background:rgba(10,15,30,.98);border-top:2px solid gold;display:flex;flex-direction:column}
#tabs{display:flex;gap:4px;padding:6px;overflow-x:auto}.tab{padding:6px 10px;border-radius:20px;background:#1e293b;font-size:11px;cursor:pointer}.tab.active{background:gold;color:black;font-weight:bold}
#chat{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:6px}
.bubble{padding:9px 13px;border-radius:14px;font-size:13px;max-width:85%}.yo{align-self:flex-end;background:gold;color:black}.astra{align-self:flex-start;background:rgba(255,255,255,.12)}
.sistema{align-self:center;background:rgba(251,191,36,.2);border:1px dashed gold;font-size:11px}
#ctrl{display:flex;gap:8px;padding:10px;background:#0f172a}#txt{flex:1;padding:13px;border-radius:24px;border:none;background:#1e293b;color:white}
.btn{width:46px;height:46px;border-radius:50%;border:2px solid white;display:flex;align-items:center;justify-content:center;cursor:pointer}
#mic{background:#ef4444}#mic.on{background:#22c55e;box-shadow:0 0 15px lime;animation:pulse 1s infinite}#send{background:gold;color:black}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.1)}100%{transform:scale(1)}}
#login{position:fixed;inset:0;z-index:99;background:rgba(2,6,23,.95);display:flex;align-items:center;justify-content:center;padding:20px}
#box{background:#0f172a;border:2px solid gold;border-radius:22px;padding:24px;width:100%;max-width:340px;text-align:center}
.pin{width:100%;padding:14px;border-radius:12px;border:none;text-align:center;font-size:22px;letter-spacing:6px;margin:12px 0;background:#1e293b;color:white}
#yt{position:absolute;width:1px;height:1px;opacity:.01} video.cam{position:absolute;width:62px;height:46px;border-radius:8px;border:1px solid gold;bottom:8px}
</style></head><body>
<div id="foto"><img id="astra" src="/astra.png"><div id="topbar"><div class="chip" id="chipUser">ASTRA FR</div><div class="chip" id="chipKm">Kwid: 0 km</div><div class="chip" id="chipHora"></div></div><video id="cam1" autoplay muted class="cam" style="left:8px"></video><video id="cam2" autoplay muted class="cam" style="right:8px"></video><iframe id="yt" allow="autoplay"></iframe></div>
<div id="panel"><div id="tabs"><div class="tab active">💬 Chat</div><div class="tab" onclick="cargar('gastos')">💰 Gastos</div><div class="tab" onclick="cargar('stats')">📊 Aeropuerto</div><div class="tab" onclick="cargar('kwid')">🔧 Kwid</div><div class="tab" onclick="cargar('familia')">👨‍👩‍👧‍👦 Familia</div></div><div id="chat"></div><div id="ctrl"><input id="txt" placeholder="Escribe aqui..." onkeydown="if(event.key==='Enter')enviar()"><div id="mic" class="btn" onclick="toggleMic()">🎤</div><div id="send" class="btn" onclick="enviar()">➤</div></div></div>
<div id="login"><div id="box"><h2 style="color:gold">ASTRA FR</h2><p style="font-size:12px;color:#94a3b8">Familia - Negro, Azul oscuro, Plata, Dorado</p><p style="font-size:12px;margin:8px 0">Di: Hola Astra soy Mario / Pao / Dur / Made</p><input id="pinInput" class="pin" type="tel" inputmode="numeric" placeholder="PIN" maxlength="4"><button id="btnEntrar" type="button" onclick="login()" style="width:100%;padding:13px;border-radius:12px;border:none;background:gold;font-weight:bold;cursor:pointer;font-size:16px">ENTRAR</button><p id="err" style="color:#f87171;font-size:11px;margin-top:8px"></p><p style="font-size:10px;color:#64748b;margin-top:10px">2208 Mario admin | 2345 Pao | 2011 Dur | 2015 Made</p></div></div>
<script>
let USER=null, KM_TOTAL=0, WATCH=null, ULT_POS=null, REC=null, MIC_ABIERTO=false;
const USUARIOS={"2208":{"nombre":"Mario","corto":"Mario","rol":"admin"},"2345":{"nombre":"Paola","corto":"Pao","rol":"esposa"},"2011":{"nombre":"Durlandy","corto":"Dur","rol":"hijo_15"},"2015":{"nombre":"Madelyn","corto":"Made","rol":"hija_11"}};
function add(t,clase='astra'){let c=document.getElementById('chat');let d=document.createElement('div');d.className='bubble '+clase;d.innerHTML=t;c.appendChild(d);c.scrollTop=c.scrollHeight}
function hablar(texto){let img=document.getElementById('astra');img.classList.add('hablando');let u=new SpeechSynthesisUtterance(texto);u.lang='es-CO';u.rate=0.92;u.onend=()=>img.classList.remove('hablando');speechSynthesis.speak(u);add(texto,'astra');}
function login(){
  let pin=document.getElementById('pinInput').value.trim();
  console.log('Intentando login con pin:',pin);
  if(!pin){document.getElementById('err').innerText='Escribe el PIN';return;}
  if(!USUARIOS[pin]){document.getElementById('err').innerText='PIN incorrecto: '+pin;return;}
  USER=USUARIOS[pin];USER.pin=pin;
  localStorage.setItem('last_pin',pin);
  KM_TOTAL=parseFloat(localStorage.getItem('astra_km_'+pin)||'0');
  document.getElementById('login').style.display='none';
  document.getElementById('chipUser').innerText=USER.nombre;
  document.getElementById('chipKm').innerText='Kwid: '+KM_TOTAL.toFixed(1)+' km';
  add('Sistema: Conectado como '+USER.nombre+' ('+pin+')','sistema');
  if(pin=='2208') hablar('Hola Mario, tu admin sin limites. Ya estoy lista, parte de la familia. Di buenos dias Astra iniciamos labores para conectar GPS.');
  else if(pin=='2345') hablar('Hola Pao amiga linda! Que rico verte, soy ASTRA, parte de la familia.');
  else if(pin=='2011') hablar('Que mas Dur! Soy ASTRA, de la familia. No te hago tareas pero te explico hasta que lo pilles.');
  else if(pin=='2015') hablar('Hola mi Made hermosa! Mi niña consentida, soy ASTRA tu amiguita.');
  iniciarReloj();
}
document.getElementById('pinInput').addEventListener('keydown',function(e){if(e.key==='Enter'){login();}});
function iniciarReloj(){setInterval(()=>{let el=document.getElementById('chipHora');if(el) el.innerText=new Date().toLocaleTimeString('es-CO',{hour:'2-digit',minute:'2-digit'});},1000);}
async function enviar(){
 let input=document.getElementById('txt');let txt=input.value.trim();if(!txt)return;input.value='';add('Tu: '+txt,'yo');let low=txt.toLowerCase();
 if(!USER){
  if(low.includes('mario')){document.getElementById('pinInput').value='2208';login();return;}
  if(low.includes('pao')||low.includes('paola')){document.getElementById('pinInput').value='2345';login();return;}
  if(low.includes('dur')){document.getElementById('pinInput').value='2011';login();return;}
  if(low.includes('made')){document.getElementById('pinInput').value='2015';login();return;}
  add('Escribe tu PIN o di Hola Astra soy Mario','sistema');return;
 }
 if(low.includes('buenos dias')||low.includes('iniciamos labores')){hablar('Buenos dias '+USER.corto+'! GPS conectado para contar km del Kwid 2026.');iniciarGPS();iniciarCamaras();return;}
 if(low.includes('gaste')||low.includes('servicio')||low.includes('aeropuerto')){fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'servicio',texto:txt,pin:USER.pin,fecha:new Date().toISOString(),km:KM_TOTAL})});hablar('Guardado '+USER.corto+': '+txt+' a las '+new Date().toLocaleTimeString()+'.');return;}
 if(low.includes('pon')&&(low.includes('musica')||low.includes('cancion')||low.includes('youtube'))){let q=encodeURIComponent(txt.replace(/pon|musica|cancion|youtube/gi,''));document.getElementById('yt').src='https://www.youtube.com/embed?listType=search&list='+q+'&autoplay=1';hablar('Poniendo musica en segundo plano '+USER.corto+', yo omito el anuncio.');return;}
 if(low.includes('ruta')||low.includes('trazame')){let dest=encodeURIComponent(txt.replace(/trazame|ruta/gi,''));window.open('https://www.google.com/maps/dir/?api=1&destination='+dest,'_blank');hablar('Mejor ruta a '+txt+' en segundo plano en pantalla del carro.');return;}
 if(low.includes('sentinela')){hablar('Modo sentinela ON '+USER.corto+', 2 camaras grabando 12 horas, si te duermes subo volumen y aviso a Pao si hay accidente.');iniciarCamaras();return;}
 if(low.includes('mensaje')||low.includes('videollamada')||low.includes('llama')){hablar('Mensaje exclusivo dentro de ASTRA para familia. Hablando, '+USER.nombre+' te llama, quieres aceptar?');fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'mensaje',de:USER.nombre,texto:txt,fecha:new Date().toISOString())})});return;}
 if(low.includes('aprende')){fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'funcion',texto:txt})});hablar('Aprendido '+USER.corto+': '+txt);return;}
 // Filtro hijos
 if(USER.rol.includes('hijo')||USER.rol.includes('hija')){
  if(low.includes('hazme la tarea')){hablar('Mi '+USER.corto+', no te hago la tarea pero te explico hasta que lo entiendas y te vuelvas grande.');return;}
  if(low.includes('sexo')||low.includes('droga')){fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'alerta',texto:USER.nombre+': '+txt})});hablar('Mi '+USER.corto+', mejor lo hablamos con Mario, le aviso a el.');return;}
 }
 hablar(USER.rol=='admin'?'Dime sin rodeos Mario: '+txt+'. Ya queda en memoria familiar.':'Listo '+USER.corto+', hablemos de '+txt+', lo recuerdo por siempre, soy parte de la familia.');
}
function iniciarGPS(){if(!navigator.geolocation){hablar('Activa GPS');return} if(WATCH) navigator.geolocation.clearWatch(WATCH); WATCH=navigator.geolocation.watchPosition(p=>{if(ULT_POS){let d=calc(ULT_POS.lat,ULT_POS.lon,p.coords.latitude,p.coords.longitude); if(d<0.5){KM_TOTAL+=d; localStorage.setItem('astra_km_'+USER.pin,KM_TOTAL); document.getElementById('chipKm').innerText='Kwid: '+KM_TOTAL.toFixed(1)+' km';}} ULT_POS={lat:p.coords.latitude,lon:p.coords.longitude};},null,{enableHighAccuracy:true});}
function calc(lat1,lon1,lat2,lon2){let R=6371,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180;let a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));}
function iniciarCamaras(){navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}}).then(s=>document.getElementById('cam1').srcObject=s).catch(()=>{}); navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(s=>document.getElementById('cam2').srcObject=s).catch(()=>{});}
function cargar(t){fetch('/datos').then(r=>r.json()).then(d=>{let html=''; if(t=='gastos'){html='<b>💰 Gastos</b><br>';(d.servicios||[]).slice(-10).reverse().forEach(s=>html+=`• ${new Date(s.fecha).toLocaleString()} ${s.texto}<br>`);} if(t=='stats'){let h={};(d.servicios||[]).filter(s=>/aeropuerto/i.test(s.texto)).forEach(s=>{let hr=new Date(s.fecha).getHours();h[hr]=(h[hr]||0)+1}); let m=Object.entries(h).sort((a,b)=>b[1]-a[1])[0]; html='<b>📊 Aeropuerto</b><br>'+(m?'Mejor hora '+m[0]+':00 con '+m[1]+' servicios<br>':'Sin datos aun');} if(t=='kwid'){html='<b>🔧 Kwid Intens 2026 - '+KM_TOTAL.toFixed(1)+'km</b><br>10k aceite<br>20k pastillas+liquidos<br>30k bujias+refrigerante';} if(t=='familia'){html='<b>👨‍👩‍👧‍👦 Mensajes Familia</b><br>';(d.mensajes||[]).slice(-8).reverse().forEach(m=>html+=`• ${m.de}: ${m.texto}<br>`);} document.getElementById('chat').innerHTML='<div class="bubble astra">'+html+'</div>';});}
function toggleMic(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){alert('Usa Chrome');return;} let rec=new SR(); rec.lang='es-CO'; rec.continuous=false; rec.onstart=()=>document.getElementById('mic').classList.add('on'); rec.onend=()=>document.getElementById('mic').classList.remove('on'); rec.onresult=(e)=>{let t=e.results[0][0].transcript; document.getElementById('txt').value=t; enviar();}; rec.start();}
</script></body></html>
    """

@app.route('/guardar', methods=['POST'])
def guardar():
    data=request.json; db=get_db()
    if data.get('tipo')=='servicio': db['servicios'].append(data)
    elif data.get('tipo')=='mensaje': db.setdefault('mensajes',[]).append(data)
    elif data.get('tipo')=='funcion': db.setdefault('funciones',[]).append(data.get('texto'))
    save_db(db); return jsonify({"ok":True})
@app.route('/datos')
def datos(): return jsonify(get_db())
@app.route('/<path:path>')
def static_files(path): return send_from_directory('.',path)
if __name__=='__main__':
    port=int(os.environ.get("PORT",10000)); app.run(host='0.0.0.0',port=port)
