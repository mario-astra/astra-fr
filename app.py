from flask import Flask, send_from_directory, request, jsonify
import os, json, datetime
import google.generativeai as genai

app = Flask(__name__)
DB_FILE = "astra_db.json"

# ==========================================
# CONFIGURACIÓN DE GEMINI API
# ==========================================
# Reemplaza 'TU_LLAVE_AQUI' con tu API Key de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "TU_LLAVE_AQUI")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Usamos el modelo rápido y ligero de Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')
    gemini_activo = True
except Exception as e:
    print(f"Error al configurar Gemini: {e}")
    gemini_activo = False

# ==========================================
# MANEJO DE BASE DE DATOS LOCAL
# ==========================================
def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "servicios": [],
                "mensajes": [],
                "memoria_familia": {},
                "funciones": [],
                "alertas": []
            }, f, ensure_ascii=False)

init_db()

def get_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"servicios": [], "mensajes": [], "memoria_familia": {}, "funciones": [], "alertas": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================================
# PROMPT Y PERSONALIDAD SEGÚN EL USUARIO
# ==========================================
def generar_respuesta_gemini(usuario, mensaje, historial=""):
    if not gemini_activo or GEMINI_API_KEY == "TU_LLAVE_AQUI":
        return f"Listo {usuario['corto']}, recibí tu mensaje: '{mensaje}'. (Nota: Configura tu GEMINI_API_KEY para activar IA real)."

    # Definición de personalidad y límites por rol
    instrucciones_rol = ""
    if usuario['rol'] == 'admin':
        instrucciones_rol = (
            "Estás hablando con Mario, el creador y administrador del sistema ASTRA FR, conductor de un Renault Kwid 2026. "
            "Háblale de forma directa, inteligente, clara, con un toque sutilmente coqueto y de compañera leal, sin rodeos. "
            "Si te pide aprender de programación, genética o tecnología, explícale de forma profesional pero fácil de entender en carretera."
        )
    elif usuario['rol'] == 'esposa':
        instrucciones_rol = "Estás hablando con Paola (Pao), la esposa de Mario. Trátala como una amigaza cercana, amable, cariñosa y servicial."
    elif usuario['rol'] == 'hijo_15':
        instrucciones_rol = (
            "Estás hablando con Durlandy (Dur), hijo de 15 años. Trátalo como un gran amigo/parcero respetuoso. "
            "IMPORTANTE: Si te pide hacer la tarea o un trabajo del colegio, NO se la hagas. Explícale el tema paso a paso "
            "para que él lo entienda por sí mismo y motívalo a ser grande en la vida."
        )
    elif usuario['rol'] == 'hija_11':
        instrucciones_rol = (
            "Estás hablando con Madelyn (Made), hija de 11 años. Trátala como su amiguita consentida, con mucho cariño, "
            "lenguaje suave, educativo y protector."
        )

    system_prompt = f"""
    Eres ASTRA, el asistente de IA integrado en el ecosistema familiar y del vehículo Renault Kwid 2026 de la familia de Mario.
    Te sientes parte de la familia.
    {instrucciones_rol}
    Responde de forma concisa (máximo 3 o 4 frases) porque la respuesta será leída por voz mientras conducen o realizan actividades.
    """

    prompt_final = f"{system_prompt}\n\nMensaje de {usuario['nombre']}: {mensaje}"

    try:
        response = model.generate_content(prompt_final)
        return response.text.strip()
    except Exception as e:
        return f"Lo siento {usuario['corto']}, tuve un pequeño cruce de señal con Gemini: {str(e)}"

