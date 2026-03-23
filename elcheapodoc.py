import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import queue
import threading
import keyboard
import pyperclip
import time
import re
import requests

# ===== SETTINGS =====
MODEL_SIZE = "medium"   # wichtig!
SAMPLE_RATE = 16000
BLOCK_DURATION = 2

def llm_prompt(text):
    return f"""
DU BIST EIN MEDIZINISCHER TRANSKRIPTIONSKORREKTUR-ASSISTENT.

AUFGABE:
Korrigiere ausschließlich Rechtschreibung und offensichtliche Spracherkennungsfehler.

REGELN (EXTREM WICHTIG):
- KEINE Interpretation
- KEINE Ergänzungen
- KEINE Umformulierungen
- KEINE medizinische Bewertung
- KEINE neuen Inhalte
- KEINE Kommentare
- KEINE Erklärungen

DU DARFST NUR:
- Wörter korrigieren (z.B. Leber statt Liebe)
- Groß-/Kleinschreibung korrigieren
- medizinische Begriffe normalisieren

WENN EIN SATZ SINNVOLL IST:
→ exakt so lassen, nur minimal korrigieren

OUTPUT:
Gib nur den korrigierten Text zurück. Kein Zusatz.

TEXT:
{text}
"""

model = WhisperModel(MODEL_SIZE, compute_type="int8")
audio_queue = queue.Queue()

# ===== MEDICAL FIXES =====
def apply_medical_rules(text):
    RULES = [
        # ===== ORGANE =====
        (r"\bliebe\b", "Leber"),
        (r"\bmilch\b", "Milz"),
        (r"\bnieren\b", "Nieren"),
        (r"\blunge\b", "Lunge"),
        (r"\bherz\b", "Herz"),
        (r"\bblase\b", "Blase"),
        (r"\bprostata\b", "Prostata"),

        # ===== HÄUFIGE FEHLER =====
        (r"\braum forderungen\b", "Raumforderungen"),
        (r"\braumforderung\b", "Raumforderung"),
        (r"\baszites\b", "Aszites"),
        (r"\bmetastasen\b", "Metastasen"),
        (r"\binfakt\b", "Infarkt"),
        (r"\bkarzinom\b", "Karzinom"),

        # ===== BEFUND-PHRASEN =====
        (r"\bkein hinweis auf\b", "Kein Hinweis auf"),
        (r"\bkeine hinweise auf\b", "Keine Hinweise auf"),
        (r"\bunauffaellig\b", "unauffällig"),
        (r"\bunauffällig\b", "unauffällig"),

        # ===== GRÖSSEN / BESCHREIBUNG =====
        (r"\bnormal gross\b", "normal groß"),
        (r"\bvergroessert\b", "vergrößert"),
        (r"\bvergrößert\b", "vergrößert"),

        # ===== UMLAUTE =====
        (r"\bgross\b", "groß"),
        (r"\bmaessig\b", "mäßig"),
        (r"\bfluessigkeit\b", "Flüssigkeit"),

        # ===== STANDARD BEFUNDE =====
        (r"\bleber unauffaellig\b", "Leber unauffällig"),
        (r"\bleber unauffällig\b", "Leber unauffällig"),
        (r"\bmilz unauffaellig\b", "Milz unauffällig"),
        (r"\bmilz unauffällig\b", "Milz unauffällig"),
    ]

    for pattern, replacement in RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+,", ",", text)

    # Satzanfang groß
    if len(text) > 0:
        text = text[0].upper() + text[1:]

    return text.strip()


# ===== LLM ====
def llm_correct(text):
    prompt = llm_prompt(text)

    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.0
        }
    )

    return r.json()["response"].strip()

def valid_text(raw_text):
    # min 1 Wort
    if len(raw_text.strip()) < 2:
        return False

    # mindestens ein Buchstabe
    if not any(c.isalpha() for c in raw_text):
        return False

    # blacklist / typische Ghost-Phrasen
    BLACKLIST = ["auf wiedersehen", "im nächsten video"]
    if any(b in raw_text.lower() for b in BLACKLIST):
        return False

    return True

# ===== STATUS =====
def status(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# ===== Adaptive Speech Detection =====
noise_floor = 0.0002  # initial

def is_speech(audio):
    global noise_floor
    energy = np.mean(audio**2)

    # adaptiver Noise Floor
    noise_floor = 0.9 * noise_floor + 0.1 * energy

    # Sprachdetektion: Energie > 2.0 x noise_floor
    return energy > noise_floor * 2.0

# ===== AUDIO =====
def record_audio():
    while True:
        audio = sd.rec(int(BLOCK_DURATION * SAMPLE_RATE),
                       samplerate=SAMPLE_RATE,
                       channels=1,
                       dtype='float32')
        sd.wait()
        audio_queue.put(audio.flatten())

# ===== TRANSCRIBE =====
def transcribe():
    while True:
        audio = audio_queue.get()

        if not is_speech(audio):
            continue

        status("🗣️ Sprache erkannt")

        t0 = time.time()

        segments, _ = model.transcribe(audio, language="de", beam_size=5, temperature=0.0)
        raw_text = " ".join([seg.text for seg in segments]).strip()

        if not valid_text(raw_text):
            print("🚫 kein gültiger Text erkannt")
            continue

        # statt no_speech_prob:
        if raw_text.strip() == "":
            print("🚫 kein Speech erkannt")
            return

        status(f"📝 erkannt ({round(time.time() - t0,1)}s): {raw_text}")

        if not raw_text:
            continue

        status("Korrektur via LLM")
        t0 = time.time()

        # 🔧 medizinische Korrektur
        final_text = apply_medical_rules(raw_text)
        final_text = clean_text(final_text)

        # LLM
        final_text = llm_correct(final_text)

        status(f"Final: ({round(time.time() - t0,1)}s): {final_text}")

        # einfügen
        pyperclip.copy(final_text + " ")
        keyboard.press_and_release("ctrl+v")

        status("✅ eingefügt\n")

# ===== START =====
threading.Thread(target=record_audio, daemon=True).start()
threading.Thread(target=transcribe, daemon=True).start()

status("🚀 elcheapodoc läuft")

while True:
    time.sleep(1)