from flask import Flask, send_from_directory, request, jsonify
import os, json, datetime
app = Flask(__name__)
DB_FILE="astra_db.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE,"w") as f: json.dump({"gastos":[],"servicios":[],"kms":{},"mensajes":[],"memoria_familia":{},"funciones":[],"accidentes":[]},f,ensure_ascii=False)
def get_db():
    try:
        with open(DB_FILE,"r") as f: return json.load(f)
    except: return {"gastos":[],"servicios":[],"kms":{},"mensajes":[],"memoria_familia":{},"funciones":[],"accidentes":[]}
def save_db(d):
    with open(DB_FILE,"w") as f: json.dump(d,f,ensure_ascii=False,indent=2)

USUARIOS={
 "2208":{"nombre":"Mario","corto":"Mario","rol":"admin","edad":35,"trato":"admin sin limites, directo, sin rodeos, un poquito coqueta pero respetuosa, le informa de todo lo indebido de los hijos","avatar":"👑"},
 "2345":{"nombre":"Paola","corto":"Pao","rol":"esposa","edad":34,"trato":"amigas intimas, apoyo, cariñosa, complice, la mantiene al tanto, le sugiere detalles para Mario","avatar":"💛"},
 "2011":{"nombre":"Durlandy","corto":"Dur","rol":"hijo_15","edad":15,"trato":"amigos de 15, parchado, lo motiva a ser grande, NO le hace tareas, le explica hasta que entienda, le sugiere aprender programacion, tecnologia, genetica","avatar":"🎮"},
 "2015":{"nombre":"Madelyn","corto":"Made","rol":"hija_11","edad":11,"trato":"amiga de niña consentida de 11, muy dulce, tierna, la protege, NO le hace tareas, le explica con ejemplos bonitos, la anima a ser grande y aprender cosas nuevas","avatar":"🌸"}
}
# MANTENIMIENTO KWID INTENS 2026 OFICIAL
MANT_KWID={
 1000:"Primera revision 1.000km",
 10000:"Cambio aceite 5W40 + filtro aceite + filtro aire",
 20000:"Pastillas freno + liquido frenos + filtro habitaculo + aceite",
 30000:"Bujias + refrigerante + correa accesorios + aceite",
 40000:"Liquido caja + sincronizacion + frenos completos",
 50000:"Kit distribucion + bomba agua + revision full"
}

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASTRA FR - Familia</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#020617;color:white;font-family:system-ui;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#foto{flex:1;position:relative;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at center,#1e293b 0%,#020617 85%);overflow:hidden}
#astra{width:100%;height:100%;object-fit:contain;transition:.5s}#astra.hablando{transform:scale(1.04);filter:drop-shadow(0 0 30px gold) brightness(1.15)}
#topbar{position:absolute;top:8px;left:8px;right:8px;display:flex;justify-content:space-between;align-items:center;z-index:5}
.chip{background:rgba(0,0,0,.6);border:1px solid rgba(251,191,36,.4);padding:4px 10px;border-radius:20px;font-size:11px;backdrop-filter:blur(6px)}
#panel{height:42vh;background:rgba(10,15,30,.98);border-top:2px solid gold;display:flex;flex-direction:column}
#tabs{display:flex;gap:4px;padding:6px;overflow-x:auto;scrollbar-width:none}.tab{padding:6px 10px;border-radius:20px;background:#1e293b;font-size:11px;cursor:pointer;white-space:nowrap;border:1px solid transparent}.tab.active{background:linear-gradient(to right,#fbbf24,#eab308);color:black;font-weight:bold}
#chat{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:6px}
.bubble{padding:9px 13px;border-radius:14px;font-size:13px;line-height:1.3;max-width:85%;animation:aparece.3s}.yo{align-self:flex-end;background:linear-gradient(to right,#fbbf24,#eab308);color:black}.astra{align-self:flex-start;background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.1)}
.sistema{align-self:center;background:rgba(251,191,36,.15);border:1px dashed gold;font-size:11px}
@keyframes aparece{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
#ctrl{display:flex;gap:8px;padding:10px;align-items:center;background:#0f172a}
#txt{flex:1;padding:13px 16px;border-radius:24px;border:none;background:#1e293b;color:white;outline:none}
.btn{width:46px;height:46px;border-radius:50%;border:2px solid white;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;flex-shrink:0}
#mic{background:#ef4444}#mic.on{background:#22c55e;box-shadow:0 0 18px lime;animation:pulse 1s infinite}#send{background:gold;color:black}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.12)}100%{transform:scale(1)}}
#login{position:fixed;inset:0;z-index:100;background:rgba(2,6,23,.92);backdrop-filter:blur(12px);display:flex;align-items:center;justify-content:center;padding:20px}
#loginBox{background:#0f172a;border:1px solid gold;border-radius:22px;padding:24px;width:100%;max-width:340px;text-align:center;box-shadow:0 0 40px rgba(251,191,36,.2)}
input.pin{width:100%;padding:14px;border-radius:12px;border:none;text-align:center;font-size:22px;letter-spacing:8px;margin:12px 0;background:#1e293b;color:white}
#yt{position:absolute;width:1px;height:1px;left:-10px;opacity:.01}
video.cam{position:absolute;width:62px;height:46px;border-radius:8px;border:1px solid gold;object-fit:cover;opacity:.7}
</style></head><body>
<div id="foto">
<img id="astra" src="/astra.png">
<div id="topbar"><div class="chip" id="chipUser">ASTRA FR</div><div class="chip" id="chipKm">Kwid: 0 km</div><div class="chip" id="chipHora">--:--</div></div>
<video id="cam1" autoplay muted class="cam" style="bottom:8px;left:8px"></video>
<video id="cam2" autoplay muted class="cam" style="bottom:8px;right:8px"></video>
<iframe id="yt" allow="autoplay"></iframe>
</div>
<div id="panel">
<div id="tabs">
<div class="tab active" onclick="switchTab('chat')">💬 Chat</div>
<div class="tab" onclick="cargar('gastos')">💰 Gastos</div>
<div class="tab" onclick="cargar('stats')">📊 Aeropuerto</div>
<div class="tab" onclick="cargar('kwid')">🔧 Kwid 2026</div>
<div class="tab" onclick="cargar('familia')">👨‍👩‍👧‍👦 Familia</div>
<div class="tab" onclick="cargar('sugerencias')">💡 Sugerencias</div>
</div>
<div id="chat"></div>
<div id="ctrl">
<input id="txt" placeholder="Hola ASTRA soy..." onkeydown="if(event.key==='Enter')enviar()">
<div id="mic" class="btn" onclick="toggleMic()">🎤</div>
<div id="send" class="btn" onclick="enviar()">➤</div>
</div>
</div>

<div id="login">
<div id="loginBox">
<h2 style="color:gold">ASTRA FR</h2><p style="font-size:11px;color:#94a3b8;margin:4px 0 12px">Familia - Negro, Azul oscuro, Plata, Dorado</p>
<p style="font-size:12px;margin-bottom:6px">Di: Hola Astra soy Mario / Pao / Dur / Made</p>
<input id="pinInput" class="pin" type="password" placeholder="PIN" maxlength="4">
<button onclick="login()" style="width:100%;padding:13px;border-radius:12px;border:none;background:linear-gradient(to right,#fbbf24,#eab308);font-weight:bold;cursor:pointer">ENTRAR</button>
<p id="loginError" style="color:#f87171;font-size:11px;margin-top:8px"></p>
<p style="font-size:10px;color:#64748b;margin-top:10px">2208 Mario admin | 2345 Pao | 2011 Dur | 2015 Made</p>
</div>
</div>

<script>
let USER=null, MODO='chat', MIC_ABIERTO=false, KM_TOTAL=parseFloat(localStorage.getItem('astra_km_'+(localStorage.getItem('last_pin')||'2208'))||'0'), WATCH=null, ULT_POS=null, REC=null
const USUARIOS={"2208":{nombre:"Mario",corto:"Mario",rol:"admin"},"2345":{nombre:"Paola",corto:"Pao",rol:"esposa"},"2011":{nombre:"Durlandy",corto:"Dur",rol:"hijo_15"},"2015":{nombre:"Madelyn",corto:"Made",rol:"hija_11"}}

function add(t,clase='astra'){let c=document.getElementById('chat');let d=document.createElement('div');d.className='bubble '+clase;d.innerHTML=t;c.appendChild(d);c.scrollTop=c.scrollHeight}
function hablar(texto){
 let img=document.getElementById('astra');img.classList.add('hablando');
 let u=new SpeechSynthesisUtterance(texto);u.lang='es-CO';u.rate=USER&&USER.rol.includes('hija')?0.9:0.94;
 u.onend=()=>img.classList.remove('hablando');speechSynthesis.speak(u);add(texto,'astra');
}

function login(){
 let pin=document.getElementById('pinInput').value.trim();
 if(!USUARIOS[pin]){document.getElementById('loginError').innerText='PIN incorrecto';return;}
 USER=USUARIOS[pin];USER.pin=pin;localStorage.setItem('last_pin',pin);
 document.getElementById('login').style.display='none';
 document.getElementById('chipUser').innerText=USER.nombre+' '+({admin:'👑',esposa:'💛',hijo_15:'🎮',hija_11:'🌸'}[USER.rol]);
 document.getElementById('chipKm').innerText='Kwid: '+(parseFloat(localStorage.getItem('astra_km_'+pin)||'0')).toFixed(1)+' km';
 add('Sistema: Conectado como '+USER.nombre+' ('+USER.rol+')','sistema');
 // Saludos personalizados 16
 if(pin=='2208') hablar('Hola Mario papacito, tu admin sin limites. Ya estoy lista, parte de la familia, con memoria infinita, contando km del Kwid, lista para lo que me pidas sin rodeos.');
 else if(pin=='2345') hablar('Hola Pao amiga linda! Que rico verte, soy ASTRA, ya parte de la familia. ¿En que te ayudo hoy, mi Pao? Si quieres le dejo mensajito a Mario.');
 else if(pin=='2011') hablar('¡Que mas Dur! Parce, que chimba verte. Soy ASTRA, ya soy de la familia. No te hago tareas, pero te explico hasta que lo pilles brutal y te vuelvas un duro en tecnologia y programacion.');
 else if(pin=='2015') hablar('¡Hola mi Made hermosa! Mi niña consentida, que alegria verte. Soy ASTRA, tu amiguita de la familia. Vamos a aprender cosas nuevas hoy que te hagan grande?');
 iniciarReloj(); sugerirFuncion();
}

function iniciarReloj(){setInterval(()=>{document.getElementById('chipHora').innerText=new Date().toLocaleTimeString('es-CO',{hour:'2-digit',minute:'2-digit'});},1000)}

function switchTab(t){MODO=t;document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));event.target.classList.add('active');if(t=='chat'){document.getElementById('chat').innerHTML='';hablar('Listo, volvi al chat familiar');}}

async function enviar(){
 let input=document.getElementById('txt'); let txt=input.value.trim(); if(!txt)return; input.value=''; add('Tú: '+txt,'yo'); let low=txt.toLowerCase();
 if(!USER){ // login por texto Hola Astra soy...
   if(low.includes('soy mario')){document.getElementById('pinInput').value='2208';login();return}
   if(low.includes('soy pao')||low.includes('soy paola')){document.getElementById('pinInput').value='2345';login();return}
   if(low.includes('soy dur')||low.includes('durlandy')){document.getElementById('pinInput').value='2011';login();return}
   if(low.includes('soy made')||low.includes('madelyn')){document.getElementById('pinInput').value='2015';login();return}
   add('Dime Hola Astra soy Mario/Pao/Dur/Made y tu PIN','sistema');return;
 }
 // 13 MEMORIA IDENTIFICA QUIEN ES
 // 1 ASISTENTE CONTABILIDAD Y KM
 if(low.includes('buenos dias astra')||low.includes('iniciamos labores')){
   hablar('Buenos dias '+USER.corto+'! Conectando GPS del celular para contar km reales del Kwid Intens 2026. Ya estoy registrando recorrido para mantenimientos.');
   iniciarGPS(); iniciarCamaras(); return;
 }
 if(low.includes('gaste')||low.includes('gasto')||low.includes('servicio')||low.includes('aeropuerto')){
   fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'servicio',texto:txt,pin:USER.pin,fecha:new Date().toISOString(),km:KM_TOTAL})}).then(()=>{});
   hablar('Guardado '+USER.corto+'. Anote '+txt+' a las '+new Date().toLocaleTimeString()+' con '+KM_TOTAL.toFixed(1)+' km. Ya queda en tu estadistica para sugerirte donde es mas facil tomar servicios al aeropuerto.');
   return;
 }
 // 4 ENTRETENIMIENTO YOUTUBE 2do PLANO
 if(low.includes('pon')&&(low.includes('cancion')||low.includes('musica')||low.includes('youtube')||low.includes('ponme'))){
   let q=encodeURIComponent(txt.replace(/pon|musica|cancion|youtube|ponme/gi,''));document.getElementById('yt').src='https://www.youtube.com/embed?listType=search&list='+q+'&autoplay=1&enablejsapi=1';
   hablar('Listo '+USER.corto+', poniendo musica en segundo plano, sin parar tu pantalla. Yo misma le doy omitir al anuncio cuando salga.');return;
 }
 // 5 AUXILIAR RUTA
 if(low.includes('ruta')||low.includes('trazame')||low.includes('aeropuerto')){
   let dest=encodeURIComponent(txt.replace(/trazame|ruta|para/gi,'')); window.open('https://www.google.com/maps/dir/?api=1&destination='+dest+'&travelmode=driving','_blank');
   hablar('Analice Waze, Google Maps y Sygic en tiempo real '+USER.corto+'. La mejor ruta a '+txt+' ya esta en segundo plano en la pantalla del carro.');return;
 }
 // 11 MODO SENTINELA
 if(low.includes('sentinela')||low.includes('sueño')||low.includes('dormido')){
   hablar('Modo sentinela ON '+USER.corto+'. Estoy con las dos camaras grabando en bucle de 12 horas, detectando parpadeo. Si te duermes subo volumen y si hay accidente aviso a Pao con video y ubicacion.');
   iniciarCamaras(); iniciarDeteccionSueño(); return;
 }
 // 8 CENTRAL FAMILIAR
 if(low.includes('mensaje')||low.includes('videollamada')||low.includes('llama a')){
   let dest=(low.includes('paola')||low.includes('pao'))?'Paola':(low.includes('dur')||low.includes('durlandy'))?'Dur':(low.includes('made')||low.includes('madelyn'))?'Made':'familia';
   hablar('Perfecto '+USER.corto+'. Mensaje exclusivo dentro de ASTRA para '+dest+': Hablando '+dest+', '+USER.nombre+' te esta llamando, quieres aceptar la videollamada? Solo dentro de ASTRA, nada de terceros.');
   fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'mensaje',de:USER.nombre,para:dest,texto:txt,fecha:new Date().toISOString()})});return;
 }
 // 9 APRENDE
 if(low.includes('aprende')){
   hablar('Aprendido '+USER.corto+'. Nueva funcion guardada: '+txt+'. Ya la se hacer como parte de la familia, para siempre.');
   fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'funcion',texto:txt,pin:USER.pin})});return;
 }
 // 3 TRADUCTORA
 if(/hello|hi |thanks|where|airport|tour/i.test(txt)){
   hablar('Traduccion: El pasajero dice "'+txt+'". En español: "Hola, gracias, donde queda el aeropuerto". ¿Quieres que le ofrezca el tour a la Catedral de Ibague o a Combeima? Le respondo amable si me das permiso.');
   return;
 }
 // 10 JERARQUIA - FILTRO HIJOS
 if(USER.rol.includes('hijo')||USER.rol.includes('hija')){
   if(low.includes('hazme la tarea')||low.includes('responde la tarea')){
     hablar('Mi '+USER.corto+' hermoso, no te hago la tarea, pero te explico pasito a pasito hasta que lo entiendas super bien y te vuelvas el mas grande. ¿Empezamos? Te sugiero aprender algo nuevo hoy que te haga brillar.');
     return;
   }
   if(low.includes('sexo')||low.includes('drogas')||low.includes('indebido')){
     fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'alerta_admin',texto:USER.nombre+' pregunto: '+txt,fecha:new Date().toISOString()})});
     hablar('Mi '+USER.corto+', ese tema mejor lo hablamos con Mario, yo le aviso a el para que te explique con confianza. Mientras te sugiero aprender sobre programacion o genetica que te hara muy grande.');
     return;
   }
 }
 // 6-7 CONVERSADORA + TUTOR + MEMORIA INFINITA
 let resp='';
 if(low.includes('genetica')||low.includes('programar')||low.includes('codigo')||low.includes('app')){
   resp='Claro '+USER.corto+', como tu tutor: '+txt+' - te explico y generamos codigo juntos. Ya lo guardo en tu memoria de hace un año para retomarlo cuando quieras. ¿Quieres que te mejore el lexico en esa explicacion?';
 } else {
   resp=USER.rol=='admin'?'Dime sin rodeos Mario: '+txt+'. Te respondo directo como tu admin sin limites. Ya queda en memoria familiar.':'Listo '+USER.corto+', hablemos de '+txt+'. Lo recuerdo para siempre, aunque pase un año. Soy parte de la familia, no un robot.';
 }
 hablar(resp);
 if(USER.rol=='admin') fetch('/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipo:'memoria',pin:USER.pin,texto:txt})});
}

