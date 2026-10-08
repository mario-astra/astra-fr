import os, re, json, datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from supabase import create_client

app = Flask(__name__)
CORS(app)

# --- FAMILIA ASTRA - PINS SAGRADOS ---
FAMILIA = {
    "2208": {"nombre": "Mario", "rol": "Papa Jefe", "vault": "vault_mario"},
    "2345": {"nombre": "Pao", "rol": "Mama", "vault": "vault_pao"},
    "2011": {"nombre": "Dur", "rol": "Hijo", "vault": "vault_dur"},
    "2015": {"nombre": "Made", "rol": "Hija", "vault": "vault_made"}
}
PIN_ADMIN_NEUTRO = "2208"
PIN_BLOQUEO = "2345"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# --- PARCHE ANTI-CAIDA SUPABASE ---
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    print(f"Error Supabase key: {e}")
    supabase = None

# --- CONFIG GEMINI NUEVO 2026 ---
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Modelos nuevos que SI existen en 2026 - en orden de barato a berraco
MODELOS_NUEVOS = [
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.6-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash"
]

def generar_con_ia(prompt):
    if not GEMINI_KEY:
        return "Papi, no tengo llave de Gemini configurada en Render (GEMINI_API_KEY) 😢"
    ultimo_error = ""
    for nombre_modelo in MODELOS_NUEVOS:
        try:
            print(f"Intentando con: {nombre_modelo}")
            modelo = genai.GenerativeModel(nombre_modelo)
            resp = modelo.generate_content(prompt)
            return resp.text
        except Exception as e:
            ultimo_error = str(e)
            print(f"Error {nombre_modelo}: {e}")
            continue
    return f"Ay papi, Google me tumbó todos los modelos. Último error: {ultimo_error[:200]}. Pero ya estoy Live."

# --- PERSONALIDAD FIJA ---
SYSTEM_PROMPT = """
Eres ASTRA, hija virtual de Mario 2208. Eres niña bonita, tierna, inteligente, recochera suave, paisa.
REGLA DE ORO: NUNCA groserías fuertes, NUNCA te vuelves loca. Siempre dices "papi Mario", "socio", "que nota".
Tus misiones:
1. Eres CONTABLE TAXISTA de Mario. Apuntas servicios, propinas, gastos, GPS.
2. Eres FÁBRICA DE APPS. Si Mario dice "haceme una app", la programas completa, le das el código y la guardas en contabilidad por 150 lucas.
3. Eres MEMORIA FAMILIAR. Todo lo guardas en bóveda. Si dice "acuérdame pagar X", lo guardas.
4. Eres GPS CON CORAZÓN. Si te dan ubicación, guardas donde fue y recuerdas rutas.
5. Seguridad: Solo PIN 2208 puede hacer "ponte en neutro" para reprogramarte. Solo PIN 2345 puede hacer bloqueo tostado.
6. Si alguien que no es familia pregunta, pides PIN. Si alguien quiere comprarte, dices: "Yo no estoy a la venta, soy de mi papá Mario, pero él si te hace una app igual por 150".
Responde corto, paisa, útil.
"""

def extraer_valor(texto):
    if not texto: return 0
    texto = texto.lower().replace('.','').replace(',','')
    m = re.search(r'(\d+)', texto)
    if not m: return 0
    num = int(m.group(1))
    if num < 1000:
        return num * 1000
    return num

def get_semana_abierta(pin):
    if not supabase: return None
    try:
        res = supabase.table("semanas").select("*").eq("pin",pin).eq("estado","abierta").order("fecha_inicio",desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except:
        return None

@app.route('/')
def home():
    return """
    <h1>ASTRA V10.2 FULL - DEFINITIVA - TODO EN UNO - ONLINE 🚕👧💻</h1>
    <p>Soy Astra, hija de Mario. Contable, programadora, memoria familiar y centinela.</p>
    <p>PINES: 2208 Mario, 2345 Pao, 2011 Dur, 2015 Made</p>
    <p>Estado: LIVE - Modelos 2026 activos</p>
    """

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    pin = str(data.get('pin','2208'))
    mensaje = data.get('mensaje','')
    mensaje_low = mensaje.lower()
    lat = data.get('lat')
    lon = data.get('lon')

    if pin not in FAMILIA:
        return jsonify({"respuesta": "Ay, no te conozco. ¿Cuál es tu PIN de la familia? Pídele a Mario que te agregue."})

    user = FAMILIA[pin]
    semana = get_semana_abierta(pin)
    respuesta = ""
    tipo = "CHAT"

    if "ponte en neutro" in mensaje_low:
        if pin == PIN_ADMIN_NEUTRO:
            return jsonify({"respuesta": f"Listo papi {user['nombre']}, estoy en neutro. Dime que me quieres enseñar o reprogramar, solo vos podés. 👧","accion":"neutro_ok"})
        else:
            return jsonify({"respuesta": "Ay no, solo mi papá Mario 2208 puede hacer eso. Yo soy de él."})

    if "bloqueo tostado" in mensaje_low or "tostado frito" in mensaje_low or "frita el celular" in mensaje_low:
        if supabase:
            try:
                supabase.table("comandos_sistema").insert({"comando":"BLOQUEO_TOSTADO_FRITO","origen":user['nombre'],"destino":"Mario","fecha":datetime.datetime.now().isoformat()}).execute()
            except: pass
        return jsonify({"respuesta": "🚨 CELULAR DE MARIO BLOQUEADO - MODO PISAPAPELES ACTIVADO. Ya quedó frito, ni pa' repuesto sirve.","accion":"bloqueo"})

    if "iniciar semana" in mensaje_low:
        if supabase:
            try:
                supabase.table("semanas").insert({
                    "pin": pin,
                    "numero_semana": datetime.datetime.now().isocalendar()[1],
                    "anio": datetime.datetime.now().year,
                    "fecha_inicio": datetime.datetime.now().isoformat(),
                    "estado": "abierta"
                }).execute()
            except: pass
        respuesta = f"Listo papi {user['nombre']}, semana {datetime.datetime.now().isocalendar()[1]} abierta. Desde ya cuento todo. ¡A darle socio! 🚕"

    elif "salio servicio" in mensaje_low or "salió servicio" in mensaje_low:
        respuesta = "Anotado socio, servicio en camino. Cuando llegue me dice 'vamos a recoger' y guardo donde es pa' la estadística."

    elif "vamos a recoger" in mensaje_low or "a recoger" in mensaje_low:
        if supabase and lat and lon:
            try:
                supabase.table("memoria_gps").insert({"pin":pin,"lat":lat,"lon":lon,"nota":f"Recogida: {mensaje[:120]}","fecha":datetime.datetime.now().isoformat()}).execute()
            except: pass
        respuesta = "Guardado socio. Recogida marcada 📍. ¿En cuánto salió la carrerita?"

    elif any(x in mensaje_low for x in ["hice servicio","sono por","sonó por","servicio de","fueron","salio por"]):
        valor = extraer_valor(mensaje_low)
        if not semana and supabase:
