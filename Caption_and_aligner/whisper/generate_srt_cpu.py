"""

UserWarning: FP16 is not supported on CPU; using FP32 instead


vient de la librairie openai-whisper officielle

whisper.load_model("large") essaye par défaut de charger le modèle en FP16 (16-bit flottant), ce qui n’est
pas supporté sur CPU.

Donc il bascule en FP32 (32-bit flottant) et te met juste un warning.

Ça ne bloque rien → ta transcription se fait bien, mais c’est plus lent qu’en GPU.

Ignorer l’avertissement (OK si tu restes en CPU)
Tu n’as rien à changer, ça marchera toujours.
C’est juste plus lent.

    Solutions:
Forcer directement le FP32 pour ne plus voir ce warning :

model = whisper.load_model("large", device="cpu")


ou bien

model = whisper.load_model("large", device="cpu", fp16=False)


→ Ça dit explicitement à Whisper : “je tourne en CPU, pas en FP16”.

"""



import whisper
import os
import sys
import time
from tqdm import tqdm

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def main():
    print("🚀 Chargement du modèle Whisper (large)...")
    model = whisper.load_model("large")
    print("✅ Modèle chargé.")

    while True:
        audio_path = input("📝 Chemin du fichier audio à transcrire (ou 'q' pour quitter) : ").strip()
        if audio_path.lower() == 'q':
            break
        if not os.path.isfile(audio_path):
            print("❌ Fichier introuvable. Réessaie.")
            continue

        print(f"\n🎧 Transcription de : {audio_path}\n")
        start_time = time.time()

        # Transcription complète
        result = model.transcribe(audio_path, verbose=False)

        segments = result.get("segments", [])
        total = len(segments)

        if total == 0:
            print("❌ Aucun segment détecté.")
            continue

        srt_path = os.path.splitext(audio_path)[0] + ".srt"
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(tqdm(segments, desc="⏳ Progression", unit="seg", ncols=100)):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                srt_file.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")

        elapsed = time.time() - start_time
        print(f"\n✅ Transcription terminée en {elapsed:.2f} secondes")
        print(f"📄 Fichier SRT généré : {srt_path}\n")

if __name__ == "__main__":
    main()
