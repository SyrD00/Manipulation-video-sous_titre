#Réservé aux utilisateurs de la carte graphique NVIDIA
#pip install ctranslate2[cuda]  Installe ctranslate2 avec le support de CUDA, donc capable
#  d’utiliser le GPU NVIDIA pour accélérer les calcul

import argparse
from faster_whisper import WhisperModel
import os

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"

def transcribe_audio(input_file, model_size="medium", language="ja", task="transcribe"):
    # Utilise CUDA (GPU) avec des poids float16, ce qui est plus rapide si ton GPU le supporte
    model = WhisperModel(model_size, device="cuda", compute_type="float16")

    segments, info = model.transcribe(input_file, beam_size=5, task=task, language=language)

    srt_filename = os.path.splitext(input_file)[0] + '.srt'
    with open(srt_filename, 'w', encoding='utf-8') as srt_file:
        for i, segment in enumerate(segments, start=1):
            start_time = format_time(segment.start)
            end_time = format_time(segment.end)
            text = segment.text.strip()
            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio and generate an SRT file.")
    parser.add_argument("input_file", help="Path to the audio file for transcription")
    parser.add_argument("--model_size", default="medium", help="Size of the Whisper model to use")
    parser.add_argument("--language", default="ja", help="Language code of the audio")
    parser.add_argument("--task", default="transcribe", choices=["transcribe", "translate"], help="Task to perform")
    args = parser.parse_args()
    transcribe_audio(args.input_file, args.model_size, args.language, args.task)
