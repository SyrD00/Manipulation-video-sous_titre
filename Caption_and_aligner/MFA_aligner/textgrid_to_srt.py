import torchaudio
import torch
from pathlib import Path
import re

# =========================
# Chemins à modifier
# =========================
textgrid_file = "C:/Users/babak/Videos/PSO/Episode/output_align/chibi_12half_cleaned.TextGrid"
audio_file = "C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav"
srt_file = "C:/Users/babak/Videos/PSO/Episode/output_align/chibi_12half_clean.srt"

# =========================
# Fonctions utilitaires
# =========================

def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def parse_textgrid_words(textgrid_path):
    intervals = []
    in_words_tier = False
    in_intervals = False
    xmin = xmax = text = None

    with open(textgrid_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith('name = "words"'):
                in_words_tier = True
            if in_words_tier and line.startswith('item ['):
                break
            if in_words_tier:
                if line.startswith("intervals:"):
                    in_intervals = True
                if in_intervals:
                    if line.startswith("xmin ="):
                        xmin = float(line.split("=")[1].strip())
                    elif line.startswith("xmax ="):
                        xmax = float(line.split("=")[1].strip())
                    elif line.startswith("text ="):
                        text = line.split("=", 1)[1].strip().strip('"')
                        intervals.append((xmin, xmax, text))
    return intervals

# =========================
# VAD : détection des segments parlés
# =========================
def detect_speech_segments(audio_path, sample_rate=16000):
    """Retourne une liste de segments parlés : [{'start':x,'end':y}, ...]"""
    # Charger l'audio
    wav, sr = torchaudio.load(audio_path)
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)  # convertir en mono
    if sr != sample_rate:
        wav = torchaudio.functional.resample(wav, sr, sample_rate)
        sr = sample_rate

    # Charger Silero VAD
    model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False
    )

    # Déballage correct selon version du repo
    if len(utils) == 4:
        get_speech_ts, _, _, _ = utils
    elif len(utils) == 3:
        get_speech_ts, _, _ = utils
    elif len(utils) == 2:
        get_speech_ts, _ = utils
    else:
        get_speech_ts = utils[0]

    wav = wav[0]  # mono
    speech_ts = get_speech_ts(wav, model, sampling_rate=sr, return_seconds=True)

    print(f"{len(speech_ts)} segments de parole détectés par VAD")
    for i, seg in enumerate(speech_ts, 1):
        print(f"Segment {i}: start={seg['start']:.2f}s, end={seg['end']:.2f}s, durée={seg['end']-seg['start']:.2f}s")

    return speech_ts


# =========================
# Ajuste xmin/xmax selon VAD
# =========================
def correct_intervals_with_vad(intervals, speech_segments, epsilon=0.03):
    corrected = []
    for xmin, xmax, text in intervals:
        if not text.strip():
            corrected.append((xmin, xmax, text))
            continue

        # Cherche le segment VAD qui chevauche le mot
        matched = None
        for seg in speech_segments:
            start = seg['start']
            end = seg['end']
            if xmax >= start and xmin <= end:
                matched = seg
                break
        if matched:
            xmin_corr = max(xmin, matched['start'] - epsilon)
            xmax_corr = min(xmax, matched['end'] + epsilon)
        else:
            xmin_corr = xmin
            xmax_corr = xmax

        corrected.append((xmin_corr, xmax_corr, text))
    return corrected

# =========================
# Génération du SRT
# =========================
def textgrid_to_srt(textgrid_path, audio_path, srt_path,
                    pause_threshold=0.2, max_chars=40, epsilon=0.03):
    intervals = parse_textgrid_words(textgrid_path)
    speech_segments = detect_speech_segments(audio_path)
    intervals = correct_intervals_with_vad(intervals, speech_segments, epsilon)

    subs = []
    current_sub = []
    xmin_courant = None
    xmax_courant = None
    last_was_silence = False

    for i, (xmin, xmax, text) in enumerate(intervals):
        if not text.strip():
            last_was_silence = True
            continue

        if not current_sub:
            current_sub = [text]
            xmin_courant = xmin
            xmax_courant = xmax
        else:
            pause = xmin - xmax_courant
            chars = sum(len(w) for w in current_sub) + len(text) + len(current_sub)
            if pause > pause_threshold or chars > max_chars or last_was_silence:
                subs.append((xmin_courant, xmax_courant, " ".join(current_sub)))
                current_sub = [text]
                xmin_courant = xmin
                xmax_courant = xmax
            else:
                current_sub.append(text)
                xmax_courant = xmax
        last_was_silence = False

    if current_sub:
        subs.append((xmin_courant, xmax_courant, " ".join(current_sub)))

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (start, end, line) in enumerate(subs, 1):
            f.write(f"{idx}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{line}\n\n")
    print(f"SRT généré : {srt_path}")

# =========================
# Lancer la conversion
# =========================
if __name__ == "__main__":
    textgrid_to_srt(textgrid_file, audio_file, srt_file,
                    pause_threshold=0.15,
                    max_chars=40,
                    epsilon=0.03)