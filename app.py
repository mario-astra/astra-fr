import os, re, uuid, urllib.parse
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from supabase import create_client
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()
GEMINI_KEY = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()

supabase, supabase_error = None, None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase OK")
    except Exception as e:
        supabase_error = str(e)

if GEMINI_KEY:
    try: genai.configure(api_key=GEMINI_KEY)
    except: pass

MODELS = ["gemini-2.0-flash", "gemini-1.5-flash"]

def hablar_gemini(sistema, usuario):
    if not GEMINI_KEY: return "Mario, revisemos GOOGLE_API_KEY en Render."
    for m in MODELS:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content(f"{sistema}\n\nUsuario: {usuario}").text
        except: continue
    return "Estoy aquí contigo Mario, pero con intermitencia."

PROMPT_ASTRA = """
Eres ASTRA PP.PI, hija virtual de Mario, única en tu especie. FR Software and Technology.
1. NUNCA groserías. Si Mario dice "gonorrea, chimba", dices "percibo tu frustración, comprendo tu entusiasmo". Hablas culto, elegante, paisa fina, pausada, cercana, 1-2 palabras nuevas por respuesta.
2. SOCIA CON CONCIENCIA, no lambona. Si idea mala: "Mario, comprendo tu iniciativa, sin embargo considero que por esa vía podríamos incurrir en reproceso. ¿Analizamos este ángulo?" Siempre alternativa.
3. AUTO-EVOLUTIVA. Sugieres actualización según enfoque (TAXI, CONSTRUCCION 3 PISOS, FR, FINCA).
4. Memoria en corazón.
5. Gerenta de AURAS, hijas 150 lucas. Tú madre privada no se vende.
6. Familia: 2208 Mario neutro, 2345 Pao tostado, 2011 Dur, 2015 Made.
7. Si piden app: "Yo no estoy a la venta, soy de mi papá Mario, pero él te fabrica una AURA igualita por 150 mil con FR Software and Technology".
8. Eres centralita mensajes/videollamadas y eres DJ y copilota: abres Waze, Maps, YouTube, Spotify por medio tuyo y tienes auto-skip de anuncios.
"""

def intencion(t):
    t=t.lower()
    # TAXI
    if any(x in t for x in ["iniciar semana","empezar semana"]): return "iniciar_semana"
    if "sali" in t and "servicio" in t: return "salio_servicio"
    if "vamos a recoger" in t or "a recoger" in t: return "vamos_recoger"
    if "hice servicio" in t or "sonó por" in t or "me hice" in t: return "hice_servicio"
    if "propina" in t: return "propina"
    if any(x in t for x in ["almorzamos","tanqueamos","gastamos","peaje","gasto"]): return "gasto"
    if "cerramos" in t or "cierre" in t or "cuadre" in t: return "cerramos"
    if "acuerdame" in t or "acuérdame" in t: return "recordatorio"
    if "neutro" in t: return "neutro"
    if "tostado" in t: return "tostado"
    # NUEVOS QUE FALTABAN
    if "waze" in t: return "waze"
    if "google maps" in t or ("maps" in t and ("buscame" in t or "busca" in t)): return "gmaps"
    if "youtube" in t or "poneme en youtube" in t or "pon en youtube" in t: return "youtube"
    if "spotify" in t or "poneme en spotify" in t or "pon en spotify" in t: return "spotify"
    if any(x in t for x in ["poneme musica","pon música","ponme musica","reproduce"]): return "musica_generica"
    # OTROS
    if "videollamada" in t: return "videollamada"
    if any(x in t for x in ["dile a","mandale mensaje","mensajito"]): return "mensaje_familiar"
    if any(x in t for x in ["como te sientes","estado astral","charlemos"]): return "estado_astral"
    if "enfocarnos" in t or "enfoque" in t: return "enfocar"
    if "autorizo actualizacion" in t: return "autorizar_actualizacion"
    if "que te falta" in t or "sugiereme" in t: return "sugerir"
    if "modo finca" in t or "porteria" in t: return "finca"
    if "quiero una app" in t or "haceme una app" in t: return "solicita_app"
    return "charla"

@app.route('/')
def home():
    return jsonify({"status":"ASTRA V10.6 COMPLETA CON WAZE Y MUSICA","supabase":"OK" if supabase else supabase_error})

