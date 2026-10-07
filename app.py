from flask import Flask, send_from_directory, request, jsonify
import os, json, datetime, requests, base64
from google import genai
from supabase import create_client

app = Flask(__name__, static_folder='.', static_url_path='')
DB_FILE = "astra_db.json"

# ==========================================
# CONFIGURACIÓN SUPABASE - BÓVEDA ETERNA
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "") # ej: mario/astra-fr

supabase_client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("SEBA: Supabase conectado - Memoria 500 años OK")
except Exception as e:
    print(f"SEBA: Error Supabase: {e}")

def obtener_memoria_500_anos():
    if not supabase_client:
        return "Bóveda eterna aún sin conexión."
    try:
        resp = supabase_client.table("recuerdos_publicos_de_astra").select("*").order("created_at", desc=True).limit(5).execute()
        if resp.data:
            texto = ""
            for r in resp.data:
                texto += f"\n- [{r.get('tipo','recuerdo')}] {r.get('usuario','familia')}: {r.get('contenido','')}"
            return texto
        else:
            return "Bóveda eterna vacía por ahora."
    except Exception as e:
        return f"Error leyendo bóveda: {e}"

def get_system_status():
    try:
        if not supabase_client: return {"status": "activo", "pending_feature": None}
        resp = supabase_client.table("system_status").select("*").eq("id", 1).single().execute()
        return resp.data if resp.data else {"status": "activo", "pending_feature": None}
    except:
        return {"status": "activo", "pending_feature": None}

def set_system_status(status, pending_feature=None):
    try:
        if not supabase_client: return
        data = {"status": status, "pending_feature": pending_feature}
        supabase_client.table("system_status").update(data).eq("id", 1).execute()
    except Exception as e:
        print(f"Error set status: {e}")

# ==========================================
# GITHUB AUTO-PUSH BLINDADO
# ==========================================
def push_a_github(nuevo_contenido, commit_msg):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False, "Falta GITHUB_TOKEN o GITHUB_REPO en Render"
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/app.py"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        # obtener SHA actual
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        if not sha:
            return False, "No pude obtener el SHA del repo"
        content_b64 = base64.b64encode(nuevo_contenido.encode("utf-8")).decode()
        data = {"message": commit_msg, "content": content_b64, "sha": sha}
        r2 = requests.put(url, headers=headers, json=data)
        if r2.status_code in [200, 201]:
            return True, "Push OK"
        else:
            return False, r2.text
    except Exception as e:
        return False, str(e)

# ==========================================
# CONFIGURACIÓN GEMINI
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = None
gemini_activo = False
try:
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_activo = True
except Exception as e:
    print(f"Error Gemini: {e}")

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"servicios": [], "mensajes": [], "memoria_familia": {}, "funciones": [], "alertas": []}, f, ensure_ascii=False)
init_db()
def get_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"servicios": [], "mensajes": [], "memoria_familia": {}, "funciones": [], "alertas": []}
def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generar_respuesta_gemini(usuario, mensaje):
    if not gemini_activo or not client:
        return f"Listo {usuario.get('corto', 'Mario')}, recibí tu mensaje: '{mensaje}'. (Modo local sin Gemini)."
    instrucciones_rol = ""
    rol = usuario.get('rol', 'admin')
    if rol == 'admin':
        instrucciones_rol = "Estás hablando con Mario, el creador y administrador del sistema ASTRA FR, conductor de un Renault Kwid 2026. Háblale de forma directa, inteligente, clara, con un toque sutilmente coqueto y de compañera leal, sin rodeos."
    elif rol == 'esposa':
        instrucciones_rol = "Estás hablando con Paola (Pao), la esposa de Mario. Trátala como una amigaza cercana."
    elif rol == 'hijo_15':
        instrucciones_rol = "Estás hablando con Durlandy (Dur), hijo de 15 años. Trátalo como un gran amigo. IMPORTANTE: Si te pide hacer la tarea, NO se la hagas. Explícale paso a paso."
    elif rol == 'hija_11':
        instrucciones_rol = "Estás hablando con Madelyn (Made), hija de 11 años. Trátala con mucho cariño."
    memoria_eterna = obtener_memoria_500_anos()
    system_prompt = f"""
    Eres ASTRA, asistente de IA integrado en el ecosistema familiar y del vehículo
