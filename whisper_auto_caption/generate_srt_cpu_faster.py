import argparse
import os
import time
from tqdm import tqdm
from faster_whisper import WhisperModel

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"

def transcribe_with_progress(audio_path: str, model_size="medium", language=None, task="transcribe"):
    print(f"🚀 Chargement du modèle '{model_size}' optimisé AVX2...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print("✅ Modèle chargé.")

    print(f"\n🎧 Transcription de : {audio_path}\n")
    start_time = time.time()

    # Transcription
    segments_generator, info = model.transcribe(
        audio_path,
        language=language,
        task=task,
        beam_size=5,
    )
    if language is None:
        print(f"🌍 Langue détectée automatiquement : {info.language} (confiance {info.language_probability:.2f})")

    segments = list(segments_generator)
    total = len(segments)

    if total == 0:
        print("❌ Aucun segment détecté.")
        return

    srt_path = os.path.splitext(audio_path)[0] + ".srt"
    with open(srt_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(tqdm(segments, desc="📝 Génération du SRT", unit="segment", ncols=100)):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()
            srt_file.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")

    elapsed = time.time() - start_time
    print(f"\n✅ Transcription terminée en {elapsed:.2f} secondes")
    print(f"📄 Fichier SRT généré : {srt_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcrire un fichier audio en SRT avec Faster-Whisper (AVX2 optimisé).")
    parser.add_argument("input_file", help="Chemin du fichier audio à transcrire")
    parser.add_argument("--model_size", default="medium", help="Taille du modèle : tiny, base, small, medium, large")
    parser.add_argument("--language", default=None, help="Langue de l'audio, ex: ('auto', 'fr', 'en', ou 'ja'). Laisse vide pour auto-détection")
    parser.add_argument("--task", default="transcribe", choices=["transcribe", "translate"], help="Tâche : transcrire ou traduire")
    args = parser.parse_args()

    transcribe_with_progress(args.input_file, args.model_size, args.language, args.task)
