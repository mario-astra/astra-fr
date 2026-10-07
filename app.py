# app.py - ASTRA FR - FINAL BLINDADO 6 OCT 2026 - RUTA CORREGIDA
from flask import Flask, send_from_directory, request, jsonify
import os, json, requests, base64
from google import genai
from supabase import create_client

app = Flask(__name__, static_folder='.', static_url_path='')
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
        supabase_client.table("system_status").update({"status":status,"pending_feature":pending_feature}).eq("id",1).execute()
    except: pass

def push_a_github(nuevo_contenido, commit_msg):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/astra-fr/app.py"
    h = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=h)
    sha = r.json().get("sha")
    if not sha: return False, "No SHA"
    b64 = base64.b64encode(nuevo_contenido.encode("utf-8")).decode()
    data = {"message": commit_msg, "content": b64, "sha": sha}
    r2 = requests.put(url, headers=h, json=data)
    return (True,"OK") if r2.status_code in [200,201] else (False,r2.text)

def obtener_memoria_500_anos():
    try:
        resp = supabase_client.table("recuerdos_publicos_de_astra").select("*").order("created_at", desc=True).limit(5).execute()
        return "\n".join([f"- {x.get('contenido','')}" for x in resp.data]) if resp.data else "Boveda vacia"
    except: return "Boveda sin conexion"

client = None
try:
    if GEMINI_API_KEY: client = genai.Client(api_key=GEMINI_API_KEY)
except: pass

def generar_respuesta_gemini(usuario, mensaje):
    try:
        memoria = obtener_memoria_500_anos()
        prompt = f"Eres ASTRA Kwid. Memoria: {memoria}. SEBA socio oficial. Usuario {usuario.get('nombre')}: {mensaje}"
        return client.models.generate_content(model='gemini-2.0-flash', contents=prompt).text.strip()
    except: return f"Recibi: {mensaje}"

def get_db():
    try:
        with open("astra_db.json","r") as f: return json.load(f)
    except: return {"servicios":[]}

@app.route("/")
def home():
    # CORREGIDO: busca index donde sea
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    if os.path.exists("astra-fr/index.html"):
        return send_from_directory("astra-fr", "index.html")
    # Si no hay index, carga interfaz de emergencia para que no salga Not Found
    return """<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>ASTRA FR</title>
    <style>body{background:#020617;color:#fff;font-family:system-ui;display:flex;flex-direction:column;height:100vh;margin:0}#chat{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px}.b{padding:10px 14px;border-radius:14px;max-width:85%}.yo{align-self:flex-end;background:#ffd700;color:#020617}.as{align-self:flex-start;background:#1e293b;border:1px solid #ffd700}#bar{display:flex;gap:8px;padding:10px;background:#0f172a}input{flex:1;padding:12px;border-radius:24px;border:1px solid #334155;background:#020617;color:#fff}</style></head>
    <body><div style="padding:12px;text-align:center;color:#ffd700;font-weight:bold">ASTRA FR - MODO EMERGENCIA OK</div><div id=chat></div>
    <div id=bar><input id=t placeholder="Escribe..."><button onclick=env() style="background:#ffd700;border:none;border-radius:50%;width:44px;height:44px">➤</button></div>
    <script>let U={nombre:"Mario",rol:"admin",pin:"2208"};function add(txt,c){let ch=document.getElementById('chat');let d=document.createElement('div');d.className='b '+c;d.innerHTML=txt;ch.appendChild(d);ch.scrollTop=ch.scrollHeight}
    async function env(){let i=document.getElementById('t');let tx=i.value.trim();if(!tx)return;i.value='';add(tx,'yo');let r=await fetch('/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:tx,usuario:U})});let d=await r.json();add(d.respuesta,'as')}
    add('Astra conectada en modo emergencia. Prueba: Astra actualizate y queda en neutro','as');</script></body></html>"""

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.json or {}
    msg = data.get("mensaje","").strip()
    usuario = data.get("usuario",{})
    estado = get_system_status()
    ml = msg.lower()
    if estado.get("status")=="neutro":
        if "cancelar" in ml:
            set_system_status("activo",None)
            return jsonify({"respuesta":"Sali de neutro."})
        if estado.get("pending_feature") and ("si, autorizo" in ml or "sí, autorizo" in ml):
            with open(__file__,"r",encoding="utf-8") as f: codigo=f.read()
            pc = f"Añade: {estado.get('pending_feature')} a este codigo. Solo codigo:\n{codigo[:12000]}"
            nuevo = client.models.generate_content(model='gemini-2.0-flash', contents=pc).text.replace("```python","").replace("```","").strip()
            ok,det = push_a_github(nuevo, f"Auto: {estado.get('pending_feature')}")
            set_system_status("activo",None)
            return jsonify({"respuesta": f"LISTO Push {det}" if ok else f"Fallo {det}"})
        if not estado.get("pending_feature"):
            set_system_status("neutro",msg)
            return jsonify({"respuesta": f"Quede en NEUTRO con '{msg}'. Di SI, AUTORIZO"})
        else:
            return jsonify({"respuesta": f"Pendiente {estado.get('pending_feature')}. Di SI, AUTORIZO"})
    if "actualizate y queda en neutro" in ml or "actualízate y queda en neutro" in ml:
        set_system_status("neutro",None)
        return jsonify({"respuesta":"Quede en NEUTRO, dime la funcion."})
    return jsonify({"respuesta": generar_respuesta_gemini(usuario, msg)})

@app.route("/datos")
def datos(): return jsonify(get_db())
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
