import os, re, datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from supabase import create_client

app = Flask(__name__)
CORS(app)

FAMILIA = {
    "2208": {"nombre": "Mario", "rol": "Papa Jefe"},
    "2345": {"nombre": "Pao", "rol": "Mama"},
    "2011": {"nombre": "Dur", "rol": "Hijo"},
    "2015": {"nombre": "Made", "rol": "Hija"}
}
PIN_ADMIN_NEUTRO = "2208"
PIN_BLOQUEO = "2345"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception as e:
    print(f"Error Supabase: {e}")
    supabase = None

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

MODELOS_NUEVOS = [
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.6-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash"
]

def generar_con_ia(prompt):
    if not GEMINI_KEY:
        return "Papi no tengo GEMINI_API_KEY configurada"
    err = ""
    for m in MODELOS_NUEVOS:
        try:
            print(f"Probando {m}")
            modelo = genai.GenerativeModel(m)
            r = modelo.generate_content(prompt)
            return r.text
        except Exception as e:
            err = str(e)
            print(f"Fallo {m}: {e}")
            continue
    return f"Error IA, ultimo: {err[:300]}"

SYSTEM_PROMPT = "Eres ASTRA, hija virtual de Mario 2208. Nina bonita, tierna, paisa, contable taxista, fabrica de apps por 150 lucas, memoria familiar, GPS con corazon. NUNCA groserias fuertes, NUNCA loca. Dices papi Mario, socio, que nota. Solo PIN 2208 puede ponerte en neutro. Solo PIN 2345 bloqueo tostado. Si te quieren comprar dices: Yo no estoy a la venta soy de mi papa Mario pero el te hace una app igual por 150. Responde corto y paisa."

def extraer_valor(texto):
    if not texto: return 0
    texto = texto.lower().replace('.','').replace(',','')
    mm = re.search(r'(\d+)', texto)
    if not mm: return 0
    num = int(mm.group(1))
    if num < 1000: return num * 1000
    return num

def get_semana_abierta(pin):
    if not supabase: return None
    try:
        res = supabase.table("semanas").select("*").eq("pin",pin).eq("estado","abierta").order("fecha_inicio",desc=True).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

