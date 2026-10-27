#!/usr/bin/env python3
"""Pre-generate the game's voice clips and sound effects with ElevenLabs.

Usage:
  ELEVENLABS_API_KEY=... python3 tools/gen_audio.py texts.json

`texts.json` is the array returned by AUDIO_TEXTS() in index.html (run it in the
browser console and save the result). Clips land in ./audio/<slug>.mp3 and are
skipped if they already exist, so re-running only generates new phrases.
The API key is read from the environment and never written anywhere.
"""
import json, os, re, sys, time, unicodedata
from concurrent.futures import ThreadPoolExecutor
import urllib.request

KEY = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("XI_API_KEY")
if not KEY:
    sys.exit("set ELEVENLABS_API_KEY")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio")
os.makedirs(OUT, exist_ok=True)

VOICE = os.environ.get("VOICE_ID", "FGY2WhTYpPnrIDTdsKH5")  # Laura (premade), multilingual model
MODEL = "eleven_multilingual_v2"
AMAP = {"á": "a_", "é": "e_", "í": "i_", "ó": "o_", "ú": "u_", "ñ": "n_", "ü": "u__"}

def aslug(t):  # must match aslug() in index.html
    raw = t.lower().strip()
    t = "".join(AMAP.get(c, c) for c in raw)
    t = re.sub(r"[^a-z0-9_]+", "-", t).strip("-")
    if len(t) > 60:  # long texts: prefix + djb2 hash of the raw text (same as the JS)
        h = 5381
        for ch in raw:
            h = ((h * 33) ^ ord(ch)) & 0xFFFFFFFF
        t = t[:48] + "-" + format(h, "x")
    return t or "x"

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read()[:200]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 * (attempt + 1)); continue
            raise RuntimeError(f"{e.code} {msg}")

def tts(text):
    path = os.path.join(OUT, aslug(text) + ".mp3")
    if os.path.exists(path):
        return "skip"
    data = post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_22050_32", {
        "text": text, "model_id": MODEL,
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.25, "use_speaker_boost": True}})
    open(path, "wb").write(data)
    return "ok"

SFX = {
    "ok": ("short bright video game correct-answer chime, two quick ascending notes, clean 8-bit style", 0.8),
    "bad": ("short soft retro video game wrong-answer buzzer, low and gentle, not harsh", 0.8),
    "tap": ("very short subtle retro UI blip click, single tick", 0.5),
    "click": ("soft video game menu select pop, short", 0.5),
    "win": ("retro 8-bit level complete jingle, triumphant and happy, two seconds", 2.0),
    "fanfare": ("epic short victory fanfare with sparkles, video game boss defeated, brass and chimes", 3.0),
    "tick": ("single short arcade countdown beep, urgent", 0.5),
    "star": ("magical sparkle star collect sound, bright chime, video game", 0.8),
    "combo": ("rising arcade power-up combo sound, quick ascending arpeggio", 0.9),
    "lose": ("short sad descending 8-bit game over tune, gentle", 1.5),
}

def sfx(name, prompt, secs):
    path = os.path.join(OUT, f"sfx-{name}.mp3")
    if os.path.exists(path):
        return "skip"
    data = post("https://api.elevenlabs.io/v1/sound-generation", {
        "text": prompt, "duration_seconds": secs, "prompt_influence": 0.6})
    open(path, "wb").write(data)
    return "ok"

if __name__ == "__main__":
    raw = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else []
    seen, texts = set(), []
    for t in raw:  # one clip per slug (case / trailing "?" variants share a file)
        if aslug(t) not in seen:
            seen.add(aslug(t)); texts.append(t)
    jobs = [(t, lambda t=t: tts(t)) for t in texts] + [(f"sfx-{n}", lambda n=n, p=p: sfx(n, *p)) for n, p in SFX.items()]
    done = {"ok": 0, "skip": 0, "err": 0}
    def run(job):
        label, fn = job
        try:
            r = fn(); done[r] += 1
        except Exception as e:
            done["err"] += 1; print("ERR", label, e)
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(run, jobs))
    chars = sum(len(t) for t in texts)
    print(f"generated={done['ok']} skipped={done['skip']} errors={done['err']} phrases={len(texts)} chars={chars}")
    json.dump(sorted(aslug(t) for t in texts), open(os.path.join(OUT, "manifest.json"), "w"), indent=0)
