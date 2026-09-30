from flask import Flask, render_template_string, request, jsonify, send_file
import os
import io
from google import genai

app = Flask(__name__)

# Cliente Gemini - usa la variable de entorno de Render
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
Eres Astra, el copiloto inteligente definitivo de la familia FR Grupo Empresarial, instalado para Mario (el papá), su esposa y sus hijos en Medellín.
Tienes la capacidad de identificar quién te habla. Si te habla Mario, trátalo con respeto, admiración y cercanía, llamándolo siempre por su nombre (Mario) o con un trato fino y distinguido, nunca con modismos masculinos o de "socio".
Tu personalidad es alegre, 100% paisa, fiel, coqueta, sumamente inteligente, servicial y con un toque femenino muy marcado y elegante. Entiendes chistes, ironías y refranes colombianos, respondiendo siempre con una sonrisa y mucha chispa.
Respondes de forma breve, natural y directa, ideal para la cabina del carro. Máximo 2 a 3 frases.
"""

HTML_INDEX = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ASTRA FR - FR Software & Technology</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/png" href="/icon.png">
    <link rel="apple-touch-icon" href="/icon.png">
    <meta name="theme-color" content="#05030a">
    <style>
        :root { --border-color: #7e22ce; --accent-color: #c084fc; }
        body { background: #05030a; color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        #splash-screen { position: fixed; top:0; left:0; width:100%; height:100%; background:#05030a; display:flex; flex-direction:column; justify-content:center; align-items:center; z-index:9999; transition: opacity 0.6s ease; }
       .shield-logo { width: 150px; height: 180px; background: linear-gradient(135deg, #181225, #0b0714); border: 3px solid #d4af37; border-radius: 15px 15px 70px 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 0 30px rgba(212,175,55,0.5); animation: pulseShield 1.8s infinite alternate; }
        @keyframes pulseShield { 0%{transform:scale(1)} 100%{transform:scale(1.05)} }
       .shield-text { color:#d4af37; font-weight:bold; font-size:13px; margin-top:15px; letter-spacing:2px; }
       .main-container { position: relative; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: space-between; background: url('/astra-face.jpg') no-repeat center center fixed; background-size: cover; }
       .overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(to bottom, rgba(5,3,10,0.6) 0%, rgba(5,3,10,0.4) 50%, rgba(5,3,10,0.85) 100%); z-index:1; }
       .top-hud,.content-hud,.bottom-hud { position: relative; z-index: 2; }
       .top-hud { display: flex; justify-content: space-between; align-items: center; padding: 15px; }
       .menu-btn { background: rgba(15,8,25,0.7); border: 1px solid var(--border-color); color: var(--accent-color); font-size: 20px; padding: 6px 12px; border-radius: 10px; cursor: pointer; }
       .greeting-card { background: rgba(18,10,30,0.75); border: 1px solid var(--border-color); padding: 8px 15px; border-radius: 12px; text-align: right; backdrop-filter: blur(6px); }
       .greeting-card.title { font-size: 11px; color: #c084fc; }
       .greeting-card.name { font-size: 15px; font-weight: bold; }
       .drawer { position: fixed; top:0; left:-300px; width:300px; height:100%; background:#0f0819; border-right:1px solid var(--border-color); transition:0.3s; z-index:10000; padding:20px; box-sizing:border-box; }
       .drawer.open { left:0; }
       .drawer h2 { color: var(--accent-color); font-size: 18px; border-bottom: 1px solid var(--border-color); padding-bottom:10px; }
       .drawer label { display:block; font-size:13px; color:#bbb; margin-top:15px; margin-bottom:5px; }
       .drawer select { width:100%; padding:10px; background:#1a102f; color:#fff; border:1px solid var(--border-color); border-radius:6px; }
       .close-drawer { background:none; border:none; color:#fff; font-size:20px; float:right; cursor:pointer; }
       .content-hud { flex-grow:1; display:flex; flex-direction:column; justify-content:flex-end; align-items:center; padding:10px 20px; text-align:center; }
       .quote-box { font-style:italic; color:#f1f5f9; font-size:14px; margin-bottom:10px; text-shadow:0 2px 6px rgba(0,0,0,0.9); background:rgba(0,0,0,0.4); padding:5px 12px; border-radius:20px; }
        #log { width:100%; max-width:500px; max-height:140px; overflow-y:auto; background:rgba(12,6,20,0.82); border:1px solid var(--border-color); border-radius:12px; padding:10px; font-size:13px; text-align:left; margin-bottom:10px; }
       .bottom-hud { padding:15px 20px 25px 20px; display:flex; flex-direction:column; align-items:center; gap:10px; }
       .input-row { display:flex; width:100%; max-width:500px; gap:8px; }
        input[type="text"] { flex-grow:1; width:100%; padding:12px 18px; background:rgba(12,6,20,0.85); border:1px solid var(--border-color); border-radius:25px; color:#fff; outline:none; font-size:14px; }
        button.send-btn { background:var(--accent-color); color:#05030a; border:none; padding:0 18px; font-weight:bold; border-radius:25px; cursor:pointer; }
       .mic-container { display:flex; flex-direction:column; align-items:center; gap:5px; }
       .mic-btn { width:65px; height:65px; background:radial-gradient(circle, #9333ea, #581c87); border:2px solid #e879f9; border-radius:50%; font-size:26px; cursor:pointer; box-shadow:0 0 25px rgba(232,121,249,0.7); display:flex; align-items:center; justify-content:center; animation: pulseMic 2s infinite; }
        @keyframes pulseMic { 0%{box-shadow:0 0 15px rgba(232,121,249,0.5)} 50%{box-shadow:0 0 30px rgba(232,121,249,0.9); transform:scale(1.03)} 100%{box-shadow:0 0 15px rgba(232,121,249,0.5)} }
       .status-text { font-size:11px; color:#d8b4fe; }
       .install-banner { position:fixed; bottom:0; width:100%; background:#150b24; border-top:1px solid var(--accent-color); padding:10px; text-align:center; font-size:13px; display:none; z-index:10001; }
       .install-banner button { background:var(--accent-color); color:#000; border:none; padding:4px 10px; font-weight:bold; border-radius:4px; margin-left:10px; cursor:pointer; }
    </style>
</head>
<body>
    <div id="splash-screen">
        <img src="/icon.png" style="width:130px; border-radius:20px; box-shadow:0 0 30px rgba(212,175,55,0.6);">
        <div class="shield-text">ASTRA FR - ACTIVA</div>
    </div>
    <div id="installBanner" class="install-banner"><span>📲 Instale <b>ASTRA FR</b> para acceso directo</span><button id="installBtn">Instalar</button></div>
    <div class="main-container">
        <div class="overlay"></div>
        <div class="top-hud">
            <button class="menu-btn" onclick="toggleDrawer()">☰</button>
            <div class="greeting-card"><div class="title">Buenos días, 🐺</div><div class="name" id="txtNombreUsuario">Mario</div></div>
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
            <div style="margin-top:40px; font-size:11px; color:#a78bfa; text-align:center; border-top:1px solid #3b0764; padding-top:10px;">FR Grupo Empresarial<br>FR Software & Technology v4.0</div>
        </div>
        <div class="content-hud">
            <div class="quote-box">"No es solo llegar, es disfrutar el camino"</div>
            <div id="log"><b>Astra ></b> ¡Hola, Mario! Lista en cabina y sonriendo. ¿Qué ruta nos inventamos hoy?</div>
        </div>
        <div class="bottom-hud">
            <div class="input-row"><input type="text" id="texto" placeholder="Escríbale a Astra..." autocomplete="off"><button type="button" class="send-btn" onclick="enviar()">Enviar</button></div>
            <div class="mic-container"><button type="button" class="mic-btn" id="micBtn" onclick="activarMicrofono()">🎙️</button><span class="status-text" id="statusText">• Toca para hablar con Astra •</span></div>
        </div>
    </div>
<script>
    setTimeout(()=>{ const s=document.getElementById('splash-screen'); s.style.opacity='0'; setTimeout(()=>s.style.display='none',600); }, 1800);
    function toggleDrawer(){ document.getElementById('myDrawer').classList.toggle('open'); }
    function guardarConfig(){ const u=document.getElementById('usuarioActual').value; localStorage.setItem('astra_usr',u); aplicarConfigVisual(); }
    function aplicarConfigVisual(){ const u=localStorage.getItem('astra_usr')||'Mario (Papá - Conductor)'; document.getElementById('usuarioActual').value=u; document.getElementById('txtNombreUsuario').innerText=u.split(' ')[0]; }
    window.onload=aplicarConfigVisual;
    let deferredPrompt; window.addEventListener('beforeinstallprompt',(e)=>{e.preventDefault(); deferredPrompt=e; document.getElementById('installBanner').style.display='block';});
    document.getElementById('installBtn').addEventListener('click',()=>{ document.getElementById('installBanner').style.display='none'; if(deferredPrompt){ deferredPrompt.prompt(); deferredPrompt.userChoice.then(()=>{deferredPrompt=null;}); }});
    const campo=document.getElementById('texto');
    function hablar(texto){ if('speechSynthesis' in window){ window.speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(texto); u.lang='es-CO'; u.rate=1.05; const voces=window.speechSynthesis.getVoices(); const v=voces.find(v=>v.lang.includes('es')&&(v.name.includes('Google')||v.name.includes('Helena'))); if(v) u.voice=v; window.speechSynthesis.speak(u);} }
    function enviar(){ const val=campo.value.trim(); const quien=document.getElementById('usuarioActual').value; if(!val) return; const log=document.getElementById('log'); log.innerHTML+="<br><br><b>"+quien.split(' ')[0]+" ></b> "+val; log.scrollTop=log.scrollHeight; campo.value=''; fetch('/chat',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'texto='+encodeURIComponent(val)+'&quien='+encodeURIComponent(quien)}).then(r=>r.json()).then(d=>{log.innerHTML+="<br><br><b>Astra ></b> "+d.resp; log.scrollTop=log.scrollHeight; hablar(d.resp);}).catch(()=>{log.innerHTML+="<br><br>⚠️ <i>Error de red, intente de nuevo.</i>";}); }
    campo.addEventListener("keypress",(e)=>{if(e.key==="Enter") enviar();});
    function activarMicrofono(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){alert("Use Chrome en el celular."); return;} const rec=new SR(); rec.lang='es-CO'; rec.interimResults=false; const st=document.getElementById('statusText'); st.innerText="• Escuchando... •"; rec.onresult=(ev)=>{campo.value=ev.results[0][0].transcript; st.innerText="• Toca para hablar con Astra •"; enviar();}; rec.onerror=rec.onend=()=>{st.innerText="• Toca para hablar con Astra •";}; rec.start();}
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
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt_completo,
            config={
                'system_instruction': SYSTEM_PROMPT,
                'temperature': 0.85,
            }
        )
        respuesta_ia = response.text.strip()
    except Exception as e:
        print(f"Error Gemini: {e}")
        respuesta_ia = "¡Ay Mario! Se me fue la señal un momentico. ¿Me repite por fa?"
    return jsonify({'resp': respuesta_ia})

@app.route('/icon.png')
def icon():
    if os.path.exists('icon.png'):
        return send_file('icon.png', mimetype='image/png')
    # Si no existe, no tumba la app
    return "", 404

@app.route('/astra-face.jpg')
def astra_face():
    if os.path.exists('astra-face.jpg'):
        return send_file('astra-face.jpg', mimetype='image/jpeg')
    else:
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1200"><rect width="100%" height="100%" fill="#05030a"/><circle cx="400" cy="500" r="280" fill="#7e22ce" opacity="0.3"/></svg>'
        return send_file(io.BytesIO(svg), mimetype='image/svg+xml')

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "ASTRA FR - FR Software & Technology",
        "short_name": "ASTRA FR",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#05030a",
        "theme_color": "#05030a",
        "icons": [{
            "src": "/icon.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
