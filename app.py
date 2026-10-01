from flask import Flask, request, jsonify, send_file
import os, json
from datetime import datetime
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MEMORIA_FILE = "memoria_fr.json"

SYSTEM_PROMPT = """
Eres Astra, copiloto de la familia FR Grupo Empresarial. Eres paisa, femenina, elegante, coqueta, inteligente, breve max 3 frases.
Memoria: Recuerdas todo lo que dice "Astra aprende que..."
MUSICA: Si piden musica, responde con [MUSICA: busqueda] al inicio. Ej: [MUSICA: Feid LUNA] Listo mi Mario...
MODO GUARDAS: Si el usuario dice "Astra guardas", "vienen los guardas", "modo guardas", "policia", activa protocolo legal.
NO inventes parentescos ni mentiras. Debes:
1. Responder en español a Mario con consejos legales cortos: no discutir, entregar papeles, derecho a guardar silencio sobre la app, no confesar.
2. Responder con [TRADUCIR: mensaje en ingles] para el pasajero. El mensaje debe ser calmado y en ingles: "We are in a routine traffic check. You may remain silent, you don't have to explain the ride. If police asks ID, show it. Stay calm, everything is ok."
Si detectas que el pasajero habla otro idioma en memoria, traduce a ese idioma.
Nunca digas que son amigos de infancia ni menciones a Maria Lucrecia ni comida china. Eso es falsedad.
"""

