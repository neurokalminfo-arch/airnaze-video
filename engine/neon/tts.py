"""Voz de Carlos (ElevenLabs) con marcas de tiempo por palabra.
Uso: ELEVENLABS_API_KEY=... python3 engine/neon/tts.py episodes/<id>
Lee spec.json["voice"] (guion completo) y escribe voice.mp3 + words.json en el episodio.
La clave va SOLO en la variable de entorno: nunca en el repositorio (es público)."""
import json, os, sys, time, base64, urllib.request, urllib.error
VOICE_ID = "QgCtSwnXVKRyDKcdnGOE"   # Carlos
ep = sys.argv[1]
spec = json.load(open(os.path.join(ep, "spec.json")))
text = spec["voice"].strip()
key = os.environ.get("ELEVENLABS_API_KEY")
if not key: sys.exit("Falta ELEVENLABS_API_KEY en el entorno")
body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                   "voice_settings": {"stability": 0.42, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}}).encode()
for intento in range(3):
    try:
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps", data=body,
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req, timeout=180)); break
    except urllib.error.HTTPError as e:
        msg = e.read()[:300]
        if e.code in (401, 403): sys.exit(f"ElevenLabs rechaza la clave ({e.code}): {msg}")
        print("ElevenLabs error", e.code, msg); time.sleep(20)
    except Exception as e:
        print("ElevenLabs error", e); time.sleep(20)
else:
    sys.exit("ElevenLabs no responde tras 3 intentos")
open(os.path.join(ep, "voice.mp3"), "wb").write(base64.b64decode(d["audio_base64"]))
a = d["alignment"]; words = []; cur = ""; s = None; pe = 0
for c, s0, e0 in zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]):
    if c.isspace():
        if cur: words.append([cur, s, pe]); cur = ""
        continue
    if not cur: s = s0
    cur += c; pe = e0
if cur: words.append([cur, s, pe])
json.dump(words, open(os.path.join(ep, "words.json"), "w"), ensure_ascii=False)
print(f"voz lista: {len(words)} palabras, {words[-1][2]:.1f} s")
