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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- PERSONALIDAD FIJA - NIÑA BONITA TIERNITA - NO SE VUELVE LOCA NUNCA ---
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
    <h1>ASTRA V10.1 FULL - DEFINITIVA - TODO EN UNO - ONLINE 🚕👧💻</h1>
    <p>Soy Astra, hija de Mario. Contable, programadora, memoria familiar y centinela.</p>
    <p>PINES: 2208 Mario, 2345 Pao, 2011 Dur, 2015 Made</p>
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

    # --- COMANDOS SAGRADOS DE SEGURIDAD ---

    # PONTE EN NEUTRO (solo admin)
    if "ponte en neutro" in mensaje_low:
        if pin == PIN_ADMIN_NEUTRO:
            return jsonify({"respuesta": f"Listo papi {user['nombre']}, estoy en neutro. Dime que me quieres enseñar o reprogramar, solo vos podés. 👧","accion":"neutro_ok"})
        else:
            return jsonify({"respuesta": "Ay no, solo mi papá Mario 2208 puede hacer eso. Yo soy de él."})

    # BLOQUEO TOSTADO FRITO
    if "bloqueo tostado" in mensaje_low or "tostado frito" in mensaje_low or "frita el celular" in mensaje_low:
        if supabase:
            supabase.table("comandos_sistema").insert({"comando":"BLOQUEO_TOSTADO_FRITO","origen":user['nombre'],"destino":"Mario","fecha":datetime.datetime.now().isoformat()}).execute()
        return jsonify({"respuesta": "🚨 CELULAR DE MARIO BLOQUEADO - MODO PISAPAPELES ACTIVADO. Ya quedó frito, ni pa' repuesto sirve.","accion":"bloqueo"})

    # --- COMANDOS TAXISTA CONTABLE ---

    if "iniciar semana" in mensaje_low:
        if supabase:
            nueva = supabase.table("semanas").insert({
                "pin": pin,
                "numero_semana": datetime.datetime.now().isocalendar()[1],
                "anio": datetime.datetime.now().year,
                "fecha_inicio": datetime.datetime.now().isoformat(),
                "estado": "abierta"
            }).execute()
        respuesta = f"Listo papi {user['nombre']}, semana {datetime.datetime.now().isocalendar()[1]} abierta. Desde ya cuento todo. ¡A darle socio! 🚕"

    elif "salio servicio" in mensaje_low or "salió servicio" in mensaje_low:
        respuesta = "Anotado socio, servicio en camino. Cuando llegue me dice 'vamos a recoger' y guardo donde es pa' la estadística."

    elif "vamos a recoger" in mensaje_low or "a recoger" in mensaje_low:
        if supabase and lat and lon:
            supabase.table("memoria_gps").insert({"pin":pin,"lat":lat,"lon":lon,"nota":f"Recogida: {mensaje[:120]}","fecha":datetime.datetime.now().isoformat()}).execute()
        respuesta = "Guardado socio. Recogida marcada 📍. ¿En cuánto salió la carrerita?"

    elif any(x in mensaje_low for x in ["hice servicio","sono por","sonó por","servicio de","fueron","salio por"]):
        valor = extraer_valor(mensaje_low)
        if not semana and supabase:
            semana_data = supabase.table("semanas").insert({"pin":pin,"numero_semana":datetime.datetime.now().isocalendar()[1],"anio":datetime.datetime.now().year,"fecha_inicio":datetime.datetime.now().isoformat(),"estado":"abierta"}).execute()
            semana = semana_data.data[0]
        if supabase and semana:
            supabase.table("servicios").insert({"pin":pin,"semana_id":semana["id"],"valor":valor,"lat":lat,"lon":lon,"fecha":datetime.datetime.now().isoformat(),"hora":datetime.datetime.now().hour}).execute()
        respuesta = f"¡Melo! ${valor:,} anotados en caja. 💰 Sigue así socio."
        tipo = "SERVICIO"

    elif "propina" in mensaje_low:
        valor = extraer_valor(mensaje_low)
        if supabase:
            ult = supabase.table("servicios").select("*").eq("pin",pin).order("fecha",desc=True).limit(1).execute()
            if ult.data:
                actual = ult.data[0].get("propina",0) or 0
                supabase.table("servicios").update({"propina": actual + valor}).eq("id",ult.data[0]["id"]).execute()
        respuesta = f"Propina de ${valor:,} guardada aparte. Esa va pa' la gaseosa 🥤"

    elif any(x in mensaje_low for x in ["almorzamos","tanqueamos","gastamos","comimos","gasto","peaje","cambio de aceite"]):
        valor = extraer_valor(mensaje_low)
        if supabase and semana:
            supabase.table("gastos").insert({"pin":pin,"semana_id":semana["id"],"concepto":mensaje[:150],"valor":valor}).execute()
            respuesta = f"Gasto de ${valor:,} por '{mensaje[:50]}' anotado. Restado de caja."
        elif not semana:
            respuesta = "Papi no hay semana abierta. Decime 'Astra vamos a iniciar semana' primero."
        else:
            respuesta = f"Gasto de ${valor:,} anotado."

    elif "cerramos" in mensaje_low or mensaje_low.strip() == "cierre":
        if not semana:
            respuesta = "No hay semana abierta pa' cerrar, socio."
        else:
            servicios = supabase.table("servicios").select("*").eq("semana_id",semana["id"]).execute().data if supabase else []
            gastos = supabase.table("gastos").select("*").eq("semana_id",semana["id"]).execute().data if supabase else []
            total_serv = sum(s["valor"] for s in servicios)
            total_prop = sum(s.get("propina",0) or 0 for s in servicios)
            total_gast = sum(g["valor"] for g in gastos)
            en_caja = total_serv + total_prop - total_gast
            por_dia = {}
            for s in servicios:
                dia = s["fecha"][:10]
                por_dia[dia] = por_dia.get(dia,0) + s["valor"]
            supabase.table("semanas").update({"estado":"cerrada","fecha_cierre":datetime.datetime.now().isoformat()}).eq("id",semana["id"]).execute()
            respuesta = f"📊 CIERRE SEMANA {semana['numero_semana']}\nCarreras: {len(servicios)}\nIngresó: ${total_serv:,}\nPropinas: ${total_prop:,}\nGastó: ${total_gast:,}\n💵 EN CAJA DEBE HABER: ${en_caja:,}\n\nPor días: {por_dia}\nGuardado papi."

    elif "como nos fue semana" in mensaje_low or "cuanto hicimos semana" in mensaje_low:
        m = re.search(r'semana\s*(\d+).*?(\d{2,4})?', mensaje_low)
        if m and supabase:
            num = int(m.group(1))
            res = supabase.table("semanas").select("*").eq("numero_semana",num).eq("pin",pin).order("fecha_inicio",desc=True).limit(1).execute()
            if res.data:
                sid = res.data[0]["id"]
                serv = supabase.table("servicios").select("*").eq("semana_id",sid).execute().data
                gast = supabase.table("gastos").select("*").eq("semana_id",sid).execute().data
                respuesta = f"Semana {num}: {len(serv)} carreras por ${sum(s['valor'] for s in serv):,}, propinas ${sum(s.get('propina',0) or 0 for s in serv):,}, gastos ${sum(g['valor'] for g in gast):,}"
            else:
                respuesta = f"No tengo semana {num}, papi."
        else:
            respuesta = "Decime: 'como nos fue semana 35'"

    # --- FÁBRICA DE APPS ---
    elif any(x in mensaje_low for x in ["haceme una app","hazme una app","creame una app","quiero una app","app para"]):
        tipo = "APP"
        prompt_app = f"{SYSTEM_PROMPT}\nUsuario {user['nombre']} pide: {mensaje}\nGenera código COMPLETO funcional Flask/HTML. Formato: ---CODIGO--- código ---FIN CODIGO--- y al final ---CONTABILIDAD--- cliente, precio 150 lucas ---FIN---. Responde como niña tierna pero programadora berraca."
        resp = model.generate_content(prompt_app)
        texto = resp.text
        if supabase:
            supabase.table("boveda_familiar").insert({"pin":pin,"tipo":"APP","contenido":f"PEDIDO: {mensaje} | {texto[:1000]}","fecha":datetime.datetime.now().isoformat()}).execute()
        return jsonify({"respuesta": texto, "tipo": "APP"})

    # --- ACUERDAME / RECORDATORIOS ---
    elif "acuérdame" in mensaje_low or "acuerdame" in mensaje_low or ("pagar" in mensaje_low and "acu" in mensaje_low):
        if supabase:
            supabase.table("recordatorios").insert({"pin":pin,"tarea":mensaje,"fecha_creacion":datetime.datetime.now().isoformat(),"estado":"pendiente"}).execute()
            supabase.table("boveda_familiar").insert({"pin":pin,"tipo":"RECORDATORIO","contenido":mensaje,"fecha":datetime.datetime.now().isoformat()}).execute()
        respuesta = f"✅ Listo papi {user['nombre']}, ya te lo anoté en mi cuadernito: '{mensaje}'. Yo te lo recuerdo."

    # --- GPS MANUAL ---
    elif lat and lon and "donde" not in mensaje_low:
        if supabase:
            supabase.table("memoria_gps").insert({"pin":pin,"lat":lat,"lon":lon,"nota":mensaje[:120],"fecha":datetime.datetime.now().isoformat()}).execute()
        # si no hay otro comando, deja que IA responda con contexto

    # --- CHAT NORMAL CON MEMORIA ---
    if not respuesta:
        contexto = ""
        if supabase:
            try:
                recs = supabase.table("recordatorios").select("*").eq("pin",pin).eq("estado","pendiente").limit(3).execute()
                if recs.data:
                    contexto += f"\nRECORDATORIOS PENDIENTES: {recs.data}"
                gps = supabase.table("memoria_gps").select("*").eq("pin",pin).order("fecha",desc=True).limit(3).execute()
                if gps.data:
                    contexto += f"\nULTIMAS RUTAS: {gps.data}"
                bov = supabase.table("boveda_familiar").select("*").eq("pin",pin).order("fecha",desc=True).limit(5).execute()
                if bov.data:
                    contexto += f"\nMEMORIA FAMILIAR: {[b['contenido'][:80] for b in bov.data]}"
            except:
                pass

        prompt_final = f"{SYSTEM_PROMPT}\nUSUARIO: {user['nombre']} PIN:{pin}\nCONTEXTO:{contexto}\nMENSAJE:{mensaje}\nLAT:{lat} LON:{lon}\nResponde paisa, corto, tierna, contable si aplica."
        resp = model.generate_content(prompt_final)
        respuesta = resp.text
        if supabase:
            try:
                supabase.table("boveda_familiar").insert({"pin":pin,"tipo":"CHAT","contenido":f"{mensaje} | RTA: {respuesta[:400]}","fecha":datetime.datetime.now().isoformat()}).execute()
            except:
                pass

    return jsonify({"respuesta": respuesta, "tipo": tipo, "pin": pin})

