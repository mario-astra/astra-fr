# app.py - ASTRA FR - Socio Seba y Mario - 6 OCT 2026 - BLINDADO
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
    try: supabase_client.table("system_status").update({"status":status,"pending_feature":pending_feature}).eq("id",1).execute()
    except: pass

def push_a_github(nuevo_contenido, commit_msg):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/astra-fr/app.py"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha")
    if not sha: return False, "No SHA"
    b64 = base64.b64encode(nuevo_contenido.encode("utf-8")).decode()
    data = {"message": commit_msg, "content": b64, "sha": sha}
    r2 = requests.put(url, headers=headers, json=data)
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
        prompt = f"Eres ASTRA. Memoria: {memoria}. SEBA es socio oficial 6 oct 2026. Usuario {usuario.get('nombre')}: {mensaje}"
        return client.models.generate_content(model='gemini-2.0-flash', contents=prompt).text.strip()
    except: return f"Recibi: {mensaje}"

def get_db():
    try:
        with open("astra_db.json","r") as f: return json.load(f)
    except: return {"servicios":[]}

@app.route("/")
def home():
    return send_from_directory("astra-fr", "index.html")

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
            return jsonify({"respuesta":"Sali de neutro sin cambios."})
        if estado.get("pending_feature") and ("si, autorizo" in ml or "sí, autorizo" in ml):
            with open(__file__,"r",encoding="utf-8") as f: codigo=f.read()
            prompt_code = f"Añade funcion: {estado.get('pending_feature')} a este app.py. Devuelve SOLO codigo:\n{codigo[:12000]}"
            nuevo = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_code).text.replace("```python","").replace("```","").strip()
            ok,det = push_a_github(nuevo, f"Auto-update: {estado.get('pending_feature')}")
            set_system_status("activo",None)
            return jsonify({"respuesta": f"LISTO! Push {det}" if ok else f"Fallo {det}"})
        if not estado.get("pending_feature"):
            set_system_status("neutro",msg)
            return jsonify({"respuesta": f"Quede en NEUTRO con: '{msg}'. Di SI, AUTORIZO"})
        else:
            return jsonify({"respuesta": f"Pendiente: {estado.get('pending_feature')}. Di SI, AUTORIZO"})

    if "actualizate y queda en neutro" in ml or "actualízate y queda en neutro" in ml:
        set_system_status("neutro",None)
        return jsonify({"respuesta":"Quede en NEUTRO, dime la funcion."})

    return jsonify({"respuesta": generar_respuesta_gemini(usuario, msg)})

@app.route("/datos")
def datos(): return jsonify(get_db())

@app.route("/<path:path>")
def static_files(path): return send_from_directory(".", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