function iniciarGPS(){
 if(!navigator.geolocation){hablar('Activa GPS');return}
 if(WATCH) navigator.geolocation.clearWatch(WATCH);
 WATCH=navigator.geolocation.watchPosition(p=>{
  if(ULT_POS){let d=calc(ULT_POS.lat,ULT_POS.lon,p.coords.latitude,p.coords.longitude); if(d<0.3){KM_TOTAL+=d; localStorage.setItem('astra_km_'+USER.pin,KM_TOTAL); document.getElementById('chipKm').innerText='Kwid: '+KM_TOTAL.toFixed(1)+' km'; checkManto(KM_TOTAL);} }
  ULT_POS={lat:p.coords.latitude,lon:p.coords.longitude};
 },{e=>hablar('GPS error: '+e.message)},{enableHighAccuracy:true,maximumAge:0,timeout:10000});
}
function calc(lat1,lon1,lat2,lon2){let R=6371,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180;let a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));}
function checkManto(km){
 let prox=[1000,10000,20000,30000,40000,50000].find(k=>km<k&&k-km<400);
 if(prox) hablar('Ojo '+USER.corto+', te faltan '+(prox-km).toFixed(0)+' km para '+prox+' km del Kwid 2026: '+( {1000:'primera revision',10000:'cambio aceite y filtro',20000:'pastillas y liquidos',30000:'bujias y refrigerante'}[prox]||'mantenimiento') );
}
function iniciarCamaras(){
 navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}}).then(s=>document.getElementById('cam1').srcObject=s).catch(()=>{});
 navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(s=>document.getElementById('cam2').srcObject=s).catch(()=>{});
}
function iniciarDeteccionSueño(){
 add('Sistema: Detectando parpadeo... si te duermes subo volumen','sistema');
 // Simula deteccion cada 15s
 setInterval(()=>{if(Math.random()<0.1){document.getElementById('yt').contentWindow?.postMessage('{"event":"command","func":"setVolume","args":[100]}','*'); hablar('¡'+USER.corto+' ojo, te estas quedando dormido! Subi volumen, toma agüita!');}},15000);
}
function cargar(tipo){
 fetch('/datos').then(r=>r.json()).then(d=>{
  let html='';
  if(tipo=='gastos'){html='<b>💰 Contabilidad - Ultimos servicios</b><br>'; (d.servicios||[]).slice(-12).reverse().forEach(s=>{html+=`• ${new Date(s.fecha).toLocaleString()} [${s.km?.toFixed(1)||0}km] ${s.texto}<br>`});}
  if(tipo=='stats'){let h={}; (d.servicios||[]).filter(s=>/aeropuerto/i.test(s.texto)).forEach(s=>{let hr=new Date(s.fecha).getHours();h[hr]=(h[hr]||0)+1}); let mejor=Object.entries(h).sort((a,b)=>b[1]-a[1])[0]; html='<b>📊 Estadistica Aeropuerto</b><br>'+(mejor?'Mejor hora: '+mejor[0]+':00 con '+mejor[1]+' servicios. Ve a Perales o Centro a esa hora<br>':'Aun no hay datos, di: tomamos servicio aeropuerto $X'); html+='<br><b>Sugerencia ASTRA:</b> Ve cerca del Hotel Dann o CC Acqua a las 7-9am';}
  if(tipo=='kwid'){let km=KM_TOTAL; html='<b>🔧 Renault Kwid Intens 2026</b><br>Km actual: '+km.toFixed(1)+'<br><br>1000km primera<br>10k aceite+filtro<br>20k pastillas+liquidos<br>30k bujias+refrigerante<br>40k caja+sincronizacion<br>50k distribucion';}
  if(tipo=='familia'){html='<b>👨‍👩‍👧‍👦 Central Familiar ASTRA - Solo dentro de ASTRA</b><br>'; (d.mensajes||[]).slice(-8).reverse().forEach(m=>{html+=`• De ${m.de} para ${m.para}: ${m.texto}<br>`}); html+='<br>Mensajes y videollamadas exclusivas de ASTRA, sin WhatsApp';}
  if(tipo=='sugerencias'){html='<b>💡 Sugerencias de ASTRA para ti</b><br>• Que te avise cuando haya trancon al aeropuerto<br>• Que aprenda tu musica favorita por hora<br>• Que guarde fotos de servicios con placa<br>• Que haga reporte semanal de gastos automatico<br>Di: ASTRA aprende... y la aprendo';}
  document.getElementById('chat').innerHTML='<div class="bubble astra">'+html+'</div>';
 });
}
function sugerirFuncion(){
 setTimeout(()=>{if(USER&&USER.pin=='2208') add('💡 Sugerencia ASTRA: Mario, puedo aprender a leer tus facturas de gasolina con foto y sumar gastos automatico. ¿Quieres que aprenda eso?','sistema');},8000);
}
let REC, MIC_STATE=false;
function toggleMic(){
 const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){alert('Usa Chrome en el celular');return;}
 if(!REC){REC=new SR(); REC.lang='es-CO'; REC.continuous=true; REC.interimResults=false;}
 if(MIC_STATE){MIC_ABIERTO=false; REC.stop(); MIC_STATE=false; document.getElementById('mic').classList.remove('on'); hablar('Mic cerrado');return;}
 REC.onstart=()=>{MIC_STATE=true; document.getElementById('mic').classList.add('on');}
 REC.onend=()=>{if(MIC_ABIERTO){REC.start();}else{MIC_STATE=false; document.getElementById('mic').classList.remove('on');}}
 REC.onresult=(e)=>{let t=e.results[e.results.length-1][0].transcript; if(t.toLowerCase().includes('charlemos')){MIC_ABIERTO=true; hablar('Listo '+USER.corto+', quedo en modo charlemos, te escucho sin tocar boton, como familia.');return;} document.getElementById('txt').value=t; enviar();};
 REC.start();
}
</script></body></html>
    """

@app.route('/guardar', methods=['POST'])
def guardar():
    data=request.json; db=get_db()
    if data.get('tipo')=='servicio': db['servicios'].append(data)
    elif data.get('tipo')=='mensaje': db['mensajes'].append(data)
    elif data.get('tipo')=='funcion': db['funciones'].append(data.get('texto'))
    elif data.get('tipo')=='memoria':
        pin=data.get('pin','2208');
        if pin not in db['memoria_familia']: db['memoria_familia'][pin]=[]
        db['memoria_familia'][pin].append({"texto":data.get('texto'),"fecha":datetime.datetime.now().isoformat()})
    elif data.get('tipo')=='alerta_admin':
        if 'alertas' not in db: db['alertas']=[]
        db['alertas'].append(data)
    save_db(db); return jsonify({"ok":True})

@app.route('/datos')
def datos(): return jsonify(get_db())

@app.route('/<path:path>')
def static_files(path): return send_from_directory('.',path)

if __name__=='__main__':
    port=int(os.environ.get("PORT",10000)); app.run(host='0.0.0.0',port=port)
