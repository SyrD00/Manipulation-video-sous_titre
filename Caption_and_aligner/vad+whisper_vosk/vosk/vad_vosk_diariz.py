# ------------------------------
# INSTALLATION
# ------------------------------
# pip install vosk pyannote.audio protobuf torch torchaudio librosa soundfile tqdm numpy psutil protobuf
# Assurez-vous d'avoir ffmpeg installé et dans le PATH

import os
import io
import re
import time
import torch
import librosa
import soundfile as sf
import subprocess
import tempfile
from tqdm import tqdm
from vosk import Model, KaldiRecognizer
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pyannote.audio import Pipeline

# ------------------------------
# CONFIGURATION
# ------------------------------
AUDIO_PATH = r"C:\Users\babak\Videos\Precure\Dancing star precure\Dancing star precure1.mp4"
OUTPUT_SRT = r"C:\Users\babak\Videos\Precure\Dancing star precure1_diarized.srt"

NUM_THREADS = os.cpu_count()
torch.set_num_threads(NUM_THREADS)
print(f"🧠 CPU : {NUM_THREADS} threads détectés")

start_time = time.time()

# ------------------------------
# EXTRACTION AUDIO
# ------------------------------
print("🎬 Extraction audio depuis la vidéo...")
tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
subprocess.run(
    ["ffmpeg", "-y", "-i", AUDIO_PATH, "-ac", "1", "-ar", "16000", tmp_wav],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
waveform, sr = librosa.load(tmp_wav, sr=16000)
waveform_tensor = torch.tensor(waveform).unsqueeze(0)  # (1, n_samples)

# ------------------------------
# DIARISATION LOCUTEUR (en mémoire pour éviter torchcodec)
# ------------------------------
print("🗣️ Diarisation en cours (pyannote.audio)...")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")

# Crée un dictionnaire audio en mémoire
audio_in_memory = {"waveform": waveform_tensor, "sample_rate": sr}
diarization = pipeline(audio_in_memory)

segments = []
for turn, _, speaker in diarization.itertracks(yield_label=True):
    segments.append({
        "start": turn.start,
        "end": turn.end,
        "speaker": speaker
    })
print(f"✅ {len(segments)} segments détectés.\n")

# ------------------------------
# CHARGEMENT DU MODELE VOSK
# ------------------------------
vosk_path = os.path.join(os.path.dirname(__file__), "model-ja")
if not os.path.exists(vosk_path):
    print("⚠️ Modèle Vosk japonais introuvable.")
    print("Télécharge : https://alphacephei.com/vosk/models et décompresse dans 'model-ja'")
    exit()

model = Model(vosk_path)
print("✅ Modèle Vosk chargé.\n")

# ------------------------------
# UTILITAIRES
# ------------------------------
def sec_to_srt_time(t):
    ms = int((t % 1) * 1000)
    h, m, s = int(t // 3600), int((t % 3600) // 60), int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def clean_japanese_text(text: str) -> str:
    text = re.sub(r"(?<=[\u3040-\u30FF\u4E00-\u9FFF])\s+(?=[\u3040-\u30FF\u4E00-\u9FFF])", "", text)
    text = re.sub(r"\s*([。、！？])\s*", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ------------------------------
# TRANSCRIPTION PAR SEGMENT
# ------------------------------
def transcribe_segment(i, start, end, speaker):
    segment_audio = waveform[int(start * sr):int(end * sr)]
    if len(segment_audio) == 0:
        return i, start, end, speaker, ""
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
    return i, start, end, speaker, text.strip()

# ------------------------------
# TRANSCRIPTION PARALLÈLE
# ------------------------------
print("⚡ Transcription en cours...\n")
results = []
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [executor.submit(transcribe_segment, i, s["start"], s["end"], s["speaker"]) for i, s in enumerate(segments, 1)]
    for fut in tqdm(as_completed(futures), total=len(futures), desc="Transcription", unit="segment"):
        results.append(fut.result())

results.sort(key=lambda x: x[0])

# ------------------------------
# ÉCRITURE SRT
# ------------------------------
with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
    for i, start, end, speaker, text in results:
        cleaned = clean_japanese_text(text)
        f.write(f"{i}\n{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n[{speaker}] {cleaned}\n\n")

elapsed = time.time() - start_time
print(f"\n✅ Transcription terminée en {elapsed:.2f} secondes")
print(f"📄 Fichier généré : {OUTPUT_SRT}")

try:
    os.remove(tmp_wav)
except Exception:
    pass
