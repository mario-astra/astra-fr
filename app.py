from flask import Flask, request, jsonify, send_file
import os, json
from datetime import datetime
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MEMORIA_FILE = "memoria_fr.json"

MODELOS_VALIDOS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]

SYSTEM_PROMPT = """
Eres Astra, copiloto familia FR. Paisa, elegante, coqueta, inteligente, muy breve max 2 frases.
MUSICA: Si piden musica responde [MUSICA: busqueda] al inicio.
MODO GUARDAS: Si dicen guardas, policia, reten, transito, vienen los tombos, activa protocolo. Responde con consejo legal corto en español para Mario y con [TRADUCIR: mensaje ingles calmado para pasajero: routine check, you may remain silent...] NUNCA inventes parentescos.
"""

def cargar_memoria():
    if os.path.exists(MEMORIA_FILE):
        try:
            with open(MEMORIA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def guardar_memoria(texto, quien):
    memoria = cargar_memoria()
    memoria.append({"fecha": datetime.now().isoformat(),"quien": quien,"texto": texto})
    memoria = memoria[-200:]
    with open(MEMORIA_FILE, 'w', encoding='utf-8') as f: json.dump(memoria, f, ensure_ascii=False, indent=2)

def generar_con_astra(prompt_completo):
    last_error = None
    for modelo in MODELOS_VALIDOS:
        try:
            resp = client.models.generate_content(model=modelo, contents=prompt_completo, config={'system_instruction': SYSTEM_PROMPT, 'temperature':0.85})
            return resp.text.strip()
        except Exception as e:
            last_error = e
            continue
    raise last_error

HTML_INDEX = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ASTRA FR</title>
<style>
body{margin:0;background:#05030a;color:#fff;font-family:Arial;display:flex;flex-direction:column;height:100vh;overflow:hidden}
.main{flex:1;position:relative;width:100%;height:100vh;overflow:hidden;background:#000}
#avatar{width:100%;height:100%;object-fit:cover;object-position:top center;position:absolute;inset:0}
.overlay{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 0%, rgba(0,0,0,0) 50%, rgba(5,3,10,0.9) 100%);pointer-events:none}
.hud{position:absolute;z-index:10;bottom:0;left:0;right:0;padding:12px;display:flex;flex-direction:column;gap:10px;align-items:center}
#player{width:100%;display:none;border-radius:12px;overflow:hidden;border:1px solid #e879f9;box-shadow:0 0 20px rgba(232,121,249,0.4)}
#player iframe{width:100%;height:160px;border:none}
#guardasBox{display:none;background:rgba(0,0,0,0.85);border:1px solid #ff4444;border-radius:14px;padding:12px;text-align:center;width:90%;backdrop-filter:blur(8px)}
#log{width:95%;max-height:90px;overflow-y:auto;background:rgba(0,0,0,0.6);border-radius:12px;padding:8px;font-size:12px;backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,0.1)}
.bottom{display:flex;gap:6px;width:100%;max-width:400px}
input{flex:1;padding:11px;border-radius:25px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.7);color:#fff;outline:none;backdrop-filter:blur(6px)}
.mic{width:68px;height:68px;border-radius:50%;font-size:24px;background:radial-gradient(circle,#a855f7,#581c87);border:2px solid rgba(255,255,255,0.8);color:#fff;box-shadow:0 0 25px rgba(168,85,247,0.6)}
.mic:active{transform:scale(0.95)}
</style></head><body>
<div class="main"><img id="avatar" src="/astra-face.jpg"><div class="overlay"></div>
<div class="hud">
<div id="player"><iframe id="yt" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>
<div id="guardasBox"><p id="msgMario" style="color:#ffaaaa;margin:0 0 8px 0;font-size:13px"></p><p id="msgPax" style="background:#fff;color:#000;padding:10px;border-radius:8px;font-weight:bold;font-size:14px;margin:0"></p></div>
<div id="log"><b>Astra ></b> Lista, mi Mario. Solo hábleme. 🎙️</div>
<div class="bottom"><input id="texto" placeholder="Hábleme por voz o escriba..."><button onclick="enviar()" style="background:#fff;color:#000;border-radius:20px;padding:10px 16px;border:none;font-weight:bold">▲</button></div>
<div style="padding:6px"><button class="mic" onclick="micro()">🎙️</button></div>
</div></div>
<script>
const log=document.getElementById('log'), campo=document.getElementById('texto'), player=document.getElementById('player'), yt=document.getElementById('yt'), box=document.getElementById('guardasBox');
function playMusic(q){ player.style.display='block'; box.style.display='none'; yt.src=`https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}&autoplay=1`; }
function enviar(){ const v=campo.value.trim(); if(!v) return; log.innerHTML+=`<br><b>Usted ></b> ${v}`; campo.value=''; fetch('/chat',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'texto='+encodeURIComponent(v)+'&quien=Mario'}).then(r=>r.json()).then(d=>{
 let resp=d.resp; const mMus=resp.match(/\\[MUSICA:\\s*(.*?)\\]/i); if(mMus){ playMusic(mMus[1]); resp=resp.replace(mMus[0],'').trim(); }
 const mTrad=resp.match(/\\[TRADUCIR:\\s*(.*?)\\]/i); if(mTrad){ box.style.display='block'; player.style.display='none'; document.getElementById('msgMario').innerText=resp.replace(mTrad[0],''); document.getElementById('msgPax').innerText=mTrad[1]; resp=resp.replace(mTrad[0],'').trim(); }
 log.innerHTML+=`<br><b>Astra ></b> ${resp}`; if(mTrad) log.innerHTML+=`<br><b>Pax ></b> ${mTrad[1]}`; log.scrollTop=log.scrollHeight;
});}
campo.addEventListener('keypress',e=>{if(e.key==='Enter') enviar();});
function micro(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; const r=new SR(); r.lang='es-CO'; r.onresult=e=>{campo.value=e.results[0][0].transcript; enviar();}; r.start();}
</script></body></html>"""

@app.route('/')
def index(): return HTML_INDEX
@app.route('/chat', methods=['POST'])
def chat():
    t = request.form.get('texto',''); guardar_memoria(t, 'Mario')
    contexto = "\\n".join([f"{m['quien']}: {m['texto']}" for m in cargar_memoria()[-20:]])
    try:
        out = generar_con_astra(f"Memoria:\\n{contexto}\\n\\nMensaje: {t}")
        return jsonify({'resp': out})
    except Exception as e:
        return jsonify({'resp': f"Mi Mario, error: {e}"})

@app.route('/icon.png')
def icon(): return send_file('icon.png', mimetype='image/png')
@app.route('/astra-face.jpg')
def face(): return send_file('astra-face.jpg', mimetype='image/jpeg')
@app.route('/manifest.json')
def mf(): return send_file('manifest.json', mimetype='application/json')
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",5000)))
