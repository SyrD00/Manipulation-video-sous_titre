"""
mfa g2p C:/Users/babak/Videos/PSO/Episode/temp/PSO23.txt ^
                    C:/Users/babak/Documents/MFA/pretrained_models/g2p/japanese_mfa.zip ^
                    C:/Users/babak/Videos/PSO/Episode/custom_g3p_lexicon.txt

mfa segment ^
  C:/Users/babak/Videos/PSO/Episode/temp/^
  C:/Users/babak/Videos/PSO/Episode/custom_g3p_lexicon.txt ^
  japanese_mfa ^
  C:/Users/babak/Videos/PSO/Episode/temp_segmented/

"""

from textgrid import TextGrid
import os

def textgrid_to_srt(textgrid_path, srt_path):
    tg = TextGrid.fromFile(textgrid_path)
    # On prend le premier tier (ou adapter si plusieurs tiers)
    tier = tg[0]

    srt_entries = []
    idx = 1
    current_text = ""
    current_start = None
    current_end = None

    for interval in tier.intervals:
        if interval.mark.strip():  # Si le texte n'est pas vide
            if current_start is None:
                current_start = interval.minTime
                current_text = interval.mark
            else:
                current_text += " " + interval.mark
            current_end = interval.maxTime
        else:
            if current_text:
                srt_entries.append((idx, current_start, current_end, current_text.strip()))
                idx += 1
                current_text = ""
                current_start = None
                current_end = None

    # Ajouter dernier segment si texte restant
    if current_text:
        srt_entries.append((idx, current_start, current_end, current_text.strip()))

    # Écriture du fichier SRT
    with open(srt_path, "w", encoding="utf-8") as f:
        for entry in srt_entries:
            i, start, end, text = entry
            start_srt = f"{int(start//3600):02}:{int((start%3600)//60):02}:{start%60:06.3f}".replace('.', ',')
            end_srt   = f"{int(end//3600):02}:{int((end%3600)//60):02}:{end%60:06.3f}".replace('.', ',')
            f.write(f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n")

    print(f"SRT généré : {srt_path}")


# Exemple d'utilisation
textgrid_file = "C:/Users/babak/Videos/PSO/Episode/temp_segmented/PSO23.TextGrid"
srt_file = "C:/Users/babak/Videos/PSO/Episode/output_align/PSO23_seg.srt"

textgrid_to_srt(textgrid_file, srt_file)
