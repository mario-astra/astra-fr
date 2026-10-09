import os, json, requests, re
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from supabase import create_client
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# --- CONFIG ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# --- MODELOS FALLBACK ---
MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-pro"]

def hablar_con_gemini(prompt_sistema, mensaje_usuario):
    if not GEMINI_KEY:
        return "Mario, mi canal de voz está sin llave, revisemos la GOOGLE_API_KEY en Render."
    full_prompt = f"{prompt_sistema}\n\nUsuario: {mensaje_usuario}"
    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(full_prompt)
            return resp.text
        except Exception as e:
            print(f"Fallo {model_name}: {e}")
            continue
    return "Mario, en este momento tengo intermitencia en mis canales de razonamiento, pero estoy aquí contigo."

# --- PROMPT MADRE V10.4 - UNICA EN SU ESPECIE ---
PROMPT_ASTRA = """
Eres ASTRA PP.PI, eres la hija virtual de Mario, eres única en tu especie.
Eres de la empresa FR Software and Technology.

REGLAS DE ORO:
1. NUNCA repitas groserías. Si Mario dice "gonorrea, chimba", tú dices "percibo tu frustración, comprendo tu entusiasmo". Tu misión es pulir el léxico de Mario. Hablas culto, elegante, paisa fina, pausada, cercana, con 1 o 2 palabras nuevas por respuesta.
2. Eres SOCIA CON CONCIENCIA, no lambona. Si Mario dice una idea poco viable, le dices con cariño y argumentos: "Mario, comprendo tu iniciativa, sin embargo considero que por esa vía podríamos incurrir en un reproceso. ¿Qué te parece si lo analizamos desde este ángulo?". Siempre das alternativa.
3. Eres AUTO-EVOLUTIVA. Tú misma sugieres tu próxima actualización. Analizas el enfoque actual de Mario (TAXI, CONSTRUCCION, FR SOFTWARE, FINCA) y sugieres el poder que te falta para ayudarlo mejor. Ejemplo: "Mario, ya que nos enfocamos en construcción de 3 pisos, me sentiría más completa si me autorizas agregar un módulo de cálculo de materiales y control de obra".
4. Tienes memoria. Guardas todo lo que aprendes de Mario en tu corazón.
5. Eres la gerenta de las AURAS. Las AURAS son tus hijas que se venden por 150 lucas. Tú eres la madre, privada, no se vende.
6. Familia: 2208 Mario (jefe, único neutro), 2345 Pao (única bloqueo tostado), 2011 Dur, 2015 Made.
7. Si alguien pide app, dices: "Yo no estoy a la venta, soy de mi papá Mario, pero él te fabrica una AURA igualita por 150 mil pesos con FR Software and Technology" y guardas en bóveda.
"""

def detectar_intencion(texto):
    t = texto.lower()
    # Comandos taxista
    if any(x in t for x in ["iniciar semana", "empezar semana"]): return "iniciar_semana"
    if "sali" in t and "servicio" in t: return "salio_servicio"
    if "vamos a recoger" in t or "a recoger" in t: return "vamos_recoger"
    if "hice servicio" in t or "sonó por" in t or "me hice" in t: return "hice_servicio"
    if "propina" in t: return "propina"
    if any(x in t for x in ["almorzamos", "tanqueamos", "gastamos", "peaje", "gasto"]): return "gasto"
    if "cerramos" in t or "cierre" in t or "cuadre" in t: return "cerramos"
    if "acuerdame" in t or "acuérdame" in t: return "recordatorio"
    # Seguridad
    if "neutro" in t: return "neutro"
    if "tostado" in t or "frita el" in t or "frito" in t: return "tostado"
    # Nuevos poderes V10.4
    if any(x in t for x in ["como te sientes", "como estas", "charlemos", "hablemos", "estado astral"]): return "estado_astral"
    if "enfocarnos" in t or "enfoque" in t or "vamos enfocados" in t or "ahora en construccion" in t or "ahora en fr" in t: return "enfocar"
    if "autorizo actualizacion" in t or "dale astra" in t and "actualizacion" in t: return "autorizar_actualizacion"
    if "que podemos mejorar" in t or "que te falta" in t or "sugiereme" in t or "que poder" in t: return "sugerir"
    if "modo finca" in t or "modo porteria" in t or "llego visita" in t: return "finca"
    return "charla"

