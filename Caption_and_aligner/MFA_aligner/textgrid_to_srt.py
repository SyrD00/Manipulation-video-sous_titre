import torch
import torchaudio

# =====================
# Fonctions utilitaires
# =====================

def format_time(seconds):
    """Convertit un temps en secondes (float) au format SRT HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def parse_textgrid_words(textgrid_path):
    """
    Parse un TextGrid et retourne la liste des intervalles (xmin, xmax, text)
    de la tier "words".
    """
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

# =====================
# Détection des segments parlés VAD
# =====================

def detect_speech_segments(audio_path, sampling_rate=16000):
    """
    Retourne la liste des segments parlés détectés par Silero VAD.
    """
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False
    )
    get_speech_ts = utils[0]

    wav, sr = torchaudio.load(audio_path)
    if sr != sampling_rate:
        wav = torchaudio.functional.resample(wav, sr, sampling_rate)
        sr = sampling_rate

    # ===== Mono obligatoire =====
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0)
    # ============================

    speech_ts = get_speech_ts(wav, model, sampling_rate=sr)
    segments = [{"start": seg["start"]/sr, "end": seg["end"]/sr} for seg in speech_ts]
    print(f"{len(segments)} segments de parole détectés par VAD")
    return segments

# =====================
# Conversion TextGrid -> SRT avec post-traitement VAD + TextGrid silence
# =====================

def textgrid_to_srt(textgrid_path, audio_path, srt_path,
                    pause_threshold=0.2, min_silence_for_cut=0.01): # max_chars=40,
    """
    Convertit un TextGrid en SRT en corrigeant xmax par VAD et en respectant les pauses.
    """
    # 1. Extraire TextGrid
    intervals = parse_textgrid_words(textgrid_path)

    # 2. Détection segments parlés
    speech_segments = detect_speech_segments(audio_path)

    # 3. Post-traitement : corriger xmin/xmax avec VAD
    corrected_intervals = []
    for xmin, xmax, text in intervals:
        if not text.strip():
            corrected_intervals.append((xmin, xmax, text))
            continue

        # Chercher le segment VAD couvrant le mot
        for seg in speech_segments:
            seg_start, seg_end = seg["start"], seg["end"]
            if seg_end >= xmin and seg_start <= xmax:
                xmin_corr = max(xmin, seg_start)
                xmax_corr = min(xmax, seg_end)
                corrected_intervals.append((xmin_corr, xmax_corr, text))
                break
        else:
            # aucun segment trouvé → on garde les valeurs TextGrid
            corrected_intervals.append((xmin, xmax, text))

    # 4. Génération des sous-titres
    subs = []
    current_sub = []
    xmin_courant = xmax_courant = None
    last_interval_was_silence = False

    for i, (xmin, xmax, text) in enumerate(corrected_intervals):
        if not text.strip():
            # intervalle vide
            if xmax - xmin >= min_silence_for_cut:
                last_interval_was_silence = True
            continue

        if not current_sub:
            current_sub = [text]
            xmin_courant = xmin
            xmax_courant = xmax
        else:
            pause = xmin - xmax_courant
            #chars = sum(len(w) for w in current_sub) + len(text) + len(current_sub)
            """
            difference entre pause et pause_threshold et min_silence_for_cut:  
            definition pause= periode de silence entre deux intervalles non vides
            definition pause_threshold= 
            min_silence_for_cut=       
            Si la pause est supérieure au seuil ou si le dernier intervalle était du silence, 

            """
            if pause > pause_threshold  or last_interval_was_silence: #or chars > max_chars
                subs.append((xmin_courant, xmax_courant, " ".join(current_sub)))
                current_sub = [text]
                xmin_courant = xmin
                xmax_courant = xmax
            else:
                current_sub.append(text)
                xmax_courant = xmax

        last_interval_was_silence = False

    if current_sub:
        subs.append((xmin_courant, xmax_courant, " ".join(current_sub)))

    # 5. Écriture SRT
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (start, end, line) in enumerate(subs, 1):
            f.write(f"{idx}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{line}\n\n")

    print(f"SRT généré : {srt_path}")

# =====================
# Exécution principale
# =====================

if __name__ == "__main__":
    """
    textgrid_file = "C:/Users/babak/Videos/PSO/Episode/output_align/chibi_12half_cleaned.TextGrid"
    audio_file    = "C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav"
    srt_file      = "C:/Users/babak/Videos/PSO/Episode/output_align/C.srt"
    """
    textgrid_file = "C:/Users/babak/Videos/PSO/Episode/output_align/1.TextGrid"
    audio_file    = "C:/Users/babak/Videos/PSO/Episode/temp/PSO23.WAV"
    srt_file      = "C:/Users/babak/Videos/PSO/Episode/output_align/1.srt"
    textgrid_to_srt(textgrid_file, audio_file, srt_file,
                    pause_threshold=0.3,
                    min_silence_for_cut=0.05) #max_chars=40,
    



"""
Version sans vad (j'aic chois version avecvad car affiner plus le xmax)
    
    



import re

def format_time(seconds):
    
    #Convertit un temps en secondes (float) au format SRT : HH:MM:SS,mmm
    #Exemple : 4.28 -> "00:00:04,280"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def parse_textgrid_words(textgrid_path):
    
    #Parse un fichier TextGrid et extrait la liste des intervalles (xmin, xmax, text)
    #de la tier "words".
    #Retourne une liste de tuples : (xmin, xmax, text)
    
    intervals = []
    in_words_tier = False
    in_intervals = False
    xmin = xmax = text = None

    # On lit le fichier ligne par ligne
    with open(textgrid_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Détecter le début de la tier "words"
            if line.startswith('name = "words"'):
                in_words_tier = True
            # Détecter la fin de la tier "words"
            if in_words_tier and line.startswith('item ['):
                break  # On sort dès qu'on arrive à la tier suivante

            # On ne traite que la tier "words"
            if in_words_tier:
                # Début des intervalles
                if line.startswith("intervals:"):
                    in_intervals = True
                # Extraction des valeurs xmin, xmax, text
                if in_intervals:
                    if line.startswith("xmin ="):
                        xmin = float(line.split("=")[1].strip())
                    elif line.startswith("xmax ="):
                        xmax = float(line.split("=")[1].strip())
                    elif line.startswith("text ="):
                        # On enlève les guillemets autour du texte
                        text = line.split("=", 1)[1].strip().strip('"')
                        # On ajoute l'intervalle à la liste
                        intervals.append((xmin, xmax, text))
    return intervals

def textgrid_to_srt(
    textgrid_path,
    srt_path,
    pause_threshold=0.2,
    #max_duration=2.5,
    max_chars=40
):
    
    #Convertit un TextGrid en SRT.
    #- pause_threshold : durée (en secondes) d'une pause considérée comme une coupure de sous-titre
    #- max_duration : durée maximale d'un sous-titre (en secondes)
    #- max_chars : nombre maximal de caractères par sous-titre (optionnel, pour la lisibilité)
    
    # 1. On extrait les intervalles de la tier "words"
    intervals = parse_textgrid_words(textgrid_path)

    # 2. On prépare la liste des sous-titres
    subs = []  # Liste de tuples (start, end, texte)
    current_sub = []  # Liste des mots du sous-titre courant
    xmin_courant = None  # xmin du sous-titre courant
    xmax_courant = None    # xmax du sous-titre courant
    last_interval_was_silence = False #sert à savoir si le mot précédent était un silence

    for i, (xmin, xmax, text) in enumerate(intervals):
        # 3. On saute les intervalles vides (silences)
        if not text.strip():#text.strip() enlève les espaces avant et après le texte, si après avoir 
                            #enlevé les espaces le texte est vide on est dans un silence
            
            last_interval_was_silence = True # 
            continue

        # 4. Si c'est le début d'un nouveau sous-titre
        if not current_sub: #sachant que current_sub est la liste des mots du sous-titre courant alors si elle est vide on est au début d'un nouveau sous-titre(if not current_sub est équivalent à if len(current_sub) == 0)
            current_sub = [text]     
            xmin_courant = xmin
            xmax_courant = xmax
        else:
            # Calcul de la pause entre la fin du dernier mot et le début du mot courant
            pause = xmin - xmax_courant
            # Durée totale si on ajoute ce mot au sous-titre courant
            #duration = xmax - xmin_courant
            # Nombre de caractères si on ajoute ce mot
            chars = sum(len(w) for w in current_sub) + len(text) + len(current_sub)

            # 5. On décide si on coupe le sous-titre ici
            if (
                pause > pause_threshold or
                #duration > max_duration or
                chars > max_chars   or
                last_interval_was_silence # On coupe aussi si le mot précédent était un silence
            ):
                # On ajoute le sous-titre courant à la liste
                subs.append((xmin_courant, xmax_courant, " ".join(current_sub)))
                # On démarre un nouveau sous-titre avec le mot courant
                current_sub = [text]
                xmin_courant = xmin
                xmax_courant = xmax
            else:
                # Sinon, on ajoute le mot au sous-titre courant
                current_sub.append(text)
                xmax_courant = xmax

         #On a traité le silence ,on le remt à False       
        last_interval_was_silence = False

    # 6. On n'oublie pas d'ajouter le dernier sous-titre
    if current_sub:
        subs.append((xmin_courant, xmax_courant, " ".join(current_sub)))

    # 7. On écrit le fichier SRT
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (start, end, line) in enumerate(subs, 1):
            f.write(f"{idx}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{line}\n\n")

    print(f"SRT généré : {srt_path}")

# =========================
# Exemple d'utilisation
# =========================
if __name__ == "__main__":
    # Chemin vers le fichier TextGrid à convertir
    textgrid_file = "C:/Users/babak/Videos/PSO/Episode/output_align/1.TextGrid"
    # Chemin de sortie du SRT
    srt_file = "C:/Users/babak/Videos/PSO/Episode/output_align/1.srt"
    # Appel de la fonction principale
    textgrid_to_srt(
        textgrid_file,
        srt_file,
        pause_threshold=0.3,   # met ce parametre uniquement si tu veux changer la valeur par défaut
        #max_duration=2.5,      # Sous-titre max 2.5s
        max_chars=40           # Sous-titre max 40 caractères (optionnel) (idem comme pause_threshold)
    )
    
    """