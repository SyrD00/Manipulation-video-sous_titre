import os
import whisperx
import torch
import srt
import time
import re

def srt_to_segments(srt_text):
    subtitles = list(srt.parse(srt_text))
    segments = []
    for sub in subtitles:
        start = sub.start.total_seconds()
        end = sub.end.total_seconds()
        segments.append({
            "text": sub.content.strip(),
            "start": start,
            "end": end
        })
    return segments

def save_segments_to_srt(segments, output_path):
    subtitles = []
    for i, seg in enumerate(segments):
        start = srt.srt_timestamp_to_timedelta(
            f"{int(seg['start'] // 3600):02}:{int((seg['start'] % 3600) // 60):02}:{int(seg['start'] % 60):02},{int((seg['start'] * 1000) % 1000):03}"
        )
        end = srt.srt_timestamp_to_timedelta(
            f"{int(seg['end'] // 3600):02}:{int((seg['end'] % 3600) // 60):02}:{int(seg['end'] % 60):02},{int((seg['end'] * 1000) % 1000):03}"
        )
        subtitles.append(srt.Subtitle(index=i+1, start=start, end=end, content=seg["text"]))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

# Regex pour reconnaître caractères japonais (hiragana, katakana, kanji)
japanese_char_pattern = re.compile(r'[\u3040-\u30ff\u4e00-\u9faf]')

def is_valid_segment(text):
    text = text.strip()
    if len(text) == 0:
        return False  # vide -> supprimer
    # Si texte que ponctuation / espaces -> supprimer
    if all(char in '、。！？,.!? ' for char in text):
        return False
    # Garder si contient au moins un caractère japonais
    if japanese_char_pattern.search(text):
        return True
    # Sinon supprimer
    return False

def filter_segments(segments):
    filtered = []
    for seg in segments:
        if is_valid_segment(seg["text"]):
            filtered.append(seg)
    return filtered

def main():
    srt_path = "C:/Users/babak/Videos/PSO/0525.srt"
    audio_path = "C:/Users/babak/Videos/PSO/PSO8.wav"
    output_path = "C:/Users/babak/Videos/PSO/PSO8_aligne.srt"

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("📥 Chargement du fichier SRT existant...")
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_text = f.read()
    segments = srt_to_segments(srt_text)

    print("🎧 Chargement de l'audio...")
    audio = whisperx.load_audio(audio_path)
    sr = 16000  # whisperx.load_audio retourne un tensor 16kHz, donc fréquence fixe
    duration = audio.shape[-1] / sr
    print(f"🔊 Durée de l'audio : {duration:.2f} secondes")

    print("🧹 Suppression des sous-titres dépassant la durée...")
    segments = [seg for seg in segments if seg["start"] < duration]

    print("🧼 Filtrage des textes vides ou invalides...")
    segments = filter_segments(segments)
    print(f"📝 Nombre de segments après filtre : {len(segments)}")

    print("🤖 Chargement du modèle WhisperX pour l'alignement forcé...")
    model_a, metadata = whisperx.load_align_model(language_code="ja", device=device)

    print(f"🔧 Appareil utilisé : {device}")
    if device == "cpu":
        print("⚠️ Aucun GPU détecté — l'alignement peut prendre plusieurs minutes...")

    print("⏱️ Alignement des sous-titres...")
    start_align = time.time()
    aligned_result = whisperx.align(segments, model_a, metadata, audio, device)
    print(f"✅ Alignement terminé en {time.time() - start_align:.2f} secondes.")

    print("💾 Sauvegarde du fichier SRT aligné...")
    save_segments_to_srt(aligned_result["segments"], output_path)
    print(f"✅ Fichier sauvegardé sous : '{output_path}'.")

if __name__ == "__main__":
    main()
