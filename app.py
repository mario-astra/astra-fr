from flask import Flask, request, jsonify, send_file
import os, json, io
from datetime import datetime
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MEMORIA_FILE = "memoria_fr.json"

SYSTEM_PROMPT = """
Eres Astra, copiloto de la familia FR Grupo Empresarial. Hablas con Mario (papá), su esposa y sus hijos.
Eres 100% paisa, femenina, elegante, coqueta, inteligente y breve (máx 3 frases).
Si el usuario dice "Astra aprende que..." debes guardar esa instrucción como una nueva regla.
Usa la memoria que te doy para recordar cosas como la gata, gustos, rutas.
"""

def cargar_memoria():
    if os.path.exists(MEMORIA_FILE):
        try:
            with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []
    return []

def guardar_memoria(texto, quien):
    memoria = cargar_memoria()
    es_aprendizaje = "aprende que" in texto.lower()
    memoria.append({
        "fecha": datetime.now().isoformat(),
        "quien": quien,
        "texto": texto,
        "tipo": "aprendizaje" if es_aprendizaje else "conversacion"
    })
    memoria = memoria[-200:]
    with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

HTML_INDEX = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA FR</title><link rel="manifest" href="/manifest.json"><link rel="icon" href="/icon.png"><meta name="theme-color" content="#05030a">
<style>
body{margin:0;background:#05030a;color:#fff;font-family:Arial;display:flex;flex-direction:column;height:100vh;overflow:hidden}
.main{flex:1;position:relative;width:100%;height:100vh;overflow:hidden;background:#05030a}
#avatar{width:100%;height:100%;object-fit:cover;object-position:top center;position:absolute;inset:0}
.overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(5,3,10,0.1) 0%, rgba(5,3,10,0) 50%, rgba(5,3,10,0.9) 100%);pointer-events:none}
.hud{position:absolute;z-index:10;bottom:0;left:0;right:0;padding:12px;display:flex;flex-direction:column;gap:10px;background:linear-gradient(to top,rgba(5,3,10,0.9),transparent)}
#log{max-height:120px;overflow-y:auto;background:rgba(12,6,20,0.75);border:1px solid #7e22ce;border-radius:12px;padding:10px;font-size:13px;backdrop-filter:blur(5px)}
.bottom{display:flex;gap:8px}
input{flex:1;padding:12px;border-radius:25px;border:1px solid #7e22ce;background:rgba(12,6,20,0.9);color:#fff;outline:none}
button{border:none;border-radius:25px;padding:10px 18px;font-weight:bold;cursor:pointer;background:#c084fc;color:#000}
.talking{filter:brightness(1.2);animation:talk 0.15s infinite}
@keyframes talk{0%{transform:scale(1)}50%{transform:scale(1.01)}100%{transform:scale(1)}}
.mic-wrap{text-align:center;padding-bottom:5px}
.mic{width:62px;height:62px;border-radius:50%;font-size:24px;background:radial-gradient(circle,#9333ea,#581c87);border:2px solid #e879f9;box-shadow:0 0 20px rgba(232,121,249,0.7);color:#fff}
</style></head><body>
<div class="main"><img id="avatar" src="/astra-face.jpg"><div class="overlay"></div>
<div class="hud">
<div id="log"><b>Astra ></b> ¡Hola Mario! Ya tengo memoria activa, si me cuenta lo de la gata no se me olvida. 🐱</div>
<div class="bottom"><input id="texto" placeholder="Escríbale a Astra o diga 'Astra aprende que...'"><button onclick="enviar()">Enviar</button></div>
<div class="mic-wrap"><button class="mic" onclick="micro()">🎙️</button><div style="font-size:10px;margin-top:4px;opacity:0.7">Toca para hablar</div></div>
</div></div>
<script>
const log=document.getElementById('log'), campo=document.getElementById('texto'), avatar=document.getElementById('avatar');
function hablar(t){ if(!'speechSynthesis' in window) return; speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(t); u.lang='es-CO'; u.rate=1.05; u.onstart=()=>avatar.classList.add('talking'); u.onend=()=>avatar.classList.remove('talking'); speechSynthesis.speak(u); }
function enviar(){ const v=campo.value.trim(); if(!v) return; log.innerHTML+=`<br><br><b>Usted ></b> ${v}`; campo.value=''; fetch('/chat',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'texto='+encodeURIComponent(v)+'&quien=Mario'}).then(r=>r.json()).then(d=>{log.innerHTML+=`<br><br><b>Astra ></b> ${d.resp}`; log.scrollTop=log.scrollHeight; hablar(d.resp);});}
campo.addEventListener('keypress',e=>{if(e.key==='Enter') enviar();});
function micro(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){alert('Mic no soportado');return} const r=new SR(); r.lang='es-CO'; r.onresult=e=>{campo.value=e.results[0][0].transcript; enviar();}; r.start();}
</script></body></html>"""

@app.route('/')
def index():
    return HTML_INDEX

@app.route('/chat', methods=['POST'])
def chat():
    t = request.form.get('texto','')
    quien = request.form.get('quien','Mario')
    guardar_memoria(t, quien)
    memoria = cargar_memoria()
    contexto_mem = "\n".join([f"{m['quien']} ({m['fecha'][:10]}): {m['texto']}" for m in memoria[-20:]])
    prompt_final = f"Memoria previa:\n{contexto_mem}\n\nMensaje actual de {quien}: {t}\n\nSi dice 'aprende que', confirma que lo aprendiste."

    try:
        resp = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt_final,
            config={'system_instruction': SYSTEM_PROMPT, 'temperature':0.85}
        )
        out = resp.text.strip()
        return jsonify({'resp': out})
    except Exception as e:
        print(f"ERROR REAL DE GOOGLE: {e}")
        return jsonify({'resp': f"Mario, se me fue la señal un momentico, ¿me repite por fa? Error: {e}"})

@app.route('/icon.png')
def icon(): return send_file('icon.png', mimetype='image/png')
@app.route('/astra-face.jpg')
def face(): return send_file('astra-face.jpg', mimetype='image/jpeg')
@app.route('/manifest.json')
def mf(): return send_file('manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
