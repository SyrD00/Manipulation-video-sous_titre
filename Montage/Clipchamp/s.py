# ============================================
# Silero-VAD + mini-pauses + fusion adaptative
# + split japonais contextuel
# + répartition texte -> segments audio (proportionnelle)
# ============================================

import torch
import torchaudio
import ffmpeg
import os
import re
import math
import pysubs2
from datetime import timedelta

# --- CONFIG ---
input_video     = r"C:/Users/babak/Videos/PSO/Video/PSO26.mp4"
input_clipchamp = r"C:/Users/babak/Downloads/PSO26.srt"
output_final    = r"C:/Users/babak/Downloads/PSO26_final.srt"
# ---------- util ----------
def convert_to_wav16k(infile):
    tmp_wav = "tmp_audio.wav"
    if not infile.lower().endswith(".wav"):
        (
            ffmpeg
            .input(infile)
            .output(tmp_wav, ac=1, ar=16000, format="wav", loglevel="quiet")
            .overwrite_output()
            .run()
        )
        return tmp_wav
    return infile

def to_srt_time(seconds):
    td = timedelta(seconds=float(seconds))
    total_seconds = int(td.total_seconds())
    ms = int(round((seconds - total_seconds) * 1000))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

# ---------- split japonais “intelligent” ----------
def smart_split_japanese_full(text: str):
    """
    1) coupe TOUJOURS après [。！？.!?] (délimiteurs conservés)
    2) coupe optionnellement après 「、」 quand c'est une pause typique :
       ...だと、  ...によると、  ...って、  ...けど、  ...が、
    3) sinon NE PAS couper sur 「、」 (on garde la virgule dans la phrase)
    4) ne supprime aucun signe (notamment 「、」)
    """
    if not text or not text.strip():
        return []

    result = []

    # coupe après fins de phrases, en gardant le délimiteur
    chunks = re.split(r'(?<=[。！？.!?])', text)

    for chunk in chunks:
        if not chunk or not chunk.strip():
            continue

        p = chunk

        # coupes contextuelles sur 「、」 pour quelques tournures
        # on coupe juste après la virgule et on GARDE la virgule dans la 1re sous-phrase
        while True:
            m = re.search(r'(だと|によると|って|けど|が)、', p)
            if not m:
                break
            cut = m.end()  # position juste après la virgule
            left = p[:cut]    # conserve 「、」
            right = p[cut:]
            if left.strip():
                result.append(left.strip())
            p = right

        # pour le reste : NE PAS couper sur 「、」 (on veut préserver la virgule)
        if p.strip():
            result.append(p.strip())

    return result

# ---------- Silero + mini-VAD ----------
def detect_internal_pauses(wav_segment, sr, frame_ms=20, silence_thresh=-40.0, min_sil_dur=0.15):
    """détecte des mini-pauses réelles dans un segment voix"""
    if wav_segment.dim() > 1:
        wav_segment = wav_segment.mean(dim=0, keepdim=True)

    frame_len = int(sr * frame_ms / 1000)
    hop = frame_len
    num_frames = wav_segment.shape[1] // hop
    energies = []
    for i in range(num_frames):
        frame = wav_segment[:, i * hop:(i + 1) * hop]
        energy = torch.sqrt(torch.mean(frame ** 2))
        db = 20 * torch.log10(energy + 1e-10)
        energies.append(db.item())

    pauses = []
    in_sil = False
    sil_start = None
    for i, val in enumerate(energies):
        t = i * frame_ms / 1000.0
        if (val < silence_thresh) and not in_sil:
            in_sil = True
            sil_start = t
        elif (val >= silence_thresh) and in_sil:
            dur = t - sil_start
            if dur >= min_sil_dur:
                pauses.append((sil_start, t))
            in_sil = False
    return pauses

# ---------- allocation audio->phrases ----------
def allocate_segments_to_sentences(durations, sent_lengths):
    """
    Répartit un nombre total de segments audio (durations) entre des phrases
    proportionnellement à la longueur de chaque phrase.
    Garantit >=1 segment par phrase. Renvoie une liste a_k.
    """
    A = len(durations)
    S = len(sent_lengths)
    if S == 0:
        return []

    total_chars = max(1, sum(max(1, L) for L in sent_lengths))
    # part brute
    raw = [A * (max(1, L) / total_chars) for L in sent_lengths]
    alloc = [max(1, int(math.floor(x))) for x in raw]

    # corriger somme
    diff = A - sum(alloc)
    # distribuer le reste selon la plus grande part fractionnaire
    fracs = [(i, raw[i] - math.floor(raw[i])) for i in range(S)]
    fracs.sort(key=lambda x: x[1], reverse=True)

    i = 0
    while diff > 0 and i < S:
        alloc[fracs[i][0]] += 1
        diff -= 1
        i += 1
    i = 0
    while diff < 0 and i < S:
        j = fracs[i][0]
        if alloc[j] > 1:
            alloc[j] -= 1
            diff += 1
        i += 1

    # sécurité : si on a encore un écart (rare), ajuster sur la dernière phrase
    if sum(alloc) != A:
        alloc[-1] += (A - sum(alloc))

    return alloc  # somme == A

