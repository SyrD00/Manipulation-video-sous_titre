import os, torch, librosa, tempfile, subprocess, time, warnings
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# --- CONFIG ---
AUDIO_PATH = r"C:\Users\babak\Videos\Precure\Dancing star precure\d.mp4"
OUTPUT_SRT = r"C:\Users\babak\Videos\Precure\Dancing star precure\d.srt"
LANGUAGE = "japanese"

# --- SILENCE WARNINGS ---
warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# --- AUDIO EXTRACTION ---
tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
subprocess.run(["ffmpeg", "-y", "-i", AUDIO_PATH, "-ac", "1", "-ar", "16000", tmp_wav],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

waveform, sr = librosa.load(tmp_wav, sr=16000)
audio_tensor = torch.tensor(waveform)

# --- VAD DETECTION ---
model_vad, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", onnx=False)
get_speech_timestamps, _, _, _, _ = utils
segments = get_speech_timestamps(audio_tensor, model_vad,
                                 sampling_rate=16000,
                                 return_seconds=True)

# --- WHISPER LOAD ---
model_id = "openai/whisper-large-v3-turbo"
model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id, dtype=torch.float32)
processor = AutoProcessor.from_pretrained(model_id)
pipe = pipeline("automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                chunk_length_s=30)

# --- UTIL ---
def sec_to_srt_time(t):
    ms = int((t % 1) * 1000)
    h, m, s = int(t // 3600), int((t % 3600) // 60), int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

# --- TRANSCRIBE ---
results = []
for i, s in enumerate(segments, 1):
    segment_audio = waveform[int(s["start"] * sr):int(s["end"] * sr)]
    if len(segment_audio) == 0: continue
    text = pipe(segment_audio, generate_kwargs={"language": LANGUAGE})["text"].strip()
    results.append((i, s["start"], s["end"], text))

# --- SAVE SRT ---
with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
    for i, start, end, text in results:
        f.write(f"{i}\n{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n{text}\n\n")

# --- CLEANUP ---
os.remove(tmp_wav)
print("✅ Transcription terminée :", OUTPUT_SRT)