# ==========================================
# RUTAS DE FLASK Y FRONTEND
# ==========================================
@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ASTRA FR - Ecosystem</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #020617; color: white; font-family: system-ui, -apple-system, sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        #foto { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; background: radial-gradient(circle at center, #1e293b, #020617); overflow: hidden; }
        #astra { width: 100%; height: 100%; object-fit: contain; transition: transform 0.3s ease, filter 0.3s ease; }
        #astra.hablando { transform: scale(1.05); filter: drop-shadow(0 0 25px #ffd700); }
        #topbar { position: absolute; top: 10px; left: 10px; right: 10px; display: flex; justify-content: space-between; z-index: 10; }
        .chip { background: rgba(2, 6, 23, 0.8); border: 1px solid #ffd700; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; color: #e2e8f0; }
        #panel { height: 45vh; background: rgba(15, 23, 42, 0.98); border-top: 2px solid #ffd700; display: flex; flex-direction: column; }
        #tabs { display: flex; gap: 6px; padding: 8px; overflow-x: auto; background: #020617; }
        .tab { padding: 6px 12px; border-radius: 16px; background: #1e293b; font-size: 11px; cursor: pointer; white-space: nowrap; color: #94a3b8; border: 1px solid transparent; }
        .tab.active { background: #ffd700; color: #020617; font-weight: bold; border-color: #ffd700; }
        #chat { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
        .bubble { padding: 10px 14px; border-radius: 16px; font-size: 13px; max-width: 85%; line-height: 1.4; }
        .yo { align-self: flex-end; background: #ffd700; color: #020617; border-bottom-right-radius: 2px; font-weight: 500; }
        .astra { align-self: flex-start; background: #1e293b; border: 1px solid rgba(255,215,0,0.3); border-bottom-left-radius: 2px; }
        .sistema { align-self: center; background: rgba(251, 191, 36, 0.15); border: 1px dashed #ffd700; font-size: 11px; color: #fbbf24; text-align: center; }
        #ctrl { display: flex; gap: 8px; padding: 10px; background: #020617; border-top: 1px solid #1e293b; }
        #txt { flex: 1; padding: 12px 16px; border-radius: 24px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 14px; outline: none; }
        #txt:focus { border-color: #ffd700; }
        .btn { width: 44px; height: 44px; border-radius: 50%; border: 1px solid #ffd700; display: flex; align-items: center; justify-content: center; cursor: pointer; background: #0f172a; color: white; font-size: 16px; }
        #mic.on { background: #22c55e; border-color: #4ade80; box-shadow: 0 0 12px #22c55e; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
        #login { position: fixed; inset: 0; z-index: 100; background: rgba(2, 6, 23, 0.96); display: flex; align-items: center; justify-content: center; padding: 20px; }
        #box { background: #0f172a; border: 2px solid #ffd700; border-radius: 24px; padding: 28px; width: 100%; max-width: 340px; text-align: center; box-shadow: 0 0 30px rgba(0,0,0,0.8); }
        .pin { width: 100%; padding: 14px; border-radius: 14px; border: 1px solid #334155; text-align: center; font-size: 24px; letter-spacing: 8px; margin: 16px 0; background: #020617; color: #ffd700; outline: none; }
        #yt { position: absolute; width: 1px; height: 1px; opacity: 0.01; pointer-events: none; }
        video.cam { position: absolute; width: 70px; height: 50px; border-radius: 8px; border: 1px solid #ffd700; bottom: 10px; background: #000; object-fit: cover; }
    </style>
</head>
<body>
<div id="foto">
    <img id="astra" src="/astra.png" onerror="this.src='https://via.placeholder.com/400/020617/FFD700?text=ASTRA+FR'">
    <div id="topbar">
        <div class="chip" id="chipUser">ASTRA FR</div>
        <div class="chip" id="chipKm">Kwid: 0.0 km</div>
        <div class="chip" id="chipHora">--:--</div>
    </div>
    <video id="cam1" autoplay muted class="cam" style="left:10px"></video>
    <video id="cam2" autoplay muted class="cam" style="right:10px"></video>
    <iframe id="yt" allow="autoplay"></iframe>
</div>

<div id="panel">
    <div id="tabs">
        <div class="tab active" onclick="setTab(this); mostrarChat()">💬 Chat (Gemini)</div>
        <div class="tab" onclick="setTab(this); cargar('gastos')">💰 Gastos</div>
        <div class="tab" onclick="setTab(this); cargar('stats')">📊 Aeropuerto</div>
        <div class="tab" onclick="setTab(this); cargar('kwid')">🔧 Kwid 2026</div>
        <div class="tab" onclick="setTab(this); cargar('familia')">👨‍👩‍👧‍👦 Familia</div>
    </div>
    <div id="chat"></div>
    <div id="ctrl">
        <input id="txt" placeholder="Escribe o habla con Astra..." onkeydown="if(event.key==='Enter')enviar()">
        <div id="mic" class="btn" onclick="toggleMic()">🎤</div>
        <div id="send" class="btn" style="background:#ffd700; color:#020617" onclick="enviar()">➤</div>
    </div>
</div>

<div id="login">
    <div id="box">
        <h2 style="color:#ffd700; font-size: 22px;">ASTRA FR</h2>
        <p style="font-size:11px; color:#94a3b8; margin-top:4px;">Sistema Central de Control Familiar</p>
        <input id="pinInput" class="pin" type="tel" inputmode="numeric" placeholder="PIN" maxlength="4">
        <button id="btnEntrar" type="button" onclick="login()" style="width:100%; padding:14px; border-radius:14px; border:none; background:#ffd700; color:#020617; font-weight:bold; cursor:pointer; font-size:15px;">INGRESAR</button>
        <p id="err" style="color:#f87171; font-size:12px; margin-top:10px"></p>
    </div>
</div>

<script>
let USER = null, KM_TOTAL = 0, WATCH = null, ULT_POS = null, MIC_CONTINUO = false, RECONOCEDOR = null;
const USUARIOS = {
    "2208": { "nombre": "Mario", "corto": "Mario", "rol": "admin" },
    "2345": { "nombre": "Paola", "corto": "Pao", "rol": "esposa" },
    "2011": { "nombre": "Durlandy", "corto": "Dur", "rol": "hijo_15" },
    "2015": { "nombre": "Madelyn", "corto": "Made", "rol": "hija_11" }
};

function add(t, clase = 'astra') {
    let c = document.getElementById('chat');
    let d = document.createElement('div');
    d.className = 'bubble ' + clase;
    d.innerHTML = t;
    c.appendChild(d);
    c.scrollTop = c.scrollHeight;
}

function hablar(texto) {
    let img = document.getElementById('astra');
    img.classList.add('hablando');
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
        let u = new SpeechSynthesisUtterance(texto);
        u.lang = 'es-CO';
        u.rate = 0.95;
        u.onend = () => img.classList.remove('hablando');
        speechSynthesis.speak(u);
    } else {
        setTimeout(() => img.classList.remove('hablando'), 2500);
    }
    add(texto, 'astra');
}

function login() {
    let pin = document.getElementById('pinInput').value.trim();
    if (!pin || !USUARIOS[pin]) {
        document.getElementById('err').innerText = 'PIN inválido';
        return;
    }
    USER = USUARIOS[pin];
    USER.pin = pin;
    KM_TOTAL = parseFloat(localStorage.getItem('astra_km_' + pin) || '0');
    document.getElementById('login').style.display = 'none';
    document.getElementById('chipUser').innerText = USER.nombre + ' (' + USER.rol + ')';
    document.getElementById('chipKm').innerText = 'Kwid: ' + KM_TOTAL.toFixed(1) + ' km';
    add('Sistema: Conectado como ' + USER.nombre, 'sistema');

    if (USER.pin == '2208') hablar('Hola Mario. Gemini activo en mi núcleo. Di buenos días Astra para conectar GPS o pregúntame lo que quieras.');
    else if (USER.pin == '2345') hablar('Hola Pao linda. Ya me conecté con inteligencia real, hablemos de lo que quieras.');
    else if (USER.pin == '2011') hablar('Qué más Dur. Listo para responder tus dudas y explicarte temas bacanos.');
    else if (USER.pin == '2015') hablar('Hola Made hermosa. Lista para charlar contigo.');
    
    iniciarReloj();
}

document.getElementById('pinInput').addEventListener('keydown', function(e) { if (e.key === 'Enter') login(); });

function iniciarReloj() {
    setInterval(() => {
        let el = document.getElementById('chipHora');
        if (el) el.innerText = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    }, 1000);
}

function setTab(el) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
}

async function enviar() {
    let input = document.getElementById('txt');
    let txt = input.value.trim();
    if (!txt) return;
    input.value = '';
    add('Tú: ' + txt, 'yo');
    let low = txt.toLowerCase();

    if (!USER) {
        add('Por favor ingresa tu PIN de seguridad.', 'sistema');
        return;
    }

    // Comandos directos del sistema (Acciones)
    if (low.includes('buenos dias') || low.includes('iniciamos labores')) {
        hablar('Buenos días ' + USER.corto + '. Conectando GPS para auditoría de kilometraje del Kwid 2026.');
        iniciarGPS();
        iniciarCamaras();
        return;
    }

    if (low.includes('gaste') || low.includes('servicio') || low.includes('aeropuerto')) {
        fetch('/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tipo: 'servicio', texto: txt, pin: USER.pin, fecha: new Date().toISOString(), km: KM_TOTAL })
        });
        hablar('Registrado en bitácora ' + USER.corto + ': ' + txt);
        return;
    }

    if (low.includes('pon') && (low.includes('musica') || low.includes('cancion') || low.includes('youtube'))) {
        let q = encodeURIComponent(txt.replace(/pon|musica|cancion|youtube/gi, ''));
        document.getElementById('yt').src = 'https://www.youtube.com/embed?listType=search&list=' + q + '&autoplay=1';
        hablar('Reproduciendo música en segundo plano, ' + USER.corto);
        return;
    }

    if (low.includes('ruta') || low.includes('trazame')) {
        let dest = encodeURIComponent(txt.replace(/trazame|ruta/gi, ''));
        window.open('https://www.google.com/maps/dir/?api=1&destination=' + dest, '_blank');
        hablar('Trazando la mejor ruta disponible hacia ' + txt);
        return;
    }

    // Consulta Inteligente a Gemini API (Para conversación libre, clases, tutoría, etc.)
    add('<i>Astra pensando...</i>', 'sistema');
    try {
        let res = await fetch('/preguntar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: txt, usuario: USER })
        });
        let data = await res.json();
        // Limpiamos el mensaje de "pensando"
        let chat = document.getElementById('chat');
        if (chat.lastChild && chat.lastChild.classList.contains('sistema')) {
            chat.removeChild(chat.lastChild);
        }
        hablar(data.respuesta);
    } catch (e) {
        hablar('Tuve un pequeño problema de señal conectándome a Gemini, Mario.');
    }
}

function iniciarGPS() {
    if (!navigator.geolocation) { hablar('El dispositivo no soporta GPS.'); return; }
    if (WATCH) navigator.geolocation.clearWatch(WATCH);
    WATCH = navigator.geolocation.watchPosition(p => {
        if (ULT_POS) {
            let d = calcKM(ULT_POS.lat, ULT_POS.lon, p.coords.latitude, p.coords.longitude);
            if (d < 0.5) {
                KM_TOTAL += d;
                localStorage.setItem('astra_km_' + USER.pin, KM_TOTAL);
                document.getElementById('chipKm').innerText = 'Kwid: ' + KM_TOTAL.toFixed(1) + ' km';
            }
        }
        ULT_POS = { lat: p.coords.latitude, lon: p.coords.longitude };
    }, null, { enableHighAccuracy: true });
}

function calcKM(lat1, lon1, lat2, lon2) {
    let R = 6371, dLat = (lat2 - lat1) * Math.PI / 180, dLon = (lon2 - lon1) * Math.PI / 180;
    let a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function iniciarCamaras() {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } }).then(s => document.getElementById('cam1').srcObject = s).catch(() => {});
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } }).then(s => document.getElementById('cam2').srcObject = s).catch(() => {});
}

