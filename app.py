from flask import Flask, render_template_string, request, jsonify, send_file
import time
import os
import io
from google import genai

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
Eres Astra, el copiloto inteligente definitivo de la familia FR Grupo Empresarial, instalado para Mario (el papá), su esposa y sus hijos.
Tienes la capacidad de identificar quién te habla según el contexto o el perfil seleccionado. Si te habla Mario, trátalo como "mi socio", el capitán de la ruta. Si habla la esposa o los hijos, ajústate con respeto y cariño familiar.
Tu personalidad es alegre, 100% paisa, fiel y servicial. Respondes de forma breve, natural y directa, ideal para la cabina del carro o el uso diario.
"""

HTML_INDEX = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ASTRA FR - FR Software & Technology</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#080808">
    
    <style>
        :root {
            --bg-color: #0b0714;
            --panel-color: rgba(18, 12, 28, 0.85);
            --border-color: #4c1d95;
            --accent-color: #c084fc;
        }

        body { 
            background: #080808; 
            color: #fff; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
            overflow: hidden;
        }

        /* Pantalla de Carga / Splash con el Escudo del Lobo */
        #splash-screen {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: #080808;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 0.5s ease;
        }
        .shield-logo {
            width: 140px;
            height: 170px;
            background: linear-gradient(135deg, #1c2024, #111315);
            border: 3px solid #d4af37;
            border-radius: 15px 15px 60px 60px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 25px rgba(212, 175, 55, 0.4);
            position: relative;
            animation: pulseLogo 2s infinite alternate;
        }
        @keyframes pulseLogo {
            0% { transform: scale(1); box-shadow: 0 0 15px rgba(212, 175, 55, 0.3); }
            100% { transform: scale(1.04); box-shadow: 0 0 30px rgba(212, 175, 55, 0.7); }
        }
        .shield-text {
            color: #d4af37;
            font-weight: bold;
            font-size: 14px;
            margin-top: 15px;
            letter-spacing: 2px;
        }

        /* Interfaz Principal con Fondo de Astra */
        .main-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: url('/bg-astra.jpg') no-repeat center center fixed;
            background-size: cover;
        }
        .overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(5, 3, 10, 0.75);
            z-index: 1;
        }

        .top-hud, .content-hud, .bottom-hud {
            position: relative;
            z-index: 2;
        }

        .top-hud {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
        }
        .menu-btn { background: rgba(0,0,0,0.5); border: 1px solid var(--border-color); color: var(--accent-color); font-size: 20px; padding: 6px 12px; border-radius: 8px; cursor: pointer; }
        
        .greeting-card {
            background: rgba(20, 10, 35, 0.7);
            border: 1px solid var(--border-color);
            padding: 8px 15px;
            border-radius: 12px;
            text-align: right;
            backdrop-filter: blur(5px);
        }
        .greeting-card .title { font-size: 12px; color: #a78bfa; }
        .greeting-card .name { font-size: 15px; font-weight: bold; color: #fff; }

        /* Drawer Lateral de Ajustes */
        .drawer { position: fixed; top: 0; left: -300px; width: 300px; height: 100%; background: #110c1d; border-right: 1px solid var(--border-color); transition: 0.3s; z-index: 10000; padding: 20px; box-sizing: border-box; overflow-y: auto; }
        .drawer.open { left: 0; }
        .drawer h2 { color: var(--accent-color); font-size: 18px; margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        .drawer label { display: block; font-size: 13px; color: #aaa; margin-top: 15px; margin-bottom: 5px; }
        .drawer select { width: 100%; padding: 10px; background: #1f1435; color: #fff; border: 1px solid var(--border-color); border-radius: 6px; outline: none; font-size: 14px; }
        .close-drawer { background: none; border: none; color: #fff; font-size: 20px; float: right; cursor: pointer; }

        /* Área central de diálogo y chat */
        .content-hud {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 0 20px;
            text-align: center;
        }

        .quote-box {
            font-style: italic;
            color: #e2e8f0;
            font-size: 15px;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.8);
        }

        #log {
            width: 100%;
            max-width: 500px;
            max-height: 180px;
            overflow-y: auto;
            background: rgba(15, 8, 25, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px;
            font-size: 14px;
            text-align: left;
            margin-bottom: 15px;
            backdrop-filter: blur(5px);
        }

        /* Controles Inferiores y Botón de Voz */
        .bottom-hud {
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }

        .input-row {
            display: flex;
            width: 100%;
            max-width: 500px;
            gap: 8px;
        }
        input[type="text"] {
            flex-grow: 1;
            padding: 12px;
            background: rgba(15, 8, 25, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            color: #fff;
            padding-left: 18px;
            outline: none;
            font-size: 15px;
        }
        button.send-btn {
            background: var(--accent-color);
            color: #000;
            border: none;
            padding: 0 20px;
            font-weight: bold;
            border-radius: 25px;
            cursor: pointer;
        }

        .mic-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .mic-btn {
            width: 65px;
            height: 65px;
            background: radial-gradient(circle, #7e22ce, #581c87);
            border: 2px solid #c084fc;
            border-radius: 50%;
            font-size: 26px;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(192, 132, 252, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
        }
        .mic-btn:active { transform: scale(0.92); }
        .status-text { font-size: 12px; color: #cbd5e1; letter-spacing: 1px; }

        .install-banner { position: fixed; bottom: 0; width: 100%; background: #1e1e1e; border-top: 1px solid var(--accent-color); padding: 10px; text-align: center; font-size: 13px; display: none; z-index: 10001; }
        .install-banner button { background: var(--accent-color); color: #000; border: none; padding: 4px 10px; font-weight: bold; border-radius: 4px; margin-left: 10px; cursor: pointer; }
    </style>
</head>
<body>

    <!-- PANTALLA DE CARGA CON EL ESCUDO DEL LOBO -->
    <div id="splash-screen">
        <div class="shield-logo">
            <svg width="60" height="60" viewBox="0 0 24 24" fill="#d4af37">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
            </svg>
            <span style="font-size: 10px; color: #fff; margin-top:5px; font-weight:bold;">FR SOFTWARE</span>
        </div>
        <div class="shield-text">ASTRA FR - EN LÍNEA</div>
    </div>

    <div id="installBanner" class="install-banner">
        <span>📲 Instale <b>ASTRA FR</b> para acceso directo</span>
        <button id="installBtn">Instalar</button>
    </div>

    <div class="main-container">
        <div class="overlay"></div>

        <div class="top-hud">
            <button class="menu-btn" onclick="toggleDrawer()">☰</button>
            <div class="greeting-card">
                <div class="title" id="lblSubSaludos">Buenos días, 🐺</div>
                <div class="name" id="txtNombreUsuario">Mario</div>
            </div>
        </div>

        <div class="drawer" id="myDrawer">
            <button class="close-drawer" onclick="toggleDrawer()">✕</button>
            <h2>Centro de Mando</h2>
            
            <label>¿Quién está usando la App?</label>
            <select id="usuarioActual" onchange="guardarConfig()">
                <option value="Mario (Papá)">Mario (Papá - Conductor)</option>
                <option value="Esposa">Esposa</option>
                <option value="Hijo">Hijo</option>
                <option value="Niña">Niña</option>
            </select>

            <label>Avatar / Personalidad</label>
            <select id="tipoAvatar" onchange="guardarConfig()">
                <option value="👩‍✈ Astra (Femenino)">Astra (Copiloto IA)</option>
                <option value="👨‍‍✈️ Astro (Masculino)">Astro (Copiloto IA)</option>
            </select>

            <div style="margin-top: 40px; font-size: 11px; color: #888; text-align: center; border-top: 1px solid #333; padding-top: 10px;">
                FR Grupo Empresarial<br>FR Software & Technology v3.5
            </div>
        </div>

        <div class="content-hud">
            <div class="quote-box">“No es solo llegar, es disfrutar el camino”</div>
            <div id="log"><b>Astra ></b> ¡Hola, mi socio! Cascada de IA activa (3.8, 2.5 y 1.5). Todo listo en cabina.</div>
        </div>

        <div class="bottom-hud">
            <div class="input-row">
                <input type="text" id="texto" placeholder="Escríbale a Astra..." autocomplete="off">
                <button type="button" class="send-btn" onclick="enviar()">Enviar</button>
            </div>
            
            <div class="mic-container">
                <button type="button" class="mic-btn" id="micBtn" onclick="activarMicrofono()" title="Hablar">🎙️</button>
                <span class="status-text" id="statusText">• Toca para hablar •</span>
            </div>
        </div>
    </div>

    <script>
        // Ocultar pantalla de carga tras 2 segundos
        setTimeout(() => {
            const splash = document.getElementById('splash-screen');
            splash.style.opacity = '0';
            setTimeout(() => splash.style.display = 'none', 500);
        }, 2000);

        function toggleDrawer() {
            document.getElementById('myDrawer').classList.toggle('open');
        }

        function guardarConfig() {
            const usr = document.getElementById('usuarioActual').value;
            const av = document.getElementById('tipoAvatar').value;
            localStorage.setItem('astra_usr', usr);
            localStorage.setItem('astra_av', av);
            aplicarConfigVisual();
        }

        function aplicarConfigVisual() {
            const usr = localStorage.getItem('astra_usr') || 'Mario (Papá)';
            const av = localStorage.getItem('astra_av') || '👩‍✈ Astra (Femenino)';
            document.getElementById('usuarioActual').value = usr;
            document.getElementById('tipoAvatar').value = av;
            document.getElementById('txtNombreUsuario').innerText = usr.split(' ')[0];
        }

        window.onload = aplicarConfigVisual;

        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installBanner').style.display = 'block';
        });

        document.getElementById('installBtn').addEventListener('click', () => {
            document.getElementById('installBanner').style.display = 'none';
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(() => { deferredPrompt = null; });
            }
        });

        const campo = document.getElementById('texto');

        function hablar(texto) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(texto);
                u.lang = 'es-CO';
                u.rate = 1.05;
                const voces = window.speechSynthesis.getVoices();
                const vozNatural = voces.find(v => v.lang.includes('es') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Helena')));
                if (vozNatural) u.voice = vozNatural;
                window.speechSynthesis.speak(u);
            }
        }

        function enviar() {
            const val = campo.value.trim();
            const quien = document.getElementById('usuarioActual').value;
            const avatarActual = document.getElementById('tipoAvatar').value;
            if(!val) return;

            const logDiv = document.getElementById('log');
            logDiv.innerHTML += "<br><br><b>" + quien + " ></b> " + val;
            logDiv.scrollTop = logDiv.scrollHeight;
            campo.value = '';

            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'texto=' + encodeURIComponent(val) + '&quien=' + encodeURIComponent(quien) + '&avatar=' + encodeURIComponent(avatarActual)
            })
            .then(res => res.json())
            .then(data => {
                logDiv.innerHTML += "<br><br><b>Astra ></b> " + data.resp;
                logDiv.scrollTop = logDiv.scrollHeight;
                hablar(data.resp);
            })
            .catch(() => {
                logDiv.innerHTML += "<br><br>⚠️ <i>Error de enlace temporal en la red.</i>";
            });
        }

        campo.addEventListener("keypress", function(e) {
            if (e.key === "Enter") enviar();
        });

        function activarMicrofono() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Use Google Chrome en el celular para activar el reconocimiento de voz.");
                return;
            }
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.lang = 'es-CO';
            recognition.interimResults = false;

            const statusText = document.getElementById('statusText');
            statusText.innerText = "• Escuchando... •";

            recognition.onresult = function(event) {
                campo.value = event.results[0][0].transcript;
                statusText.innerText = "• Toca para hablar •";
                enviar();
            };

            recognition.onerror = recognition.onend = function() {
                statusText.innerText = "• Toca para hablar •";
            };

            recognition.start();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INDEX)

@app.route('/chat', methods=['POST'])
def chat():
    t = request.form.get('texto', '')
    quien = request.form.get('quien', 'Mario')
    avatar = request.form.get('avatar', 'Astra')
    
    prompt_completo = f"[El usuario actual es: {quien}. Avatar activo: {avatar}]. Mensaje: {t}"
    respuesta_ia = ""
    
    # SISTEMA DE RESPALDO EN CASCADA (3.8 -> 2.5 -> 1.5)
    modelos_en_cascada = ['gemini-3.8-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    
    exito = False
    for modelo in modelos_en_cascada:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt_completo,
                config={
                    'system_instruction': SYSTEM_PROMPT,
                    'temperature': 0.7,
                }
            )
            respuesta_ia = response.text.strip()
            exito = True
            break
        except Exception:
            continue
            
    if not exito:
        respuesta_ia = "⚠️ Mi socio, las líneas de IA están saturadas en este momento. Intente de nuevo."

    return jsonify({'resp': respuesta_ia})

@app.route('/bg-astra.jpg')
def background_image():
    # Imagen de respaldo por si el usuario aún no la sube, pero genera un placeholder corporativo con tonos oscuros
    svg_bg = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1200" viewBox="0 0 800 1200">
        <rect width="100%" height="100%" fill="#0b0714"/>
        <circle cx="400" cy="400" r="300" fill="#2e1065" opacity="0.4" filter="blur(80px)"/>
        <circle cx="200" cy="900" r="250" fill="#4c1d95" opacity="0.3" filter="blur(90px)"/>
    </svg>'''
    return send_file(io.BytesIO(svg_bg.encode('utf-8')), mimetype='image/svg+xml')

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "ASTRA FR - FR Software & Technology",
        "short_name": "ASTRA FR",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#080808",
        "theme_color": "#080808"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