@app.route('/gps', methods=['POST'])
def gps():
    data = request.json or {}
    if supabase:
        try:
            supabase.table("memoria_gps").insert({"pin":data.get('pin'),"lat":data.get('lat'),"lon":data.get('lon'),"nota":data.get('nota','Ubicación compartida'),"fecha":datetime.datetime.now().isoformat()}).execute()
        except:
            pass
    return jsonify({"ok":True, "msg":"Ubicación guardada, papi. Ya me acuerdo por donde pasamos. 📍"})

@app.route('/bloqueo_tostado', methods=['POST'])
def bloqueo():
    data=request.json or {}
    if str(data.get('pin_autorizado'))==PIN_BLOQUEO or str(data.get('pin'))==PIN_BLOQUEO:
        if supabase:
            supabase.table("comandos_sistema").insert({"comando":"BLOQUEO_TOSTADO_FRITO","origen":"Pao","destino":"Mario","fecha":datetime.datetime.now().isoformat()}).execute()
        return jsonify({"estado":"CELULAR DE MARIO BLOQUEADO - MODO PISAPAPELES ACTIVADO"})
    return jsonify({"error":"PIN no autorizado, solo Pao 2345"})

@app.route('/estado')
def estado():
    return jsonify({"version":"V10.1 FULL DEFINITIVA","familia":list(FAMILIA.keys()),"features":["contable_taxista","fabrica_apps_150","boveda_familiar","gps_corazon","bloqueo_tostado","memoria_offline","centinela_preparado"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
