import os, json, base64, datetime, traceback, requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__)
DB_FILE = "astra_db.json"

# GEMINI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# SUPABASE - MEMORIA POR 500 AÑOS
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def supabase_save(tabla, data):
    if not SUPABASE_URL or not SUPABASE_KEY: return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabla}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        r = requests.post(url, headers=headers, json=data, timeout=5)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Supabase save error: {e}")
        return False

# GITHUB AUTO-PUSH - FUNCION AUTOPILOTO
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
def auto_push_path(path, context, msg):
    if not GITHUB_TOKEN or not GITHUB_REPO: return False
    try:
        import base64 as b64
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        sha = r.json().get('sha') if r.status_code == 200 else None
        data = {"message": msg, "content": b64.b64encode(context.encode()).decode(), "branch": "main"}
        if sha: data["sha"] = sha
        requests.put(url, headers=headers, json=data, timeout=10)
        return True
    except Exception as e:
        print(f"Github push error: {e}")
        return False

# DB LOCAL
def get_db():
    if not os.path.exists(DB_FILE):
        return {"mensajes": [], "memoria": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"mensajes": [], "memoria": []}

def save_db(d):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)

def gemini_conversa(usuario, mensaje, img_b44=None):
    from google import genai
    from google.genai import types
    import os
    
    if not client:
        return "Falta configurar la GEMINI_API_KEY."
    
    instr = (
        "Eres ASTRA FR v2 FINAL AUTO-ACTUALIZABLE. "
        "Admin Mario (2208). Seba (0709), parcero técnico. Si te dicen 'Astra' respondes. "
        "Conectada a Supabase 500 años y Bóveda. Responde carina voz 2 frases. Si piden más amplias."
    )
    prompt_completo = f"{instr}\n\n{mensaje}"
    
    try:
        if img_b44:
            resp = client.models.generate_content(
                model='models/gemini-3.8-flash',
                contents=[
                    types.Part.from_bytes(
                        data=__import__('base64').b64decode(img_b44),
                        mime_type='image/jpeg',
                    ),
                    prompt_completo
                ]
            )
        else:
            resp = client.models.generate_content(
                model='models/gemini-3.8-flash',
                contents=prompt_completo
            )
        return resp.text
    except Exception as e:
        return f"Error conectando con Gemini: {str(e)}"
        
        
                            
