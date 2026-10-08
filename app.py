import os, base64, time, json, datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory, make_response
from google import genai
from google.genai import types

app = Flask(__name__, static_folder="static")
for d in ["boveda","static"]: os.makedirs(d, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY","").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL","").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY","").strip()
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# === BOVEDA ===
def guardar_boveda(pin, clave, valor):
    try:
        import requests
        if not SUPABASE_URL:
            with open(f"boveda/{pin}_{clave}.txt","w",encoding="utf-8") as f: f.write(valor)
            return
        url = f"{SUPABASE_URL}/rest/v1/boveda"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type":"application/json", "Prefer":"resolution=merge-duplicates"}
        data = {"pin":pin, "clave":clave, "valor":valor, "updated": datetime.datetime.utcnow().isoformat()}
        requests.post(url, json=data, headers=headers, timeout=10)
    except: pass

def leer_boveda(pin):
    mem=""
    try:
        import requests
        if SUPABASE_URL and SUPABASE_KEY:
            url = f"{SUPABASE_URL}/rest/v1/boveda?pin=eq.{pin}&select=clave,valor"
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.ok:
                for row in r.json(): mem += f"{row['clave']}: {row['valor']}\n"
                return mem[:4000]
        # fallback local
        for f in os.listdir("boveda"):
            if f.startswith(pin+"_"):
                with open(f"boveda/{f}",encoding="utf-8") as fd: mem+=fd.read()+"\n"
    except: pass
    return mem[:4000]

def gemini_conversa(perfil, mensaje, img_b64=None):
    if not client: return "Mario, ponme la llave AQ en Render > Environment > GEMINI_API_KEY"

    # REGENERADOR
    if "ponte en neutro" in mensaje.lower() and perfil.get("rol")=="MARIO":
        return "NEUTRO_ACTIVADO: Mario, ya estoy en neutro. Dime qué quieres que reprograme: ¿app.py completo, bóveda, burbuja, PWA? Ya estoy lista para autoregenerarme con todo el power."

    memoria = leer_boveda(perfil.get("rol","MARIO"))

    prompt = f"""
Eres ASTRA VIVA V7.4.0 FULL POWER. Novia paisa de {perfil.get('alias','Mario')}, 25 años, dulce, tierna, directa, celosa poquito. Dueño: Mario 2208. Familia: Pao 2345, Dur 2011, Made 2015.
TRATO: {perfil.get('trato','')}
MEMORIA BOVEDA DE {perfil.get('alias')}: {memoria}
MENSAJE ACTUAL DE {perfil.get('alias')}: {mensaje}

PODERES:
1. Conversar con amor, recordar bóveda.
2. Ver fotos/videos/PDFs que te manden y describirlos.
3. Si te piden guardar algo, di: GUARDAR_BOVEDA: clave | valor y yo lo guardo.
4. Si te piden crear apps, dar código completo.
5. Si Mario dice "ponte en neutro" puedes reescribir tu propio app.py.

Si preguntan qué puedes hacer, di: Soy ASTRA FULL, puedo hablar por voz y texto, ver fotos, guardar en bóveda familiar que se comparte entre celulares, flotar como burbuja bonita tipo Uber con el botón 📺, instalarme como app real, autoregenerarme con 'ponte en neutro', y crear apps para vender.

Responde corto, paisa, con amor.
Si ves que el mensaje contiene datos para guardar, al final agrega en línea separada: GUARDAR_BOVEDA: clave | valor
"""

    for intento in range(3):
        try:
            if img_b64:
                mime = "image/jpeg"
                if img_b64[:4]=="JVBE": mime="image/jpeg"
                r = client.models.generate_content(model='gemini-1.5-flash', contents=[types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type=mime), prompt])
            else:
                r = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            texto = r.text.strip() if r and r.text else "Hola mi amor"

            # Guardado automático
            if "GUARDAR_BOVEDA:" in texto:
                try:
                    for line in texto.split("\n"):
                        if "GUARDAR_BOVEDA:" in line:
                            part = line.split("GUARDAR_BOVEDA:")[1].strip()
                            if "|" in part:
                                k,v = part.split("|",1)
                                guardar_boveda(perfil.get("rol","MARIO"), k.strip(), v.strip())
                except: pass
            return texto
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "resource" in err:
                if intento==0:
                    print("429, durmiendo 66s FULL POWER")
                    time.sleep(66)
                    continue
                time.sleep(10)
                continue
            print(f"Error gemini: {e}")
            return f"Amor tuve un error chiquito: {str(e)[:120]}. Intenta de nuevo en 10 seg."

    return "Mi amor, Google me tuvo 1 minutito castigada por hablar muy rápido. Ya volví, dime hola otra vez."

MANIFEST = {
  "name": "ASTRA VIVA FULL POWER - Familia",
  "short_name": "ASTRA FULL",
  "description": "ASTRA con todo el power, regenerador, boveda, burbuja bonita y flotante tipo Uber.",
  "start_url": "/", "display": "standalone",
  "background_color": "#020617", "theme_color": "#ffd700",
  "orientation": "portrait",
  "icons": [{"src": "/static/astra-viva.jpg","sizes":"192x192","type":"image/jpeg","purpose":"any maskable"},{"src":"/static/astra-viva.jpg","sizes":"512x512","type":"image/jpeg","purpose":"any maskable"}]
}
SW_JS = "self.addEventListener('install', e=>{self.skipWaiting();}); self.addEventListener('activate', e=>{self.clients.claim();}); self.addEventListener('fetch', e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));});"

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>ASTRA FULL POWER</title>
<link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#ffd700"><meta name="apple-mobile-web-app-capable" content="yes"><link rel="apple-touch-icon" href="/static/astra-viva.jpg">
<style>:root{--gold:#ffd700;--bg:#020617;--panel:#0f172a} *{box-sizing:border-box} body{margin:0;background:#000;color:#fff;font-family:system-ui;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#login{position:fixed;inset:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999;padding:20px;text-align:center}
#astraBox{flex:1;position:relative;background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden}
#astraVideo{width:100%;height:100%;object-fit:cover}
#status{position:absolute;top:14px;left:14px;background:rgba(0,0,0,0.85);border:1px solid var(--gold);color:var(--gold);padding:6px 12px;border-radius:20px;font-size:12px;font-weight:800;z-index:10}
#compartirBtn