def cut_text_by_char_proportions(text, durations):
    """
    Coupe 'text' en n parts (n=len(durations)) proportionnelles aux durées.
    Couper au caractère (on ne supprime pas «、»). Retourne liste de sous-textes.
    """
    n = len(durations)
    if n == 1:
        return [text]

    total_dur = sum(durations)
    if total_dur <= 0:
        # fallback : coupes égales
        total_dur = n

    total_chars = len(text)
    # indices de coupe cibles (en nb de caractères)
    cuts = []
    acc = 0.0
    for d in durations[:-1]:
        acc += d
        cuts.append(int(round(acc / total_dur * total_chars)))

    parts = []
    start = 0
    for c in cuts:
        # éviter part vide en ajustant un peu
        c = max(start + 1, min(c, total_chars - (n - len(parts) - 1)))
        part = text[start:c]
        parts.append(part)
        start = c
    parts.append(text[start:])

    # nettoyage léger des espaces, sans toucher à la ponctuation japonaise
    parts = [p.strip() for p in parts]
    return parts

# ================== PIPELINE ==================
# 1) audio -> VAD macro
wav_file = convert_to_wav16k(input_video)
print("🔄 Silero-VAD model…")
model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad")
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

wav, sr = torchaudio.load(wav_file)
if sr != 16000:
    wav = torchaudio.transforms.Resample(sr, 16000)(wav)
    sr = 16000

print("🎧 Détection vocale…")
speech_segments = get_speech_timestamps(wav, model, sampling_rate=sr)
print(f"🧠 VAD macro segments: {len(speech_segments)}")

# 2) mini-VAD interne pour micro-pauses
raw_segments = []
for seg in speech_segments:
    start_t = seg["start"] / sr
    end_t   = seg["end"]   / sr
    segment_audio = wav[:, seg["start"]:seg["end"]]
    internal = detect_internal_pauses(segment_audio, sr)

    last = 0.0
    for ps, pe in internal:
        if ps - last > 0.2:
            raw_segments.append((start_t + last, start_t + ps))
        last = pe
    if end_t - (start_t + last) > 0.2:
        raw_segments.append((start_t + last, end_t))

print(f"🎧 Segments après mini-pauses: {len(raw_segments)}")

# 3) fusion adaptative (anti-faux-silences)
merged = []
MIN_LEN = 0.8   # < 0.8 s → trop court → fusion
MAX_GAP = 0.3   # gap < 0.3 s → fusion
for seg in raw_segments:
    if not merged:
        merged.append(list(seg))
        continue
    ps, pe = merged[-1]
    cs, ce = seg
    seg_len = pe - ps
    gap = cs - pe
    if seg_len < MIN_LEN or gap < MAX_GAP:
        merged[-1][1] = ce
    else:
        merged.append([cs, ce])

vad_segments = [(s, e) for s, e in merged]
vad_durations = [e - s for (s, e) in vad_segments]
print(f"🎙️ Segments fusionnés: {len(vad_segments)}")

# 4) lire Clipchamp et splitter “intelligent”
clip = pysubs2.load(input_clipchamp, encoding="utf-8")
sentences = []
for line in clip:
    sentences.extend(smart_split_japanese_full(line.text))
sentences = [s for s in sentences if s]
print(f"✂️ Phrases (split intelligent): {len(sentences)}")

if not vad_segments or not sentences:
    raise RuntimeError("Pas de segments audio ou pas de phrases.")

# 5) allouer des segments audio aux phrases (proportion longueur)
sent_lengths = [len(s) for s in sentences]
alloc = allocate_segments_to_sentences(vad_durations, sent_lengths)  # liste a_k, somme == len(vad_segments)

# 6) pour chaque phrase, on découpe son texte selon les durées des segments alloués
new_subs = pysubs2.SSAFile()
seg_idx = 0
for sent, k in zip(sentences, alloc):
    k = max(1, k)
    # durées des k segments audio alloués
    these_segments = vad_segments[seg_idx:seg_idx + k]
    seg_durs = [e - s for (s, e) in these_segments]

    # coupe la phrase en k morceaux proportionnels aux durées
    subtexts = cut_text_by_char_proportions(sent, seg_durs)

    # émet k sous-titres
    for (s, e), txt in zip(these_segments, subtexts):
        evt = pysubs2.SSAEvent(start=int(s * 1000), end=int(e * 1000), text=txt)
        new_subs.append(evt)

    seg_idx += k
    if seg_idx >= len(vad_segments):
        break

# s'il reste des segments audio non utilisés (rare), on les émet vides
while seg_idx < len(vad_segments):
    s, e = vad_segments[seg_idx]
    new_subs.append(pysubs2.SSAEvent(start=int(s * 1000), end=int(e * 1000), text=""))
    seg_idx += 1

new_subs.save(output_final, encoding="utf-8")
print("✅ Fichier SRT généré :", output_final)

# cleanup
if wav_file == "tmp_audio.wav" and os.path.exists(wav_file):
    os.remove(wav_file)
