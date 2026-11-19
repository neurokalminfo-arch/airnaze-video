"""Render del estilo noche neón.
Uso: python3 engine/neon/render.py episodes/<id> [--frames]
El episodio necesita spec.json, words.json + voice.mp3 (tts.py) y scenes.py, que define:
  KEY      = {"palabra", ...}            # palabras que salen en recuadro en los subtítulos
  def timeline(L):                        # L = engine/neon/lib.py
      return [(inicio_s, nombre, funcion(F, t, t0)), ...], fin_s
  opcional: ACCENTS(L) -> lista de tiempos con 'pop', CHIMES(L) -> tiempos con campanita, TICKS_UNTIL(L) -> s de tic-tac.
--frames: hoja de contacto en <ep>/final_work/contact.jpg (2 fotogramas por escena). Sin --frames: final.mp4."""
import sys, os, json, importlib.util, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lib as L
import audio as AU
from PIL import Image
ep = os.path.abspath(sys.argv[1]); work = os.path.join(ep, "final_work"); os.makedirs(work, exist_ok=True)
spec = json.load(open(os.path.join(ep, "spec.json")))
L.load_words(os.path.join(ep, "words.json"))
sp = importlib.util.spec_from_file_location("scenes", os.path.join(ep, "scenes.py")); S = importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
L.KEY.clear(); L.KEY.update(getattr(S, "KEY", set()))
TL, END = S.timeline(L)
TL = sorted(TL, key=lambda x: x[0])

def draw(t, i):
    t0, name, fn = TL[i]
    F = L.Frame(); L.time_g[0] = t
    fn(F, t, t0)
    if t < L.last_end() + 0.3: L.caption(F.o, t)
    F.o.select_font_face("DejaVu Sans Mono", 0, 0); F.o.set_font_size(22); F.o.set_source_rgba(0.75, 0.75, 0.9, 0.35)
    e = F.o.text_extents("@myairnaze"); F.o.move_to(L.W / 2 - e.x_advance / 2, 1880); F.o.show_text("@myairnaze")
    return F.compose()

def frame(t):
    i = max([k for k, s in enumerate(TL) if t >= s[0]] or [0])
    img = draw(t, i)
    t0 = TL[i][0]
    if i > 0 and 0 < t - t0 < 0.18:
        img = Image.blend(draw(t, i - 1).convert("RGB"), img.convert("RGB"), (t - t0) / 0.18)
    return img.convert("RGB")

def chunk(args):
    k, f0, f1 = args; tmp = os.path.join(work, f"c{k}.tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L.W}x{L.H}", "-r", "30", "-i", "-",
                          "-c:v", "libx264", "-profile:v", "main", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(f0, f1): p.stdin.write(frame(f / 30).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, os.path.join(work, f"c{k}.mp4"))

if __name__ == "__main__":
    if "--frames" in sys.argv:
        ts = []
        for i, (t0, name, fn) in enumerate(TL):
            t1 = TL[i + 1][0] if i + 1 < len(TL) else END
            ts += [t0 + (t1 - t0) * 0.35, t0 + (t1 - t0) * 0.85]
        ims = [frame(t).resize((270, 480)) for t in ts]
        cols = 6; rows = (len(ims) + cols - 1) // cols
        g = Image.new("RGB", (270 * cols, 480 * rows))
        for i, im in enumerate(ims): g.paste(im, ((i % cols) * 270, (i // cols) * 480))
        g.save(os.path.join(work, "contact.jpg"), quality=85)
        print("hoja de contacto:", os.path.join(work, "contact.jpg"), "escenas:", [(round(s, 1), n) for s, n, _ in TL], "fin:", round(END, 1))
        sys.exit()
    from multiprocessing import Pool
    n = round(END * 30); C = 8; b = [round(n * k / C) for k in range(C + 1)]
    with Pool(C) as pool: pool.map(chunk, [(k, b[k], b[k + 1]) for k in range(C)])
    with open(os.path.join(work, "list.txt"), "w") as f:
        for k in range(C): f.write(f"file 'c{k}.mp4'\n")
    vid = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "list.txt"), "-c", "copy", vid], check=True)
    bedp = os.path.join(work, "bed.wav")
    AU.bed(bedp, END, boundaries=[s for s, _, _ in TL[1:]], accents=getattr(S, "ACCENTS", lambda L: [])(L),
           chimes=getattr(S, "CHIMES", lambda L: [])(L), ticks_until=getattr(S, "TICKS_UNTIL", lambda L: 0)(L), seed=spec.get("music_seed", 0))
    out = os.path.join(ep, "final.mp4")
    fc = ("[1:a]apad,volume=5dB,asplit=2[v][vs];[2:a]volume=-13dB[b];[b][vs]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[bd];"
          "[v][bd]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", os.path.join(ep, "voice.mp3"), "-i", bedp, "-filter_complex", fc,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-tag:v", "avc1", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("listo:", out)