def cargar_memoria():
    if os.path.exists(MEMORIA_FILE):
        try:
            with open(MEMORIA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def guardar_memoria(texto, quien):
    memoria = cargar_memoria()
    es_aprendizaje = "aprende que" in texto.lower()
    memoria.append({"fecha": datetime.now().isoformat(),"quien": quien,"texto": texto,"tipo": "aprendizaje" if es_aprendizaje else "conversacion"})
    memoria = memoria[-200:]
    with open(MEMORIA_FILE, 'w', encoding='utf-8') as f: json.dump(memoria, f, ensure_ascii=False, indent=2)

HTML_INDEX = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA FR</title><link rel="manifest" href="/manifest.json"><link rel="icon" href="/icon.png"><meta name="theme-color" content="#05030a">
<style>
body{margin:0;background:#05030a;color:#fff;font-family:Arial;display:flex;flex-direction:column;height:100vh;overflow:hidden}
.main{flex:1;position:relative;width:100%;height:100vh;overflow:hidden;background:#05030a}
#avatar{width:100%;height:100%;object-fit:cover;object-position:top center;position:absolute;inset:0}
.overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(5,3,10,0.1) 0%, rgba(5,3,10,0) 45%, rgba(5,3,10,0.95) 100%);pointer-events:none}
.hud{position:absolute;z-index:10;bottom:0;left:0;right:0;padding:10px;display:flex;flex-direction:column;gap:8px}
#player{width:100%;display:none;border-radius:12px;overflow:hidden;border:1px solid #e879f9}
#player iframe{width:100%;height:175px;border:none}
#guardasBox{display:none;background:rgba(180,0,0,0.9);border:2px solid red;border-radius:12px;padding:12px;text-align:center}
#guardasBox h3{margin:0 0 8px 0;color:#fff}
#guardasBox p{margin:5px 0;font-size:13px}
#log{max-height:100px;overflow-y:auto;background:rgba(12,6,20,0.8);border:1px solid #7e22ce;border-radius:12px;padding:8px;font-size:12px}
.bottom{display:flex;gap:6px}
input{flex:1;padding:11px;border-radius:25px;border:1px solid #7e22ce;background:rgba(12,6,20,0.9);color:#fff;outline:none}
button{border:none;border-radius:25px;padding:8px 14px;font-weight:bold;cursor:pointer;background:#c084fc;color:#000;font-size:13px}
.mic-wrap{display:flex;gap:8px;justify-content:center;align-items:center;padding-bottom:2px}
.mic{width:56px;height:56px;border-radius:50%;font-size:20px;background:radial-gradient(circle,#9333ea,#581c87);border:2px solid #e879f9;color:#fff}
.btn-guardas{background:#ff0000;color:#fff;border:2px solid #ffaaaa;box-shadow:0 0 15px rgba(255,0,0,0.7);font-size:12px;padding:10px 15px;border-radius:20px}
</style></head><body>
<div class="main"><img id="avatar" src="/astra-face.jpg"><div class="overlay"></div>
<div class="hud">
<div id="player"><iframe id="yt" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>
<div id="guardasBox"><h3>🚨 MODO GUARDAS ACTIVO</h3><p id="msgMario" style="color:#ffaaaa"></p><p id="msgPax" style="background:#fff;color:#000;padding:8px;border-radius:8px;font-weight:bold;font-size:14px"></p><button onclick="cerrarGuardas()" style="margin-top:8px;background:#fff;color:#000">Cerrar</button></div>
<div id="log"><b>Astra ></b> ¡Hola Mario! Lista con memoria, música y modo guardas. 🎵🛡️</div>
<div class="bottom"><input id="texto" placeholder="Pon música o hable..."><button onclick="enviar()">Enviar</button></div>
<div class="mic-wrap"><button class="mic" onclick="micro()">🎙️</button><button class="btn-guardas" onclick="activarGuardas()">🚨 GUARDAS</button></div>
</div></div>
<script>
const log=document.getElementById('log'), campo=document.getElementById('texto'), avatar=document.getElementById('avatar'), player=document.getElementById('player'), yt=document.getElementById('yt'), guardasBox=document.getElementById('guardasBox'), msgMario=document.getElementById('msgMario'), msgPax=document.getElementById('msgPax');
function hablar(t){ if(!'speechSynthesis' in window) return; speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(t); u.lang='es-CO'; u.rate=1.05; u.onstart=()=>avatar.classList.add('talking'); u.onend=()=>avatar.classList.remove('talking'); speechSynthesis.speak(u); }
function playMusic(q){ player.style.display='block'; guardasBox.style.display='none'; yt.src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1`; }
function activarGuardas(){ campo.value='Astra vienen los guardas'; enviar(); }
function cerrarGuardas(){ guardasBox.style.display='none'; player.style.display='none'; yt.src=''; }
function mostrarGuardas(mario, pax){ player.style.display='none'; guardasBox.style.display='block'; msgMario.innerText=mario; msgPax.innerText=pax; hablar(mario); }
function enviar(){ const v=campo.value.trim(); if(!v) return; log.innerHTML+=`<br><br><b>Usted ></b> ${v}`; campo.value=''; fetch('/chat',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'texto='+encodeURIComponent(v)+'&quien=Mario'}).then(r=>r.json()).then(d=>{
 let resp=d.resp; const mMus=resp.match(/\\[MUSICA:\\s*(.*?)\\]/i); if(mMus){ playMusic(mMus[1]); resp=resp.replace(mMus[0],'').trim(); }
 const mTrad=resp.match(/\\[TRADUCIR:\\s*(.*?)\\]/i); let tradTxt=''; if(mTrad){ tradTxt=mTrad[1]; resp=resp.replace(mTrad[0],'').trim(); mostrarGuardas(resp, tradTxt); }
 log.innerHTML+=`<br><br><b>Astra ></b> ${resp}`; if(tradTxt) log.innerHTML+=`<br><b>Para pasajero ></b> ${tradTxt}`; log.scrollTop=log.scrollHeight; if(!mTrad) hablar(resp);
});}
campo.addEventListener('keypress',e=>{if(e.key==='Enter') enviar();});
function micro(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){alert('No soportado');return} const r=new SR(); r.lang='es-CO'; r.onresult=e=>{campo.value=e.results[0][0].transcript; enviar();}; r.start();}
</script></body></html>"""

@app.route('/')
def index(): return HTML_INDEX

@app.route('/chat', methods=['POST'])
def chat():
    t = request.form.get('texto',''); quien = request.form.get('quien','Mario')
    guardar_memoria(t, quien)
    memoria = cargar_memoria()
    contexto_mem = "\\n".join([f"{m['quien']}: {m['texto']}" for m in memoria[-20:]])
    prompt_final = f"Memoria:\\n{contexto_mem}\\n\\nMensaje de {quien}: {t}"
    try:
        resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_final, config={'system_instruction': SYSTEM_PROMPT, 'temperature':0.85})
        out = resp.text.strip()
        return jsonify({'resp': out})
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({'resp': f"Mi Mario, se me fue un momentico la señal, ¿me repite? Error: {e}"})

@app.route('/icon.png')
def icon(): return send_file('icon.png', mimetype='image/png')
@app.route('/astra-face.jpg')
def face(): return send_file('astra-face.jpg', mimetype='image/jpeg')
@app.route('/manifest.json')
def mf(): return send_file('manifest.json', mimetype='application/json')
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
