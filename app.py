from flask import Flask, render_template_string, request, jsonify
import time
import os
from google import genai

app = Flask(__name__)

# Cliente configurado leyendo explícitamente la llave de las variables de entorno
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
</head>
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#080808">
    
    <style>
        body { background: #080808; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
        
        /* Barra Superior Estilo App Profesional */
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 12px 15px; border-bottom: 1px solid #333; }
        .menu-btn { background: none; border: none; color: #d4af37; font-size: 22px; cursor: pointer; }
        .app-title { color: #d4af37; font-weight: bold; font-size: 16px; letter-spacing: 1px; }
        .avatar-indicator { font-size: 14px; background: #222; padding: 4px 8px; border-radius: 6px; border: 1px solid #444; color: #aaa; }

        /* Menú Lateral Desplegable (Drawer) */
        .drawer { position: fixed; top: 0; left: -260px; width: 260px; height: 100%; background: #111; border-right: 1px solid #333; transition: 0.3s; z-index: 1000; padding: 20px; box-sizing: border-box; }
        .drawer.open { left: 0; }
        .drawer h2 { color: #d4af37; font-size: 18px; margin-top: 0; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .drawer label { display: block; font-size: 13px; color: #888; margin-top: 15px; margin-bottom: 5px; }
        .drawer select { width: 100%; padding: 8px; background: #222; color: #fff; border: 1px solid #444; border-radius: 5px; outline: none; }
        .close-drawer { background: none; border: none; color: #fff; font-size: 20px; float: right; cursor: pointer; }

        /* Área de Chat y Pantalla */
        .main-content { display: flex; flex-direction: column; flex-grow: 1; padding: 15px; overflow: hidden; }
        
        #log { font-size: 16px; color: #d4af37; background: #121212; padding: 15px; border-radius: 10px; border: 1px solid #333; width: 100%; max-width: 650px; margin: 0 auto; line-height: 1.4; text-align: left; flex-grow: 1; overflow-y: auto; box-sizing: border-box; }
        
        .box { margin-top: 15px; display: flex; justify-content: center; gap: 8px; width: 100%; max-width: 650px; margin-left: auto; margin-right: auto; }
        input { padding: 12px; flex-grow: 1; font-size: 16px; border-radius: 8px; border: 1px solid #444; background: #181818; color: #fff; outline: none; }
        input:focus { border-color: #d4af37; }
        button.send-btn { padding: 12px 18px; font-size: 15px; background: #d4af37; color: #000; border: none; font-weight: bold; cursor: pointer; border-radius: 8px; }
        button.mic-btn { padding: 12px 16px; font-size: 18px; background: #1a1a1a; border: 1px solid #60a5fa; color: #60a5fa; border-radius: 8px; cursor: pointer; }
        
        .install-banner { background: #1e1e1e; border: 1px solid #d4af37; padding: 10px; text-align: center; font-size: 13px; display: none; }
        .install-banner button { background: #d4af37; color: #000; border: none; padding: 4px 10px; font-weight: bold; border-radius: 4px; margin-left: 10px; cursor: pointer; }
    </style>
</head>
<body>

    <div id="installBanner" class="install-banner">
        <span>📲 Instalar <b>ASTRA FR</b> en el celular</span>
        <button id="installBtn">Instalar</button>
    </div>

    <!-- Barra Superior -->
    <div class="top-bar">
        <button class="menu-btn" onclick="toggleDrawer()">☰</button>
        <div class="app-title">ASTRA FR <span style="font-size:10px; color:#888;">(FR Software)</span></div>
        <div class="avatar-indicator" id="lblUsuario">Mario</div>
    </div>

    <!-- Menú Lateral (Configuración e Independencia) -->
    <div class="drawer" id="myDrawer">
        <button class="close-drawer" onclick="toggleDrawer()">✕</button>
        <h2>Configuración</h2>
        
        <label>¿Quién está usando la App?</label>
        <select id="usuarioActual" onchange="actualizarPerfilText()">
            <option value="Mario (Papá)">Mario (Papá - Conductor)</option>
            <option value="Esposa">Esposa</option>
            <option value="Hijo">Hijo</option>
            <option value="Niña">Niña</option>
        </select>

        <label>Voz / Avatar de Astra</label>
        <select id="tipoVoz">
            <option value="es-CO">Operadora Femenina (Latina)</option>
            <option value="es-ES">Operadora Estándar</option>
        </select>

        <div style="margin-top: 30px; font-size: 11px; color: #666; text-align: center;">
            FR Software & Technology<br>Innovation at your command
        </div>
    </div>

    <!-- Pantalla Principal -->
    <div class="main-content">
        <div id="log"><b>Astra ></b> ¡Sistema en línea, mi socio! Despliegue el menú ☰ arriba para cambiar de perfil o toque el micrófono.</div>

        <div class="box">
            <button type="button" class="mic-btn" id="micBtn" onclick="activarMicrofono()" title="Hablar">🎙️</button>
            <input type="text" id="texto" placeholder="Escríbale a Astra..." autocomplete="off">
            <button type="button" class="send-btn" onclick="enviar()">Enviar</button>
        </div>
    </div>

    <script>
        // Menú lateral
        function toggleDrawer() {
            document.getElementById('myDrawer').classList.toggle('open');
        }

        function actualizarPerfilText() {
            const select = document.getElementById('usuarioActual');
            document.getElementById('lblUsuario').innerText = select.value.split(' ')[0];
        }

        // PWA Install Banner
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
                u.lang = document.getElementById('tipoVoz').value;
                u.rate = 1.05;
                window.speechSynthesis.speak(u);
            }
        }

        function enviar() {
            const val = campo.value.trim();
            const quien = document.getElementById('usuarioActual').value;
            if(!val) return;

            const logDiv = document.getElementById('log');
            logDiv.innerHTML += "<br><br><b>" + quien + " ></b> " + val;
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
                logDiv.innerHTML += "<br><br>⚠️ <i>Error de enlace temporal.</i>";
            });
        }

        campo.addEventListener("keypress", function(e) {
            if (e.key === "Enter") enviar();
        });

        function activarMicrofono() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Use Google Chrome en el celular para el micrófono.");
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
    
    prompt_completo = f"[El usuario actual que te está hablando es: {quien}]. Mensaje: {t}"

    respuesta_ia = ""
    intentos = 3
    
    for intento in range(intentos):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt_completo,
                config={
                    'system_instruction': SYSTEM_PROMPT,
                    'temperature': 0.7,
                }
            )
            respuesta_ia = response.text.strip()
            break
        except Exception as e:
            if intento < intentos - 1:
                time.sleep(1)
            else:
                respuesta_ia = f"⚠️ Error técnico: {str(e)}"

    return jsonify({'resp': respuesta_ia})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
