import whisperx
import torch
from tqdm import tqdm

def format_timestamp(seconds: float) -> str:
    milliseconds = int(seconds * 1000)
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    milliseconds = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def save_srt(segments, srt_path):
    print("🧪 Vérification des segments...")
    if not segments or not isinstance(segments[0], dict) or "start" not in segments[0]:
        raise ValueError("❌ Les segments alignés ont une structure inattendue.")

    print(f"💾 Sauvegarde de {len(segments)} lignes dans {srt_path}")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip().replace("\n", " ")
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

def transcribe_and_align(audio_path, srt_path, device="cpu", language="ja"):
    print("🤖 Chargement du modèle WhisperX (medium)...")
    model = whisperx.load_model("medium", device=device, compute_type="float32")

    print(f"🎧 Transcription de l'audio {audio_path}...")
    result = model.transcribe(audio_path, batch_size=16, language=language)

    print("🤖 Chargement du modèle d'alignement forcé...")
    model_a, metadata = whisperx.load_align_model(language_code=language, device=device)

    print("⏱️ Alignement des sous-titres avec barre de progression...")

    segments = result["segments"]
    aligned_segments = []

    for segment in tqdm(segments, desc="Alignement"):
        aligned = whisperx.align([segment], model_a, metadata, audio_path, device=device)
        if isinstance(aligned, list):
            aligned_segments.extend(aligned)
        else:
            print(f"⚠️ Segment mal formé ignoré : {segment}")

    print(f"📝 Écriture du fichier SRT dans {srt_path}...")
    save_srt(aligned_segments, srt_path)
    print("✅ Transcription et alignement terminés.")

if __name__ == "__main__":
    audio_file = "C:/Users/babak/Videos/PSO/PSO8.wav"
    srt_file = "C:/Users/babak/Videos/PSO/PSO8v2.srt"
    device = "cpu"

    transcribe_and_align(audio_file, srt_file, device=device, language="ja")
