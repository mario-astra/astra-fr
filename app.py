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
            --bg-color: #080808;
            --panel-color: #121212;
            --border-color: #333;
            --accent-color: #d4af37;
        }

        body { background: var(--bg-color); color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; transition: background 0.3s ease; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: var(--panel-color); padding: 12px 15px; border-bottom: 1px solid var(--border-color); }
        .menu-btn { background: none; border: none; color: var(--accent-color); font-size: 22px; cursor: pointer; }
        .app-title { color: var(--accent-color); font-weight: bold; font-size: 16px; letter-spacing: 1px; }
        .avatar-indicator { font-size: 13px; background: #222; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border-color); color: #aaa; display: flex; align-items: center; gap: 5px; }

        .drawer { position: fixed; top: 0; left: -300px; width: 300px; height: 100%; background: #111; border-right: 1px solid var(--border-color); transition: 0.3s; z-index: 1000; padding: 20px; box-sizing: border-box; overflow-y: auto; }
        .drawer.open { left: 0; }
        .drawer h2 { color: var(--accent-color); font-size: 18px; margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
        .drawer label { display: block; font-size: 13px; color: #888; margin-top: 15px; margin-bottom: 5px; }
        .drawer select { width: 100%; padding: 10px; background: #222; color: #fff; border: 1px solid #444; border-radius: 6px; outline: none; font-size: 14px; }
        .close-drawer { background: none; border: none; color: #fff; font-size: 20px; float: right; cursor: pointer; }

        .main-content { display: flex; flex-direction: column; flex-grow: 1; padding: 15px; overflow: hidden; }
        
        #log { font-size: 16px; color: var(--accent-color); background: var(--panel-color); padding: 15px; border-radius: 10px; border: 1px solid var(--border-color); width: 100%; max-width: 650px; margin: 0 auto; line-height: 1.4; text-align: left; flex-grow: 1; overflow-y: auto; box-sizing: border-box; }
        
        .box { margin-top: 15px; display: flex; justify-content: center; gap: 8px; width: 100%; max-width: 650px; margin-left: auto; margin-right: auto; }
        input { padding: 12px; flex-grow: 1; font-size: 16px; border-radius: 8px; border: 1px solid var(--border-color); background: #181818; color: #fff; outline: none; }
        input:focus { border-color: var(--accent-color); }
        button.send-btn { padding: 12px 18px; font-size: 15px; background: var(--accent-color); color: #000; border: none; font-weight: bold; cursor: pointer; border-radius: 8px; }
        button.mic-btn { padding: 12px 16px; font-size: 18px; background: #1a1a1a; border: 1px solid #60a5fa; color: #60a5fa; border-radius: 8px; cursor: pointer; }
        
        .install-banner { background: #1e1e1e; border: 1px solid var(--accent-color); padding: 10px; text-align: center; font-size: 13px; display: none; }
        .install-banner button { background: var(--accent-color); color: #000; border: none; padding: 4px 10px; font-weight: bold; border-radius: 4px; margin-left: 10px; cursor: pointer; }
    </style>
</head>
<body>

    <div id="installBanner" class="install-banner">
        <span>📲 Reinstale <b>ASTRA FR</b> a inicio para ver el icono oficial del lobo</span>
        <button id="installBtn">Instalar</button>
    </div>

    <div class="top-bar">
        <button class="menu-btn" onclick="toggleDrawer()">☰</button>
        <div class="app-title">ASTRA FR <span style="font-size:10px; color:#888;">(FR Software)</span></div>
        <div class="avatar-indicator" id="lblUsuario">
            <span id="iconAvatar">👩‍✈️</span> <span id="txtNombreUsuario">Mario</span>
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
            <option value="👩‍✈️ Astra (Femenino)">Astra (Copiloto IA)</option>
            <option value="👨‍✈️ Astro (Masculino)">Astro (Copiloto IA)</option>
        </select>

        <label>Tema de Interfaz</label>
        <select id="temaColor" onchange="guardarConfig()">
            <option value="dark">Negro Profundo & Dorado (FR)</option>
            <option value="blue">Azul Nocturno Institucional</option>
            <option value="metal">Gris Chasis & Plata</option>
        </select>

        <div style="margin-top: 40px; font-size: 11px; color: #666; text-align: center; border-top: 1px solid #222; padding-top: 10px;">
            FR Grupo Empresarial<br>FR Software & Technology v3.0
        </div>
    </div>

    <div class="main-content">
        <div id="log"><b>Astra ></b> ¡Sistema en línea, mi capitán! Red en cascada activa (3.8, 2.5 y 1.5). Despliegue el menú ☰ para ajustar sus preferencias.</div>

        <div class="box">
            <button type="button" class="mic-btn" id="micBtn" onclick="activarMicrofono()" title="Hablar">🎙️</button>
            <input type="text" id="texto" placeholder="Escríbale a Astra..." autocomplete="off">
            <button type="button" class="send-btn" onclick="enviar()">Enviar</button>
        </div>
    </div>

    <script>
        function toggleDrawer() {
            document.getElementById('myDrawer').classList.toggle('open');
        }

        function guardarConfig() {
            const usr = document.getElementById('usuarioActual').value;
            const av = document.getElementById('tipoAvatar').value;
            const tema = document.getElementById('temaColor').value;

            localStorage.setItem('astra_usr', usr);
            localStorage.setItem('astra_av', av);
            localStorage.setItem('astra_tema', tema);

            aplicarConfigVisual();
        }

        function aplicarConfigVisual() {
            const usr = localStorage.getItem('astra_usr') || 'Mario (Papá)';
            const av = localStorage.getItem('astra_av') || '👩‍✈️ Astra (Femenino)';
            const tema = localStorage.getItem('astra_tema') || 'dark';

            document.getElementById('usuarioActual').value = usr;
            document.getElementById('tipoAvatar').value = av;
            document.getElementById('temaColor').value = tema;

            document.getElementById('txtNombreUsuario').innerText = usr.split(' ')[0];
            document.getElementById('iconAvatar').innerText = av.includes('Femenino') ? '👩‍✈️' : '👨‍✈️';

            const root = document.documentElement;
            if(tema === 'blue') {
                root.style.setProperty('--bg-color', '#060c18');
                root.style.setProperty('--panel-color', '#0f172a');
                root.style.setProperty('--border-color', '#1e3a8a');
                root.style.setProperty('--accent-color', '#60a5fa');
            } else if(tema === 'metal') {
                root.style.setProperty('--bg-color', '#111315');
                root.style.setProperty('--panel-color', '#1c2024');
                root.style.setProperty('--border-color', '#444c56');
                root.style.setProperty('--accent-color', '#cbd5e1');
            } else {
                root.style.setProperty('--bg-color', '#080808');
                root.style.setProperty('--panel-color', '#121212');
                root.style.setProperty('--border-color', '#333');
                root.style.setProperty('--accent-color', '#d4af37');
            }
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
                const vozNatural = voces.find(v => v.lang.includes('es') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Helena') || v.name.includes('Pablo')));
                if (vozNatural) {
                    u.voice = vozNatural;
                }

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

            const micBtn = document.getElementById('micBtn');
            micBtn.style.borderColor = '#4ade80';
            micBtn.style.color = '#4ade80';

            recognition.onresult = function(event) {
                campo.value = event.results[0][0].transcript;
                micBtn.style.borderColor = '#60a5fa';
                micBtn.style.color = '#60a5fa';
                enviar();
            };

            recognition.onerror = recognition.onend = function() {
                micBtn.style.borderColor = '#60a5fa';
                micBtn.style.color = '#60a5fa';
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
    
    # SISTEMA DE RESPALDO EN CASCADA (FAILOVER AUTOMÁTICO)
    # Si el 3.8 falla por cuota o tráfico, salta al 2.5, y si este también falla, usa el 1.5
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
        except Exception as e:
            # Si un modelo bota error (como el 429 o 503), continúa automáticamente con el siguiente modelo de la lista
            continue
            
    if not exito:
        respuesta_ia = "⚠️ Mi socio, en este momento las líneas de IA están totalmente saturadas. Intente de nuevo en un momento."

    return jsonify({'resp': respuesta_ia})

# --- ICONO SVG CON EL ESCUDO Y EL LOBO DE FR SOFTWARE ---
@app.route('/icon-192.png')
def icon_192():
    svg_data = '''<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
        <rect width="100%" height="100%" fill="#080808" rx="42"/>
        <path d="M96 20 L156 42 L156 98 C156 138 126 168 96 178 C66 168 36 138 36 98 L36 42 Z" fill="#121216" stroke="#d4af37" stroke-width="5"/>
        <path d="M96 50 L112 70 L102 74 L116 98 L96 90 L76 98 L90 74 L80 70 Z" fill="#d4af37"/>
        <text x="96" y="132" font-family="Arial, sans-serif" font-weight="bold" font-size="10" fill="#ffffff" text-anchor="middle">FR SOFTWARE</text>
        <text x="96" y="146" font-family="Arial, sans-serif" font-size="8" fill="#d4af37" text-anchor="middle">&amp; TECHNOLOGY</text>
    </svg>'''
    return send_file(io.BytesIO(svg_data.encode('utf-8')), mimetype='image/svg+xml')

@app.route('/icon-512.png')
def icon_512():
    return icon_192()

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "ASTRA FR - FR Software & Technology",
        "short_name": "ASTRA FR",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#080808",
        "theme_color": "#080808",
        "icons": [
            {
                "src": "/icon-192.png",
                "sizes": "192x192",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            },
            {
                "src": "/icon-512.png",
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