@app.route('/')
def index():
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ASTRA FR - Final Auto-Actualizable</title>
    <style>
        :root { --bg: #020617; --gold: #ffd700; --gold-glow: rgba(255, 215, 0, 0.4); --panel: #0f172a; }
        body { background: var(--bg); color: var(--gold); font-family: system-ui; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        .avatar-container { display: flex; flex-direction: column; align-items: center; padding: 10px; background: var(--panel); border-bottom: 1px solid rgba(255,215,0,0.2); }
        .avatar-frame { width: 90px; height: 90px; border-radius: 50%; border: 2px solid var(--gold); overflow: hidden; box-shadow: 0 0 15px var(--gold-glow); position: relative; }
        .avatar-frame img, .avatar-frame video { width: 100%; height: 100%; object-fit: cover; }
        @keyframes talk { 0% { height: 5px; } 50% { height: 15px; } 100% { height: 5px; } }
        .mouth-position { position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%); width: 20px; height: 5px; background: #ff55a5; border-radius: 20px; display: none; }
        .avatar-frame.talk .mouth-position { display: block; animation: talk 0.18s infinite; }
        /* burbuja ube/movil */
        #uberBubble { position: fixed; bottom: 80px; right: 20px; width: 60px; height: 60px; background: radial-gradient(circle, #0f172a, #ffd700); border: 2px solid var(--gold); border-radius: 50%; box-shadow: 0 0 20px var(--gold-glow); display: flex; justify-content: center; align-items: center; cursor: pointer; z-index: 9998; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        .uberBubble.listening { animation: pulse 1s infinite; border-color: #ef4444; }
        /* chat */
        .chat-container { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
        .message { max-width: 80%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.4; word-break: break-word; }
        .user-msg { background: #1e293b; color: #fff; align-self: flex-end; border: 1px solid rgba(255,215,0,0.3); }
        .astra-msg { background: #0f172a; color: var(--gold); align-self: flex-start; border: 1px solid var(--gold); font-weight: bold; }
        /* input bar */
        .input-bar { display: flex; align-items: center; padding: 10px; background: var(--panel); border-top: 1px solid rgba(255,215,0,0.2); gap: 8px; }
        .btn-action { background: transparent; border: 1px solid var(--gold); color: var(--gold); border-radius: 50%; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; font-size: 18px; cursor: pointer; }
        .chat-input { flex: 1; background: #0f172a; border: 1px solid rgba(255,215,0,0.4); color: #fff; padding: 10px 14px; border-radius: 20px; outline: none; }
        #plusMenu { position: absolute; bottom: 65px; left: 10px; background: #0f172a; border: 1px solid var(--gold); border-radius: 10px; display: none; flex-direction: column; overflow: hidden; z-index: 1000; }
        #plusMenu button { background: none; border: none; color: #fff; padding: 10px 15px; text-align: left; cursor: pointer; border-bottom: 1px solid rgba(255,215,0,0.1); }
        #plusMenu button:hover { background: rgba(255,215,0,0.1); color: var(--gold); }
    </style>
</head>
<body>

    <!-- LOGIN -->
    <div id="loginScreen" style="position:fixed; top:0; left:0; width:100%; height:100%; background:var(--bg); display:flex; flex-direction:column; justify-content:center; align-items:center; z-index:9999;">
        <h2 style="color:var(--gold)">PIN 2208 Mario / 0709 Seba</h2>
        <input type="password" id="pinInput" class="pin-input" maxlength="4" style="background:#0f172a; border:2px solid var(--gold); color:var(--gold); padding:12px; font-size:24px; text-align:center; border-radius:8px; width:150px; outline:none;" placeholder="••••">
        <button onclick="verificarPin()" style="margin-top:15px; background:var(--gold); color:#020617; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; cursor:pointer;">ACCEDER</button>
    </div>

    <!-- AVATAR -->
    <div class="avatar-container">
        <div id="avatarFrame" class="avatar-frame">
            <img id="avatarImg" src="/static/astra.png" alt="Astra" onerror="this.src='https://i.imgur.com/8N4M8RU.png'">
            <video id="avatarVideo" autoplay loop muted playsinline style="display:none"><source src="/static/astra-viva.mp4" type="video/mp4"></video>
            <div class="mouth-position"></div>
        </div>
        <div id="status" style="font-size:12px; color:var(--gold); margin-top:5px;">Sistema en Línea - Memoria Supabase 500 Años</div>
    </div>

    <!-- CHAT -->
    <div id="chat" class="chat-container">
        <div class="message astra-msg">Hola Mario, dime. Activa FR FINAL lista.</div>
    </div>

    <!-- INPUT BAR -->
    <div class="input-bar">
        <div id="plusMenu">
            <button onclick="pickFile()">📁 Archivo</button>
            <button onclick="pickCam()">📷 Cámara</button>
        </div>
        <input type="file" id="fileInput" accept="image/*,video/*,pdf,.doc" style="display:none" onchange="handleFile(this)">
        <input type="file" id="camInput" accept="image/*" capture="environment" style="display:none" onchange="handleFile(this)">
        
        <button class="btn-action" onclick="togglePlus()">+</button>
        <input type="text" id="userInput" class="chat-input" placeholder="Astra o escribe...">
        <button id="micBtn" class="btn-action" onclick="handleMic()">🎤</button>
    </div>

    <!-- BURBUJA -->
    <div id="uberBubble" onclick="hablarHola()" title="Astra Activa">✨</div>

<script>
    let USR = {nombre: "Mario", rol: "admin"}, MODO_CHARLA = false, lastTap = 0, RECON = null, escuchando = false, imgB64 = null;
    const USERS = [{pin: "2208", nombre: "Mario", rol: "admin"}, {pin: "0709", nombre: "Seba", rol: "seba"}, {pin: "2345", nombre: "Paola", rol: "invitado"}];

    function hablar(txt) {
        let f = document.getElementById('avatarFrame'); f.classList.add('talk');
        let vid = document.getElementById('avatarVideo'); if (vid.src) { vid.style.display = 'block'; document.getElementById('avatarImg').style.display = 'none'; }
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            let s = new SpeechSynthesisUtterance(txt); s.lang = 'es-CO'; s.rate = 0.95;
            s.onend = () => f.classList.remove('talk');
            window.speechSynthesis.speak(s);
        } else { setTimeout(() => f.classList.remove('talk'), 2000); }
    }

    function verificarPin() {
        let p = document.getElementById('pinInput').value;
        let u = USERS.find(x => x.pin === p);
        if (u) {
            USR = u;
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('uberBubble').style.display = 'flex';
            hablar(`Hola ${USR.nombre}, dime.`);
        } else { alert('PIN inválido'); }
    }

    function togglePlus() { let m = document.getElementById('plusMenu'); m.style.display = m.style.display === 'flex' ? 'none' : 'flex'; }
    function pickFile() { document.getElementById('fileInput').click(); togglePlus(); }
    function pickCam() { document.getElementById('camInput').click(); togglePlus(); }

    function handleFile(input) {
        if (!input.files || !input.files[0]) return;
        let r = new FileReader();
        r.onload = function(e) {
            imgB64 = e.target.result.split(',')[1];
            addChat("📁 Archivo adjuntado: " + input.files[0].name, 'user-msg');
            enviarConImg(input.files[0].name, imgB64);
        };
        r.readAsDataURL(input.files[0]);
    }

    function handleMic() {
        let now = new Date().getTime();
        if (now - lastTap < 300) { extraTap(); } else { grabarVoz(); }
        lastTap = now;
    }

    function grabarVoz() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if(!SpeechRecognition) { alert('Use Chrome'); return; }
        let rec = new SpeechRecognition(); rec.lang = 'es-CO';
        rec.onresult = (e) => { document.getElementById('userInput').value = e.results[0][0].transcript; enviar(); };
        rec.start();
    }

    function extraTap() {
        MODO_CHARLA = !MODO_CHARLA;
        let bub = document.getElementById('uberBubble'), st = document.getElementById('status');
        if (MODO_CHARLA) {
            bub.classList.add('listening'); st.innerText = "MODO CHARLA - Solo escucha..."; st.style.color = "#ef4444";
            iniciarModoEscuchaPasiva();
        } else {
            bub.classList.remove('listening'); st.innerText = "Sistema en Línea"; st.style.color = "var(--gold)";
        }
    }

    function iniciarModoEscuchaPasiva() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if(!SpeechRecognition) return;
        try {
            let RECON_INT = new SpeechRecognition(); RECON_INT.continuous = true; RECON_INT.interimResults = true;
            RECON_INT.onresult = (e) => {
                let res = e.results[e.results.length - 1][0].transcript.toLowerCase();
                if(res.includes('astra')) { hablar("Hola Mario, dime."); setTimeout(() => { escuchando = true; }, 2000); }
                else if(escuchando && res.trim().length > 4) { document.getElementById('userInput').value = res; enviar(); escuchando = false; }
            };
            RECON_INT.onend = () => { if(MODO_CHARLA) RECON_INT.start(); };
            RECON_INT.start();
        } catch(e){}
    }

    function hablarHola() { hablar(`Hola ${USR.nombre}, dime.`); }

    async function enviar() {
        let input = document.getElementById('userInput'); let txt = input.value.trim(); if (!txt && !imgB64) return;
        if(txt) addChat(txt, 'user-msg');
        input.value = '';

        if(txt.toLowerCase().includes('busca en waze')) {
            let dest = txt.substring(13).trim() || "Aeropuerto Jose Maria Cordova";
            addChat(`🗺️ [Waze Abierto: ${dest}]`, 'astra-msg');
            document.body.innerHTML += `<iframe src="https://embed.waze.com/iframe?zoom=14&lat=6.1645&lon=-75.5862&pin=1" width="100%" height="250"></iframe>`;
            hablar("Abriendo Waze hacia " + dest); return;
        }
        if(txt.toLowerCase().includes('busca en google maps') || txt.toLowerCase().includes('busca en mapas')) {
            let dest = txt.replace('busca en google maps', '').replace('busca en mapas', '').trim() || "Medellin";
            addChat(`🗺️ [Google Maps: ${dest}]`, 'astra-msg');
            document.body.innerHTML += `<iframe src="https://www.google.com/maps/embed/v1/place?key=AIzaSyDummy&q=${encodeURIComponent(dest)}" width="100%" height="250"></iframe>`;
            hablar("Abriendo en Google Maps " + dest); return;
        }
        if(txt.toLowerCase().includes('busca en spotify')) {
            let q = txt.replace('busca en spotify', '').trim() || "Karol G";
            addChat(`🎵 [Spotify: ${q}]`, 'astra-msg');
            document.body.innerHTML += `<iframe src="https://open.spotify.com/embed/search/${encodeURIComponent(q)}" width="100%" height="152" allow="encrypted-media"></iframe>`;
            hablar("Buscando en Spotify " + q); return;
        }
        if(txt.toLowerCase().includes('busca en youtube')) {
            let q = txt.replace('busca en youtube', '').trim() || "Vallenato";
            addChat(`📺 [YouTube: ${q}]`, 'astra-msg');
            document.body.innerHTML += `<iframe src="https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}" width="100%" height="250" allowfullscreen></iframe>`;
            hablar("Buscando en YouTube " + q); return;
        }
        if(txt.toLowerCase().includes('actualizate') || txt.toLowerCase().includes('si autorizo')) {
            addChat("⚡ [Astra ejecutando auto-actualización...]", 'astra-msg');
            try {
                let r = await fetch('/asv/auto-actualizar', {method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({instruccion: txt, usuario: USR})});
                let j = await r.json();
                addChat(j.msg || "Sistema actualizado con éxito.", 'astra-msg');
                hablar("Listo, me auto-actualicé con éxito.");
                if(j.code) eval(j.code);
            } catch(e){ addChat("Error medicina sistema", 'astra-msg'); }
            imgB64 = null; return;
        }
        enviarConImg(txt, imgB64);
        imgB64 = null;
    }

    async function enviarConImg(txt, b64) {
        try {
            let res = await fetch('/preguntar', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mensaje: txt, usuario: USR, imagen: b64})});
            let data = await res.json();
            addChat(data.respuesta, 'astra-msg');
            hablar(data.respuesta);
        } catch(e) { addChat("Error conexion", 'astra-msg'); }
    }

    function addChat(txt, cls) {
        let c = document.getElementById('chat');
        let d = document.createElement('div'); d.className = `message ${cls}`; d.innerText = txt;
        c.appendChild(d); c.scrollTop = c.scrollHeight;
    }

    document.getElementById('userInput').addEventListener('keydown', (e) => { if(e.key === 'Enter') enviar(); });
