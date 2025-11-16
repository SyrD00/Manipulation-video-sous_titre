
r'''

Si tu veux supprimertous les model installe:
    Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--openai--whisper*"

    ou vas directement dans:
    C:\Users\babak\.cache\huggingface\hub\models--openai



pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers accelerate datasets[audio] soundfile librosa tqdm psutil

pip install silero-vad
pip install sentencepiece

pip uninstall -y torch torchcodec torchvision torchaudio 
pip install torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu --index-url https://download.pytorch.org/whl/cpu



NB:
| Option                                               | Signification                      | Utilisation                   |
| :--------------------------------------------------- | :--------------------------------- | :---------------------------- |
| `--index-url https://download.pytorch.org/whl/cpu`   | Installe la version CPU officielle | Si tu n’as pas de GPU         |
| `--index-url https://download.pytorch.org/whl/cu118` | Installe la version GPU CUDA 11.8  | Si ton GPU supporte CUDA 11.8 |
| `--index-url https://download.pytorch.org/whl/cu121` | Installe la version GPU CUDA 12.1  | Si ton GPU supporte CUDA 12.1 |




Bizarement quand j'ai teste medium etait plus lent que large-v3-turbo sur cpu:
large-v3-turbo est optimisé pour cpu/gpu leger donc plus rapide que medium sur cpu pur
| Nom du modèle                   | Taille | Multilingue | Remarques                 |
| ------------------------------- | ------ | ----------- | ------------------------- |
| `openai/whisper-tiny`           | 148 Mo   | ✅           | Très rapide, moins précis |
| `openai/whisper-base`           | 281 Mo   | ✅           | Bon équilibre             |
| `openai/whisper-small`          | 926 M  | ✅           | Recommandé CPU            |
| `openai/whisper-medium`         | 2.84 M  | ✅           | Plus précis mais lent     |
| `openai/whisper-large-v3`       | 3.06 G | ✅           | Très précis mais lourd    |
| `openai/whisper-large-v3-turbo` | 1.51 M  | ✅           | Version optimisée CPU/GPU |

en general small est bon compromis vitesse/qualite pour cpu mia sparfois fais erreur contrairement a medium donc a tester selon usage



| Critère                                   | 🟪 **Whisper Large-v3**                                          | ⚡ **Whisper Large-v3-Turbo**                                |
| ----------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------- |
| 🧠 **Taille du modèle**                   | ≈ 2.9 Go (1.55 milliard paramètres)                              | ≈ 1.6 Go (809 millions paramètres)                          |
| 🧩 **Architecture**                       | 32 couches d’encodeur + 32 couches de décodeur                   | 32 couches d’encodeur + **4 couches** de décodeur           |
| 🗣️ **Langues supportées**                | Multilingue (99 langues)                                         | Multilingue (99 langues)                                    |
| 🕓 **Vitesse (CPU)**                      | Lente : ~0.3× temps réel (≈ 1 min d’audio = 3 min de traitement) | ⚡ 2–3 × plus rapide (≈ 1 min d’audio = 1 min de traitement) |
| 🎯 **Précision (WER)**                    | Excellente ≈ 1 % erreur sur audio propre                         | Très bonne ≈ 1.5–2 % erreur (presque identique)             |
| 🧮 **RAM requise (CPU)**                  | 5–6 Go                                                           | 3–3.5 Go                                                    |
| 💻 **GPU recommandé**                     | 8 Go VRAM minimum                                                | 4 Go VRAM minimum                                           |
| 💬 **Hallucinations (phrases inventées)** | Très rares                                                       | Légèrement plus fréquentes                                  |
| 🔁 **Utilisation typique**                | Qualité maximale (films, archives)                               | Production rapide, CPU/GPU légers                           |
| 🔊 **Version trad. (vers anglais)**       | Oui (task=translate)                                             | Oui (identique)                                             |


'''


import os
import io
import time
import torch
import librosa
import soundfile as sf
import psutil
import subprocess
import tempfile
import warnings
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# ------------------------------
# ⚙️ CONFIGURATION
# ------------------------------
AUDIO_PATH = r"C:\Users\babak\Videos\Precure\Dancing star precure\d.mp4"   # vidéo ou audio
OUTPUT_SRT = r"C:\Users\babak\Videos\Precure\Dancing star precure\d.srt"
LANGUAGE = "japanese"

# ------------------------------
# 🧹 SUPPRIMER LES WARNINGS
# ------------------------------
warnings.filterwarnings("ignore")
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ------------------------------
# 🧠 AUTO-DÉTECTION CPU (100% cœurs)
# ------------------------------
NUM_THREADS = os.cpu_count()
torch.set_num_threads(NUM_THREADS)
torch.set_num_interop_threads(NUM_THREADS)

print(f"🧠 CPU : {NUM_THREADS} threads forcés.")
print(f"🔧 Threads PyTorch: {torch.get_num_threads()} / Interop: {torch.get_num_interop_threads()}\n")

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
get_speech_timestamps, _, _, _, _ = utils
segments = get_speech_timestamps(audio_tensor, model_vad,
                                 sampling_rate=16000,
                                 return_seconds=True)
print(f"✅ {len(segments)} segments détectés.\n")

# ------------------------------
# 🎧 CHARGEMENT DU MODÈLE WHISPER TURBO
# ------------------------------
print("🎧 Chargement du modèle Whisper Turbo...")
device, dtype = "cpu", torch.float32
model_id = "openai/whisper-large-v3-turbo"



model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, dtype=dtype, low_cpu_mem_usage=True
).to(device)
processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    chunk_length_s=30,
    batch_size=2,
    dtype=dtype,
    device=device,
    ignore_warning=True
)

# ------------------------------
# 🪶 UTILITAIRES
# ------------------------------
def sec_to_srt_time(t):
    """Convertit secondes → hh:mm:ss,ms"""
    ms = int((t % 1) * 1000)
    h, m, s = int(t // 3600), int((t % 3600) // 60), int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def format_elapsed(seconds):
    """Affiche le temps écoulé au format hh:mm:ss,ms"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def transcribe_segment(i, start, end):
    """Découpe un segment et le transcrit."""
    segment_audio = waveform[int(start * sr):int(end * sr)]
    if len(segment_audio) == 0:
        return i, start, end, ""
    try:
        result = pipe(segment_audio, generate_kwargs={"language": LANGUAGE}, return_timestamps=False)
        text = result["text"].strip()
    except Exception as e:
        text = f"[Erreur transcription: {e}]"
    return i, start, end, text

# ------------------------------
# ⚡ TRANSCRIPTION EN PARALLÈLE
# ------------------------------
print("⚡ Transcription en cours...\n")
results = []
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [executor.submit(transcribe_segment, i, s["start"], s["end"])
               for i, s in enumerate(segments, 1)]
    for fut in tqdm(as_completed(futures), total=len(futures),
                    desc="Transcription", unit="segment"):
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