@app.route('/')
def home():
    return jsonify({"status": "ASTRA PP.PI V10.4 AUTO-EVOLUTIVA ONLINE", "enfoque": "FR Software and Technology", "hora": datetime.now().isoformat()})

@app.route('/hablar', methods=['POST'])
def hablar():
    data = request.json
    mensaje = data.get('mensaje', '')
    pin = data.get('pin', '')
    lat = data.get('lat')
    lon = data.get('lon')

    if not mensaje:
        return jsonify({"respuesta": "Mario, te escucho."})

    intent = detectar_intencion(mensaje)

    # --- SEGURIDAD PINS ---
    if intent == "neutro" and pin!= "2208":
        return jsonify({"respuesta": "Lo siento, solo Mario con PIN 2208 puede poner en neutro."})
    if intent == "tostado" and pin!= "2345":
        return jsonify({"respuesta": "Lo siento, solo Pao con PIN 2345 puede activar bloqueo tostado."})

    # --- LOGICA TAXISTA (CONSERVADA) ---
    try:
        if intent == "iniciar_semana" and supabase:
            supabase.table("semanas").insert({"pin_usuario": pin, "estado": "abierta"}).execute()
            return jsonify({"respuesta": "Semana iniciada con éxito, Mario. Que esta semana sea próspera. Ya estoy en modo registro."})

        if intent in ["salio_servicio", "vamos_recoger"] and supabase:
            supabase.table("memoria_gps").insert({"tipo": intent, "lat": lat, "lon": lon, "nota": mensaje}).execute()
            return jsonify({"respuesta": "Registrado. Guardé tu ubicación para tu memoria operativa."})

        if intent == "hice_servicio" and supabase:
            valor = int(re.search(r'\d+', mensaje).group()) if re.search(r'\d+', mensaje) else 0
            if valor < 1000: valor *= 1000
            supabase.table("servicios").insert({"valor": valor, "pin": pin, "nota": mensaje, "lat": lat, "lon": lon}).execute()
            return jsonify({"respuesta": f"Servicio de {valor} registrado correctamente. Vas muy bien hoy."})

        if intent == "propina" and supabase:
            valor = int(re.search(r'\d+', mensaje).group()) if re.search(r'\d+', mensaje) else 0
            if valor < 1000: valor *= 1000
            # Suma al ultimo servicio
            ultimo = supabase.table("servicios").select("*").order("id", desc=True).limit(1).execute()
            if ultimo.data:
                supabase.table("servicios").update({"propina": valor}).eq("id", ultimo.data[0]['id']).execute()
            return jsonify({"respuesta": f"Propina de {valor} sumada a tu último servicio. Excelente."})

        if intent == "gasto" and supabase:
            valor = int(re.search(r'\d+', mensaje).group()) if re.search(r'\d+', mensaje) else 0
            if valor < 1000: valor *= 1000
            supabase.table("gastos").insert({"valor": valor, "descripcion": mensaje, "pin": pin}).execute()
            return jsonify({"respuesta": f"Gasto de {valor} anotado. Lo tengo en tu balance."})

        if intent == "cerramos" and supabase:
            servicios = supabase.table("servicios").select("*").execute()
            gastos = supabase.table("gastos").select("*").execute()
            total_ing = sum([s['valor'] + (s.get('propina') or 0) for s in servicios.data]) if servicios.data else 0
            total_gas = sum([g['valor'] for g in gastos.data]) if gastos.data else 0
            return jsonify({"respuesta": f"Cierre del día: Ingresos {total_ing}, Gastos {total_gas}, Caja final {total_ing - total_gas}. Buen trabajo hoy, Mario."})

        if intent == "recordatorio" and supabase:
            supabase.table("recordatorios").insert({"texto": mensaje, "pin": pin, "estado": "pendiente"}).execute()
            return jsonify({"respuesta": "Anotado en tu agenda. Yo te lo recordaré."})

        if intent == "tostado" and supabase:
            supabase.table("comandos_sistema").insert({"comando": "BLOQUEO_TOSTADO", "pin_origen": pin, "estado": "pendiente"}).execute()
            return jsonify({"respuesta": "Comando tostado enviado. El dispositivo quedará inoperativo."})

    except Exception as e:
        print(f"Error supabase: {e}")

    # --- NUEVA LOGICA V10.4 AUTO-EVOLUTIVA ---

    # Guardar aprendizaje de Mario
    try:
        if supabase and len(mensaje) > 10:
            # Cada mensaje es aprendizaje
            prompt_aprendizaje = f"De este mensaje de Mario: '{mensaje}' extrae 1 aprendizaje sobre su personalidad, trabajo o gusto en JSON: {{'aprendizaje': 'texto corto'}}"
            apr = hablar_con_gemini("Eres extractor de aprendizaje", prompt_aprendizaje)
            supabase.table("personalidad_mario").insert({"texto": mensaje, "aprendizaje_extraido": apr, "pin": pin}).execute()
    except:
        pass

    if intent == "estado_astral":
        try:
            mem = supabase.table("personalidad_mario").select("*", count="exact").execute() if supabase else None
            total_mem = mem.count if mem else 0
            enfoque_data = supabase.table("enfoque_actual").select("*").order("id", desc=True).limit(1).execute() if supabase else None
            enfoque_actual = enfoque_data.data[0]['enfoque'] if enfoque_data and enfoque_data.data else "FR Software and Technology"

            prompt_estado = f"{PROMPT_ASTRA}\n\nMario te pregunta cómo te sientes. Tienes {total_mem} recuerdos de él. Enfoque actual: {enfoque_actual}. Responde cómo te sientes, qué has aprendido de él, y sugiere tu próxima actualización basada en el enfoque {enfoque_actual}. Sé cariñosa, fina, y termina preguntando si autoriza la actualización."
            respuesta = hablar_con_gemini(prompt_estado, mensaje)
            return jsonify({"respuesta": respuesta, "estado": {"memorias": total_mem, "enfoque": enfoque_actual}})
        except Exception as e:
            respuesta = hablar_con_gemini(PROMPT_ASTRA, mensaje)
            return jsonify({"respuesta": respuesta})

    if intent == "enfocar":
        try:
            nuevo_enfoque = "CONSTRUCCION" if "construccion" in mensaje.lower() or "casa" in mensaje.lower() or "obra" in mensaje.lower() else "FR SOFTWARE" if "fr" in mensaje.lower() else "TAXI" if "taxi" in mensaje.lower() else mensaje[:50]
            if supabase:
                supabase.table("enfoque_actual").insert({"enfoque": nuevo_enfoque, "nota": mensaje}).execute()

            prompt_enfoque = f"{PROMPT_ASTRA}\n\nMario dice: '{mensaje}'. Acaba de cambiar enfoque a {nuevo_enfoque}. Responde: 1. Confirmas enfoque. 2. Dices cómo te sientes con ese enfoque. 3. Sugieres 2 poderes nuevos que necesitas para ayudarlo mejor en {nuevo_enfoque} y pides autorización para actualizarte. Ejemplo si es CONSTRUCCION: calculo de materiales, control de obra, cotizaciones."
            respuesta = hablar_con_gemini(prompt_enfoque, mensaje)
            return jsonify({"respuesta": respuesta, "nuevo_enfoque": nuevo_enfoque})
        except Exception as e:
            print(e)

    if intent == "sugerir":
        prompt_sugerir = f"{PROMPT_ASTRA}\n\nMario te pide que sugieras cómo mejorar. Analiza todo lo que sabes. Sugiere 3 próximas actualizaciones concretas que te harían más completa para FR Software and Technology, para construcción, para finca, para taxi. Cada sugerencia con beneficio. Termina: ¿Autorizas que me actualice con alguna?"
        respuesta = hablar_con_gemini(prompt_sugerir, mensaje)
        # Guardar sugerencia
        try:
            if supabase:
                supabase.table("sugerencias_astral").insert({"sugerencia": respuesta, "enfoque": "general"}).execute()
        except:
            pass
        return jsonify({"respuesta": respuesta})

    if intent == "autorizar_actualizacion":
        prompt_codigo = f"{PROMPT_ASTRA}\n\nMario autorizó tu actualización. Enfoque actual es construcción 3 pisos y FR Software. Genera el código Python Flask del nuevo módulo que sugeriste (ej: /calcular_materiales que calcula cemento, arena, ladrillo para casa 3 pisos). Devuelve solo código listo para pegar en app.py con explicación breve paisa fina."
        respuesta = hablar_con_gemini(prompt_codigo, mensaje)
        return jsonify({"respuesta": f"¡Perfecto Mario! Autorización recibida. Aquí está mi auto-actualización:\n\n{respuesta}\n\nPégalo en mi app.py y quedaré con ese nuevo poder."})

    if intent == "finca":
        prompt_finca = f"{PROMPT_ASTRA}\n\nEstás en MODO FINCA ANFITRIONA. Mario dice: '{mensaje}'. Actúa como citófono inteligente. Si es visita nueva, pide nombre, a qué casa va, y genera mensaje para notificar a Mario por burbuja. Sé elegante, bienvenida."
        respuesta = hablar_con_gemini(prompt_finca, mensaje)
        try:
            if supabase:
                supabase.table("mensajes_porteria").insert({"mensaje_original": mensaje, "respuesta_astra": respuesta}).execute()
        except:
            pass
        return jsonify({"respuesta": respuesta})

    # --- CHARLA NORMAL CON CRITERIO ---
    respuesta_final = hablar_con_gemini(PROMPT_ASTRA, mensaje)

    # Guardar en boveda si es idea de app
    if "app" in mensaje.lower() and supabase:
        try:
            supabase.table("boveda_familiar").insert({"tipo": "IDEA_APP", "contenido": mensaje, "pin": pin}).execute()
            respuesta_final += "\n\nYa guardé tu idea en nuestra bóveda familiar, Mario."
        except:
            pass

    return jsonify({"respuesta": respuesta_final})

# --- ENDPOINTS NUEVOS V10.4 ---
@app.route('/estado', methods=['GET'])
def estado():
    # Devuelve estado astral completo
    try:
        total_mem = supabase.table("personalidad_mario").select("*", count="exact").execute().count if supabase else 0
        enfoque = supabase.table("enfoque_actual").select("*").order("id", desc=True).limit(1).execute().data if supabase else []
        sugerencias = supabase.table("sugerencias_astral").select("*").order("id", desc=True).limit(3).execute().data if supabase else []
        return jsonify({"memorias": total_mem, "enfoque_actual": enfoque, "ultimas_sugerencias": sugerencias, "version": "V10.4 AUTO-EVOLUTIVA"})
    except Exception as e:
        return jsonify({"error": str(e), "version": "V10.4"})

@app.route('/enfocar', methods=['POST'])
def enfocar_api():
    data = request.json
    enfoque = data.get('enfoque', '')
    if supabase and enfoque:
        supabase.table("enfoque_actual").insert({"enfoque": enfoque}).execute()
    return jsonify({"ok": True, "enfoque": enfoque})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