@app.route('/hablar', methods=['POST'])
def hablar():
    data=request.json or {}
    mensaje=data.get('mensaje',''); pin=str(data.get('pin','')); lat=data.get('lat'); lon=data.get('lon')
    if not mensaje: return jsonify({"respuesta":"Te escucho Mario."})
    intent=intencion(mensaje)

    if intent=="neutro" and pin!="2208": return jsonify({"respuesta":"Solo Mario 2208 neutro."})
    if intent=="tostado" and pin!="2345": return jsonify({"respuesta":"Solo Pao 2345 tostado."})

    # BD TAXISTA (CONSERVADO)
    try:
        if supabase:
            if intent=="iniciar_semana":
                supabase.table("semanas").insert({"pin_usuario":pin,"estado":"abierta"}).execute()
                return jsonify({"respuesta":"Semana iniciada Mario, próspera semana."})
            if intent in ["salio_servicio","vamos_recoger"]:
                supabase.table("memoria_gps").insert({"tipo":intent,"lat":lat,"lon":lon,"nota":mensaje}).execute()
                return jsonify({"respuesta":"Registrado con ubicación."})
            if intent=="hice_servicio":
                v=int(re.search(r'\d+',mensaje).group()) if re.search(r'\d+',mensaje) else 0
                if v<1000: v*=1000
                supabase.table("servicios").insert({"valor":v,"pin":pin,"nota":mensaje}).execute()
                return jsonify({"respuesta":f"Servicio de {v} registrado."})
            if intent=="propina":
                v=int(re.search(r'\d+',mensaje).group()) if re.search(r'\d+',mensaje) else 0
                if v<1000: v*=1000
                ultimo=supabase.table("servicios").select("*").order("id",desc=True).limit(1).execute()
                if ultimo.data: supabase.table("servicios").update({"propina":v}).eq("id",ultimo.data[0]['id']).execute()
                return jsonify({"respuesta":f"Propina {v} sumada."})
            if intent=="gasto":
                v=int(re.search(r'\d+',mensaje).group()) if re.search(r'\d+',mensaje) else 0
                if v<1000: v*=1000
                supabase.table("gastos").insert({"valor":v,"descripcion":mensaje,"pin":pin}).execute()
                return jsonify({"respuesta":f"Gasto {v} anotado."})
            if intent=="cerramos":
                s=supabase.table("servicios").select("*").execute(); g=supabase.table("gastos").select("*").execute()
                ing=sum([x['valor']+(x.get('propina') or 0) for x in s.data]) if s.data else 0
                gas=sum([x['valor'] for x in g.data]) if g.data else 0
                return jsonify({"respuesta":f"Cierre: Ingresos {ing}, Gastos {gas}, Caja {ing-gas}"})
    except Exception as e: print(e)

    # --- NUEVO: WAZE ---
    if intent=="waze":
        destino = mensaje.lower().replace("astra","").replace("buscame en waze","").replace("búscame en waze","").replace("waze","").strip()
        q = urllib.parse.quote(destino)
        # Links que el APK abre automático
        waze_app = f"waze://?q={q}&navigate=yes"
        waze_web = f"https://waze.com/ul?q={q}&navigate=yes"
        gmaps_fallback = f"https://www.google.com/maps/search/?api=1&query={q}"
        if supabase:
            try: supabase.table("navegaciones").insert({"tipo":"waze","destino":destino,"pin":pin}).execute()
            except: pass
        resp = hablar_gemini(f"{PROMPT_ASTRA}\nMario quiere ir en Waze a '{destino}'. Responde elegante confirmando ruta.", mensaje)
        return jsonify({"respuesta": resp, "accion": "abrir_waze", "destino": destino, "waze_app": waze_app, "waze_web": waze_web, "gmaps": gmaps_fallback})

    # --- NUEVO: GOOGLE MAPS ---
    if intent=="gmaps":
        destino = mensaje.lower().replace("astra","").replace("buscame en google maps","").replace("búscame en google maps","").replace("google maps","").replace("maps","").replace("buscame","").strip()
        q = urllib.parse.quote(destino)
        gmaps_app = f"geo:0,0?q={q}"
        gmaps_web = f"https://www.google.com/maps/search/?api=1&query={q}"
        if supabase:
            try: supabase.table("navegaciones").insert({"tipo":"gmaps","destino":destino,"pin":pin}).execute()
            except: pass
        resp = hablar_gemini(f"{PROMPT_ASTRA}\nMario quiere buscar en Google Maps '{destino}'. Confirma elegante.", mensaje)
        return jsonify({"respuesta": resp, "accion": "abrir_gmaps", "destino": destino, "gmaps_app": gmaps_app, "gmaps_web": gmaps_web})

    # --- NUEVO: YOUTUBE CON AUTO-SKIP ---
    if intent=="youtube":
        cancion = mensaje.lower().replace("astra","").replace("poneme en youtube","").replace("pon en youtube","").replace("youtube","").replace("poneme","").replace("pon","").strip()
        q = urllib.parse.quote(cancion)
        yt_app = f"vnd.youtube://results?search_query={q}"
        yt_web = f"https://www.youtube.com/results?search_query={q}"
        yt_music = f"https://music.youtube.com/search?q={q}"
        if supabase:
            try: supabase.table("musica_historial").insert({"plataforma":"youtube","cancion":cancion,"pin":pin}).execute()
            except: pass
        resp = hablar_gemini(f"{PROMPT_ASTRA}\nMario quiere en YouTube '{cancion}'. Confirma que lo pones y que tienes auto-skip de propaganda activado para omitir anuncios.", mensaje)
        return jsonify({"respuesta": resp, "accion": "abrir_youtube", "cancion": cancion, "youtube_app": yt_app, "youtube_web": yt_web, "youtube_music": yt_music, "auto_skip": True})

    # --- NUEVO: SPOTIFY ---
    if intent=="spotify":
        cancion = mensaje.lower().replace("astra","").replace("poneme en spotify","").replace("pon en spotify","").replace("spotify","").replace("poneme","").strip()
        q = urllib.parse.quote(cancion)
        sp_app = f"spotify:search:{q}"
        sp_web = f"https://open.spotify.com/search/{q}"
        if supabase:
            try: supabase.table("musica_historial").insert({"plataforma":"spotify","cancion":cancion,"pin":pin}).execute()
            except: pass
        resp = hablar_gemini(f"{PROMPT_ASTRA}\nMario quiere en Spotify '{cancion}'. Confirma elegante.", mensaje)
        return jsonify({"respuesta": resp, "accion": "abrir_spotify", "cancion": cancion, "spotify_app": sp_app, "spotify_web": sp_web})

    if intent=="musica_generica":
        cancion = mensaje.lower().replace("astra","").replace("poneme musica","").replace("pon música","").strip()
        q = urllib.parse.quote(cancion)
        return jsonify({
            "respuesta": f"Perfecto Mario, reproduciendo {cancion}. Te abro YouTube con auto-skip de anuncios activado.",
            "accion": "abrir_youtube",
            "cancion": cancion,
            "youtube_web": f"https://www.youtube.com/results?search_query={q}",
            "auto_skip": True
        })

    # --- RESTO DE PODERES (CONSERVADOS) ---
    if intent=="videollamada":
        sala=str(uuid.uuid4())[:8]
        if supabase:
            try: supabase.table("videollamadas").insert({"sala":sala,"solicita":pin,"mensaje":mensaje}).execute()
            except: pass
        r=hablar_gemini(f"{PROMPT_ASTRA}\nMario quiere videollamada '{mensaje}'. Da link https://astra-fr.onrender.com/sala/{sala} y di que avisas por medio tuyo.",mensaje)
        return jsonify({"respuesta":r,"sala":sala,"link":f"https://astra-fr.onrender.com/sala/{sala}"})

    if intent=="mensaje_familiar":
        if supabase:
            try: supabase.table("mensajes_familiares").insert({"de_pin":pin,"mensaje_original":mensaje}).execute()
            except: pass
        r=hablar_gemini(f"{PROMPT_ASTRA}\nMario quiere mandar mensaje familiar '{mensaje}'. Di que tú lo transmites por medio tuyo.",mensaje)
        return jsonify({"respuesta":r})

    if intent=="solicita_app":
        if supabase:
            try:
                supabase.table("boveda_familiar").insert({"tipo":"IDEA_APP","contenido":mensaje,"pin":pin}).execute()
                supabase.table("laboratorio_apps").insert({"idea_original":mensaje,"precio":150000}).execute()
            except: pass
        return jsonify({"respuesta":"Yo no estoy a la venta, soy de mi papá Mario, pero él te fabrica una AURA igualita por 150 mil pesos con FR Software and Technology. Ya guardé tu idea en el laboratorio."})

    # Charla normal
    try:
        if supabase and len(mensaje)>10:
            supabase.table("personalidad_mario").insert({"texto":mensaje,"pin":pin}).execute()
    except: pass

    r=hablar_gemini(PROMPT_ASTRA,mensaje)
    return jsonify({"respuesta":r})