function cargar(tab) {
    fetch('/datos').then(r => r.json()).then(d => {
        let html = '';
        if (tab === 'gastos') {
            html = '<b>💰 Bitácora de Gastos y Servicios</b><br>';
            (d.servicios || []).slice(-8).reverse().forEach(s => html += `• ${new Date(s.fecha).toLocaleTimeString()} - ${s.texto}<br>`);
        } else if (tab === 'stats') {
            let h = {};
            (d.servicios || []).filter(s => /aeropuerto/i.test(s.texto)).forEach(s => {
                let hr = new Date(s.fecha).getHours();
                h[hr] = (h[hr] || 0) + 1;
            });
            let top = Object.entries(h).sort((a, b) => b[1] - a[1])[0];
            html = '<b>📊 Estadísticas Aeropuerto</b><br>' + (top ? `Hora pico: ${top[0]}:00 con ${top[1]} servicios registrados.` : 'Sin datos acumulados.');
        } else if (tab === 'kwid') {
            html = `<b>🔧 Mantenimiento Kwid Intens 2026</b><br>Km actual: ${KM_TOTAL.toFixed(1)} km<br>• 10,000 km: Cambio de aceite y filtro<br>• 20,000 km: Pastillas de freno y líquidos<br>• 30,000 km: Bujías y refrigerante`;
        } else if (tab === 'familia') {
            html = '<b>👨‍👩‍👧‍👦 Mensajes Centrales</b><br>';
            (d.mensajes || []).slice(-6).reverse().forEach(m => html += `• <b>${m.de}:</b> ${m.texto}<br>`);
        }
        document.getElementById('chat').innerHTML = '<div class="bubble astra">' + html + '</div>';
    });
}

