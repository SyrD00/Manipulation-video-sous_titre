import torch
import torchaudio
from datetime import timedelta
import ffmpeg
import os
import soundfile as sf  # pour lire l’audio de manière fiable

# --- Configuration ---
MEDIA_FILE = r"C:\Users\babak\Videos\Precure\Dancing star precure\Dancing star precure.mp4"
OUTPUT_SRT = r"C:\Users\babak\Videos\Precure\Dancing star precure\Dancing star precure_vad.srt"

# --- Convertir automatiquement en WAV 16 kHz mono ---
def convert_to_wav16k(infile):
    tmp_wav = "tmp_audio.wav"
    if not infile.lower().endswith(".wav"):
        print("🎞️ Conversion audio en WAV 16 kHz...")
        (
            ffmpeg
            .input(infile)
            .output(tmp_wav, ac=1, ar=16000, format="wav", loglevel="quiet")
            .overwrite_output()
            .run()
        )
        return tmp_wav
    else:
        return infile

wav_file = convert_to_wav16k(MEDIA_FILE)

# --- Charger modèle Silero VAD ---
print("🔄 Chargement du modèle Silero-VAD...")
model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad")
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

# --- Lire audio (sans torchaudio.load) ---
print("🎧 Lecture du fichier audio...")
wav_data, sr = sf.read(wav_file, dtype="float32")

# Si stéréo, on moyenne en mono
if wav_data.ndim > 1:
    wav_data = wav_data.mean(axis=1)

wav = torch.from_numpy(wav_data).unsqueeze(0)

# Resample si besoin
if sr != 16000:
    print(f"⚙️ Resample {sr} → 16000 Hz")
    wav = torchaudio.transforms.Resample(sr, 16000)(wav)
    sr = 16000

# --- Détection de voix ---
print("🧠 Analyse du signal vocal...")
speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=sr)
print(f"✅ Segments de voix détectés : {len(speech_timestamps)}")

# --- Fonction pour format SRT ---
def to_srt_time(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    ms = int((seconds - total_seconds) * 1000)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

# --- Créer SRT ---
print("📝 Création du fichier SRT...")
with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
    for i, seg in enumerate(speech_timestamps):
        start = seg["start"] / sr
        end = seg["end"] / sr
        f.write(f"{i+1}\n{to_srt_time(start)} --> {to_srt_time(end)}\n[Speech detected]\n\n")

print(f"✅ Fichier SRT généré : {OUTPUT_SRT}")
print("💡 Ouvre-le dans VLC ou Subtitle Edit pour visualiser les moments de voix réelle.")

# --- Nettoyer le fichier temporaire ---
if wav_file == "tmp_audio.wav" and os.path.exists(wav_file):
    os.remove(wav_file)
    print("🧹 Fichier temporaire supprimé.")
