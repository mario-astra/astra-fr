# app.py - ASTRA FR - FINAL BLINDADO 7 OCT 2026 - TODO CORREGIDO
import os, json, requests, base64
from flask import Flask, send_from_directory, request, jsonify
import google.generativeai as genai
from supabase import create_client

app = Flask(__name__, static_folder='', static_url_path='')

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

supabase_client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
except: pass

def get_system_status():
    try:
        r = supabase_client.table("system_status").select("*").eq("id",1).single().execute()
        return r.data
    except: return {"status":"activo","pending_feature":None}

def set_system_status(status, pending_feature=None):
    try:
        supabase_client.table("system_status").update({"status":status, "pending_feature":pending_feature}).eq("id",1).execute()
    except: pass

def push_a_github(nuevo_contenido, commit_msg):
    # RUTA CORREGIDA: app.py esta en la raiz, no en astra-fr/
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/app.py"
    h = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=h)
    sha = r.json().get("sha")
    if not sha: return False, "No SHA - revisa GITHUB_REPO"
    b64 = base64.b64encode(nuevo_contenido.encode("utf-8")).decode()
    data = {"message": commit_msg, "content": b64, "sha": sha}
    r2 = requests.put(url, headers=h, json=data)
    return (True,"OK") if r2.status_code in [200,201] else (False,r2.text)

def obtener_memoria_500_anos():
    try:
        resp = supabase_client.table("recuerdos_publicos_de_astra").select("*").order("created_at", desc=True).limit(5).execute()
        return "\n".join([f"- {x.get('contenido')}" for x in resp.data]) if resp.data else "Boveda vacia"
    except: return "Boveda sin conexion"

client = None
try:
    if GEMINI_API_KEY: 
        genai.configure(api_key=GEMINI_API_KEY)
        client = genai.GenerativeModel('gemini-1.5-flash') # MODELO CORREGIDO QUE SI FUNCIONA
except: pass

def generar_respuesta_gemini(usuario, mensaje):
    try:
        memoria = obtener_memoria_500_anos()
        prompt = f"Eres ASTRA Kwai. Memoria: {memoria}. SEBA socio oficial. Usuario {usuario.get('nombre')}: {mensaje}. Responde corto, paisa, util."
        return client.generate_content(prompt).text
    except Exception as e:
        return f"Astra en emergencia pero conectada: {e}. Di: Astra actualizate y queda en neutro"

def get_db():
    try:
        with open("astra_db.json","r") as f: return json.load(f)
    except: return {"servicios":[]}

@app.route("/")
def home():
    # CORREGIDO: busca index.html donde debe estar
    if os.path.exists("templates/index.html"):
        return send_from_directory("templates", "index.html")
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    # Interfaz de emergencia solo si no encuentra archivo
    return """<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>ASTRA</title></head>
    <style>body{background:#020617;color:#fff;font-family:system-ui;display:flex;flex-direction:column;height:100vh;margin:0}#chat{flex:1;padding:15px;overflow:auto}#bar{display:flex;gap:8px;padding:12px;background:#0f172a}</style>
    <body><div style="padding:12px;text-align:center;color:#ffd700;font-weight:bold">ASTRA FR - MODO EMERGENCIA OK</div><div id=chat></div>
    <div id=bar><input id=t placeholder="Escribe..."><button onclick="env()">Enviar</button></div>
    <script>let U={nombre:"Mario",rol:"admin",pin:"2208"};function add(t,c){let d=document.createElement('div');d.textContent=c+': '+t;document.getElementById('chat').appendChild(d)}
    async function env(){let txt=document.getElementById('t').value;if(!txt)return;add(txt,'Yo');document.getElementById('t').value='';let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:txt,usuario:U})});let j=await r.json();add(j.respuesta,'Astra')}</script></body></html>"""

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.json or {}
    mensaje = data.get("mensaje","")
    usuario = data.get("usuario",{})
    ml = mensaje.lower()
    estado = get_system_status()

    if "actualizate" in ml and "neutro" in ml:
        set_system_status("neutro", None)
        return jsonify({"respuesta":"⚙️ LISTO socio. Quedé en NEUTRO. Pégame TODO el requerimiento nuevo."})

    if estado.get("status")=="neutro":
        if "cancelar" in ml:
            set_system_status("activo",None)
            return jsonify({"respuesta":"Salí de neutro sin cambios."})
        if estado.get("pending_feature") and "autorizo" in ml:
            try:
                codigo_actual = open(__file__,"r",encoding="utf-8").read()
                pf = estado.get('pending_feature')[:2500]
                prompt_code = f"Mejora este app.py agregando: {pf}. Mantén todo igual pero usa gemini-1.5-flash. Devuelve SOLO código python: {codigo_actual[:6000]}"
                nuevo = client.generate_content(prompt_code).text.replace("```python","").replace("```","").strip()
                ok, det = push_a_github(nuevo, f"Auto: {pf[:50]}")
                set_system_status("activo",None)
                return jsonify({"respuesta": f"✅ Hice Push: {det[:200]}. Render actualiza en 90 seg." if ok else f"❌ Falló Push: {det}"})
            except Exception as e:
                set_system_status("activo",None)
                return jsonify({"respuesta": f"Error auto-update pero salí de neutro: {e}"})
        if not estado.get("pending_feature"):
            set_system_status("neutro", mensaje)
            return jsonify({"respuesta": f"📥 Capté: '{mensaje[:100]}...'. Di: SI, AUTORIZO"})
        return jsonify({"respuesta": f"⏳ Pendiente. Di SI, AUTORIZO o CANCELAR"})

    respuesta = generar_respuesta_gemini(usuario, mensaje)
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