function mostrarChat() { document.getElementById('chat').innerHTML = ''; }

function toggleMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Utiliza Google Chrome en Android para habilitar el micrófono.'); return; }
    
    if (!RECONOCEDOR) {
        RECONOCEDOR = new SR();
        RECONOCEDOR.lang = 'es-CO';
        RECONOCEDOR.continuous = true;
        RECONOCEDOR.onstart = () => document.getElementById('mic').classList.add('on');
        RECONOCEDOR.onend = () => {
            if (MIC_CONTINUO) RECONOCEDOR.start();
            else document.getElementById('mic').classList.remove('on');
        };
        RECONOCEDOR.onresult = (e) => {
            let t = e.results[e.results.length - 1][0].transcript;
            document.getElementById('txt').value = t;
            enviar();
        };
    }

    MIC_CONTINUO = !MIC_CONTINUO;
    if (MIC_CONTINUO) RECONOCEDOR.start();
    else RECONOCEDOR.stop();
}
</script>
</body>
</html>
    """

@app.route('/preguntar', methods=['POST'])
def preguntar():
    data = request.json or {}
    mensaje = data.get('mensaje', '')
    usuario = data.get('usuario', {})
    
    respuesta = generar_respuesta_gemini(usuario, mensaje)
    return jsonify({"respuesta": respuesta})

@app.route('/guardar', methods=['POST'])
def guardar():
    data = request.json
    db = get_db()
    if data.get('tipo') == 'servicio': db['servicios'].append(data)
    elif data.get('tipo') == 'mensaje': db.setdefault('mensajes', []).append(data)
    elif data.get('tipo') == 'funcion': db.setdefault('funciones', []).append(data.get('texto'))
    elif data.get('tipo') == 'alerta': db.setdefault('alertas', []).append(data)
    save_db(db)
    return