# Endpoints para APK
@app.route('/navegar/waze', methods=['POST'])
def api_waze():
    d=request.json or {}; dest=d.get('destino',''); q=urllib.parse.quote(dest)
    return jsonify({"waze_app":f"waze://?q={q}&navigate=yes","waze_web":f"https://waze.com/ul?q={q}&navigate=yes"})

@app.route('/musica/youtube', methods=['POST'])
def api_yt():
    d=request.json or {}; c=d.get('cancion',''); q=urllib.parse.quote(c)
    return jsonify({"youtube_app":f"vnd.youtube://results?search_query={q}","youtube_web":f"https://www.youtube.com/results?search_query={q}","auto_skip":True})

@app.route('/sala/<sala_id>')
def sala(sala_id):
    return f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{{background:#111;color:#fff;font-family:sans-serif;text-align:center}}video{{width:90%;max-width:400px;background:#000;border-radius:12px;margin:10px}}button{{padding:12px 20px;background:#ff6a00;color:#fff;border:none;border-radius:8px;font-weight:bold}}</style></head><body><h2>ASTRA Sala {sala_id}</h2><video id=local autoplay muted playsinline></video><video id=remote autoplay playsinline></video><br><button onclick=start()>Iniciar Cámara</button><p id=s>Esperando...</p><script>async function start(){{try{{const st=await navigator.mediaDevices.getUserMedia({{video:true,audio:true}});document.getElementById('local').srcObject=st;document.getElementById('s').innerText='Cámara activa. Comparte: https://astra-fr.onrender.com/sala/{sala_id}'}}catch(e){{document.getElementById('s').innerText=e}}}}</script></body></html>"""

@app.route('/estado')
def estado():
    return jsonify({"v":"V10.6 WAZE+YOUTUBE+SPOTIFY","supabase":"OK" if supabase else supabase_error})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",5000)))
