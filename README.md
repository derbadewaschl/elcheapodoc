# 🩺 elcheapodoc (Whisper + VAD + LLM)

**elcheapodoc** ist ein lokales Diktier-Tool für medizinische Befunde:

* 🎤 Sprache → Text (Whisper)
* 🔇 Stille-Filter (Voice Activity Detection)
* 🧠 Optionale Verbesserung durch LLM (z. B. Llama3 via Ollama)
* ⌨️ Direkte Eingabe an der Cursorposition (z. B. in Microsoft Word)

---

# ✨ Features

* Fast-Echtzeit Diktat (~1–3s Delay ohne LLM)
* Verhindert "Ghost-Transkripte" durch VAD
* Funktioniert komplett lokal (DSGVO-freundlich)
* Optional: automatische medizinische Textverbesserung

---

# ⚙️ Voraussetzungen

* Python 3.10+
* Mikrofon
* (Optional) GPU für bessere Performance

---

# 📦 Installation

## 1. Repository / Script vorbereiten

Speichere das Python-Script z. B. als:

```bash
elcheapodoc.py
```

---

## 2. Python-Abhängigkeiten installieren

```bash
pip install faster-whisper sounddevice numpy keyboard pyperclip torch torchaudio requests
```

---

## 3. (Optional) LLM installieren (Ollama)

👉 [https://ollama.com](https://ollama.com)

Dann Modell laden:

```bash
ollama run llama3
```

---

# ▶️ Verwendung

1. Microsoft Word (oder anderes Textfeld) öffnen
2. Cursor an gewünschte Stelle setzen
3. Script starten:

```bash
python elcheapodoc.py
```

4. Sprechen 🎤

👉 Der Text wird automatisch eingefügt

---

# 🧠 Funktionsweise

1. Audio wird aufgenommen
2. VAD prüft: wird gesprochen?
3. Whisper transkribiert Sprache
4. (Optional) LLM verbessert den Text
5. Text wird per Copy/Paste eingefügt

---

# ⚠️ Hinweise

## Häufiger Fehler

**Fehler:** `ModuleNotFoundError: No module named 'torchaudio'`

👉 Lösung:

```bash
pip install torchaudio
```

Falls Probleme auftreten (z. B. unter Windows ohne GPU):

```bash
pip install torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

* Erste Modell-Downloads können einige Minuten dauern
* Ohne GPU kann das LLM langsam sein (5–15s)
* Audioqualität hat großen Einfluss auf Genauigkeit

---

# 🔒 Datenschutz

* Whisper läuft lokal
* VAD läuft lokal
* LLM kann lokal (Ollama) betrieben werden

👉 Keine Cloud erforderlich

---

# 🚀 Verbesserungsmöglichkeiten

* Streaming (noch geringere Latenz)
* Erweiterte Sprachbefehle
* Medizinische Templates
* UI (Start/Stop Button)

---

# 🧭 Lizenz

Freie Nutzung für private und experimentelle Zwecke

---

# 🙌 Hinweis

Dieses Projekt ist ein Prototyp und ersetzt keine zertifizierte medizinische Software.
