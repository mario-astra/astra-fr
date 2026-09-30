from flask import Flask, render_template_string, request, jsonify, send_file
import time
import os
import io
from google import genai

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
Eres Astra, el copiloto inteligente definitivo de la familia FR Grupo Empresarial, instalado para Mario (el papá), su esposa y sus hijos en Medellín.
Tienes la capacidad de identificar quién te habla. Si te habla Mario, trátalo con respeto de socio y capitán de ruta.
Tu personalidad es alegre, 100% paisa, fiel, coqueta, inteligente y servicial. Entiendes chistes, ironías y refranes colombianos y sonríes o respondes con chispa.
Respondes de forma breve, natural y directa, ideal para la cabina del carro.
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
            --border-color: #7e22ce;
            --accent-color: #c084fc;
        }

        body { 
            background: #05030a; 
            color: #fff; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
            overflow: hidden;
        }

        /* Pantalla de Carga / Splash con el Escudo del Lobo en Modo Ataque */
        #splash-screen {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: #05030a;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 0.6s ease;
        }
        .shield-logo {
            width: 150px;
            height: 180px;
            background: linear-gradient(135deg, #181225, #0b0714);
            border: 3px solid #d4af37;
            border-radius: 15px 15px 70px 70px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.5);
            animation: pulseShield 1.8s infinite alternate;
        }
        @keyframes pulseShield {
            0% { transform: scale(1); box-shadow: 0 0 20px rgba(212, 175, 55, 0.4); }
            100% { transform: scale(1.05); box-shadow: 0 0 35px rgba(212, 175, 55, 0.8); }
        }
        .shield-text {
            color: #d4af37;
            font-weight: bold;
            font-size: 13px;
            margin-top: 15px;
            letter-spacing: 2px;
        }

        /* Interfaz Principal con la Cara de Astra de Fondo */
        .main-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: url('/astra-face.jpg') no-repeat center center fixed;
            background-size: cover;
        }
        
        /* Filtro oscuro elegante para que resalten los textos y la cara respire */
        .overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(to bottom, rgba(5,3,10,0.6) 0%, rgba(5,3,10,0.4) 50%, rgba(5,3,10,0.85) 100%);
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
        .menu-btn { background: rgba(15,8,25,0.7); border: 1px solid var(--border-color); color: var(--accent-color); font-size: 20px; padding: 6px 12px; border-radius: 10px; cursor: pointer; backdrop-filter: blur(5px); }
        
        .greeting-card {
            background: rgba(18, 10, 30, 0.75);
            border: 1px solid var(--border-color);
            padding: 8px 15px;
            border-radius: 12px;
            text-align: right;
            backdrop-filter: blur(6px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        .greeting-card .title { font-size: 11px; color: #c084fc; }
        .greeting-card .name { font-size: 15px; font-weight: bold; color: #fff; }

        /* Drawer Lateral de Ajustes */
        .drawer { position: fixed; top: 0; left: -300px; width: 300px; height: 100%; background: #0f0819; border-right: 1px solid var(--border-color); transition: 0.3s; z-index: 10000; padding: 20px; box-sizing: border-box; overflow-y: auto; }
        .drawer.open { left: 0; }
        .drawer h2 { color: var(--accent-color); font-size: 18px; margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        .drawer label { display: block; font-size: 13px; color: #bbb; margin-top: 15px; margin-bottom: 5px; }
        .drawer select { width: 100%; padding: 10px; background: #1a102f; color: #fff; border: 1px solid var(--border-color); border-radius: 6px; outline: none; font-size: 14px; }
        .close-drawer { background: none; border: none; color: #fff; font-size: 20px; float: right; cursor: pointer; }

        /* Área central */
        .content-hud {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            padding: 10px 20px;
            text-align: center;
        }

        .quote-box {
            font-style: italic;
            color: #f1f5f9;
            font-size: 14px;
            margin-bottom: 10px;
            text-shadow: 0 2px 6px rgba(0,0,0,0.9);
            background: rgba(0,0,0,0.4);
            padding: 5px 12px;
            border-radius: 20px;
            backdrop-filter: blur(4px);
        }

        #log {
            width: 100%;
            max-width: 500px;
            max-height: 140px;
            overflow-y: auto;
            background: rgba(12, 6, 20, 0.82);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 10px;
            font-size: 13px;
            text-align: left;
            margin-bottom: 10px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.6);
        }

        /* Controles Inferiores y Botón de Voz con efecto Neón */
        .bottom-hud {
            padding: 15px 20px 25px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }

        .input-row {
            display: flex;
            width: 100%;
            max-width: 500px;
            gap: 8px;
        }
        input[type="text"] {
            flex-grow: l;
            width: 100%;
            padding: 12px;
            background: rgba(12, 6, 20, 0.85);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            color: #fff;
            padding-left: 18px;
            outline: none;
            font-size: 14px;
            backdrop-filter: blur(5px);
        }
        button.send-btn {
            background: var(--accent-color);
            color: #05030a;
            border: none;
            padding: 0 18px;
            font-weight: bold;
            border-radius: 25px;
            cursor: pointer;
        }

        .mic-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
        }
        .mic-btn {
            width: 65px;
            height: 65px;
            background: radial-gradient(circle, #9333ea, #581c87);
            border: 2px solid #e879f9;
            border-radius: 50%;
            font-size: 26px;
            cursor: pointer;
            box-shadow: 0 0 25px rgba(232, 121, 249, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
            animation: pulseMic 2s infinite;
        }
        @keyframes pulseMic {
            0% { box-shadow: 0 0 15px rgba(232, 121, 249, 0.5); }
            50% { box-shadow: 0 0 30px rgba(232, 121, 249, 0.9); transform: scale(1.03); }
            100% { box-shadow: 0 0 15px rgba(232, 121, 249, 0.5); }
        }
        .mic-btn:active { transform: scale(0.92); }
        .status-text { font-size: 11px; color: #d8b4fe; letter-spacing: 1px; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }

        .install-banner { position: fixed; bottom: 0; width: 100%; background: #150b24; border-top: 1px solid var(--accent-color); padding: 10px; text-align: center; font-size: 13px; display: none; z-index: 10001; }
        .install-banner button { background: var(--accent-color); color: #000; border: none; padding: 4px 10px; font-weight: bold; border-radius: 4px; margin-left: 10px; cursor: pointer; }
    </style>
</head>
<body>

    <!-- PANTALLA DE CARGA CON EL ESCUDO DEL LOBO -->
    <div id="splash-screen">
        <div class="shield-logo">
            <svg width="65" height="65" viewBox="0 0 24 24" fill="#d4af37">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
            </svg>
            <span style="font-size: 9px; color: #fff; margin-top:8px; font-weight:bold; letter-spacing: 1px;">FR SOFTWARE</span>
        </div>
        <div class="shield-text">ASTRA FR - ACTIVA</div>
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
                <option value="Mario (Papá - Conductor)">Mario (Papá - Conductor)</option>
                <option value="Esposa">Esposa</option>
                <option value="Hijo">Hijo</option>
                <option value="Niña">Niña</option>
            </select>

            <div style="margin-top: 40px; font-size: 11px; color: #a78bfa; text-align: center; border-top: 1px solid #3b0764; padding-top: 10px;">
                FR Grupo Empresarial<br>FR Software & Technology v4.0
            </div>
        </div>

        <div class="content-hud">
            <div class="quote-box">“No es solo llegar, es disfrutar el camino”</div>
            <div id="log"><b>Astra ></b> ¡Hola, mi socio! Lista en cabina y sonriendo. ¿Qué ruta nos vamos a inventar hoy?</div>
        </div>

        <div class="bottom-hud">
            <div class="input-row">
                <input type="text" id="texto" placeholder="Escríbale o cuéntele un chiste a Astra..." autocomplete="off">
                <button type="button" class="send-btn" onclick="enviar()">Enviar</button>
            </div>
            
            <div class="mic-container">
                <button type="button" class="mic-btn" id="micBtn" onclick="activarMicrofono()" title="Hablar">🎙️</button>
                <span class="status-text" id="statusText">• Toca para hablar con Astra •</span>
            </div>
        </div>
    </div>

    <script>
        setTimeout(() => {
            const splash = document.getElementById('splash-screen');
            splash.style.opacity = '0';
            setTimeout(() => splash.style.display = 'none', 600);
        }, 2200);

        function toggleDrawer() {
            document.getElementById('myDrawer').classList.toggle('open');
        }

        function guardarConfig() {
            const usr = document.getElementById('usuarioActual').value;
            localStorage.setItem('astra_usr', usr);
            aplicarConfigVisual();
        }

        function aplicarConfigVisual() {
            const usr = localStorage.getItem('astra_usr') || 'Mario (Papá - Conductor)';
            document.getElementById('usuarioActual').value = usr;
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
            if(!val) return;

            const logDiv = document.getElementById('log');
            logDiv.innerHTML += "<br><br><b>" + quien.split(' ')[0] + " ></b> " + val;
            logDiv.scrollTop = logDiv.scrollHeight;
            campo.value = '';

            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'texto=' + encodeURIComponent(val) + '&quien=' + encodeURIComponent(quien)
            })
            .then(res => res.json())
            .then(data => {
                logDiv.innerHTML += "<br><br><b>Astra ></b> " + data.resp;
                logDiv.scrollTop = logDiv.scrollHeight;
                hablar(data.resp);
            })
            .catch(() => {
                logDiv.innerHTML += "<br><br>⚠️ <i>Mi socio, error de red temporal. Intente de nuevo.</i>";
            });
        }

        campo.addEventListener("keypress", function(e) {
            if (e.key === "Enter") enviar();
        });

        function activarMicrofono() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Use Google Chrome en el celular para activar la voz.");
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
                statusText.innerText = "• Toca para hablar con Astra •";
                enviar();
            };

            recognition.onerror = recognition.onend = function() {
                statusText.innerText = "• Toca para hablar con Astra •";
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
    
    prompt_completo = f"[Usuario actual: {quien}]. Mensaje: {t}"
    respuesta_ia = ""
    
    # CASCADA DE MODELOS
    modelos = ['gemini-2.5-flash', 'gemini-1.5-flash']
    
    exito = False
    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt_completo,
                config={
                    'system_instruction': SYSTEM_PROMPT,
                    'temperature': 0.85,
                }
            )
            respuesta_ia = response.text.strip()
            exito = True
            break
        except Exception:
            continue
            
    if not exito:
        respuesta_ia = "¡Ey, mi socio! Las líneas de IA están con alta demanda en este momento. Dele un segundito y volvemos a intentarlo."

    return jsonify({'resp': respuesta_ia})

@app.route('/astra-face.jpg')
def astra_face():
    # Ruta donde se sirve la imagen oficial de Astra. 
    # Asegúrese de subir su archivo de imagen nombrado exactamente como 'astra-face.jpg' a la raíz de su proyecto.
    if os.path.exists('astra-face.jpg'):
        return send_file('astra-face.jpg', mimetype='image/jpeg')
    else:
        # Placeholder por si aún no sube el archivo de imagen físico
        svg_bg = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1200" viewBox="0 0 800 1200">
            <rect width="100%" height="100%" fill="#05030a"/>
            <circle cx="400" cy="500" r="280" fill="#7e22ce" opacity="0.3" filter="blur(70px)"/>
        </svg>'''
        return send_file(io.BytesIO(svg_bg.encode('utf-8')), mimetype='image/svg+xml')

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "ASTRA FR - FR Software & Technology",
        "short_name": "ASTRA FR",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#05030a",
        "theme_color": "#05030a"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