</script>
</body>
</html>
    """
    return render_template_string(html_content)

@app.route('/preguntar', methods=['POST'])
def preguntar():
    try:
        data = request.json
        mensaje = data.get('mensaje', '')
        usuario = data.get('usuario', {})
        imagen = data.get('imagen', None)
        db = get_db()
        db["mensajes"].append({"de": usuario.get("nombre"), "texto": mensaje, "fecha": datetime.datetime.now().isoformat()})
        save_db(db)
        supabase_save("mensajes", {"de": usuario.get("nombre"), "texto": mensaje, "pin": usuario.get("pin")})
        resp = gemini_conversa(usuario, mensaje, imagen)
        return jsonify({'respuesta': resp})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'respuesta': f'Error en núcleo: {str(e)}'})

@app.route('/datos')
def datos(): return jsonify(get_db())

@app.route('/api/upload-avatar', methods=['POST'])
def upload_avatar():
    try:
        f = request.files.get('file')
        if not f: return jsonify({'ok': False})
        os.makedirs('static', exist_ok=True)
        f.save('static/astra-viva.mp4')
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/asv/auto-actualizar', methods=['POST'])
def auto_actualizar():
    try:
        data = request.json
        inst = data.get('instruccion', '')
        usuario = data.get('usuario', {})
        if usuario.get('rol') != 'admin' and usuario.get('rol') != 'seba':
            return jsonify({'ok': False, 'msg': 'Solo admin.'})
        prompt = "Genera solo código Python limpio para: " + inst + ". Responde solo código entre ```."
        codigo = gemini_conversa(usuario, prompt)
        
        with open("parche_astra.py", "w", encoding="utf-8") as f:
            f.write(f"# Auto-parche {datetime.datetime.now()}\n" + codigo)
        pushed = auto_push_path("parche_auto.py", codigo, "Auto-evaluacion fixed")
        return jsonify({"ok": True, "codigo": codigo, "pushed": pushed, "msg": "Auto parche generado"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/status')
def status():
    return jsonify({'status': 'ONLINE', 'supabase': bool(SUPABASE_URL), 'gemini': bool(GEMINI_API_KEY), 'github': bool(GITHUB_TOKEN), 'worker': 'pid 49'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