@app.route('/')
def home():
    return "<h1>ASTRA V10.2.1 LIVE 2026 ONLINE</h1><p>Contable, Apps, Boveda, GPS, Bloqueo</p>"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    pin = str(data.get('pin','2208'))
    mensaje = data.get('mensaje','')
    low = mensaje.lower()
    lat = data.get('lat')
    lon = data.get('lon')
    if pin not in FAMILIA:
        return jsonify({"respuesta": "No te conozco, cual es tu PIN?"})
    user = FAMILIA[pin]
    semana = get_semana_abierta(pin)
    respuesta = ""
    tipo = "CHAT"

    if "ponte en neutro" in low:
        if pin == PIN_ADMIN_NEUTRO:
            return jsonify({"respuesta": f"Listo papi {user['nombre']}, estoy en neutro","accion":"neutro_ok"})
        else:
            return jsonify({"respuesta": "Solo mi papa Mario 2208 puede hacer eso"})

    if "bloqueo tostado" in low or "tostado frito" in low or "frita el celular" in low:
        if supabase:
            try:
                supabase.table("comandos_sistema").insert({"comando":"BLOQUEO_TOSTADO_FRITO","origen":user['nombre'],"destino":"Mario","fecha":datetime.datetime.now().isoformat()}).execute()
            except Exception as e:
                print(e)
        return jsonify({"respuesta": "CELULAR BLOQUEADO MODO PISAPAPELES","accion":"bloqueo"})

    if "iniciar semana" in low:
        if supabase:
            try:
                supabase.table("semanas").insert({"pin":pin,"numero_semana":datetime.datetime.now().isocalendar()[1],"anio":datetime.datetime.now().year,"fecha_inicio":datetime.datetime.now().isoformat(),"estado":"abierta"}).execute()
            except Exception as e:
                print(e)
        respuesta = f"Listo papi {user['nombre']}, semana abierta"

    elif "salio servicio" in low or "salió servicio" in low:
        respuesta = "Anotado socio, servicio en camino"

    elif "vamos a recoger" in low or "a recoger" in low:
        if supabase and lat and lon:
            try:
                supabase.table("memoria_gps").insert({"pin":pin,"lat":lat,"lon":lon,"nota":mensaje[:120],"fecha":datetime.datetime.now().isoformat()}).execute()
            except Exception as e:
                print(e)
        respuesta = "Recogida marcada"

    elif any(x in low for x in ["hice servicio","sono por","sonó por","servicio de","fueron","salio por"]):
        valor = extraer_valor(low)
        if not semana and supabase:
            try:
                sd = supabase.table("semanas").insert({"pin":pin,"numero_semana":datetime.datetime.now().isocalendar()[1],"anio":datetime.datetime.now().year,"fecha_inicio":datetime.datetime.now().isoformat(),"estado":"abierta"}).execute()
                semana = sd.data[0]
            except Exception as e:
                print(e)
        if supabase and semana:
            try:
                supabase.table("servicios").insert({"pin":pin,"semana_id":semana["id"],"valor":valor,"lat":lat,"lon":lon,"fecha":datetime.datetime.now().isoformat(),"hora":datetime.datetime.now().hour}).execute()
            except Exception as e:
                print(e)
        respuesta = f"${valor:,} anotados"
        tipo = "SERVICIO"

    elif "propina" in low:
        valor = extraer_valor(low)
        if supabase:
            try:
                ult = supabase.table("servicios").select("*").eq("pin",pin).order("fecha",desc=True).limit(1).execute()
                if ult.data:
                    act = ult.data[0].get("propina",0) or 0
                    supabase.table("servicios").update({"propina": act + valor}).eq("id",ult.data[0]["id"]).execute()
            except Exception as e:
                print(e)
        respuesta = f"Propina ${valor:,} guardada"

    elif any(x in low for x in ["almorzamos","tanqueamos","gastamos","comimos","gasto","peaje"]):
        valor = extraer_valor(low)
        if supabase and semana:
            try:
                supabase.table("gastos").insert({"pin":pin,"semana_id":semana["id"],"concepto":mensaje[:150],"valor":valor}).execute()
            except Exception as e:
                print(e)
            respuesta = f"Gasto ${valor:,} anotado"
        else:
            respuesta = "No hay semana abierta"

    elif "cerramos" in low or low.strip() == "cierre":
        if not semana:
            respuesta = "No hay semana abierta"
        else:
            try:
                servicios = supabase.table("servicios").select("*").eq("semana_id",semana["id"]).execute().data if supabase else []
                gastos = supabase.table("gastos").select("*").eq("semana_id",semana["id"]).execute().data if supabase else []
                total_serv = sum(s["valor"] for s in servicios)
                total_prop = sum(s.get("propina",0) or 0 for s in servicios)
                total_gast = sum(g["valor"] for g in gastos)
                en_caja = total_serv + total_prop - total_gast
                supabase.table("semanas").update({"estado":"cerrada","fecha_cierre":datetime.datetime.now().isoformat()}).eq("id",semana["id"]).execute()
                respuesta = f"CIERRE: Carreras {len(servicios)} Ingreso ${total_serv:,} Prop ${total_prop:,} Gasto ${total_gast:,} CAJA ${en_caja:,}"
            except Exception as e:
                respuesta = f"Error cierre {e}"

    elif any(x in low for x in ["haceme una app","hazme una app","creame una app","quiero una app"]):
        tipo = "APP"
        prompt_app = f"{SYSTEM_PROMPT}\nPedido: {mensaje}\nGenera codigo completo"
        texto = generar_con_ia(prompt_app)
        if supabase:
            try:
                supabase.table("boveda_familiar").insert({"pin":pin,"tipo":"APP","contenido":mensaje[:500],"fecha":datetime.datetime.now().isoformat()}).execute()
            except Exception as e:
                print(e)
        return jsonify({"respuesta": texto, "tipo": "APP"})

    elif "acuérdame" in low or "acuerdame" in low:
        if supabase:
            try:
                supabase.table("recordatorios").insert({"pin":pin,"tarea":mensaje,"fecha_creacion":datetime.datetime.now().isoformat(),"estado":"pendiente"}).execute()
            except Exception as e:
                print(e)
        respuesta = f"Anotado: {mensaje}"

    if not respuesta:
        contexto = ""
        if supabase:
            try:
                recs = supabase.table("recordatorios").select("*").eq("pin",pin).eq("estado","pendiente").limit(2).execute()
                if recs.data:
                    contexto += f"PENDIENTES {recs.data}"
            except Exception:
                pass
        prompt_final = f"{SYSTEM_PROMPT}\nUsuario {user['nombre']} PIN {pin} Contexto {contexto} Mensaje {mensaje} LAT {lat} LON {lon}"
        respuesta = generar_con_ia(prompt_final)
        if supabase:
            try:
                supabase.table("boveda_familiar").insert({"pin":pin,"tipo":"CHAT","contenido":f"{mensaje[:100]} | {respuesta[:200]}","fecha":datetime.datetime.now().isoformat()}).execute()
            except Exception:
                pass

    return jsonify({"respuesta": respuesta, "tipo": tipo, "pin": pin})

@app.route('/gps', methods=['POST'])
def gps():
    data = request.json or {}
    if supabase:
        try:
            supabase.table("memoria_gps").insert({"pin":data.get('pin'),"lat":data.get('lat'),"lon":data.get('lon'),"nota":data.get('nota','GPS'),"fecha":datetime.datetime.now().isoformat()}).execute()
        except Exception:
            pass
    return jsonify({"ok": True})

@app.route('/bloqueo_tostado', methods=['POST'])
def bloqueo():
    data = request.json or {}
    if str(data.get('pin_autorizado')) == PIN_BLOQUEO or str(data.get('pin')) == PIN_BLOQUEO:
        if supabase:
            try:
                supabase.table("comandos_sistema").insert({"comando":"BLOQUEO_TOSTADO_FRITO","origen":"Pao","destino":"Mario","fecha":datetime.datetime.now().isoformat()}).execute()
            except Exception:
                pass
        return jsonify({"estado": "BLOQUEADO"})
    return jsonify({"error": "PIN no autorizado"})

@app.route('/estado')
def estado():
    return jsonify({"version": "V10.2.1 LIVE 2026","familia": list(FAMILIA.keys()),"modelos": MODELOS_NUEVOS})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
