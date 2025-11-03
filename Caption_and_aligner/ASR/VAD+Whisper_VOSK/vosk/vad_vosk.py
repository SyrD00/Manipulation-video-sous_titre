'''
pip install vosk silero-vad librosa soundfile tqdm psutil numpy

Si t'as erreur:ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
1.pyannote-audio 4.0.1 requires torchcodec>=0.6.0, which is not installed.
2.datasets 4.3.0 requires fsspec[http]<=2025.9.0,>=2023.1.0, but you have fsspec 2025.10.0 which is incompatible.
3.numba 0.61.2 requires numpy<2.3,>=1.24, but you have numpy 2.3.4 which is incompatible.
4.transformers 4.57.1 requires huggingface-hub<1.0,>=0.34.0, but you have huggingface-hub 1.0.1 which is incompatible.

Solutions:
1.pip install torchcodec>=0.6.0
2. pip install fsspec<=2025.9.0,>=2023.1.0
3. pip install numpy<2.3
4. pip install huggingface-hub<1.0

Ou tout resoudre en une seule ligne:
pip install torchcodec>=0.6.0 "fsspec<=2025.9.0,>=2023.1.0" "numpy<2.3" "huggingface-hub<1.0" --force-reinstall

ou
pip install -U pyannote-audio datasets numba transformers --upgrade --upgrade-strategy eager


'''


import numpy as np
import re
import os
import io
import time
import librosa
import soundfile as sf
import torch
import psutil
import subprocess
import tempfile
from tqdm import tqdm
from vosk import Model, KaldiRecognizer
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------
# ⚙️ CONFIGURATION
# ------------------------------



AUDIO_PATH= r"C:\Users\babak\Videos\PSO\Video\PSO29.mp4"
OUTPUT_SRT= r"C:\Users\babak\Videos\PSO\Video\PSO29.srt"

#AUDIO_PATH = r"C:\Users\babak\Videos\Precure\Dancing star precure\Dancing star precure1.mp4"
#OUTPUT_SRT = r"C:\Users\babak\Videos\Precure\Dancing star precure\Dancing star precure1.srt"


# ------------------------------
# 🧠 CPU UTILISATION
# ------------------------------
NUM_THREADS = os.cpu_count()
print(f"🧠 CPU : {NUM_THREADS} threads détectés")
torch.set_num_threads(NUM_THREADS)

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
# 🎙️ DÉTECTION DE PAROLE (Silero VAD)
# ------------------------------
print("🔍 Détection des segments de parole (VAD)...")
model_vad, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", onnx=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

segments = get_speech_timestamps(
    audio_tensor,                # 🟩 (torch.Tensor) — Signal audio mono, normalisé dans [-1, 1].
    model_vad,                   # 🟩 (torch.nn.Module) — Modèle Silero VAD chargé via torch.hub.
    sampling_rate=16000,         # 🎵 Taux d’échantillonnage de ton audio. Doit être 8000 ou 16000 Hz.

    threshold=0.35,              # 🎚️ [Optionnel, défaut=0.5]
                                 # Niveau de probabilité minimale pour considérer qu’il y a parole.
                                 # ↓ Plus petit → plus sensible → capte voix faibles / chuchotements.
                                 # ↑ Plus grand → plus strict → ignore bruits et voix éloignées.

    #min_speech_duration_ms=150,  # ⏳ [Optionnel, défaut=250 ms]
                                 # Durée minimale d’un segment de parole. 
                                 # En dessous → ignoré (utile pour éviter “ah”, “hm”, clics audio).

    min_silence_duration_ms=100, # 🤫 [Optionnel, défaut=100 ms]
                                 # Durée minimale de silence séparant deux segments.
                                 # ↓ petit → fusionne des phrases rapprochées.
                                 # ↑ grand → coupe davantage.

    speech_pad_ms=50,           # 🪶 [Optionnel, défaut=30 ms]
                                 # Marge de sécurité ajoutée avant et après un segment pour ne pas
                                 # couper des mots au début ou à la fin.
                                 # (utile contre coupures brusques de voix ou OST).

    #window_size_samples=512,     # 🔍 [Optionnel, interne]
                                 # Taille de la fenêtre d’analyse en échantillons (normalement 512 pour 16 kHz).
                                 # Plus grande fenêtre = plus stable mais plus lente.

    visualize_probs=True,       # 📈 [Optionnel, défaut=False]
                                 # Si True, affiche une courbe matplotlib de la probabilité de voix
                                 # pour t’aider à régler le threshold.

    #return_seconds=True          # ⏱️ [Optionnel, défaut=False]
                                 # Si True → les timestamps de sortie sont en secondes (float).
                                 # Si False → renvoyés en échantillons (int).
)

print(f"✅ {len(segments)} segments détectés.\n")


# ------------------------------
# 🗣️ CHARGEMENT DU MODÈLE VOSK
# ------------------------------
print("🎧 Chargement du modèle Vosk (japonais)...")
vosk_path = os.path.join(os.path.dirname(__file__), "model-ja") #
if not os.path.exists(vosk_path):
    print("⚠️ Modèle Vosk japonais introuvable. Télécharge-le avec :")
    print("   https://alphacephei.com/vosk/models ou depuis ce lien direct : : https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip")
    print("   et décompresse-le dans le dossier zip vosk-model-small-ja-0.22 ou vosk-model-ja-0.22 selon la version choisie.")
    print("   Place ensuite ce dossier dans le même répertoire que ce script et renomme-le en 'model-ja'. pour le model-ja et model-small-ja selon la version choisie.")
    
    exit()

model = Model(vosk_path)
print("✅ Modèle chargé.\n")

# ------------------------------
# 🪶 UTILITAIRES
# ------------------------------
def sec_to_srt_time(t):
    ms = int((t % 1) * 1000)
    h, m, s = int(t // 3600), int((t % 3600) // 60), int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def format_elapsed(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def clean_japanese_text(text: str) -> str:
    """Supprime les espaces inutiles entre caractères japonais."""
    # Enlève espaces entre kanji/kana
    text = re.sub(r"(?<=[\u3040-\u30FF\u4E00-\u9FFF])\s+(?=[\u3040-\u30FF\u4E00-\u9FFF])", "", text)
    # Enlève espaces avant/ après ponctuation japonaise
    text = re.sub(r"\s*([。、！？])\s*", r"\1", text)
    # Nettoie espaces multiples
    text = re.sub(r"\s+", " ", text).strip()
    return text



# ------------------------------
# 🔠 TRANSCRIPTION AVEC VOSK
# ------------------------------
def transcribe_segment(i, start, end):
    segment_audio = waveform[int(start * sr):int(end * sr)]
    if len(segment_audio) == 0:
        return i, start, end, ""
    buf = io.BytesIO()
    sf.write(buf, segment_audio, sr, format="wav")
    buf.seek(0)

    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    text = ""
    while True:
        data = buf.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text += res.get("text", "") + " "
    final_res = json.loads(rec.FinalResult())
    text += final_res.get("text", "")
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
# 💾 ÉCRITURE DU SRT
# ------------------------------
with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
    for i, start, end, text in results:
        cleaned =clean_japanese_text(text)
        f.write(f"{i}\n{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n{cleaned}\n\n")

# ------------------------------
# ⏲️ TEMPS TOTAL
# ------------------------------
elapsed = time.time() - start_time
print(f"\n✅ Transcription terminée en {format_elapsed(elapsed)} (hh:mm:ss,ms).")
print(f"📄 Fichier généré : {OUTPUT_SRT}")

try:
    os.remove(tmp_wav)
except Exception:
    pass
