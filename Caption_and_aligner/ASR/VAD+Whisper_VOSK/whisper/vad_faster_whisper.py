'''
pip install --upgrade --force-reinstall ctranslate2 faster-whisper est mieux que pip install faster-whisper parofis erreur


pip install silero-vad librosa soundfile tqdm psutil



si tu veux desinstaller= pip uninstall -y faster-whisper ctranslate2 


Si malgre ca tu as l'erreur:
ImportError: Numba needs NumPy 2.2 or less. Got NumPy 2.3.

👉 En résumé :
librosa (et donc ton code audio) utilise numba, et numba n’est pas encore compatible avec NumPy 2.3.x.
Il faut donc downgrader NumPy à une version stable compatible.


⚙️ Étape 1 : Corrige la version de NumPy

Dans ton terminal PowerShell, exécute simplement :
pip install "numpy<2.3" --force-reinstall



'''

import os
import time
import librosa
import soundfile as sf
import psutil
import subprocess
import tempfile
import warnings
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from faster_whisper import WhisperModel
import torch

# ------------------------------
# ⚙️ CONFIGURATION
# ------------------------------
AUDIO_PATH = r"C:\Users\babak\Videos\PSO\PSO24\14.mp4"   # vidéo ou audio
OUTPUT_SRT = r"C:\Users\babak\Videos\PSO\PSO24\14_result.srt"
LANGUAGE = "ja"  # code ISO pour japonais

# ------------------------------
# 🧹 SUPPRESSION WARNINGS
# ------------------------------
warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# ------------------------------
# 🧠 CPU DETECTION
# ------------------------------
NUM_THREADS = os.cpu_count()
print(f"🧠 CPU : {NUM_THREADS} threads détectés\n")

# ------------------------------
# ⏱️ CHRONOMÈTRE
# ------------------------------
start_time = time.time()

# ------------------------------
# 🎬 EXTRACTION AUDIO
# ------------------------------
print("🎬 Extraction audio depuis la vidéo...")
tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
subprocess.run(
    ["ffmpeg", "-y", "-i", AUDIO_PATH, "-ac", "1", "-ar", "16000", tmp_wav],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

waveform, sr = librosa.load(tmp_wav, sr=16000)
audio_tensor = torch.tensor(waveform)

# ------------------------------
# 🎙️ DÉTECTION VOCALE (Silero VAD)
# ------------------------------
print("🔍 Détection des segments de parole (VAD)...")
model_vad, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", onnx=False)
get_speech_timestamps, _, _, _, _ = utils
segments = get_speech_timestamps(audio_tensor, model_vad, sampling_rate=16000, return_seconds=True)
print(f"✅ {len(segments)} segments détectés.\n")

# ------------------------------
# ⚡ CHARGEMENT DU MODÈLE FASTER-WHISPER
# ------------------------------
print("⚡ Chargement du modèle Faster-Whisper (large-v3-turbo)...")
model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

# ------------------------------
# 🧩 UTILITAIRES
# ------------------------------
def sec_to_srt_time(t):
    """Convertit secondes → hh:mm:ss,ms"""
    ms = int((t % 1) * 1000)
    h, m, s = int(t // 3600), int((t % 3600) // 60), int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def format_elapsed(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def transcribe_segment(i, start, end):
    """Transcrit un segment isolé avec Faster-Whisper."""
    segment_audio = waveform[int(start * sr):int(end * sr)]
    if len(segment_audio) == 0:
        return i, start, end, ""
    try:
        # Sauvegarde temporaire du segment
        seg_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        sf.write(seg_path, segment_audio, sr)
        segments, info = model.transcribe(seg_path, language=LANGUAGE)
        text = " ".join([s.text.strip() for s in segments])
        os.remove(seg_path)
    except Exception as e:
        text = f"[Erreur transcription: {e}]"
    return i, start, end, text.strip()

# ------------------------------
# ⚡ TRANSCRIPTION PARALLÈLE
# ------------------------------
print("⚡ Transcription en cours...\n")
results = []
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [executor.submit(transcribe_segment, i, s["start"], s["end"]) for i, s in enumerate(segments, 1)]
    for fut in tqdm(as_completed(futures), total=len(futures), desc="Transcription", unit="segment"):
        results.append(fut.result())

results.sort(key=lambda x: x[0])

# ------------------------------
# 💾 GÉNÉRATION DU FICHIER SRT
# ------------------------------
with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
    for i, start, end, text in results:
        f.write(f"{i}\n{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n{text}\n\n")

# ------------------------------
# ⏲️ TEMPS FINAL
# ------------------------------
elapsed = time.time() - start_time
print(f"\n✅ Transcription terminée en {format_elapsed(elapsed)} (hh:mm:ss,ms).")
print(f"📄 Fichier généré : {OUTPUT_SRT}")

# ------------------------------
# 🧹 NETTOYAGE DU FICHIER TEMP
# ------------------------------
try:
    os.remove(tmp_wav)
except Exception:
    pass
